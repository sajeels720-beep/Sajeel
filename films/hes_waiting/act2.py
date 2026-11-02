"""Act 2 (1:32-2:37): Day 1, the year that changes the old man, the last temptation, and the trailhead."""
from __future__ import annotations

import math
from dataclasses import replace

import skia

from act1 import OLD_X, corner_eyes, hero_in_bed, old_on_bed, shade_emissive, sitting_hero, to_local_pose
from common import (BED, DOOR, FLOOR, HERO, HERO_LOOK, LIE_HIP, MATT, NIGHTSTAND, POSTER, SHADE, STRIKE_LINE, WINDOW,
                    WRITE_AT, Character, Room, blanket, cane, draw_room, in_world, lying_blanket_contour, lying_pose,
                    old_face, old_man, phone_side, pocket_watch, poster_marks, sit_edge_pose, to_world, vitality)
from cues import EV, SPEECH, WHISPERS
from engine.captions import whisper
from engine.core import H, W, clamp, hrand, hrange, noise1, smooth
from engine.draw import mixc, oval, paint, poly, rrect, text, text_width
from engine.fx import dissolve, falling_leaves, rainfall, snowfall
from engine.light import pool
from engine.motion import CamPath, Curve, Gait, blend, breath, settle, stand_feet
from engine.render import Shot
from engine.rig import BASE_POSE, blink, solve
from world import PATH_Y, river_path, street_dawn, trailhead

RUNNER = Character(replace(HERO_LOOK, shoes='#ECE9E2'), seed=1)
HIKER = Character(replace(HERO_LOOK, shoes='#6B4E35', pants='#3B4A3A'), seed=1)


# --- shared helpers ------------------------------------------------------------------------------------------------

def old_standing(x, T, v, *, facing=-1, cane_hand=True, face=None, floor=FLOOR, run=False, scale=1.0):
    """The old man on his feet; the weaker he is, the more he leans on the stick."""
    u = 1 - v
    p = stand_feet(x, floor, scale, facing)
    hunch = 4 + 24 * u * u
    p.update(old_face(v, T))
    p.update(lean=hunch, tilt=4 + 10 * u, sb=6, sf=-4 + 20 * u, ef=40 * u + 10)
    # knees soften and the hips drop a little when he's weak
    p['y'] += 8 * u * scale
    if face:
        p.update(face)
    return p


def draw_old_standing(c, p, T, v, *, stick=True, run=False):
    who = old_man(v, run=run)
    j = who.draw(c, p, t=T)
    if stick:
        hand = to_world(p, j['hand_f'])
        tip = (hand[0] + 16 * p.get('facing', 1), FLOOR - 2 if p.get('floor_y') is None else p['floor_y'])
        cane(c, hand, tip)
    return j


def watch_ticking_again(T):
    """The second hand stopped at 72.2 and starts again with the tick in the dark at 92."""
    from act1 import tick_angle
    stopped = math.floor(EV['watch_stops'])
    if T < EV['tick_back']:
        return stopped / 60 * math.tau
    return tick_angle(T, [EV['tick_back'] + k for k in range(0, 120)]) + stopped / 60 * math.tau


# --- 1. Day 1: dawn; he never slept. ONE DAY. becomes DAY ONE. (92.6-97) -------------------------------------------

def old_slumped_dawn(head=0.0):
    def draw(cc, TT, rim_pass=False):
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=head(TT) if callable(head) else head, look=0.6)
        pp['hand_f'] = (34, 18)
        m = cc.getTotalMatrix()

        def mid(c2, j):
            c2.save()
            c2.setMatrix(m)
            hand = to_world(pp, (34, 18))
            pocket_watch(c2, hand[0] + 4, hand[1] + 74, 11, TT, detail=False, open_lid=False, chain=hand,
                         hand_angle=watch_ticking_again(TT))
            c2.restore()
        old_man(v).draw(cc, pp, layers={'mid': mid}, t=TT)
        cane(cc, (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2))
        return pp
    return draw


def _dawn_face(TT):
    """Red-eyed after the night; his eyes go from the old man up to the poster on the wall."""
    up = smooth(93.0, 93.7, TT)
    return dict(lx=0.9 - 0.5 * up, ly=0.3 - 1.1 * up, tilt=-10 * up, brow=-4 - 4 * up, eye=0.9 * blink(TT, 1, 3.4),
                bags=1.0, reflect=None)


def dawn_look(c, t, T):
    R = Room(light='dawn', sky='dawn', curtain=0.0, ambient='#4E587E',
             hero=sitting_hero(lambda TT: 1.0, _dawn_face, phone_dead=0.0),
             old=old_slumped_dawn(0.0), old_rim=0.35)

    def lights(cc):
        pool(cc, 1285, 450, 300, 300, '#FFB27A', 0.35)
        x, y, w, h = POSTER
        pool(cc, x + w / 2, y + h / 2, w * 1.8, h * 1.5, '#C9C3D8', 0.3)
    R.lights_extra = lights
    draw_room(c, T, R)


cam_dawn_look = CamPath([(0.0, (860, 690, 1.5)), (0.5, (858, 684, 1.52)), (1.4, (836, 602, 1.7))], handheld=3,
                        seed=51)


