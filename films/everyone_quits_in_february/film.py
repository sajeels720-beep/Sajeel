"""'Everyone Quits in February. | An Animated Short Film' - picture assembly."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import act1  # noqa: E402
from cues import COUNTERS, DAY_FLASH, DURATION, EV, NARRATOR  # noqa: E402
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
    # fade up from black, the dip into the title, fade out
    a = 1 - smooth(0.0, 0.6, T)
    a = max(a, smooth(147.2, 147.95, T) * (1 - smooth(148.0, 148.6, T)))
    a = max(a, smooth(158.6, 159.9, T))
    fade(c, W, H, a)
    flash(c, W, H, 0.9 * beat_env(T, [EV['photo_flash'], EV['photo_flash2']], 0.18)
          + 0.18 * beat_env(T, DAY_FLASH, 0.1)
          + 0.5 * beat_env(T, [EV['drop']], 0.2)
          + 0.12 * beat_env(T, [EV['midnight']], 0.3)
          + 0.35 * beat_env(T, [120.8], 0.25))


def build():
    shots = act1.shots()
    if act2:
        shots += act2.shots()
    if act3:
        shots += act3.shots()
    extra_overlays = [act.overlays for act in (act1, act2, act3) if act and hasattr(act, 'overlays')]
    return Film(DURATION, shots, overlays=[overlays] + extra_overlays, post=[post])
