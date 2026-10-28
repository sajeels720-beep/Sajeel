"""Props for home, study and school scenes, drawn in the house style (flat fills, dark outlines)."""
from __future__ import annotations

import math

import skia

from .core import hrand, hrange, noise1
from .draw import OUTLINE_W, col, cone, light_pool, mixc, oval, paint, poly, rrect, smooth_path, text, text_width

BOOK_COLORS = ['#7A5C8F', '#4F7A6B', '#B0624A', '#3F5F8A', '#C9A54E', '#6B6B78', '#8C4A4A', '#4A6B8C',
               '#A8875A', '#5E7A3F']


# --- the study desk ---------------------------------------------------------------------------

def desk_lamp(c, x, y, on=1.0, facing=1, reach=150):
    """Angle-poise lamp standing on a surface at (x, y), head leaning toward facing."""
    c.drawOval(oval(x, y - 5, 34, 9), paint('#2B2D33'))
    c.drawOval(oval(x, y - 5, 34, 9), paint('outline', stroke=3))
    elbow = (x - facing * 30, y - 120)
    head = (x + facing * (reach - 40), y - 170)
    c.drawLine(x, y - 8, *elbow, paint('#3A3D45', stroke=8))
    c.drawLine(*elbow, *head, paint('#3A3D45', stroke=7))
    c.drawCircle(*elbow, 7, paint('#2B2D33'))
    tip = (head[0] + facing * 38, head[1] + 36)
    dx, dy = tip[0] - head[0], tip[1] - head[1]
    dl = math.hypot(dx, dy)
    ux, uy = dx / dl, dy / dl
    px, py = -uy, ux
    if on > 0:
        cone(c, tip, 26, y + 4, 190, 'warm', 0.16 * on, soft=26)
        light_pool(c, tip[0], y, 300, 70, 'warm', 0.38 * on)
        light_pool(c, tip[0], tip[1], 160, 120, 'warm', 0.35 * on)
    shade = poly([(head[0] - ux * 8 + px * 10, head[1] - uy * 8 + py * 10),
                  (head[0] - ux * 8 - px * 10, head[1] - uy * 8 - py * 10),
                  (tip[0] + ux * 8 - px * 34, tip[1] + uy * 8 - py * 34),
                  (tip[0] + ux * 8 + px * 34, tip[1] + uy * 8 + py * 34)], True)
    c.drawPath(shade, paint(mixc('#4E6A84', '#6F8FAD', on)))
    c.drawPath(shade, paint('outline', stroke=3.5))
    if on > 0:
        c.drawCircle(tip[0] + ux * 6, tip[1] + uy * 6, 11, paint('#FFE7B0', on))
        c.drawCircle(tip[0] + ux * 6, tip[1] + uy * 6, 26, paint('warm', 0.5 * on, blur=12, blend='add'))
    return tip


