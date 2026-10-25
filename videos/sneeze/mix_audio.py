"""Mix the voiceover, sound effects and music into the sneeze video at the times and levels in
timeline.py: each voiceover part is split into phrases that start on their cues, her sneeze
lands on the CHOO, every sound is brought to the same loudness as the voice and then offset,
the music dips under the voice, and the result is set to YouTube loudness (-14 LUFS).

usage: python3 mix_audio.py AUDIO_DIR VIDEO.mp4 OUT.mp4
AUDIO_DIR holds voiceover_1 ... voiceover_6, the sfx_* files and music (.wav, .mp3, .m4a ...);
any of them may be missing. Needs ffmpeg.
"""
import argparse
import os
import subprocess

from timeline import (BEDS, MUSIC_DB, PAD, PEAK, SFX, SILENCE_DB, SNEEZE, duration, find_audio, loudness,
                      peak_time, place_voice, sneeze_start)

RATE = 48000
VOICE_LUFS = -20                 # every voiceover part is brought to this level first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio_dir")
    ap.add_argument("video")
    ap.add_argument("out")
    a = ap.parse_args()
    files = find_audio(a.audio_dir)
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

    def at(t):
        ms = max(int(round(t * 1000)), 0)
        return f"adelay={ms}|{ms}"

    vo, report = [], []
    placed = place_voice(files["vo"])
    for j, (n, text, s, e, t) in enumerate(placed):                   # the narrator, phrase by phrase
        path = files["vo"][n]
        pre, post = min(PAD[0], s), PAD[1]
        k = new_input(path)
        chains.append(f"[{k}:a]{fmt},atrim={s - pre:.3f}:{e + post:.3f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.01,afade=t=out:st={e - s + pre + post - 0.03:.3f}:d=0.03,"
                      f"volume={gain(path):.2f}dB,{at(t - pre)}[vo{j}]")
        vo.append(f"[vo{j}]")
        report.append(f"  {t:6.2f}-{t + e - s:6.2f} s  voiceover_{n}: {text}")
    if SNEEZE in files["vo"]:                                         # her sneeze, on the CHOO
        path = files["vo"][SNEEZE]
        t = sneeze_start(path)
        k = new_input(path)
        chains.append(f"[{k}:a]{fmt},volume={gain(path, 1):.2f}dB,{at(t)}[sneeze]")
        mix.append("[sneeze]")
        report.append(f"  {t:6.2f} s  voiceover_{SNEEZE}: her sneeze (CHOO at {t + peak_time(path):.2f} s)")
    if vo:
        chains.append("".join(vo) + f"amix=inputs={len(vo)}:normalize=0,asplit=2[voice][duck]")
        mix.append("[voice]")
    for name, places in SFX.items():                                  # one-shots, from their first sound
        if name not in files["sfx"]:
            continue
        path = files["sfx"][name]
        g = gain(path)
        lead = peak_time(path) if name in PEAK else 0.0
        for j, (t, db) in enumerate(places):
            k = new_input(path)
            trim = "" if name in PEAK else f"silenceremove=start_periods=1:start_threshold={SILENCE_DB}dB,"
            chains.append(f"[{k}:a]{fmt},{trim}volume={g + db:.2f}dB,{at(t - lead)}[{name}{j}]")
            mix.append(f"[{name}{j}]")
    for name, (spans, db) in BEDS.items():                            # beds, trimmed to their spans
        if name not in files["sfx"]:
            continue
        path = files["sfx"][name]
        g = gain(path, db)
        for j, (t0, t1) in enumerate(spans):
            d = min(t1, length) - t0
            k = new_input(path, loop=True)
            chains.append(f"[{k}:a]{fmt},atrim=0:{d:.3f},asetpts=PTS-STARTPTS,"
                          f"afade=t=in:d={min(0.4, d / 3):.3f},afade=t=out:st={d - min(0.6, d / 3):.3f}:"
                          f"d={min(0.6, d / 3):.3f},volume={g:.2f}dB,{at(t0)}[{name}{j}]")
            mix.append(f"[{name}{j}]")
    if files["music"]:
        k = new_input(files["music"])
        chains.append(f"[{k}:a]{fmt},atrim=0:{length:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={length - 1.0:.3f}:"
                      f"d=1.0,volume={gain(files['music'], MUSIC_DB):.2f}dB[mraw]")
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
                  f"apad=whole_dur={length:.3f},atrim=0:{length:.3f},loudnorm=I=-14:TP=-3.0:LRA=11,"
                  f"aresample={RATE}[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains), "-map", "0:v",
           "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
           os.path.abspath(a.out)]
    subprocess.run(cmd, check=True)
    print("\n".join(report))
    print("voiceover parts:", sorted(files["vo"]), "| sound effects:", sorted(files["sfx"]),
          "| music:", bool(files["music"]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
