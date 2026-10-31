"""Shared characters, the gym, the January crowd and their workouts, the shadow's tap and the wall of photos."""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'studio'))

import skia  # noqa: E402

from engine.core import H, W, clamp, hrand, hrange, noise1, smooth  # noqa: E402
from engine.draw import circle, col, cone, light_pool, mixc, oval, paint, poly, rrect, text  # noqa: E402
from engine.fx import FIREWORK_COLORS, dissolve, falling_leaves, firework, rainfall, snowfall  # noqa: E402
from engine.gym import (banner, barbell, bench, ceiling_light, dumbbell, dumbbell_rack, exit_sign,  # noqa: E402
                        jump_rope, mirror, photo_frame, plate_tree, power_rack, radio, rubber_floor, towel, treadmill,
                        water_bottle)
from engine.home import front_door, wall_clock  # noqa: E402
from engine.props import phone, street_lamp, string_lights  # noqa: E402
from engine.rig import SHADOW, Character, Look, blink, idle, run, solve, to_local, walk  # noqa: E402

# --- cast -----------------------------------------------------------------------------------------------

YELLOW = '#E8B93A'
INK = '#2B2416'


def resolution_look(**kw):
    """The January uniform: a bright NEW ME t-shirt, shorts and brand-new trainers."""
    base = dict(top=YELLOW, hood=False, pocket=False, sleeve='short', shorts='#4A4F5C', shoes='#ECE9E2',
                print_text='NEW\nME', print_color=INK)
    base.update(kw)
    return Look(**base)


HERO_TEAL = '#2F7F8C'   # his shorts: the one thing that tells him apart in a crowd of yellow shirts
HERO_JAN = Character(resolution_look(shorts=HERO_TEAL), seed=1)


def hero_fit(u=1.0):
    """The hero after he stays: a plain dark tee; u 0..1 is how far into the year (broader, stronger)."""
    return Character(Look(top='#46505F', hood=False, pocket=False, sleeve='short', shorts=HERO_TEAL,
                          shoes='#ECE9E2', shoulder_w=77 + 10 * u, arm_w=15 + 2.6 * u, leg_w=18 + 1.4 * u,
                          hip_w=64), seed=1)


HERO_FIT = hero_fit(1.0)
OLD_LOOK = Look(skin='#A8754E', top='#8A8F99', hood=False, pocket=False, sleeve='none', shorts='#2B2E36',
                shoes='#D9D3C4', hair='sides', hair_color='#ECE8E0', beard='#ECE8E0', headband='#3F6E8C',
                brow_color='#F2EFE8', shoulder_w=84, arm_w=17)
OLD = Character(OLD_LOOK, seed=3)
NEWBIE = Character(resolution_look(skin='#E4CBA9', hair='short', hair_color='#5A3A24', shorts='#5B6070',
                                   shoulder_w=78, torso=94), seed=4)
SHADE = Character(SHADOW, seed=5)

SKINS = ['#EDE6D9', '#E4CBA9', '#C99A72', '#9C6B48', '#D9B48F', '#EDE6D9', '#B07A52', '#E4CBA9', '#C99A72',
         '#EDE6D9', '#9C6B48', '#D9B48F']
HAIRS = ['short', 'long', 'spiky', 'bun', 'spiky', 'short', 'long', 'short', 'short', 'bun', 'long', 'spiky']
HAIR_COLS = ['#2E2420', '#5A3A24', '#1E1A18', '#7A5A3A', '#3A2E28', '#B5893F']
SHORTS = ['#4A4F5C', '#2F3A44', '#3B3540', '#5B4A6B']


def extra(i, **kw):
    look = resolution_look(skin=SKINS[i % len(SKINS)], hair=HAIRS[i % len(HAIRS)],
                           hair_color=HAIR_COLS[i % len(HAIR_COLS)], shorts=SHORTS[i % len(SHORTS)], **kw)
    return Character(look, seed=100 + i)


# --- the gym (cross-section, back wall facing us) ----------------------------------------------------------------

WALL_FLOOR = 800          # where the back wall meets the floor
ROW_B, ROW_F = 836, 952   # feet of the back and front rows
SB, SF = 0.74, 0.9        # their scales
STAND_HIP = 123           # pelvis height above the feet at scale 1
DOOR = (56, 196, 420)     # x, width, height
PHOTOS_X, PHOTOS_Y, PHOTO_GAP = 330, 318, 84
PHOTO_W, PHOTO_H = 64, 36
MIRROR_X = (660, 1010)
WINDOWS = [(1096, 270), (1286, 270), (1476, 270)]
WIN_W, WIN_H = 160, 310
BANNER = (1056, 1666, 160)
CLOCK = (836, 196)
LIGHTS = [250, 690, 1130, 1570]
CORNER_X = 1806           # the old man's corner
TREADS = [1166, 1356, 1546]
RACK_X, BENCH_X = 470, 1150

# the camera framing of the gym's New Year photo (centre, zoom) and the photo's aspect
PHOTO_CAM = (1430, 690, 2.0)


