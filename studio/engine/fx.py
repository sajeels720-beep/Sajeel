"""Stateless effects: every function draws the effect as it looks at time t."""
from __future__ import annotations

import math

import skia

from .core import clamp, hrand, hrange, noise1, smooth
from .draw import font, paint, poly, text


def dust_motes(c, x0, y0, x1, y1, t, n=60, seed=1, color='#FFE6B0', a=0.6, size=(1.2, 3.2), speed=12.0):
    """Floating specks in a light beam."""
    w, h = x1 - x0, y1 - y0
    for i in range(n):
        bx, by = hrand(i, seed), hrand(i, seed, 2)
        px = x0 + ((bx * w + noise1(t * 0.15 + i, seed) * 40 + t * speed * (hrand(i, 5) - 0.5)) % w)
        py = y0 + ((by * h + t * speed * (0.3 + hrand(i, 6)) * 0.5) % h)
        tw = 0.5 + 0.5 * math.sin(t * (1 + hrand(i, 7) * 2) + i)
        r = hrange(size[0], size[1], i, seed, 3)
        c.drawCircle(px, py, r, paint(color, a * (0.35 + 0.65 * tw), blend='add'))


def note_path(s, kind=0):
    p = skia.Path()
    if kind == 0:
        p.addOval(skia.Rect.MakeLTRB(-0.6 * s, -0.42 * s, 0.6 * s, 0.42 * s))
        p.addRect(skia.Rect.MakeLTRB(0.42 * s, -2.3 * s, 0.6 * s, 0.0))
        p.moveTo(0.6 * s, -2.3 * s)
        p.cubicTo(1.4 * s, -1.9 * s, 1.5 * s, -1.3 * s, 1.1 * s, -0.9 * s)
        p.cubicTo(1.2 * s, -1.4 * s, 0.9 * s, -1.6 * s, 0.6 * s, -1.7 * s)
        p.close()
    else:
        for dx in (0.0, 1.6 * s):
            p.addOval(skia.Rect.MakeLTRB(dx - 0.6 * s, -0.42 * s, dx + 0.6 * s, 0.42 * s))
            p.addRect(skia.Rect.MakeLTRB(dx + 0.42 * s, -2.2 * s, dx + 0.6 * s, 0.0))
        p.addPoly([(0.42 * s, -2.2 * s), (2.2 * s, -2.5 * s), (2.2 * s, -2.1 * s), (0.42 * s, -1.8 * s)], True)
    return p


def notes(c, x, y, t, start, end=None, rate=2.2, life=2.6, seed=3, size=16, rise=220, color='warm', a=1.0,
          freeze_at=None, fall=None, drift=1.0):
    """Music notes spawned from (x, y). freeze_at: time they stop; fall: time they drop and shatter.
    drift: +1 drifts right, -1 drifts left."""
    if t < start:
        return
    last = t if end is None else min(t, end)
    count = int((last - start) * rate) + 1
    for i in range(count):
        born = start + i / rate
        age = t - born
        if age < 0 or age > life:
            continue
        u = age / life
        if freeze_at is not None and t > freeze_at:
            age_f = freeze_at - born
            if age_f < 0:
                continue
            u = age_f / life
        dx = drift * (hrand(i, seed) - 0.15) * 180 * u + math.sin(age * 2.4 + i) * 14
        dy = -rise * u
        rot = math.sin(age * 2 + i) * 18
        alpha = a * smooth(0, 0.12, u) * (1 - smooth(0.7, 1.0, u))
        px, py = x + dx, y + dy
        if fall is not None and t > fall:
            ft = t - fall
            py += 600 * ft * ft
            rot += ft * 200 * (1 if i % 2 else -1)
            alpha *= clamp(1 - ft / 0.6)
        if alpha <= 0.01:
            continue
        s = size * (0.8 + 0.4 * hrand(i, seed, 1))
        c.save()
        c.translate(px, py)
        c.rotate(rot)
        path = note_path(s, i % 3 == 2)
        c.drawPath(path, paint(color, alpha * 0.8, blur=8, blend='add'))
        c.drawPath(path, paint('#FFE8B8', alpha))
        c.restore()


def shards(c, x, y, t, t0, n=14, seed=5, color='warm', size=10, speed=420, gravity=900, life=1.1, a=1.0,
           spread=math.tau, direction=0.0):
    """Burst of triangular shards from (x, y) at t0."""
    if t < t0:
        return
    age = t - t0
    if age > life:
        return
    fade = 1 - smooth(life * 0.5, life, age)
    for i in range(n):
        ang = direction + (hrand(i, seed) - 0.5) * spread
        v = speed * (0.4 + 0.6 * hrand(i, seed, 1))
        px = x + math.cos(ang) * v * age
        py = y + math.sin(ang) * v * age + 0.5 * gravity * age * age
        rot = age * 600 * (hrand(i, seed, 2) - 0.5)
        s = size * (0.5 + hrand(i, seed, 3))
        c.save()
        c.translate(px, py)
        c.rotate(rot)
        tri = poly([(-s, -s * 0.4), (s * 0.8, -s * 0.6), (s * 0.2, s * 0.9)], True)
        c.drawPath(tri, paint(color, a * fade * 0.6, blur=5, blend='add'))
        c.drawPath(tri, paint(color, a * fade))
        c.restore()


