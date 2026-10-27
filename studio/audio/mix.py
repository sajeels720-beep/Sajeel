"""Timeline mixer: place clips on buses, automate gains, duck, limit."""
from __future__ import annotations

import numpy as np

from .dsp import SR, db, leveler, limiter, secs, stereo


class Mix:
    def __init__(self, duration, tail=2.0):
        self.n = secs(duration + tail)
        self.duration = duration
        self.buses = {}
        self.autom = {}

    def bus(self, name):
        if name not in self.buses:
            self.buses[name] = np.zeros((self.n, 2), np.float32)
        return self.buses[name]

    def add(self, bus, x, t, gain_db=0.0, pan=0.0, fade_in=0.0, fade_out=0.0, max_len=None):
        if x is None or len(x) == 0:
            return
        x = stereo(x, pan) if x.ndim == 1 else x.copy()
        if max_len is not None:
            x = x[: secs(max_len)]
        if fade_in > 0:
            k = min(len(x), secs(fade_in))
            x[:k] *= np.linspace(0, 1, k)[:, None]
        if fade_out > 0:
            k = min(len(x), secs(fade_out))
            x[-k:] *= np.linspace(1, 0, k)[:, None]
        b = self.bus(bus)
        i = secs(t)
        if i >= self.n:
            return
        if i < 0:
            x = x[-i:]
            i = 0
        m = min(len(x), self.n - i)
        b[i:i + m] += x[:m] * db(gain_db)

    def automate(self, bus, points):
        """points: [(time, gain_db)] linear-in-dB between points."""
        self.autom.setdefault(bus, []).extend(points)

    def duck(self, bus, windows, amount_db=-6.0, ramp=0.2):
        """Dip a bus during windows [(t0, t1)]; overlapping ducks take the deepest value."""
        self.ducks = getattr(self, 'ducks', {})
        self.ducks.setdefault(bus, []).extend((t0, t1, amount_db, ramp) for t0, t1 in windows)

    def _env(self, bus):
        pts = sorted(self.autom.get(bus, []))
        ducks = getattr(self, 'ducks', {}).get(bus, [])
        if not pts and not ducks:
            return None
        t = np.arange(self.n) / SR
        g_db = np.zeros(self.n)
        if pts:
            times = np.array([p[0] for p in pts])
            vals = np.array([p[1] for p in pts])
            g_db = np.interp(t, times, vals, left=vals[0], right=vals[-1])
        duck_db = np.zeros(self.n)
        for t0, t1, amount, ramp in ducks:
            shape = np.interp(t, [t0 - ramp, t0, t1, t1 + ramp], [0.0, 1.0, 1.0, 0.0], left=0.0, right=0.0)
            duck_db = np.minimum(duck_db, shape * amount)
        return (10 ** ((g_db + duck_db) / 20)).astype(np.float32)

    def render(self, bus_gains=None, ceiling=0.94, level=None):
        """level: {bus: target_db} to run a slow leveler on that bus before mixing."""
        bus_gains = bus_gains or {}
        level = level or {}
        out = np.zeros((self.n, 2), np.float32)
        for name, b in self.buses.items():
            if name in level:
                b = leveler(b, level[name])
            env = self._env(name)
            sig = b * env[:, None] if env is not None else b
            out += sig * db(bus_gains.get(name, 0.0))
        out = limiter(out, ceiling)
        return out[: secs(self.duration + 1.0)]