def marker_path(T):
    """(tip, pressing) for the marker over the poster: in from below, the line through ONE DAY., a lift across to
    the sky, DAY ONE. written left to right, and away."""
    x, y, w, h = POSTER
    st, wr = poster_marks(T)
    (ax, ay), _, (bx, by) = STRIKE_LINE
    a = (x + w * ax, y + h * ay)
    b = (x + w * bx, y + h * by)
    cx, base, ang, sz = WRITE_AT
    size = sz * w
    tw = text_width('DAY ONE.', 'CaveatBrush', size)
    tan = math.tan(math.radians(ang))

    def on_text(u):
        px = x + w * cx - tw / 2 + tw * u
        py = y + h * base - size * (0.3 + 0.28 * math.sin(u * 44.0))
        return (px, py + (px - (x + w * cx)) * tan)
    w0, w1 = EV['write'] + 0.1, EV['write'] + 1.4
    s0, s1 = EV['strike'] + 0.15, EV['strike'] + 0.6
    below = (a[0] - 260, a[1] + 300)
    if T < s0:
        u = smooth(EV['strike'] - 0.25, s0, T)
        return (below[0] + (a[0] - below[0]) * u, below[1] + (a[1] - below[1]) * u), False
    if T <= s1:
        return (a[0] + (b[0] - a[0]) * st, a[1] + (b[1] - a[1]) * st), True
    if T < w0:
        u = smooth(s1, w0, T)
        e = on_text(0.0)
        hop = 30 * math.sin(math.pi * u)
        return (b[0] + (e[0] - b[0]) * u, b[1] + (e[1] - b[1]) * u - hop), False
    if T <= w1:
        return on_text(wr), True
    u = smooth(w1 + 0.1, w1 + 0.7, T)
    e = on_text(1.0)
    away = (e[0] - 120, e[1] + 420)
    return (e[0] + (away[0] - e[0]) * u, e[1] + (away[1] - e[1]) * u), False


def marker_hand(c, T):
    """His hand with a black marker; the blue sleeve runs out of the bottom of the frame."""
    (tx, ty), pressing = marker_path(T)
    ang = math.radians(-58)
    d = (math.cos(ang), math.sin(ang))                 # from the hand toward the tip
    hand = (tx - d[0] * 44, ty - d[1] * 44 + (0 if pressing else 4))
    sleeve_end = (hand[0] - 150, hand[1] + 260)
    c.drawLine(hand[0], hand[1], *sleeve_end, paint('outline', stroke=34))
    c.drawLine(hand[0], hand[1], *sleeve_end, paint(HERO_LOOK.top, stroke=27))
    # the marker
    tail = (tx - d[0] * 64, ty - d[1] * 64)
    nib = (tx - d[0] * 6, ty - d[1] * 6)
    c.drawLine(*tail, *nib, paint('outline', stroke=13))
    c.drawLine(*tail, *nib, paint('#2A2B31', stroke=9))
    c.drawLine(*nib, tx, ty, paint('#141418', stroke=5))
    c.drawLine(tail[0] + d[0] * 6, tail[1] + d[1] * 6, tail[0] + d[0] * 18, tail[1] + d[1] * 18,
               paint('#E9E4DA', stroke=9))
    # the fist around it
    skin = HERO_LOOK.skin
    c.drawCircle(hand[0], hand[1], 15, paint(skin))
    c.drawCircle(hand[0], hand[1], 15, paint('outline', stroke=4))
    c.drawCircle(hand[0] + d[0] * 10, hand[1] + d[1] * 10, 7, paint(skin))
    c.drawCircle(hand[0] + d[0] * 10, hand[1] + d[1] * 10, 7, paint('outline', stroke=3))


def day_one(c, t, T):
    R = Room(light='dawn', sky='dawn', curtain=0.0, ambient='#5A6488', hero=None, old=None)
    R.front = marker_hand
    x, y, w, h = POSTER
    R.lights_extra = lambda cc: pool(cc, x + w / 2 + 30, y + h / 2 - 20, w * 2.6, h * 2.1, '#E2D6DE', 0.6)
    draw_room(c, T, R)


cam_day_one = CamPath([(0.0, (826, 500, 3.45)), (3.0, (826, 494, 3.7))], handheld=2, seed=55)


# --- 2. he opens the curtains (97-102) ------------------------------------------------------------------------------------

WALK1 = Curve([(97.6, 700.0), (99.8, 1222.0)])
GAIT1 = Gait(WALK1, 97.6, 99.8, FLOOR, step=86, lean=4)


def curtain_open(T):
    return smooth(EV['curtains'], EV['curtains'] + 0.9, T)


def curtains_shot(c, t, T):
    op = curtain_open(T)
    warm = smooth(EV['curtains'], EV['curtains'] + 1.4, T)

    def hero(cc, TT, rim_pass=False):
        p = GAIT1.pose(TT)
        p.update(turn=0.3, eye=blink(TT, 1, 3.5), bags=0.8, breathe=breath(TT, 0.3, 0.8, 1))
        reach = smooth(99.7, 100.15, TT)
        if reach > 0:
            sweep = op
            hb = (1278 - 140 * sweep, 440 + 10 * sweep)
            hf = (1292 + 60 * sweep, 436)
            p['hand_b'] = to_local_pose(p, (p['x'] + (hb[0] - p['x']) * reach, p['y'] - 40 + (hb[1] - p['y'] + 40) * reach))
            p['hand_f'] = to_local_pose(p, (p['x'] + (hf[0] - p['x']) * reach, p['y'] - 40 + (hf[1] - p['y'] + 40) * reach))
            p['ik_b'] = p['ik_f'] = 1.0
            p['tilt'] = -10 * reach
            p['ly'] = -0.6 * reach
        HERO.draw(cc, p, t=TT)
        return p

    def old(cc, TT, rim_pass=False):
        return old_slumped_dawn(lambda T_: 0.5 * smooth(EV['old_wakes'], EV['old_wakes'] + 1.6, T_))(cc, TT, rim_pass)

    R = Room(light='dawn', sky='dawn', curtain=op, warm=warm, ambient=mixc_hex('#4E587E', '#C9B6A6', warm),
             hero=hero, old=old, old_rim=0.3 + 0.6 * warm, hero_last=True)
    R.lights_extra = lambda cc: _sunbeam(cc, warm)
    R.old_rim_color = '#FFC48A'
    draw_room(c, T, R)