def puff(c, x, y, t, t0, n=16, seed=8, color='#BDB6A8', size=26, spread=180, life=1.6, a=0.7, wind=(160, -30)):
    """Soft dust cloud blown from (x, y)."""
    if t < t0:
        return
    age = t - t0
    if age > life:
        return
    u = age / life
    for i in range(n):
        ang = (hrand(i, seed) - 0.5) * 1.6
        d = spread * (0.3 + 0.7 * hrand(i, seed, 1)) * (1 - (1 - u) ** 2)
        px = x + wind[0] * u + math.cos(ang) * d * 0.6
        py = y + wind[1] * u + math.sin(ang) * d * 0.4
        r = size * (0.6 + 0.8 * hrand(i, seed, 2)) * (0.5 + u)
        c.drawCircle(px, py, r, paint(color, a * (1 - u) * 0.45, blur=r * 0.5))


def shockwave(c, x, y, t, t0, max_r=1400, life=1.2, color='warm', width=40, a=1.0):
    if t < t0 or t > t0 + life:
        return
    u = (t - t0) / life
    r = max_r * (1 - (1 - u) ** 3)
    alpha = a * (1 - u)
    c.drawCircle(x, y, r, paint(color, alpha * 0.8, stroke=width * (1 - u * 0.6), blur=18, blend='add'))
    c.drawCircle(x, y, r, paint('#FFF3D6', alpha, stroke=4))


def sound_waves(c, x, y, t, start, end=None, rate=2.0, life=1.4, max_r=360, color='warm', a=0.8, arc=(-70, 140)):
    """Arcs radiating from an instrument."""
    if t < start:
        return
    last = t if end is None else min(t, end)
    count = int((last - start) * rate) + 1
    for i in range(count):
        age = t - (start + i / rate)
        if 0 <= age <= life:
            u = age / life
            r = 40 + max_r * u
            path = skia.Path()
            path.addArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), arc[0], arc[1])
            alpha = a * (1 - u)
            c.drawPath(path, paint(color, alpha * 0.7, stroke=10, blur=8, blend='add'))
            c.drawPath(path, paint('#FFE8B8', alpha, stroke=3))


def word_projectile(c, word, p0, p1, t, t0, dur=0.9, size=56, color='#FF5C55', shatter=True, seed=2, arc=-80):
    """A whispered word thrown from p0 to p1; shatters on arrival."""
    if t < t0:
        return
    age = t - t0
    if age < dur:
        u = age / dur
        e = u * u * (3 - 2 * u)
        x = p0[0] + (p1[0] - p0[0]) * e
        y = p0[1] + (p1[1] - p0[1]) * e + arc * math.sin(math.pi * u)
        rot = (p1[0] - p0[0]) * 0.01 * math.sin(u * 3)
        c.save()
        c.translate(x, y)
        c.rotate(rot)
        text(c, word, 0, size * 0.35, size, 'PatrickHand', color, smooth(0, 0.15, u), glow='red', glow_a=0.7)
        c.restore()
    elif shatter:
        shards(c, p1[0], p1[1], t, t0 + dur, n=18, seed=seed, color='#FF6B60', size=9, speed=380)


def eye_field(c, eyes, t, rim='red'):
    """Many floating eye pairs drawn in one batch.

    eyes: iterable of (x, y, size, openness, slant, alpha)."""
    core = skia.Path()
    glow_items = []
    for (x, y, s, o, slant, a) in eyes:
        if o <= 0.03 or a <= 0.02:
            continue
        ew, eh = s * 0.17, s * 0.085 * o
        hs = s * 0.3
        for ex, inner in ((x - hs, 1), (x + hs, -1)):
            sl = math.radians(slant) * inner
            tl = (ex - ew, y - eh * 0.2 - math.tan(sl) * ew * 0.6)
            tr = (ex + ew, y - eh * 0.2 + math.tan(sl) * ew * 0.6)
            p = skia.Path()
            p.moveTo(*tl)
            p.lineTo(*tr)
            p.quadTo(ex + ew * 0.9, y + eh * 1.6, ex, y + eh * 1.5)
            p.quadTo(ex - ew * 0.9, y + eh * 1.6, *tl)
            p.close()
            core.addPath(p)
        glow_items.append((x, y, s, a))
    if core.isEmpty():
        return
    c.drawPath(core, paint(rim, 0.95, blur=9, blend='add'))
    c.drawPath(core, paint('#FF2A22'))
    c.drawPath(core, paint('#FFB3A6', 0.5, blur=2, blend='add'))


def flash(c, w, h, amount, color='#FFF6E0'):
    if amount > 0.003:
        c.drawRect(skia.Rect.MakeWH(w, h), paint(color, min(1.0, amount), blend='add'))


def light_rays(c, x, y, t, n=14, length=1600, a=0.12, color='warm', spin=0.05, width=0.07):
    for i in range(n):
        ang = (i / n) * math.tau + t * spin + hrand(i, 9) * 0.2
        w = width * (0.6 + hrand(i, 10))
        path = poly([(x, y), (x + math.cos(ang - w) * length, y + math.sin(ang - w) * length),
                     (x + math.cos(ang + w) * length, y + math.sin(ang + w) * length)], True)
        c.drawPath(path, paint(color, a * (0.5 + 0.5 * math.sin(t * 1.3 + i)), blur=24, blend='add'))
