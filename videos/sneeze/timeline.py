"""Shared timing for the sneeze edit: the shots as rendered, where each voiceover phrase starts
and where each sound effect plays. mix_audio.py uses it.

The picture is fixed (her acting runs across the cuts), so the voice is fitted to the picture:
each recorded part is split at its pauses into phrases, and each phrase starts on its cue, or
just after the phrase before it if that one runs long. Times are seconds in the finished video.
"""
import os
import re
import subprocess

import numpy as np

FPS = 30
SHOTS = [("shot01", 36), ("shot02", 30), ("shot03", 60), ("shot04", 63), ("shot05", 48), ("shot06", 60),
         ("shot07", 57), ("shot08", 42), ("shot09", 42), ("shot10", 60), ("shot11", 48), ("shot12", 48),
         ("shot13", 42), ("shot14", 54), ("shot15", 42), ("shot16", 48), ("shot17", 60), ("shot18", 60),
         ("shot19", 66), ("shot20", 42), ("shot21", 48), ("shot22", 54)]   # (folder, frames)
LENGTH = sum(n for _, n in SHOTS) / FPS                                # 37.0 s

VOICEOVER = {  # voiceover_N: (cue s, phrase) for each phrase, in the order spoken
    1: [(0.05, "You feel a giant sneeze coming..."),
        (3.05, "so you pinch your nose, shut your mouth, and hold it in."),  # after her "ahh... AHH": "pinch"
                                                                            # as her fingers close on her nose
        (6.30, "Big... mistake.")],                                         # "Big" on the crash zoom
    2: [(8.35, "You see, a sneeze blasts air out of your lungs super fast."),  # on the x-ray reveal
        (12.35, "With nowhere to go, it gets trapped inside you,"),        # as the air slams into her lips
        (15.15, "and the pressure in your airways jumps about twenty times higher.")],  # "twenty": the gauge slams
    3: [(18.50, "That air shoots up the tiny tubes to your ears,"),
        (21.80, "and can burst your eardrums,"),                            # "burst" just before it pops
        (23.75, "or pop the blood vessels in your eyes.")],                # "pop" as the vessels swell up
    4: [(26.00, "But, in rare cases..."),
        (28.20, "it can even tear a hole in your throat.")],                # "tear" on the rip
    5: [(30.45, "So next time you feel one coming,"),
        (32.50, "just let it out.")],                                       # as she lets go of her nose
}
SNEEZE = 6                       # voiceover_6 is her sneeze: its loudest moment lands on CHOO
CHOO = 34.17                     # her head snaps forward (shot 21)
MIN_GAP = 0.15                   # a phrase never starts sooner than this after the one before
SILENCE_DB = -38                 # quieter than this counts as a pause
PAD = (0.04, 0.08)               # kept before and after each phrase, so no consonant is clipped

SFX = {  # sfx_name: [(time s, level dB against the voice[, cut s]), ...]: its loudest moment lands on the time
         # (its first sound, for START); cut ends the sound that far into its file
    "sfx_ahh": [(2.98, -6, 1.22),                    # "ahh... AHH" cut off as her fingers close on her nose
                (33.45, -10)],                       # under "just let it out": "ahh..." 32.8, "AHH" 33.4
    "sfx_stifled": [(4.63, -6), (5.57, -12)],        # the sneeze hits inside, then a smaller hiccup
    "sfx_sniff": [(1.75, -12), (1.92, -14), (31.05, -10), (36.12, -4)],
    "sfx_whoosh_soft": [(0.50, -14), (1.45, -14), (30.80, -14), (35.70, -10)],   # seeds drifting
    "sfx_whoosh_fast": [(3.15, -10), (6.36, -6), (16.98, -8), (32.40, -12), (34.28, -8)],  # hand up, zooms, let go
    "sfx_tap": [(1.63, -10), (30.97, -10)],
    "sfx_pinch": [(3.32, -10)],
    "sfx_puff": [(4.63, -6), (12.20, -8)],
    "sfx_thump": [(4.60, -4), (12.18, -4)],
    "sfx_boom": [(6.33, -4), (16.97, -6), (22.30, -6), (28.77, -6), (34.17, -4)],
    "sfx_alert_pop": [(6.43, -6)],
    "sfx_xray_scan": [(8.00, -10), (19.85, -12)],
    "sfx_air_rush": [(9.00, -8)],
    "sfx_air_hiss": [(18.20, -10)],
    "sfx_stretch": [(14.97, -12), (15.77, -12), (20.37, -12), (21.63, -10), (28.23, -10)],
    "sfx_heartbeat": [(13.57, -10), (14.17, -10), (23.37, -8), (23.77, -8), (24.17, -8), (26.30, -8), (26.77, -8),
                      (27.23, -8), (27.70, -8)],
    "sfx_gauge": [(16.97, -6)],
    "sfx_glass_crack": [(16.97, -6), (26.40, -18), (27.00, -18)],
    "sfx_membrane_pop": [(22.30, -4)],
    "sfx_ear_ring": [(22.35, -18)],
    "sfx_wet_pop": [(24.70, -6)],
    "sfx_tear": [(28.77, -4)],
    "sfx_slowmo_blast": [(34.15, -6)],
    "sfx_seeds_poof": [(34.27, -8)],
}
START = {"sfx_xray_scan", "sfx_air_rush", "sfx_air_hiss", "sfx_ear_ring", "sfx_slowmo_blast"}  # long sweeps
BEDS = {  # sfx_name: ([(start s, end s), ...], level dB): trimmed to each span, faded in and out
    "sfx_breeze": ([(0.0, 1.4), (35.0, LENGTH)], -20),
    "sfx_air_swirl": ([(13.2, 16.6)], -14),
    "sfx_tension_drone": ([(26.0, 28.9)], -16),
}
MUSIC_DB = -14                   # under the voice; dips a few dB more while it talks
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")


