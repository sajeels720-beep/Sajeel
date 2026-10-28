"""'90 Days Left. | An Animated Short Film' - picture assembly."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import act1  # noqa: E402
from cues import COUNTERS, DURATION, EV, LAPSE_FLASH, NARRATOR  # noqa: E402
from engine.captions import counter, narrator  # noqa: E402
from engine.core import H, W, beat_env, smooth  # noqa: E402
from engine.draw import fade  # noqa: E402
from engine.fx import flash  # noqa: E402
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


def post(c, T):
    # fade up from black, the blackout before 5 AM, the dip into the title, fade out
    a = 1 - smooth(0.0, 1.0, T)
    a = max(a, smooth(EV['blackout'], 49.95, T) * (1 - smooth(50.0, 50.3, T)))
    a = max(a, smooth(147.2, 147.95, T) * (1 - smooth(148.0, 148.5, T)))
    a = max(a, smooth(158.6, 159.9, T))
    fade(c, W, H, a)
    flash(c, W, H, 0.22 * beat_env(T, LAPSE_FLASH, 0.1) + 0.75 * beat_env(T, [EV['drop']], 0.15)
          + 0.4 * beat_env(T, [EV['release']], 0.25)
          + 0.5 * beat_env(T, [EV['look_door'], EV['pencil_up']], 0.18))


def build():
    shots = act1.shots()
    if act2:
        shots += act2.shots()
    if act3:
        shots += act3.shots()
    extra_overlays = [act.overlays for act in (act1, act2, act3) if act and hasattr(act, 'overlays')]
    return Film(DURATION, shots, overlays=[overlays] + extra_overlays, post=[post])
