"""Shared cast, props, sets and poses for 'He's Waiting.'.

The bedroom is drawn once in plain daylight colours and lit by a light map (engine/light.py), so the same room
serves for 2:47 AM, dawn, a rainy morning and noon.
"""
from __future__ import annotations

import math
import sys
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'studio'))

import skia  # noqa: E402

from cues import EV, VITALITY  # noqa: E402
from engine.core import H, W, clamp, hrand, hrange, noise1, smooth  # noqa: E402
from engine.draw import circle, col, mixc, oval, paint, poly, rrect, text  # noqa: E402
from engine.light import beam, begin_light, end_light, pool, rim  # noqa: E402
from engine.motion import Curve, breath, settle  # noqa: E402
from engine.rig import SHADOW, Character, Look, blink  # noqa: E402

# --- cast ---------------------------------------------------------------------------------------------------

MUSTARD = '#D6A23D'
SKIN = '#E3BE98'
HAIR = '#2E2420'
HERO_LOOK = Look(skin=SKIN, top=MUSTARD, pants='#2B3140', hair='swoop', hair_color=HAIR)
HERO = Character(HERO_LOOK, seed=1)
SHADE = Character(SHADOW, seed=5)


def hx(rgb):
    return '#%02X%02X%02X' % tuple(int(v) for v in rgb)


@lru_cache(maxsize=512)
def _old_look(vq, run=False):
    v = vq / 100.0
    u = 1 - v
    look = replace(HERO_LOOK, skin=hx(mixc(SKIN, '#B8ADA3', 0.55 * u)), top=hx(mixc(MUSTARD, '#8C8574', 0.85 * u)),
                   pants=hx(mixc('#2B3140', '#3A3B40', 0.5 * u)), hair='swoop_thin', hair_color='#E8E5DF',
                   brow_color='#D8D3CB', stubble='#DCD7CF', wrinkles=1.0, arm_w=13.5 + 1.5 * v,
                   leg_w=16.5 + 1.0 * v, shoulder_w=70 + 6 * v)
    if run:
        look = replace(look, headband='#E8E2D4')
    return look


def old_man(v, run=False):
    """The hero at 75. v is his vitality (0 = dying, 1 = strong): it sets his colour, his frame and his posture."""
    return Character(_old_look(int(round(clamp(v) * 100)), run), seed=2)


VIT = Curve(VITALITY)


def vitality(T):
    return clamp(VIT(T))


def old_face(v, T, seed=2):
    """Face and posture fields that follow his vitality."""
    u = 1 - v
    return dict(eye=(0.5 + 0.5 * v) * blink(T, seed, 4.4), bags=1.25 * u, brow=-4 - 13 * u,
                smile=-0.32 * u + 0.45 * max(0.0, v - 0.45), shiver=0.35 * u * u,
                breathe=breath(T, 0.2 + 0.1 * u, 0.6 + 0.6 * u, seed))


# --- small helpers -------------------------------------------------------------------------------------------

def to_world(pose, local):
    """A point in a character's local frame -> world (the inverse of rig.to_local)."""
    s = pose.get('scale', 1.0)
    x, y = local[0] * s * pose.get('facing', 1), local[1] * s
    r = math.radians(pose.get('rot', 0.0))
    return (pose.get('x', 0.0) + x * math.cos(r) - y * math.sin(r), pose.get('y', 0.0) + x * math.sin(r) + y * math.cos(r))


def to_local(pose, world):
    from engine.rig import to_local as tl
    return tl(pose, world)


def in_world(c, fn):
    """Wrap fn(c) so it draws in world coordinates from inside a character layer callback."""
    m = c.getTotalMatrix()

    def layer(cc, j):
        cc.save()
        cc.setMatrix(m)
        fn(cc)
        cc.restore()
    return layer


def ticks(T, every=1.0, offset=0.0):
    """The second hand's position in ticks with a little overshoot after each tick."""
    k = math.floor((T - offset) / every)
    dt = (T - offset) - k * every
    return k + 1 - math.exp(-dt * 38) * (1 + 0.0 * dt) + settle(dt, 0.0, 0.08, 9.0, 0.06)


# --- props ---------------------------------------------------------------------------------------------------

GOLD = '#D9A93F'


def pocket_watch(c, x, y, r, T, *, hand_angle=None, stopped=None, open_lid=True, glow=0.0, crack=True, a=1.0,
                 chain=None, detail=True):
    """A brass pocket watch, open, face toward the viewer. The second hand ticks once a second until `stopped`."""
    c.save()
    c.translate(x, y)
    if a < 1:
        c.saveLayerAlpha(None, int(255 * a))
    if chain:
        cx, cy = chain
        path = skia.Path()
        path.moveTo(0, -r * 1.1)
        path.quadTo((cx - x) * 0.5, (cy - y) * 0.5 + r * 2.2, cx - x, cy - y)
        c.drawPath(path, paint('#8C6A2A', stroke=max(2.0, r * 0.12)))
        c.drawPath(path, paint('#F2D27A', 0.5, stroke=max(1.0, r * 0.05)))
    if glow > 0:
        c.drawCircle(0, 0, r * 2.4, paint('#FFD98A', 0.35 * glow, blur=r * 0.9, blend='add'))
    # bow and crown
    c.drawCircle(0, -r * 1.16, r * 0.2, paint(GOLD, stroke=max(2.0, r * 0.09)))
    c.drawRRect(rrect(-r * 0.13, -r * 1.08, r * 0.26, r * 0.2, r * 0.05), paint(GOLD))
    if open_lid:
        lid = oval(0, r * 2.05, r * 0.98, r * 0.92)
        c.drawOval(lid, paint('#B68A2E'))
        c.drawOval(lid, paint('outline', stroke=max(2.0, r * 0.08)))
        if detail:
            c.drawOval(oval(0, r * 2.05, r * 0.7, r * 0.64), paint('#E9C66B', 0.45, stroke=max(1.0, r * 0.04)))
    c.drawCircle(0, 0, r, paint(GOLD))
    c.drawCircle(0, 0, r * 0.86, paint('#F3EBDD'))
    if detail:
        for k in range(12):
            ang = k * math.tau / 12
            r0 = r * (0.66 if k % 3 == 0 else 0.72)
            c.drawLine(math.sin(ang) * r0, -math.cos(ang) * r0, math.sin(ang) * r * 0.8, -math.cos(ang) * r * 0.8,
                       paint('#2B2B30', stroke=max(1.0, r * (0.06 if k % 3 == 0 else 0.03))))
        # small seconds dial
        c.drawCircle(0, r * 0.4, r * 0.18, paint('#2B2B30', stroke=max(1.0, r * 0.02)))
    # hands at 2:47
    for ang, ln, w in ((2.783 / 12 * math.tau, 0.42, 0.075), (47 / 60 * math.tau, 0.62, 0.05)):
        c.drawLine(0, 0, math.sin(ang) * r * ln, -math.cos(ang) * r * ln, paint('#1E1E24', stroke=max(1.5, r * w)))
    if hand_angle is None:
        tt = T if stopped is None else min(T, stopped)
        k = math.floor(tt)
        dt = tt - k
        step = k + (1 - math.exp(-dt * 40)) + (settle(dt, 0.0, 0.12, 10.0, 0.05) if stopped is None or T < stopped else 0)
        hand_angle = step / 60 * math.tau
    sx, sy = 0, r * 0.4
    c.drawLine(sx, sy, sx + math.sin(hand_angle) * r * 0.16, sy - math.cos(hand_angle) * r * 0.16,
               paint('#B3362E', stroke=max(1.0, r * 0.025)))
    sweep = hand_angle * 1.0
    c.drawLine(0, 0, math.sin(sweep) * r * 0.74, -math.cos(sweep) * r * 0.74, paint('#B3362E', stroke=max(1.0, r * 0.022)))
    c.drawCircle(0, 0, r * 0.05, paint('#1E1E24'))
    if crack:
        cp = skia.Path()
        cp.moveTo(-r * 0.62, -r * 0.35)
        cp.lineTo(-r * 0.3, -r * 0.18)
        cp.lineTo(-r * 0.12, -r * 0.3)
        cp.lineTo(r * 0.18, -r * 0.05)
        cp.moveTo(-r * 0.3, -r * 0.18)
        cp.lineTo(-r * 0.36, r * 0.12)
        c.drawPath(cp, paint('#FFFFFF', 0.75, stroke=max(1.0, r * 0.018)))
    # glass sheen
    c.drawArc(oval(0, 0, r * 0.74, r * 0.74), 200, 50, False, paint('#FFFFFF', 0.45, stroke=max(1.0, r * 0.05)))
    c.drawCircle(0, 0, r, paint('outline', stroke=max(2.0, r * 0.09)))
    if a < 1:
        c.restore()
    c.restore()