def gym_room(c, T, *, lights=(1, 1, 1, 1), flicker=None, banner_loose=0.0, banner_a=1.0, outside='snow_night',
             corner=1.0, door=0.0, door_out=None, photos=5, string=0.0, hour=6.0, new_photo=None, exit_glow=1.0,
             bulb_pools=True):
    """The back wall, windows, banner, photos, mirror, door, ceiling lights and floor."""
    fy = WALL_FLOOR
    wall_top, wall_bot = '#1D2330', '#141821'
    sh = skia.GradientShader.MakeLinear(points=[(0, 0), (0, fy)], colors=[col(wall_top), col(wall_bot)])
    c.drawRect(skia.Rect.MakeLTRB(-600, -400, W + 600, fy), paint('#000000', shader=sh))
    c.drawRect(skia.Rect.MakeLTRB(-600, 560, W + 600, 588), paint('#22404A'))
    c.drawRect(skia.Rect.MakeLTRB(-600, 588, W + 600, 594), paint('#000000', 0.25))
    for k in range(-3, 26):
        c.drawLine(k * 96, 0, k * 96, 560, paint('#000000', 0.08, stroke=2))
    # ceiling band
    c.drawRect(skia.Rect.MakeLTRB(-600, -400, W + 600, 70), paint('#0D1016'))
    c.drawLine(-600, 70, W + 600, 70, paint('#262B36', stroke=3))

    # windows onto the street
    for wx, wy in WINDOWS:
        frame = rrect(wx, wy, WIN_W, WIN_H, 4)
        c.save()
        c.clipRRect(frame, doAntiAlias=True)
        outside_view(c, wx, wy, WIN_W, WIN_H, T, outside, seed=wx)
        c.drawLine(wx + 20, wy + WIN_H - 30, wx + 120, wy + 30, paint('#FFFFFF', 0.06, stroke=18))
        c.restore()
        c.drawRRect(frame, paint('#2E323C', stroke=12))
        c.drawLine(wx + WIN_W / 2, wy, wx + WIN_W / 2, wy + WIN_H, paint('#2E323C', stroke=8))
        c.drawRRect(frame, paint('outline', stroke=3.5))
        c.drawRect(skia.Rect.MakeLTRB(wx - 12, wy + WIN_H, wx + WIN_W + 12, wy + WIN_H + 12), paint('#2E323C'))
        if string > 0:
            string_lights(c, wx - 6, wx + WIN_W + 6, wy + 4, sag=22, n=7, t=T + wx, a=string)
    if banner_a > 0:
        banner(c, BANNER[0], BANNER[1], BANNER[2], 78, loose=banner_loose, t=T, a=banner_a)

    # the photo wall by the door
    for k in range(photos):
        px = PHOTOS_X + k * PHOTO_GAP
        photo_frame(c, px, PHOTOS_Y, PHOTO_W, PHOTO_H, photo_content(1986 + 10 * k), label=str(1986 + 10 * k),
                    tilt=[-2, 1, -1, 2, 0][k])
    if new_photo is not None:
        x, y, s, rot = new_photo
        photo_frame(c, x, y, PHOTO_W * s, PHOTO_H * s, photo_content(2027), label='2027', tilt=rot)
    mirror(c, MIRROR_X[0], MIRROR_X[1], 380, 760)
    wall_clock(c, *CLOCK, 46, hour)

    # the entrance and its EXIT sign
    dx, dw, dh = DOOR
    front_door(c, dx, fy, dw, dh, open_amt=door, outside=door_out or '#0B1424', light=1.0,
               light_color='#9DB7FF', hinge='left')
    exit_sign(c, dx + dw / 2, fy - dh - 44, glow=exit_glow)

    # the corner: a shelf with a radio, a hook, a lamp of its own
    cx = CORNER_X
    c.drawRect(skia.Rect.MakeLTRB(cx - 70, 470, cx + 70, 482), paint('#4A3A2E'))
    c.drawRect(skia.Rect.MakeLTRB(cx - 70, 470, cx + 70, 482), paint('outline', stroke=3))
    radio(c, cx - 20, 470, on=corner)

    # the floor
    rubber_floor(c, -600, W + 600, fy, H + 400)
    # ceiling lights
    levels = []
    for k, lx in enumerate(LIGHTS):
        on = lights[k] if k < len(lights) else 1
        fl = flicker[k] if flicker and k < len(flicker) else 0.0
        levels.append(ceiling_light(c, lx, 96, ROW_F + 20, on=on, t=T, flicker=fl, seed=k, cone_a=0.06,
                                    pool_a=0.14 if bulb_pools else 0.0))
    corner_lamp(c, cx, ROW_B, corner)
    return levels


def corner_lamp(c, x, floor_y, on=1.0):
    """The old cage lamp over the corner: warm, where every other light is cold."""
    c.drawLine(x, 70, x, 150, paint('#2B2B30', stroke=3))
    if on > 0:
        cone(c, (x, 162), 16, floor_y + 10, 230, 'warm', 0.10 * on, soft=40)
        light_pool(c, x, floor_y, 260, 60, 'warm', 0.22 * on)
        light_pool(c, x, 170, 120, 100, 'warm', 0.3 * on)
    cage = poly([(x - 22, 150), (x + 22, 150), (x + 30, 176), (x - 30, 176)], True)
    c.drawPath(cage, paint('#3A3D45'))
    c.drawCircle(x, 172, 9, paint(mixc('#5A5A60', '#FFE7B0', on)))
    c.drawPath(cage, paint('outline', stroke=3))


