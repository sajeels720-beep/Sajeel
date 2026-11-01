"""Smooth motion: keyframes that flow through poses, overlapping action, settles, planted-foot walks and runs,
and camera paths.

The older Track eases in and out of every key, so a character stops dead at each pose ("move, hold, move").
Curve instead runs a monotone cubic spline through the keys (Fritsch-Carlson): motion only comes to rest where
it changes direction or where a key asks it to ('stop'), never overshoots, and has no velocity jumps. Body parts
can trail the hips by a few hundredths of a second (overlap), which is most of what makes a move feel organic.

Walks and runs are driven by the distance the body has travelled, not by time, so a planted foot never slides,
even while the body speeds up or slows down. Everything is still a pure function of time.
"""
from __future__ import annotations

import bisect
import math

from .core import clamp, noise1

# --- monotone cubic channels -----------------------------------------------------------------------------------


class _Channel:
    """One numeric channel through keys [(t, v, mode)]; mode is 'smooth', 'stop' (come to rest) or 'hold' (jump)."""

    __slots__ = ('ts', 'vs', 'ms', 'holds')

    def __init__(self, keys):
        keys = sorted(keys, key=lambda k: k[0])
        self.ts = [k[0] for k in keys]
        self.vs = [float(k[1]) for k in keys]
        modes = [k[2] for k in keys]
        self.holds = [m == 'hold' for m in modes]
        n = len(keys)
        ms = [0.0] * n
        if n > 2:
            h = [self.ts[i + 1] - self.ts[i] for i in range(n - 1)]
            d = [(self.vs[i + 1] - self.vs[i]) / h[i] if h[i] > 1e-9 else 0.0 for i in range(n - 1)]
            for i in range(1, n - 1):
                if modes[i] in ('stop', 'hold') or self.holds[i + 1] or d[i - 1] * d[i] <= 0:
                    continue
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                ms[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        self.ms = ms

    def __call__(self, t):
        ts = self.ts
        if t <= ts[0]:
            return self.vs[0]
        if t >= ts[-1]:
            return self.vs[-1]
        i = bisect.bisect_right(ts, t) - 1
        if self.holds[i + 1]:
            return self.vs[i]
        h = ts[i + 1] - ts[i]
        u = (t - ts[i]) / h
        u2, u3 = u * u, u * u * u
        return ((2 * u3 - 3 * u2 + 1) * self.vs[i] + (u3 - 2 * u2 + u) * h * self.ms[i]
                + (-2 * u3 + 3 * u2) * self.vs[i + 1] + (u3 - u2) * h * self.ms[i + 1])


class _Step:
    """A non-numeric channel (a string, a flag): takes each key's value from that key's time on."""

    __slots__ = ('ts', 'vs')

    def __init__(self, keys):
        keys = sorted(keys, key=lambda k: k[0])
        self.ts = [k[0] for k in keys]
        self.vs = [k[1] for k in keys]

    def __call__(self, t):
        i = bisect.bisect_right(self.ts, t) - 1
        return self.vs[max(0, i)]


def _numeric(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class Curve:
    """Keys [(t, value[, mode])] where value is a number, a tuple of numbers or a pose dict.

    Each dict key is its own channel and is only constrained by the keys that mention it, so a pose can be built
    from overlapping layers of keys. lag={'tilt': 0.08} makes a channel trail the rest (overlapping action);
    'head' and 'arms' are shorthands for the usual groups.
    """

    GROUPS = {'head': ('tilt', 'head_dx', 'head_dy', 'lx', 'ly'),
              'arms': ('sb', 'eb', 'sf', 'ef', 'hand_b', 'hand_f'),
              'legs': ('hb', 'kb', 'hf', 'kf', 'foot_b', 'foot_f')}

    def __init__(self, keys, lag=None):
        self.kind = None
        keys = [k if len(k) == 3 else (k[0], k[1], 'smooth') for k in keys]
        first = keys[0][1]
        self.lag = {}
        for name, d in (lag or {}).items():
            for ch in self.GROUPS.get(name, (name,)):
                self.lag[ch] = d
        if isinstance(first, dict):
            self.kind = 'dict'
            per = {}
            for t, v, m in keys:
                for name, x in v.items():
                    per.setdefault(name, []).append((t, x, m))
            self.chans = {}
            for name, ks in per.items():
                self.chans[name] = self._make(ks)
        else:
            self.kind = 'value'
            self.chan = self._make(keys)

    @staticmethod
    def _make(ks):
        v0 = ks[0][1]
        if isinstance(v0, (tuple, list)):
            comps = [_Channel([(t, v[i], m) for t, v, m in ks]) for i in range(len(v0))]
            return ('vec', comps, type(v0))
        if _numeric(v0) and all(_numeric(v) for _, v, _ in ks):
            return ('num', _Channel(ks))
        return ('step', _Step([(t, v) for t, v, _ in ks]))

    @staticmethod
    def _eval(spec, t):
        if spec[0] == 'num':
            return spec[1](t)
        if spec[0] == 'vec':
            return spec[2](c(t) for c in spec[1])
        return spec[1](t)

    def __call__(self, t, base=None, lag_scale=1.0):
        if self.kind == 'value':
            return self._eval(self.chan, t)
        out = dict(base) if base else {}
        for name, spec in self.chans.items():
            out[name] = self._eval(spec, t - self.lag.get(name, 0.0) * lag_scale)
        return out


def curve(t, keys, base=None, lag=None):
    """One-off evaluation (builds the curve each call: fine for a handful of keys)."""
    return Curve(keys, lag)(t, base)


# --- small motion helpers ----------------------------------------------------------------------------------------

def settle(t, t0, amp, freq=2.2, decay=0.35):
    """A damped wobble that starts at t0 (a head nodding to rest after a stop, a cane after it lands)."""
    if t < t0:
        return 0.0
    dt = t - t0
    return amp * math.exp(-dt / decay) * math.sin(2 * math.pi * freq * dt)


def ease_window(t, t0, t1, rise=0.35, fall=0.35):
    """0 -> 1 -> 0 with smooth (C1) shoulders: blend a cycle in and out of a pose."""
    from .core import smooth
    return smooth(t0, t0 + rise, t) * (1 - smooth(t1 - fall, t1, t))


def breath(t, rate=0.23, depth=1.0, seed=0):
    """Breathing (0..1) with a little irregularity, for 'breathe'."""
    ph = t * rate * 2 * math.pi + seed + 0.6 * noise1(t * 0.3, seed + 3)
    return (math.sin(ph) * 0.5 + 0.5) * depth


def sway(t, amount=1.0, seed=0):
    """Idle weight shift: lean, head tilt and a little hip drift, all slow and uncorrelated."""
    return dict(lean=noise1(t * 0.35, seed) * 1.6 * amount,
                tilt=noise1(t * 0.5, seed + 11) * 2.4 * amount,
                head_dx=noise1(t * 0.4, seed + 23) * 1.5 * amount)


def blend(a, b, w):
    """Mix two pose dicts channel by channel (numbers and tuples blend; anything else switches at w = 0.5)."""
    out = dict(a)
    for k, vb in b.items():
        if k not in a:
            out[k] = vb
            continue
        va = a[k]
        if _numeric(va) and _numeric(vb):
            out[k] = va + (vb - va) * w
        elif isinstance(va, (tuple, list)) and isinstance(vb, (tuple, list)):
            out[k] = type(va)(x + (y - x) * w for x, y in zip(va, vb))
        else:
            out[k] = vb if w >= 0.5 else va
    return out


# --- planted-foot locomotion ----------------------------------------------------------------------------------------

LEG = 114.0          # thigh + shin for the standard look
ANKLE = 9.0          # ankle height above the sole


class Gait:
    """Walk or run along x, driven by distance travelled.

    x_of_t: the body's x over time (e.g. a Curve), from x(t0) to x(t1). Each walking step moves the body `step`
    units; the first and last steps are half steps, so the walker starts and ends with both feet together.
    pose(t) returns pose fields for the rig: x, y, facing, scale, foot_b / foot_f IK targets, arm swing, lean, bob.
    """

    def __init__(self, x_of_t, t0, t1, floor_y, scale=1.0, step=84.0, lift=18.0, run=False, arm=22.0,
                 lean=4.0, bob=1.0, leg=LEG, duty=0.36, heel=1.0, facing=None, hunch=0.0, reach=0.35, ground=None):
        self.x = x_of_t
        self.t0, self.t1 = t0, t1
        self.xa, self.xb = x_of_t(t0), x_of_t(t1)
        self.dir = 1 if self.xb >= self.xa else -1
        self.facing = facing if facing is not None else self.dir
        self.D = abs(self.xb - self.xa)
        self.floor_y = floor_y
        self.g = ground or (lambda x: floor_y)       # ground height under any x (a slope, steps)
        self.s = scale
        self.run = run
        self.leg = leg
        if run:
            self.n = max(1, round(self.D / (step * scale)))
            self.S = self.D / self.n if self.D > 0 else step * scale
        else:
            self.n = max(2, round(self.D / (step * scale)) + 1)
            self.S = self.D / (self.n - 1) if self.D > 0 else step * scale
        self.lift, self.arm, self.lean, self.bob = lift, arm, lean, bob
        self.duty, self.heel, self.hunch, self.reach = duty, heel, hunch, reach

    def _phase(self, d):
        """Distance travelled -> (walking step index, progress 0..1 within that step)."""
        S = self.S
        if d <= S / 2:
            return 0, d / (S / 2) if S > 0 else 1.0
        k = 1 + int((d - S / 2) / S)
        if k >= self.n - 1:
            return self.n - 1, clamp((d - (S / 2 + (self.n - 2) * S)) / (S / 2))
        return k, (d - S / 2 - (k - 1) * S) / S

    def _land(self, j):
        """Where (distance along the path) the foot that swings in step j comes down."""
        return 0.0 if j < 0 else min(self.D, (j + 1) * self.S)

    def speed(self, t, dt=1 / 60):
        return abs(self.x(t + dt) - self.x(t - dt)) / (2 * dt)

    def pose(self, t):
        x = self.x(t)
        d = clamp(abs(x - self.xa), 0.0, self.D)
        if self.D <= 1 or t <= self.t0 or t >= self.t1:
            return self._stand(x)
        if self.run:
            w = clamp(min(d, self.D - d) / (0.7 * self.S))
            w = w * w * (3 - 2 * w)
            return blend(self._stand(x), self._run(t, x, d), w)
        s = self.s
        k, u = self._phase(d)
        frm, to, stance = self._land(k - 2), self._land(k), self._land(k - 1)
        e = u * u * (3 - 2 * u)
        swing_d = frm + (to - frm) * e
        lift = self.lift * s * math.sin(math.pi * u) * (0.6 if k in (0, self.n - 1) else 1.0)
        front_swings = k % 2 == 0
        off = 3 * s if front_swings else -3 * s      # the near foot rests a little ahead of the far one
        swx = self.xa + self.dir * (swing_d + off)
        frm_y = self.g(self.xa + self.dir * (frm + off))
        to_y = self.g(self.xa + self.dir * (to + off))
        sw = (swx, frm_y + (to_y - frm_y) * e - lift)
        stx = self.xa + self.dir * (stance - off)
        st = (stx, self.g(stx))
        # hip height from the stance leg (a compass gait), so the knees never have to over-stretch
        top = (self.leg - 2.5) * s + ANKLE * s
        L = self.leg * s * 0.985
        reach = abs(st[0] - x)
        y_hip = max(self.g(x) - top, st[1] - ANKLE * s - math.sqrt(max(1.0, L * L - reach * reach)))
        hip_h = self.g(x) - y_hip
        y = y_hip + (top - hip_h) * (self.bob - 1.0)
        pose = self._limbs(x, y, sw if front_swings else st, st if front_swings else sw)
        # arms swing against the legs; the swing grows with speed, so starts and stops are calm
        v = clamp(self.speed(t) / (self.S * 1.6 + 1e-6)) ** 0.7
        swing = math.cos(math.pi * (k + u))
        amp = self.arm * v
        pose.update(sb=4 - amp * swing, sf=-2 + amp * swing, eb=14 + 10 * v * max(0.0, -swing),
                    ef=14 + 10 * v * max(0.0, swing), lean=self.lean * v + self.hunch,
                    head_dy=-max(0.0, top - hip_h) * 0.35 / s)
        return pose

    def _run(self, t, x, d):
        s, S = self.s, self.S
        ph = d / S                                   # steps so far; a foot lands on every whole number
        v = clamp(self.speed(t) / (S * 2.2 + 1e-6))
        reach, duty = S * self.reach, self.duty
        stance_len = 2 * S * duty
        feet = {}
        for side, off in (('f', 0.0), ('b', 1.0)):
            p = ((ph + off) / 2.0) % 1.0             # this foot's own cycle (two steps)
            if p < duty:                             # planted: slides back under the hip at exactly body speed
                q = p / duty
                fx_ = x + self.dir * (reach - stance_len * q)
                feet[side] = (fx_, self.g(fx_))
            else:                                    # swing: heel kicks up behind, the knee drives, the foot reaches
                q = (p - duty) / (1 - duty)
                start = reach - stance_len
                rel = start + (reach - start) * (q * q * (3 - 2 * q))
                rel -= math.sin(math.pi * q) * S * 0.22 * self.heel * (1 - q)
                up = math.sin(math.pi * q) ** 0.8 * self.lift * s * 2.0
                if q < 0.62:
                    up += math.sin(math.pi * q / 0.62) * 30 * s * self.heel
                feet[side] = (x + self.dir * rel, self.g(x + self.dir * rel) - up)
        cyc = ph % 1.0
        flight = 0.5 - 0.5 * math.cos(2 * math.pi * (cyc - duty))
        y = self.g(x) - ((self.leg - 14) * s + ANKLE * s + flight * 10 * s * self.bob)
        pose = self._limbs(x, y, feet['f'], feet['b'])
        swing = math.cos(math.pi * ph)
        amp = self.arm * (0.5 + 0.5 * v)
        pose.update(sb=10 + amp * swing, sf=4 - amp * swing, eb=88 + 16 * swing, ef=88 - 16 * swing,
                    lean=self.lean * (0.5 + 0.5 * v) + self.hunch, head_dy=-flight * 3)
        return pose

    def _limbs(self, x, y, foot_f, foot_b):
        s, fx = self.s, self.facing

        def loc(p):
            return ((p[0] - x) / s * fx, (p[1] - ANKLE * s - y) / s)

        return dict(x=x, y=y, facing=fx, scale=s, foot_f=loc(foot_f), foot_b=loc(foot_b), ikl_f=-1.0, ikl_b=-1.0)

    def _stand(self, x):
        s = self.s
        fa, fb = x + 3 * s * self.dir, x - 3 * s * self.dir
        y = min(self.g(fa), self.g(fb)) - (self.leg - 2.5) * s - ANKLE * s
        pose = self._limbs(x, y, (fa, self.g(fa)), (fb, self.g(fb)))
        pose.update(sb=4, sf=-2, eb=14, ef=14, lean=self.hunch, head_dy=0.0)
        return pose


def stand_feet(x, floor_y, scale=1.0, facing=1, apart=12.0, bend=2.5):
    """Standing pose fields with both feet planted on the floor (IK), the hip a little below full stretch."""
    s = scale
    y = floor_y - (LEG - bend) * s - ANKLE * s
    return dict(x=x, y=y, facing=facing, scale=s, foot_f=(apart * 0.6, (LEG - bend)), foot_b=(-apart * 0.4, (LEG - bend)),
                ikl_f=-1.0, ikl_b=-1.0)


# --- camera ------------------------------------------------------------------------------------------------------------

class CamPath:
    """Camera keys [(t, (cx, cy, zoom[, rot])[, mode])] through a monotone spline, plus an optional slow handheld
    drift (pixels at zoom 1) that never stops, so locked shots still breathe."""

    def __init__(self, keys, handheld=0.0, seed=0, speed=0.35):
        norm = []
        for k in keys:
            v = tuple(k[1]) + ((0.0,) if len(k[1]) == 3 else ())
            norm.append((k[0], v) + ((k[2],) if len(k) == 3 else ()))
        self.c = Curve(norm)
        self.hh = handheld
        self.seed = seed
        self.speed = speed

    def __call__(self, t):
        cx, cy, z, rot = self.c(t)
        if self.hh:
            cx += noise1(t * self.speed, self.seed) * self.hh / z
            cy += noise1(t * self.speed, self.seed + 7) * self.hh * 0.7 / z
            rot += noise1(t * self.speed * 0.8, self.seed + 13) * self.hh * 0.012
        return (cx, cy, z, rot)
