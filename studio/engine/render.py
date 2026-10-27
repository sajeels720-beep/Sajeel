"""Timeline of shots -> frames -> H.264, rendered in parallel slices."""
from __future__ import annotations

import math
import multiprocessing as mp
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import skia

from .core import FPS, H, W, clamp
from .draw import col, vignette


@dataclass
class Shot:
    start: float
    end: float
    draw: Callable            # draw(canvas, t_local, T_global)
    camera: Callable | None = None  # camera(t_local) -> (cx, cy, zoom[, rot])
    bg: str = 'bg'
    name: str = ''


@dataclass
class Film:
    duration: float
    shots: list
    overlays: list = field(default_factory=list)   # fn(canvas, T) in screen space
    post: list = field(default_factory=list)        # fn(canvas, T) after vignette (fades, flashes)
    fps: int = FPS
    vignette: float = 0.72

    def shot_at(self, T):
        for s in self.shots:
            if s.start <= T < s.end:
                return s
        return self.shots[-1] if T >= self.shots[-1].start else None

    def draw_frame(self, c, T):
        shot = self.shot_at(T)
        c.clear(col(shot.bg if shot else 'bg'))
        if shot:
            t = T - shot.start
            c.save()
            if shot.camera:
                cam = shot.camera(t)
                cx, cy, z = cam[:3]
                rot = cam[3] if len(cam) > 3 else 0.0
                c.translate(W / 2, H / 2)
                if rot:
                    c.rotate(rot)
                c.scale(z, z)
                c.translate(-cx, -cy)
            shot.draw(c, t, T)
            c.restore()
        for fn in self.overlays:
            fn(c, T)
        if self.vignette:
            vignette(c, W, H, self.vignette)
        for fn in self.post:
            fn(c, T)


def _surface():
    return skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))


def still(film: Film, T: float, path, scale=1.0):
    s = _surface()
    film.draw_frame(s.getCanvas(), T)
    img = s.makeImageSnapshot()
    if scale != 1.0:
        img = img.resize(int(W * scale), int(H * scale))
    img.save(str(path), skia.kPNG)
    return path


def contact_sheet(film: Film, times, path, cols=4, thumb_w=640):
    thumb_h = int(thumb_w * H / W)
    rows = math.ceil(len(times) / cols)
    sheet = skia.Surface(cols * thumb_w, rows * (thumb_h + 34))
    sc = sheet.getCanvas()
    sc.clear(skia.ColorBLACK)
    s = _surface()
    from .draw import text
    for i, T in enumerate(times):
        film.draw_frame(s.getCanvas(), T)
        img = s.makeImageSnapshot()
        x, y = (i % cols) * thumb_w, (i // cols) * (thumb_h + 34)
        sc.drawImageRect(img, skia.Rect.MakeXYWH(x, y, thumb_w, thumb_h), skia.SamplingOptions(skia.FilterMode.kLinear))
        text(sc, f'{int(T // 60)}:{T % 60:05.2f}', x + 8, y + thumb_h + 26, 24, 'Inter', 'white', align='left')
    sheet.makeImageSnapshot().save(str(path), skia.kPNG)
    return path


def _encoder(out_path, fps, grain=6):
    vf = f'noise=c0s={grain}:c0f=t+u,format=yuv420p' if grain else 'format=yuv420p'
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
           '-vf', vf, '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-tune', 'animation',
           '-g', str(fps * 2), '-threads', '2', str(out_path)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _render_range(film, f0, f1, out_path, progress_path):
    s = _surface()
    canvas = s.getCanvas()
    enc = _encoder(out_path, film.fps)
    t_start = time.time()
    for f in range(f0, f1):
        film.draw_frame(canvas, f / film.fps)
        enc.stdin.write(s.toarray().tobytes())
        if (f - f0) % 30 == 0:
            Path(progress_path).write_text(f'{f - f0}/{f1 - f0} frames, {time.time() - t_start:.0f}s\n')
    enc.stdin.close()
    enc.wait()
    Path(progress_path).write_text(f'done {f1 - f0} frames in {time.time() - t_start:.0f}s\n')


def render(film: Film, out_path, workers=4, t0=0.0, t1=None, workdir=None):
    """Render [t0, t1) to out_path (video only)."""
    out_path = Path(out_path)
    workdir = Path(workdir or out_path.parent / (out_path.stem + '_parts'))
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    f0 = int(round(t0 * film.fps))
    f1 = int(round((film.duration if t1 is None else t1) * film.fps))
    n = max(1, min(workers, f1 - f0))
    bounds = [f0 + (f1 - f0) * k // n for k in range(n + 1)]
    ctx = mp.get_context('fork')
    procs = []
    parts = []
    for k in range(n):
        part = workdir / f'part{k:02d}.mp4'
        parts.append(part)
        p = ctx.Process(target=_render_range, args=(film, bounds[k], bounds[k + 1], part, workdir / f'progress{k}.txt'))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
        if p.exitcode != 0:
            raise RuntimeError(f'render worker failed with exit code {p.exitcode}')
    listing = workdir / 'parts.txt'
    listing.write_text(''.join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
                    '-i', str(listing), '-c', 'copy', str(out_path)], check=True)
    return out_path


def mux(video, audio, out_path, loudness=-14.0, true_peak=-1.5):
    """Combine picture and soundtrack; two-pass loudness normalisation to YouTube's -14 LUFS."""
    import json
    base = f'loudnorm=I={loudness}:TP={true_peak}:LRA=20'
    probe = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(audio), '-af',
                            base + ':print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    err = probe.stderr
    m = json.loads(err[err.rindex('{'):err.rindex('}') + 1])
    af = (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(video), '-i', str(audio),
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', af, '-ar', '48000',
                    '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', str(out_path)], check=True)
    return out_path