def _ffmpeg_log(path, af):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", af, "-f", "null", "-"],
                          capture_output=True, text=True).stderr


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "default=nw=1:nk=1", path], capture_output=True, text=True).stdout)


def loudness(path):
    """Integrated loudness in LUFS (mean level for clips too short to measure)."""
    log = _ffmpeg_log(path, "ebur128=framelog=quiet")
    found = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    if found and float(found[-1]) > -70:
        return float(found[-1])
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", _ffmpeg_log(path, "volumedetect"))
    return float(mean.group(1)) - 3.0 if mean else -23.0


def sound_span(path, db=SILENCE_DB):
    """(first sound, last sound, [(pause start, pause end), ...]) in seconds."""
    log = _ffmpeg_log(path, f"silencedetect=noise={db}dB:d=0.1")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    total = duration(path)
    pauses = list(zip(starts, ends + [total] * (len(starts) - len(ends))))
    first = pauses[0][1] if pauses and pauses[0][0] <= 0.02 else 0.0
    last = pauses[-1][0] if pauses and pauses[-1][1] >= total - 0.02 else total
    inner = [(a, b) for a, b in pauses if a > first and b < last]
    return max(first, 0.0), last, inner


def phrases(path, count):
    """Split a recording into `count` phrases at its longest pauses: [(start, end), ...]."""
    first, last, inner = sound_span(path)
    cuts = sorted(sorted(inner, key=lambda p: p[1] - p[0], reverse=True)[:count - 1])
    bounds = [first] + [x for a, b in cuts for x in (a, b)] + [last]
    return [(bounds[2 * i], bounds[2 * i + 1]) for i in range(len(bounds) // 2)]


def peak_time(path):
    """When a recording is loudest (s), from 20 ms windows."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    w = 320
    rms = np.sqrt(np.mean(x[:len(x) // w * w].reshape(-1, w) ** 2, axis=1))
    return float(np.argmax(rms)) * w / 16000


def find_audio(folder):
    """{"vo": {n: path}, "sfx": {name: path}, "music": path} from loosely named files:
    voiceover_1.mp3, Voiceover 2.wav, eaa4e770-voiceover_1.mp3.mp3, sfx_boom.wav, music.mp3 ..."""
    found = {"vo": {}, "sfx": {}, "music": None}
    names = sorted(set(SFX) | set(BEDS), key=len, reverse=True)       # longest first: sfx_whoosh_fast before ...
    for root, _, files in os.walk(folder or ""):
        for f in sorted(files):
            name, path = f.lower(), os.path.join(root, f)
            if not name.endswith(AUDIO_EXT):
                continue
            vo = re.search(r"voice\w*?[\s_-]*0*(\d+)", name)
            if "music" in name:
                found["music"] = found["music"] or path
            elif "sfx" in name:
                hit = next((n for n in names if n in name.replace(" ", "_").replace("-", "_")), None)
                if hit:
                    found["sfx"].setdefault(hit, path)
            elif vo:
                found["vo"].setdefault(int(vo.group(1)), path)
    return found


def place_voice(vo_files):
    """Where every phrase goes: [(part, text, start in the file, end in the file, start in the video)]."""
    placed, prev_end = [], -MIN_GAP
    for n in sorted(VOICEOVER):
        if n not in vo_files:
            continue
        cues = VOICEOVER[n]
        segs = phrases(vo_files[n], len(cues))
        if len(segs) != len(cues):                                     # fewer pauses than phrases: keep it whole
            segs, cues = [(segs[0][0], segs[-1][1])], [(cues[0][0], " ".join(t for _, t in cues))]
        for (cue, text), (a, b) in zip(cues, segs):
            start = max(cue, prev_end + MIN_GAP)
            placed.append((n, text, a, b, start))
            prev_end = start + (b - a)
    return placed


def sneeze_start(path):
    """Where her sneeze starts in the video, so its CHOO lands on the frame her head snaps forward."""
    return CHOO - peak_time(path)
