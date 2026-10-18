"""Shared timing for the brain-freeze edit: the planned shot slots and voiceover lines, and
how they stretch when a recorded line runs longer than planned. assemble_cut.py (picture and
captions) and mix_audio.py (sound) both use it, so everything stays in sync with the voice.
"""
import os
import re
import subprocess

LENGTH = 36.8                                # planned length (s)
CUT = [  # (folder, start s, end s) - slots follow SCRIPT_AND_SHOTS.md
    ("shot01", 0.0, 1.5), ("shot02", 1.5, 3.0), ("shot03", 3.0, 5.6), ("shot04", 5.6, 7.0),
    ("shot05", 7.0, 8.4), ("shot06", 8.4, 11.0), ("shot07", 11.0, 12.8), ("shot08", 12.8, 14.8),
    ("shot09", 14.8, 16.8), ("shot10", 16.8, 18.8), ("shot11", 18.8, 20.4), ("shot12", 20.4, 22.0),
    ("shot13", 22.0, 23.8), ("shot14", 23.8, 25.9), ("shot15", 25.9, 27.8), ("shot16", 27.8, 29.6),
    ("shot17", 29.6, 32.0), ("shot18", 32.0, 34.2), ("shot19a", 34.2, 35.4), ("shot19b", 35.4, 36.8),
]
SCRIPT = [  # voiceover_NN: (start s, end s, caption groups) - 1-4 words, broken where he would pause
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
MIN_GAP = 0.15                               # shortest breath between two recorded lines (s)
SILENCE_DB = -45                             # quieter than this counts as silence
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")


def _ffmpeg_log(path, af):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", af, "-f", "null", "-"],
                          capture_output=True, text=True).stderr


def speech_length(path):
    """Seconds of sound in a recording without the silence before and after it."""
    log = _ffmpeg_log(path, f"silencedetect=noise={SILENCE_DB}dB:d=0.15")
    h, m, sec = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log).groups()
    total = int(h) * 3600 + int(m) * 60 + float(sec)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    begin = ends[0] if starts and starts[0] <= 0.02 and ends else 0.0
    finish = starts[-1] if len(starts) > len(ends) else total         # silence running to the end
    return max(finish - begin, 0.1)


def loudness(path):
    """Integrated loudness in LUFS (mean level for clips too short to measure)."""
    log = _ffmpeg_log(path, "ebur128=framelog=quiet")
    found = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    if found and float(found[-1]) > -70:
        return float(found[-1])
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", _ffmpeg_log(path, "volumedetect"))
    return float(mean.group(1)) - 3.0 if mean else -23.0


def find_audio(folder):
    """{"vo": {n: path}, "sfx": {n: path}, "music": path} from loosely named files:
    voiceover_01.mp3, Voiceover 1.wav, 9430b88d-voiceover_1.mp3, sfx_02_spoon.wav, music_01.wav ..."""
    found = {"vo": {}, "sfx": {}, "music": None}
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            name, path = f.lower(), os.path.join(root, f)
            if not name.endswith(AUDIO_EXT):
                continue
            vo, sfx = re.search(r"voice\w*?[\s_-]*0*(\d+)", name), re.search(r"sfx[\s_-]*0*(\d+)", name)
            if "music" in name:
                found["music"] = found["music"] or path
            elif sfx:
                found["sfx"].setdefault(int(sfx.group(1)), path)
            elif vo:
                found["vo"].setdefault(int(vo.group(1)), path)
    return found


class Timeline:
    """Line i plays over the planned interval from its start to the next line's start. When
    its recording (plus the planned pause after it, at least MIN_GAP) is longer, that interval
    and every shot in it stretch to fit; later lines and shots move back. Nothing gets shorter."""

    def __init__(self, vo_lengths=None):
        vo_lengths = vo_lengths or {}
        starts = [t0 for t0, _, _ in SCRIPT] + [LENGTH]
        self.planned = list(zip(starts[:-1], starts[1:]))
        self.speech = dict(vo_lengths)
        self.new, t = [], 0.0
        for i, ((a, b), (_, t1, _)) in enumerate(zip(self.planned, SCRIPT)):
            need = vo_lengths[i + 1] + max(b - t1, MIN_GAP) if i + 1 in vo_lengths else 0.0
            length = max(b - a, need)
            self.new.append((t, t + length))
            t += length
        self.length = t

    @classmethod
    def from_folder(cls, folder):
        vo = find_audio(folder)["vo"] if folder else {}
        return cls({n: speech_length(p) for n, p in vo.items() if 1 <= n <= len(SCRIPT)})

    def warp(self, t):
        """Planned time (s) -> time in the stretched edit."""
        for (a, b), (A, B) in zip(self.planned, self.new):
            if t < b:
                return A + (max(t, a) - a) * (B - A) / (b - a)
        a, b = self.planned[-1]
        A, B = self.new[-1]
        return B + (t - b)

    def line_start(self, n):
        return self.new[n - 1][0]

    def caption_span(self, n):
        """When line n's captions show: while it is spoken, else its planned time."""
        if n in self.speech:
            return self.line_start(n), self.line_start(n) + self.speech[n]
        t0, t1, _ = SCRIPT[n - 1]
        return self.warp(t0), self.warp(t1)

    def report(self):
        rows = []
        for n, ((a, b), (A, B)) in enumerate(zip(self.planned, self.new), start=1):
            extra = (B - A) - (b - a)
            rows.append(f"line {n:2d}: {A:5.2f}-{B:5.2f} s" + (f"  (+{extra:.2f} s)" if extra > 0.005 else ""))
        return "\n".join(rows) + f"\ntotal {self.length:.2f} s (planned {LENGTH} s)"