def outside_view(c, x, y, w, h, T, kind, seed=0):
    """What the windows show: the street in snow, rain, autumn or fireworks (drawn inside the window clip)."""
    skies = {'snow_night': ('#0B1424', '#1B2B45'), 'snow_dawn': ('#16243C', '#4A6390'),
             'rain': ('#2B3646', '#4E5C6E'), 'autumn': ('#5A3A2A', '#D88A48'), 'summer': ('#3F8FCB', '#A8D8F0'),
             'spring': ('#5C8FB8', '#BFDDEB'), 'fireworks': ('#070B16', '#15203A'), 'fog': ('#3B4250', '#6B7380')}
    top, bot = skies.get(kind, skies['snow_night'])
    sh = skia.GradientShader.MakeLinear(points=[(x, y), (x, y + h)], colors=[col(top), col(bot)])
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint('#000000', shader=sh))
    night = kind in ('snow_night', 'fireworks', 'snow_dawn', 'rain', 'fog')
    # the buildings across the street
    for k in range(4):
        bx = x - 20 + k * 52 + hrange(-10, 10, k, seed)
        bh = hrange(90, 170, k, seed, 1)
        c.drawRect(skia.Rect.MakeLTRB(bx, y + h - bh, bx + 46, y + h), paint('#0A0E18' if night else '#5B6170'))
        for r in range(6):
            for q in range(2):
                if hrand(k, r, q, seed) > 0.55:
                    c.drawRect(skia.Rect.MakeXYWH(bx + 8 + q * 18, y + h - bh + 12 + r * 24, 10, 12),
                               paint('#E9B85A', 0.5 if night else 0.15))
    ground = '#DDE6F2' if kind.startswith('snow') or kind == 'fireworks' else '#2A2E36'
    c.drawRect(skia.Rect.MakeLTRB(x, y + h - 26, x + w, y + h), paint(ground, 0.9 if night else 1.0))
    if night:
        light_pool(c, x + w * 0.5, y + h - 30, w * 0.6, 60, 'warm', 0.25)
    if kind.startswith('snow') or kind == 'fireworks':
        snowfall(c, x, y, x + w, y + h, T, n=26, seed=seed, wind=18, size=(1.4, 3.4))
    elif kind == 'rain':
        rainfall(c, x, y, x + w, y + h, T, n=40, seed=seed, length=26, a=0.45)
    elif kind == 'autumn':
        falling_leaves(c, x, y, x + w, y + h, T, n=7, seed=seed, size=7)
    elif kind == 'spring':
        falling_leaves(c, x, y, x + w, y + h, T, n=8, seed=seed, size=5, colors=('#F6B8C8', '#FFD7E0'),
                       petals=True)
    if kind == 'fireworks':
        for k in range(5):
            t0 = 122.0 + k * 0.45 + hrand(k, seed) * 0.3
            for rep in range(4):
                firework(c, x + hrange(20, w - 20, k, rep, seed), y + hrange(40, 140, k, rep, seed, 2), T,
                         t0 + rep * 2.3, FIREWORK_COLORS[(k + rep + seed) % 6], n=26, radius=60, seed=k + rep,
                         rocket=0.4, size=0.6)


def gym_props_back(c, T, *, treads=(0.0, 0.0, 0.0), screens=(0.0, 0.0, 0.0), corner=True, rack_missing=()):
    """Equipment against the back wall, behind the back row."""
    dumbbell_rack(c, 500, ROW_B - 10, w=300, missing=rack_missing, scale=SB)
    for k, tx in enumerate(TREADS):
        treadmill(c, tx, ROW_B, t=T, belt=treads[k], screen=screens[k], scale=SB)
    if corner:
        dumbbell_rack(c, CORNER_X + 40, ROW_B - 6, w=150, scale=SB * 0.9, missing=((1, 0), (1, 1), (0, 0)))


def gym_props_front(c, T, *, rack=True, bench_on=True, plates=True):
    if rack:
        power_rack(c, RACK_X, ROW_F, scale=SF * 0.92)
    if bench_on:
        bench(c, BENCH_X, ROW_F, length=300 * SF, height=100 * SF, uprights=-1)
    if plates:
        plate_tree(c, 1990, ROW_F, scale=SF)


def treadmill_top(x):
    return ROW_B - 42 * SB


# --- workouts: pose fragments for the crowd -------------------------------------------------------------

def curl_pose(T, seed=0, speed=1.0, heavy=False):
    """Alternating dumbbell curls; returns arm angles (forearm up = big elbow angle)."""
    ph = (T * 0.62 * speed + hrand(seed, 3)) % 1.0
    f = math.sin(min(1.0, ph / 0.5) * math.pi) if ph < 0.5 else 0.0
    b = math.sin(min(1.0, (ph - 0.5) / 0.5) * math.pi) if ph >= 0.5 else 0.0
    sh = 4 if heavy else 0
    return dict(sf=-4 + sh * f, ef=12 + 128 * f, sb=6, eb=12 + 128 * b, lean=-2 - 3 * (f + b) * (1 if heavy else 0.4))


