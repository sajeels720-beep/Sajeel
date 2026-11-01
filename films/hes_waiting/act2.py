"""Act 2 (1:32-2:37): Day 1, the year that changes the old man, the last temptation, and the trailhead."""
from __future__ import annotations

import math
from dataclasses import replace

import skia

from act1 import OLD_X, corner_eyes, hero_in_bed, old_on_bed, shade_emissive, sitting_hero, to_local_pose
from common import (BED, DOOR, FLOOR, HERO, HERO_LOOK, LIE_HIP, MATT, NIGHTSTAND, SHADE, WINDOW, Character, Room,
                    blanket, cane, draw_room, in_world, lying_blanket_contour, lying_pose, old_face, old_man,
                    phone_side, pocket_watch, sit_edge_pose, to_world, vitality)
from cues import EV, SPEECH, WHISPERS
from engine.captions import whisper
from engine.core import H, W, clamp, hrand, hrange, noise1, smooth
from engine.draw import mixc, oval, paint, poly, rrect, text
from engine.fx import dissolve, falling_leaves, rainfall, snowfall
from engine.light import pool
from engine.motion import CamPath, Curve, Gait, blend, breath, settle, stand_feet
from engine.render import Shot
from engine.rig import blink
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


# --- 1. Day 1: dawn, he never slept (92.6-97) ------------------------------------------------------------------------

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


def dawn_sit(c, t, T):
    R = Room(light='dawn', sky='dawn', curtain=0.0, ambient='#4E587E',
             hero=sitting_hero(lambda TT: 1.0, lambda TT: dict(lx=0.9, ly=0.3, brow=-4, eye=0.9 * blink(TT, 1, 3.4),
                                                               bags=1.0), phone_dead=0.0),
             old=old_slumped_dawn(0.0), old_rim=0.35)
    R.lights_extra = lambda cc: pool(cc, 1285, 450, 300, 300, '#FFB27A', 0.35)
    draw_room(c, T, R)


cam_dawn = CamPath([(0.0, (860, 690, 1.5)), (4.4, (880, 694, 1.62))], handheld=3, seed=51)


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
        sit = sit_edge_pose(OLD_X, TT, v, head_up=0.6, look=0.9)
        sit['hand_f'] = (40, -10)
        st = old_standing(OLD_X - 40, TT, v, facing=-1, face=dict(lx=0.6, smile=0.15))
        p = sit_to_stand(TT, EV['rise'] + 0.3, 1.5, sit, st)
        j = old_man(v).draw(cc, p, t=TT)
        up = smooth(EV['rise'] + 0.3, EV['rise'] + 1.8, TT)
        hand = to_world(p, j['hand_f'])
        lean_tip = (OLD_X + 92, FLOOR - 2)
        planted = (hand[0] - 18, FLOOR - 2)
        tip = (lean_tip[0] + (planted[0] - lean_tip[0]) * up, FLOOR - 2)
        top = (OLD_X + 74 + (hand[0] - OLD_X - 74) * up, MATT - 70 + (hand[1] - MATT + 70) * up)
        cane(cc, top, tip)
        return p

    R = Room(light='day', sky='dawn', curtain=1.0, warm=0.8, ambient='#E9D6C2', hero=hero, old=old)
    R.lights_extra = lambda cc: _sunbeam(cc, 1.0)
    draw_room(c, T, R)


cam_stand = CamPath([(0.0, (870, 690, 1.55)), (5.0, (890, 670, 1.5))], handheld=4, seed=53)


# --- 4. out of the door (107-111) ---------------------------------------------------------------------------------------

OUT_WALK = Curve([(107.9, 800.0), (108.9, 1010.0)])
OUT_RUN = Curve([(109.1, 1010.0), (111.2, 1880.0, 'smooth')])
GAIT_OUT = Gait(OUT_WALK, 107.9, 108.9, PATH_Y, step=88)
RUN_OUT = Gait(OUT_RUN, 109.1, 111.2, PATH_Y, step=118, run=True, lean=9, arm=34, lift=13, blend_steps=0.3)