# The phone's scrolling clips: each swipe brings a new colour of light
CLIP_COLORS = ['#9CD8FF', '#FFB36B', '#FF7FB2', '#8CFFC1', '#FFFFFF', '#B59CFF', '#FFD86B', '#7FE3FF']


def clip_index(T, swipes=None):
    swipes = EV['swipes'] if swipes is None else swipes
    k = sum(1 for s in swipes if T >= s)
    return k


def phone_light(T, swipes=None, base=0.85):
    """(colour, brightness) of the screen: a little pop and settle at each swipe, a slow flicker otherwise."""
    swipes = EV['swipes'] if swipes is None else swipes
    k = clip_index(T, swipes)
    colr = CLIP_COLORS[k % len(CLIP_COLORS)]
    last = max([s for s in swipes if T >= s], default=-10.0)
    pop = math.exp(-(T - last) / 0.18) if T >= last else 0.0
    flick = 0.06 * noise1(T * 6.0, 9)
    return colr, clamp(base + 0.35 * pop + flick, 0.0, 1.4)


def scroll_screen(c, w, h, T, swipes=None, seed=0):
    """What's on the screen: stacked clip thumbnails sliding up at each swipe."""
    swipes = EV['swipes'] if swipes is None else swipes
    k = clip_index(T, swipes)
    last = max([s for s in swipes if T >= s], default=-10.0)
    slide = 1 - (1 - min(1.0, (T - last) / 0.22)) ** 3 if T >= last else 1.0
    for j in (-1, 0, 1):
        idx = k + j
        top = (j - (1 - slide)) * h
        colr = CLIP_COLORS[idx % len(CLIP_COLORS)]
        c.drawRect(skia.Rect.MakeXYWH(0, top, w, h), paint(mixc(colr, '#101018', 0.35)))
        c.drawCircle(w * 0.5, top + h * 0.45, w * 0.22, paint(colr, 0.9))
        c.drawRect(skia.Rect.MakeXYWH(w * 0.1, top + h * 0.78, w * 0.6, h * 0.05), paint('#FFFFFF', 0.7))
        c.drawRect(skia.Rect.MakeXYWH(w * 0.1, top + h * 0.86, w * 0.4, h * 0.04), paint('#FFFFFF', 0.45))