def mixc_hex(a, b, u):
    return '#%02X%02X%02X' % mixc(a, b, clamp(u))


def _sunbeam(c, warm):
    x, y, w, h = WINDOW
    pool(c, x + w / 2, y + h / 2, w * 1.2, h * 1.1, '#FFB27A', 0.25 + 0.6 * warm)
    from engine.light import beam
    beam(c, poly([(x + 20, y + h), (x + w - 20, y + h), (x + w - 520, FLOOR + 60), (x - 640, FLOOR + 60)], True),
         '#FFB070', 0.65 * warm, blur=50)
    pool(c, OLD_X - 20, 640, 260, 240, '#FFC48A', 0.5 * warm)


cam_curtains = CamPath([(0.0, (900, 660, 1.3)), (2.8, (1060, 640, 1.34)), (5.0, (1080, 650, 1.42))],
                       handheld=4, seed=52)


# --- 3. shoes on; he stands, and the old man stands with him (102-107) ------------------------------------------------

def seated_tie(T, x, tie):
    """Sitting on the side of the bed, bending down to his shoes (tie 0..1 how far down)."""
    p = dict(x=x, y=MATT - 4, facing=1, turn=0.3, foot_f=(44, FLOOR - 9 - (MATT - 4) - 1),
             foot_b=(30, FLOOR - 9 - (MATT - 4) - 1), ikl_f=-1.0, ikl_b=-1.0, lean=6 + 46 * tie, tilt=12 * tie,
             ly=0.8 * tie, eye=blink(T, 1, 3.3), breathe=breath(T, 0.3, 0.8, 1))
    if tie > 0.05:
        p['hand_f'] = (56 + 6 * math.sin(T * 9) * tie, 70 * tie - 10)
        p['hand_b'] = (40 - 4 * math.sin(T * 9) * tie, 66 * tie - 6)
        p['ik_f'] = p['ik_b'] = 1.0
    return p


def sit_to_stand(T, t0, dur, sit, stand):
    u = smooth(t0, t0 + dur, T)
    if u <= 0:
        return sit
    if u >= 1:
        return stand
    p = blend(sit, stand, u)
    # the hips lift forward over the feet, chest leaning in on the way up
    p['lean'] = p.get('lean', 0) + 26 * math.sin(math.pi * u)
    return p


def stand_shot(c, t, T):
    tie = smooth(102.5, 103.0, T) * (1 - smooth(104.6, 105.0, T))
    hx = 700

    def hero(cc, TT, rim_pass=False):
        sit = seated_tie(TT, hx, tie)
        st = stand_feet(hx + 30, FLOOR, 1.0, 1)
        st.update(turn=0.3, eye=blink(TT, 1, 3.4), sb=4, sf=-2, lean=2, breathe=breath(TT, 0.3, 0.8, 1))
        p = sit_to_stand(TT, EV['rise'], 0.9, sit, st)
        RUNNER.draw(cc, p, t=TT)
        return p

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        p = stand_old(TT)
        j = old_man(v).draw(cc, p, t=TT)
        if TT < EV['cane_drop']:
            up = smooth(EV['rise'] + 0.2, EV['cane_drop'], TT)
            hand = to_world(p, j['hand_f'])
            lean_tip = (OLD_X + 92, FLOOR - 2)
            planted = (hand[0] - 18, FLOOR - 2)
            tip = (lean_tip[0] + (planted[0] - lean_tip[0]) * up, FLOOR - 2)
            top = (OLD_X + 74 + (hand[0] - OLD_X - 74) * up, MATT - 70 + (hand[1] - MATT + 70) * up)
            cane(cc, top, tip)
        else:
            hand, tip = dropped_cane()
            falling_cane(cc, TT, EV['cane_drop'], hand, tip, side=-1)
        return p

    R = Room(light='day', sky='dawn', curtain=1.0, warm=0.8, ambient='#E9D6C2', hero=hero, old=old)
    R.lights_extra = lambda cc: _sunbeam(cc, 1.0)
    draw_room(c, T, R)


cam_stand = CamPath([(0.0, (870, 690, 1.55)), (5.4, (890, 674, 1.5))], handheld=4, seed=53)


def stand_old(T):
    """Day 1: the old man gets up with the boy, on his stick; then he lets it go and stands a little straighter."""
    v = vitality(T)
    drop = EV['cane_drop']
    sit = sit_edge_pose(OLD_X, T, v, head_up=0.6, look=0.9)
    sit['hand_f'] = (40, -10)
    st = old_standing(OLD_X - 40, T, v, facing=-1,
                      face=dict(lx=0.6, smile=0.15 + 0.3 * smooth(drop + 0.3, drop + 0.9, T)))
    p = sit_to_stand(T, EV['rise'] + 0.2, 1.05, sit, st)
    free = smooth(drop + 0.1, drop + 0.7, T)
    p['lean'] = p.get('lean', 0.0) - 7 * free
    p['sf'] = p.get('sf', 0.0) * (1 - free) + 6 * free
    p['ef'] = p.get('ef', 0.0) * (1 - free) + 14 * free
    return p


_DROPPED = {}