def out_shot(c, t, T):
    door = smooth(EV['door_open'], EV['door_open'] + 0.4, T)
    street_dawn(c, T, cam_x=960, warm=0.3, door_open=door)
    v = vitality(T)
    if T >= 108.5:
        a = smooth(108.5, 109.0, T)
        p = old_standing(820, T, v, facing=1, face=dict(lx=1.0, smile=0.1 + 0.3 * smooth(109.6, 110.6, T)))
        p['alpha'] = a
        if T > 110.0:
            p['hand_b'] = (30, -60 - 30 * smooth(110.0, 110.4, T))
            p['ik_b'] = 1.0
        draw_old_standing(c, p, T, v)
    if T >= EV['door_open'] + 0.2:
        if T < 109.1:
            p = GAIT_OUT.pose(T)
        else:
            p = RUN_OUT.pose(T)
        p.update(turn=0.3, eye=blink(T, 1, 3.3), mopen=0.15 if T > 108.9 else 0.0)
        RUNNER.draw(c, p, t=T)
        # breath in the cold air
        for k in range(4):
            t0 = 108.0 + k * 0.7
            u = (T - t0) / 1.1
            if 0 < u < 1:
                hp = (p['x'] + 70, p['y'] - 150)
                c.drawCircle(hp[0] + 60 * u, hp[1] - 10 * u, 10 + 22 * u, paint('#FFFFFF', 0.35 * (1 - u), blur=6))


cam_out = CamPath([(0.0, (960, 640, 1.08)), (4.0, (1040, 640, 1.08))], handheld=3, seed=54)


# --- the montage ----------------------------------------------------------------------------------------------------------

def track(cam_curve, y=600, z=1.15, seed=0, hh=3):
    def cam(t):
        return (cam_curve(t), y + noise1(t * 0.4, seed) * hh, z, 0.0)
    return cam


# DAY 3: he runs out of breath; the old man catches up with his stick
D3 = EV['days'][0]
D3_GAIT1 = Gait(Curve([(D3 - 1.4, 0.0), (D3 + 2.3, 1060.0, 'stop')]), D3 - 1.4, D3 + 2.3, PATH_Y, step=104,
                run=True, lean=8, arm=26, lift=10, duty=0.4, blend_steps=0.25)
D3_GAIT2 = Gait(Curve([(D3 + 3.65, 1060.0), (D3 + 4.6, 1420.0)]), D3 + 3.65, D3 + 4.6, PATH_Y, step=104, run=True,
                lean=8, arm=26, lift=10, blend_steps=0.25)
D3_OLD = Curve([(D3 + 0.6, 560.0), (D3 + 3.2, 900.0)])
D3_OLD_GAIT = Gait(D3_OLD, D3 + 0.6, D3 + 3.2, PATH_Y, step=44, lift=8, arm=6, lean=2)


def day3(c, t, T):
    cx = cam_day3(t)[0]
    river_path(c, T, cx, 'dawn')
    v = vitality(T)
    # the old man, shuffling in on his stick
    if T > D3 + 0.6:
        p = D3_OLD_GAIT.pose(T)
        p.update(old_face(v, T))
        p.update(lean=p.get('lean', 0) + 18, tilt=8, turn=0.3, lx=0.6)
        tap = [D3 + 3.2, D3 + 3.5]
        j = old_man(v).draw(c, p, t=T)
        hand = to_world(p, j['hand_f'])
        lift = sum(14 * math.sin(math.pi * clamp((T - t0) / 0.25)) for t0 in tap)
        cane(c, (hand[0], hand[1] - lift), (hand[0] + 18, PATH_Y - 2 - lift))
    # the boy
    if T < D3 + 2.3:
        p = D3_GAIT1.pose(T)
        p.update(mopen=0.3, sweat=0.8, brow=-6)
    elif T < D3 + 3.65:
        bent = smooth(D3 + 2.3, D3 + 2.6, T) * (1 - smooth(D3 + 3.45, D3 + 3.65, T))
        p = D3_GAIT1._stand(1060.0)            # the same stance the run stops in and starts from
        pant = math.sin((T - D3) * 14)
        p.update(lean=48 * bent, tilt=10 * bent - 14 * smooth(D3 + 3.3, D3 + 3.5, T), mopen=0.35 + 0.15 * pant,
                 sweat=1.2, brow=-10, hand_f=(40 * bent + 4, 30 * bent), hand_b=(30 * bent, 36 * bent),
                 ik_f=-1.0, ik_b=-1.0, y=stand_feet(1060, PATH_Y)['y'] + 10 * bent + 2 * pant * bent,
                 lx=-0.6 * smooth(D3 + 3.2, D3 + 3.4, T))
    else:
        p = D3_GAIT2.pose(T)
        p.update(mopen=0.2, sweat=0.8, brow=-8)
    p.update(turn=0.3, eye=blink(T, 1, 3.3))
    RUNNER.draw(c, p, t=T)


D3_CAM = Curve([(0.0, 620.0), (2.3, 980.0), (3.6, 1000.0), (4.0, 1080.0)])


