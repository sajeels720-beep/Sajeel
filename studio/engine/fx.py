"""Stateless effects: every function draws the effect as it looks at time t."""
from __future__ import annotations

import math

import skia

from .core import clamp, hrand, hrange, noise1, smooth
from .draw import font, oval, paint, poly, text


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


# --- quitting: turning to smoke ---------------------------------------------------------------------------

def _crumble_mask(box, thr, seed, freq=0.045, k=7.0, from_top=False):
    """A paint that keeps pixels where noise + height < thr (the bottom of the box goes first, or the top)."""
    x0, y0, x1, y1 = box
    noise = skia.PerlinNoiseShader.MakeFractalNoise(freq, freq, 3, float(seed % 97))
    ends = [skia.Color(0, 0, 0, 255), skia.Color(255, 255, 255, 255)]
    grad = skia.GradientShader.MakeLinear(points=[(x0, y0), (x0, y1)], colors=ends[::-1] if from_top else ends)
    comb = skia.Shaders.Blend(skia.BlendMode.kPlus, noise, grad)
    m = [0, 0, 0, 0, 0,
         0, 0, 0, 0, 0,
         0, 0, 0, 0, 0,
         -k, 0, 0, 0, k * thr]
    p = skia.Paint()
    p.setShader(comb.makeWithColorFilter(skia.ColorFilters.Matrix(m)))
    p.setBlendMode(skia.BlendMode.kDstIn)
    return p


def dissolve(c, draw_fn, box, t, t0, dur=1.7, seed=1, smoke='#A3A8B2', smoke_a=0.55, grey=0.6, rise=260,
             embers=None, n=34, drift=40.0):
    """Draw draw_fn(c) as someone quitting: the colour drains out, then the figure crumbles away from the feet
    up while smoke rises from the crumbling edge. box: (x0, y0, x1, y1) around the figure (world units).
    Before t0 - 0.5 it is drawn untouched; the smoke keeps rising for a while after it is gone."""
    x0, y0, x1, y1 = box
    u = (t - t0) / dur
    if u < 1:
        if t < t0 - 0.55:
            draw_fn(c)
            return
        c.saveLayer(skia.Rect.MakeLTRB(x0 - 60, y0 - 80, x1 + 60, y1 + 40), None)
        draw_fn(c)
        g = grey * smooth(t0 - 0.55, t0 + 0.25, t)
        if g > 0:
            gp = paint('#7E848F', g)
            gp.setBlendMode(skia.BlendMode.kSrcATop)
            c.drawRect(skia.Rect.MakeLTRB(x0 - 60, y0 - 80, x1 + 60, y1 + 40), gp)
        if u > 0:
            thr = 1.75 - 2.1 * u
            c.drawRect(skia.Rect.MakeLTRB(x0 - 60, y0 - 80, x1 + 60, y1 + 40), _crumble_mask(box, thr, seed))
        c.restore()
    # smoke puffs born along the crumbling edge, which climbs the figure over `dur`
    life = 1.9
    for i in range(n):
        born = t0 + dur * (i / n) * 0.95
        age = t - born
        if age < 0 or age > life:
            continue
        v = age / life
        front = y1 - (y1 - y0) * ((born - t0) / dur) * 1.05
        bx = x0 + (x1 - x0) * (0.25 + 0.5 * hrand(i, seed))
        px = bx + noise1(age * 0.9 + i, seed) * drift + (hrand(i, seed, 3) - 0.5) * 60 * v
        py = front - rise * (1 - (1 - v) ** 1.6) - 10
        r = (16 + 22 * hrand(i, seed, 2)) * (0.6 + 1.3 * v)
        alpha = smoke_a * smooth(0.0, 0.12, v) * (1 - smooth(0.45, 1.0, v))
        c.drawCircle(px, py, r, paint(smoke, alpha, blur=r * 0.55))
        if embers and hrand(i, seed, 5) > 0.5:
            c.drawCircle(px + 6, py + 4, 2.6, paint(embers, alpha * 1.4, blur=1.5, blend='add'))


def crumble(c, draw_fn, box, amount, seed=1, from_top=True, grey=0.0, freq=0.09):
    """Draw draw_fn(c) partly eaten away (amount 0 = whole, 1 = gone), e.g. fingertips going to smoke."""
    x0, y0, x1, y1 = box
    if amount <= 0.001 and grey <= 0:
        draw_fn(c)
        return
    c.saveLayer(skia.Rect.MakeLTRB(x0 - 40, y0 - 40, x1 + 40, y1 + 40), None)
    draw_fn(c)
    if grey > 0:
        gp = paint('#8E949E', grey)
        gp.setBlendMode(skia.BlendMode.kSrcATop)
        c.drawRect(skia.Rect.MakeLTRB(x0 - 40, y0 - 40, x1 + 40, y1 + 40), gp)
    if amount > 0.001:
        c.drawRect(skia.Rect.MakeLTRB(x0 - 40, y0 - 40, x1 + 40, y1 + 40),
                   _crumble_mask(box, 1.75 - 2.1 * amount, seed, freq=freq, from_top=from_top))
    c.restore()


def wisps(c, points, t, a=1.0, color='#B6BBC4', rise=120, seed=4, width=7.0):
    """Thin smoke streams curling up from each point (fingertips starting to go)."""
    if a <= 0:
        return
    for k, (x, y) in enumerate(points):
        for j in range(3):
            phase = (t * 0.7 + j / 3 + hrand(k, seed)) % 1.0
            path = skia.Path()
            pts = []
            for m in range(9):
                u = m / 8
                yy = y - rise * u * (0.6 + 0.4 * phase)
                xx = x + math.sin(u * 5 + t * 2.4 + k + j) * 12 * u + noise1(t * 0.8 + j, k + seed) * 10 * u
                pts.append((xx, yy))
            path.moveTo(*pts[0])
            for p in pts[1:]:
                path.lineTo(*p)
            alpha = a * 0.5 * (1 - phase) * smooth(0.0, 0.2, phase)
            c.drawPath(path, paint(color, alpha, stroke=width * (1.2 - 0.6 * phase), blur=3))