def stand(x, feet_y, scale, facing=1, **kw):
    pose = dict(x=x, y=feet_y - STAND_HIP * scale, scale=scale, facing=facing, hb=-4, kb=3, hf=5, kf=3)
    pose.update(kw)
    return pose


def dumbbells_layers(size=0.9, back=True, front=True):
    layers = {}
    if back:
        layers['behind'] = lambda cc, j: dumbbell(cc, *j['hand_b'], size=size)
    if front:
        layers['front'] = lambda cc, j: dumbbell(cc, *j['hand_f'], size=size)
    return layers


@dataclass
class Member:
    key: str
    who: Character
    x: float
    row: str          # 'b' (back) or 'f' (front)
    act: str          # curl | tread | rope | squat | queue | bench | stretch | pushup | selfie
    facing: int = 1
    gone: float = 1e9           # absent from this time on (quit off screen)
    tap: float | None = None    # the shadow taps them at this time; they go to smoke right after

    @property
    def feet(self):
        return ROW_B if self.row == 'b' else ROW_F

    @property
    def scale(self):
        return SB if self.row == 'b' else SF


DAYS = [20.0, 24.0, 28.0, 32.0, 36.0, 40.0]
CROWD = [
    Member('runner1', extra(0), TREADS[0] - 14, 'b', 'tread', 1, tap=DAYS[0] + 1.0),
    Member('rope', extra(1), 214, 'f', 'rope', 1, gone=DAYS[1]),
    Member('curl_b1', extra(2), 400, 'b', 'curl', 1, tap=DAYS[1] + 1.0),
    Member('runner2', extra(3), TREADS[1] - 14, 'b', 'tread', 1, gone=DAYS[2]),
    Member('selfie', extra(4), 800, 'b', 'selfie', 1, tap=DAYS[2] + 1.0),
    Member('stretch', extra(5), 660, 'f', 'stretch', -1, gone=DAYS[3]),
    Member('squat', extra(6), RACK_X, 'f', 'squat', 1, tap=DAYS[3] + 1.0),
    Member('curl_b2', extra(7), 590, 'b', 'curl', -1, gone=DAYS[4]),
    Member('queue', extra(8), 1330, 'f', 'queue', -1, tap=DAYS[4] + 1.0),
    Member('bench', extra(9), BENCH_X, 'f', 'bench', 1, tap=DAYS[4] + 1.0),
    Member('runner3', extra(10), TREADS[2] - 14, 'b', 'tread', 1, gone=DAYS[5]),
    Member('pushup', extra(11), 1650, 'f', 'pushup', -1, tap=DAYS[5] + 1.0),
]
QUIT_DUR = 1.7


def member_pose(m, T, frozen=None):
    """The member's pose while working out; frozen: a time after which the motion winds down to a stop."""
    if frozen is not None and T > frozen:
        T = frozen + (1 - math.exp(-(T - frozen) * 4)) / 4
    s, x, fy = m.scale, m.x, m.feet
    seed = hash(m.key) % 97
    face = dict(turn=0.35, eye=blink(T, seed), smile=0.25, brow=2)
    layers = None
    if m.act == 'curl':
        pose = stand(x, fy, s, m.facing, **curl_pose(T, seed), **face)
        layers = dumbbells_layers()
    elif m.act == 'tread':
        r = run(T, 1.15, 30)
        dy = r.pop('dy')
        pose = dict(x=x, y=treadmill_top(x) - STAND_HIP * s + dy * s * 0.6, scale=s, facing=m.facing, **r, **face)
        pose['lean'] = 6
    elif m.act == 'rope':
        hop = abs(math.sin(T * math.pi * 2.3)) * 16
        pose = stand(x, fy - hop, s, m.facing, sb=18, eb=40, sf=-14, ef=40, **face)
        pose['hand_b'] = (-26, 30)
        pose['hand_f'] = (34, 26)
        pose['kb'] = pose['kf'] = 8 + 10 * (1 - hop / 16)

        def rope_layer(cc, j, T=T):
            jump_rope(cc, j['hand_b'], j['hand_f'], (T * 2.3) % 1.0, low=0)
        layers = {'front': rope_layer}
    elif m.act == 'squat':
        d = 0.5 - 0.5 * math.cos(T * 1.8)
        hip_y = fy - STAND_HIP * s + 62 * s * d
        pose = dict(x=x - 10 * s * d, y=hip_y, scale=s, facing=m.facing, lean=8 + 26 * d, **face)
        pose['foot_b'] = (-6, (fy - hip_y) / s - 6)
        pose['foot_f'] = (14, (fy - hip_y) / s - 6)
        pose['hand_b'] = (-30, -80)
        pose['hand_f'] = (34, -84)
        pose['tilt'] = -10 * d
        pose['brow'] = -6 * d
        pose['smile'] = 0.1 - 0.3 * d

        def bar(cc, j):
            n = j['neck']
            barbell(cc, n[0] - 26, n[1] + 10, plates=2, length=170, plate_r=40, depth=(0.12, -0.16))
        layers = {'mid': bar}
    elif m.act == 'queue':
        pose = stand(x, fy, s, m.facing, **idle(T, seed), turn=0.4, lx=0.3, ly=0.8, eye=blink(T, seed),
                     smile=0.1, brow=0)
        pose['hand_f'] = (40, -40)
        pose['hand_b'] = (24, -36)

        def phone_layer(cc, j):
            phone(cc, j['hand_f'][0] + 6, j['hand_f'][1] - 18, -20, 0.55, glow=0.6)
        layers = {'front': phone_layer}
    elif m.act == 'bench':
        return bench_press_pose(x, fy, s, T, seed, m.facing, face)
    elif m.act == 'stretch':
        b = 0.5 + 0.5 * math.sin(T * 2.0 + seed)
        pose = stand(x, fy, s, m.facing, lean=64 + 18 * b, sb=-4, eb=0, sf=4, ef=0, turn=0.3, eyes='closed',
                     smile=0.0, brow=-2)
    elif m.act == 'pushup':
        return pushup_pose(x, fy, s, T, seed, m.facing, face)
    elif m.act == 'selfie':
        flex = 0.5 + 0.5 * math.sin(T * 1.4 + seed)
        pose = stand(x, fy, s, m.facing, sb=-92, eb=-70 - 20 * flex, turn=0.45, eyes='happy',
                     smile=0.6, lx=0.6, ly=-0.2, lean=-4)
        pose['hand_f'] = (64, -196)

        def selfie_phone(cc, j):
            phone(cc, j['hand_f'][0] + 4, j['hand_f'][1] - 14, -8, 0.6, glow=0.8)
        layers = {'front': selfie_phone}
    else:
        pose = stand(x, fy, s, m.facing, **face)
    return pose, layers