def dropped_cane():
    """(hand, tip) of the stick at the moment he lets it go."""
    if not _DROPPED:
        drop = EV['cane_drop']
        q = stand_old(drop)
        pp = dict(BASE_POSE)
        pp.update(q)
        hand = to_world(q, solve(old_man(vitality(drop)).look, pp)['hand_f'])
        _DROPPED['v'] = (hand, (hand[0] - 18, FLOOR - 2))
    return _DROPPED['v']


def cane_on_floor(c, T=None):
    """The stick he let fall on Day 1, still lying where it fell at the end of the bed."""
    hand, tip = dropped_cane()
    falling_cane(c, EV['cane_drop'] + 5.0, EV['cane_drop'], hand, tip, side=-1)


# --- 4. out of the door (107-111) ---------------------------------------------------------------------------------------

OUT_WALK = Curve([(107.9, 800.0), (108.9, 1010.0)])
OUT_RUN = Curve([(109.1, 1010.0), (111.2, 1880.0, 'smooth')])
GAIT_OUT = Gait(OUT_WALK, 107.9, 108.9, PATH_Y, step=88)
RUN_OUT = Gait(OUT_RUN, 109.1, 111.2, PATH_Y, step=118, run=True, lean=9, arm=34, lift=13, blend_steps=0.3)


def out_shot(c, t, T):
    door = smooth(EV['door_open'], EV['door_open'] + 0.4, T)
    street_dawn(c, T, cam_x=960, warm=0.3, door_open=door)
    if T >= EV['door_open'] + 0.2:
        if T < 109.1:
            p = GAIT_OUT.pose(T)
        else:
            p = RUN_OUT.pose(T)
        p.update(turn=0.3, eye=blink(T, 1, 3.3), mopen=0.0)
        RUNNER.draw(c, p, t=T)
        # breath in the cold air
        for k in range(4):
            t0 = 108.0 + k * 0.7
            u = (T - t0) / 1.1
            if 0 < u < 1:
                hp = (p['x'] + 70, p['y'] - 150)
                c.drawCircle(hp[0] + 60 * u, hp[1] - 10 * u, 10 + 22 * u, paint('#FFFFFF', 0.35 * (1 - u), blur=6))


def falling_cane(c, T, t0, hand, tip, side=1):
    """A walking stick let go of: it tips over around its foot and clatters down flat."""
    L = math.hypot(hand[0] - tip[0], hand[1] - tip[1])
    a0 = math.atan2(hand[0] - tip[0], tip[1] - hand[1])
    flat = side * math.pi / 2 * 0.97
    dt = T - t0
    if dt < 0.42:
        ang = a0 + (flat - a0) * (dt / 0.42) ** 2
    else:
        ang = flat - side * 0.12 * math.exp(-(dt - 0.42) / 0.1) * abs(math.sin((dt - 0.42) * 28))
    cane(c, (tip[0] + math.sin(ang) * L, tip[1] - math.cos(ang) * L), tip)


cam_out = CamPath([(0.0, (960, 640, 1.08)), (3.6, (1040, 640, 1.08))], handheld=3, seed=54)


# --- the montage ----------------------------------------------------------------------------------------------------------

def rising_motes(c, T, src, pulses, n=24, seed=9, dur=1.7, drift=(160.0, -330.0)):
    """The drain run backwards: each time he pushes on, warm sparks leave his chest and float up and away, toward
    the light. The old man is not with him; this is him getting stronger, somewhere ahead. src is fn(T) -> (x, y);
    each spark keeps the place it left him from."""
    for t0 in pulses:
        if T < t0 or T > t0 + dur + 0.6:
            continue
        s0 = src(t0)
        k = math.exp(-max(0.0, T - t0) / 0.3) * smooth(t0, t0 + 0.06, T)
        c.drawCircle(s0[0], s0[1], 46, paint('#FFD27A', 0.4 * k, blur=18, blend='add'))
        for i in range(n):
            delay = hrand(i, seed, int(t0 * 10)) * 0.4
            u = (T - t0 - delay) / dur
            if u <= 0 or u >= 1:
                continue
            o = src(t0 + delay)
            e = 1 - (1 - u) ** 1.8
            x = o[0] + drift[0] * e + hrange(-70, 70, i, seed, 2) * e + 14 * math.sin(u * 7 + i)
            y = o[1] + drift[1] * e + hrange(-40, 40, i, seed, 3) * e
            a = min(1.0, u * 6) * (1 - smooth(0.6, 1.0, u))
            colr = mixc('#FFF1C9', '#FFC24F', e)
            r = hrange(3.0, 6.0, i, seed, 5) * (1 - 0.4 * e)
            c.drawCircle(x, y, r * 3.2, paint(colr, 0.35 * a, blur=8, blend='add'))
            c.drawCircle(x, y, r, paint(colr, 0.95 * a, blend='add'))


def track(cam_curve, y=600, z=1.15, seed=0, hh=3):
    def cam(t):
        return (cam_curve(t), y + noise1(t * 0.4, seed) * hh, z, 0.0)
    return cam


# DAY 3: he runs out of breath, alone; he gets it back and runs on
D3 = EV['days'][0]
D3_GAIT1 = Gait(Curve([(D3 - 1.4, 0.0), (D3 + 2.3, 1060.0, 'stop')]), D3 - 1.4, D3 + 2.3, PATH_Y, step=104,
                run=True, lean=8, arm=26, lift=10, duty=0.4, blend_steps=0.25)
D3_GAIT2 = Gait(Curve([(D3 + 3.65, 1060.0), (D3 + 4.6, 1420.0)]), D3 + 3.65, D3 + 4.6, PATH_Y, step=104, run=True,
                lean=8, arm=26, lift=10, blend_steps=0.25)


