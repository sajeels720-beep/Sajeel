"""Act 3 (1:46-2:40): New Year's Eve and 'you've done enough', midnight, the next January 1st, the new photo."""
from __future__ import annotations

import math

import skia

from common import (BENCH_X, CORNER_X, CROWD, DOOR, HERO_JAN, NEWBIE, OLD, PHOTO_CAM, PHOTO_GAP, PHOTO_H, PHOTO_W,
                    PHOTOS_X, PHOTOS_Y, ROW_B, ROW_F, SB, SF, SHADE, STAND_HIP, WINDOWS, WIN_H, WIN_W, corner_hero,
                    corner_regular, curl_pose, dumbbells_layers, extra, gym_props_back, gym_props_front, gym_room,
                    hero_fit, member_pose, photo_content, photo_scene, stand)
from cues import EV, NEW_PHOTO_YEAR
from engine.captions import title, whisper
from engine.core import H, W, Track, hrand, noise1, out_back, shake, smooth
from engine.draw import circle, col, light_pool, mixc, oval, paint, poly, rrect, text, text_width
from engine.fx import FIREWORK_COLORS, dissolve, firework, puff, wisps
from engine.gym import barbell, chalk_bowl, photo_frame, towel, water_bottle
from engine.render import Shot
from engine.rig import blink, idle, to_local, walk

import act1
import act2

HERO = hero_fit(1.0)
LIFT_X = 900          # where he deadlifts on New Year's Eve
SEAT2 = (BENCH_X - 34, ROW_F - 100 * SF - 6)


