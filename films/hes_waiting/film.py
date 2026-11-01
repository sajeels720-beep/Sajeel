"""'He's Waiting. | An Animated Short Film' - picture assembly."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import act1  # noqa: E402
from cues import COUNTERS, DURATION, EV, NARRATOR, SPEECH  # noqa: E402
from engine.captions import counter, narrator  # noqa: E402
from engine.core import H, W, smooth  # noqa: E402
from engine.draw import fade  # noqa: E402
from engine.render import Film  # noqa: E402

try:
    import act2  # noqa: E402
except ImportError:  # acts are added as they are written
    act2 = None
try:
    import act3  # noqa: E402
except ImportError:
    act3 = None


def overlays(c, T):
    for s, t0, t1 in NARRATOR:
        narrator(c, T, s, t0, t1)
    for label, t0, t1 in COUNTERS:
        counter(c, T, label, t0, t1)
    for s, t0, t1, who in SPEECH:
        # spoken lines: warmer and larger than the narrator, so they read as a voice
        narrator(c, T, s, t0, t1 + 0.5, size=76, color='#FFE9C2')


def post(c, T):
    a = 1 - smooth(0.15, 0.7, T)                       # up from black
    a = max(a, smooth(EV['black'] - 0.5, EV['black'], T) * (1 - smooth(EV['dawn'] - 0.1, EV['dawn'] + 1.2, T)))
    a = max(a, smooth(211.0, 211.9, T))                # out
    fade(c, W, H, a)


def build():
    shots = act1.shots()
    if act2:
        shots += act2.shots()
    if act3:
        shots += act3.shots()
    shots.sort(key=lambda s: s.start)
    extra_overlays = [act.overlays for act in (act1, act2, act3) if act and hasattr(act, 'overlays')]
    return Film(DURATION, shots, overlays=[overlays] + extra_overlays, post=[post])