def day3(c, t, T):
    cx = cam_day3(t)[0]
    river_path(c, T, cx, 'dawn')
    # the boy, alone
    if T < D3 + 2.3:
        p = D3_GAIT1.pose(T)
        p.update(mopen=0.0, smile=-0.3, sweat=0.8, brow=-6)
    elif T < D3 + 3.65:
        bent = smooth(D3 + 2.3, D3 + 2.6, T) * (1 - smooth(D3 + 3.45, D3 + 3.65, T))
        p = D3_GAIT1._stand(1060.0)            # the same stance the run stops in and starts from
        pant = math.sin((T - D3) * 14)
        p.update(lean=48 * bent, tilt=10 * bent - 14 * smooth(D3 + 3.3, D3 + 3.5, T), mopen=0.0, smile=-0.35,
                 sweat=1.2, brow=-10, hand_f=(40 * bent + 4, 30 * bent), hand_b=(30 * bent, 36 * bent),
                 ik_f=-1.0, ik_b=-1.0, y=stand_feet(1060, PATH_Y)['y'] + 10 * bent + 2 * pant * bent,
                 ly=-0.4 * smooth(D3 + 3.2, D3 + 3.4, T))
    else:
        p = D3_GAIT2.pose(T)
        p.update(mopen=0.0, smile=-0.2, sweat=0.8, brow=-8)
    p.update(turn=0.3, eye=blink(T, 1, 3.3))
    RUNNER.draw(c, p, t=T)
    rising_motes(c, T, _d3_hero_chest, [D3 + 3.3])


def _d3_hero_chest(T):
    if T < D3 + 3.65:
        return (1072.0, stand_feet(1060, PATH_Y)['y'] - 70)
    q = D3_GAIT2.pose(T)
    return to_world(q, (14, -66))


D3_CAM = Curve([(0.0, 620.0), (2.3, 980.0), (3.6, 1000.0), (4.0, 1080.0)])


def cam_day3(t):
    return (D3_CAM(t), 640 + noise1(t * 0.5, 61) * 3, 1.25, 0.0)


# DAY 12: push-ups on the bedroom floor, alone; the old man's place at the end of the bed is empty
def pushup(T, x, floor, rate=0.75, phase=0.0, depth=1.0, shaky=0.0, facing=1, scale=1.0):
    """A push-up rotating about the toes. Returns a pose with IK hands on the floor."""
    cyc = 0.5 - 0.5 * math.cos(2 * math.pi * (T * rate + phase))      # 0 up .. 1 down
    phi = math.radians(26 - 17 * cyc * depth + shaky * 2.5 * math.sin(T * 23))
    toes = (x, floor - 9 * scale)
    L = 114 * scale
    hip = (toes[0] + facing * L * math.cos(phi), toes[1] - L * math.sin(phi))
    rot = facing * (90 - math.degrees(phi))
    p = dict(x=hip[0], y=hip[1], rot=rot, facing=facing, scale=scale, turn=0.3, hb=4, kb=2, hf=2, kf=2, tilt=10,
             ly=0.6)
    sh = to_world(p, (0, -(100 - 16)))
    hand = (sh[0] + facing * 6 * scale, floor - 8 * scale)
    p['hand_f'] = to_local_pose(p, hand)
    p['hand_b'] = to_local_pose(p, (hand[0] - facing * 10 * scale, hand[1]))
    p['ik_f'] = p['ik_b'] = -1.0
    p['_cyc'] = cyc
    return p


def day12(c, t, T):
    def hero(cc, TT, rim_pass=False):
        p = pushup(TT, 1470, FLOOR + 10, rate=0.8, shaky=1.0, facing=-1)
        p.update(sweat=0.9, mopen=0.0, smile=-0.25, brow=-8, eye=blink(TT, 1, 3.3))
        RUNNER.draw(cc, p, t=TT)
        return p

    R = Room(light='day', sky='day', curtain=1.0, ambient='#F1E8DC', hero=hero, back=cane_on_floor)
    R.after = lambda cc, TT: rising_motes(cc, TT, _d12_hero_chest, D12_PULSES, drift=(-90.0, -360.0))
    draw_room(c, T, R)


D12_PULSES = [115.15, 116.25, 117.5, 118.4]


def _d12_hero_chest(T):
    p = pushup(T, 1470, FLOOR + 10, rate=0.8, shaky=1.0, facing=-1)
    return to_world(p, (14, -70))


cam_day12 = CamPath([(0.0, (1190, 720, 1.6)), (4.0, (1206, 716, 1.66))], handheld=4, seed=62)


# DAY 30: the phone goes in the drawer, the lamp goes off; the old man tucks his feet in
HAND30 = Curve([(119.25, (700.0, 770.0)), (119.6, (500.0, 790.0)), (120.4, (500.0, 790.0), 'stop'),
                (120.7, (474.0, 716.0)), (121.0, (474.0, 716.0), 'stop'), (121.45, (700.0, 770.0))])