def bench_press_pose(x, fy, s, T, seed=0, facing=1, face=None, press=None, plates=2, spot=None):
    """Lying on the bench at x (head toward the uprights on the left), pressing a bar. press 0..1 overrides
    the bar height (1 = arms locked out)."""
    top = fy - 100 * s
    hip = (x + 46 * s, top - 13 * s)
    p = press if press is not None else 0.5 - 0.5 * math.cos(T * 1.9 + seed)
    pose = dict(turn=0.3, eye=1.0)
    pose.update(face or {})
    pose.update(x=hip[0], y=hip[1], rot=-90, facing=1, scale=s)
    chest_x = hip[0] - 74 * s
    bar = (chest_x, top - (40 + 76 * p) * s)
    pose['hand_b'] = to_local(pose, (bar[0] + 6 * s, bar[1] + 4 * s))
    pose['hand_f'] = to_local(pose, (bar[0] - 6 * s, bar[1] + 6 * s))
    pose['ik_b'] = pose['ik_f'] = -1.0
    pose['foot_b'] = to_local(pose, (hip[0] + 80 * s, fy - 4))
    pose['foot_f'] = to_local(pose, (hip[0] + 100 * s, fy - 4))
    pose['ikl_b'] = pose['ikl_f'] = 1.0

    def far(cc, j):
        cc.save()
        cc.concat(_inverse_of(pose))
        barbell(cc, *bar, plates=plates, length=150 * s, plate_r=46 * s, part='far', depth=(0.1, -0.3))
        cc.restore()

    def near(cc, j):
        cc.save()
        cc.concat(_inverse_of(pose))
        barbell(cc, *bar, plates=plates, length=150 * s, plate_r=46 * s, part='near', depth=(0.1, -0.3))
        cc.restore()
    pose['_bar'] = bar
    return pose, {'behind': far, 'mid': near}


def _inverse_of(pose):
    """Matrix that undoes the character's own transform, so a layer can draw in world coordinates."""
    m = skia.Matrix()
    m.preTranslate(pose['x'], pose['y'])
    if pose.get('rot'):
        m.preRotate(pose['rot'])
    s = pose.get('scale', 1.0)
    m.preScale(s * pose.get('facing', 1), s)
    inv = skia.Matrix()
    m.invert(inv)
    return inv


def pushup_pose(x, fy, s, T, seed=0, facing=-1, face=None):
    d = 0.5 - 0.5 * math.cos(T * 2.4 + seed)
    theta = 21 + 12 * (1 - d)
    feet = (x + 120 * s * (-facing), fy - 6)
    ang = math.radians(theta)
    hip = (feet[0] + facing * math.cos(ang) * 112 * s, feet[1] - math.sin(ang) * 112 * s)
    pose = dict(turn=0.2)
    pose.update(face or {})
    pose.update(x=hip[0], y=hip[1], rot=(-90 + theta) * (-facing), facing=facing, scale=s, hb=0, kb=0, hf=0, kf=0)
    shoulder_world = (hip[0] + facing * 82 * s * math.cos(ang), hip[1] - 82 * s * math.sin(ang))
    pose['hand_b'] = to_local(pose, (shoulder_world[0] + 6 * s * facing, fy - 4))
    pose['hand_f'] = to_local(pose, (shoulder_world[0] - 6 * s * facing, fy - 4))
    pose['ik_b'] = pose['ik_f'] = 1.0 if facing < 0 else -1.0
    pose['eyes'] = 'closed' if d > 0.6 else 'dot'
    pose['brow'] = -8
    return pose, None


def member_box(m, pose):
    s = m.scale
    if m.act in ('bench', 'pushup'):
        return (m.x - 230 * s, m.feet - 190 * s, m.x + 200 * s, m.feet + 6)
    return (m.x - 110 * s, m.feet - 370 * s, m.x + 110 * s, m.feet + 6)


