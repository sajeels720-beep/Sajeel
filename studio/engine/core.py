"""Time, easing, keyframes and deterministic randomness.

Every frame is a pure function of time, so any frame range can be rendered
in parallel and in any order.
"""
from __future__ import annotations

import math

W, H = 1920, 1080
FPS = 30


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, u):
    return a + (b - a) * u


def remap(x, a, b, c=0.0, d=1.0):
    """Map x from [a, b] to [c, d], clamped."""
    if b == a:
        return d
    return lerp(c, d, clamp((x - a) / (b - a)))


def smooth(a, b, x):
    u = clamp((x - a) / (b - a)) if b != a else 1.0
    return u * u * (3 - 2 * u)


def pulse(t, start, attack, hold, release):
    """0 -> 1 -> 0 envelope: rises over `attack`, holds, falls over `release`."""
    if t < start:
        return 0.0
    t -= start
    if t < attack:
        return smooth(0, attack, t)
    t -= attack
    if t < hold:
        return 1.0
    t -= hold
    return 1.0 - smooth(0, release, t)


# --- easing -----------------------------------------------------------------

def linear(u):
    return u


def in_quad(u):
    return u * u


def out_quad(u):
    return 1 - (1 - u) * (1 - u)


def in_out_quad(u):
    return 2 * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 2 / 2


def in_cubic(u):
    return u ** 3


def out_cubic(u):
    return 1 - (1 - u) ** 3


def in_out_cubic(u):
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def in_out_sine(u):
    return -(math.cos(math.pi * u) - 1) / 2


def out_back(u, s=1.70158):
    u -= 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2


def out_elastic(u):
    if u in (0, 1):
        return u
    return 2 ** (-10 * u) * math.sin((u * 10 - 0.75) * (2 * math.pi) / 3) + 1


def out_expo(u):
    return 1 if u >= 1 else 1 - 2 ** (-10 * u)


def in_expo(u):
    return 0 if u <= 0 else 2 ** (10 * u - 10)


def hold(u):
    return 0.0 if u < 1 else 1.0


EASES = {name: fn for name, fn in globals().items()
         if callable(fn) and name in {
             'linear', 'in_quad', 'out_quad', 'in_out_quad', 'in_cubic', 'out_cubic', 'in_out_cubic',
             'in_out_sine', 'out_back', 'out_elastic', 'out_expo', 'in_expo', 'hold'}}


def ease(name, u):
    return EASES[name](clamp(u))


# --- interpolation of numbers, tuples and pose dicts ---------------------------

def mix(a, b, u):
    if isinstance(a, dict) or isinstance(b, dict):
        a = a or {}
        b = b or {}
        out = {}
        for k in set(a) | set(b):
            if k in a and k in b:
                out[k] = mix(a[k], b[k], u)
            else:
                out[k] = a[k] if k in a else b[k]
        return out
    if isinstance(a, (tuple, list)):
        return type(a)(mix(x, y, u) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * u
    return b if u >= 0.5 else a


class Track:
    """Keyframes [(time, value[, ease])]; the ease shapes the move INTO that key."""

    def __init__(self, keys, default_ease='in_out_cubic'):
        self.keys = sorted((k if len(k) == 3 else (k[0], k[1], default_ease)) for k in keys)

    def __call__(self, t):
        keys = self.keys
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, v0, _), (t1, v1, e) in zip(keys, keys[1:]):
            if t < t1:
                return mix(v0, v1, ease(e, (t - t0) / (t1 - t0)))
        return keys[-1][1]


def poses(t, keys, base=None, default_ease='in_out_cubic'):
    """Evaluate a pose keyframe list layered over a base pose dict."""
    value = Track(keys, default_ease)(t)
    if base:
        merged = dict(base)
        merged.update(value)
        return merged
    return value


# --- deterministic randomness --------------------------------------------------

def hrand(*args):
    """Stable pseudo-random float in [0, 1) from any hashable integers/floats."""
    h = 2166136261
    for a in args:
        x = int(a * 1000003) if isinstance(a, float) else int(a)
        h ^= x & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= h >> 13
        h = (h * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFFFF) / float(0x1000000)


def hrange(lo, hi, *args):
    return lo + (hi - lo) * hrand(*args)


def noise1(x, seed=0):
    """Smooth 1-D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = hrand(i, seed) * 2 - 1
    b = hrand(i + 1, seed) * 2 - 1
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def shake(t, amount, speed=18.0, seed=0):
    return (noise1(t * speed, seed) * amount, noise1(t * speed, seed + 71) * amount)


def beat_env(t, times, decay=0.25):
    """Sum of exponential decays after each event time (for hits and flashes)."""
    v = 0.0
    for e in times:
        if t >= e:
            v += math.exp(-(t - e) / decay)
    return v
