"""Shared characters, sets and helpers for '90 Days Left.'."""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'studio'))

import skia  # noqa: E402

from engine.core import H, W, hrand, hrange, noise1, smooth  # noqa: E402
from engine.draw import col, cone, light_pool, mixc, oval, paint, poly, rrect, text  # noqa: E402
from engine.home import (book_mountain, book_pile, calendar, desk_lamp, digital_clock, front_door,  # noqa: E402
                         light_switch, sticky, study_desk, wall_clock)
from engine.props import bed, chair, nightstand, phone, window  # noqa: E402
from engine.rig import SHADOW, Character, Look, eye_pair  # noqa: E402

# --- cast ---------------------------------------------------------------------------------------

HERO = Character(Look(), seed=1)
FATHER = Character(Look(top='#6E5A48', pants='#3B3F4A', shoes='#4A3626', hood=False, pocket=False, hair='sides',
                        hair_color='#B8B3AA', mustache='#4F4A44', shoulder_w=80, torso=104), seed=3)
SHADE = Character(SHADOW, seed=5)

SKINS = ['#EDE6D9', '#E4CBA9', '#C99A72', '#9C6B48', '#EDE6D9', '#D9B48F']
TOPS = ['#6B4F7A', '#4E7A68', '#8C5A46', '#3F5F8A', '#7A7A84', '#A67C3D', '#5B6E8C', '#7C4A5A']
HAIRS = [None, 'short', 'long', 'bun', 'spiky', 'short', None, 'long']
HAIR_COLS = ['#2E2420', '#5A3A24', '#1E1A18', '#7A5A3A', '#3A2E28']


def extra(i, scale=1.0):
    """A classmate with a varied look (deterministic by index)."""
    look = Look(skin=SKINS[i % len(SKINS)], top=TOPS[i % len(TOPS)], hood=False, pocket=False,
                hair=HAIRS[i % len(HAIRS)], hair_color=HAIR_COLS[i % len(HAIR_COLS)],
                pants=['#2B2E36', '#3B3540', '#2F3A44'][i % 3])
    return Character(look, seed=100 + i)


SEAT_DY = 108  # pelvis height above the floor when seated on a chair


def seated(x, floor_y, **kw):
    """Pose fragment for sitting on a chair facing +x, feet on the floor."""
    return dict(x=x, y=floor_y - SEAT_DY, hb=88, kb=88, hf=84, kf=84, foot_b=(50, 104), foot_f=(66, 104), **kw)


STAND_HIP = 123  # pelvis height above the floor line for a standing character


def standing(**kw):
    return dict(hb=-4, kb=3, hf=5, kf=3, **kw)


def merge(*parts, **kw):
    """Combine pose fragments left to right; later ones (and keywords) win."""
    out = {}
    for part in parts:
        out.update(part or {})
    out.update(kw)
    return out


# --- the phone and the shadow inside it ------------------------------------------------------------

def phone_eyes(openness=1.0, t=0.0, red=1.0, glitch=0.0, size=10):
    """Screen content: the shadow's red eyes looking out of the phone."""
    def draw(c, w, h):
        c.drawRect(skia.Rect.MakeWH(w, h), paint(mixc('#1C2633', '#2A0606', red)))
        if red > 0:
            light_pool(c, w / 2, h * 0.45, w, h * 0.6, 'red', 0.35 * red)
        drift = noise1(t * 0.8, 9) * 2
        eye_pair(c, w / 2 + drift, h * 0.42, size, openness, 18, a=red)
        if glitch > 0:
            for k in range(3):
                gy = (hrand(int(t * 12), k) * h)
                c.drawRect(skia.Rect.MakeLTRB(0, gy, w, gy + 2), paint('#FF6A5E', 0.5 * glitch))
    return draw


def phone_feed(t=0.0, scroll=0.0):
    """Screen content: an endless bright feed."""
    def draw(c, w, h):
        c.drawRect(skia.Rect.MakeWH(w, h), paint('#101722'))
        off = (scroll * 60) % 30
        for k in range(-1, 4):
            y = k * 30 - off
            c.drawRRect(rrect(3, y + 3, w - 6, 24, 3), paint(['#3F6E8C', '#8C4A6B', '#C9A54E', '#4E7A68'][k % 4]))
    return draw