def cam_day3(t):
    return (D3_CAM(t), 640 + noise1(t * 0.5, 61) * 3, 1.25, 0.0)


# DAY 12: push-ups on the bedroom floor; the old man counts them with a nod
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
        p.update(sweat=0.9, mopen=0.2 + 0.2 * p['_cyc'], brow=-8, eye=blink(TT, 1, 3.3))
        RUNNER.draw(cc, p, t=TT)
        return p

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        p = sit_edge_pose(OLD_X, TT, v, head_up=0.7, look=0.8)
        nod = 0.5 - 0.5 * math.cos(2 * math.pi * TT * 0.8)
        p.update(tilt=p['tilt'] + 7 * nod, smile=0.2, hand_f=(40, -10))
        old_man(v).draw(cc, p, t=TT)
        cane(cc, (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2))
        return p

    R = Room(light='day', sky='day', curtain=1.0, ambient='#F1E8DC', hero=hero, old=old)
    draw_room(c, T, R)


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

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        tuck = smooth(EV['tuck'], EV['tuck'] + 0.6, TT) * (1 - smooth(EV['tuck'] + 1.3, EV['tuck'] + 1.8, TT))
        p = sit_edge_pose(OLD_X, TT, v, head_up=0.75, look=0.9)
        p.update(smile=0.25, hand_f=(40, -10))
        if tuck > 0:
            p['hand_f'] = to_local_pose(p, (OLD_X - 90 - 30 * tuck, MATT - 30 + 10 * tuck))
            p['ik_f'] = 1.0
            p['lean'] += 14 * tuck
        old_man(v).draw(cc, p, t=TT)
        return p

    R = Room(light='night', sky='night', curtain=0.86, lamp=lamp, drawer=drawer, hero=hero, old=old, old_rim=0.5)
    draw_room(c, T, R)


cam_day30 = CamPath([(0.0, (760, 690, 1.55)), (4.0, (800, 690, 1.6))], handheld=3, seed=63)


# DAY 48: reading at the desk, the old man reading over his shoulder
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

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        p = old_standing(20, TT, v, facing=1, face=dict(lx=0.8, ly=0.5, smile=0.35))
        nod = smooth(125.0, 125.3, TT) * (1 - smooth(125.5, 125.9, TT))
        p.update(lean=p['lean'] + 4, tilt=p['tilt'] + 6 + 10 * nod)
        draw_old_standing(cc, p, TT, v)
        return p

    R = Room(light='day', sky='day', curtain=1.0, ambient='#F1E8DC', hero=hero, old=old, back=back, books=True)
    draw_room(c, T, R)


cam_day48 = CamPath([(0.0, (200, 640, 1.55)), (4.0, (212, 636, 1.62))], handheld=3, seed=64)


# DAY 77: he looks back, and the old man is jogging behind him
D77 = EV['days'][4]
D77_HERO = Curve([(D77 - 1.0, 0.0), (D77 + 9.0, 3300.0)])
D77_OLD = Curve([(D77 - 1.0, -380.0), (D77 + 9.0, 2980.0)])
G77_H = Gait(D77_HERO, D77 - 1.0, D77 + 9.0, PATH_Y, step=120, run=True, lean=9, arm=34, lift=13)
G77_O = Gait(D77_OLD, D77 - 1.0, D77 + 9.0, PATH_Y, step=104, run=True, lean=7, arm=26, lift=10)


def day77(c, t, T):
    cx = cam_day77(t)[0]
    river_path(c, T, cx, 'golden')
    v = vitality(T)
    look = smooth(EV['jog_look'], EV['jog_look'] + 0.3, T) * (1 - smooth(EV['jog_look'] + 1.6, EV['jog_look'] + 2.0, T))
    smile = smooth(EV['jog_look'] + 0.5, EV['jog_look'] + 1.0, T)
    p = G77_O.pose(T)
    p.update(old_face(v, T))
    wave = smooth(EV['wave'], EV['wave'] + 0.3, T) * (1 - smooth(EV['wave'] + 1.0, EV['wave'] + 1.4, T))
    p.update(turn=0.3, smile=0.45 + 0.2 * wave, eye=0.9 * blink(T, 2, 3.8), mopen=0.12)
    if wave > 0:
        p['sf'] = 150 * wave + p['sf'] * (1 - wave)
        p['ef'] = 20 + 20 * math.sin(T * 14) * wave
    old_man(v, run=True).draw(c, p, t=T)
    p = G77_H.pose(T)
    p.update(turn=0.3 - 0.35 * look, lx=-1.0 * look, tilt=-6 * look, eye=blink(T, 1, 3.3),
             smile=0.2 + 0.5 * smile * look, mopen=0.1)
    RUNNER.draw(c, p, t=T)


