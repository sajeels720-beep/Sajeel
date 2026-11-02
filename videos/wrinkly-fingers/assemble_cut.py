"""Assemble the wrinkly-fingers Short from the rendered shot folders (PNG sequences), with optional
captions (2-4 white bold words at ~72% height, as in the brain-freeze and sneeze videos). Every shot
plays all its frames: his acting runs across the cuts, so the picture is never retimed. Add the
sound afterwards with mix_audio.py. (The sneeze video's, with this video's timeline.)

usage: python3 assemble_cut.py SHOTS_DIR OUT.mp4 [--captions --voiceover AUDIO_DIR] [--width 1080]
                                [--font F.ttf]
SHOTS_DIR holds one folder per shot (shot01 ... shot16), each with f_0001.png ... directly inside
it (Blender's output) or in a frames/ subfolder. --captions needs --voiceover: each caption group
comes up as it is spoken. Needs ffmpeg. Missing shots become labelled placeholders. Works on
Windows, macOS and Linux.
"""
import argparse
import os
import shutil
import subprocess
import tempfile

from timeline import FPS, SHOTS, captions, find_audio

FONTS = [  # first bold sans found is used for captions and placeholder labels
    r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def caption_filters(tmp, height, groups):
    """drawtext filters, one per caption group. Text files and the font sit in tmp, which is
    ffmpeg's working folder, so the filter only holds relative names (Windows drive colons
    would break the filter syntax)."""
    filters = []
    for k, (t0, t1, words) in enumerate(groups):
        name = f"cap_{k:02d}.txt"
        with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
            f.write(words)
        filters.append(
            f"drawtext=fontfile=font.ttf:textfile={name}:fontsize={int(height * 0.036)}:fontcolor=white:"
            f"shadowcolor=black@0.7:shadowx=3:shadowy=3:borderw=2:bordercolor=black@0.35:"
            f"x=(w-text_w)/2:y=h*0.72:enable='between(t,{t0:.3f},{t1:.3f})'")
    return filters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots_dir")
    ap.add_argument("out")
    ap.add_argument("--captions", action="store_true")
    ap.add_argument("--voiceover", help="folder with voiceover_1 ... voiceover_4: the captions follow it")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--font", help="bold .ttf for captions (default: Arial Bold / DejaVu Sans Bold)")
    a = ap.parse_args()
    W, H = a.width, a.width * 16 // 9
    if a.captions and not a.voiceover:
        raise SystemExit("--captions needs --voiceover AUDIO_DIR: the captions follow the recording")
    font = next((f for f in ([a.font] if a.font else FONTS) if os.path.isfile(f)), None)
    if a.captions and not font:
        raise SystemExit("No caption font found: pass --font path/to/bold.ttf")
    inputs, parts = [], []
    for i, (name, count) in enumerate(SHOTS):
        folder = os.path.abspath(os.path.join(a.shots_dir, name))
        if os.path.isdir(os.path.join(folder, "frames")):
            folder = os.path.join(folder, "frames")
        if os.path.isfile(os.path.join(folder, "f_0001.png")):
            inputs += ["-framerate", str(FPS), "-start_number", "1", "-i", os.path.join(folder, "f_%04d.png")]
            # a shot with frames missing at its end holds its last frame, so the cuts stay in time
            parts.append(f"[{i}:v]scale={W}:{H}:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop={count},"
                         f"trim=end_frame={count},settb=1/{FPS},setpts=N[v{i}]")
        else:
            inputs += ["-f", "lavfi", "-i", f"color=c=0x101418:s={W}x{H}:r={FPS}:d={count / FPS:.3f}"]
            label = (f"drawtext=fontfile=font.ttf:text='{name} - not rendered':fontcolor=white:fontsize={H // 30}:"
                     f"x=(w-text_w)/2:y=(h-text_h)/2," if font else "")
            parts.append(f"[{i}:v]{label}trim=end_frame={count},settb=1/{FPS},setpts=N[v{i}]")
    graph = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(SHOTS))) + \
        f"concat=n={len(SHOTS)}:v=1:a=0[cut]"
    out = os.path.abspath(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        if font:
            shutil.copyfile(font, os.path.join(tmp, "font.ttf"))
        last = "[cut]"
        if a.captions:
            groups = captions(find_audio(a.voiceover)["vo"])
            graph += ";[cut]" + ",".join(caption_filters(tmp, H, groups)) + "[capt]"
            last = "[capt]"
            for t0, t1, words in groups:
                print(f"  {t0:6.2f}-{t1:6.2f} s  {words}")
        cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", last, "-r", str(FPS),
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               out]
        subprocess.run(cmd, check=True, cwd=tmp)
    print("wrote", out)


if __name__ == "__main__":
    main()