# --- the hero's room ----------------------------------------------------------------------------------

ROOM_FLOOR = 860
DESK_X, DESK_W = 250, 520
DESK_TOP = ROOM_FLOOR - 158
CHAIR_X = 214
BED_X, BED_W = 1230, 520
BED_TOP = ROOM_FLOOR - 96
STAND_X = 1772
PILE_X = 548          # the to-study pile on the desk
MOUNTAIN_X = 980     # where the pile spills onto the floor and becomes a mountain
CAL = (296, 268)
WINDOW = (900, 250, 250, 290)

# where each TOMORROW note lands on the wall (x, y, angle)
NOTE_SPOTS = [(612, 300, -6), (700, 352, 5), (548, 404, 3), (650, 448, -4), (742, 268, 8), (520, 238, -9),
              (790, 420, -3), (590, 520, 6), (840, 300, 4), (452, 560, -7), (700, 560, 2), (880, 470, -5),
              (418, 236, 6), (760, 640, -2), (232, 300, 3), (880, 620, 7), (240, 470, -6), (620, 640, 4),
              (960, 590, -8), (380, 640, 5), (1000, 220, 3), (520, 650, -4)]


NIGHT, DAWN, NOON, DUSK = '#0E1830', '#F2A15E', '#7FB2E5', '#F08A4B'
_SKY_KEYS = [(0.0, NIGHT), (0.2, NIGHT), (0.27, DAWN), (0.36, NOON), (0.64, NOON), (0.73, DUSK), (0.82, NIGHT),
             (1.0, NIGHT)]
_LIGHT_KEYS = [(0.0, 0.0), (0.22, 0.0), (0.36, 1.0), (0.64, 1.0), (0.78, 0.0), (1.0, 0.0)]


def _interp(keys, d, mixer):
    for (d0, v0), (d1, v1) in zip(keys, keys[1:]):
        if d0 <= d <= d1:
            return mixer(v0, v1, (d - d0) / (d1 - d0) if d1 > d0 else 0.0)
    return keys[-1][1]


def sky_color(day):
    """day: time of day, 0 midnight, 0.27 dawn, 0.5 noon, 0.73 dusk (wraps)."""
    return _interp(_SKY_KEYS, day % 1.0, mixc)


def daylight_at(day):
    return _interp(_LIGHT_KEYS, day % 1.0, lambda a, b, u: a + (b - a) * u)