def phone_side(c, x, y, angle, T, scale=1.0, on=True, swipes=None):
    """A phone seen at a slant, screen tipped toward us a little so its light and content read."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.scale(scale, scale)
    w, h = 44, 82
    body = rrect(-w / 2, -h / 2, w, h, 8)
    c.drawRRect(body, paint('#16171C'))
    scr = rrect(-w / 2 + 3, -h / 2 + 4, w - 6, h - 8, 5)
    if on:
        c.save()
        c.clipRRect(scr, doAntiAlias=True)
        c.translate(-w / 2 + 3, -h / 2 + 4)
        scroll_screen(c, w - 6, h - 8, T, swipes)
        c.restore()
    else:
        c.drawRRect(scr, paint('#0C0D10'))
    c.drawRRect(body, paint('outline', stroke=3.5))
    c.restore()


def cane(c, hand, tip, a=1.0):
    """A walking stick from the hand to its tip, with a crook over the hand."""
    hx_, hy = hand
    tx, ty = tip
    c.drawLine(hx_, hy - 4, tx, ty, paint('outline', a, stroke=11))
    c.drawLine(hx_, hy - 4, tx, ty, paint('#7A5638', a, stroke=6))
    crook = skia.Path()
    crook.moveTo(hx_, hy - 4)
    crook.cubicTo(hx_, hy - 26, hx_ + 26, hy - 26, hx_ + 24, hy - 8)
    c.drawPath(crook, paint('outline', a, stroke=11))
    c.drawPath(crook, paint('#7A5638', a, stroke=6))
    c.drawCircle(tx, ty, 4, paint('#2B2B30', a))


def curtain_panel(c, x0, x1, top, bottom, open_amt, side, color='#56677F', T=0.0, sway=0.0):
    """One curtain panel hanging from the rod between x0 and x1; open_amt 0..1 bunches it toward its side."""
    w = (x1 - x0)
    pw = w * (1 - 0.72 * open_amt)
    if side < 0:
        a0, a1 = x0, x0 + pw
    else:
        a0, a1 = x1 - pw, x1
    folds = 5
    path = skia.Path()
    path.moveTo(a0, top)
    path.lineTo(a1, top)
    hem = []
    for k in range(folds * 2 + 1):
        u = k / (folds * 2)
        xx = a1 - (a1 - a0) * u
        yy = bottom + (8 if k % 2 else 0) + sway * math.sin(T * 1.3 + u * 6) * 6
        hem.append((xx + sway * 5 * math.sin(T * 1.1 + u * 3), yy))
    for p in hem:
        path.lineTo(*p)
    path.close()
    c.drawPath(path, paint(color))
    for k in range(1, folds * 2):
        xx = a0 + (a1 - a0) * k / (folds * 2)
        c.drawLine(xx, top + 6, xx + sway * 3, bottom, paint('#000000', 0.16 if k % 2 else 0.07, stroke=6))
    c.drawPath(path, paint('outline', stroke=4))


# --- the bedroom -----------------------------------------------------------------------------------------------

FLOOR = 880
MATT = 818              # mattress top: a low bed, so the old man's feet reach the floor when he sits on it
BED = (560, 1120)       # head end (left) and foot end (right)
WINDOW = (1150, 300, 270, 300)   # x, y, w, h
DOOR = (1480, 440, 180)          # x, top, width
DESK = (60, 380)
NIGHTSTAND = (418, 530)
POSTER = (740, 380, 170, 230)

NOTES = [(130, 455, 'RUN\n5K', -6), (232, 430, 'LEARN\nGUITAR', 4), (330, 470, 'SAVE\nMONEY', -3),
         (190, 548, 'READ\nMORE', 5), (300, 562, 'CALL\nMOM', -4)]


def sky(c, x, y, w, h, T, mode='night', seed=0):
    """What the window shows: night with the moon and the city, dawn, a rainy grey morning, or day."""
    top, bot = {'night': ('#0B1328', '#1C2A4D'), 'dawn': ('#2E3E70', '#F19A63'), 'rain': ('#2A3140', '#4A5468'),
                'day': ('#6FA8DC', '#CFE6F7'), 'deep': ('#05070F', '#0D1428')}[mode]
    sh = skia.GradientShader.MakeLinear(points=[(x, y), (x, y + h)], colors=[col(top), col(bot)])
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint(top, shader=sh))
    if mode in ('night', 'deep'):
        for i in range(16):
            sx, sy = x + hrange(8, w - 8, i, seed, 1), y + hrange(8, h * 0.55, i, seed, 2)
            tw = 0.5 + 0.5 * math.sin(T * 1.7 + i * 2.1)
            c.drawCircle(sx, sy, 1.6, paint('#FFFFFF', 0.25 + 0.45 * tw))
        mx, my = x + w * 0.7, y + h * 0.28
        c.drawCircle(mx, my, 70, paint('#9DB7FF', 0.25, blur=30, blend='add'))
        c.drawCircle(mx, my, 28, paint('#EEF2FF'))
        c.drawCircle(mx + 11, my - 7, 24, paint(top))
    if mode == 'dawn':
        c.drawCircle(x + w * 0.3, y + h * 0.95, 60, paint('#FFD3A0', 0.6, blur=26, blend='add'))
    # the city
    base = y + h
    for k in range(9):
        bx = x - 10 + k * (w / 7.5)
        bh = hrange(40, 120, k, seed, 3)
        bw = hrange(26, 44, k, seed, 4)
        bcol = {'night': '#090D18', 'deep': '#05070D', 'dawn': '#3A3150', 'rain': '#2C313C', 'day': '#8FA6BC'}[mode]
        c.drawRect(skia.Rect.MakeXYWH(bx, base - bh, bw, bh), paint(bcol))
        if mode in ('night', 'deep', 'rain'):
            for r in range(int(bh / 16)):
                for q in range(2):
                    if hrand(k, r, q, seed) > 0.72:
                        c.drawRect(skia.Rect.MakeXYWH(bx + 6 + q * 13, base - bh + 8 + r * 16, 6, 7),
                                   paint('#F2C26B', 0.75))
    if mode == 'rain':
        for i in range(40):
            rx = x + hrange(0, w, i, 77)
            ry = y + ((hrange(0, h, i, 78) + T * 600) % h)
            c.drawLine(rx, ry, rx - 3, ry + 16, paint('#BFD3EA', 0.45, stroke=1.6))
        for i in range(14):
            dx, dy = x + hrange(10, w - 10, i, 91), y + hrange(10, h - 10, i, 92)
            slide = (T * hrange(10, 40, i, 93)) % 60
            c.drawCircle(dx, dy + slide, 3.2, paint('#DDE8F5', 0.55))


def mountain_poster(c, x, y, w, h):
    r = rrect(x, y, w, h, 4)
    sh = skia.GradientShader.MakeLinear(points=[(x, y), (x, y + h)], colors=[col('#F7B267'), col('#F25F5C')])
    c.drawRRect(r, paint('#F7B267', shader=sh))
    c.save()
    c.clipRRect(r)
    c.drawCircle(x + w * 0.62, y + h * 0.42, w * 0.16, paint('#FFF1C9'))
    peak = poly([(x - 10, y + h), (x + w * 0.42, y + h * 0.36), (x + w * 0.58, y + h * 0.5), (x + w * 0.72, y + h * 0.4),
                 (x + w + 10, y + h)], True)
    c.drawPath(peak, paint('#3B2F4A'))
    snow = poly([(x + w * 0.42, y + h * 0.36), (x + w * 0.35, y + h * 0.47), (x + w * 0.42, y + h * 0.44),
                 (x + w * 0.47, y + h * 0.48), (x + w * 0.5, y + h * 0.44)], True)
    c.drawPath(snow, paint('#F4EFEA'))
    c.restore()
    text(c, 'ONE DAY.', x + w / 2, y + h - 18, 26, 'LuckiestGuy', '#FFF6E6')
    c.drawRRect(r, paint('outline', stroke=4))
    c.drawCircle(x + w / 2, y + 8, 4, paint('#C8463D'))


def desk(c, T, laptop=0.0, books=False):
    x0, x1 = DESK
    top = 720
    c.drawRect(skia.Rect.MakeLTRB(x0 + 14, top + 14, x0 + 30, FLOOR), paint('#5A4535'))
    c.drawRect(skia.Rect.MakeLTRB(x1 - 30, top + 14, x1 - 14, FLOOR), paint('#5A4535'))
    c.drawRect(skia.Rect.MakeLTRB(x0 + 14, top + 14, x0 + 30, FLOOR), paint('outline', stroke=3.5))
    c.drawRect(skia.Rect.MakeLTRB(x1 - 30, top + 14, x1 - 14, FLOOR), paint('outline', stroke=3.5))
    slab = rrect(x0, top, x1 - x0, 18, 5)
    c.drawRRect(slab, paint('#8A6544'))
    c.drawRRect(slab, paint('outline', stroke=4))
    # laptop, side view, lid open toward the chair (left)
    lx = x0 + 170
    c.drawRRect(rrect(lx - 70, top - 8, 140, 9, 3), paint('#9BA3AE'))
    c.drawRRect(rrect(lx - 70, top - 8, 140, 9, 3), paint('outline', stroke=3))
    lid = poly([(lx + 66, top - 8), (lx + 96, top - 118), (lx + 104, top - 116), (lx + 74, top - 6)], True)
    c.drawPath(lid, paint('#9BA3AE'))
    c.drawPath(lid, paint('outline', stroke=3))
    if books:
        for k, (bw, bh, colr) in enumerate(((120, 22, '#3F5F8A'), (110, 20, '#B0624A'), (126, 24, '#4F7A6B'))):
            by = top - 8 - 22 * (k + 1)
            c.drawRRect(rrect(x0 + 20, by, bw, bh, 3), paint(colr))
            c.drawRRect(rrect(x0 + 20, by, bw, bh, 3), paint('outline', stroke=3))
    return (lx + 85, top - 62)


def chair(c, x, facing=1):
    c.drawRect(skia.Rect.MakeLTRB(x - 40, 770, x + 40, 786), paint('#3B3E46'))
    c.drawRect(skia.Rect.MakeLTRB(x - 40, 770, x + 40, 786), paint('outline', stroke=3.5))
    bx = x - 40 * facing
    c.drawLine(bx, 786, bx, 650, paint('outline', stroke=12))
    c.drawLine(bx, 786, bx, 650, paint('#3B3E46', stroke=6))
    for lx in (x - 32, x + 32):
        c.drawLine(lx, 786, lx, FLOOR, paint('outline', stroke=9))
        c.drawLine(lx, 786, lx, FLOOR, paint('#2B2E36', stroke=4))


def nightstand(c, T, lamp=0.0, watch=False, phone_on_stand=None, alarm=0.0, drawer=0.0):
    x0, x1 = NIGHTSTAND
    top = 790
    box = rrect(x0, top, x1 - x0, FLOOR - top, 6)
    c.drawRRect(box, paint('#6E5442'))
    c.drawRRect(box, paint('outline', stroke=4))
    dy = top + 20
    c.drawRRect(rrect(x0 + 8 + drawer * 50, dy, x1 - x0 - 16, 32, 4), paint('#7E624E'))
    c.drawRRect(rrect(x0 + 8 + drawer * 50, dy, x1 - x0 - 16, 32, 4), paint('outline', stroke=3))
    c.drawCircle((x0 + x1) / 2 + drawer * 50, dy + 16, 4, paint('#B9A27A'))
    lx = x0 + 30
    c.drawRect(skia.Rect.MakeLTRB(lx - 3, top - 70, lx + 3, top), paint('#2B2B30'))
    c.drawOval(oval(lx, top - 2, 20, 6), paint('#2B2B30'))
    shade = poly([(lx - 24, top - 70), (lx + 24, top - 70), (lx + 16, top - 108), (lx - 16, top - 108)], True)
    c.drawPath(shade, paint(mixc('#B59B6C', '#FFE2A8', lamp)))
    c.drawPath(shade, paint('outline', stroke=4))
    if phone_on_stand is not None:
        on, face_down = phone_on_stand
        px, py = x0 + 80, top - 6
        c.drawRRect(rrect(px - 24, py - 7, 48, 9, 3), paint('#16171C'))
        if not face_down and on > 0:
            c.drawRRect(rrect(px - 21, py - 9, 42, 4, 2), paint('#BFE6FF', 0.9 * on))
        c.drawRRect(rrect(px - 24, py - 7, 48, 9, 3), paint('outline', stroke=3))
    if watch:
        pocket_watch(c, x0 + 82, top - 16, 13, T, open_lid=False, detail=False, crack=False)
    return (lx, top - 90)


def bed_back(c):
    """Headboard, frame and mattress (drawn under the sleeper)."""
    x0, x1 = BED
    c.drawRRect(rrect(x0 - 26, MATT - 190, 34, FLOOR - (MATT - 190), 10), paint('#7A5A44'))
    c.drawRRect(rrect(x0 - 26, MATT - 190, 34, FLOOR - (MATT - 190), 10), paint('outline', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(x1 - 18, MATT + 30, x1 - 6, FLOOR), paint('#5A4535'))
    c.drawRect(skia.Rect.MakeLTRB(x1 - 18, MATT + 30, x1 - 6, FLOOR), paint('outline', stroke=3))
    frame = rrect(x0, MATT + 26, x1 - x0, 26, 6)
    c.drawRRect(frame, paint('#7A5A44'))
    c.drawRRect(frame, paint('outline', stroke=4))
    matt = rrect(x0 + 4, MATT, x1 - x0 - 8, 36, 12)
    c.drawRRect(matt, paint('#E8E4DC'))
    c.drawRRect(matt, paint('outline', stroke=4))
    pil = rrect(x0 + 6, MATT - 46, 120, 52, 22)
    c.drawRRect(pil, paint('#F0ECE4'))
    c.drawRRect(pil, paint('outline', stroke=4))


def blanket_path(x_from, contour=None):
    """The quilt's outline (see blanket())."""
    x1 = BED[1]
    path = skia.Path()
    pts = list(contour or [(x_from, MATT - 4)])
    path.moveTo(pts[0][0], MATT + 34)
    path.lineTo(*pts[0])
    for k in range(1, len(pts)):
        p0, p1 = pts[k - 1], pts[k]
        mx = (p0[0] + p1[0]) / 2
        path.cubicTo(mx, p0[1], mx, p1[1], *p1)
    last = pts[-1]
    path.cubicTo(last[0] + 40, last[1], x1 - 40, MATT - 6, x1 + 4, MATT - 2)
    path.cubicTo(x1 + 14, MATT + 10, x1 + 12, MATT + 40, x1 + 6, MATT + 52)
    path.lineTo(pts[0][0], MATT + 56)
    path.close()
    return path