def study_desk(c, x, floor_y, w=500, drawer=0.0, glow=0.0, jolt=0.0, lamp=1.0, lamp_x=None, t=0.0):
    """Wooden desk seen from the front, a drawer unit on the right with a lockable top drawer.

    drawer: 0 closed .. 1 open; glow: red light leaking out of the closed drawer; jolt: the drawer
    being banged from inside (0..1). Returns dict(top, drawer_rect, keyhole)."""
    top = floor_y - 158
    wood, dark = '#7A5638', '#5A3E28'
    # legs and drawer unit
    c.drawRect(skia.Rect.MakeLTRB(x + 14, top + 18, x + 32, floor_y), paint(dark))
    c.drawRect(skia.Rect.MakeLTRB(x + 14, top + 18, x + 32, floor_y), paint('outline', stroke=3))
    ux0, ux1 = x + w - 170, x + w - 14
    c.drawRect(skia.Rect.MakeLTRB(ux0, top + 18, ux1, floor_y), paint(wood))
    c.drawRect(skia.Rect.MakeLTRB(ux0, top + 18, ux1, floor_y), paint('outline', stroke=4))
    # bottom drawer
    c.drawRRect(rrect(ux0 + 10, top + 90, ux1 - ux0 - 20, floor_y - top - 104, 5), paint('#86613F'))
    c.drawRRect(rrect(ux0 + 10, top + 90, ux1 - ux0 - 20, floor_y - top - 104, 5), paint('outline', stroke=3))
    c.drawRRect(rrect((ux0 + ux1) / 2 - 22, top + 104, 44, 9, 4), paint('#C9B48A'))
    # top drawer: shakes when banged, slides out when open
    jx = noise1(t * 60, 3) * 7 * jolt
    jy = noise1(t * 60, 4) * 4 * jolt - 3 * jolt
    dx0, dy0, dw, dh = ux0 + 10, top + 28 + jy, ux1 - ux0 - 20, 52
    if drawer > 0:
        inner = poly([(dx0 - 6 * drawer, dy0 + 6 - 30 * drawer), (dx0 + dw + 6 * drawer, dy0 + 6 - 30 * drawer),
                      (dx0 + dw, dy0 + 6), (dx0, dy0 + 6)], True)
        c.drawPath(inner, paint('#1A120C'))
        c.drawPath(inner, paint('outline', stroke=3))
        dy0 += 26 * drawer
        dx0 -= 8 * drawer
        dw += 16 * drawer
    if glow > 0:
        c.drawRect(skia.Rect.MakeLTRB(dx0 - 4, dy0 - 4, dx0 + dw + 4, dy0 + dh + 4),
                   paint('red', 0.9 * glow, stroke=7, blur=8, blend='add'))
        light_pool(c, dx0 + dw / 2, dy0 + dh / 2, 220, 120, 'red', 0.22 * glow)
    face = rrect(dx0 + jx, dy0, dw, dh, 5)
    c.drawRRect(face, paint('#8E6845'))
    c.drawRRect(face, paint('outline', stroke=3.5))
    kx, ky = dx0 + jx + dw / 2, dy0 + dh / 2
    c.drawRRect(rrect(kx - 26, ky + 6, 52, 9, 4), paint('#C9B48A'))
    c.drawCircle(kx, ky - 8, 7, paint('#C9B48A'))
    c.drawCircle(kx, ky - 8, 7, paint('outline', stroke=2.5))
    c.drawRect(skia.Rect.MakeLTRB(kx - 1.5, ky - 8, kx + 1.5, ky - 2), paint('outline'))
    # top
    c.drawRect(skia.Rect.MakeLTRB(x - 10, top, x + w + 10, top + 20), paint(wood))
    c.drawLine(x - 10, top + 6, x + w + 10, top + 6, paint('#9A7250', stroke=3))
    c.drawRect(skia.Rect.MakeLTRB(x - 10, top, x + w + 10, top + 20), paint('outline', stroke=4))
    if lamp is not None:
        desk_lamp(c, lamp_x if lamp_x is not None else x + w - 70, top, on=lamp, facing=-1)
    return dict(top=top, drawer=(dx0 + jx, dy0, dw, dh), keyhole=(kx, ky - 8))


# --- books ----------------------------------------------------------------------------------------

