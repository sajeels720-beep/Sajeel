"""Props and minimal sets drawn in the house style (flat fills, dark outlines, light pools)."""
from __future__ import annotations

import math

import skia

from .core import hrand, hrange, noise1
from .draw import (OUTLINE_W, col, cone, light_pool, mixc, oval, paint, poly, radial, rrect,
                   smooth_path, text)

# --- guitar ----------------------------------------------------------------------------

_GUITAR_BODY = [(-76, 0), (-68, -31), (-42, -46), (-14, -39), (2, -27), (18, -34), (40, -33), (57, -19),
                (62, 0), (57, 19), (40, 33), (18, 34), (2, 27), (-14, 39), (-42, 46), (-68, 31)]


def guitar_local(gx, gy, angle, scale, lx, ly):
    """Point in guitar-local coordinates -> parent coordinates."""
    a = math.radians(angle)
    x, y = lx * scale, ly * scale
    return gx + x * math.cos(a) - y * math.sin(a), gy + x * math.sin(a) + y * math.cos(a)


def guitar(c, x, y, angle=-18.0, scale=1.0, dust=0.0, shine=1.0, strum=0.0, t=0.0, body='wood', a=1.0):
    """Acoustic guitar; origin at the sound hole region, neck toward +x."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.scale(scale, scale)
    if a < 1:
        c.saveLayerAlpha(None, int(255 * a))
    body_path = smooth_path(_GUITAR_BODY, closed=True)
    # neck and headstock behind the body
    neck = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(50, -8, 182, 8), 3, 3)
    c.drawRRect(neck, paint('#6E4320'))
    c.drawRRect(neck, paint('outline', stroke=4))
    for k in range(9):
        fx = 64 + k * 13.5
        c.drawLine(fx, -8, fx, 8, paint('#CFC6B5', 0.8, stroke=2))
    head = poly([(178, -10), (210, -13), (214, 0), (210, 13), (178, 10)], True)
    c.drawPath(head, paint('#5A3518'))
    c.drawPath(head, paint('outline', stroke=4))
    for k in range(3):
        px = 186 + k * 9
        for sgn in (-1, 1):
            c.drawCircle(px, sgn * (13 + 4), 3.6, paint('#D8D2C4'))
            c.drawCircle(px, sgn * (13 + 4), 3.6, paint('outline', stroke=2))
    # body
    c.drawPath(body_path, paint(body))
    c.save()
    c.clipPath(body_path, doAntiAlias=True)
    c.drawOval(oval(-30, 26, 70, 30), paint('wood_dark', 0.35))
    if shine:
        arc = skia.Path()
        arc.addArc(oval(-36, -2, 34, 34), 200, 70)
        c.drawPath(arc, paint('#FFFFFF', 0.25 * shine, stroke=5))
    c.restore()
    c.drawPath(body_path, paint('outline', stroke=OUTLINE_W))
    c.drawCircle(18, 0, 13, paint('#2A170B'))
    c.drawCircle(18, 0, 16, paint('#E8D6B8', 0.55, stroke=2.5))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-44, -13, -34, 13), 3, 3), paint('#3B2412'))
    # strings, vibrating while strummed
    for k in range(6):
        sy = -5 + k * 2
        amp = strum * 1.6 * math.sin(t * 90 + k * 1.3)
        path = skia.Path()
        path.moveTo(-40, sy)
        path.quadTo(70, sy + amp, 180, sy * 0.8)
        c.drawPath(path, paint('#EDE7DA', 0.85, stroke=1.2))
    if dust > 0:
        c.save()
        c.clipPath(body_path, doAntiAlias=True)
        c.drawPaint(paint('#9A968C', 0.35 * dust))
        c.restore()
        c.drawRRect(neck, paint('#9A968C', 0.3 * dust))
        for i in range(int(80 * dust)):
            px, py = hrange(-74, 200, i, 3), hrange(-40, 40, i, 4)
            if px > 60 and abs(py) > 9:
                continue
            c.drawCircle(px, py, hrange(0.8, 2.2, i, 5), paint('#C9C4B8', 0.6 * dust))
    if a < 1:
        c.restore()
    c.restore()


def toy_guitar(c, x, y, angle=-25.0, scale=0.55):
    guitar(c, x, y, angle, scale, body='#E2574C', shine=1.0)


# --- phone ----------------------------------------------------------------------------

def phone(c, x, y, angle=0.0, scale=1.0, screen='#1C2633', glow=0.8, content=None, face_down=False, a=1.0):
    """Portrait phone centred at (x, y). content(c, w, h) draws the screen in screen-local coords."""
    w, h = 40, 72
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.scale(scale, scale)
    body = rrect(-w / 2, -h / 2, w, h, 8)
    if face_down:
        c.drawRRect(body, paint('#2A2C33', a))
        c.drawRRect(body, paint('outline', a, stroke=4))
        c.drawCircle(-w / 2 + 10, -h / 2 + 10, 4, paint('#111', a))
        c.restore()
        return
    if glow > 0:
        light_pool(c, 0, 0, 90, 90, '#9CC8FF', 0.22 * glow * a)
    c.drawRRect(body, paint('#15161A', a))
    scr = rrect(-w / 2 + 3, -h / 2 + 4, w - 6, h - 8, 5)
    c.drawRRect(scr, paint(screen, a))
    if content:
        c.save()
        c.clipRRect(scr, doAntiAlias=True)
        c.translate(-w / 2 + 3, -h / 2 + 4)
        content(c, w - 6, h - 8)
        c.restore()
    c.drawRRect(body, paint('outline', a, stroke=4))
    c.restore()


# --- bedroom ------------------------------------------------------------------------------

def window(c, x, y, w=230, h=260, sky='#101A30', moon=True, dawn=0.0, light=1.0, t=0.0):
    """Window on the back wall with a moon; dawn 0..1 warms the sky."""
    frame = rrect(x, y, w, h, 6)
    sky_c = mixc(sky, '#F08A4B', dawn)
    shader = skia.GradientShader.MakeLinear(points=[(x, y), (x, y + h)],
                                           colors=[col(mixc(sky_c, '#000000', 0.25)), col(sky_c)])
    c.drawRRect(frame, paint(sky_c, shader=shader))
    c.save()
    c.clipRRect(frame, doAntiAlias=True)
    for i in range(14):
        sx, sy = x + hrange(10, w - 10, i, 11), y + hrange(10, h * 0.6, i, 12)
        tw = 0.5 + 0.5 * math.sin(t * 2 + i)
        c.drawCircle(sx, sy, 1.6, paint('#FFFFFF', (0.35 + 0.4 * tw) * (1 - dawn)))
    if moon:
        mx, my = x + w * 0.68, y + h * 0.3
        c.drawCircle(mx, my, 60, paint('moon', 0.25 * (1 - dawn), blur=26, blend='add'))
        c.drawCircle(mx, my, 26, paint('#E9EEFF', 1 - 0.7 * dawn))
        c.drawCircle(mx + 9, my - 6, 22, paint(sky_c, 1 - 0.7 * dawn))
    if dawn > 0:
        light_pool(c, x + w * 0.4, y + h, w * 0.9, h * 0.6, '#FF9E5E', 0.55 * dawn)
    c.restore()
    c.drawRRect(frame, paint('#2E2F37', stroke=14))
    c.drawLine(x + w / 2, y, x + w / 2, y + h, paint('#2E2F37', stroke=10))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, paint('#2E2F37', stroke=10))
    c.drawRRect(frame, paint('outline', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(x - 16, y + h, x + w + 16, y + h + 14), paint('#33343C'))
    c.drawRect(skia.Rect.MakeLTRB(x - 16, y + h, x + w + 16, y + h + 14), paint('outline', stroke=4))


def moonbeam(c, x, y, w, h, floor_y, slant=180, a=0.12, color='moon'):
    path = poly([(x, y), (x + w, y), (x + w + slant, floor_y), (x + slant, floor_y)], True)
    p = paint(color, a, blur=30, blend='add')
    c.drawPath(path, p)


def bed(c, x, floor_y, w=430, blanket='#5B4E7A', pillow='#D8D2C6', a=1.0, messy=0.0, height=96):
    """Side-view bed; returns the mattress top y."""
    top = floor_y - height
    leg_top = top + 86
    c.drawRect(skia.Rect.MakeLTRB(x + 10, leg_top, x + 22, floor_y), paint('#4A3A2E', a))
    c.drawRect(skia.Rect.MakeLTRB(x + w - 22, leg_top, x + w - 10, floor_y), paint('#4A3A2E', a))
    head = rrect(x + w - 26, top - 120, 26, 200, 8)
    c.drawRRect(head, paint('#5A4535', a))
    c.drawRRect(head, paint('outline', a, stroke=4))
    frame = rrect(x, top + 58, w, 30, 6)
    c.drawRRect(frame, paint('#5A4535', a))
    c.drawRRect(frame, paint('outline', a, stroke=4))
    matt = rrect(x + 6, top, w - 36, 64, 16)
    c.drawRRect(matt, paint('#E6E0D4', a))
    c.drawRRect(matt, paint('outline', a, stroke=4))
    pil = rrect(x + w - 150, top - 26, 110, 40, 18)
    c.drawRRect(pil, paint(pillow, a))
    c.drawRRect(pil, paint('outline', a, stroke=4))
    bl = skia.Path()
    bl.moveTo(x + 2, top + 8)
    bl.cubicTo(x + 120, top - 14 - 10 * messy, x + 220, top + 4, x + w - 170, top - 6)
    bl.lineTo(x + w - 170, top + 70)
    bl.lineTo(x + 2, top + 74)
    bl.close()
    c.drawPath(bl, paint(blanket, a))
    c.drawPath(bl, paint('outline', a, stroke=4))
    return top


def nightstand(c, x, floor_y, lamp_on=1.0, w=110):
    top = floor_y - 110
    box = rrect(x, top, w, 110, 6)
    c.drawRRect(box, paint('#3F3A3A'))
    c.drawRRect(box, paint('outline', stroke=4))
    c.drawLine(x + 8, top + 50, x + w - 8, top + 50, paint('outline', stroke=3))
    c.drawCircle(x + w / 2, top + 30, 4, paint('#B9A27A'))
    lx = x + w / 2
    c.drawRect(skia.Rect.MakeLTRB(lx - 4, top - 60, lx + 4, top), paint('#2B2B30'))
    c.drawOval(oval(lx, top - 2, 24, 7), paint('#2B2B30'))
    shade = poly([(lx - 26, top - 60), (lx + 26, top - 60), (lx + 18, top - 104), (lx - 18, top - 104)], True)
    if lamp_on > 0:
        light_pool(c, lx, top - 70, 260, 200, 'warm', 0.32 * lamp_on)
        cone(c, (lx, top - 60), 26, floor_y, 140, 'warm', 0.12 * lamp_on, soft=30)
    c.drawPath(shade, paint(mixc('#B59B6C', '#FFD58A', lamp_on)))
    c.drawPath(shade, paint('outline', stroke=4))
    return top


def shelf(c, x, y, w=260, books=True, plant=True, tiny_shadow=None):
    c.drawRect(skia.Rect.MakeLTRB(x, y, x + w, y + 12), paint('#4C3E32'))
    c.drawRect(skia.Rect.MakeLTRB(x, y, x + w, y + 12), paint('outline', stroke=4))
    if books:
        bx = x + 14
        palette = ['#7A5C8F', '#4F7A6B', '#B0624A', '#3F5F8A', '#C9A54E', '#6B6B78']
        for i in range(7):
            bw, bh = hrange(16, 26, i, 21), hrange(52, 74, i, 22)
            lean = 10 if i == 6 else 0
            c.save()
            c.translate(bx, y)
            c.rotate(lean)
            r = skia.Rect.MakeLTRB(0, -bh, bw, 0)
            c.drawRect(r, paint(palette[i % len(palette)]))
            c.drawRect(r, paint('outline', stroke=3))
            c.restore()
            bx += bw + 3
    if plant:
        px = x + w - 50
        pot = poly([(px - 20, y - 36), (px + 20, y - 36), (px + 14, y), (px - 14, y)], True)
        for k, ang in enumerate((-35, -10, 15, 38)):
            a = math.radians(ang)
            leaf = skia.Path()
            leaf.moveTo(px, y - 36)
            leaf.quadTo(px + math.sin(a) * 40 - 10, y - 36 - math.cos(a) * 30, px + math.sin(a) * 34, y - 36 - math.cos(a) * 62)
            leaf.quadTo(px + math.sin(a) * 40 + 12, y - 36 - math.cos(a) * 26, px, y - 36)
            c.drawPath(leaf, paint('#5E8C5A'))
            c.drawPath(leaf, paint('outline', stroke=3))
        c.drawPath(pot, paint('#B8674A'))
        c.drawPath(pot, paint('outline', stroke=3.5))


def poster(c, x, y, w=150, h=200, kind='singer', glow=0.0, t=0.0):
    r = rrect(x, y, w, h, 4)
    c.drawRRect(r, paint('#1D2433' if kind == 'singer' else '#2A1E14'))
    c.save()
    c.clipRRect(r)
    cx = x + w / 2
    light_pool(c, cx, y + h * 0.45, w * 0.6, h * 0.5, 'warm', 0.35)
    if kind == 'singer':
        # tiny performer silhouette with a mic stand
        c.drawCircle(cx, y + h * 0.36, 16, paint('#0B0B0E'))
        c.drawRRect(rrect(cx - 15, y + h * 0.36 + 14, 30, 44, 10), paint('#0B0B0E'))
        c.drawLine(cx + 26, y + h * 0.38, cx + 26, y + h * 0.78, paint('#0B0B0E', stroke=3))
        c.drawCircle(cx + 22, y + h * 0.37, 5, paint('#0B0B0E'))
        text(c, 'LIVE', cx, y + h - 22, 30, 'Fredoka', 'warm')
    else:
        # his own gig flyer: round head with a beanie
        c.drawCircle(cx, y + h * 0.36, 20, paint('skin'))
        c.drawCircle(cx, y + h * 0.36, 20, paint('outline', stroke=3))
        dome = skia.Path()
        dome.addArc(oval(cx, y + h * 0.36, 21, 21), 180, 180)
        c.drawPath(dome, paint('beanie'))
        c.drawRect(skia.Rect.MakeLTRB(cx - 22, y + h * 0.36 - 9, cx + 22, y + h * 0.36 - 3), paint('beanie'))
        text(c, 'TONIGHT', cx, y + h - 46, 24, 'Fredoka', 'warm')
        text(c, 'LIVE', cx, y + h - 18, 26, 'Fredoka', 'white')
    c.restore()
    c.drawRRect(r, paint('outline', stroke=4))
    for px in (x + 8, x + w - 8):
        c.drawCircle(px, y + 8, 4, paint('#C9C4B8'))


# --- school noticeboard ----------------------------------------------------------------------

def noticeboard(c, x, y, w=520, h=330, names=3, extra_name=0.0, pen=True, t=0.0):
    board = rrect(x, y, w, h, 8)
    c.drawRRect(board, paint('#8A6440'))
    for i in range(60):
        c.drawCircle(x + hrange(8, w - 8, i, 31), y + hrange(8, h - 8, i, 32), 1.5, paint('#6D4C2E', 0.7))
    c.drawRRect(board, paint('#4A3420', stroke=14))
    c.drawRRect(board, paint('outline', stroke=4))
    # side flyers
    for i, (fx, fy, fw, fh, fc) in enumerate([(x + 30, y + 40, 110, 140, '#D9D3C4'), (x + w - 140, y + 60, 100, 120, '#B7D3E0')]):
        c.save()
        c.translate(fx + fw / 2, fy + fh / 2)
        c.rotate(-4 + i * 7)
        rr = skia.Rect.MakeLTRB(-fw / 2, -fh / 2, fw / 2, fh / 2)
        c.drawRect(rr, paint(fc))
        c.drawRect(rr, paint('outline', stroke=3))
        for k in range(4):
            c.drawLine(-fw / 2 + 12, -fh / 2 + 22 + k * 22, fw / 2 - 12 - (k % 2) * 20, -fh / 2 + 22 + k * 22,
                       paint('#6B6B6B', stroke=3))
        c.restore()
        c.drawCircle(fx + fw / 2, fy + 6, 5, paint('#D94B4B'))
    # sign-up sheet
    sx, sy, sw, sh = x + w / 2 - 95, y + 30, 190, 270
    sheet = skia.Rect.MakeXYWH(sx, sy, sw, sh)
    c.drawRect(sheet, paint('#F4F0E6'))
    c.drawRect(sheet, paint('outline', stroke=3.5))
    c.drawCircle(sx + sw / 2, sy + 6, 6, paint('#3E8ED0'))
    text(c, 'TALENT SHOW', sx + sw / 2, sy + 42, 28, 'Fredoka', '#C2413A')
    text(c, 'SIGN UP', sx + sw / 2, sy + 70, 22, 'Fredoka', '#333333')
    for k in range(7):
        ly = sy + 104 + k * 24
        c.drawLine(sx + 18, ly, sx + sw - 18, ly, paint('#B8B2A4', stroke=2))
        if k < names:
            wobble = smooth_path([(sx + 22 + i * 14, ly - 6 + (hrand(k, i) - 0.5) * 8) for i in range(int(6 + hrand(k) * 4))])
            c.drawPath(wobble, paint('#2E4FA0', stroke=2.5))
        elif k == names and extra_name > 0:
            n = max(2, int(10 * extra_name))
            wobble = smooth_path([(sx + 22 + i * 13, ly - 6 + math.sin(i * 1.7) * 5) for i in range(n)])
            c.drawPath(wobble, paint('#C24A1E', stroke=3))
    return (sx, sy, sw, sh)


# --- office ---------------------------------------------------------------------------------

def office_desk(c, x, floor_y, w=420, screen_glow=1.0, t=0.0):
    top = floor_y - 150
    c.drawRect(skia.Rect.MakeLTRB(x, top, x + w, top + 16), paint('#6B6F78'))
    c.drawRect(skia.Rect.MakeLTRB(x, top, x + w, top + 16), paint('outline', stroke=4))
    for lx in (x + 16, x + w - 30):
        c.drawRect(skia.Rect.MakeLTRB(lx, top + 16, lx + 14, floor_y), paint('#54575F'))
    mx = x + w * 0.62
    c.drawRect(skia.Rect.MakeLTRB(mx - 8, top - 50, mx + 8, top), paint('#2C2E34'))
    mon = rrect(mx - 95, top - 170, 190, 125, 8)
    if screen_glow:
        light_pool(c, mx - 60, top - 100, 260, 160, '#9CC8FF', 0.16 * screen_glow)
    c.drawRRect(mon, paint('#1A1C22'))
    c.drawRRect(rrect(mx - 86, top - 162, 172, 108, 4), paint('#2C4A63'))
    for k in range(6):
        c.drawLine(mx - 74, top - 146 + k * 16, mx - 74 + hrange(60, 140, k, 41), top - 146 + k * 16,
                   paint('#8FB7D6', 0.7, stroke=4))
    c.drawRRect(mon, paint('outline', stroke=4))
    c.drawRRect(rrect(mx - 70, top - 12, 120, 12, 4), paint('#3A3D45'))
    mug_x = x + 40
    c.drawRRect(rrect(mug_x, top - 36, 28, 36, 5), paint('#D9D3C4'))
    c.drawRRect(rrect(mug_x, top - 36, 28, 36, 5), paint('outline', stroke=3))
    return top


def cubicle(c, x0, x1, floor_y):
    c.drawRect(skia.Rect.MakeLTRB(x0, floor_y - 330, x1, floor_y), paint('#1B1D22'))
    c.drawRect(skia.Rect.MakeLTRB(x0, floor_y - 330, x1, floor_y - 318), paint('#2A2D34'))


# --- mirror ---------------------------------------------------------------------------------

def mirror_frame(c, cx, cy, rx, ry, glow=0.0, rim='#5D5F69'):
    if glow > 0:
        c.drawOval(oval(cx, cy, rx + 4, ry + 4), paint('red', glow, stroke=14, blur=14, blend='add'))
    c.drawOval(oval(cx, cy, rx, ry), paint(rim, stroke=16))
    c.drawOval(oval(cx, cy, rx + 8, ry + 8), paint('outline', stroke=4))
    c.drawOval(oval(cx, cy, rx - 8, ry - 8), paint('outline', stroke=3))


def cracks(c, cx, cy, amount, seed=7, reach=260, color='#E8ECF2'):
    """Radial glass cracks growing from (cx, cy); amount 0..1."""
    if amount <= 0:
        return
    for k in range(9):
        ang = (k / 9) * math.tau + hrand(k, seed) * 0.5
        length = reach * (0.55 + 0.45 * hrand(k, seed, 1)) * min(1.0, amount * 1.4)
        pts = [(cx, cy)]
        steps = 6
        for s in range(1, steps + 1):
            r = length * s / steps
            jitter = (hrand(k, s, seed) - 0.5) * 0.35
            pts.append((cx + math.cos(ang + jitter) * r, cy + math.sin(ang + jitter) * r))
        c.drawPath(poly(pts), paint(color, 0.9, stroke=2.2))
        c.drawPath(poly(pts), paint('#FFFFFF', 0.25, stroke=6, blur=4))
        if amount > 0.5:
            mid = pts[3]
            b_ang = ang + (0.7 if k % 2 else -0.7)
            bl = length * 0.3 * (amount - 0.5) * 2
            c.drawLine(mid[0], mid[1], mid[0] + math.cos(b_ang) * bl, mid[1] + math.sin(b_ang) * bl,
                       paint(color, 0.8, stroke=1.6))
    rings = [0.25, 0.5]
    for i, rr in enumerate(rings):
        if amount > 0.4 + i * 0.25:
            path = skia.Path()
            pts = [(cx + math.cos(a) * reach * rr * (0.9 + 0.2 * hrand(i, j)), cy + math.sin(a) * reach * rr * (0.9 + 0.2 * hrand(j, i)))
                   for j, a in enumerate([x * math.tau / 11 for x in range(11)])]
            c.drawPath(poly(pts, True), paint(color, 0.55, stroke=1.4))


# --- stage, street, café ------------------------------------------------------------------

def stage_floor(c, x0, x1, top, front=60, color='#3B2A20', a=1.0):
    c.drawRect(skia.Rect.MakeLTRB(x0, top, x1, top + front), paint(color, a))
    for k in range(int((x1 - x0) / 90) + 1):
        c.drawLine(x0 + k * 90, top, x0 + k * 90 - 20, top + front, paint('#2A1D16', a, stroke=3))
    c.drawRect(skia.Rect.MakeLTRB(x0, top + front, x1, top + front + 26), paint('#1E1612', a))
    c.drawLine(x0, top, x1, top, paint('#6B4E3A', a, stroke=4))


def curtains(c, w, h, open_amt=1.0, color='#5A1626', t=0.0):
    """Theatre curtains; open_amt 0 closed .. 1 fully open."""
    half = w / 2
    span = half * (1 - 0.82 * open_amt)
    for side in (-1, 1):
        x_inner = half + side * (half - span) if side == 1 else half - (half - span)
        path = skia.Path()
        if side == -1:
            path.moveTo(0, 0)
            path.lineTo(span, 0)
            path.cubicTo(span - 20, h * 0.4, span + 10, h * 0.7, span - 30 * open_amt, h)
            path.lineTo(0, h)
        else:
            path.moveTo(w, 0)
            path.lineTo(w - span, 0)
            path.cubicTo(w - span + 20, h * 0.4, w - span - 10, h * 0.7, w - span + 30 * open_amt, h)
            path.lineTo(w, h)
        path.close()
        c.drawPath(path, paint(color))
        folds = 6
        for k in range(1, folds):
            fx = (span * k / folds) if side == -1 else (w - span * k / folds)
            c.drawLine(fx, 0, fx + side * 10 * math.sin(t + k), h, paint('#000000', 0.25, stroke=10, blur=4))
        c.drawPath(path, paint('outline', stroke=4))
    val = skia.Path()
    val.moveTo(0, 0)
    for k in range(13):
        val.quadTo(k * w / 12 + w / 24, 70, (k + 1) * w / 12, 40)
    val.lineTo(w, 0)
    val.close()
    c.drawPath(val, paint(color))
    c.drawPath(val, paint('#000000', 0.2))
    c.drawPath(val, paint('outline', stroke=4))


def mic_stand(c, x, floor_y, height=300, mic_angle=-20.0):
    top = floor_y - height
    c.drawOval(oval(x, floor_y - 4, 34, 8), paint('#26272C'))
    c.drawLine(x, floor_y - 4, x, top, paint('#3A3B42', stroke=6))
    c.drawLine(x, top, x - 34, top - 12, paint('#3A3B42', stroke=5))
    c.save()
    c.translate(x - 38, top - 14)
    c.rotate(mic_angle)
    c.drawRRect(rrect(-8, -26, 16, 34, 7), paint('#2B2C31'))
    c.drawCircle(0, -28, 11, paint('#8E9099'))
    c.drawCircle(0, -28, 11, paint('outline', stroke=3))
    c.restore()
    return (x - 38, top - 42)


def street_lamp(c, x, floor_y, height=520, on=1.0):
    top = floor_y - height
    c.drawRect(skia.Rect.MakeLTRB(x - 7, top, x + 7, floor_y), paint('#2A2B31'))
    c.drawLine(x, top, x + 70, top - 10, paint('#2A2B31', stroke=9))
    lamp = poly([(x + 50, top - 12), (x + 96, top - 16), (x + 88, top + 4), (x + 56, top + 6)], True)
    c.drawPath(lamp, paint('#3A3B42'))
    if on:
        cone(c, (x + 74, top + 6), 18, floor_y, 230, 'warm', 0.16 * on, soft=28)
        light_pool(c, x + 74, floor_y, 300, 50, 'warm', 0.3 * on)
        c.drawCircle(x + 73, top + 4, 26, paint('warm', 0.5 * on, blur=14, blend='add'))
    c.drawPath(lamp, paint('outline', stroke=3))


def buildings(c, x0, x1, base_y, seed=3, t=0.0):
    x = x0
    i = 0
    while x < x1:
        bw = hrange(140, 260, i, seed)
        bh = hrange(260, 520, i, seed, 1)
        c.drawRect(skia.Rect.MakeLTRB(x, base_y - bh, x + bw - 6, base_y), paint('#121319'))
        for wy in range(int(base_y - bh + 30), int(base_y - 40), 46):
            for wx in range(int(x + 18), int(x + bw - 30), 38):
                if hrand(wx, wy, seed) > 0.72:
                    c.drawRect(skia.Rect.MakeXYWH(wx, wy, 18, 24), paint('#E9B85A', 0.45))
        x += bw
        i += 1


def guitar_case(c, x, floor_y, coins=0, coin_t=None, t=0.0):
    shell = rrect(x - 130, floor_y - 34, 260, 34, 14)
    c.drawRRect(shell, paint('#1E1F25'))
    inner = rrect(x - 118, floor_y - 30, 236, 22, 10)
    c.drawRRect(inner, paint('#2C5E63'))
    c.drawRRect(shell, paint('outline', stroke=4))
    for i in range(coins):
        cx = x - 90 + hrange(0, 180, i, 61)
        c.drawOval(oval(cx, floor_y - 18 - (i % 2) * 3, 9, 4), paint('#E8C35A'))
        c.drawOval(oval(cx, floor_y - 18 - (i % 2) * 3, 9, 4), paint('#8C6A1E', stroke=1.5))
    if coin_t is not None and 0 <= coin_t < 0.6:
        # falling coin with a bounce
        u = coin_t / 0.6
        cy = floor_y - 260 + 240 * min(1.0, (u / 0.7) ** 2) - (40 * math.sin((u - 0.7) / 0.3 * math.pi) if u > 0.7 else 0)
        c.drawOval(oval(x + 20, cy, 9, 9 * abs(math.cos(t * 20))), paint('#F2CF63'))
        c.drawCircle(x + 20, cy, 16, paint('warm', 0.4, blur=8, blend='add'))


def string_lights(c, x0, x1, y, sag=60, n=16, t=0.0, a=1.0):
    path = skia.Path()
    path.moveTo(x0, y)
    path.quadTo((x0 + x1) / 2, y + sag * 2, x1, y)
    c.drawPath(path, paint('#2C2C30', a, stroke=3))
    for k in range(n):
        u = (k + 0.5) / n
        bx = x0 + (x1 - x0) * u
        by = y + sag * 4 * u * (1 - u) * 1.0
        flick = 0.75 + 0.25 * math.sin(t * 3 + k * 1.7)
        c.drawCircle(bx, by + 8, 14, paint('warm', 0.45 * flick * a, blur=8, blend='add'))
        c.drawCircle(bx, by + 8, 5, paint('#FFE2A3', a))


def cafe_table(c, x, floor_y, a=1.0):
    c.drawOval(oval(x, floor_y - 120, 60, 12), paint('#5A4535', a))
    c.drawOval(oval(x, floor_y - 120, 60, 12), paint('outline', a, stroke=3.5))
    c.drawRect(skia.Rect.MakeLTRB(x - 5, floor_y - 118, x + 5, floor_y), paint('#3A2E26', a))
    c.drawOval(oval(x, floor_y - 3, 26, 6), paint('#3A2E26', a))


def chair(c, x, floor_y, facing=1, color='#3B3E46', a=1.0):
    c.save()
    c.translate(x, floor_y)
    c.scale(facing, 1)
    c.drawRect(skia.Rect.MakeLTRB(-30, -84, 30, -72), paint(color, a))
    c.drawRect(skia.Rect.MakeLTRB(-30, -180, -20, -72), paint(color, a))
    for lx in (-28, 22):
        c.drawRect(skia.Rect.MakeLTRB(lx, -72, lx + 6, 0), paint(color, a))
    c.restore()


def riser(c, x0, x1, floor_y, h=40):
    c.drawRect(skia.Rect.MakeLTRB(x0, floor_y - h, x1, floor_y), paint('#3A2C24'))
    c.drawLine(x0, floor_y - h, x1, floor_y - h, paint('#6B4E3A', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(x0, floor_y - h, x1, floor_y), paint('outline', stroke=3))
    return floor_y - h


def cobweb(c, x, y, size=90, a=0.6, corner='tl'):
    sx = 1 if corner in ('tl', 'bl') else -1
    sy = 1 if corner in ('tl', 'tr') else -1
    for k in range(6):
        ang = math.radians(k * 18)
        c.drawLine(x, y, x + sx * math.cos(ang) * size, y + sy * math.sin(ang) * size, paint('#CFCFD6', a * 0.6, stroke=1.2))
    for r in (0.3, 0.55, 0.8):
        pts = [(x + sx * math.cos(math.radians(k * 18)) * size * r, y + sy * math.sin(math.radians(k * 18)) * size * r)
               for k in range(6)]
        path = skia.Path()
        path.moveTo(*pts[0])
        for p0, p1 in zip(pts, pts[1:]):
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            path.quadTo(mx - sx * 4, my - sy * 4, *p1)
        c.drawPath(path, paint('#CFCFD6', a * 0.5, stroke=1.1))
