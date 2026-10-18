"""Assemble the brain-freeze Short from rendered shot folders (PNG sequences) at the script
timings, holding a shot's last frame where the voiceover pauses. Optional caption guide
(2-4 white bold words at ~75% height, his style) to check timing before the real edit.

usage: python3 assemble_cut.py SHOTS_DIR OUT.mp4 [--captions] [--width 1080] [--fps 30] [--font F.ttf]
SHOTS_DIR holds one folder per shot (shot01 ... shot19b), each with f_0001.png ... directly
inside it (Blender's output) or in a frames/ subfolder.
Needs ffmpeg. Missing shots become labelled placeholders. Works on Windows, macOS and Linux.
"""
import argparse
import glob
import os
import shutil
import subprocess
import tempfile

CUT = [  # (folder, start s, end s) - slots follow SCRIPT_AND_SHOTS.md
    ("shot01", 0.0, 1.5), ("shot02", 1.5, 3.0), ("shot03", 3.0, 5.6), ("shot04", 5.6, 7.0),
    ("shot05", 7.0, 8.4), ("shot06", 8.4, 11.0), ("shot07", 11.0, 12.8), ("shot08", 12.8, 14.8),
    ("shot09", 14.8, 16.8), ("shot10", 16.8, 18.8), ("shot11", 18.8, 20.4), ("shot12", 20.4, 22.0),
    ("shot13", 22.0, 23.8), ("shot14", 23.8, 25.9), ("shot15", 25.9, 27.8), ("shot16", 27.8, 29.6),
    ("shot17", 29.6, 32.0), ("shot18", 32.0, 34.2), ("shot19a", 34.2, 35.4), ("shot19b", 35.4, 36.8),
]
SCRIPT = [  # (start s, end s, caption groups) - 1-4 words, broken where he would pause
    (0.0, 3.0, ["You take", "a giant bite", "of ice cream"]),
    (3.0, 5.2, ["and for a second", "it's perfect"]),
    (5.6, 8.4, ["Then a", "stabbing pain", "shoots through", "your forehead"]),
    (8.4, 10.6, ["like your brain", "is freezing solid"]),
    (11.0, 14.8, ["You see", "when something freezing", "hits the roof", "of your mouth"]),
    (14.8, 18.8, ["the blood vessels", "in your head", "squeeze tight", "to hold in heat"]),
    (18.8, 22.0, ["then suddenly", "rush wide open", "to warm back up"]),
    (22.0, 25.4, ["and that flood", "of blood", "sets off", "pain sensors"]),
    (25.9, 29.6, ["But the nerve", "carrying that signal", "also runs", "to your forehead"]),
    (29.6, 32.0, ["so that's where", "your brain feels it"]),
    (32.0, 36.8, ["leaving you", "with a frozen brain", "that isn't frozen", "at all"]),
]
FONTS = [  # first bold sans found is used for captions and placeholder labels
    r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def caption_filters(tmp, height):
    """drawtext filters: each line's groups share its time in proportion to their length.
    Text files and the font sit in tmp, which is ffmpeg's working folder, so the filter
    only holds relative names (Windows drive colons would break the filter syntax)."""
    filters = []
    k = 0
    for t0, t1, groups in SCRIPT:
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
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--font", help="bold .ttf for captions (default: Arial Bold / DejaVu Sans Bold)")
    a = ap.parse_args()
    W, H, fps = a.width, a.width * 16 // 9, a.fps
    font = next((f for f in ([a.font] if a.font else FONTS) if os.path.isfile(f)), None)
    if a.captions and not font:
        raise SystemExit("No caption font found: pass --font path/to/bold.ttf")
    inputs, parts = [], []
    for i, (name, t0, t1) in enumerate(CUT):
        slot = round((t1 - t0) * fps)
        folder = os.path.abspath(os.path.join(a.shots_dir, name))
        if os.path.isdir(os.path.join(folder, "frames")):
            folder = os.path.join(folder, "frames")
        frames = sorted(glob.glob(os.path.join(folder, "f_*.png")))
        if frames:
            inputs += ["-framerate", str(fps), "-start_number", "1", "-i", os.path.join(folder, "f_%04d.png")]
            hold = max(slot - len(frames), 0) / fps
            parts.append(f"[{i}:v]scale={W}:{H}:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop_duration={hold:.3f},"
                         f"trim=end_frame={slot},setpts=PTS-STARTPTS[v{i}]")
        else:
            inputs += ["-f", "lavfi", "-i", f"color=c=0x101418:s={W}x{H}:r={fps}:d={slot / fps:.3f}"]
            label = (f"drawtext=fontfile=font.ttf:text='{name} - not rendered':fontcolor=white:fontsize={H // 30}:"
                     f"x=(w-text_w)/2:y=(h-text_h)/2," if font else "")
            parts.append(f"[{i}:v]{label}trim=end_frame={slot},setpts=PTS-STARTPTS[v{i}]")
    graph = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(CUT))) + f"concat=n={len(CUT)}:v=1:a=0[cut]"
    out = os.path.abspath(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        if font:
            shutil.copyfile(font, os.path.join(tmp, "font.ttf"))
        last = "[cut]"
        if a.captions:
            graph += ";[cut]" + ",".join(caption_filters(tmp, H)) + "[capt]"
            last = "[capt]"
        cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", last, "-r", str(fps),
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               out]
        subprocess.run(cmd, check=True, cwd=tmp)
    print("wrote", out)


if __name__ == "__main__":
    main()