D77_CAM = Curve([(0.0, 700.0), (3.6, 1880.0), (5.0, 2290.0), (8.0, 3200.0)])


def cam_day77(t):
    T = D77 + t
    z = 1.3 - 0.18 * smooth(3.6, 4.6, t)
    hx = D77_HERO(T)
    ox = D77_OLD(T)
    reveal = smooth(3.6, 4.6, t)
    cx = hx + 520 + (((hx + ox) / 2) - (hx + 520)) * reveal
    return (cx, 640 + noise1(t * 0.5, 66) * 3, z, 0.0)


# --- the last temptation (135-145) ---------------------------------------------------------------------------------------

def temptation(c, t, T):
    up = smooth(EV['up_through'], EV['up_through'] + 0.75, T)
    speak = 0.0
    for text_, t0, t1, who in SPEECH:
        if who == 'hero' and t0 <= T <= t1:
            speak = 0.2 + 0.25 * abs(math.sin((T - t0) * 10))
    look = smooth(EV['look_door'], EV['look_door'] + 0.4, T)

    def hero(cc, TT, rim_pass=False):
        from common import sit_blanket_contour, sit_up_pose
        face = dict(eye=(0.35 + 0.5 * smooth(136.0, 136.6, TT) - 0.25 * smooth(139.0, 140.0, TT)
                         + 0.4 * look) * blink(TT, 1, 3.4),
                    lx=0.3 + 0.7 * look, ly=-0.3 + 0.5 * look, brow=-12 * smooth(141.4, 141.8, TT), mopen=speak,
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

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        p = old_standing(DOOR[0] + 70, TT, v, facing=-1, run=True,
                         face=dict(lx=0.9, smile=0.15 + 0.35 * smooth(143.4, 144.0, TT), eye=0.95 * blink(TT, 2, 4.0)))
        hold = (DOOR[0] + 70 - 64, 712)
        p['hand_f'] = to_local_pose(p, hold)
        p['hand_b'] = to_local_pose(p, (hold[0] + 10, hold[1] + 4))
        p['ik_f'] = p['ik_b'] = 1.0
        p['lean'] = 2
        old_man(v, run=True).draw(cc, p, t=TT)
        for k, dx in enumerate((-10, 12)):
            sw = 6 * math.sin(TT * 2.2 + k)
            cc.drawLine(hold[0] + dx * 0.3, hold[1], hold[0] + dx + sw, hold[1] + 44, paint('#ECE9E2', stroke=2.5))
            sneaker(cc, hold[0] + dx + sw, hold[1] + 62, 0.9, -1)
        return p

    ring = 1.0 - smooth(143.0, 143.1, T)
    R = Room(light='rain', sky='rain', curtain=0.86, hero=hero, old=old, stand_phone=(ring, False), ambient='#3E465C',
             old_rim=0.5, door_open=0.55, door_light=0.85)
    R.lights_extra = lambda cc: (pool(cc, DOOR[0] + 90, 700, 300, 380, '#FFC98A', 0.75),
                                 pool(cc, DOOR[0] + 20, 760, 200, 300, '#FFD9A0', 0.4))

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


cam_temptation = CamPath([(0.0, (640, 660, 2.0)), (5.3, (650, 664, 2.15)), (5.45, (650, 664, 2.15)),
                          (5.8, (1500, 640, 2.0)), (6.6, (1520, 640, 2.05)), (6.95, (680, 666, 2.15)),
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
    old_x = Curve([(t0 - 1.0, -260.0), (t0 + dur + 1.0, (dur + 2.0) * 470 - 230)])
    gh = Gait(hero_x, t0 - 1.0, t0 + dur + 1.0, PATH_Y, step=124, run=True, lean=10, arm=36, lift=14)
    go = Gait(old_x, t0 - 1.0, t0 + dur + 1.0, PATH_Y, step=118, run=True, lean=9, arm=32, lift=13)

    def draw(c, t, T):
        cx = (hero_x(T) + old_x(T)) / 2 + 40
        river_path(c, T, cx, mood)
        v = vitality(T)
        p = go.pose(T)
        p.update(old_face(v, T))
        p.update(turn=0.3, smile=0.5, mopen=0.15, eye=0.95 * blink(T, 2, 3.6))
        old_man(v, run=True).draw(c, p, t=T)
        p2 = gh.pose(T)
        p2.update(turn=0.3, smile=0.3, mopen=0.15, eye=blink(T, 1, 3.3))
        RUNNER.draw(c, p2, t=T)
        if weather == 'rain':
            rainfall(c, cx - 1100, -200, cx + 1100, 1200, T, n=160, a=0.45)
            for who in (p, p2):
                for side in ('f', 'b'):
                    pass
        elif weather == 'snow':
            snowfall(c, cx - 1100, -200, cx + 1100, 1200, T, n=140, a=0.85)
            for who, k in ((p, 0), (p2, 1)):
                u = ((T * 1.3 + k * 0.4) % 1.0)
                hx_, hy_ = who['x'] + 80, who['y'] - 150
                c.drawCircle(hx_ + 50 * u, hy_ - 6 * u, 8 + 18 * u, paint('#FFFFFF', 0.35 * (1 - u), blur=6))
        elif weather == 'leaves':
            falling_leaves(c, cx - 1100, -200, cx + 1100, 1100, T, n=40)

    def cam(t):
        T = t0 + t
        cx = (hero_x(T) + old_x(T)) / 2 + 40
        return (cx, 640, 1.22, 0.0)
    return draw, cam


def day330(c, t, T):
    def hero(cc, TT, rim_pass=False):
        p = pushup(TT, 1190, FLOOR + 10, rate=1.0)
        p.update(sweat=0.4, smile=0.3, eye=blink(TT, 1, 3.3))
        RUNNER.draw(cc, p, t=TT)
        return p

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        p = pushup(TT, 1980, FLOOR + 10, rate=1.0, facing=-1)
        p.update(old_face(v, TT))
        p.update(smile=0.55, eye=0.9 * blink(TT, 2, 3.6), turn=0.3)
        old_man(v, run=True).draw(cc, p, t=TT)
        return p

    R = Room(light='day', sky='day', curtain=1.0, ambient='#F1E8DC', hero=hero, old=old)
    draw_room(c, T, R)


cam_day330 = CamPath([(0.0, (1585, 750, 1.42)), (2.0, (1590, 746, 1.47))], handheld=3, seed=72)


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
TH_WALK_O = Curve([(EV['set_off'] + 0.25, 620.0), (EV['set_off'] + 1.85, 1200.0)])
G_TH_H = Gait(TH_WALK_H, EV['set_off'], EV['set_off'] + 1.6, PATH_Y, step=92, lean=6, arm=20)
G_TH_O = Gait(TH_WALK_O, EV['set_off'] + 0.25, EV['set_off'] + 1.85, PATH_Y, step=88, lean=5, arm=18)


def trailhead_shot(c, t, T):
    trailhead(c, T)
    v = vitality(T)
    nod = smooth(EV['nod'], EV['nod'] + 0.25, T) * (1 - smooth(EV['nod'] + 0.45, EV['nod'] + 0.8, T))
    po = G_TH_O.pose(T) if T > EV['set_off'] + 0.25 else old_standing(620, T, v, facing=1)
    po.update(old_face(v, T))
    po.update(turn=0.3, smile=0.5, lx=0.8, tilt=po.get('tilt', 0) + 10 * nod, eye=0.95 * blink(T, 2, 3.8))
    jo = old_man(v, run=False).draw(c, po, layers={'behind': strap_layer('#4A3A2E'), 'over_head': headband_lamp}, t=T)
    hand = to_world(po, jo['hand_f'])
    c.drawLine(hand[0], hand[1] - 30, hand[0] + 26, PATH_Y - 2, paint('outline', stroke=10))
    c.drawLine(hand[0], hand[1] - 30, hand[0] + 26, PATH_Y - 2, paint('#9C7A52', stroke=5))
    ph = G_TH_H.pose(T) if T > EV['set_off'] else stand_feet(880, PATH_Y, 1.0, -1 if T < EV['nod'] + 0.6 else 1)
    strap = smooth(153.4, 153.8, T) * (1 - smooth(154.6, 155.0, T))
    ph.update(turn=0.3, eye=blink(T, 1, 3.4), smile=0.2 + 0.3 * smooth(EV['nod'], EV['nod'] + 0.5, T),
              tilt=ph.get('tilt', 0) + 10 * nod, lx=0.6)
    if strap > 0 and T < EV['set_off']:
        ph['hand_f'] = (16, -78)
        ph['hand_b'] = (6, -70)
        ph['ik_f'] = ph['ik_b'] = 1.0
    jh = HIKER.draw(c, ph, layers={'behind': strap_layer(), 'over_head': headband_lamp}, t=T)
    headlamp(c, po, jo, T)
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
        Shot(EV['dawn'], 97.0, dawn_sit, cam_dawn, name='dawn_sit'),
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