def day30(c, t, T):
    d0 = EV['drawer']
    drawer = smooth(d0 - 0.7, d0 - 0.4, T) * (1 - smooth(d0, d0 + 0.3, T))
    lamp = 1 - smooth(120.9, 121.0, T)
    phone_in_hand = T < d0 - 0.25

    def hero(cc, TT, rim_pass=False):
        reach = smooth(119.3, 119.6, TT) * (1 - smooth(120.5, 120.8, TT))
        p = lying_pose(TT, phone=False, face=dict(eye=(1 - 0.8 * smooth(121.4, 122.2, TT)) * blink(TT, 1, 3.4),
                                                    smile=0.15 + 0.15 * smooth(121.4, 122.2, TT)), swipes=[])
        p['back_arm_late'] = True
        p['hand_f'] = to_local_pose(p, HAND30(TT))
        p['ik_f'] = -1.0
        quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 130, lying_blanket_contour(p)))
        HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        if phone_in_hand or (TT < d0 and reach > 0.5):
            hand = to_world(p, p['hand_f'])
            phone_side(cc, hand[0], hand[1] - 20, 30, TT, 0.9, on=True, swipes=[])
        return p

    R = Room(light='night', sky='night', curtain=0.86, lamp=lamp, drawer=drawer, hero=hero, back=cane_on_floor)
    draw_room(c, T, R)


cam_day30 = CamPath([(0.0, (760, 690, 1.55)), (4.0, (800, 690, 1.6))], handheld=3, seed=63)


# DAY 48: reading at the desk
def day48(c, t, T):
    def back(cc, TT):
        from common import chair
        chair(cc, 250, facing=1)

    def hero(cc, TT, rim_pass=False):
        hip = (250, 762)
        p = dict(x=hip[0], y=hip[1], facing=1, turn=0.3, foot_f=(42, FLOOR - 9 - hip[1] - 1),
                 foot_b=(30, FLOOR - 9 - hip[1] - 1), ikl_f=-1.0, ikl_b=-1.0, lean=12, tilt=14, ly=0.7, lx=0.4,
                 eye=blink(TT, 1, 3.6), breathe=breath(TT, 0.25, 0.8, 1), smile=0.1)
        p['hand_f'] = to_local_pose(p, (330, 706))
        p['hand_b'] = to_local_pose(p, (300, 708))
        p['ik_f'] = p['ik_b'] = 1.0
        page = int((TT - 123.0) / 1.3)
        cc.drawRRect(rrect(290, 700, 90, 12, 3), paint('#F4EFE6'))
        cc.drawRRect(rrect(290, 700, 90, 12, 3), paint('outline', stroke=3))
        HERO.draw(cc, p, t=TT)
        return p

    R = Room(light='day', sky='day', curtain=1.0, ambient='#F1E8DC', hero=hero, back=back, books=True)
    draw_room(c, T, R)


cam_day48 = CamPath([(0.0, (200, 640, 1.55)), (4.0, (212, 636, 1.62))], handheld=3, seed=64)


# DAY 77: he runs further and faster, alone
D77 = EV['days'][4]
D77_HERO = Curve([(D77 - 1.0, 0.0), (D77 + 9.0, 3300.0)])
G77_H = Gait(D77_HERO, D77 - 1.0, D77 + 9.0, PATH_Y, step=120, run=True, lean=9, arm=34, lift=13)


def day77(c, t, T):
    cx = cam_day77(t)[0]
    river_path(c, T, cx, 'golden')
    p = G77_H.pose(T)
    p.update(turn=0.3, eye=blink(T, 1, 3.3), smile=0.2 + 0.25 * smooth(D77 + 2.0, D77 + 3.0, T), mopen=0.0)
    RUNNER.draw(c, p, t=T)
    rising_motes(c, T, lambda TT: to_world(G77_H.pose(TT), (14, -66)), [D77 + 3.2, D77 + 6.0], n=18)


D77_CAM = Curve([(0.0, 700.0), (3.6, 1880.0), (5.0, 2290.0), (8.0, 3200.0)])


def cam_day77(t):
    T = D77 + t
    z = 1.3 - 0.18 * smooth(3.6, 4.6, t)
    hx = D77_HERO(T)
    cx = hx + 260 + 120 * smooth(3.6, 4.6, t)
    return (cx, 640 + noise1(t * 0.5, 66) * 3, z, 0.0)


# --- the last temptation (135-145) ---------------------------------------------------------------------------------------

def temptation(c, t, T):
    up = smooth(EV['up_through'], EV['up_through'] + 0.75, T)
    speak = 0.0                      # he doesn't say it out loud: the caption carries it
    look = smooth(EV['look_spot'], EV['look_spot'] + 0.4, T)

    def hero(cc, TT, rim_pass=False):
        from common import sit_blanket_contour, sit_up_pose
        face = dict(eye=(0.35 + 0.5 * smooth(136.0, 136.6, TT) - 0.25 * smooth(139.0, 140.0, TT)
                         + 0.4 * look) * blink(TT, 1, 3.4),
                    lx=0.3 + 0.7 * look, ly=-0.3 + 0.75 * look, brow=-12 * smooth(EV['he_doesnt'] - 0.4, EV['he_doesnt'], TT), mopen=speak,
                    smile=0.0)
        from common import quilt_contour
        lie = lying_pose(TT, phone=False, face=face, swipes=[])
        lie['hand_f'] = to_local_pose(lie, (700, 770))
        lie['ik_f'] = -1.0
        if up <= 0:
            p = lie
        else:
            sit = sit_up_pose(TT, up, face=face)
            sit['hand_f'] = (52, -26)
            sit['ik_f'] = -1.0
            p = blend(lie, sit, min(1.0, up * 1.6))
        p['back_arm_late'] = True
        quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 130 + 70 * up, quilt_contour(p, up)))
        if rim_pass:
            from common import under_quilt
            cc.save()
            under_quilt(cc, p['x'] - 130 + 70 * up, quilt_contour(p, up))
            HERO.draw(cc, p, t=TT)
            cc.restore()
        else:
            HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        return p

    def spot(cc, TT):
        # where the old man used to sit every night: nobody. His stick on the floor, the boy's shoes beside it.
        cane_on_floor(cc)
        sneaker(cc, 1060, FLOOR - 9, 1.0, 1)
        sneaker(cc, 1112, FLOOR - 9, 1.0, 1)

    ring = 1.0 - smooth(143.0, 143.1, T)
    R = Room(light='rain', sky='rain', curtain=0.86, hero=hero, front=spot, stand_phone=(ring, False),
             ambient='#3E465C')
    R.lights_extra = lambda cc: (pool(cc, 1050, 800, 420, 300, '#B4C4E8', 0.6),
                                 pool(cc, 1000, 880, 300, 120, '#C9D6FF', 0.4))

    def after(cc, TT):
        from act1 import _buzz
        _buzz(cc, TT, ring)
        if TT < EV['shade_gone']:
            eye = smooth(EV['shade_rises'], EV['shade_rises'] + 0.4, TT)
            lean = 22 * smooth(EV['shade_rises'], EV['shade_rises'] + 1.0, TT)
            shade_emissive(cc, TT, 452 + 22 * smooth(137.0, 138.0, TT), 792, lean=lean, eye=eye, scale=1.22)
        else:
            def body(c2):
                shade_emissive(c2, EV['shade_gone'], 474, 792, lean=22, eye=1.0, scale=1.22)
            dissolve(cc, body, (360, 420, 700, 900), TT, EV['shade_gone'], dur=1.9, seed=9, smoke='#2A0A0A',
                     smoke_a=0.7, rise=240)
    R.after = after
    draw_room(c, T, R)
    w = WHISPERS[7]
    whisper(c, T, w[0], w[1], w[2], 560, 520, 64, seed=70)