def under_quilt(c, x_from, contour):
    """Clip away what the quilt covers (so a rim light never outlines a body under the covers)."""
    c.clipPath(blanket_path(x_from, contour), skia.ClipOp.kDifference, True)


def blanket(c, x_from, contour=None, color='#3F5E86', over_feet=True, tent=0.0, T=0.0):
    """The quilt from x_from to the foot of the bed; contour [(x, y)] is its top edge over a sleeper."""
    x1 = BED[1]
    path = skia.Path()
    pts = list(contour or [(x_from, MATT - 4)])
    path.moveTo(pts[0][0], MATT + 34)
    path.lineTo(*pts[0])
    for k in range(1, len(pts)):
        p0, p1 = pts[k - 1], pts[k]
        mx = (p0[0] + p1[0]) / 2
        path.cubicTo(mx, p0[1], mx, p1[1], *p1)
    last = pts[-1]
    path.cubicTo(last[0] + 40, last[1], x1 - 40, MATT - 6, x1 + 4, MATT - 2)
    path.cubicTo(x1 + 14, MATT + 10, x1 + 12, MATT + 40, x1 + 6, MATT + 52)
    n = 9
    for k in range(n + 1):
        u = k / n
        xx = x1 + 6 - (x1 + 6 - pts[0][0]) * u
        path.lineTo(xx, MATT + 50 + (6 if k % 2 else 0))
    path.close()
    c.drawPath(path, paint(color))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    for k in range(-6, 30):
        xx = x_from - 100 + k * 36
        c.drawLine(xx, MATT - 120, xx + 70, MATT + 70, paint('#FFFFFF', 0.06, stroke=3))
    c.drawRect(skia.Rect.MakeLTRB(x_from - 50, MATT + 30, x1 + 30, MATT + 60), paint('#000000', 0.12))
    c.restore()
    c.drawPath(path, paint('outline', stroke=4))