def draw_member(c, m, T, extra_face=None):
    """Draw a crowd member at T (going to smoke after their tap)."""
    if T >= m.gone:
        return None
    frozen = m.tap if m.tap is not None else None
    pose, layers = member_pose(m, T, frozen)
    if m.tap is not None and T > m.tap:
        k = smooth(m.tap + 0.1, m.tap + 0.5, T)
        pose.update(eyes='tired' if pose.get('eyes') != 'closed' else 'closed', smile=0.15 - 0.45 * k,
                    brow=-4 - 10 * k, ly=0.3 * k)
    if extra_face:
        pose.update(extra_face)
    pose.pop('_bar', None)
    if m.tap is not None and T > m.tap + 0.1:
        t0 = m.tap + 0.5
        if T > t0 + QUIT_DUR + 2.0:
            return None
        dissolve(c, lambda cc: m.who.draw(cc, pose, layers, t=T), member_box(m, pose), T, t0, QUIT_DUR,
                 seed=hash(m.key) % 50)
        return pose
    m.who.draw(c, pose, layers, t=T)
    return pose


def present(m, T):
    if T >= m.gone:
        return False
    if m.tap is not None and T > m.tap + 0.5 + QUIT_DUR:
        return False
    return True


# --- what quitters leave behind -----------------------------------------------------------------------------

def dropped(c, T):
    """Things left on the floor by people who quit (each drops when its owner goes to smoke)."""
    for key, kind, x, fy, color in (('curl_b1', 'dumbbell', 446, ROW_B, None),
                                    ('selfie', 'phone', 850, ROW_B, None),
                                    ('queue', 'bottle', 1300, ROW_F, '#3F8FD0'),
                                    ('pushup', 'towel', 1590, ROW_F, '#D9D3C4'),
                                    ('rope', 'rope', 230, ROW_F, None)):
        m = next(mm for mm in CROWD if mm.key == key)
        t_drop = (m.tap + 0.5 + 0.4) if m.tap is not None else m.gone - 3.0
        if T < t_drop:
            continue
        u = min(1.0, (T - t_drop) / 0.35)
        start = fy - (150 if m.row == 'b' else 180) * m.scale
        y = start + (fy - start) * u * u
        bounce = 10 * math.sin(min(1.0, (T - t_drop - 0.35) / 0.3) * math.pi) if T > t_drop + 0.35 else 0
        roll = 40 * smooth(t_drop + 0.35, t_drop + 1.2, T)
        if kind == 'dumbbell':
            dumbbell(c, x + roll, y - 18 * m.scale - bounce, size=0.8 * m.scale / SB, angle=-26 + roll * 4)
        elif kind == 'phone':
            phone(c, x, y - 4 - bounce, 80 * u, 0.5, glow=0.4, face_down=False)
        elif kind == 'bottle':
            water_bottle(c, x + roll * 0.6, y - bounce, '#3F8FD0', scale=0.8, angle=90 * u)
        elif kind == 'towel':
            c.drawOval(oval(x, fy - 6, 46, 9), paint('#D9D3C4'))
            c.drawOval(oval(x, fy - 6, 46, 9), paint('outline', stroke=3))
        elif kind == 'rope':
            path = skia.Path()
            path.moveTo(x - 80, fy - 4)
            path.cubicTo(x - 30, fy - 20, x + 10, fy + 4, x + 70, fy - 6)
            c.drawPath(path, paint('outline', stroke=4))
            c.drawLine(x - 80, fy - 4, x - 96, fy - 10, paint('#C8463D', stroke=7))
            c.drawLine(x + 70, fy - 6, x + 88, fy - 2, paint('#C8463D', stroke=7))


# --- the shadow's tap -----------------------------------------------------------------------------------------

def shade_tap(c, T, t_tap, target, feet_y, scale, side=-1, both=None, grow=1.0):
    """The shadow steps out of the dark beside someone, taps their shoulder (world point `target`) and fades.
    side: which side of the target it stands on (-1 left, +1 right). both: a second shoulder for the other hand.
    Returns the shadow's pose, or None when it isn't there."""
    rel = T - t_tap
    if rel < -1.0 or rel > 2.2:
        return None
    s = scale * grow
    appear = smooth(-1.0, -0.45, rel) * (1 - smooth(1.5, 2.2, rel))
    reach = smooth(-0.4, 0.0, rel) * (1 - smooth(0.7, 1.3, rel))
    x = target[0] + side * (78 + 20 * (1 - reach)) * s
    if both is not None:
        x = (target[0] + both[0]) / 2
    rise = (1 - smooth(-1.0, -0.4, rel)) * 40 * s
    pose = dict(x=x, y=feet_y - STAND_HIP * s + rise, scale=s, facing=-side if both is None else 1, turn=0.15,
                hb=-4, kb=3, hf=5, kf=3, lean=8 + 10 * reach, tilt=10 * reach, alpha=appear,
                eye=smooth(-0.6, -0.3, rel), brow=20, sb=6, eb=10, sf=-4, ef=12)
    if reach > 0.01:
        rest = (pose['x'] + 30 * s * pose['facing'], pose['y'] + 10 * s)
        tgt = (rest[0] + (target[0] - rest[0]) * reach, rest[1] + (target[1] - rest[1]) * reach)
        pose['hand_f'] = to_local(pose, tgt)
        if both is not None:
            tgt2 = (rest[0] + (both[0] - rest[0]) * reach, rest[1] + (both[1] - rest[1]) * reach)
            pose['hand_b'] = to_local(pose, tgt2)
    SHADE.draw(c, pose, t=T)
    return pose


