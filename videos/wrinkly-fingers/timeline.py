"""Shared timing for the wrinkly-fingers edit: the shots as rendered, where each voiceover phrase
starts, when each caption shows and where each sound effect plays. assemble_cut.py (picture and
captions) and mix_audio.py (sound) both use it.

The picture is fixed (his acting runs across the cuts), so the voice is fitted to the picture:
each recorded part is split at its pauses into phrases, and each phrase starts on its cue, or
just after the phrase before it if that one runs long. Times are seconds in the finished video.
Needs only Python 3 and ffmpeg. (Adapted from the sneeze video's.)
"""
import array
import math
import os
import re
import subprocess

FPS = 30
SHOTS = [("shot01", 69), ("shot02", 39), ("shot03", 45), ("shot04", 42), ("shot05", 45), ("shot06", 36),
         ("shot07", 33), ("shot08", 45), ("shot09", 39), ("shot10", 39), ("shot11", 63), ("shot12", 33),
         ("shot13", 72), ("shot14", 42), ("shot15", 45), ("shot16", 63)]   # (folder, frames)
LENGTH = sum(n for _, n in SHOTS) / FPS                                # 25.0 s

VOICEOVER = {  # voiceover_N: (cue s, phrase) for each phrase, in the order spoken; | breaks the captions
    1: [(0.10, "You stay | in the pool | too long,"),
        (2.35, "and your fingers | turn into | wrinkly raisins."),           # "raisins" on the crash zoom (4.5)
        (5.10, "It's not just | the water..."),                             # the drops soak in
        (6.55, "It's your nerves.")],                                       # "nerves" as they light up (7.1)
    2: [(8.00, "You see, | water sets off | your nerves,"),               # on the skin macro
        (10.35, "which squeeze | the blood vessels | under your skin."),     # "squeeze" on the crash zoom (10.6)
        (13.10, "Your fingertips | shrink,"),                               # the pad shrinks (13.2-14.1)
        (14.40, "and the skin | crumples | into wrinkles.")],               # "wrinkles" on the crash zoom (15.7)
    3: [(16.50, "But why?"),                                                # the red "?" pops (16.8)
        (17.60, "Scientists think | wrinkles grip | wet things better..."),  # the pinch under water (18.6)
        (20.10, "like | tyre treads.")],                                    # the tyre
    4: [(21.40, "So those | raisin fingers?"),                              # the marble to the sun
        (22.90, "Built-in | rain tyres.")],                                 # the toss (23.2)
}
CAPTION_STARTS = {}  # (part, phrase): (its length s, where its 2nd, 3rd ... caption starts, s into it), measured on
# the recordings once they exist (word timings, snapped to pauses); until then the captions are spread over each
# phrase's sound by their letters.
MIN_GAP = 0.15                   # a phrase never starts sooner than this after the one before
SILENCE_DB = -38                 # quieter than this counts as a pause
PAD = (0.04, 0.08)               # kept before and after each phrase, so no consonant is clipped

SFX = {  # sfx_name: [(time s, level dB against the voice[, until s[, fade s]]), ...]: its hit (hit_time) lands on
         # the time (its first sound, for START); until cuts it off at that time in the video, fading out over fade
    "sfx_timelapse": [(0.05, -14, 2.30, 0.3)],                # shot 1 runs fast
    "sfx_splash_small": [(2.78, -8), (23.75, -6)],            # his hand out of the water; the marble plops in
    "sfx_drips": [(3.00, -16, 3.60), (21.60, -16, 22.90)],   # water off his fingers
    "sfx_whoosh_fast": [(4.50, -8), (7.12, -8), (10.57, -8), (15.68, -8), (23.20, -12)],  # crash zooms; the toss
    "sfx_boom": [(7.22, -6), (10.68, -6)],                    # under "nerves" and "squeeze"
    "sfx_alert_pop": [(5.90, -6), (16.80, -6)],               # his red "?"
    "sfx_sigh": [(24.25, -6)],                                # he leans back at sunset
    "sfx_crinkle": [(3.73, -10, 4.75), (13.20, -12, 14.10), (14.43, -10, 15.70)],   # the skin puckers
    "sfx_drop_plink": [(5.30, -8), (5.43, -10), (5.57, -8), (5.70, -10)],          # drops land on his fingertips
    "sfx_seep": [(8.07, -12, 9.00)],                          # drops drain into the pores
    "sfx_xray_scan": [(6.50, -10)],                           # the x-ray reveal
    "sfx_zap": [(6.75, -12), (9.37, -6), (10.47, -10)],       # nerves light; the ending sparks; the fibres light
    "sfx_signal": [(7.20, -12), (9.40, -10)],                 # pulses race along the nerves
    "sfx_squeeze": [(10.60, -6)],                             # the vessels clamp down
    "sfx_heartbeat": [(11.05, -10), (11.55, -12)],            # the blood slows
    "sfx_drain": [(12.00, -12, 12.85)],                       # the vessels drain
    "sfx_marble_click": [(18.65, -10)],                       # his fingertips pinch the marble off the tiles
    "sfx_tyre_splash": [(20.00, -6)],                         # the tyre through the water
    "sfx_glint": [(21.50, -8)],                               # the marble glints in the sun
}
START = {"sfx_timelapse", "sfx_drips", "sfx_crinkle", "sfx_seep", "sfx_xray_scan", "sfx_drain",
         "sfx_tyre_splash"}      # long sounds: they start on their time
BEDS = {  # sfx_name: ([(start s, end s), ...], level dB): trimmed to each span, faded in and out
    "sfx_pool": ([(0.0, 3.6), (16.5, 17.6), (21.4, LENGTH)], -18),
    "sfx_underwater": ([(17.6, 20.0)], -12),
}
MUSIC_DB = -12                   # under the voice; dips a few dB more while it talks
MUSIC_BUTTON = 24.55             # the music's last big hit lands here, as he leans back (it is stretched a little)
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
    """When each caption shows: [(start s, end s, words without punctuation)]. Each group comes up
    as it is spoken (at CAPTION_STARTS, or else its phrase's sound, pauses left out, shared by the
    groups' letters) and stays until the next; the last one of a phrase stays a moment after it."""
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
        out += zip(starts, ends, (re.sub(r"[^\w\s]", "", g).strip() for g in groups))   # no punctuation
    return out