def room_shell(c, T, door_open=0.0, door_light=0.0):
    """Walls, floor, window frame with sky, the door, the desk wall and the poster."""
    # wall and floor
    c.drawRect(skia.Rect.MakeLTRB(-1200, -800, 3200, FLOOR), paint('#5B6177'))
    for k in range(-30, 70):
        xx = k * 48
        c.drawLine(xx, -800, xx, FLOOR - 40, paint('#000000', 0.05, stroke=14))
    c.drawRect(skia.Rect.MakeLTRB(-1200, FLOOR - 40, 3200, FLOOR), paint('#45495A'))
    c.drawLine(-1200, FLOOR - 40, 3200, FLOOR - 40, paint('outline', 0.6, stroke=3))
    c.drawRect(skia.Rect.MakeLTRB(-1200, FLOOR, 3200, 2400), paint('#5C4636'))
    for k in range(10):
        yy = FLOOR + 18 + k * k * 9
        c.drawLine(-1200, yy, 3200, yy, paint('#000000', 0.18, stroke=3))
    c.drawLine(-1200, FLOOR, 3200, FLOOR, paint('outline', stroke=4))
    # door (far right)
    dx, dtop, dw = DOOR
    c.drawRect(skia.Rect.MakeLTRB(dx - 12, dtop - 12, dx + dw + 12, FLOOR), paint('#D9D2C3'))
    c.drawRect(skia.Rect.MakeLTRB(dx - 12, dtop - 12, dx + dw + 12, FLOOR), paint('outline', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(dx, dtop, dx + dw, FLOOR), paint('#1A1C24'))
    if door_light > 0:
        c.drawRect(skia.Rect.MakeLTRB(dx, dtop, dx + dw, FLOOR), paint('#FFE3B0', door_light))
    leaf_w = dw * (1 - 0.82 * door_open)
    c.drawRect(skia.Rect.MakeLTRB(dx, dtop, dx + leaf_w, FLOOR), paint('#B89A74'))
    if leaf_w > 30:
        c.drawRect(skia.Rect.MakeLTRB(dx + 18, dtop + 24, dx + leaf_w - 18, dtop + 200), paint('#000000', 0.08))
        c.drawRect(skia.Rect.MakeLTRB(dx + 18, dtop + 230, dx + leaf_w - 18, FLOOR - 30), paint('#000000', 0.08))
        c.drawCircle(dx + leaf_w - 22, dtop + 230, 7, paint('#D9C27A'))
    c.drawRect(skia.Rect.MakeLTRB(dx, dtop, dx + leaf_w, FLOOR), paint('outline', stroke=4))
    # window
    x, y, w, h = WINDOW
    c.drawRect(skia.Rect.MakeLTRB(x - 14, y - 14, x + w + 14, y + h + 14), paint('#E3DED3'))
    c.drawRect(skia.Rect.MakeLTRB(x - 14, y - 14, x + w + 14, y + h + 14), paint('outline', stroke=4))
    mountain_poster(c, *POSTER)
    # wall calendar and notes above the desk
    return (x, y, w, h)


def window_glass(c, T, mode):
    x, y, w, h = WINDOW
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    sky(c, x, y, w, h, T, mode)
    c.restore()
    c.drawLine(x + w / 2, y, x + w / 2, y + h, paint('#E3DED3', stroke=10))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, paint('#E3DED3', stroke=10))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint('outline', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(x - 24, y + h + 8, x + w + 24, y + h + 24), paint('#D2CCBF'))
    c.drawRect(skia.Rect.MakeLTRB(x - 24, y + h + 8, x + w + 24, y + h + 24), paint('outline', stroke=4))


def curtains(c, T, open_amt=0.0, sway=0.0):
    x, y, w, h = WINDOW
    c.drawLine(x - 50, y - 30, x + w + 50, y - 30, paint('outline', stroke=10))
    c.drawLine(x - 50, y - 30, x + w + 50, y - 30, paint('#6B5444', stroke=5))
    curtain_panel(c, x - 40, x + w / 2 + 4, y - 30, y + h + 60, open_amt, -1, T=T, sway=sway)
    curtain_panel(c, x + w / 2 - 4, x + w + 40, y - 30, y + h + 60, open_amt, 1, T=T, sway=sway)


NOTE_FALLS = {0: 32.6, 1: 37.5, 2: 38.6, 3: 39.6, 4: 40.5}    # each goal lets go of the wall
NOTE_REPIN = 112.0                                               # after Day 1 he puts them all back up
NOTE_CHECKS = {0: 124.0, 1: 148.6, 2: 149.6, 3: 150.6, 4: 190.0}   # and ticks them off, one by one
NOTE_FLOOR = [(150, FLOOR + 10), (232, FLOOR + 18), (318, FLOOR + 8), (196, FLOOR + 26), (352, FLOOR + 22)]
NOTE_COLORS = ['#F6D654', '#FF9F7A', '#8FD3FF', '#A8E6A1', '#F6D654']


