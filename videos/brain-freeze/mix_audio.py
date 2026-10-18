"""Mix the voiceover, sound effects and music into the assembled brain-freeze video at the
times and levels in VOICEOVER.md and SOUND_EFFECTS.md, duck the music under the voice and
bring the result to YouTube loudness (-14 LUFS).

usage: python3 mix_audio.py AUDIO_DIR VIDEO.mp4 OUT.mp4
AUDIO_DIR holds voiceover_01 ... voiceover_11, sfx_NN_name and music_01 files (.wav, .mp3,
.m4a ...); any of them may be missing. Needs ffmpeg.
"""
import argparse
import os
import re
import subprocess

LENGTH = 36.8
RATE = 48000
VO_START = [0.0, 3.0, 5.6, 8.4, 11.0, 14.8, 18.8, 22.0, 25.9, 29.6, 32.0]   # voiceover_01 ... _11
SFX = {  # number: [(start s, level dB relative to the voice), ...]
    2: [(0.5, -8)], 3: [(1.55, -10)], 4: [(2.6, -6), (36.5, -6)], 5: [(3.05, -16)], 6: [(5.55, -6)],
    7: [(5.8, -12)], 8: [(7.1, -6)], 9: [(7.2, -14)], 10: [(8.5, -8), (32.0, -14)],
    11: [(11.0, -10), (14.8, -12)], 12: [(13.0, -8)], 13: [(13.1, -10)],
    14: [(13.1, -14), (13.4, -14), (13.75, -14), (28.85, -10), (30.75, -10)], 16: [(17.0, -12)],
    17: [(18.85, -4)], 18: [(20.6, -14)], 19: [(22.0, -8)], 20: [(23.95, -8)], 21: [(26.05, -8)],
    22: [(29.65, -8)], 23: [(30.35, -12)], 24: [(32.0, -16)], 25: [(34.35, -4)],
}
BEDS = {  # looped beds: number: ([(start, end), ...], level dB)
    1: ([(0.0, 11.0), (29.6, LENGTH)], -26),                   # park ambience
    15: ([(14.8, 22.8)], -16),                                 # heartbeat
}
MUSIC_DB = -24
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")


def find_files(folder):
    """{"vo": {n: path}, "sfx": {n: path}, "music": path} from loosely named files
    (voiceover_01.mp3, Voiceover 1.wav, sfx_02_spoon_scoop.wav, music_01.wav ...)."""
    found = {"vo": {}, "sfx": {}, "music": None}
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if not f.lower().endswith(AUDIO_EXT):
                continue
            name, path = f.lower(), os.path.join(root, f)
            num = re.search(r"(\d+)", name)
            if name.startswith("music"):
                found["music"] = found["music"] or path
            elif name.startswith("sfx") and num:
                found["sfx"].setdefault(int(num.group(1)), path)
            elif ("voice" in name or name.startswith("vo")) and num:
                found["vo"].setdefault(int(num.group(1)), path)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio_dir")
    ap.add_argument("video")
    ap.add_argument("out")
    a = ap.parse_args()
    files = find_files(a.audio_dir)
    inputs, chains, mix = ["-i", os.path.abspath(a.video)], [], []
    fmt = f"aformat=sample_rates={RATE}:channel_layouts=stereo"
    n_in = 1                                                          # input 0 is the video

    def new_input(path, loop=False):
        nonlocal n_in
        inputs.extend((["-stream_loop", "-1"] if loop else []) + ["-i", os.path.abspath(path)])
        n_in += 1
        return n_in - 1

    vo = []
    for n, t in enumerate(VO_START, start=1):
        if n in files["vo"]:
            k = new_input(files["vo"][n])
            ms = int(t * 1000)
            chains.append(f"[{k}:a]{fmt},silenceremove=start_periods=1:start_threshold=-45dB,"
                          f"adelay={ms}|{ms}[vo{n}]")
            vo.append(f"[vo{n}]")
    if vo:
        chains.append("".join(vo) + f"amix=inputs={len(vo)}:normalize=0,asplit=2[voice][duck]")
        mix.append("[voice]")
    for n, places in SFX.items():
        if n not in files["sfx"]:
            continue
        for j, (t, db) in enumerate(places):
            k = new_input(files["sfx"][n])
            ms = int(t * 1000)
            chains.append(f"[{k}:a]{fmt},volume={db}dB,adelay={ms}|{ms}[s{n}_{j}]")
            mix.append(f"[s{n}_{j}]")
    for n, (spans, db) in BEDS.items():
        if n not in files["sfx"]:
            continue
        for j, (t0, t1) in enumerate(spans):
            k = new_input(files["sfx"][n], loop=True)
            d, ms = t1 - t0, int(t0 * 1000)
            chains.append(f"[{k}:a]{fmt},atrim=0:{d:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.6,"
                          f"afade=t=out:st={max(d - 0.8, 0):.3f}:d=0.8,volume={db}dB,adelay={ms}|{ms}[b{n}_{j}]")
            mix.append(f"[b{n}_{j}]")
    if files["music"]:
        k = new_input(files["music"], loop=True)
        chains.append(f"[{k}:a]{fmt},atrim=0:{LENGTH},asetpts=PTS-STARTPTS,afade=t=out:st={LENGTH - 1.2}:d=1.2,"
                      f"volume={MUSIC_DB}dB[mraw]")
        if vo:                                                        # dip the music while the voice talks
            chains.append("[mraw][duck]sidechaincompress=threshold=0.02:ratio=5:attack=30:release=400[music]")
        else:
            chains.append("[mraw]anull[music]")
        mix.append("[music]")
    elif vo:
        chains.append("[duck]anullsink")
    if not mix:
        raise SystemExit(f"No audio files found in {a.audio_dir}")
    chains.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=longest,"
                  f"apad=whole_dur={LENGTH},atrim=0:{LENGTH},loudnorm=I=-14:TP=-1.5:LRA=11,"
                  f"aresample={RATE}[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains), "-map", "0:v",
           "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
           os.path.abspath(a.out)]
    subprocess.run(cmd, check=True)
    print("voiceover lines:", sorted(files["vo"]), "| sound effects:", sorted(files["sfx"]),
          "| music:", bool(files["music"]))
    missing = [n for n in range(1, 12) if n not in files["vo"]]
    if missing:
        print("missing voiceover lines:", missing)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