# --- the year outside: fireworks, snow, rain, leaves --------------------------------------------------------

FIREWORK_COLORS = ['#FFD36E', '#FF7A59', '#7FD3FF', '#C59BFF', '#9CFFB8', '#FFFFFF']


def firework(c, x, y, t, t0, color='#FFD36E', n=40, radius=230, seed=0, life=1.9, rocket=0.65, a=1.0, size=1.0):
    """A rocket climbs for `rocket` seconds, then bursts at (x, y) at t0 into falling sparks."""
    if t < t0 - rocket or t > t0 + life:
        return
    if t < t0:
        u = (t - (t0 - rocket)) / rocket
        ry = y + 420 * size * (1 - u) ** 1.4
        for k in range(6):
            tr = y + 420 * size * (1 - max(0.0, u - k * 0.02)) ** 1.4
            c.drawCircle(x + math.sin(k + t * 30) * 1.5, tr, 3.0 - 0.4 * k, paint('#FFE7B8', a * (1 - k / 6)))
        c.drawCircle(x, ry, 10, paint(color, 0.5 * a, blur=6, blend='add'))
        return
    age = t - t0
    v = age / life
    if age < 0.2:
        c.drawCircle(x, y, radius * size * 0.32, paint(color, a * 0.2 * (1 - age / 0.2), blur=40, blend="add"))
    for i in range(n):
        ang = math.tau * i / n + hrand(i, seed) * 0.2
        sp = radius * size * (0.7 + 0.3 * hrand(i, seed, 1))
        reach = 1 - (1 - min(1.0, age / 0.9)) ** 3
        fall = 70 * size * age * age
        px = x + math.cos(ang) * sp * reach
        py = y + math.sin(ang) * sp * reach + fall
        tail = 0.12 * sp * (1 - reach) + 6
        tx = px - math.cos(ang) * tail
        ty = py - math.sin(ang) * tail - 2
        alpha = a * (1 - smooth(0.5, 1.0, v)) * (0.6 + 0.4 * math.sin(age * 30 + i) ** 2)
        c.drawLine(tx, ty, px, py, paint(color, alpha * 0.8, stroke=3.2 * size, blur=2, blend='add'))
        c.drawCircle(px, py, 2.4 * size, paint('#FFFFFF', alpha))


def snowfall(c, x0, y0, x1, y1, t, n=90, seed=1, wind=24.0, speed=55.0, size=(1.6, 4.4), a=0.85, color='#F4F6FF'):
    w, h = x1 - x0, y1 - y0
    for i in range(n):
        sp = speed * (0.6 + 0.8 * hrand(i, seed))
        px = x0 + (hrand(i, seed, 1) * w + t * wind * (0.5 + hrand(i, seed, 2)) + math.sin(t * 1.3 + i) * 12) % w
        py = y0 + (hrand(i, seed, 3) * h + t * sp) % h
        r = size[0] + (size[1] - size[0]) * hrand(i, seed, 4)
        c.drawCircle(px, py, r, paint(color, a * (0.55 + 0.45 * hrand(i, seed, 5))))


def rainfall(c, x0, y0, x1, y1, t, n=110, seed=2, slant=0.18, speed=1300.0, length=38.0, a=0.35, color='#BFD3EA'):
    w, h = x1 - x0, y1 - y0
    p = paint(color, a, stroke=2.2)
    for i in range(n):
        sp = speed * (0.8 + 0.4 * hrand(i, seed))
        py = y0 + (hrand(i, seed, 1) * h + t * sp) % h
        px = x0 + (hrand(i, seed, 2) * w + (py - y0) * slant) % w
        c.drawLine(px, py, px - length * slant, py - length, p)


def falling_leaves(c, x0, y0, x1, y1, t, n=24, seed=3, colors=('#E07B39', '#C9572B', '#E8A93A', '#B5452A'),
                   speed=70.0, size=11.0, a=1.0, petals=False):
    w, h = x1 - x0, y1 - y0
    for i in range(n):
        sp = speed * (0.6 + 0.8 * hrand(i, seed))
        py = y0 + (hrand(i, seed, 1) * h + t * sp) % h
        px = x0 + (hrand(i, seed, 2) * w + math.sin(t * 1.4 + i) * 40 + t * 30) % w
        rot = t * 140 * (hrand(i, seed, 3) - 0.5) + i * 40
        s = size * (0.7 + 0.6 * hrand(i, seed, 4))
        c.save()
        c.translate(px, py)
        c.rotate(rot)
        c.scale(1.0, 0.45 + 0.55 * abs(math.sin(t * 2 + i)))
        if petals:
            c.drawOval(oval(0, 0, s * 0.8, s * 0.55), paint(colors[i % len(colors)], a))
        else:
            leaf = skia.Path()
            leaf.moveTo(-s, 0)
            leaf.quadTo(0, -s * 0.8, s, 0)
            leaf.quadTo(0, s * 0.8, -s, 0)
            c.drawPath(leaf, paint(colors[i % len(colors)], a))
            c.drawLine(-s, 0, s, 0, paint('#000000', 0.25 * a, stroke=1.2))
        c.restore()