def shade_hand(c, pose, T, which='f'):
    """Redraw the shadow's hand on top (so its finger lands on the shoulder in front of the victim)."""
    if pose is None or pose.get('alpha', 1) <= 0.02:
        return
    j = solve(SHADE.look, dict(_BASE_POSE(), **pose))
    hx, hy = j[f'hand_{which}']
    s = pose['scale']
    wx = pose['x'] + hx * s * pose['facing']
    wy = pose['y'] + hy * s
    a = pose.get('alpha', 1.0)
    c.drawCircle(wx, wy, 14 * s, paint('red', 0.7 * a, blur=6, blend='add'))
    c.drawCircle(wx, wy, 12 * s, paint('#040405', a))


def _BASE_POSE():
    from engine.rig import BASE_POSE
    return dict(BASE_POSE)


def shoulder_world(who, pose, side='b'):
    """World position of a character's shoulder (for the tap)."""
    j = solve(who.look, dict(_BASE_POSE(), **pose))
    sx, sy = j[f'sh_{side}']
    s = pose.get('scale', 1.0)
    rot = math.radians(pose.get('rot', 0.0))
    lx, ly = sx * s * pose.get('facing', 1), sy * s
    wx = lx * math.cos(rot) - ly * math.sin(rot)
    wy = lx * math.sin(rot) + ly * math.cos(rot)
    return (pose['x'] + wx, pose['y'] + wy)


# --- the New Year photos ---------------------------------------------------------------------------------------

# how the regular looked in each photo, and the colours of that year's crowd
ERAS = {
    1986: dict(hair='short', hair_color='#1E1A18', beard=None, mustache=None, brow='#1E1A18',
               tops=['#E85A9C', '#2FB5A8', '#F2A33A', '#8C5AC8', '#E85A9C', '#2FB5A8', '#F2D14A', '#5AC8E8'],
               grade='sepia', label='1986'),
    1996: dict(hair='short', hair_color='#3A3530', beard=None, mustache='#3A3530', brow='#3A3530',
               tops=['#6B4F9A', '#4E9A5A', '#C84A3D', '#3F5F8A', '#D9A43A', '#6B4F9A', '#4E9A5A', '#C84A3D'],
               grade='faded', label='1996'),
    2006: dict(hair='sides', hair_color='#77736C', beard='#8A867F', mustache=None, brow='#77736C',
               tops=['#6B6E78', '#2E3038', '#8C2F3A', '#5B6E8C', '#6B6E78', '#2E3038', '#3F6E5A', '#8C2F3A'],
               grade='warm', label='2006'),
    2016: dict(hair='sides', hair_color='#C9C5BD', beard='#C9C5BD', mustache=None, brow='#C9C5BD',
               tops=['#2F2F35', '#C8463D', '#3F8FD0', '#E9E6DF', '#2F2F35', '#5AA86B', '#C8463D', '#3F8FD0'],
               grade='cool', label='2016'),
    2026: dict(hair='sides', hair_color='#ECE8E0', beard='#ECE8E0', mustache=None, brow='#F2EFE8',
               tops=[YELLOW] * 8, grade=None, label='2026'),
    2027: dict(hair='sides', hair_color='#ECE8E0', beard='#ECE8E0', mustache=None, brow='#F2EFE8',
               tops=[YELLOW] * 8, grade=None, label='2027'),
}

GRADES = {
    'sepia': [0.39, 0.77, 0.19, 0, 0.06, 0.35, 0.69, 0.17, 0, 0.03, 0.27, 0.53, 0.13, 0, -0.02, 0, 0, 0, 1, 0],
    'faded': [0.8, 0.15, 0.05, 0, 0.08, 0.1, 0.75, 0.1, 0, 0.06, 0.08, 0.15, 0.62, 0, 0.08, 0, 0, 0, 1, 0],
    'warm': [0.95, 0.08, 0.0, 0, 0.04, 0.04, 0.9, 0.04, 0, 0.02, 0.0, 0.08, 0.78, 0, 0.0, 0, 0, 0, 1, 0],
    'cool': [0.92, 0.04, 0.04, 0, 0.0, 0.03, 0.95, 0.04, 0, 0.0, 0.04, 0.06, 1.0, 0, 0.02, 0, 0, 0, 1, 0],
}

# the posing group: (x, row, look index, arms)  arms: 'up' (V), 'thumbs', 'wave'
POSERS = [(1010, 'b', 0, 'up'), (1190, 'b', 1, 'thumbs'), (1372, 'b', 2, 'up'), (1550, 'b', 3, 'wave'),
          (1094, 'f', 4, 'thumbs'), (1280, 'f', 5, 'up'), (1466, 'f', 6, 'thumbs'), (1640, 'f', 7, 'up')]