def book(c, x, y, w, h, color, angle=0.0, open_amt=0.0, a=1.0):
    """A closed book lying flat (seen from the side), bottom-left corner at (x, y)."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    r = skia.Rect.MakeLTRB(0, -h, w, 0)
    c.drawRect(r, paint(color, a))
    c.drawRect(skia.Rect.MakeLTRB(w - 8, -h + 4, w - 2, -4), paint('#EFE8DA', a))
    c.drawLine(10, -h / 2, w * 0.55, -h / 2, paint('#FFFFFF', 0.35 * a, stroke=3))
    c.drawRect(r, paint('outline', a, stroke=3))
    c.restore()


def book_pile(c, x, base_y, n, seed=1, width=(110, 150), thick=(18, 30), jitter=10, a=1.0, sway=0.0):
    """A stack of n books centred on x; returns the top y. sway tilts the upper books (a wobble)."""
    y = base_y
    for i in range(n):
        w = hrange(width[0], width[1], i, seed)
        h = hrange(thick[0], thick[1], i, seed, 1)
        off = (hrand(i, seed, 2) - 0.5) * 2 * jitter + sway * i * i * 0.6
        ang = (hrand(i, seed, 3) - 0.5) * 4 + sway * i * 0.25
        book(c, x - w / 2 + off, y, w, h, BOOK_COLORS[int(hrand(i, seed, 4) * len(BOOK_COLORS))], ang, a=a)
        y -= h - 1
    return y


def book_mountain(c, cx, base_y, height, width, seed=5, sway=0.0, a=1.0):
    """Columns of books stacked into a rough pyramid `height` tall and `width` wide."""
    cols = max(1, int(width / 120))
    order = sorted(range(cols), key=lambda k: -abs(k - (cols - 1) / 2))  # outer columns first
    for k in order:
        u = (k + 0.5) / cols * 2 - 1
        col_h = height * max(0.08, (1 - abs(u)) ** 0.75) * (0.85 + 0.3 * hrand(k, seed))
        n = max(1, int(col_h / 24))
        x = cx + u * width / 2
        book_pile(c, x, base_y, n, seed=seed * 31 + k, width=(105, 140), jitter=12, a=a,
                  sway=sway * (1 - abs(u)))


# --- wall things --------------------------------------------------------------------------------

def calendar(c, x, y, w=200, h=230, crossed=0, circle_day=None, label='FINALS', t=0.0, label_a=1.0):
    """Wall calendar (top-left at x, y): days 1..35 in a 7x5 grid; the first `crossed` get a red X."""
    c.drawRRect(rrect(x + 6, y + 8, w, h, 6), paint('#000000', 0.35, blur=6))
    page = rrect(x, y, w, h, 6)
    c.drawRRect(page, paint('#F1ECE1'))
    c.drawRect(skia.Rect.MakeLTRB(x, y, x + w, y + 46), paint('#C8463D'))
    for k in range(4):
        rx = x + 30 + k * (w - 60) / 3
        c.drawCircle(rx, y + 2, 7, paint('#2B2B30'))
    c.drawRRect(page, paint('outline', stroke=4))
    gx0, gy0 = x + 14, y + 62
    cw, ch = (w - 28) / 7, (h - 76) / 5
    for d in range(35):
        cx, cy = gx0 + (d % 7) * cw, gy0 + (d // 7) * ch
        c.drawRect(skia.Rect.MakeXYWH(cx + 2, cy + 2, cw - 4, ch - 4), paint('#D8D1C2', stroke=1.5))
        if d < crossed:
            c.drawLine(cx + 6, cy + 6, cx + cw - 6, cy + ch - 6, paint('#D23A2E', stroke=3.5))
            c.drawLine(cx + cw - 6, cy + 6, cx + 6, cy + ch - 6, paint('#D23A2E', stroke=3.5))
        if circle_day is not None and d == circle_day:
            c.drawOval(oval(cx + cw / 2, cy + ch / 2, cw * 0.62, ch * 0.62), paint('#D23A2E', stroke=4))
            c.drawOval(oval(cx + cw / 2, cy + ch / 2, cw * 0.9, ch * 0.9), paint('red', 0.5, stroke=6, blur=6, blend='add'))
            if label and label_a > 0:
                text(c, label, cx + cw / 2, cy - 8, 22, 'PatrickHand', '#D23A2E', label_a)
    return (x, y, w, h)


def sticky(c, x, y, txt='TOMORROW', angle=0.0, size=96, color='#F6D654', a=1.0, scale=1.0, font_name='GochiHand',
           ink='#2C2A26'):
    """A square sticky note centred at (x, y) with handwritten text."""
    if a <= 0 or scale <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.scale(scale, scale)
    s = size / 2
    c.drawRect(skia.Rect.MakeLTRB(-s + 4, -s + 6, s + 4, s + 6), paint('#000000', 0.3 * a, blur=5))
    note = poly([(-s, -s), (s, -s), (s, s - 10), (s - 12, s), (-s, s)], True)
    c.drawPath(note, paint(color, a))
    c.drawRect(skia.Rect.MakeLTRB(-s, -s, s, -s + 12), paint('#000000', 0.06 * a))
    c.drawPath(poly([(s, s - 10), (s - 12, s - 10), (s - 12, s)], True), paint(mixc(color, '#000000', 0.2), a))
    c.drawPath(note, paint('outline', a, stroke=2.5))
    lines = txt.split('\n')
    fs = size * 0.3
    for line in lines:
        while text_width(line, font_name, fs) > size * 0.86 and fs > 8:
            fs *= 0.92
    for k, line in enumerate(lines):
        yy = (k - (len(lines) - 1) / 2) * fs * 1.05 + fs * 0.35
        text(c, line, 0, yy, fs, font_name, ink, a)
    c.restore()


def alarm_clock(c, x, y, scale=1.0, ring=0.0, t=0.0, hour=7.0):
    """Twin-bell alarm clock standing on (x, y); ring 0..1 shakes it and draws ring lines."""
    sx = noise1(t * 70, 5) * 5 * ring
    rot = noise1(t * 70, 6) * 8 * ring
    c.save()
    c.translate(x + sx, y)
    c.rotate(rot)
    c.scale(scale, scale)
    for side in (-1, 1):
        c.drawLine(side * 18, -6, side * 28, 4, paint('#2B2B30', stroke=5))
        c.drawCircle(side * 26, -66, 14, paint('#C8463D'))
        c.drawCircle(side * 26, -66, 14, paint('outline', stroke=3))
    c.drawLine(-14, -78, 14, -78, paint('#2B2B30', stroke=4))
    c.drawCircle(0, -40, 34, paint('#C8463D'))
    c.drawCircle(0, -40, 34, paint('outline', stroke=3.5))
    c.drawCircle(0, -40, 26, paint('#F4F1EA'))
    for k in range(12):
        a = k * math.tau / 12
        c.drawLine(math.sin(a) * 21, -40 - math.cos(a) * 21, math.sin(a) * 24, -40 - math.cos(a) * 24,
                   paint('outline', stroke=2))
    ha = (hour % 12) / 12 * math.tau
    ma = (hour % 1) * math.tau
    c.drawLine(0, -40, math.sin(ha) * 13, -40 - math.cos(ha) * 13, paint('outline', stroke=3.5))
    c.drawLine(0, -40, math.sin(ma) * 20, -40 - math.cos(ma) * 20, paint('outline', stroke=2.5))
    c.restore()
    if ring > 0.05:
        for side in (-1, 1):
            for k in range(3):
                r = (52 + k * 14) * scale
                arc = skia.Path()
                arc.addArc(oval(x, y - 50 * scale, r, r), (-60 if side > 0 else 200) + k * 4, 40)
                c.drawPath(arc, paint('#F4F1EA', ring * (0.8 - 0.2 * k), stroke=4))


def digital_clock(c, x, y, label='5:00', scale=1.0, color='#FF4A3D', glow=1.0):
    """Small bedside digital clock; (x, y) is the bottom centre."""
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    body = rrect(-64, -52, 128, 52, 10)
    c.drawRRect(body, paint('#1C1D22'))
    c.drawRRect(body, paint('outline', stroke=3.5))
    c.drawRRect(rrect(-54, -44, 108, 36, 5), paint('#0B0B0E'))
    if glow > 0:
        text(c, label, 0, -15, 34, 'Inter-Bold', color, glow, glow=color, glow_a=0.8, glow_r=10)
    c.restore()


def wall_clock(c, x, y, r=60, hour=10.0):
    c.drawCircle(x + 4, y + 6, r, paint('#000000', 0.3, blur=6))
    c.drawCircle(x, y, r, paint('#F4F1EA'))
    c.drawCircle(x, y, r, paint('#2B2B30', stroke=8))
    c.drawCircle(x, y, r + 4, paint('outline', stroke=3))
    for k in range(12):
        a = k * math.tau / 12
        c.drawLine(x + math.sin(a) * r * 0.78, y - math.cos(a) * r * 0.78, x + math.sin(a) * r * 0.9,
                   y - math.cos(a) * r * 0.9, paint('outline', stroke=3 if k % 3 == 0 else 2))
    ha = (hour % 12) / 12 * math.tau
    ma = (hour % 1) * math.tau
    c.drawLine(x, y, x + math.sin(ha) * r * 0.5, y - math.cos(ha) * r * 0.5, paint('outline', stroke=6))
    c.drawLine(x, y, x + math.sin(ma) * r * 0.75, y - math.cos(ma) * r * 0.75, paint('outline', stroke=4))
    c.drawLine(x, y, x + math.sin(ma * 60) * r * 0.8, y - math.cos(ma * 60) * r * 0.8, paint('#C8463D', stroke=2))
    c.drawCircle(x, y, 5, paint('outline'))


# --- the father's shoes ----------------------------------------------------------------------------

def shoe(c, x, y, scale=1.0, facing=1, torn=0.0, tape=0.0, stitched=0.0, polish=0.0, color='#5A3E2B'):
    """A worn leather work shoe in side view, sole resting on y, toe toward `facing`.

    torn: the sole peels away from the toe (0..1); tape: grey tape wrapped round the toe;
    stitched: neat new stitching along the sole; polish: a fresh shine."""
    c.save()
    c.translate(x, y)
    c.scale(scale * facing, scale)
    # sole: heel to toe; the toe part bends down when torn
    gap = 18 * torn
    sole = skia.Path()
    sole.moveTo(-92, 0)
    sole.lineTo(10, 0)
    sole.cubicTo(50, 0, 78, 2 + gap * 0.5, 96, 4 + gap)
    sole.cubicTo(104, 8 + gap, 100, 16 + gap, 88, 16 + gap)
    sole.cubicTo(60, 16 + gap * 0.6, 30, 14, 10, 14)
    sole.lineTo(-92, 14)
    sole.close()
    c.drawPath(sole, paint('#2A2420'))
    c.drawPath(sole, paint('outline', stroke=3.5))
    if torn > 0.05:
        # the dark gap between the upper and the peeled sole
        c.drawPath(poly([(14, -1), (96, -2), (96, 4 + gap), (14, 1)], True), paint('#0E0B09'))
    upper = skia.Path()
    upper.moveTo(-90, 0)
    upper.lineTo(-90, -62)
    upper.cubicTo(-88, -74, -60, -76, -40, -70)
    upper.lineTo(-6, -58)
    upper.cubicTo(30, -52, 70, -40, 90, -22)
    upper.cubicTo(102, -12, 100, -2, 92, 0)
    upper.close()
    c.drawPath(upper, paint(color))
    c.save()
    c.clipPath(upper, doAntiAlias=True)
    c.drawOval(oval(-20, -8, 120, 18), paint('#000000', 0.2))
    if polish > 0:
        hl = skia.Path()
        hl.moveTo(20, -46)
        hl.cubicTo(50, -42, 74, -30, 86, -16)
        c.drawPath(hl, paint('#FFFFFF', 0.55 * polish, stroke=6))
        c.drawCircle(40, -40, 5, paint('#FFFFFF', 0.7 * polish))
    else:
        for k in range(5):  # scuffs and creases
            px, py = hrange(-70, 70, k, 9), hrange(-50, -14, k, 10)
            c.drawLine(px, py, px + 16, py + 4, paint('#2A1C12', 0.5, stroke=2))
    c.restore()
    c.drawPath(upper, paint('outline', stroke=3.5))
    # laces
    for k in range(4):
        lx = -30 + k * 14
        c.drawLine(lx, -64 + k * 3, lx + 12, -54 + k * 3, paint('#D8D0BE', stroke=3))
    if tape > 0:
        band = poly([(40, -48), (64, -40), (80, 14 + gap), (54, 14 + gap * 0.7)], True)
        c.drawPath(band, paint('#9A9A9E', 0.95 * tape))
        c.drawLine(52, -44, 66, 12 + gap * 0.8, paint('#BEBEC2', 0.8 * tape, stroke=2))
        c.drawPath(band, paint('outline', tape, stroke=3))
    if stitched > 0:
        n = int(14 * stitched)
        for k in range(n):
            sx = -84 + k * 12.5
            c.drawLine(sx, 4, sx + 6, 4, paint('#E8DFC8', stroke=2.5))
    c.restore()


# --- doors, tables, school ------------------------------------------------------------------------

def front_door(c, x, floor_y, w=180, h=380, open_amt=0.0, outside='#1B2740', light=0.0, light_color='#9DB7FF',
               hinge='left', part='all'):
    """Front door in a frame; open_amt swings it inward to reveal `outside`, spilling light on the floor.

    part: 'all', or 'back' (frame and opening) then 'leaf' (the door itself) with a character between."""
    top = floor_y - h
    if part == 'leaf':
        _door_leaf(c, x, top, w, h, floor_y, open_amt, hinge)
        return (x, top, w, h)
    c.drawRect(skia.Rect.MakeLTRB(x - 14, top - 14, x + w + 14, floor_y), paint('#3A3027'))
    c.drawRect(skia.Rect.MakeLTRB(x - 14, top - 14, x + w + 14, floor_y), paint('outline', stroke=4))
    opening = skia.Rect.MakeLTRB(x, top, x + w, floor_y)
    c.drawRect(opening, paint(outside))
    if open_amt > 0 and light > 0:
        sh = skia.GradientShader.MakeLinear(points=[(x, top), (x, floor_y)],
                                           colors=[col(mixc(outside, '#FFFFFF', 0.15)), col(outside)])
        c.drawRect(opening, paint('#000000', shader=sh))
        spill = poly([(x, floor_y), (x + w, floor_y), (x + w + 260 * light, floor_y + 200), (x - 60, floor_y + 200)], True)
        c.drawPath(spill, paint(light_color, 0.25 * light * open_amt, blur=30, blend='add'))
        light_pool(c, x + w / 2, top + h * 0.45, w * 1.6, h * 0.7, light_color, 0.2 * light * open_amt)
    if part == 'all':
        _door_leaf(c, x, top, w, h, floor_y, open_amt, hinge)
    return (x, top, w, h)


def _door_leaf(c, x, top, w, h, floor_y, open_amt, hinge):
    leaf_w = w * (1 - 0.85 * open_amt)
    lx = x if hinge == 'left' else x + w - leaf_w
    leaf = skia.Rect.MakeLTRB(lx, top, lx + leaf_w, floor_y)
    c.drawRect(leaf, paint(mixc('#6B4A33', '#3E2B1E', open_amt)))
    if leaf_w > 30:
        for k in range(2):
            c.drawRect(skia.Rect.MakeLTRB(lx + leaf_w * 0.14, top + 30 + k * (h / 2 - 10),
                                          lx + leaf_w * 0.86, top + h / 2 - 20 + k * (h / 2 - 10)),
                       paint('#000000', 0.18, stroke=4))
        kx = lx + leaf_w - 22 if hinge == 'left' else lx + 22
        c.drawCircle(kx, top + h * 0.55, 8, paint('#C9B48A'))
        c.drawCircle(kx, top + h * 0.55, 8, paint('outline', stroke=2.5))
    c.drawRect(leaf, paint('outline', stroke=4))


def light_switch(c, x, y, on=True):
    c.drawRRect(rrect(x - 14, y - 22, 28, 44, 4), paint('#E8E3D8'))
    c.drawRRect(rrect(x - 14, y - 22, 28, 44, 4), paint('outline', stroke=2.5))
    c.drawRRect(rrect(x - 5, y - 12 if on else y, 10, 12, 2), paint('#BEB8AA'))


def stool(c, x, floor_y, h=110, color='#5A4535'):
    c.drawRect(skia.Rect.MakeLTRB(x - 44, floor_y - h, x + 44, floor_y - h + 14), paint(color))
    c.drawRect(skia.Rect.MakeLTRB(x - 44, floor_y - h, x + 44, floor_y - h + 14), paint('outline', stroke=3.5))
    for lx in (-36, 26):
        c.drawLine(x + lx + 5, floor_y - h + 14, x + lx + 5 + (-8 if lx < 0 else 8), floor_y, paint(color, stroke=9))
    return floor_y - h


def lunchbox(c, x, y, scale=1.0, color='#3F6E8C'):
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    c.drawRRect(rrect(-40, -46, 80, 46, 8), paint(color))
    c.drawRRect(rrect(-40, -46, 80, 46, 8), paint('outline', stroke=3))
    c.drawLine(-40, -30, 40, -30, paint('outline', stroke=2.5))
    handle = skia.Path()
    handle.moveTo(-16, -46)
    handle.cubicTo(-16, -64, 16, -64, 16, -46)
    c.drawPath(handle, paint('#2B2B30', stroke=5))
    c.restore()


def table(c, x, floor_y, w=460, h=150, color='#8A6544', cloth=None):
    top = floor_y - h
    for lx in (x + 20, x + w - 36):
        c.drawRect(skia.Rect.MakeLTRB(lx, top + 14, lx + 16, floor_y), paint(mixc(color, '#000000', 0.25)))
    c.drawRect(skia.Rect.MakeLTRB(x, top, x + w, top + 18), paint(color))
    c.drawRect(skia.Rect.MakeLTRB(x, top, x + w, top + 18), paint('outline', stroke=4))
    if cloth:
        c.drawRect(skia.Rect.MakeLTRB(x + 30, top - 2, x + w - 30, top + 40), paint(cloth))
        c.drawRect(skia.Rect.MakeLTRB(x + 30, top - 2, x + w - 30, top + 40), paint('outline', stroke=3))
    return top


def mug(c, x, y, color='#D9D3C4', steam=0.0, t=0.0):
    c.drawRRect(rrect(x - 16, y - 40, 32, 40, 6), paint(color))
    c.drawRRect(rrect(x - 16, y - 40, 32, 40, 6), paint('outline', stroke=3))
    handle = skia.Path()
    handle.addArc(oval(x + 18, y - 22, 10, 12), -90, 180)
    c.drawPath(handle, paint('outline', stroke=4))
    for k in range(3 if steam > 0 else 0):
        path = skia.Path()
        sx = x - 8 + k * 8
        path.moveTo(sx, y - 46)
        for j in range(1, 6):
            path.lineTo(sx + math.sin(t * 2 + j + k) * 5, y - 46 - j * 9)
        c.drawPath(path, paint('#FFFFFF', 0.35 * steam, stroke=2.5))


def laptop_back(c, x, y, scale=1.0, glow=1.0, color='#9BA3AE'):
    """An open laptop seen from behind (lid toward us, screen hidden); (x, y) is the hinge centre."""
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    if glow > 0:
        light_pool(c, 0, -60, 160, 120, '#CFE4FF', 0.25 * glow)
    lid = poly([(-80, 0), (80, 0), (72, -112), (-72, -112)], True)
    c.drawPath(lid, paint(color))
    c.drawPath(lid, paint('outline', stroke=3.5))
    c.drawCircle(0, -58, 10, paint('#FFFFFF', 0.5))
    c.drawRect(skia.Rect.MakeLTRB(-86, 0, 86, 8), paint('#7E8692'))
    c.drawRect(skia.Rect.MakeLTRB(-86, 0, 86, 8), paint('outline', stroke=3))
    c.restore()


def school_desk(c, x, floor_y, w=210, scale=1.0, paper=True, color='#8A6A4A', a=1.0):
    """Exam-hall desk (front view, scaled for depth); returns the desk top y in world coordinates."""
    c.save()
    c.translate(x, floor_y)
    c.scale(scale, scale)
    if a < 1:
        c.saveLayerAlpha(None, int(255 * a))
    h = 120
    for lx in (-w / 2 + 10, w / 2 - 22):
        c.drawRect(skia.Rect.MakeLTRB(lx, -h + 10, lx + 12, 0), paint('#3E4048'))
    c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h, w / 2, -h + 14), paint(color))
    c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h, w / 2, -h + 14), paint('outline', stroke=3.5))
    if paper:
        c.drawPath(poly([(-60, -h), (54, -h), (62, -h - 6), (-52, -h - 6)], True), paint('#F4F1EA'))
    if a < 1:
        c.restore()
    c.restore()
    return floor_y - h * scale


def exam_paper(c, x, y, w=520, h=680, blur=0.0, written=0.0, angle=0.0, seed=3, title='FINAL EXAM', t=0.0):
    """A close-up exam sheet centred at (x, y). blur 0..1 melts the questions away (his mind going blank);
    written 0..1 fills the answer lines with pencil."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.drawRect(skia.Rect.MakeLTRB(-w / 2 + 8, -h / 2 + 10, w / 2 + 8, h / 2 + 10), paint('#000000', 0.35, blur=10))
    c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), paint('#F4F1EA'))
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-w / 2 + 4, -h / 2 + 4, w / 2 - 4, h / 2 - 4))
    ink = mixc('#2C2A26', '#F4F1EA', min(1.0, blur * 1.1))
    text(c, title, 0, -h / 2 + 60, 40, 'PatrickHand', ink)
    c.drawLine(-w / 2 + 40, -h / 2 + 80, w / 2 - 40, -h / 2 + 80, paint(ink, stroke=2.5))
    y0 = -h / 2 + 120
    k = 0
    while y0 < h / 2 - 60:
        # a question: a number and a few words of scribble
        drift = blur * 14
        qx = -w / 2 + 40 + noise1(t * 3 + k, seed) * drift
        qy = y0 + noise1(t * 3 + k, seed + 9) * drift
        text(c, f'{k + 1}.', qx, qy + 6, 26, 'PatrickHand', ink, 1 - 0.6 * blur)
        words = int(hrange(3, 6, k, seed))
        wx = qx + 34
        for j in range(words):
            ww = min(hrange(40, 90, k, j, seed), w / 2 - 36 - wx)
            if ww < 12:
                break
            c.drawLine(wx, qy, wx + ww, qy, paint(ink, 1 - 0.7 * blur, stroke=5 + 6 * blur, blur=8 * blur))
            wx += ww + 12
        # answer lines
        for line in range(2):
            ly = qy + 40 + line * 30
            c.drawLine(-w / 2 + 70, ly, w / 2 - 40, ly, paint('#C9C2B2', stroke=1.5))
            fill = max(0.0, min(1.0, written * 6 - (k * 2 + line) * 0.5))
            if fill > 0:
                pts = []
                x1 = -w / 2 + 74 + (w - 120) * fill
                xx = -w / 2 + 74
                while xx < x1:
                    pts.append((xx, ly - 8 + math.sin(xx * 0.31 + k * 2 + line) * 5))
                    xx += 7
                if len(pts) > 1:
                    c.drawPath(smooth_path(pts), paint('#3A3F52', stroke=2.5))
        y0 += 130
        k += 1
    c.restore()
    c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), paint('outline', stroke=4))
    c.restore()


