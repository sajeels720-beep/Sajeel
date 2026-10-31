"""Gym props in the flat side-view house style: weights, benches, racks, treadmills, lights and wall things.

Barbells and dumbbells are drawn in a slight three-quarter view (the near end lower-left and bigger), so they
read as weights even though everything else is a side view. Pass part='far' before drawing the lifter and
part='near' after, to put the lifter between the two ends.
"""
from __future__ import annotations

import math

import skia

from .core import hrand, hrange, noise1
from .draw import circle, col, cone, light_pool, mixc, oval, paint, poly, rrect, text

IRON = '#26282E'
IRON_EDGE = '#3B3E46'
STEEL = '#9AA0AA'
PAD = '#2B2F38'
PLATE_COLORS = ['#2F5FA8', '#2F5FA8', '#3B3E46']
DEPTH = (0.42, -0.2)   # unit-ish direction from the near end of a bar to the far end


# --- weights -----------------------------------------------------------------------------------

def _plate(c, x, y, r, color=IRON, a=1.0, squash=0.5, angle=-26.0):
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.drawOval(oval(0, 0, r * squash, r), paint(color, a))
    c.drawOval(oval(r * squash * 0.18, 0, r * squash * 0.55, r * 0.72), paint('#FFFFFF', 0.08 * a))
    c.drawOval(oval(0, 0, r * squash * 0.86, r * 0.86), paint('#BFD0EE', 0.55 * a, stroke=2.5))
    c.drawOval(oval(0, 0, r * squash, r), paint('outline', a, stroke=4))
    c.drawOval(oval(0, 0, r * squash * 0.22, r * 0.18), paint('#111216', a))
    c.restore()


def barbell(c, x, y, plates=1, length=330, plate_r=50, part='all', a=1.0, tilt=0.0, chalk=0.0, depth=DEPTH):
    """A loaded barbell centred at (x, y) (between the hands). plates: per side (1-4), each a little smaller.
    depth: direction from the near end to the far end (a small one shows the bar almost end-on)."""
    dx, dy = depth
    rot = math.radians(tilt)
    dx, dy = dx * math.cos(rot) - dy * math.sin(rot), dx * math.sin(rot) + dy * math.cos(rot)
    near = (x - dx * length / 2, y - dy * length / 2)
    far = (x + dx * length / 2, y + dy * length / 2)
    sizes = [plate_r * (1.0 - 0.12 * k) for k in range(max(0, plates))]

    def end(p, sign, scale):
        for k, r in enumerate(sizes):
            off = (k * 13 + 8) * sign
            _plate(c, p[0] + dx * off, p[1] + dy * off, r * scale, PLATE_COLORS[k % 3], a)
        cap = (p[0] + dx * (len(sizes) * 13 + 22) * sign, p[1] + dy * (len(sizes) * 13 + 22) * sign)
        c.drawLine(p[0], p[1], cap[0], cap[1], paint('outline', a, stroke=11))
        c.drawLine(p[0], p[1], cap[0], cap[1], paint(STEEL, a, stroke=6))

    if part in ('all', 'far'):
        end(far, 1, 0.82)
        c.drawLine(x, y, far[0], far[1], paint('outline', a, stroke=10))
        c.drawLine(x, y, far[0], far[1], paint(STEEL, a, stroke=5))
    if part in ('all', 'near'):
        c.drawLine(near[0], near[1], x, y, paint('outline', a, stroke=10))
        c.drawLine(near[0], near[1], x, y, paint(STEEL, a, stroke=5))
        if chalk > 0:
            c.drawCircle(x, y, 9, paint('#FFFFFF', 0.5 * chalk * a, blur=4))
        end(near, -1, 1.0)
    return near, far