# his eyes go to the end of the bed, the camera follows them: the old man's place is empty, his stick on the
# floor, the running shoes beside it. And back.
cam_temptation = CamPath([(0.0, (640, 660, 2.0)), (5.3, (650, 664, 2.15)), (5.6, (652, 664, 2.15)),
                          (6.1, (1010, 744, 1.95)), (6.75, (1016, 746, 2.0)), (7.2, (680, 666, 2.15)),
                          (8.2, (700, 668, 2.2)), (8.6, (820, 660, 1.6)), (10.0, (840, 660, 1.55))],
                         handheld=4, seed=71)


def sneaker(c, x, y, s=1.0, facing=1):
    """A white running shoe, side on, hanging by its laces."""
    c.save()
    c.translate(x, y)
    c.scale(s * facing, s)
    body = skia.Path()
    body.moveTo(-26, 8)
    body.lineTo(-26, -14)
    body.cubicTo(-18, -20, -6, -18, 2, -10)
    body.cubicTo(12, -4, 26, -2, 30, 6)
    body.lineTo(30, 10)
    body.close()
    c.drawPath(body, paint('#ECE9E2'))
    c.drawRRect(rrect(-28, 6, 60, 9, 4), paint('#D6A23D'))
    c.drawPath(body, paint('outline', stroke=3.5))
    c.drawRRect(rrect(-28, 6, 60, 9, 4), paint('outline', stroke=3))
    c.drawLine(-12, -6, 6, -2, paint('#3F6E8C', stroke=3))
    c.restore()


# --- quick days (145-153) ----------------------------------------------------------------------------------------------

def run_pair(t0, mood, weather=None, dur=2.0):
    hero_x = Curve([(t0 - 1.0, 0.0), (t0 + dur + 1.0, (dur + 2.0) * 470)])
    gh = Gait(hero_x, t0 - 1.0, t0 + dur + 1.0, PATH_Y, step=124, run=True, lean=10, arm=36, lift=14)

    def draw(c, t, T):
        cx = hero_x(T) + 120
        river_path(c, T, cx, mood)
        p2 = gh.pose(T)
        p2.update(turn=0.3, smile=0.3, mopen=0.0, eye=blink(T, 1, 3.3))
        RUNNER.draw(c, p2, t=T)
        if weather == 'rain':
            rainfall(c, cx - 1100, -200, cx + 1100, 1200, T, n=160, a=0.45)
        elif weather == 'snow':
            snowfall(c, cx - 1100, -200, cx + 1100, 1200, T, n=140, a=0.85)
            u = ((T * 1.3 + 0.4) % 1.0)
            hx_, hy_ = p2['x'] + 80, p2['y'] - 150
            c.drawCircle(hx_ + 50 * u, hy_ - 6 * u, 8 + 18 * u, paint('#FFFFFF', 0.35 * (1 - u), blur=6))
        elif weather == 'leaves':
            falling_leaves(c, cx - 1100, -200, cx + 1100, 1100, T, n=40)

    def cam(t):
        T = t0 + t
        return (hero_x(T) + 120, 640, 1.22, 0.0)
    return draw, cam


def day330(c, t, T):
    def hero(cc, TT, rim_pass=False):
        p = pushup(TT, 1190, FLOOR + 10, rate=1.0)
        p.update(sweat=0.4, smile=0.3, eye=blink(TT, 1, 3.3))
        RUNNER.draw(cc, p, t=TT)
        return p

    R = Room(light='day', sky='day', curtain=1.0, ambient='#F1E8DC', hero=hero)
    draw_room(c, T, R)


cam_day330 = CamPath([(0.0, (1290, 760, 1.6)), (2.0, (1296, 756, 1.66))], handheld=3, seed=72)


# --- the trailhead (153-157) ---------------------------------------------------------------------------------------------

