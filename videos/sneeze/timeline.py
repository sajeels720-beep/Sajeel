"""Shared timing for the sneeze edit: the shots as rendered, where each voiceover phrase starts,
when each caption shows and where each sound effect plays. assemble_cut.py (picture and
captions) and mix_audio.py (sound) both use it.

The picture is fixed (her acting runs across the cuts), so the voice is fitted to the picture:
each recorded part is split at its pauses into phrases, and each phrase starts on its cue, or
just after the phrase before it if that one runs long. Times are seconds in the finished video.
Needs only Python 3 and ffmpeg.
"""
import array
import math
import os
import re
import subprocess

FPS = 30
SHOTS = [("shot01", 36), ("shot02", 30), ("shot03", 60), ("shot04", 63), ("shot05", 48), ("shot06", 60),
         ("shot07", 57), ("shot08", 42), ("shot09", 42), ("shot10", 60), ("shot11", 48), ("shot12", 48),
         ("shot13", 42), ("shot14", 54), ("shot15", 42), ("shot16", 48), ("shot17", 60), ("shot18", 60),
         ("shot19", 66), ("shot20", 42), ("shot21", 48), ("shot22", 54)]   # (folder, frames)
LENGTH = sum(n for _, n in SHOTS) / FPS                                # 37.0 s

VOICEOVER = {  # voiceover_N: (cue s, phrase) for each phrase, in the order spoken; | breaks the captions
    1: [(0.05, "You feel a | giant sneeze | coming..."),
        (3.05, "so you pinch | your nose, | shut your mouth, | and hold it in."),  # after her "ahh... AHH":
                                                                            # "pinch" as her fingers close on her nose
        (6.30, "Big... | mistake.")],                                       # "Big" on the crash zoom
    2: [(8.35, "You see, | a sneeze blasts air | out of your lungs | super fast."),  # on the x-ray reveal
        (12.35, "With nowhere to go, | it gets trapped | inside you,"),    # as the air slams into her lips
        (15.15, "and the pressure | in your airways | jumps about | 20 times higher.")],  # "twenty": the gauge
    3: [(18.50, "That air shoots up | the tiny tubes | to your ears,"),
        (21.80, "and can burst | your eardrums,"),                          # "burst" just before it pops
        (23.75, "or pop the | blood vessels | in your eyes.")],            # "pop" as the vessels swell up
    4: [(26.00, "But, | in rare cases..."),
        (28.20, "it can even | tear a hole | in your throat.")],            # "tear" on the rip
    5: [(30.45, "So next time | you feel one coming,"),
        (32.50, "just let it out.")],                                       # as she lets go of her nose
}
CAPTION_STARTS = {  # (part, phrase): (its length s, where its 2nd, 3rd ... caption starts, s into it), measured on
    # these recordings (word timings, snapped to pauses). A part recorded again (another length) falls back to
    # spreading its captions over its sound by their letters.
    (1, 0): (2.02, [0.58, 1.66]), (1, 1): (3.20, [0.50, 1.30, 2.38]), (1, 2): (1.88, [1.04]),
    (2, 0): (3.79, [0.78, 2.06, 2.74]), (2, 1): (2.59, [1.17, 1.80]), (2, 2): (3.25, [0.49, 1.31, 2.05]),
    (3, 0): (2.87, [1.18, 1.96]), (3, 1): (1.46, [0.58]), (3, 2): (2.01, [0.63, 1.19]),
    (4, 0): (1.90, [0.77]), (4, 1): (2.07, [0.60, 1.28]),
    (5, 0): (1.83, [0.72]), (5, 1): (1.13, []),
}
SNEEZE = 6                      # voiceover_6 is her sneeze: its hit (the CHOO) lands on CHOO
CHOO = 34.17                     # her head snaps forward (shot 21)
MIN_GAP = 0.15                   # a phrase never starts sooner than this after the one before
SILENCE_DB = -38                 # quieter than this counts as a pause
PAD = (0.04, 0.08)               # kept before and after each phrase, so no consonant is clipped