def wall_notes(c, T, fallen=None, drop=None, checked=None):
    """The goals on the wall above the desk. Unless told otherwise, they follow the story: one falls on the
    second day, the rest during the time-lapse, they lie on the floor until he pins them back after Day 1,
    then they get ticked off."""
    from engine.home import sticky
    for k, (x, y, txt, ang) in enumerate(NOTES):
        tf = NOTE_FALLS[k]
        if fallen is not None:
            gone = k in fallen
            falling = None
        else:
            gone = tf <= T < NOTE_REPIN
            falling = T - tf if gone and T - tf < 1.3 else None
        if gone and falling is None:
            fx, fy = NOTE_FLOOR[k]
            c.save()
            c.translate(fx, fy)
            c.scale(1.0, 0.3)
            c.rotate(ang * 3 + 20 * k)
            c.drawRect(skia.Rect.MakeXYWH(-34, -34, 68, 68), paint(NOTE_COLORS[k]))
            c.drawRect(skia.Rect.MakeXYWH(-34, -34, 68, 68), paint('outline', stroke=6))
            c.restore()
            continue
        xx, yy, rot = x, y, ang
        if falling is not None:
            u = falling
            # paper falls: a quick start, then it drifts down at an even speed, swinging side to side
            yy = y + (380 * u - 120 * (1 - math.exp(-u / 0.32)))
            land = NOTE_FLOOR[k][1] - 4
            sway = math.sin(u * 7.5) * 46 * min(1.0, u * 3)
            xx = x + sway + (NOTE_FLOOR[k][0] - x) * min(1.0, u / 1.2)
            rot = ang + 38 * math.sin(u * 7.5 + 0.8)
            if yy >= land:
                yy = land
        sticky(c, xx, yy, txt, rot, size=84, color=NOTE_COLORS[k])
        ticked = (k in checked) if checked is not None else T >= NOTE_CHECKS[k]
        if ticked and not gone:
            c.drawLine(x - 30, y + 16, x - 14, y + 30, paint('#2F9E5B', stroke=7))
            c.drawLine(x - 14, y + 30, x + 26, y - 18, paint('#2F9E5B', stroke=7))


# --- lighting moods ------------------------------------------------------------------------------------------------

def night_lights(c, T, phone_at=None, phone_amt=1.0, moon=1.0, ambient='#2A3150', lamp=0.0, extra=None):
    begin_light(c, ambient)
    x, y, w, h = WINDOW
    # moonlight through the window: the glass, a soft pool, a slanted beam across the foot of the bed
    pool(c, x + w / 2, y + h / 2, w * 0.95, h * 0.95, '#B8C8FF', 0.55 * moon)
    beam(c, poly([(x + 10, y + h), (x + w - 10, y + h), (x + w - 260, FLOOR + 40), (x - 330, FLOOR + 40)], True),
         '#7F95D6', 0.35 * moon, blur=40)
    if phone_at is not None:
        colr, br = phone_light(T)
        px, py = phone_at
        pool(c, px, py + 20, 300, 260, colr, 0.95 * br * phone_amt)
        pool(c, px, py + 30, 120, 110, '#FFFFFF', 0.35 * br * phone_amt)
        pool(c, 1010, 690, 230, 200, colr, 0.16 * br * phone_amt)   # spill on the end of the bed
    if lamp > 0:
        lx, ly = NIGHTSTAND[0] + 30, 700
        pool(c, lx, ly, 460, 360, '#FFC879', 0.9 * lamp)
    if extra:
        extra(c)
    end_light(c)


def day_lights(c, T, warm=0.0, ambient='#F3EEE6', window_a=0.5, extra=None):
    begin_light(c, ambient)
    x, y, w, h = WINDOW
    pool(c, x + w / 2, y + h / 2, w * 1.4, h * 1.2, mixc('#FFFFFF', '#FFD6A0', warm), window_a)
    if extra:
        extra(c)
    end_light(c)


# --- poses in bed ------------------------------------------------------------------------------------------------

LIE_HIP = (790, MATT - 34)
LIE_ROT = -68


def phone_spot(T, lift=0.0):
    """Where the phone is held over his face (world): it drifts, sags and gets re-gripped every few seconds,
    and kicks a little with each swipe of the thumb."""
    regrip = 0.0
    for k in range(int(T / 3.7) - 1, int(T / 3.7) + 1):
        t0 = 3.7 * k + 1.3 * hrand(k, 51)
        regrip += math.exp(-max(0.0, T - t0) / 0.5) * (T >= t0) * (hrand(k, 52) - 0.5) * 18
    sag = 6 * math.sin(T * 0.45)
    kick = 0.0
    for s_ in EV['swipes']:
        if 0 <= T - s_ < 0.4:
            kick += math.sin(math.pi * (T - s_) / 0.4) * 5
    return (676 + noise1(T * 0.6, 3) * 9 + regrip, 616 - lift + noise1(T * 0.5, 4) * 8 + sag - kick)


def phone_angle(T):
    """The phone tips a little as he holds it and with each swipe."""
    tip = 0.0
    for s_ in EV['swipes']:
        if 0 <= T - s_ < 0.35:
            tip -= math.sin(math.pi * (T - s_) / 0.35) * 6
    return 18 + noise1(T * 0.4, 7) * 7 + tip


def lying_pose(T, *, phone=True, face=None, swipes=None, laugh=0.0, sleepy=0.0, look_at=None):
    """Half-reclined on the pillow scrolling; the thumb flicks at each swipe."""
    swipes = EV['swipes'] if swipes is None else swipes
    hip = LIE_HIP
    p = dict(x=hip[0], y=hip[1] - laugh * 3 * abs(math.sin(T * 18)), rot=LIE_ROT, facing=1, turn=0.25,
             hb=24, kb=10, hf=30, kf=18, sb=40, eb=60, tilt=-8, breathe=breath(T, 0.22, 0.7, 1),
             eye=(0.78 - 0.3 * sleepy) * blink(T, 1, 4.0), bags=0.6, smile=0.05 + 0.5 * laugh, brow=-2,
             ly=-0.5, lx=0.3, reflect=(phone_light(T, swipes)[0], 0.85) if phone else None)
    if phone:
        last = max([s for s in swipes if T >= s], default=-10.0)
        flick = math.sin(math.pi * clamp((T - last) / 0.25)) if T >= last else 0.0
        px, py = phone_spot(T)
        p['hand_f'] = to_local(p, (px + 2, py + 30 - 6 * flick))
        p['ik_f'] = 1.0
    else:
        p.update(sf=30, ef=40)
    p['hand_b'] = to_local(p, (hip[0] - 20, hip[1] - 10))
    if face:
        p.update(face)
    return p