def his_room(c, T, *, day=0.0, lamp=1.0, pile=4, pile_sway=0.0, notes=0.0, crossed=0, drawer=0.0, glow=0.0,
             jolt=0.0, mountain=0.0, mountain_sway=0.0, red=0.0, clock_spin=None, today_note=0.0, bed_layer=True):
    """The hero's room in cross-section: desk on the left, window, bed on the right.

    day: time of day (see sky_color). notes: how many TOMORROW notes are on the wall (the fractional part
    animates the newest one slapping on). mountain: 0..1 how far the book pile has spread onto the floor."""
    fy = ROOM_FLOOR
    daylight = daylight_at(day)
    wall = mixc('#151A24', '#2A3446', 0.6 * daylight)
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, W + 400, fy), paint(wall))
    c.drawRect(skia.Rect.MakeLTRB(-400, fy - 220, W + 400, fy - 210), paint(mixc(wall, '#000000', 0.25)))
    shader = skia.GradientShader.MakeLinear(points=[(0, fy - 520), (0, fy)],
                                           colors=[col('#000000', 0.0), col('#000000', 0.32)])
    c.drawRect(skia.Rect.MakeLTRB(-400, fy - 520, W + 400, fy), paint('#000000', shader=shader))
    c.drawRect(skia.Rect.MakeLTRB(-400, fy, W + 400, H + 400), paint('#10131A'))
    c.drawLine(-400, fy, W + 400, fy, paint('#2A2F3B', stroke=3))

    wx, wy, ww, wh = WINDOW
    sky = sky_color(day)
    window(c, wx, wy, ww, wh, sky=sky, moon=daylight < 0.3, t=T)
    if daylight > 0:
        c.drawPath(poly([(wx, wy + wh), (wx + ww, wy + wh), (wx + ww + 300, fy), (wx + 120, fy)], True),
                   paint('#FFF1D6', 0.10 * daylight, blur=30, blend='add'))
    if clock_spin is not None:
        wall_clock(c, wx + ww / 2, 150, 44, clock_spin)

    calendar(c, CAL[0], CAL[1], 190, 220, crossed=crossed, circle_day=29)
    n_full = int(notes)
    for k in range(min(n_full, len(NOTE_SPOTS))):
        x, y, a = NOTE_SPOTS[k]
        sticky(c, x, y, 'TOMORROW', a, size=104)
    frac = notes - n_full
    if frac > 0 and n_full < len(NOTE_SPOTS):
        x, y, a = NOTE_SPOTS[n_full]
        s = 1.0 + 0.6 * (1 - smooth(0.0, 0.35, frac))  # slaps onto the wall
        sticky(c, x, y, 'TOMORROW', a + 10 * (1 - smooth(0.0, 0.35, frac)), size=104, a=smooth(0.0, 0.08, frac),
               scale=s)
    if today_note > 0:
        sticky(c, 640, 360, 'TODAY.', -3, size=130, color='#F6D654', a=today_note)

    # bed and nightstand
    if bed_layer:
        bed(c, BED_X, fy, BED_W, blanket='#4B5A7A', pillow='#D8D2C6', height=96)
    nightstand(c, STAND_X, fy, lamp_on=0.0)

    # the desk, its lamp, the pile of books and the mountain they become
    # the mountain sits behind the desk, so the drawer stays in view
    if mountain > 0:
        book_mountain(c, MOUNTAIN_X, fy, 120 + 640 * mountain, 220 + 420 * mountain, seed=5, sway=mountain_sway)
    chair(c, CHAIR_X, fy, 1, '#3B3E46')
    d = study_desk(c, DESK_X, fy, DESK_W, drawer=drawer, glow=glow, jolt=jolt, lamp=None, t=T)
    top_y = book_pile(c, PILE_X, d['top'], pile, seed=9, sway=pile_sway) if pile > 0 else d['top']
    tip = desk_lamp(c, DESK_X + DESK_W - 60, d['top'], on=lamp, facing=-1)
    if red > 0:
        light_pool(c, W / 2, fy - 260, 1300, 600, 'red', 0.10 * red)
    return dict(desk=d, pile_top=top_y, lamp_tip=tip, bed_top=fy - 96)


def blanket(c, x0, x1, top, wave=0.0, sink=0.0, t=0.0, color='#4B5A7A', swirl=0.0):
    """The blanket surface over a lying or sinking body. wave/swirl turn it into quicksand."""
    path = skia.Path()
    n = 28
    pts = []
    for k in range(n + 1):
        u = k / n
        x = x0 + (x1 - x0) * u
        bump = math.sin(u * math.pi) * 18
        ripple = wave * (math.sin(u * 14 - t * 5) * 7 + math.sin(u * 6 + t * 3.1) * 6)
        pts.append((x, top - bump + ripple + sink * 10))
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.lineTo(x1, top + 70)
    path.lineTo(x0, top + 70)
    path.close()
    c.drawPath(path, paint(color))
    if swirl > 0:
        c.save()
        c.clipPath(path, doAntiAlias=True)
        for k in range(7):
            cx = x0 + (x1 - x0) * hrange(0.1, 0.9, k, 4)
            cy = top + 26 + hrange(-6, 18, k, 5)
            r = hrange(14, 40, k, 6)
            arc = skia.Path()
            arc.addArc(oval(cx, cy, r, r * 0.4), (t * 140 + k * 60) % 360, 220)
            c.drawPath(arc, paint('#2A3248', 0.7 * swirl, stroke=4))
        c.restore()
    c.drawPath(path, paint('outline', stroke=4))
    return pts