def regular(year):
    e = ERAS[year]
    return Character(Look(skin='#A8754E', top='#8A8F99', hood=False, pocket=False, sleeve='none', shorts='#2B2E36',
                          shoes='#D9D3C4', hair=e['hair'], hair_color=e['hair_color'], beard=e['beard'],
                          mustache=e['mustache'], headband='#3F6E8C', brow_color=e['brow'], shoulder_w=84,
                          arm_w=17), seed=3)


def poser_pose(x, row, arms, T, k, pop=1.0):
    s = SB if row == 'b' else SF
    fy = ROW_B if row == 'b' else ROW_F
    pose = stand(x, fy, s, 1 if k % 2 == 0 else -1, turn=0.05, eyes='happy', smile=0.7, brow=6, lx=0.0)
    if arms == 'up':
        pose.update(sb=-150 * pop, eb=-10, sf=150 * pop, ef=10)
    elif arms == 'thumbs':
        pose.update(sf=70 * pop, ef=60 * pop, sb=-10, eb=20)
    else:
        pose.update(sf=150 * pop, ef=20 + 20 * math.sin(T * 9), sb=6, eb=12)
    return pose


def poser(year, li):
    """Who stands in slot li of that year's photo: this year's crowd, or strangers from another decade."""
    if year >= 2026:
        return extra(li + (4 if year == 2027 else 0))
    e = ERAS[year]
    who = extra(li + 3 * (year % 7), top=e['tops'][li])
    return who.with_look(print_text=None, headband='#F2F2F2' if year == 1986 and li % 2 == 0 else None)


def posed_group(c, T, year, pop=1.0, hero=None, members=None, skip=()):
    """The New Year photo line-up for a given year. hero: (Character, slot index) to put the hero in the group."""
    e = ERAS[year]
    for k, (x, row, li, arms) in enumerate(POSERS):
        if row != 'b' or k in skip:
            continue
        who = poser(year, li)
        who.draw(c, poser_pose(x, row, arms, T, k, pop), t=T)
    for k, (x, row, li, arms) in enumerate(POSERS):
        if row != 'f' or k in skip:
            continue
        if hero is not None and hero[1] == k:
            who = hero[0]
        else:
            who = poser(year, li)
        who.draw(c, poser_pose(x, row, arms, T, k, pop), t=T)


def corner_regular(c, T, year=2026, x=CORNER_X, who=None, curl_speed=0.8, face=None):
    """The regular in his corner, curling, never posing."""
    who = who or (OLD if year >= 2026 else regular(year))
    pose = stand(x, ROW_B, SB * 1.08, -1, **curl_pose(T, 7, curl_speed, heavy=True), turn=0.3,
                 eye=blink(T, 11), smile=0.05, brow=-2, ly=0.2)
    if face:
        pose.update(face)
    who.draw(c, pose, dumbbells_layers(), t=T)
    return pose


def photo_scene(c, T, year, slot=None, pop=1.0, corner_face=None):
    """The world as the gym's camera frames it for the New Year photo (used live and for the prints).
    slot: (Character, poser index) to put someone particular in the line-up."""
    gym_room(c, T, outside='snow_dawn', photos=0, corner=1.0, hour=8.0)
    gym_props_back(c, T, corner=True)
    corner_regular(c, T, year, curl_speed=0.8, face=corner_face)
    skip = ()
    if year >= 2027:
        corner_hero(c, T)
        skip = (3, 7)
    posed_group(c, T, year, pop=pop, hero=slot, skip=skip)
    gym_props_front(c, T, rack=False, bench_on=False)


def photo_content(year, T=None):
    """A function that draws that year's photo into a w x h box (from a cached print)."""
    def draw(c, w, h):
        img = photo_print(year)
        c.drawImageRect(img, skia.Rect.MakeWH(w, h), skia.SamplingOptions(skia.CubicResampler.Mitchell()))
    return draw


@lru_cache(maxsize=None)
def photo_print(year, size=(960, 540)):
    surface = skia.Surface(*size)
    cc = surface.getCanvas()
    cc.clear(col('#000000'))
    draw_photo(year)(cc, *size)
    return surface.makeImageSnapshot()


def draw_photo(year, T=None):
    """Draw that year's photo live into a w x h box."""
    def draw(c, w, h):
        cx, cy, z = PHOTO_CAM
        vw, vh = W / z, H / z
        c.save()
        c.scale(w / vw, h / vh)
        c.translate(-(cx - vw / 2), -(cy - vh / 2))
        grade = ERAS[year]['grade']
        if grade:
            c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(GRADES[grade])))
        slot = {2026: (HERO_JAN, 5), 2027: (NEWBIE, 5)}.get(year)
        flash = 18.0 if year < 2027 else 139.8
        photo_scene(c, flash if T is None else T, year, slot=slot)
        if grade:
            c.restore()
        c.restore()
        c.drawRect(skia.Rect.MakeWH(w, h), paint('#FFF4DC', 0.08 if grade else 0.0))
    return draw


def corner_hero(c, T, x=CORNER_X - 150):
    """The hero, a year on, curling beside the old man in the corner."""
    pose = stand(x, ROW_B, SB * 1.08, -1, **curl_pose(T + 0.4, 7, 0.8, heavy=True), turn=0.3,
                 eye=blink(T, 12), smile=0.05, brow=-2, ly=0.2)
    HERO_FIT.draw(c, pose, dumbbells_layers(), t=T)
    return pose