def lying_blanket_contour(p):
    """Top edge of the quilt over a half-reclined sleeper (chest, belly, knees, toes)."""
    x, y = p['x'], p['y']
    return [(x - 120, y - 54), (x - 60, y - 52), (x, y - 40), (x + 70, y - 46), (x + 120, y - 44), (x + 160, y - 50),
            (x + 196, MATT - 8)]


def sit_edge_pose(x, T, v, *, facing=-1, hands=None, head_up=0.0, look=0.0, face=None):
    """The old man sitting on the end of the bed, feet on the floor, hunched by how weak he is."""
    u = 1 - v
    hunch = 6 + 26 * u * u
    p = dict(x=x, y=MATT - 4, facing=facing, turn=0.3, foot_f=(46, FLOOR - 9 - (MATT - 4) - 1),
             foot_b=(30, FLOOR - 9 - (MATT - 4) - 1), ikl_f=-1.0, ikl_b=-1.0,
             lean=hunch * (1 - 0.55 * head_up), tilt=(10 + 22 * u) * (1 - head_up) - 6 * head_up,
             ly=0.6 * (1 - head_up) - 0.2 * look, lx=0.4 * look)
    p.update(old_face(v, T))
    if hands is None:
        p['hand_f'] = (44, -4)
        p['hand_b'] = (38, 2)
    else:
        p.update(hands)
    if face:
        p.update(face)
    return p


# --- the bedroom, assembled ----------------------------------------------------------------------------------------

class Room:
    """Everything that can change in the bedroom between scenes (all optional)."""

    def __init__(self, **kw):
        self.light = 'night'          # 'night' | 'dawn' | 'day' | 'rain'
        self.sky = 'night'
        self.curtain = 0.86           # how open the curtains are
        self.sway = 0.0
        self.lamp = 0.0
        self.door_open = 0.0
        self.door_light = 0.0
        self.notes_drop = None
        self.notes_fallen = None      # None: follow the story (see wall_notes)
        self.notes_checked = None
        self.books = False
        self.stand_phone = None       # (on, face_down) when the phone lies on the nightstand
        self.stand_watch = False
        self.drawer = 0.0
        self.hero = None              # fn(c, T) -> pose, draws the hero (and his quilt)
        self.old = None               # fn(c, T) -> pose, draws the old man
        self.back = None              # fn(c, T): things behind the people
        self.front = None             # fn(c, T): things in front of the people (still lit)
        self.after = None             # fn(c, T): emissive / unlit things after the light pass
        self.phone_at = None          # (x, y) of a lit phone, for the light map
        self.phone_amt = 1.0
        self.moon = 1.0
        self.ambient = None
        self.lights_extra = None
        self.old_rim = 0.0            # moonlight rim on the old man
        self.hero_rim = 0.0           # phone-light rim on the hero
        self.warm = 0.0
        self.__dict__.update(kw)


def draw_room(c, T, R):
    room_shell(c, T, R.door_open, R.door_light)
    window_glass(c, T, R.sky)
    curtains(c, T, R.curtain, R.sway)
    desk(c, T, books=R.books)
    chair(c, 250, facing=1)
    wall_notes(c, T, fallen=R.notes_fallen, drop=R.notes_drop, checked=R.notes_checked)
    nightstand(c, T, lamp=R.lamp, watch=R.stand_watch, phone_on_stand=R.stand_phone, drawer=R.drawer)
    bed_back(c)
    if R.back:
        R.back(c, T)
    if getattr(R, 'hero_last', False):
        old_pose = R.old(c, T) if R.old else None
        hero_pose = R.hero(c, T) if R.hero else None
    else:
        hero_pose = R.hero(c, T) if R.hero else None
        old_pose = R.old(c, T) if R.old else None
    if R.front:
        R.front(c, T)
    if R.light == 'night':
        night_lights(c, T, R.phone_at, R.phone_amt, R.moon, R.ambient or '#2A3150', R.lamp, R.lights_extra)
    elif R.light == 'dawn':
        day_lights(c, T, warm=R.warm, ambient=R.ambient or '#56628A', window_a=0.45 + 0.5 * R.warm,
                   extra=R.lights_extra)
    elif R.light == 'rain':
        night_lights(c, T, R.phone_at, R.phone_amt, 0.45, R.ambient or '#3A4258', R.lamp, R.lights_extra)
    else:
        day_lights(c, T, warm=R.warm, ambient=R.ambient or '#F3EEE6', extra=R.lights_extra)
    if R.old and R.old_rim > 0 and old_pose is not None:
        rim(c, lambda cc: R.old(cc, T, rim_pass=True), 4, -3, '#C9D6FF', R.old_rim, blur=1.5)
    if R.hero and R.hero_rim > 0 and hero_pose is not None:
        colr, br = phone_light(T)
        rim(c, lambda cc: R.hero(cc, T, rim_pass=True), 2, -4, colr, R.hero_rim * min(1.0, br), blur=1.5)
    if R.after:
        R.after(c, T)
    return hero_pose, old_pose


# --- more poses -----------------------------------------------------------------------------------------------------

def sit_up_pose(T, up, *, face=None, x_shift=0.0):
    """From half-reclined (up=0) to sitting up straight in bed (up=1), legs flat under the quilt, facing the foot."""
    rot = LIE_ROT * (1 - up)
    p = dict(x=LIE_HIP[0] - 104 * up + x_shift, y=LIE_HIP[1] + 14 * up, rot=rot, facing=1, turn=0.3,
             hb=90 + rot + 2, kb=6, hf=90 + rot + 6, kf=10, sb=12, eb=30, sf=18, ef=36,
             tilt=-8 * (1 - up), breathe=breath(T, 0.25, 0.8, 1), eye=blink(T, 1, 3.8))
    if face:
        p.update(face)
    return p


def sit_blanket_contour(p):
    """The quilt over legs stretched out along the bed (sitting up)."""
    x, y = p['x'], p['y']
    return [(x - 26, y - 16), (x + 40, y - 30), (x + 100, y - 28), (x + 140, y - 36), (x + 166, MATT - 6)]


def _resample(pts, n):
    out = []
    for k in range(n):
        u = k / (n - 1) * (len(pts) - 1)
        i = min(len(pts) - 2, int(u))
        f = u - i
        out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f))
    return out


def quilt_contour(p, up):
    """The quilt's top edge morphing from over a half-reclined sleeper (up=0) to over legs stretched out (up=1)."""
    a = _resample(lying_blanket_contour(p), 9)
    b = _resample(sit_blanket_contour(p), 9)
    e = up * up * (3 - 2 * up)
    return [(x0 + (x1 - x0) * e, y0 + (y1 - y0) * e) for (x0, y0), (x1, y1) in zip(a, b)]


