"""Outdoor sets for 'He's Waiting.': the street door at dawn, the river path in every season, the trailhead,
the mountain at night and the summit at sunrise. Far layers take a parallax factor so tracking shots have depth."""
from __future__ import annotations

import math

import skia

from engine.core import W, clamp, hrand, hrange, noise1, smooth
from engine.draw import col, mixc, oval, paint, poly, rrect, text

PATH_Y = 900          # the running path's surface


def grad(c, rect, stops, vertical=True):
    """Fill rect with a multi-stop gradient: stops [(pos, colour)]."""
    x0, y0, x1, y1 = rect
    pts = [(x0, y0), (x0, y1)] if vertical else [(x0, y0), (x1, y0)]
    sh = skia.GradientShader.MakeLinear(points=pts, colors=[col(cc) for _, cc in stops],
                                        positions=[p for p, _ in stops])
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), paint('#000000', shader=sh))


def hexmix(a, b, u):
    return '#%02X%02X%02X' % mixc(a, b, clamp(u))


SKIES = {
    'night': [(0.0, '#05070F'), (0.55, '#0E1630'), (1.0, '#1B2647')],
    'predawn': [(0.0, '#070B1C'), (0.5, '#1A2350'), (0.8, '#4A3A72'), (1.0, '#B35F6E')],
    'dawn': [(0.0, '#1E2A5A'), (0.45, '#5B5A93'), (0.75, '#E58A7A'), (1.0, '#FFC27A')],
    'golden': [(0.0, '#3B66A8'), (0.5, '#8FB7E0'), (0.85, '#FFD79A'), (1.0, '#FFB86B')],
    'day': [(0.0, '#4C8BD0'), (1.0, '#BFE0F7')],
    'rain': [(0.0, '#2A3140'), (1.0, '#5A6476')],
    'snow': [(0.0, '#5C6E8E'), (1.0, '#C9D3E2')],
    'autumn': [(0.0, '#4A6FA5'), (0.6, '#F2B880'), (1.0, '#F59E5C')],
}


def sky(c, mood, x0=-2000, x1=4000, y0=-1200, y1=1100):
    grad(c, (x0, y0, x1, y1), SKIES[mood])


def stars(c, T, x0, y0, x1, y1, n=120, seed=3, a=1.0):
    if a <= 0:
        return
    for i in range(n):
        x, y = hrange(x0, x1, i, seed, 1), hrange(y0, y1, i, seed, 2)
        tw = 0.55 + 0.45 * math.sin(T * (1.0 + hrand(i, seed, 3) * 2.5) + i)
        r = hrange(0.9, 2.4, i, seed, 4)
        c.drawCircle(x, y, r, paint('#FFFFFF', a * (0.3 + 0.6 * tw)))


def skyline(c, x0, x1, base, color, seed=0, hmin=80, hmax=260, windows=None, wcol='#F2C26B'):
    x = x0
    k = 0
    while x < x1:
        bw = hrange(60, 150, k, seed, 1)
        bh = hrange(hmin, hmax, k, seed, 2)
        c.drawRect(skia.Rect.MakeLTRB(x, base - bh, x + bw, base + 400), paint(color))
        if hrand(k, seed, 3) > 0.7:
            c.drawRect(skia.Rect.MakeLTRB(x + bw * 0.4, base - bh - 30, x + bw * 0.46, base - bh), paint(color))
        if windows:
            for r in range(int(bh / 26)):
                for q in range(int(bw / 22)):
                    if hrand(k, r, q, seed) > windows:
                        c.drawRect(skia.Rect.MakeXYWH(x + 8 + q * 22, base - bh + 10 + r * 26, 9, 11), paint(wcol, 0.8))
        x += bw + hrange(4, 30, k, seed, 4)
        k += 1


