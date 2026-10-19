"""Mix the voiceover, sound effects and music into the assembled brain-freeze video at the
times and levels in VOICEOVER.md and SOUND_EFFECTS.md, following the same timeline as
`assemble_cut.py --voiceover` (lines that run long push everything after them back). Every
line is brought to the same loudness, the music dips under the voice, and the result is set
to YouTube loudness (-14 LUFS).

usage: python3 mix_audio.py AUDIO_DIR VIDEO.mp4 OUT.mp4
AUDIO_DIR holds voiceover_01 ... voiceover_11, sfx_NN_name and music_01 files (.wav, .mp3,
.m4a ...); any of them may be missing. Build VIDEO.mp4 with assemble_cut.py --voiceover AUDIO_DIR.
Needs ffmpeg.
"""
import argparse
import math
import os
import subprocess

from timeline import SILENCE_DB, VO_TEMPO, Timeline, find_audio, loudness

RATE = 48000
VOICE_LUFS = -20                             # every voiceover line is brought to this level first
SFX = {  # number: [(planned time s, level dB relative to the voice), ...]
    2: [(0.5, -8)], 3: [(1.55, -10)], 4: [(2.6, -6), (36.5, -6)], 5: [(3.05, -16)], 6: [(5.55, -6)],
    7: [(5.8, -12)], 8: [(7.1, -6)], 9: [(7.2, -14)], 10: [(8.5, -8), (32.0, -14)],
    11: [(11.0, -10), (14.8, -12)], 12: [(13.0, -8)], 13: [(13.1, -10)],
    14: [(13.1, -14), (13.4, -14), (13.75, -14), (28.85, -10), (30.75, -10)], 16: [(17.0, -12)],
    17: [(18.85, -4)], 18: [(20.6, -14)], 19: [(22.0, -8)], 20: [(23.95, -8)], 21: [(26.05, -8)],
    22: [(29.65, -8)], 23: [(30.35, -12)], 24: [(32.0, -16)], 25: [(34.35, -4)],
}
BEDS = {  # looped beds: number: ([(planned start, planned end), ...], level dB)
    1: ([(0.0, 11.0), (29.6, 36.8)], -26),                     # park ambience
    15: ([(14.8, 22.8)], -16),                                 # heartbeat
}
MUSIC_DB = -12                               # under the voice; dips a further few dB while it talks


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "default=nw=1:nk=1", path], capture_output=True, text=True).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio_dir")
    ap.add_argument("video")
    ap.add_argument("out")
    a = ap.parse_args()
    files = find_audio(a.audio_dir)
    tl = Timeline.from_folder(a.audio_dir)
    length = duration(a.video)                                        # sound runs exactly as long as the picture
    inputs, chains, mix = ["-i", os.path.abspath(a.video)], [], []
    fmt = f"aformat=sample_rates={RATE}:channel_layouts=stereo"
    count = [1]                                                       # input 0 is the video

    def new_input(path, loop=False):
        inputs.extend((["-stream_loop", "-1"] if loop else []) + ["-i", os.path.abspath(path)])
        count[0] += 1
        return count[0] - 1

    def gain(path, db=0.0):                                           # match the voice level, then offset
        return VOICE_LUFS - loudness(path) + db

    vo = []
    for n in sorted(files["vo"]):
        if not 1 <= n <= len(tl.new):
            continue
        k, ms = new_input(files["vo"][n]), int(tl.line_start(n) * 1000)
        chains.append(f"[{k}:a]{fmt},silenceremove=start_periods=1:start_threshold={SILENCE_DB}dB,"
                      f"atempo={VO_TEMPO},volume={gain(files['vo'][n]):.2f}dB,adelay={ms}|{ms}[vo{n}]")
        vo.append(f"[vo{n}]")
    if vo:
        chains.append("".join(vo) + f"amix=inputs={len(vo)}:normalize=0,asplit=2[voice][duck]")
        mix.append("[voice]")
    for n, places in SFX.items():
        if n not in files["sfx"]:
            continue
        g = gain(files["sfx"][n])
        for j, (t, db) in enumerate(places):
            k, ms = new_input(files["sfx"][n]), int(tl.warp(t) * 1000)
            chains.append(f"[{k}:a]{fmt},volume={g + db:.2f}dB,adelay={ms}|{ms}[s{n}_{j}]")
            mix.append(f"[s{n}_{j}]")
    for n, (spans, db) in BEDS.items():
        if n not in files["sfx"]:
            continue
        src = files["sfx"][n]
        g, seg = gain(src), duration(src)
        for j, (t0, t1) in enumerate(spans):
            start, end = tl.warp(t0), min(tl.warp(t1), length)
            d, ms = end - start, int(start * 1000)
            # repeats overlap by a second and crossfade, so the loop never clicks at the seam
            copies = max(1, math.ceil((d - 1.0) / (seg - 1.0))) if seg > 2.0 else 1
            last = None
            for c in range(copies):
                k = new_input(src, loop=seg <= 2.0)
                chains.append(f"[{k}:a]{fmt}[b{n}_{j}_{c}]")
                if last is None:
                    last = f"[b{n}_{j}_{c}]"
                else:
                    chains.append(f"{last}[b{n}_{j}_{c}]acrossfade=d=1:c1=tri:c2=tri[b{n}_{j}_x{c}]")
                    last = f"[b{n}_{j}_x{c}]"
            chains.append(f"{last}atrim=0:{d:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.6,"
                          f"afade=t=out:st={max(d - 0.8, 0):.3f}:d=0.8,volume={g + db:.2f}dB,"
                          f"adelay={ms}|{ms}[b{n}_{j}]")
            mix.append(f"[b{n}_{j}]")
    if files["music"]:
        # a track up to 20% shorter than the edit is slowed to fit (same pitch) instead of restarting
        ratio = duration(files["music"]) / length
        fit = f"atempo={ratio:.4f}," if 0.8 <= ratio < 1.0 else ""
        k = new_input(files["music"], loop=not fit)
        chains.append(f"[{k}:a]{fmt},{fit}atrim=0:{length:.3f},asetpts=PTS-STARTPTS,"
                      f"afade=t=out:st={length - 1.2:.3f}:d=1.2,volume={gain(files['music'], MUSIC_DB):.2f}dB[mraw]")
        if vo:                                                        # dip the music while the voice talks
            chains.append("[mraw][duck]sidechaincompress=threshold=0.03:ratio=3:attack=40:release=500[music]")
        else:
            chains.append("[mraw]anull[music]")
        mix.append("[music]")
    elif vo:
        chains.append("[duck]anullsink")
    if not mix:
        raise SystemExit(f"No audio files found in {a.audio_dir}")
    chains.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=longest,"
                  f"apad=whole_dur={length:.3f},atrim=0:{length:.3f},loudnorm=I=-14:TP=-1.5:LRA=11,"
                  f"aresample={RATE}[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains), "-map", "0:v",
           "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
           os.path.abspath(a.out)]
    subprocess.run(cmd, check=True)
    print(tl.report())
    print("voiceover lines:", sorted(files["vo"]), "| sound effects:", sorted(files["sfx"]),
          "| music:", bool(files["music"]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