def laptop_lap(c, p, T, open_amt=1.0):
    """A laptop on his thighs, its screen tipped toward him. Returns the screen's centre (world)."""
    x, y = p['x'], p['y']
    bx, by = x + 58, y - 30
    c.drawRRect(rrect(bx - 52, by - 7, 110, 10, 3), paint('#9BA3AE'))
    c.drawRRect(rrect(bx - 52, by - 7, 110, 10, 3), paint('outline', stroke=3))
    hx_, hy_ = bx + 56, by - 4
    al = math.radians(18 + 72 * (1 - open_amt))
    tx, ty = hx_ - 84 * math.sin(al + math.pi / 2 * (1 - open_amt) * 0) * 1.0, hy_ - 84 * math.cos(al)
    tx = hx_ - 84 * math.sin(al)
    lid = poly([(hx_, hy_), (hx_ + 7, hy_ - 3), (tx + 7, ty - 2), (tx, ty)], True)
    c.drawPath(lid, paint('#9BA3AE'))
    c.drawPath(lid, paint('outline', stroke=3))
    return ((hx_ + tx) / 2 - 6, (hy_ + ty) / 2)


def hero_desk_free(T):
    return None


# --- the bathroom ----------------------------------------------------------------------------------------------------

MIRROR = (600, 150, 760, 500)     # x, y, w, h


def bathroom_wall(c, T, dark=0.0):
    c.drawRect(skia.Rect.MakeLTRB(-600, -600, 2600, 1600), paint('#A9C2BD'))
    for gx in range(-600, 2600, 80):
        c.drawLine(gx, -600, gx, 1600, paint('#7E9894', stroke=3))
    for gy in range(-600, 1600, 80):
        c.drawLine(-600, gy, 2600, gy, paint('#7E9894', stroke=3))
    x, y, w, h = MIRROR
    # light bar
    c.drawRRect(rrect(x + 120, y - 70, w - 240, 26, 12), paint('#F4F1EA'))
    c.drawRRect(rrect(x + 120, y - 70, w - 240, 26, 12), paint('outline', stroke=4))
    # counter and basin
    c.drawRect(skia.Rect.MakeLTRB(x - 120, y + h + 30, x + w + 120, y + h + 110), paint('#E6E1D8'))
    c.drawRect(skia.Rect.MakeLTRB(x - 120, y + h + 30, x + w + 120, y + h + 110), paint('outline', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(x - 100, y + h + 110, x + w + 100, y + h + 600), paint('#C9B79F'))
    c.drawRect(skia.Rect.MakeLTRB(x - 100, y + h + 110, x + w + 100, y + h + 600), paint('outline', stroke=4))
    fx = x + w / 2
    c.drawRRect(rrect(fx - 10, y + h - 14, 20, 46, 6), paint('#B9BEC6'))
    c.drawRRect(rrect(fx - 44, y + h - 22, 60, 16, 7), paint('#B9BEC6'))
    c.drawRRect(rrect(fx - 10, y + h - 14, 20, 46, 6), paint('outline', stroke=3.5))
    c.drawRRect(rrect(fx - 44, y + h - 22, 60, 16, 7), paint('outline', stroke=3.5))
    # cup with a toothbrush
    cx = x + w - 90
    c.drawRRect(rrect(cx - 22, y + h - 30, 44, 60, 8), paint('#7FA7C9'))
    c.drawRRect(rrect(cx - 22, y + h - 30, 44, 60, 8), paint('outline', stroke=3.5))


def mirror_back(c, T, x, y, w, h):
    """What the mirror shows behind whoever stands in front of it: the bathroom door and a towel."""
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint('#93ABA7'))
    for gx in range(int(x) - 80, int(x + w) + 80, 64):
        c.drawLine(gx, y, gx, y + h, paint('#7A918D', stroke=2.5))
    for gy in range(int(y), int(y + h), 64):
        c.drawLine(x, gy, x + w, gy, paint('#7A918D', stroke=2.5))
    c.drawRect(skia.Rect.MakeLTRB(x + w - 230, y + 60, x + w - 80, y + h + 10), paint('#C9B79F'))
    c.drawRect(skia.Rect.MakeLTRB(x + w - 230, y + 60, x + w - 80, y + h + 10), paint('outline', stroke=3))
    c.drawCircle(x + w - 210, y + 300, 6, paint('#D9C27A'))
    c.drawRRect(rrect(x + 70, y + 120, 70, 160, 14), paint('#E7B9A6'))
    c.drawRRect(rrect(x + 70, y + 120, 70, 160, 14), paint('outline', stroke=3))


def back_view(c, x, y, s, look, hood=True, tremble=0.0, T=0.0):
    """The hero seen from behind, filling the foreground: shoulders in his hoodie and the back of his head."""
    jx = noise1(T * 22, 7) * tremble
    c.save()
    c.translate(x + jx, y)
    c.scale(s, s)
    sh = skia.Path()
    sh.moveTo(-150, 260)
    sh.cubicTo(-150, 120, -120, 70, -60, 62)
    sh.lineTo(60, 62)
    sh.cubicTo(120, 70, 150, 120, 150, 260)
    sh.close()
    c.drawPath(sh, paint(look.top))
    c.drawPath(sh, paint('#000000', 0.18))
    c.drawPath(sh, paint('outline', stroke=6))
    if hood:
        hd = skia.Path()
        hd.moveTo(-70, 70)
        hd.cubicTo(-60, 120, 60, 120, 70, 70)
        hd.cubicTo(40, 96, -40, 96, -70, 70)
        hd.close()
        c.drawPath(hd, paint(look.top))
        c.drawPath(hd, paint('outline', stroke=5))
    c.drawCircle(0, 0, 66, paint(look.skin))
    c.drawCircle(0, 0, 66, paint('#000000', 0.12))
    hair = skia.Path()
    hair.addArc(oval(0, -2, 70, 70), 160, 220)
    hair.cubicTo(50, 20, -50, 20, -64, 26)
    hair.close()
    c.drawPath(hair, paint(look.hair_color))
    c.drawPath(hair, paint('outline', stroke=5))
    for side in (-1, 1):
        c.drawOval(oval(side * 64, 8, 10, 16), paint(look.skin))
        c.drawOval(oval(side * 64, 8, 10, 16), paint('outline', stroke=4))
    c.drawCircle(0, 0, 66, paint('outline', stroke=6))
    c.restore()