def layer(c, cam_x, f, fn, cam_y=None, fy=0.0):
    """Draw fn() with parallax: f=0 sticks to the screen (infinitely far), f=1 moves with the ground."""
    c.save()
    c.translate(cam_x * (1 - f), (cam_y or 0.0) * (1 - fy) if cam_y is not None else 0.0)
    fn()
    c.restore()


# --- the street door at dawn ---------------------------------------------------------------------------------------

DOOR_X = 720


def street_dawn(c, T, cam_x=960, warm=0.0, door_open=0.0):
    sky(c, 'dawn')
    c.drawCircle(1500 + cam_x * 0.9 - 864, 820, 300, paint('#FFD3A0', 0.3 + 0.2 * warm, blur=90, blend='add'))
    layer(c, cam_x, 0.25, lambda: skyline(c, -800, 3200, 880, '#3A3355', seed=11, hmin=140, hmax=420))
    layer(c, cam_x, 0.5, lambda: skyline(c, -800, 3400, 900, '#2A2440', seed=12, hmin=90, hmax=260, windows=0.86))
    # the building: brick wall to the left, its door, the step
    c.drawRect(skia.Rect.MakeLTRB(-1200, 140, DOOR_X + 330, PATH_Y), paint('#8C5A4A'))
    for r in range(40):
        y = 140 + r * 28
        off = 0 if r % 2 else 40
        for q in range(-30, 30):
            x = -1200 + off + q * 80
            if x > DOOR_X + 330:
                break
            c.drawRect(skia.Rect.MakeXYWH(x, y, 78, 26), paint('#7A4C3E', stroke=2))
    c.drawRect(skia.Rect.MakeLTRB(-1200, 140, DOOR_X + 330, PATH_Y), paint('#000000', 0.12))
    c.drawLine(DOOR_X + 330, 140, DOOR_X + 330, PATH_Y, paint('outline', stroke=5))
    # door frame and the warm hall behind
    c.drawRect(skia.Rect.MakeLTRB(DOOR_X - 20, 470, DOOR_X + 220, PATH_Y - 20), paint('#3A2A24'))
    c.drawRect(skia.Rect.MakeLTRB(DOOR_X, 490, DOOR_X + 200, PATH_Y - 20), paint('#FFD9A0'))
    leaf = 200 * (1 - 0.86 * door_open)
    c.drawRect(skia.Rect.MakeLTRB(DOOR_X, 490, DOOR_X + leaf, PATH_Y - 20), paint('#2F4A5E'))
    if leaf > 40:
        c.drawRect(skia.Rect.MakeLTRB(DOOR_X + 20, 520, DOOR_X + leaf - 20, 640), paint('#BFD6E8', 0.5))
        c.drawCircle(DOOR_X + leaf - 22, 700, 7, paint('#D9C27A'))
    c.drawRect(skia.Rect.MakeLTRB(DOOR_X, 490, DOOR_X + leaf, PATH_Y - 20), paint('outline', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(DOOR_X - 20, 470, DOOR_X + 220, PATH_Y - 20), paint('outline', stroke=5))
    c.drawRRect(rrect(DOOR_X - 60, PATH_Y - 22, 320, 24, 4), paint('#9A9AA2'))
    c.drawRRect(rrect(DOOR_X - 60, PATH_Y - 22, 320, 24, 4), paint('outline', stroke=4))
    # wall lamp
    c.drawRRect(rrect(DOOR_X + 240, 470, 30, 44, 8), paint('#2B2B30'))
    c.drawCircle(DOOR_X + 255, 500, 12, paint('#FFE2A8'))
    c.drawCircle(DOOR_X + 255, 500, 60, paint('#FFD08A', 0.35 * (1 - 0.5 * warm), blur=24, blend='add'))
    # pavement and road
    c.drawRect(skia.Rect.MakeLTRB(-1200, PATH_Y, 3600, 1400), paint('#6E6A72'))
    c.drawLine(-1200, PATH_Y, 3600, PATH_Y, paint('outline', stroke=4))
    for k in range(-12, 40):
        c.drawLine(k * 140, PATH_Y + 4, k * 140 - 40, PATH_Y + 120, paint('#000000', 0.15, stroke=3))
    c.drawRect(skia.Rect.MakeLTRB(-1200, PATH_Y + 120, 3600, 1400), paint('#3E3C44'))
    # street lamp, still on
    lx = DOOR_X + 820
    c.drawLine(lx, PATH_Y, lx, 380, paint('outline', stroke=16))
    c.drawLine(lx, PATH_Y, lx, 380, paint('#3B3E46', stroke=9))
    c.drawRRect(rrect(lx - 30, 350, 60, 34, 10), paint('#3B3E46'))
    c.drawCircle(lx, 388, 70, paint('#FFD08A', 0.3 * (1 - warm), blur=30, blend='add'))


# --- the river path --------------------------------------------------------------------------------------------------

def river_path(c, T, cam_x, mood='dawn', sun=0.0):
    sky(c, mood)
    sun_col = {'dawn': '#FFD3A0', 'golden': '#FFE7B0', 'autumn': '#FFD39A'}.get(mood)
    if sun_col:
        c.drawCircle(cam_x + 380, 640, 160, paint(sun_col, 0.55, blur=80, blend='add'))
        c.drawCircle(cam_x + 380, 640, 54, paint('#FFF6DD', 0.9))
    far = {'dawn': '#4C4A78', 'golden': '#7A90B8', 'rain': '#3A4252', 'snow': '#8D9AB2', 'autumn': '#8C7A9A'}[mood]
    mid = {'dawn': '#33315A', 'golden': '#55688E', 'rain': '#2C3340', 'snow': '#6E7C96', 'autumn': '#6A5A7A'}[mood]
    layer(c, cam_x, 0.15, lambda: skyline(c, cam_x * 0.85 - 1400, cam_x * 0.85 + 2600, 700, far, seed=21, hmin=60, hmax=220))
    layer(c, cam_x, 0.3, lambda: _bridge(c, cam_x * 0.7 + 200, 700, mid))
    # the river
    water = {'dawn': '#3E4C7A', 'golden': '#5A86B8', 'rain': '#323B4A', 'snow': '#6F82A0', 'autumn': '#5D6E98'}[mood]
    grad(c, (cam_x - 2000, 700, cam_x + 2000, 820), [(0.0, water), (1.0, hexmix(water, '#000000', 0.25))])
    for k in range(18):
        rx = cam_x - 1100 + ((hrange(0, 2200, k, 31) - cam_x * 0.4) % 2200)
        ry = 712 + hrange(0, 100, k, 32)
        c.drawLine(rx, ry, rx + hrange(30, 90, k, 33), ry, paint('#FFFFFF', 0.18, stroke=3))
    # far bank grass, trees with parallax 0.7
    layer(c, cam_x, 0.7, lambda: _trees(c, cam_x * 0.3 - 1400, cam_x * 0.3 + 2400, 820, mood))
    # railing and lamps move with the ground
    grass = {'dawn': '#3E5A48', 'golden': '#5E8A50', 'rain': '#33473C', 'snow': '#E8EDF4', 'autumn': '#8A7A44'}[mood]
    c.drawRect(skia.Rect.MakeLTRB(cam_x - 2000, 812, cam_x + 2000, PATH_Y), paint(grass))
    x0 = math.floor((cam_x - 1400) / 150) * 150
    for k in range(24):
        px = x0 + k * 150
        c.drawLine(px, PATH_Y - 6, px, 812, paint('outline', stroke=9))
        c.drawLine(px, PATH_Y - 6, px, 812, paint('#5C5F68', stroke=5))
    c.drawLine(cam_x - 2000, 812, cam_x + 2000, 812, paint('outline', stroke=9))
    c.drawLine(cam_x - 2000, 812, cam_x + 2000, 812, paint('#7A7E88', stroke=5))
    x0 = math.floor((cam_x - 1600) / 640) * 640
    for k in range(7):
        lx = x0 + k * 640 + 200
        c.drawLine(lx, PATH_Y, lx, 470, paint('outline', stroke=14))
        c.drawLine(lx, PATH_Y, lx, 470, paint('#2E3038', stroke=8))
        c.drawRRect(rrect(lx - 24, 446, 48, 30, 10), paint('#2E3038'))
        if mood in ('dawn', 'rain', 'snow'):
            c.drawCircle(lx, 478, 50, paint('#FFD08A', 0.28, blur=22, blend='add'))
    # the path
    path_col = {'snow': '#DCE3EE'}.get(mood, '#8E8A86')
    c.drawRect(skia.Rect.MakeLTRB(cam_x - 2000, PATH_Y, cam_x + 2000, PATH_Y + 120), paint(path_col))
    c.drawLine(cam_x - 2000, PATH_Y, cam_x + 2000, PATH_Y, paint('outline', stroke=4))
    x0 = math.floor((cam_x - 1400) / 90) * 90
    for k in range(34):
        px = x0 + k * 90
        c.drawLine(px, PATH_Y + 30, px + 40, PATH_Y + 30, paint('#000000', 0.08, stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(cam_x - 2000, PATH_Y + 120, cam_x + 2000, 1600), paint(hexmix(grass, '#000000', 0.2)))
    if mood == 'rain':
        for k in range(10):
            px = x0 + k * 260 + 60
            c.drawOval(oval(px, PATH_Y + 60, 70, 10), paint('#9FB4CC', 0.35))


def _bridge(c, x, base, color):
    for k in range(5):
        cx = x + k * 260
        arc = skia.Path()
        arc.moveTo(cx - 130, base)
        arc.quadTo(cx, base - 120, cx + 130, base)
        c.drawPath(arc, paint(color, stroke=22))
    c.drawRect(skia.Rect.MakeLTRB(x - 160, base - 150, x + 1200, base - 128), paint(color))


def _trees(c, x0, x1, base, mood):
    x = x0
    k = 0
    canopy = {'dawn': '#2E4A3E', 'golden': '#4E7A44', 'rain': '#2A3D34', 'snow': '#C8D2DE', 'autumn': '#C8642E'}[mood]
    alt = {'autumn': '#E09A3A', 'snow': '#E6ECF4'}.get(mood, hexmix(canopy, '#FFFFFF', 0.12))
    while x < x1:
        h = hrange(120, 200, k, 41)
        r = hrange(60, 95, k, 42)
        c.drawLine(x, base, x, base - h + r * 0.4, paint('#3A2A24', stroke=14))
        c.drawCircle(x, base - h, r, paint(canopy))
        c.drawCircle(x - r * 0.4, base - h + r * 0.3, r * 0.7, paint(alt if k % 2 else canopy))
        c.drawCircle(x, base - h, r, paint('outline', 0.5, stroke=4))
        x += hrange(180, 320, k, 43)
        k += 1


# --- the mountain ------------------------------------------------------------------------------------------------------

def ridges(c, cam_x, base, colors, seeds, amp=(220, 160, 110), f=(0.1, 0.25, 0.45), glow=None):
    for k, (colr, sd, a_, ff) in enumerate(zip(colors, seeds, amp, f)):
        def draw(colr=colr, sd=sd, a_=a_, k=k):
            path = skia.Path()
            x0, x1 = -2400, 4400
            path.moveTo(x0, 2000)
            n = 60
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n
                y = base + k * 70 - a_ * (0.5 + 0.5 * noise1(x / 420.0, sd)) - a_ * 0.4 * noise1(x / 160.0, sd + 9)
                path.lineTo(x, y)
            path.lineTo(x1, 2000)
            path.close()
            c.drawPath(path, paint(colr))
            if glow:
                c.drawPath(path, paint(glow, 0.25, stroke=3))
        layer(c, cam_x, ff, draw)


def trailhead(c, T, cam_x=960):
    sky(c, 'night')
    stars(c, T, -400, -300, 2400, 600, n=160, seed=5)
    ridges(c, cam_x, 760, ['#0F1630', '#0B1126', '#080C1C'], [3, 7, 11])
    # the peak far away with the summit marked by a single star
    c.drawRect(skia.Rect.MakeLTRB(-2000, PATH_Y, 4000, 1600), paint('#0A0D16'))
    c.drawLine(-2000, PATH_Y, 4000, PATH_Y, paint('#1E2436', stroke=4))
    # the trail sign
    sx = 1160
    c.drawLine(sx, PATH_Y, sx, 640, paint('outline', stroke=18))
    c.drawLine(sx, PATH_Y, sx, 640, paint('#6B4E35', stroke=11))
    sign = poly([(sx - 120, 640), (sx + 160, 640), (sx + 200, 680), (sx + 160, 720), (sx - 120, 720)], True)
    c.drawPath(sign, paint('#7A5638'))
    c.drawPath(sign, paint('outline', stroke=5))
    text(c, 'SUMMIT  4.2 km', sx + 30, 693, 34, 'Fredoka-700', '#F2E6CF')
    for k in range(9):
        gx = hrange(-200, 2200, k, 61)
        c.drawLine(gx, PATH_Y, gx + 8, PATH_Y - 30, paint('#1B2233', stroke=4))
        c.drawLine(gx, PATH_Y, gx - 10, PATH_Y - 22, paint('#1B2233', stroke=4))


def slope_y(x):
    """The trail on the mountainside: climbing to the right (about 17 degrees), gently uneven."""
    return 1040 - 0.31 * x + 10 * noise1(x / 260.0, 4)


def mountainside(c, T, cam_x, cam_y, dawn=0.0):
    sky_mix = [(0.0, hexmix('#05070F', '#141C44', dawn)), (0.55, hexmix('#0E1630', '#3B3A78', dawn)),
               (0.85, hexmix('#1B2647', '#A85A72', dawn)), (1.0, hexmix('#1B2647', '#F49A6A', dawn))]
    grad(c, (cam_x - 2400, cam_y - 1400, cam_x + 2400, cam_y + 700), sky_mix)
    stars(c, T, cam_x - 1400, cam_y - 900, cam_x + 1400, cam_y + 200, n=160, seed=8, a=1 - 0.8 * dawn)
    layer(c, cam_x, 0.12, lambda: _far_peaks(c, cam_x, cam_y + 260, dawn), cam_y=cam_y, fy=0.12)
    # the slope itself
    path = skia.Path()
    x0, x1 = cam_x - 2200, cam_x + 2200
    path.moveTo(x0, slope_y(x0) + 2000)
    for i in range(81):
        x = x0 + (x1 - x0) * i / 80
        path.lineTo(x, slope_y(x))
    path.lineTo(x1, slope_y(x1) + 2000)
    path.close()
    c.drawPath(path, paint(hexmix('#141826', '#2A2238', dawn)))
    c.drawPath(path, paint(hexmix('#2A3350', '#C97A6A', dawn), 0.8, stroke=5))
    # rocks and grass tufts along the trail
    k0 = math.floor(x0 / 180)
    for k in range(k0, k0 + 26):
        x = k * 180 + hrange(-40, 40, k, 71)
        y = slope_y(x)
        if hrand(k, 72) > 0.5:
            rr = hrange(18, 40, k, 73)
            c.drawPath(poly([(x - rr, y + 6), (x - rr * 0.4, y - rr * 0.8), (x + rr * 0.6, y - rr * 0.5), (x + rr, y + 6)], True),
                       paint(hexmix('#232838', '#4A3A48', dawn)))
        else:
            c.drawLine(x, y, x - 8, y - 22, paint(hexmix('#2A3448', '#6A5A50', dawn), stroke=4))
            c.drawLine(x, y, x + 6, y - 18, paint(hexmix('#2A3448', '#6A5A50', dawn), stroke=4))


def _far_peaks(c, cam_x, base, dawn):
    ridges(c, 0, base, [hexmix('#10183A', '#5A4A86', dawn), hexmix('#0C1330', '#3E3A6A', dawn)], [21, 25],
           amp=(300, 200), f=(1.0, 1.0))


# --- the summit ------------------------------------------------------------------------------------------------------------

SUMMIT_Y = 760        # the flat top of the summit rock
SUMMIT_X = (720, 1240)


def summit_sky(c, T, sun, cam_x=960, cam_y=540):
    """sun 0..1: 0 the sky just before, 1 the sun well up."""
    top = hexmix('#141A44', '#3A5AA8', sun)
    mid = hexmix('#5B3F7A', '#E99A8A', sun)
    low = hexmix('#E07A6A', '#FFD49A', sun)
    grad(c, (cam_x - 2600, cam_y - 1600, cam_x + 2600, cam_y + 600), [(0.0, top), (0.55, mid), (0.82, low), (1.0, low)])
    stars(c, T, cam_x - 1600, cam_y - 1200, cam_x + 1600, cam_y - 200, n=90, seed=12, a=(1 - sun) * 0.6)


def sun_disc(c, x, y, r, a=1.0, bloom=1.0):
    c.drawCircle(x, y, r * 9, paint('#FFB45E', 0.22 * a * bloom, blur=r * 3.5, blend='add'))
    c.drawCircle(x, y, r * 4.2, paint('#FFD49A', 0.35 * a * bloom, blur=r * 1.6, blend='add'))
    c.drawCircle(x, y, r * 1.6, paint('#FFF1C9', 0.6 * a, blur=r * 0.5, blend='add'))
    c.drawCircle(x, y, r, paint('#FFF8E6', a))


def cloud_sea(c, T, base, sun, cam_x=960, rows=4):
    for row in range(rows):
        y = base + row * 60
        lit = hexmix('#8A6A9A', '#FFC9A0', sun * (1 - 0.18 * row))
        shade = hexmix('#3A3460', '#B9809A', sun * (1 - 0.2 * row))
        drift = T * (6 + row * 4)
        k0 = math.floor((cam_x - 1600 - drift) / 140)
        for k in range(k0, k0 + 26):
            x = k * 140 + drift + hrange(-30, 30, k, row, 81)
            r = hrange(70, 130, k, row, 82)
            c.drawCircle(x, y + hrange(-14, 14, k, row, 83), r, paint(shade))
            c.drawCircle(x - r * 0.15, y - r * 0.18 + hrange(-14, 14, k, row, 83), r * 0.85, paint(lit))
        c.drawRect(skia.Rect.MakeLTRB(cam_x - 2600, y + 40, cam_x + 2600, y + 900), paint(shade))


def summit_rock(c, sun):
    path = skia.Path()
    path.moveTo(200, 1400)
    path.cubicTo(380, 1000, 560, SUMMIT_Y + 40, SUMMIT_X[0], SUMMIT_Y + 4)
    path.lineTo(SUMMIT_X[0] + 120, SUMMIT_Y - 6)
    path.lineTo(SUMMIT_X[1] - 140, SUMMIT_Y - 2)
    path.lineTo(SUMMIT_X[1], SUMMIT_Y + 8)
    path.cubicTo(1400, SUMMIT_Y + 60, 1560, 1000, 1760, 1400)
    path.close()
    c.drawPath(path, paint(hexmix('#1A1626', '#3A2830', sun)))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    for k in range(10):
        x = 400 + k * 130
        c.drawLine(x, SUMMIT_Y + 60, x - 60, 1400, paint('#000000', 0.18, stroke=8))
    c.restore()
    c.drawPath(path, paint(hexmix('#3A3350', '#FFB27A', sun), 0.9, stroke=6))