def lying_head_pose(**kw):
    base = dict(turn=-0.25, eyes='tired', bags=1, smile=-0.25, brow=-12, lx=-0.7, ly=0.2)
    base.update(kw)
    return base


# --- the hallway at 5 AM ---------------------------------------------------------------------------

HALL_FLOOR = 880
SON_DOOR = (180, 200)        # x, width
FRONT_DOOR = (1460, 190)     # x, width
STOOL_X = 1260


def hallway(c, T, *, dawn=0.0, bulb=1.0, son_door=0.0, son_light=0.0, front_open=0.0, outside=None, sun=0.0,
            son_leaf=True):
    """Narrow hallway: the son's door on the left, a stool, the front door on the right."""
    fy = HALL_FLOOR
    wall = mixc('#141A28', '#3A2A22', sun * 0.6)
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, W + 400, fy), paint(wall))
    c.drawRect(skia.Rect.MakeLTRB(-400, fy, W + 400, H + 400), paint('#0E1118'))
    c.drawLine(-400, fy, W + 400, fy, paint('#283042', stroke=3))
    c.drawRect(skia.Rect.MakeLTRB(-400, fy - 40, W + 400, fy - 30), paint('#000000', 0.25))
    # small high window: blue before dawn, gold at sunrise
    wx, wy = 820, 230
    sky = mixc(mixc('#0B1226', '#3B5A8C', dawn), '#F2A65A', sun)
    window(c, wx, wy, 170, 150, sky=sky, moon=False, t=T)
    c.drawPath(poly([(wx, wy + 150), (wx + 170, wy + 150), (wx + 330, fy), (wx + 90, fy)], True),
               paint(mixc('#9DB7FF', '#FFC37A', sun), 0.06 + 0.05 * dawn + 0.12 * sun, blur=30, blend='add'))
    # the son's door, a line of lamplight under it when he's studying
    sx, sw = SON_DOOR
    front_door(c, sx, fy, sw, 370, open_amt=son_door, outside='#2A2116' if son_light else '#07080B',
               light=son_light, light_color='#FFC37A', hinge='right', part='all' if son_leaf else 'back')
    if son_light > 0 and son_door < 0.05:
        c.drawRect(skia.Rect.MakeLTRB(sx + 6, fy - 4, sx + sw - 6, fy), paint('warm', 0.9 * son_light))
        light_pool(c, sx + sw / 2, fy, sw * 0.9, 40, 'warm', 0.35 * son_light)
    # coat hooks, the switch, a ceiling bulb on a cord
    for k in range(3):
        c.drawCircle(1000 + k * 46, 470, 6, paint('#8A8478'))
    c.drawPath(poly([(1040, 470), (1080, 470), (1100, 610), (1020, 610)], True), paint('#4A3A2E'))
    c.drawPath(poly([(1040, 470), (1080, 470), (1100, 610), (1020, 610)], True), paint('outline', stroke=3))
    light_switch(c, 1420, 560, on=bulb > 0.5)
    bx, by = 1080, 150
    c.drawLine(bx, -60, bx, by, paint('#2B2B30', stroke=3))
    if bulb > 0:
        cone(c, (bx, by + 10), 20, fy, 420, 'warm', 0.10 * bulb, soft=40)
        light_pool(c, bx, by + 10, 300, 260, 'warm', 0.28 * bulb)
        light_pool(c, bx, fy, 520, 90, 'warm', 0.22 * bulb)
    c.drawCircle(bx, by + 12, 14, paint(mixc('#5A5A60', '#FFE7B0', bulb)))
    c.drawCircle(bx, by + 12, 14, paint('outline', stroke=3))
    fx, fw = FRONT_DOOR
    out = outside or mixc(mixc('#0B1226', '#2E4A7A', dawn), '#F28C3A', sun)
    front_door(c, fx, fy, fw, 380, open_amt=front_open, outside=out, light=1.0,
               light_color=mixc('#9DB7FF', '#FFC37A', sun))
    return dict(floor=fy)