def soft_whisper(c, T, s, t0, t1, x, y, size=58):
    """The shadow being kind: thin italic letters, smoky, drifting up as they fade."""
    from engine.captions import envelope
    a = envelope(T, t0, t1, 0.5, 0.7)
    if a <= 0:
        return
    f = skia.Font(skia.Typeface('FreeSerif', skia.FontStyle.Italic()), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    w = f.measureText(s)
    yy = y - (T - t0) * 12
    x0 = x - w / 2
    c.drawString(s, x0, yy, f, paint('#FF3B36', 0.35 * a, blur=12, blend='add'))
    c.drawString(s, x0 + 1, yy + 2, f, paint('#000000', 0.6 * a, blur=4))
    c.drawString(s, x0, yy, f, paint('#E8D2CF', 0.95 * a))
    fade = smooth(t1 - 0.7, t1, T)
    if fade > 0:
        for k in range(10):
            px = x0 + w * (k + 0.5) / 10
            r = 8 + 14 * fade
            c.drawCircle(px, yy - size * 0.3 - 30 * fade, r, paint('#9A9EA6', 0.25 * fade * (1 - fade) * 4, blur=r))


def dec_room(c, T, corner=0.7, outside='snow_night'):
    """New Year's Eve: string lights in the windows, snow, the corner empty but for his towel."""
    hour = 23.0 + 50 / 60 + (T - 106.0) / 16.0 * (10 / 60)
    gym_room(c, T, lights=(0.0, 1.0, 1.0, 0.0), banner_a=0.0, outside=outside, hour=hour, string=1.0, corner=corner)
    gym_props_back(c, T)
    towel(c, CORNER_X + 90, 400, '#E9E6DF', sway=0.0)


def deadlift_pose(T, t0, x=LIFT_X, hold=1.2, down=0.6):
    """One deadlift starting at t0: up over 0.8 s, hold, back down. Returns (pose, bar centre)."""
    lift = smooth(t0, t0 + 0.8, T) * (1 - smooth(t0 + 0.8 + hold, t0 + 0.8 + hold + down, T))
    plate_r = 46 * SF
    bar = (x + 18, ROW_F - plate_r * 0.95 - (ROW_F - plate_r - (ROW_F - 132 * SF)) * lift)
    hip_y = ROW_F - (92 + 31 * lift) * SF
    pose = dict(x=x - 30 * (1 - lift), y=hip_y, scale=SF, facing=1, turn=0.35, lean=52 * (1 - lift) + 2,
                tilt=-20 * (1 - lift), eye=blink(T, 5), eyes='dot', brow=10, smile=0.2 * lift,
                mouth='teeth' if 0.15 < lift < 0.85 and T < t0 + 0.8 else 'curve')
    pose['foot_b'] = to_local(pose, (x - 6, ROW_F - 4))
    pose['foot_f'] = to_local(pose, (x + 14, ROW_F - 4))
    pose['hand_b'] = to_local(pose, (bar[0] + 6, bar[1] + 2))
    pose['hand_f'] = to_local(pose, (bar[0] - 6, bar[1] + 4))
    return pose, bar


def draw_lift(c, T, pose, bar, plates=3):
    barbell(c, *bar, plates=plates, length=200 * SF, plate_r=46 * SF, part='far', depth=(0.18, -0.2))
    HERO.draw(c, pose, t=T)
    barbell(c, *bar, plates=plates, length=200 * SF, plate_r=46 * SF, part='near', depth=(0.18, -0.2))


def bar_on_floor(c, plates=3):
    bar = (LIFT_X + 18, ROW_F - 46 * SF * 0.95)
    barbell(c, *bar, plates=plates, length=200 * SF, plate_r=46 * SF, depth=(0.18, -0.2))


# --- 1. December 31st, nearly midnight (106-110) -------------------------------------------------------------------------

def dec_wide(c, t, T):
    dec_room(c, T)
    gym_props_front(c, T, bench_on=True)
    if T < 108.4:
        pose, bar = deadlift_pose(T, 106.3)
        draw_lift(c, T, pose, bar)
    else:
        bar_on_floor(c)
        walk_u = smooth(108.4, 109.6, T)
        x = LIFT_X + (SEAT2[0] - 40 - LIFT_X) * walk_u
        pose = stand(x, ROW_F, SF, 1, turn=0.35, eye=blink(T, 5), brow=4, smile=0.05, **(walk(T, 0.9, 16)
                                                                                         if walk_u < 0.98 else {}))
        HERO.draw(c, pose, t=T)


def cam_dec_wide(t):
    u = smooth(0, 4.0, t)
    return (1060 + 40 * u, 640, 1.45 + 0.1 * u)


# --- 2. the shadow sits beside him: "you've done enough." (110-114), "rest now." (114-116) ---------------------------------

def seated2(T, look=0.0, hand_up=0.0):
    hip = SEAT2
    pose = dict(x=hip[0], y=hip[1], scale=SF, facing=1, turn=0.35, lean=18, tilt=-6, eye=blink(T, 6),
                breathe=idle(T, 4, 1.2)['breathe'], eyes='dot', brow=0, smile=0.1, ly=0.3, lx=0.2)
    pose['foot_b'] = to_local(pose, (hip[0] + 64 * SF, ROW_F - 4))
    pose['foot_f'] = to_local(pose, (hip[0] + 84 * SF, ROW_F - 4))
    pose['hand_b'] = to_local(pose, (hip[0] + 62 * SF, hip[1] + 16 * SF))
    rest_f = (hip[0] + 80 * SF, hip[1] + 14 * SF)
    raised = (hip[0] + 112 * SF, hip[1] - 120 * SF)
    pose['hand_f'] = to_local(pose, (rest_f[0] + (raised[0] - rest_f[0]) * hand_up,
                                     rest_f[1] + (raised[1] - rest_f[1]) * hand_up))
    return pose


def shade_sitting(c, T, hero_pose, arm=1.0, alpha=1.0, eye=0.75, lift_off=0.0):
    """The shadow sitting on the bench beside him, an arm round his shoulders. Gentle, almost kind."""
    s = SF * 1.04
    hip = (SEAT2[0] - 92 * s, SEAT2[1] + 2)
    pose = dict(x=hip[0], y=hip[1], scale=s, facing=1, turn=0.2, lean=10 + 6 * arm, tilt=14 * arm, alpha=alpha,
                eye=eye, brow=6, sb=6, eb=10, sf=-4, ef=12)
    pose['foot_b'] = to_local(pose, (hip[0] + 60 * s, ROW_F - 4))
    pose['foot_f'] = to_local(pose, (hip[0] + 80 * s, ROW_F - 4))
    sh = act2.world_of(HERO, hero_pose, 'sh_f')
    across = (sh[0] + 6, sh[1] + 4 - 40 * lift_off)
    rest = (hip[0] + 40 * s, hip[1] - 10 * s)
    pose['hand_f'] = to_local(pose, (rest[0] + (across[0] - rest[0]) * arm, rest[1] + (across[1] - rest[1]) * arm))
    pose['hand_b'] = to_local(pose, (hip[0] + 30 * s, hip[1] + 20 * s))
    SHADE.draw(c, pose, t=T)
    return pose, (rest[0] + (across[0] - rest[0]) * arm, rest[1] + (across[1] - rest[1]) * arm), s


def dec_shade(c, t, T):
    dec_room(c, T)
    gym_props_front(c, T)
    bar_on_floor(c)
    sit_in = smooth(EV['shade_sits'], EV['shade_sits'] + 0.6, T)
    arm = smooth(EV['shade_sits'] + 0.4, EV['shade_sits'] + 1.0, T)
    hand_up = smooth(EV['hand_smoke2'] - 0.2, EV['hand_smoke2'] + 0.4, T)
    pose = seated2(T, hand_up=hand_up)
    if T > EV['shade_sits'] + 0.5:
        pose.update(lx=-0.5 + 1.3 * hand_up, ly=0.2 - 0.6 * hand_up, brow=-4 - 6 * hand_up, smile=0.0,
                    eyes='dot' if T < 111.8 else 'tired', eye=blink(T, 6) * (1 - 0.35 * smooth(111.2, 112.6, T)))
    amount = 0.3 * smooth(EV['hand_smoke2'], EV['hand_smoke2'] + 1.4, T)
    layers = None
    if amount > 0:
        pose['no_arm_f'] = True
        layers = {'front': act2.smoking_arm(HERO, T, amount)}
    sp, hand, s = shade_sitting(c, T, pose, arm=arm, alpha=sit_in)
    HERO.draw(c, pose, layers, t=T)
    act2.shade_hand_on(c, hand, s, sit_in)
    soft_whisper(c, T, 'you’ve done enough.', 110.8, 113.2, SEAT2[0] - 60, 590, 58)
    soft_whisper(c, T, 'rest now.', 114.3, 115.8, SEAT2[0] + 10, 600, 52)


def cam_dec_shade(t):
    T = 110.0 + t
    u = smooth(110.0, 113.5, T)
    v = smooth(EV['hand_smoke2'], EV['hand_smoke2'] + 1.0, T)
    return (SEAT2[0] - 50 + 70 * v, 700 - 30 * v, 1.9 + 0.2 * u + 0.6 * v)


# --- 3. the old man's towel in the empty corner (116-118), and a memory of his nod ---------------------------------------

def dec_towel(c, t, T):
    dec_room(c, T, corner=1.0)
    light_pool(c, CORNER_X + 80, 440, 160, 140, 'warm', 0.25)
    m = smooth(117.0, 117.35, T) * (1 - smooth(117.75, 118.0, T))
    if m > 0:
        # not him: a memory of him, see-through and warm, nodding where he always stood
        sepia = [0.5, 0.45, 0.12, 0, 0.06, 0.4, 0.42, 0.1, 0, 0.04, 0.3, 0.32, 0.08, 0, 0.0, 0, 0, 0, 1, 0]
        p = skia.Paint(ColorFilter=skia.ColorFilters.Matrix(sepia), ImageFilter=skia.ImageFilters.Blur(2.5, 2.5))
        p.setAlphaf(0.6 * m)
        light_pool(c, CORNER_X, 560, 260, 280, 'warm', 0.18 * m)
        c.saveLayer(None, p)
        dip = math.sin(math.pi * smooth(117.25, 117.85, T))
        corner_regular(c, 66.0, face=dict(lx=-0.9, smile=0.35, head_dy=14 * dip, tilt=-15 * dip, sf=-4, ef=14, sb=6,
                                          eb=14, eyes='closed' if dip > 0.6 else 'dot'))
        c.restore()


def cam_towel(t):
    T = 116.0 + t
    u = smooth(116.0, 118.0, T)
    return (CORNER_X + 20, 540, 2.5 + 0.35 * u)


# --- 4. no: he lifts the arm off, chalks up, and lifts; the shadow goes to smoke (118-122) -----------------------------------

def dec_refuse(c, t, T):
    dec_room(c, T)
    gym_props_front(c, T)
    bar_on_floor(c)
    up = smooth(EV['stand2'], EV['stand2'] + 0.5, T)
    off = smooth(118.2, 118.6, T)
    pose = seated2(T, hand_up=0.0)
    pose.update(eyes='dot', brow=8, smile=0.15, lx=-0.4 * (1 - up), ly=0.0)
    if up > 0:
        walk_u = smooth(EV['stand2'] + 0.4, EV['chalk'] - 0.1, T)
        x = SEAT2[0] + (LIFT_X - 20 - SEAT2[0]) * walk_u
        pose = stand(x, ROW_F, SF, -1, turn=0.35, eye=blink(T, 5), brow=10, smile=0.1,
                     **(walk(T, 1.0, 16) if 0.02 < walk_u < 0.98 else {}))
        if T > EV['chalk'] - 0.2:
            clap = math.sin(math.pi * smooth(EV['chalk'] - 0.2, EV['chalk'] + 0.1, T))
            pose['facing'] = 1
            pose['hand_f'] = (40 - 10 * clap, -70)
            pose['hand_b'] = (24 + 10 * clap, -72)
    sp, hand, s = shade_sitting(c, T, seated2(T), arm=1.0 - off, alpha=1.0, lift_off=off)
    HERO.draw(c, pose, t=T)
    if up < 0.5:
        act2.shade_hand_on(c, hand, s, 1.0 - off)
    if T > EV['chalk']:
        from engine.fx import puff
        puff(c, pose['x'] + 30, pose['y'] - 70, T, EV['chalk'], n=18, seed=4, color='#F4F1EA', size=16, spread=90,
             life=1.2, a=0.9, wind=(20, -60))


def cam_refuse(t):
    T = 118.0 + t
    u = smooth(118.4, 119.4, T)
    return (SEAT2[0] - 60 - 200 * u, 680, 2.0 - 0.3 * u)


SHADE_GONE_DUR = 1.6


def shade_at_lift(T):
    """The shadow behind him at the lift: reaching, then thrown back by the lockout."""
    s = SF * 1.12
    hit = 120.8
    recoil = smooth(hit, hit + 0.3, T)
    return dict(x=LIFT_X - 170 * s - 90 * recoil, y=ROW_F - 123 * s, scale=s * (1 - 0.1 * recoil), facing=1,
                turn=0.15, hb=-4, kb=3, hf=5, kf=3, lean=14 - 40 * recoil, tilt=10 - 26 * recoil,
                eye=1.0, brow=24, sb=6 - 30 * recoil, eb=10, sf=60 + 60 * recoil, ef=30), s


def shade_dissolving(c, T):
    pose, s = shade_at_lift(T)
    box = (pose['x'] - 130 * s, ROW_F - 390 * s, pose['x'] + 150 * s, ROW_F + 6)
    dissolve(c, lambda cc: SHADE.draw(cc, pose, t=T), box, T, EV['shade_gone'], SHADE_GONE_DUR, seed=9,
             smoke='#08080A', smoke_a=0.8, grey=0.0, embers='#FF4A3D', rise=340, n=48)


def dec_lift(c, t, T):
    dec_room(c, T)
    gym_props_front(c, T)
    pose, bar = deadlift_pose(T, EV['lift2'], hold=1.6)
    shade_dissolving(c, T)
    draw_lift(c, T, pose, bar)
    hit = 120.8
    from engine.fx import shockwave
    burst = math.exp(-(T - hit) / 0.7) if T >= hit else 0.0
    if burst > 0.01:
        from engine.fx import light_rays
        light_pool(c, LIFT_X + 10, ROW_F - 220, 620, 560, 'warm', 0.45 * burst)
        light_rays(c, LIFT_X + 10, ROW_F - 220, T, n=16, length=1100, a=0.16 * burst, color='#FFE7B0', spin=0.2)
    shockwave(c, bar[0], bar[1], T, hit, max_r=1100, life=1.0, color='#F4F1EA', width=50, a=0.8)
    puff(c, bar[0], bar[1], T, hit, n=26, seed=12, color='#F4F1EA', size=20, spread=300, life=1.5, a=0.8,
         wind=(-60, -80))
    glow = smooth(121.6, 122.0, T)
    if glow > 0:
        light_pool(c, 960, 400, 900, 300, '#C59BFF', 0.06 * glow)


def cam_lift(t):
    T = 120.0 + t
    u = smooth(120.0, 122.0, T)
    sx, sy = shake(T, 14 * smooth(120.8, 120.83, T) * (1 - smooth(120.83, 121.3, T)))
    return (LIFT_X - 110 + sx, 640 + sy, 1.75 - 0.2 * u)


# --- 5. midnight: fireworks in the windows (122-124) ---------------------------------------------------------------------

def midnight(c, t, T):
    gym_room(c, T, lights=(0.0, 1.0, 1.0, 0.0), banner_a=0.0, outside='fireworks', hour=0.02, string=1.0, corner=0.7)
    gym_props_back(c, T)
    towel(c, CORNER_X + 90, 400, '#E9E6DF')
    gym_props_front(c, T)
    bar_on_floor(c)
    # colour from the bursts washing over the room
    for k in range(5):
        t0 = 122.0 + k * 0.45
        if T > t0:
            g = math.exp(-(T - t0) / 0.5)
            light_pool(c, WINDOWS[1][0] + WIN_W / 2, 600, 900, 500, FIREWORK_COLORS[k % 6], 0.12 * g)
    shade_dissolving(c, T)
    turn = smooth(122.3, 122.7, T)
    pose = stand(LIFT_X + 40, ROW_F, SF, 1, turn=0.35 - 0.6 * turn, eye=blink(T, 5), brow=2, smile=0.3 + 0.2 * turn,
                 lx=0.6, ly=-0.7 * turn, eyes='dot', **idle(T, 2, 1.0))
    HERO.draw(c, pose, t=T)


def cam_midnight(t):
    u = smooth(0, 2.0, t)
    return (1120, 560, 1.6 + 0.08 * u)


# --- 6. January 1st again: the doors, the crowd, the two of them in the corner (124-132) -------------------------------------

ENTRY2 = [(extra(i + 4), 124.45 + 0.28 * k) for k, i in enumerate((0, 3, 6, 1, 7, 2, 5))]


def doors2(c, t, T):
    opened = smooth(EV['doors2'], EV['doors2'] + 0.18, T)
    gym_room(c, T, door=opened, door_out='#2C3E60', outside='snow_dawn', hour=6.0)
    gym_props_back(c, T)
    dx, dw, dh = DOOR
    for k, (who, t0) in enumerate(ENTRY2):
        if T < t0:
            continue
        x = dx + dw * 0.5 + (T - t0) * 300
        pose = dict(x=x, y=ROW_B - STAND_HIP * SB, scale=SB, facing=1, turn=0.4, **walk(T + k * 0.3, 1.25, 24),
                    eyes='happy', smile=0.75, brow=10, lx=0.4, ly=-0.1, alpha=smooth(t0, t0 + 0.12, T))
        cap = {'behind': lambda cc, j: water_bottle(cc, j['hand_b'][0], j['hand_b'][1] + 26, '#3F8FD0', 0.7)}
        who.draw(c, pose, cap if k % 2 else None, t=T)
    gym_props_front(c, T, rack=False, bench_on=False)


# the new crowd: the same spots as last year, new faces
def new_crowd(c, T, row, clear=None):
    """clear: (x0, x1) or a list of them to leave empty (so a particular person stands out)."""
    spans = [clear] if clear and not isinstance(clear[0], (tuple, list)) else (clear or [])
    for m in sorted((mm for mm in CROWD if mm.row == row), key=lambda mm: mm.x):
        if any(a <= m.x <= b for a, b in spans):
            continue
        who = extra(CROWD.index(m) + 4)
        pose, layers = member_pose(m, T)
        pose.pop('_bar', None)
        who.draw(c, pose, layers, t=T)


def two_in_corner(c, T, nod=None, proud=None):
    """The old man and the hero curling side by side in the corner."""
    face = dict(eye=blink(T, 11))
    if proud is not None:
        p = smooth(proud, proud + 0.5, T)
        face.update(lx=-0.9 * p, smile=0.1 + 0.35 * p, eyes='happy' if p > 0.6 else 'dot')
    corner_regular(c, T, face=face)
    hpose = stand(CORNER_X - 150, ROW_B, SB * 1.08, -1, **curl_pose(T + 0.4, 7, 0.8, heavy=True), turn=0.3,
                  eye=blink(T, 12), smile=0.05, brow=-2, ly=0.2)
    if nod is not None:
        look = smooth(nod - 1.2, nod - 0.8, T)
        dip = math.sin(math.pi * smooth(nod, nod + 0.5, T))
        hpose.update(lx=0.9 * look, ly=0.0, head_dy=5 * dip, tilt=-7 * dip, smile=0.05 + 0.3 * look,
                     brow=-3 * look)
        if T > nod - 0.9:
            hpose.update(sf=-4, ef=14, sb=6, eb=14)
    HERO.draw(c, hpose, dumbbells_layers(), t=T)
    return hpose


def callback_wide(c, t, T, nod=None, proud=None):
    gym_room(c, T, outside='snow_dawn', hour=7.0)
    gym_props_back(c, T, treads=(1.6, 1.6, 1.6), screens=(1, 1, 1))
    new_crowd(c, T, 'b')
    two_in_corner(c, T, nod, proud)
    gym_props_front(c, T)
    new_crowd(c, T, 'f', clear=(1450, 2000) if nod is not None else None)
    act1_hero_spot = extra(13)
    act1_hero_spot.draw(c, act1.hero_pose(T, x=act1.HERO_X), dumbbells_layers(), t=T)


def cam_callback(t):
    T = EV['corner'] + t
    u = smooth(EV['corner'] + 1.0, EV['corner'] + 4.6, T)
    return (960 + (CORNER_X - 120 - 960) * u, 560 + 60 * u, 1.0 + 1.0 * u)


# --- 7. the newcomer at the door; the nod (132-138.6) -------------------------------------------------------------------------

NEW_X = DOOR[0] + DOOR[1] + 70


def newcomer_pose(T):
    step = smooth(EV['step_in'], EV['step_in'] + 1.4, T)
    seen = smooth(EV['nod2'] + 0.3, EV['nod2'] + 0.6, T)
    dart = noise1(T * 1.6, 3) if T < EV['nod2'] else 0.9
    pose = stand(NEW_X + 230 * step, ROW_B, SB * 1.06, 1, turn=0.45, eye=blink(T, 21), eyes='dot', pupil=0.7,
                 brow=-14 + 8 * seen, mouth='wavy' if seen < 0.5 else 'curve', mwide=0.6, smile=0.1 + 0.25 * seen,
                 lx=dart, ly=-0.2)
    if 0.02 < step < 0.98:
        pose.update(walk(T, 0.8, 14))
    pose.update(sf=40, ef=70, sb=30, eb=80)   # both hands hugging the water bottle
    if seen > 0 and T < EV['step_in']:
        dip = math.sin(math.pi * smooth(EV['nod2'] + 0.55, EV['nod2'] + 0.95, T))
        pose.update(head_dy=4 * dip, tilt=-6 * dip)
    return pose


def bottle_layer(cc, j):
    water_bottle(cc, (j['hand_f'][0] + j['hand_b'][0]) / 2, j['hand_f'][1] + 28, '#3F8FD0', 0.8)


def whole_room(c, T):
    """January 1st, the whole room at once: the newcomer at the door with the shadow behind, the crowd, and the
    hero beside the old man in the corner, so a camera can travel from one to the other."""
    gym_room(c, T, outside='snow_dawn', hour=7.0, door=0.85, door_out='#2C3E60')
    gym_props_back(c, T, treads=(1.6, 1.6, 1.6), screens=(1, 1, 1))
    new_crowd(c, T, 'b', clear=(0, 620))
    eyes = smooth(133.4, 133.9, T) * (1 - smooth(EV['step_in'] + 0.3, EV['step_in'] + 1.3, T))
    if eyes > 0:
        dx, dw, dh = DOOR
        back = smooth(EV['step_in'] + 0.2, EV['step_in'] + 1.3, T)
        SHADE.draw(c, dict(x=dx + dw * (0.5 - 0.25 * back), y=ROW_B - 123 * SB * 1.1 * (1 - 0.3 * back) - 20 * back,
                           scale=SB * 1.1 * (1 - 0.3 * back), facing=1, turn=0.2, hb=-4, kb=3, hf=5, kf=3,
                           alpha=eyes, eye=eyes, brow=22, lean=6 - 16 * back), t=T)
    NEWBIE.draw(c, newcomer_pose(T), {'front': bottle_layer}, t=T)
    two_in_corner(c, T, nod=EV['nod2'], proud=EV['proud'])
    gym_props_front(c, T, rack=False, bench_on=True)
    new_crowd(c, T, 'f', clear=[(0, 600), (1450, 2000)])
    extra(13).draw(c, act1.hero_pose(T, x=act1.HERO_X), dumbbells_layers(), t=T)


def newcomer(c, t, T):
    whole_room(c, T)


TORCH = Track([(132.0, (NEW_X + 40, 600.0, 2.25)),
               (134.6, (NEW_X + 40, 600.0, 2.4)),
               (135.9, (CORNER_X - 110, 600.0, 2.4)),
               (136.95, (CORNER_X - 110, 600.0, 2.45)),
               (137.9, (NEW_X + 150, 600.0, 2.3)),
               (138.7, (NEW_X + 220, 600.0, 2.25)),
               (139.6, (980.0, 560.0, 1.12))])


def cam_torch(t):
    """One unbroken move: the newcomer at the door, across the room to the hero's nod, back to the newcomer
    stepping in as the shadow gives up, then out wide to see them all."""
    T = EV['newcomer'] + t
    x, y, z = TORCH(T)
    for a, b in ((134.6, 135.9), (136.95, 137.9)):
        if a < T < b:
            z -= 0.7 * math.sin(math.pi * (T - a) / (b - a))
    return (x, y, z)


def cam_room_pan(t):
    """From the newcomer at the door, across the room, to the corner: one move, so we know where they all are."""
    T = 134.8 + t
    u = smooth(134.8, 136.0, T)
    x = NEW_X + 40 + (CORNER_X - 110 - NEW_X - 40) * u
    z = 2.3 - 0.75 * math.sin(math.pi * u) + 0.1 * u
    return (x, 600 - 30 * math.sin(math.pi * u), z)


def cam_newcomer(t):
    T = EV['newcomer'] + t
    u = smooth(132.0, 134.8, T)
    return (NEW_X + 40, 600, 2.3 + 0.15 * u)


def nod_corner(c, t, T):
    callback_wide(c, t, T, nod=EV['nod2'], proud=EV['proud'])


def cam_nod_corner(t):
    return (CORNER_X - 110, 600, 2.4)


def newcomer_steps_in(c, t, T):
    newcomer(c, t, T)


def cam_steps_in(t):
    T = 136.9 + t
    step = smooth(EV['step_in'], EV['step_in'] + 1.4, T)
    return (NEW_X + 40 + 200 * step, 610, 2.3 - 0.2 * step)


def proud_corner(c, t, T):
    whole_room(c, T)


# --- 8. the new photo, and onto the wall it goes (138.6-147.4) -------------------------------------------------------------

def photo2(c, t, T):
    flash = EV['photo_flash2']
    Tf = min(T, flash)
    pop = smooth(EV['photo_call2'], EV['photo_call2'] + 0.5, T)
    shrink = smooth(flash + 0.35, flash + 1.3, T)
    k = 1.0 - 0.4 * shrink
    rot = 3 * shrink
    c.drawPaint(paint('#0B0D12'))
    c.save()
    c.translate(W / 2, H / 2 - 120 * shrink)
    c.rotate(rot)
    c.scale(k, k)
    if shrink > 0:
        m = 46 * shrink
        c.drawRect(skia.Rect.MakeLTRB(-W / 2 - m + 12, -H / 2 - m + 16, W / 2 + m + 12, H / 2 + m * 3.2 + 16),
                   paint('#000000', 0.5, blur=14))
        c.drawRect(skia.Rect.MakeLTRB(-W / 2 - m, -H / 2 - m, W / 2 + m, H / 2 + m * 3.2), paint('#F2EEE6'))
        text(c, str(NEW_PHOTO_YEAR), 0, H / 2 + m * 2.4, 120 * shrink, 'GochiHand', '#2C2A26', shrink)
    c.clipRect(skia.Rect.MakeLTRB(-W / 2, -H / 2, W / 2, H / 2))
    cx, cy, z = PHOTO_CAM
    c.scale(z, z)
    c.translate(-cx, -cy)
    photo_scene(c, Tf, NEW_PHOTO_YEAR, slot=(NEWBIE, 5), pop=pop)
    c.restore()


NEW_SLOT = (PHOTOS_X + 5 * PHOTO_GAP, PHOTOS_Y)


def photo_wall(c, t, T):
    """The new print flies onto the wall beside the other five; the camera pulls back to see them all."""
    u = smooth(EV['photo_wall'], EV['photo_wall'] + 1.1, T)
    x = NEW_SLOT[0] + 260 * (1 - u)
    y = NEW_SLOT[1] - 120 * (1 - u) ** 2
    s = 1.0 + 2.2 * (1 - u)
    rot = -10 * (1 - u) + 1.5
    gym_room(c, T, outside='snow_dawn', hour=8.0, new_photo=(x, y, s, rot), corner=1.0)
    gym_props_back(c, T)
    glow = smooth(EV['photo_wall'] + 1.2, EV['photo_wall'] + 1.8, T)
    if glow > 0:
        for k in range(6):
            rx, ry = act2.regular_in_print(k)
            light_pool(c, rx, ry, 9, 12, '#FFE2A0', 0.45 * glow)
        # and, in the new one, the young man beside him
        light_pool(c, act2.regular_in_print(5)[0] - 9, act2.regular_in_print(5)[1] + 1, 9, 12, '#FFE2A0', 0.45 * glow)


def cam_photo_wall(t):
    T = EV['photo_wall'] + t
    u = smooth(EV['photo_wall'] + 1.0, EV['photo_wall'] + 4.0, T)
    cx = NEW_SLOT[0] - (NEW_SLOT[0] - (PHOTOS_X + 2.5 * PHOTO_GAP)) * u
    return (cx, PHOTOS_Y + 4, 6.0 - 2.8 * u)


# --- 9. the title (148-160) --------------------------------------------------------------------------------------------------

def title_card(c, t, T):
    c.drawPaint(paint('#050608'))
    ghost = 0.3 * smooth(148.6, 150.4, T)
    if ghost > 0:
        # behind the words, faint and out of focus: the corner, and the two of them still training
        c.save()
        c.translate(W / 2, H / 2 + 60)
        c.scale(2.0, 2.0)
        c.translate(-(CORNER_X - 80), -(ROW_B - 200))
        p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(8, 8))
        p.setAlphaf(ghost)
        c.saveLayer(None, p)
        gym_room(c, T, outside='snow_dawn', hour=8.0, banner_a=0.0, photos=0, corner=1.0)
        gym_props_back(c, T)
        two_in_corner(c, T)
        c.restore()
        c.restore()
    t0 = EV['title_card']
    title(c, T, 'EVERYONE QUITS IN FEBRUARY.', t0 + 0.4, 159.6, 430, size=104, underline=t0 + 1.2,
          ul_color='#E8B93A')
    a = smooth(t0 + 3.0, t0 + 3.8, T) * (1 - smooth(158.6, 159.6, T))
    text(c, 'Be the one who stays.', W / 2, 640, 78, 'PatrickHand', '#E8B93A', a)