def headlamp(c, p, j, T, a=1.0, reach=520, spread=0.33):
    """A lamp on the forehead and its beam ahead (world coords)."""
    hx_, hy_ = to_world(p, j['head'])
    fx = p.get('facing', 1)
    ang = math.radians(p.get('lean', 0) + p.get('tilt', 0)) * fx
    d = (fx * math.cos(ang), math.sin(ang) + 0.18)
    lx, ly = hx_ + fx * 50, hy_ - 30
    beam = skia.Path()
    beam.moveTo(lx, ly)
    nx, ny = -d[1], d[0]
    ex, ey = lx + d[0] * reach, ly + d[1] * reach
    beam.lineTo(ex + nx * reach * spread, ey + ny * reach * spread)
    beam.lineTo(ex - nx * reach * spread, ey - ny * reach * spread)
    beam.close()
    sh = skia.GradientShader.MakeLinear(points=[(lx, ly), (ex, ey)],
                                        colors=[skia.Color(255, 244, 214, int(110 * a)), skia.Color(255, 244, 214, 0)])
    pp = skia.Paint(AntiAlias=True, Shader=sh, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    pp.setBlendMode(skia.BlendMode.kPlus)
    c.drawPath(beam, pp)
    c.drawCircle(lx, ly, 9, paint('#FFF4D6', a))
    c.drawCircle(lx, ly, 22, paint('#FFF4D6', 0.5 * a, blur=10, blend='add'))


def strap_layer(color='#2B2E36'):
    def behind(c, j):
        hip, neck = j['hip'], j['neck']
        bx = (hip[0] + neck[0]) / 2 - 46
        by = (hip[1] + neck[1]) / 2 - 6
        c.drawRRect(rrect(bx - 30, by - 50, 60, 100, 18), paint(color))
        c.drawRRect(rrect(bx - 30, by - 50, 60, 100, 18), paint('outline', stroke=4))
    return behind


def headband_lamp(c, j):
    hx_, hy_ = j['head']
    c.drawLine(hx_ - 50, hy_ - 34, hx_ + 54, hy_ - 30, paint('outline', stroke=12))
    c.drawLine(hx_ - 50, hy_ - 34, hx_ + 54, hy_ - 30, paint('#2B2E36', stroke=7))
    c.drawRRect(rrect(hx_ + 44, hy_ - 44, 18, 22, 5), paint('#3B3E46'))
    c.drawRRect(rrect(hx_ + 44, hy_ - 44, 18, 22, 5), paint('outline', stroke=3))


TH_WALK_H = Curve([(EV['set_off'], 880.0), (EV['set_off'] + 1.6, 1460.0)])
G_TH_H = Gait(TH_WALK_H, EV['set_off'], EV['set_off'] + 1.6, PATH_Y, step=92, lean=6, arm=20)


def trailhead_shot(c, t, T):
    trailhead(c, T)
    up = smooth(154.9, 155.4, T) * (1 - smooth(155.6, 156.0, T))         # he looks up at the mountain
    ph = G_TH_H.pose(T) if T > EV['set_off'] else stand_feet(880, PATH_Y, 1.0, 1)
    strap = smooth(153.4, 153.8, T) * (1 - smooth(154.6, 155.0, T))
    ph.update(turn=0.3, eye=blink(T, 1, 3.4), smile=0.15 + 0.2 * smooth(155.3, 155.8, T),
              tilt=ph.get('tilt', 0) - 10 * up, ly=-0.6 * up, lx=0.6)
    if strap > 0 and T < EV['set_off']:
        ph['hand_f'] = (16, -78)
        ph['hand_b'] = (6, -70)
        ph['ik_f'] = ph['ik_b'] = 1.0
    jh = HIKER.draw(c, ph, layers={'behind': strap_layer(), 'over_head': headband_lamp}, t=T)
    headlamp(c, ph, jh, T)


cam_trailhead = CamPath([(0.0, (860, 640, 1.3)), (4.0, (940, 630, 1.24))], handheld=3, seed=81)


# --- assemble -------------------------------------------------------------------------------------------------------------

def shots():
    d = EV['days']
    q = EV['quick_days']
    rain_d, rain_c = run_pair(q[0], 'rain', 'rain')
    leaf_d, leaf_c = run_pair(q[1], 'autumn', 'leaves')
    snow_d, snow_c = run_pair(q[2], 'snow', 'snow')
    return [
        Shot(EV['dawn'], EV['strike'] - 0.2, dawn_look, cam_dawn_look, name='dawn_look'),
        Shot(EV['strike'] - 0.2, 97.0, day_one, cam_day_one, name='day_one'),
        Shot(97.0, 102.0, curtains_shot, cam_curtains, name='curtains'),
        Shot(102.0, EV['out'], stand_shot, cam_stand, name='stand'),
        Shot(EV['out'], d[0], out_shot, cam_out, name='out'),
        Shot(d[0], d[1], day3, cam_day3, name='day3'),
        Shot(d[1], d[2], day12, cam_day12, name='day12'),
        Shot(d[2], d[3], day30, cam_day30, name='day30'),
        Shot(d[3], d[4], day48, cam_day48, name='day48'),
        Shot(d[4], EV['temptation'], day77, cam_day77, name='day77'),
        Shot(EV['temptation'], EV['drop'], temptation, cam_temptation, name='temptation'),
        Shot(q[0], q[1], rain_d, rain_c, name='day180'),
        Shot(q[1], q[2], leaf_d, leaf_c, name='day240'),
        Shot(q[2], q[3], snow_d, snow_c, name='day300'),
        Shot(q[3], EV['trailhead'], day330, cam_day330, name='day330'),
        Shot(EV['trailhead'], EV['ascent'], trailhead_shot, cam_trailhead, name='trailhead'),
    ]