def dumbbell(c, x, y, size=1.0, angle=-26.0, a=1.0, color=IRON):
    """A hex dumbbell centred on the grip (x, y), drawn across the hand in three-quarter view."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    s = size
    c.drawLine(-26 * s, 0, 26 * s, 0, paint('outline', a, stroke=9 * s))
    c.drawLine(-26 * s, 0, 26 * s, 0, paint(STEEL, a, stroke=5 * s))
    for side, k in ((1, 0.8), (-1, 1.0)):
        hx = side * 30 * s
        hexa = poly([(hx + math.cos(math.radians(60 * i)) * 9 * s * k,
                      math.sin(math.radians(60 * i)) * 19 * s * k) for i in range(6)], True)
        c.drawPath(hexa, paint(color, a))
        c.drawPath(hexa, paint('#FFFFFF', 0.07 * a))
        c.drawPath(hexa, paint('outline', a, stroke=3.5))
    c.restore()


def kettlebell(c, x, floor_y, size=1.0, color=IRON, a=1.0):
    s = size
    body = oval(x, floor_y - 22 * s, 24 * s, 22 * s)
    handle = skia.Path()
    handle.addArc(oval(x, floor_y - 44 * s, 15 * s, 16 * s), 180, 180)
    c.drawPath(handle, paint('outline', a, stroke=10 * s))
    c.drawPath(handle, paint(color, a, stroke=5 * s))
    c.drawOval(body, paint(color, a))
    c.drawOval(body, paint('outline', a, stroke=3.5))


def dumbbell_rack(c, x, floor_y, w=330, missing=(), a=1.0, scale=1.0):
    """A two-tier rack seen from the side; the dumbbells point at the camera so their hex ends show."""
    s = scale
    for tier, (ty, lean) in enumerate(((floor_y - 70 * s, 0), (floor_y - 128 * s, -14 * s))):
        c.drawLine(x - w / 2, ty + 10 * s, x + w / 2, ty + 10 * s + lean, paint('outline', a, stroke=12 * s))
        c.drawLine(x - w / 2, ty + 10 * s, x + w / 2, ty + 10 * s + lean, paint('#4A4E58', a, stroke=7 * s))
        n = 6
        for k in range(n):
            if (tier, k) in missing:
                continue
            r = (10 + 2.4 * k + 3 * tier) * s
            hx = x - w / 2 + (k + 0.5) * w / n
            hy = ty - r + lean * (k + 0.5) / n + 8 * s
            hexa = poly([(hx + math.cos(math.radians(60 * i + 30)) * r, hy + math.sin(math.radians(60 * i + 30)) * r)
                         for i in range(6)], True)
            c.drawPath(hexa, paint(IRON, a))
            c.drawCircle(hx, hy, r * 0.32, paint(STEEL, a))
            c.drawPath(hexa, paint('outline', a, stroke=3))
    for lx in (x - w / 2 + 14 * s, x + w / 2 - 14 * s):
        c.drawLine(lx, floor_y, lx - 10 * s, floor_y - 130 * s, paint('outline', a, stroke=12 * s))
        c.drawLine(lx, floor_y, lx - 10 * s, floor_y - 130 * s, paint('#4A4E58', a, stroke=7 * s))


def plate_tree(c, x, floor_y, n=4, a=1.0, scale=1.0):
    s = scale
    c.drawLine(x, floor_y, x, floor_y - 170 * s, paint('outline', a, stroke=12 * s))
    c.drawLine(x, floor_y, x, floor_y - 170 * s, paint('#4A4E58', a, stroke=7 * s))
    c.drawRect(skia.Rect.MakeLTRB(x - 50 * s, floor_y - 10 * s, x + 50 * s, floor_y), paint('#4A4E58', a))
    for k in range(n):
        side = 1 if k % 2 else -1
        _plate(c, x + side * 22 * s, floor_y - (50 + 36 * (k // 2)) * s, (40 - 5 * (k // 2)) * s,
               PLATE_COLORS[k % 3], a)


# --- benches and racks ---------------------------------------------------------------------------------

def bench(c, x, floor_y, length=300, height=104, uprights=None, a=1.0, pad=PAD):
    """Flat bench centred at x; uprights: -1 or +1 puts the bar rack at that end. Returns the pad top y."""
    top = floor_y - height
    for lx in (x - length * 0.36, x + length * 0.36):
        c.drawLine(lx, top + 14, lx, floor_y - 6, paint('outline', a, stroke=14))
        c.drawLine(lx, top + 14, lx, floor_y - 6, paint('#4A4E58', a, stroke=8))
        c.drawRRect(rrect(lx - 30, floor_y - 10, 60, 10, 4), paint('#4A4E58', a))
        c.drawRRect(rrect(lx - 30, floor_y - 10, 60, 10, 4), paint('outline', a, stroke=3))
    c.drawRRect(rrect(x - length / 2, top, length, 22, 9), paint(pad, a))
    c.drawRRect(rrect(x - length / 2 + 6, top + 3, length - 12, 6, 3), paint('#FFFFFF', 0.06 * a))
    c.drawRRect(rrect(x - length / 2, top, length, 22, 9), paint('outline', a, stroke=4))
    if uprights:
        ux = x + uprights * (length / 2 - 18)
        c.drawLine(ux, floor_y - 6, ux, top - 150, paint('outline', a, stroke=14))
        c.drawLine(ux, floor_y - 6, ux, top - 150, paint('#4A4E58', a, stroke=8))
        hook = poly([(ux, top - 120), (ux + uprights * 22, top - 120), (ux + uprights * 22, top - 136)])
        c.drawPath(hook, paint('outline', a, stroke=8))
        c.drawPath(hook, paint(STEEL, a, stroke=4))
    return top


def power_rack(c, x, floor_y, w=250, h=560, hook_y=None, a=1.0, scale=1.0):
    """Squat rack: two uprights, a top bar (for pull-ups), J-hooks and safety arms. Returns the top bar y."""
    s = scale
    w *= s
    h *= s
    top = floor_y - h
    for ux in (x - w / 2, x + w / 2):
        c.drawLine(ux, floor_y, ux, top, paint('outline', a, stroke=16 * s))
        c.drawLine(ux, floor_y, ux, top, paint('#3F434C', a, stroke=10 * s))
        for k in range(14):
            c.drawCircle(ux, top + 40 * s + k * (h - 80 * s) / 14, 2.2 * s, paint('#15161A', a))
    c.drawLine(x - w / 2 - 10 * s, top, x + w / 2 + 10 * s, top, paint('outline', a, stroke=16 * s))
    c.drawLine(x - w / 2 - 10 * s, top, x + w / 2 + 10 * s, top, paint('#3F434C', a, stroke=10 * s))
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2 - 30 * s, floor_y - 10 * s, x + w / 2 + 30 * s, floor_y),
               paint('#3F434C', a))
    hy = hook_y if hook_y is not None else floor_y - 330 * s
    for ux, sgn in ((x - w / 2, 1), (x + w / 2, -1)):
        hook = poly([(ux, hy), (ux + sgn * 20 * s, hy), (ux + sgn * 20 * s, hy - 14 * s)])
        c.drawPath(hook, paint('outline', a, stroke=8 * s))
        c.drawPath(hook, paint(STEEL, a, stroke=4 * s))
        c.drawLine(ux, floor_y - 170 * s, ux + sgn * 34 * s, floor_y - 170 * s, paint('outline', a, stroke=10 * s))
        c.drawLine(ux, floor_y - 170 * s, ux + sgn * 34 * s, floor_y - 170 * s, paint(STEEL, a, stroke=5 * s))
    return top


def treadmill(c, x, floor_y, t=0.0, belt=0.0, screen=1.0, facing=1, a=1.0, scale=1.0):
    """A treadmill centred at x with the console toward `facing`. belt: belt speed (stripes per second).
    Returns the deck top y."""
    s = scale
    c.save()
    c.translate(x, floor_y)
    c.scale(facing * s, s)
    deck = rrect(-170, -42, 330, 36, 12)
    c.drawRRect(deck, paint('#2E3038', a))
    c.drawRRect(rrect(-170, -42, 330, 12, 6), paint('#18191D', a))
    off = (t * belt * 60) % 40
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-160, -42, 150, -30))
    for k in range(-1, 10):
        bx = -160 + k * 40 - off
        c.drawLine(bx, -41, bx + 6, -31, paint('#3A3C44', a, stroke=3))
    c.restore()
    c.drawRRect(deck, paint('outline', a, stroke=4))
    c.drawCircle(-150, -14, 7, paint('#4A4E58', a))
    # upright, console and handrails
    post = poly([(130, -38), (170, -38), (196, -250), (172, -252)], True)
    c.drawPath(post, paint('#3A3D45', a))
    c.drawPath(post, paint('outline', a, stroke=4))
    c.drawLine(176, -205, 70, -200, paint('outline', a, stroke=10))
    c.drawLine(176, -205, 70, -200, paint(STEEL, a, stroke=5))
    con = rrect(150, -292, 74, 50, 8)
    c.drawRRect(con, paint('#2B2D34', a))
    if screen > 0:
        c.drawRRect(rrect(160, -284, 46, 26, 4), paint(mixc('#101820', '#5FD3FF', 0.75 * screen), a))
        c.drawCircle(183, -271, 30, paint('#5FD3FF', 0.25 * screen * a, blur=12, blend='add'))
    c.drawRRect(con, paint('outline', a, stroke=4))
    c.restore()
    return floor_y - 42 * s


def pullup_frame(c, x, floor_y, w=220, h=520, a=1.0):
    top = floor_y - h
    for ux in (x - w / 2, x + w / 2):
        c.drawLine(ux, floor_y, ux, top, paint('outline', a, stroke=16))
        c.drawLine(ux, floor_y, ux, top, paint('#3F434C', a, stroke=10))
    c.drawLine(x - w / 2 - 20, top + 6, x + w / 2 + 20, top + 6, paint('outline', a, stroke=12))
    c.drawLine(x - w / 2 - 20, top + 6, x + w / 2 + 20, top + 6, paint(STEEL, a, stroke=6))
    return top + 6


# --- small things -------------------------------------------------------------------------------------

def water_bottle(c, x, floor_y, color='#3F8FD0', scale=1.0, a=1.0, angle=0.0):
    c.save()
    c.translate(x, floor_y)
    c.rotate(angle)
    c.scale(scale, scale)
    body = rrect(-11, -52, 22, 52, 7)
    c.drawRRect(body, paint(color, a))
    c.drawRRect(rrect(-5, -60, 10, 10, 3), paint('#E9E6DF', a))
    c.drawRect(skia.Rect.MakeLTRB(-11, -36, 11, -24), paint('#FFFFFF', 0.25 * a))
    c.drawRRect(body, paint('outline', a, stroke=3))
    c.drawRRect(rrect(-5, -60, 10, 10, 3), paint('outline', a, stroke=2.5))
    c.restore()


def gym_bag(c, x, floor_y, color='#3B4252', scale=1.0, a=1.0, lift=0.0):
    """A duffel bag on the floor (or held: lift raises it by that many pixels)."""
    s = scale
    y = floor_y - lift
    strap = skia.Path()
    strap.moveTo(x - 40 * s, y - 52 * s)
    strap.quadTo(x, y - 110 * s, x + 40 * s, y - 52 * s)
    c.drawPath(strap, paint('outline', a, stroke=9 * s))
    c.drawPath(strap, paint('#1E2128', a, stroke=4 * s))
    body = rrect(x - 70 * s, y - 60 * s, 140 * s, 60 * s, 26 * s)
    c.drawRRect(body, paint(color, a))
    c.drawLine(x - 50 * s, y - 50 * s, x + 50 * s, y - 50 * s, paint('#000000', 0.3 * a, stroke=3 * s))
    c.drawRRect(body, paint('outline', a, stroke=4))


def towel(c, x, y, color='#E9E6DF', a=1.0, sway=0.0, hook=True):
    """A towel hanging from a hook at (x, y)."""
    if hook:
        c.drawCircle(x, y, 7, paint('#8A8478', a))
        c.drawCircle(x, y, 7, paint('outline', a, stroke=2.5))
    path = poly([(x - 30, y + 4), (x + 30, y + 4), (x + 34 + sway, y + 120), (x - 26 + sway, y + 124)], True)
    c.drawPath(path, paint(color, a))
    c.drawLine(x - 28 + sway * 0.9, y + 104, x + 32 + sway, y + 101, paint('#3F6E8C', 0.8 * a, stroke=5))
    c.drawPath(path, paint('outline', a, stroke=3.5))


def radio(c, x, y, a=1.0, on=0.0, t=0.0):
    """An old portable radio standing on a shelf at y."""
    body = rrect(x - 48, y - 58, 96, 58, 8)
    c.drawRRect(body, paint('#5A4A3C', a))
    c.drawCircle(x - 20, y - 28, 16, paint('#2A2420', a))
    c.drawCircle(x - 20, y - 28, 16, paint('outline', a, stroke=3))
    c.drawRRect(rrect(x + 6, y - 46, 32, 14, 3), paint(mixc('#2A2420', '#F2C26B', 0.8 * on), a))
    c.drawRRect(body, paint('outline', a, stroke=3.5))
    c.drawLine(x + 30, y - 58, x + 52, y - 104, paint('outline', a, stroke=3))
    if on > 0:
        c.drawCircle(x + 22, y - 39, 18, paint('warm', 0.35 * on * a, blur=8, blend='add'))


def chalk_bowl(c, x, y, a=1.0):
    bowl = skia.Path()
    bowl.addArc(oval(x, y - 6, 34, 26), 0, 180)
    bowl.close()
    c.drawPath(bowl, paint('#3A3D45', a))
    c.drawOval(oval(x, y - 6, 34, 7), paint('#F1EEE8', a))
    c.drawPath(bowl, paint('outline', a, stroke=3))


# --- walls, light and signs ---------------------------------------------------------------------------

def ceiling_light(c, x, y, floor_y, on=1.0, w=230, t=0.0, flicker=0.0, seed=0, cone_a=0.07, pool_a=0.16,
                  color='#DCEBFF'):
    """A fluorescent tube fixture hanging at y; flicker 0..1 makes it stutter. Returns the light level used."""
    level = on
    if flicker > 0:
        k = int(t * 14)
        stutter = 1.0 if hrand(k, seed) > 0.35 else 0.15 + 0.3 * hrand(k, seed, 1)
        level = on * (1 - flicker + flicker * stutter)
    c.drawLine(x - w * 0.3, y - 60, x - w * 0.3, y, paint('#2B2B30', stroke=3))
    c.drawLine(x + w * 0.3, y - 60, x + w * 0.3, y, paint('#2B2B30', stroke=3))
    if level > 0.02:
        cone(c, (x, y + 10), w * 0.45, floor_y, w * 1.2, color, cone_a * level, soft=36)
        light_pool(c, x, floor_y, w * 1.5, 70, color, pool_a * level)
        c.drawRRect(rrect(x - w / 2 - 10, y - 4, w + 20, 26, 12), paint(color, 0.35 * level, blur=12, blend='add'))
    c.drawRRect(rrect(x - w / 2, y, w, 16, 6), paint('#2E3038'))
    c.drawRRect(rrect(x - w / 2 + 8, y + 9, w - 16, 9, 4), paint(mixc('#4A4E58', '#F4F8FF', level)))
    c.drawRRect(rrect(x - w / 2, y, w, 16, 6), paint('outline', stroke=3))
    return level


def exit_sign(c, x, y, a=1.0, glow=1.0):
    box = rrect(x - 56, y - 20, 112, 40, 6)
    c.drawRRect(box, paint('#0F3A24', a))
    if glow > 0:
        c.drawRRect(box, paint('#3CFF8A', 0.25 * glow * a, blur=18, blend='add'))
    text(c, 'EXIT', x, y + 11, 30, 'Fredoka-700', mixc('#1D6B40', '#9CFFC2', glow), a)
    c.drawRRect(box, paint('outline', a, stroke=3))


def banner(c, x0, x1, y, h=82, words='NEW YEAR. NEW ME.', loose=0.0, t=0.0, a=1.0, color='#E8B93A',
           ink='#2B2416'):
    """A fabric banner hung from two hooks; loose 0..1 lets the right-hand hook go so it swings down."""
    if a <= 0:
        return
    w = x1 - x0
    ang = 58 * loose + 2 * math.sin(t * 1.3) * loose
    c.save()
    c.translate(x0, y)
    c.rotate(ang)
    sag = 10 + 16 * (1 - loose)
    path = skia.Path()
    path.moveTo(0, 0)
    path.quadTo(w / 2, sag, w, 0)
    path.lineTo(w, h)
    path.quadTo(w / 2, h + sag, 0, h)
    path.close()
    c.drawPath(path, paint(color, a))
    for k in range(5):
        fx = w * (k + 1) / 6
        c.drawLine(fx, 6 + sag * 0.5, fx + 8, h - 4 + sag * 0.5, paint('#000000', 0.07 * a, stroke=10))
    text(c, words, w / 2, h * 0.68 + sag * 0.5, h * 0.56, 'LuckiestGuy', ink, a)
    c.drawPath(path, paint('outline', a, stroke=4))
    c.restore()
    for hx, hy in ((x0, y), (x1, y)):
        if hx == x1 and loose > 0.05:
            continue
        c.drawCircle(hx, hy, 6, paint('#8A8478', a))


def photo_frame(c, x, y, w, h, content=None, label=None, tilt=0.0, a=1.0, label_size=None):
    """A framed photo centred at (x, y). content(c, w, h) draws the picture in a local box (0, 0, w, h)."""
    c.save()
    c.translate(x, y)
    c.rotate(tilt)
    m = w * 0.06
    lab = h * 0.26 if label else m
    fw, fh = w + 2 * m, h + m + lab
    c.drawRect(skia.Rect.MakeXYWH(-fw / 2 + 5, -fh / 2 + 7, fw, fh), paint('#000000', 0.35 * a, blur=6))
    c.drawRect(skia.Rect.MakeXYWH(-fw / 2 - 6, -fh / 2 - 6, fw + 12, fh + 12), paint('#2A2420', a))
    c.drawRect(skia.Rect.MakeXYWH(-fw / 2, -fh / 2, fw, fh), paint('#F2EEE6', a))
    if content is not None:
        c.save()
        c.translate(-w / 2, -fh / 2 + m)
        c.clipRect(skia.Rect.MakeWH(w, h))
        if a < 1:
            c.saveLayerAlpha(None, int(255 * a))
        content(c, w, h)
        if a < 1:
            c.restore()
        c.restore()
    if label:
        text(c, label, 0, fh / 2 - lab * 0.22, label_size or lab * 0.8, 'GochiHand', '#2C2A26', a)
    c.drawRect(skia.Rect.MakeXYWH(-fw / 2 - 6, -fh / 2 - 6, fw + 12, fh + 12), paint('outline', a, stroke=3))
    c.restore()


def mirror(c, x0, x1, top, bottom, a=1.0, glint=0.0):
    r = skia.Rect.MakeLTRB(x0, top, x1, bottom)
    sh = skia.GradientShader.MakeLinear(points=[(x0, top), (x1, bottom)],
                                       colors=[col('#3A4458', a), col('#232A38', a), col('#2E3647', a)])
    c.drawRect(r, paint('#000000', shader=sh))
    for k in range(3):
        sx = x0 + (x1 - x0) * (0.15 + 0.3 * k)
        c.drawLine(sx, bottom - 20, sx + 120, top + 20, paint('#FFFFFF', (0.05 + 0.04 * glint) * a, stroke=14 - 4 * k))
    c.drawRect(r, paint('#585C66', a, stroke=8))
    c.drawRect(r, paint('outline', a, stroke=3))


def rubber_floor(c, x0, x1, top, bottom, color='#15171C'):
    c.drawRect(skia.Rect.MakeLTRB(x0, top, x1, bottom), paint(color))
    for k in range(int((x1 - x0) / 160) + 2):
        sx = x0 + k * 160
        c.drawLine(sx, top, sx - 90, bottom, paint('#0E0F12', 0.6, stroke=3))
    c.drawLine(x0, top, x1, top, paint('#2A2E38', stroke=3))


def jump_rope(c, left, right, phase, a=1.0, low=60.0, reach=None):
    """A skipping rope seen from the side: a loop from the hands that sweeps round the jumper (over the head,
    out in front, under the feet, up behind). phase 0..1 per turn (0 = overhead, 0.5 = under the feet)."""
    ang = phase * math.tau
    mid = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
    up, down, out = 205.0, 110.0 + low, 95.0
    ry = up if math.cos(ang) > 0 else down
    far = (mid[0] + math.sin(ang) * out, mid[1] - math.cos(ang) * ry)
    k = 0.5 + 0.5 * abs(math.sin(ang))
    path = skia.Path()
    path.moveTo(*left)
    path.quadTo(far[0] - 22, far[1], *far)
    path.quadTo(far[0] + 22, far[1], *right)
    c.drawPath(path, paint('outline', a, stroke=7))
    c.drawPath(path, paint('#D9DCE2', a * k, stroke=3.5))
    for h in (left, right):
        c.drawLine(h[0], h[1], h[0], h[1] + 18, paint('#C8463D', a, stroke=7))