def overlays(c, T):
    pass


# --- assemble ---------------------------------------------------------------------------------------------------------------

def shots():
    return [
        Shot(EV['dec'], EV['shade_sits'], dec_wide, cam_dec_wide, name='dec_wide'),
        Shot(EV['shade_sits'], EV['towel'], dec_shade, cam_dec_shade, name='dec_shade'),
        Shot(EV['towel'], EV['stand2'] - 0.2, dec_towel, cam_towel, name='dec_towel'),
        Shot(EV['stand2'] - 0.2, EV['lift2'], dec_refuse, cam_refuse, name='dec_refuse'),
        Shot(EV['lift2'], EV['midnight2'], dec_lift, cam_lift, name='dec_lift'),
        Shot(EV['midnight2'], 124.0, midnight, cam_midnight, name='midnight'),
        Shot(124.0, EV['corner'], doors2, act1.cam_doors, name='doors2'),
        Shot(EV['corner'], EV['newcomer'], callback_wide, cam_callback, name='callback'),
        Shot(EV['newcomer'], EV['photo_call2'], newcomer, cam_torch, name='torch'),
        Shot(EV['photo_call2'], EV['photo_wall'], photo2, None, name='photo2'),
        Shot(EV['photo_wall'], 148.0, photo_wall, cam_photo_wall, name='photo_wall'),
        Shot(148.0, 160.0, title_card, None, name='title'),
    ]