def test_result(c, x, y, w=300, h=380, score='42%', score_color='#D23A2E', stamp=1.0, angle=0.0):
    """A marked practice test with a big circled score, centred at (x, y)."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.drawRect(skia.Rect.MakeLTRB(-w / 2 + 6, -h / 2 + 8, w / 2 + 6, h / 2 + 8), paint('#000000', 0.35, blur=8))
    c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), paint('#F4F1EA'))
    c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), paint('outline', stroke=3.5))
    text(c, 'PRACTICE TEST', -w / 2 + 22, -h / 2 + 38, 24, 'PatrickHand', '#2C2A26', align='left')
    for k in range(max(2, int((h - 190) / 40))):
        ly = -h / 2 + 170 + k * 40
        c.drawLine(-w / 2 + 24, ly, w / 2 - 24, ly, paint('#C9C2B2', stroke=1.5))
        c.drawLine(-w / 2 + 24, ly - 8, -w / 2 + 24 + hrange(80, 200, k, 7), ly - 8, paint('#3A3F52', stroke=2.5))
        mark_ok = hrand(k, len(score)) < (float(score.rstrip('%')) / 100 if score.rstrip('%').isdigit() else 0.5)
        mx = w / 2 - 40
        if mark_ok:
            c.drawPath(poly([(mx - 10, ly - 14), (mx - 2, ly - 4), (mx + 14, ly - 24)]), paint(score_color, stroke=4))
        else:
            c.drawLine(mx - 10, ly - 22, mx + 8, ly - 4, paint(score_color, stroke=4))
            c.drawLine(mx + 8, ly - 22, mx - 10, ly - 4, paint(score_color, stroke=4))
    if stamp > 0:
        s = 0.6 + 0.4 * stamp
        c.save()
        c.translate(w / 2 - 74, -h / 2 + 102)
        c.scale(s, s)
        c.drawOval(oval(0, -12, 62, 44), paint(score_color, stamp, stroke=5))
        text(c, score, 0, 4, 48, 'CaveatBrush', score_color, stamp)
        c.restore()
    c.restore()
