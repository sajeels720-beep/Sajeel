"""Assemble the brain-freeze Short from rendered shot folders (PNG sequences) at the script
timings. Every shot is fitted to its slot, so the picture never freezes, and the still frames
where a camera move eases in or out are left out at the cuts. Optional captions (2-4 white
bold words at ~75% height, his style).

usage: python3 assemble_cut.py SHOTS_DIR OUT.mp4 [--captions] [--voiceover AUDIO_DIR] [--width 1080]
                                [--fps 30] [--font F.ttf]
SHOTS_DIR holds one folder per shot (shot01 ... shot19b), each with f_0001.png ... directly
inside it (Blender's output) or in a frames/ subfolder.
--voiceover: the edit follows your recording. A line that runs longer than planned stretches
the shots under it (later shots move back) and the captions show while each line is spoken.
Use the same folder with mix_audio.py so the sound lines up.
Needs ffmpeg. Missing shots become labelled placeholders. Works on Windows, macOS and Linux.
"""
import argparse
import glob
import os
import shutil
import subprocess
import tempfile

from timeline import CUT, SCRIPT, Timeline

FONTS = [  # first bold sans found is used for captions and placeholder labels
    r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def motion(folder, count):
    """How much each frame differs from the next (mean grey change on a 45x80 copy)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-start_number", "1", "-i", os.path.join(folder, "f_%04d.png"),
                          "-frames:v", str(count), "-vf", "scale=45:80,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    size = 45 * 80
    frames = [raw[k:k + size] for k in range(0, len(raw) - size + 1, size)]
    return [sum(abs(p - q) for p, q in zip(f, g)) / size for f, g in zip(frames, frames[1:])]


def still_edges(steps, limit=4, share=0.2):
    """Frames to leave out at the start and end of a shot while its camera move is still easing
    in or out (moving less than `share` of the shot's typical motion), at most `limit` each: a
    cut then lands on movement instead of a short stop."""
    if len(steps) < 3 * limit:
        return 0, 0
    slow = share * sorted(steps)[len(steps) // 2]
    head = next((k for k, d in enumerate(steps[:limit]) if d >= slow), limit)
    tail = next((k for k, d in enumerate(reversed(steps[-limit:])) if d >= slow), limit)
    return head, tail


def caption_filters(tmp, height, tl):
    """drawtext filters: each line's groups share its time in proportion to their length.
    Text files and the font sit in tmp, which is ffmpeg's working folder, so the filter
    only holds relative names (Windows drive colons would break the filter syntax)."""
    filters = []
    k = 0
    for n, (_, _, groups) in enumerate(SCRIPT, start=1):
        t0, t1 = tl.caption_span(n)
        weights = [len(g) for g in groups]
        t = t0
        for g, w in zip(groups, weights):
            dt = (t1 - t0) * w / sum(weights)
            name = f"cap_{k:02d}.txt"
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
                f.write(g)
            filters.append(
                f"drawtext=fontfile=font.ttf:textfile={name}:fontsize={int(height * 0.036)}:fontcolor=white:"
                f"shadowcolor=black@0.7:shadowx=3:shadowy=3:borderw=2:bordercolor=black@0.35:"
                f"x=(w-text_w)/2:y=h*0.72:enable='between(t,{t:.3f},{t + dt:.3f})'")
            t += dt
            k += 1
    return filters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots_dir")
    ap.add_argument("out")
    ap.add_argument("--captions", action="store_true")
    ap.add_argument("--voiceover", help="folder with voiceover_01 ... _11: the edit follows the recording")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--font", help="bold .ttf for captions (default: Arial Bold / DejaVu Sans Bold)")
    a = ap.parse_args()
    W, H, fps = a.width, a.width * 16 // 9, a.fps
    tl = Timeline.from_folder(a.voiceover)
    if a.voiceover:
        print(tl.report())
    font = next((f for f in ([a.font] if a.font else FONTS) if os.path.isfile(f)), None)
    if a.captions and not font:
        raise SystemExit("No caption font found: pass --font path/to/bold.ttf")
    inputs, parts = [], []
    for i, (name, t0, t1) in enumerate(CUT):
        start, end = tl.warp(t0), tl.warp(t1)
        slot = round(end * fps) - round(start * fps)                  # frames, so slots tile exactly
        folder = os.path.abspath(os.path.join(a.shots_dir, name))
        if os.path.isdir(os.path.join(folder, "frames")):
            folder = os.path.join(folder, "frames")
        frames = sorted(glob.glob(os.path.join(folder, "f_*.png")))
        if frames:
            # every shot plays all its moving frames, fitted to its slot: slower where a line runs
            # long (frames blended so the motion stays smooth), faster where it is short; never a
            # frozen last frame, never a cut-off ending. Its first and last kept frames land on
            # the slot's first and last frames, and frames are renumbered (frame N at N/fps) so
            # the slots tile exactly and the picture never drifts off the voice.
            head, tail = still_edges(motion(folder, len(frames)))
            keep = len(frames) - head - tail
            stretch = min(max((slot - 1) / max(keep - 1, 1), 0.7), 1.6)
            retime = f"minterpolate=fps={fps}:mi_mode=blend" if stretch > 1.05 else f"fps={fps}"
            inputs += ["-framerate", str(fps), "-start_number", str(1 + head), "-i", os.path.join(folder, "f_%04d.png")]
            # (two spare copies of the last frame, cut off again below, let the blend reach it)
            parts.append(f"[{i}:v]trim=end_frame={keep},tpad=stop_mode=clone:stop=2,scale={W}:{H}:flags=lanczos,"
                         f"setsar=1,settb=AVTB,setpts=N*{stretch:.8f}/{fps}/TB,{retime},"
                         f"tpad=stop_mode=clone:stop_duration={slot / fps + 1:.3f},"
                         f"trim=end_frame={slot},settb=1/{fps},setpts=N[v{i}]")
        else:
            inputs += ["-f", "lavfi", "-i", f"color=c=0x101418:s={W}x{H}:r={fps}:d={slot / fps:.3f}"]
            label = (f"drawtext=fontfile=font.ttf:text='{name} - not rendered':fontcolor=white:fontsize={H // 30}:"
                     f"x=(w-text_w)/2:y=(h-text_h)/2," if font else "")
            parts.append(f"[{i}:v]{label}trim=end_frame={slot},settb=1/{fps},setpts=N[v{i}]")
    graph = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(CUT))) + f"concat=n={len(CUT)}:v=1:a=0[cut]"
    out = os.path.abspath(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        if font:
            shutil.copyfile(font, os.path.join(tmp, "font.ttf"))
        last = "[cut]"
        if a.captions:
            graph += ";[cut]" + ",".join(caption_filters(tmp, H, tl)) + "[capt]"
            last = "[capt]"
        cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", last, "-r", str(fps),
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               out]
        subprocess.run(cmd, check=True, cwd=tmp)
    print("wrote", out)


if __name__ == "__main__":
    main()