SFX = {  # sfx_name: [(time s, level dB against the voice[, until s[, fade s]]), ...]: its hit (hit_time) lands on
         # the time (its first sound, for START); until cuts it off at that time in the video, fading out over fade
    "sfx_ahh": [(2.98, -6, 3.24),                    # "ahh... AHH" cut off as her fingers close on her nose
                (33.45, -10)],                       # under "just let it out": "ahh..." 32.8, "AHH" 33.4
    "sfx_stifled": [(4.63, -6), (5.57, -12)],        # the sneeze hits inside, then a smaller hiccup
    "sfx_sniff": [(1.75, -12), (1.92, -14), (31.05, -10), (36.12, -4)],
    "sfx_whoosh_soft": [(0.50, -14), (1.45, -14), (30.80, -14), (35.70, -10)],   # seeds drifting
    "sfx_whoosh_fast": [(3.15, -10), (6.36, -6), (16.98, -10), (32.40, -12), (34.28, -8)],  # hand up, zooms, let go
    "sfx_tap": [(1.63, -10, 1.75), (30.97, -10, 31.09)],   # just the tap, not the hiss after it
    "sfx_pinch": [(3.32, -10)],                              # her fingers squeeze her nose
    "sfx_puff": [(4.63, -8), (12.20, -8)],                   # her cheeks balloon
    "sfx_thump": [(4.60, -6), (12.18, -4)],                  # the sneeze hits inside; the air slams into her lips
    "sfx_boom": [(6.33, -4), (16.97, -8), (22.30, -6), (28.77, -6), (34.17, -4)],  # Big mistake, gauge, eardrum,
                                                                                   # throat, CHOO
    "sfx_alert_pop": [(6.43, -6)],                           # the red "!"
    "sfx_xray_scan": [(8.00, -10), (19.85, -12)],            # the x-ray reveals
    "sfx_air_rush": [(9.00, -8)],                            # the blast up her windpipe, loudest at the top
    "sfx_air_hiss": [(18.20, -8)],                           # air up the tubes to her ears
    "sfx_stretch": [(14.60, -12, 16.40),                     # the throat wall bulging (shot 10)
                    (20.85, -12, 22.30),                     # the eardrum straining, cut off as it pops
                    (27.33, -10, 28.77)],                    # the blister straining, cut off as it rips
    "sfx_heartbeat": [(13.57, -10), (14.17, -10), (23.37, -8), (23.77, -8), (24.17, -8), (26.30, -8), (26.77, -8),
                      (27.23, -8), (27.70, -8)],             # the pressure throbbing
    "sfx_gauge": [(16.97, -6)],                              # the needle hits its stop
    "sfx_glass_crack": [(16.97, -8), (26.40, -18), (27.00, -18)],  # the gauge glass; the red cracks creeping
    "sfx_membrane_pop": [(22.30, -4)],
    "sfx_ear_ring": [(22.35, -14, 23.40, 0.8)],             # ringing after the eardrum pops, dying away
    "sfx_wet_pop": [(24.70, -6)],                            # the vessel in her eye pops
    "sfx_tension_drone": [(25.95, -14, 28.80)],              # rising under the weak spot, cut dead by the rip
    "sfx_tear": [(28.77, -4)],                               # the throat wall rips
    "sfx_slowmo_blast": [(34.27, -6)],                       # the slow-motion blast hitting the dandelion
    "sfx_seeds_poof": [(34.27, -8)],
}
START = {"sfx_xray_scan", "sfx_air_rush", "sfx_air_hiss", "sfx_stretch", "sfx_ear_ring",
         "sfx_tension_drone"}    # long sounds: they start on their time
BEDS = {  # sfx_name: ([(start s, end s), ...], level dB): trimmed to each span, faded in and out
    "sfx_breeze": ([(0.0, 1.4), (35.0, LENGTH)], -20),
    "sfx_air_swirl": ([(13.2, 16.6)], -14),
}
MUSIC_DB = -12                   # under the voice; dips a few dB more while it talks
MUSIC_BUTTON = 36.45             # the music's last big hit lands here, on her smile (it is stretched a little)
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


def levels(path, window=0.02):
    """The level (dB) of each `window` seconds of a recording."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = array.array("f")
    x.frombytes(raw[:len(raw) // 4 * 4])
    w = int(16000 * window)
    return [10 * math.log10(sum(v * v for v in x[i:i + w]) / w + 1e-18) for i in range(0, len(x) - w + 1, w)]


def hit_time(path, within=6.0):
    """When a recording hits (s): the first 20 ms that come within `within` dB of its loudest (leaving out
    its last 60 ms, where a cut-off file often clicks)."""
    db = levels(path)[:-3]
    top = max(db)
    return next(i for i, d in enumerate(db) if d >= top - within) * 0.02


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
            segs, cues = [(segs[0][0], segs[-1][1])], [(cues[0][0], " | ".join(t for _, t in cues))]
        for (cue, text), (a, b) in zip(cues, segs):
            start = max(cue, prev_end + MIN_GAP)
            placed.append((n, text, a, b, start))
            prev_end = start + (b - a)
    return placed


def button_time(path):
    """A music track's last big hit (s): its loudest 0.1 s in the last fifth of the track."""
    db = levels(path, 0.1)
    first = int(len(db) * 0.8)
    return max(range(first, len(db)), key=lambda i: db[i]) * 0.1


def captions(vo_files):
    """When each caption shows: [(start s, end s, words)]. Each group comes up as it is spoken (at
    CAPTION_STARTS, or else its phrase's sound, pauses left out, shared by the groups' letters) and
    stays until the next; the last one of a phrase stays a moment after it."""
    placed = place_voice(vo_files)
    pauses = {n: sound_span(path)[2] for n, path in vo_files.items()}
    out, count = [], {}
    for k, (n, text, s, e, t) in enumerate(placed):
        j = count[n] = count.get(n, -1) + 1                           # the phrase's number within its part
        spoken, at = [], s                                            # the phrase's sound, without its pauses
        for a, b in pauses[n]:
            if s < b and a < e:
                if a > at:
                    spoken.append((at, a))
                at = max(at, b)
        if at < e:
            spoken.append((at, e))
        total = sum(b - a for a, b in spoken)

        def when(x):                                                  # x seconds into its sound -> video time
            for a, b in spoken:
                if x <= b - a:
                    return t + a + x - s
                x -= b - a
            return t + e - s
        groups = [g.strip() for g in text.split("|")]
        length, measured = CAPTION_STARTS.get((n, j), (0.0, []))
        if abs(length - (e - s)) < 0.05 and len(measured) == len(groups) - 1:
            starts = [t] + [t + x for x in measured]
        else:                                                         # a digit is said with about 3 letters
            sizes = [sum(c.isalpha() + 3 * c.isdigit() for c in g) for g in groups]
            starts = [when(total * sum(sizes[:i]) / sum(sizes)) for i in range(len(groups))]
        after = placed[k + 1][4] if k + 1 < len(placed) else LENGTH
        ends = starts[1:] + [min(t + e - s + 0.3, after)]
        out += zip(starts, ends, groups)
    return out


def sneeze_start(path):
    """Where her sneeze starts in the video, so its CHOO lands on the frame her head snaps forward."""
    return CHOO - hit_time(path)
