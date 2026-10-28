"""Act 1 (0:00-1:02): plenty of time, the time-lapse, the quicksand bed, the mountain, the shadow, 5 AM."""
from __future__ import annotations

import math

import skia

from common import (BED_TOP, BED_W, BED_X, CHAIR_X, DESK_TOP, FATHER, HALL_FLOOR, HERO, MOUNTAIN_X, NOTE_SPOTS,
                    PILE_X, ROOM_FLOOR, SEAT_DY, SHADE, STAND_HIP, STAND_X, STOOL_X, FRONT_DOOR, SON_DOOR, blanket,
                    hallway, his_room, lying_head_pose, merge, phone_eyes, phone_feed, seated, standing)
from cues import EV
from engine.captions import whisper
from engine.core import H, W, Track, clamp, hrand, noise1, shake, smooth
from engine.draw import circle, col, light_pool, mixc, oval, paint, poly, rrect, text
from engine.fx import dust_motes, eye_field
from engine.home import alarm_clock, book, digital_clock, lunchbox, shoe, stool
from engine.props import phone
from engine.render import Shot
from engine.rig import blink, idle, walk

HIP = (CHAIR_X + 6, ROOM_FLOOR - SEAT_DY)   # seated at the desk, facing right
BOOK_X = 318                                 # the open book in front of him
PHONE_X = 452                                # where the phone lies on the desk


def open_book(c, x, y, w=150, flip=0.0, h=None):
    """An open book standing in a shallow V on a surface at y, pages toward the camera; flip turns a page."""
    h = h or w * 0.5
    hw = w / 2
    for side in (-1, 1):
        page = poly([(x, y - 2), (x + side * hw, y - 10), (x + side * (hw - 10), y - h), (x, y - h + 12)], True)
        c.drawPath(page, paint('#F1ECE1'))
        c.drawPath(page, paint('outline', stroke=3))
        for k in range(5):
            u = (k + 1) / 6
            yy = y - 12 - (h - 24) * u
            x0 = x + side * 10
            x1 = x + side * (hw - 16 - 6 * u)
            c.drawLine(x0, yy + 3 * (1 - u), x1, yy - 3 + 3 * (1 - u), paint('#9C9586', stroke=2.5))
    c.drawPath(poly([(x - hw - 4, y - 8), (x, y), (x + hw + 4, y - 8), (x + hw + 4, y - 2), (x, y + 4),
                     (x - hw - 4, y - 2)], True), paint('#4F7A6B'))
    if 0 < flip < 1:
        ang = math.pi * flip
        tip = (x + math.cos(ang) * (hw - 6), y - h + 8 - math.sin(ang) * 26)
        pg = poly([(x, y - 2), (tip[0], y - 10 - math.sin(ang) * 20), tip, (x, y - h + 12)], True)
        c.drawPath(pg, paint('#FBF7EE'))
        c.drawPath(pg, paint('outline', stroke=2.5))


def desk_phone(c, x, y, buzz=0.0, glow=0.0, t=0.0):
    """The phone lying flat on the desk; buzz makes it skitter, glow is the screen light leaking out."""
    jx = noise1(t * 90, 2) * 4 * buzz
    if glow > 0:
        light_pool(c, x, y, 120, 40, 'red', 0.5 * glow)
    c.drawRRect(rrect(x - 34 + jx, y - 9, 68, 9, 4), paint('#24262C'))
    c.drawRRect(rrect(x - 34 + jx, y - 9, 68, 9, 4), paint('outline', stroke=3))
    if buzz > 0.05:
        for side in (-1, 1):
            for k in range(2):
                c.drawLine(x + side * (44 + k * 10) + jx, y - 16 - k * 4, x + side * (52 + k * 10) + jx, y - 22 - k * 4,
                           paint('#F4F1EA', 0.8 * buzz, stroke=3))


def buzzing(T, times, dur=0.75):
    return max((1.0 - smooth(t0 + dur - 0.2, t0 + dur, T)) * smooth(t0, t0 + 0.04, T) for t0 in times)


def to_local(hip, facing, world):
    return ((world[0] - hip[0]) * facing, world[1] - hip[1])


# --- 1. the desk at night (0-6.1), the phone's eyes (6.1-7.6), leaning back (7.6-9) ----------------------------

def desk_night(c, t, T):
    his_room(c, T, day=0.0, lamp=1.0, pile=3, notes=0)
    open_book(c, BOOK_X, DESK_TOP, 130, flip=smooth(EV['book_open'], EV['book_open'] + 0.6, T))
    buzz = buzzing(T, EV['buzz'])
    desk_phone(c, PHONE_X, DESK_TOP, buzz, glow=0.6 * buzz, t=T)
    look = Track([(0.0, 0.0), (EV['glance'], 0.0), (EV['glance'] + 0.25, 0.9), (EV['glance'] + 0.9, 0.9),
                  (EV['glance'] + 1.2, 0.0), (5.4, 0.0), (5.65, 0.95)])(T)
    reach = smooth(5.7, EV['flip'], T)
    hand_f = (150 + 80 * reach, -52 + 2 * reach - 10 * math.sin(math.pi * reach))
    pose = seated(*HIP[:1], ROOM_FLOOR, facing=1, turn=0.42, lean=16 + 14 * reach, tilt=14 - 6 * smooth(3.0, 3.4, T),
                  hand_b=(46, -52), hand_f=hand_f, lx=look, ly=0.35, eye=blink(T, 2),
                  brow=Track([(0, 0), (3.2, -6), (4.4, -10), (5.6, -4)])(T),
                  smile=Track([(0, 0.05), (3.2, -0.1), (5.6, 0.15)])(T), breathe=idle(T, 1, 0.6)['breathe'])
    HERO.draw(c, pose, t=T)


def cam_desk(t):
    u = smooth(0, 6.1, t)
    return (350, 600, 2.1 + 0.15 * u)


def phone_insert(c, t, T):
    """Close-up: his hand turns the phone over; two red eyes open in the screen."""
    c.drawPaint(paint('#0B0D12'))
    light_pool(c, 960, 560, 900, 600, 'warm', 0.10)
    turn = smooth(0.0, 0.45, t)
    ang = -18 + 8 * math.sin(t * 1.3)
    eyes_open = smooth(0.55, 0.85, t)
    x, y = 960, 560
    if turn < 0.5:
        phone(c, x, y, ang, 8.0, face_down=True)
    else:
        light_pool(c, x, y, 520, 520, 'red', 0.25 * eyes_open)
        phone(c, x, y, ang, 8.0, glow=0.6, content=phone_eyes(eyes_open, T, red=1.0, glitch=0.3 * eyes_open,
                                                              size=15))
    # his fingers round the edges
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    for k, (fx, fy) in enumerate([(-168, 50), (-168, 140), (168, -30), (168, 70), (168, 170)]):
        circle(c, fx, fy, 38, 'skin', 'outline', 6)
    c.restore()
    whisper(c, T, 'just five minutes.', 6.6, 8.6, 960, 180, 78, seed=1)


def lean_back(c, t, T):
    his_room(c, T, day=0.0, lamp=1.0, pile=3, notes=0)
    open_book(c, BOOK_X, DESK_TOP, 130, flip=1.0)
    u = smooth(0.0, 0.8, t)
    hip = HIP
    hand_world = (hip[0] + 92 - 10 * u, hip[1] - 148 + 6 * math.sin(T * 3))
    pose = seated(hip[0], ROOM_FLOOR, facing=1, turn=0.35, lean=12 - 20 * u, tilt=-6 * u,
                  hand_f=to_local(hip, 1, hand_world), hand_b=(70, -40), lx=0.6, ly=-0.1,
                  eyes='dot', smile=0.25 * u, brow=2, eye=blink(T, 5), breathe=idle(T, 2, 0.5)['breathe'])
    j = HERO.draw(c, pose, t=T)
    light_pool(c, hand_world[0] - 20, hand_world[1] - 10, 200, 160, '#9CC8FF', 0.32)
    phone(c, hand_world[0] + 8, hand_world[1] - 18, 12, 1.1, face_down=True)
    whisper(c, T, 'just five minutes.', 6.6, 8.6, 640, 430, 60, seed=1)


def cam_lean(t):
    return (380, 590, 2.0 - 0.1 * smooth(0, 1.4, t))


# --- 2. the time-lapse (9-22) ------------------------------------------------------------------------------

LAPSE = EV['lapse_cuts']
DAY_LEN = 2.6


def lapse(c, t, T):
    k = max(i for i, t0 in enumerate(LAPSE) if T >= t0 - 1e-6)
    u = T - LAPSE[k]
    day = 0.3 + 0.62 * (u / DAY_LEN)
    night = smooth(0.72, 0.82, day)
    notes = k + smooth(EV['note_slap'], EV['note_slap'] + 0.35, u)
    pile = 3 + 2 * k + (1 if u >= EV['book_thud'] else 0) + (1 if u >= EV['book_thud'] + 0.12 else 0)
    r = his_room(c, T, day=day, lamp=night, pile=pile, notes=notes, clock_spin=6 + day * 24)
    open_book(c, BOOK_X, DESK_TOP, 130, flip=1.0)
    # a book dropping onto the pile
    for j, dt in enumerate((0.0, 0.12)):
        f = (u - (EV['book_thud'] + dt - 0.22)) / 0.22
        if 0 <= f < 1:
            y = r['pile_top'] - 260 * (1 - f * f)
            book(c, PILE_X - 60, y, 120, 24, ['#B0624A', '#3F5F8A'][j], -6 + 8 * f)
    if k % 2 == 0:
        # at the desk, on the phone
        hand_world = (HIP[0] + 86, HIP[1] - 150 + 4 * math.sin(T * 3))
        pose = seated(HIP[0], ROOM_FLOOR, facing=1, turn=0.35, lean=-6, tilt=4, hand_f=to_local(HIP, 1, hand_world),
                      hand_b=(70, -40), lx=0.6, eyes='tired' if k else 'dot', bags=0.4 * k, smile=0.1,
                      eye=blink(T, 7))
        HERO.draw(c, pose, t=T)
        light_pool(c, hand_world[0] - 20, hand_world[1] - 10, 180, 140, '#9CC8FF', 0.28)
        phone(c, hand_world[0] + 8, hand_world[1] - 18, 12, 1.1, face_down=True)
    else:
        bed_scroll(c, T, k)
    whisper(c, T, 'you have time.', 11.8, 13.6, 1500, 520, 64, seed=2)
    whisper(c, T, 'start tomorrow.', 16.0, 17.8, 1340, 640, 64, seed=3)
    whisper(c, T, 'one more video.', 19.6, 21.4, 640, 420, 64, seed=4)


def bed_scroll(c, T, k=1, glow=1.0, eyes='tired'):
    """Lying in bed with the phone held over his face."""
    hx, hy = BED_X + BED_W - 108, BED_TOP - 30
    HERO.draw_head(c, hx, hy, lying_head_pose(eyes=eyes, eye=blink(T, 9 + k), bags=0.5 + 0.2 * k), angle=-14)
    blanket(c, BED_X + 6, BED_X + BED_W - 160, BED_TOP + 2)
    px, py = hx - 96 + 3 * math.sin(T * 3), hy - 70
    light_pool(c, hx - 20, hy, 170, 140, '#9CC8FF', 0.3 * glow)
    phone(c, px, py, -14, 1.1, face_down=True)
    circle(c, px + 6, py + 34, 13, 'skin', 'outline', 4.5)


def cam_lapse(t):
    return (960, 500, 1.0 + 0.04 * smooth(0, 13, t))


# --- 3. the quicksand bed (22-30) ------------------------------------------------------------------------

def quicksand(c, t, T):
    his_room(c, T, day=0.32, lamp=0.0, pile=13, notes=8, bed_layer=False)
    from engine.props import bed
    bed(c, BED_X, ROOM_FLOOR, BED_W, blanket='#4B5A7A', height=96)
    ring = smooth(EV['alarm'], EV['alarm'] + 0.1, T) * (1 - smooth(26.4, 27.2, T))
    alarm_clock(c, STAND_X + 55, ROOM_FLOOR - 110, 1.05, ring=ring, t=T, hour=7.0)
    up = smooth(EV['sit_up'] - 0.3, EV['sit_up'] + 0.4, T)
    sink = smooth(EV['sink'], EV['sunk'], T)
    wave = smooth(EV['sink'] - 0.2, EV['sink'] + 0.6, T) * (1 - 0.6 * smooth(EV['sunk'], EV['sunk'] + 1.5, T))
    if up < 0.02:
        HERO.draw_head(c, BED_X + BED_W - 108, BED_TOP - 30, lying_head_pose(eyes='closed', smile=0.05, brow=0,
                                                                              bags=0.3), angle=-14)
        blanket(c, BED_X + 6, BED_X + BED_W - 160, BED_TOP + 2)
        return
    hip = (BED_X + BED_W - 170, BED_TOP + 10 + 128 * sink)
    struggle = math.sin(T * 9) * smooth(EV['sink'], EV['sink'] + 0.4, T) * (1 - sink)
    phone_hand = (hip[0] - 70, BED_TOP - 60 - 40 * smooth(25.0, 26.0, T))
    pose = dict(x=hip[0], y=hip[1], facing=-1, turn=0.3, hb=88, kb=0, hf=86, kf=0,
                lean=-10 + 30 * (1 - up) - 8 * struggle, tilt=-10 * sink + 6 * struggle,
                hand_b=to_local(hip, -1, (hip[0] - 40 - 30 * struggle, hip[1] - 150 + 40 * sink)) if sink < 0.6
                else to_local(hip, -1, phone_hand),
                hand_f=to_local(hip, -1, (hip[0] - 90 + 40 * sink, hip[1] - 120 + 30 * struggle)),
                eyes='tired' if T < EV['sink'] else ('wide' if sink < 0.8 else 'dot'), pupil=0.6, lx=0.3,
                ly=-0.2, bags=0.6,
                brow=-14 - 8 * sink, mopen=0.35 * smooth(EV['sink'], EV['sink'] + 0.3, T) * (1 - sink),
                smile=-0.3)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-400, -400, W + 400, BED_TOP + 58))
    HERO.draw(c, pose, t=T)
    c.restore()
    pts = blanket(c, BED_X + 6, BED_X + BED_W - 30, BED_TOP + 2, wave=wave, sink=sink, t=T, swirl=wave)
    if sink > 0.55:
        # his arm stays up out of the quicksand, holding the phone
        from engine.draw import limb
        base = (phone_hand[0] + 14, BED_TOP + 14)
        limb(c, [base, (phone_hand[0] + 4, phone_hand[1] + 26)], 'hoodie', 22)
        light_pool(c, phone_hand[0], phone_hand[1], 160, 140, 'red', 0.3)
        phone(c, phone_hand[0], phone_hand[1] - 6, -8, 1.15, glow=0.4, content=phone_eyes(1.0, T))
        circle(c, phone_hand[0] + 6, phone_hand[1] + 20, 14, 'skin', 'outline', 4.5)


def cam_quick(t):
    u = smooth(0, 8, t)
    sx, sy = shake(t, 4 * smooth(2.0, 2.3, t) * (1 - smooth(5.4, 6.0, t)))
    return (1530 + sx, 640 + sy, 1.75 + 0.2 * u)


# --- 4. the mountain (30-40) ------------------------------------------------------------------------------

def mountain(c, t, T):
    cuts = EV['mountain_cuts']
    k = max(i for i, t0 in enumerate(cuts) if T >= t0 - 1e-6)
    m = [0.35, 0.55, 1.0][k]
    wob = 0.0
    if k == 2:
        wob = math.sin((T - EV['wobble']) * 11) * math.exp(-(T - EV['wobble']) * 1.6) * 0.5 if T > EV['wobble'] else 0
    red = smooth(36.0, 38.0, T) * (1 - smooth(38.6, 39.6, T)) if k == 2 else 0.0
    his_room(c, T, day=0.5 if k < 2 else 0.78, lamp=0.0 if k < 2 else 0.6, pile=14 + 2 * k, notes=9 + 4 * k,
             mountain=m, mountain_sway=wob, red=red)
    if k < 2:
        bed_scroll(c, T, 2 + k)
        return
    # 30 days left: he faces the mountain
    back = smooth(EV['wobble'] + 0.15, EV['wobble'] + 0.8, T)
    turn_away = smooth(38.6, 39.0, T)
    if T < 38.6:
        x = 1280 + 120 * back - 30 * smooth(EV['reach'] - 0.4, EV['reach'], T) * (1 - back)
        reach = smooth(EV['reach'] - 0.3, EV['reach'], T) * (1 - smooth(EV['wobble'], EV['wobble'] + 0.2, T))
        pose = merge(standing(), dict(sf=-10, ef=20, sb=10, eb=14),
                     walk(T, 1.2, 14) if 0.05 < back < 0.95 else None,
                     x=x, y=ROOM_FLOOR - STAND_HIP, facing=-1, turn=0.3,
                     lean=-4 + 14 * reach - 10 * back, tilt=-18 * (1 - reach) + 10 * back,
                     lx=0.0, ly=-0.8 * (1 - reach), eyes='wide' if back > 0.2 else 'dot', pupil=0.6,
                     brow=-16 - 8 * back, smile=-0.35,
                     mopen=0.3 * smooth(EV['wobble'], EV['wobble'] + 0.2, T) * (1 - smooth(37.0, 37.5, T)))
        if reach > 0.02:
            pose['hand_f'] = (90 + 40 * reach, -40 + 40 * reach)
        HERO.draw(c, pose, t=T)
    else:
        # he turns and drops face-down onto the bed
        f = smooth(38.6, EV['flop'], T)
        x = 1420 + 120 * f
        pose = dict(x=x, y=ROOM_FLOOR - STAND_HIP + 40 * f, facing=1, turn=0.1, **standing(),
                    lean=10 + 70 * smooth(38.8, EV['flop'] + 0.2, T), tilt=10, eyes='closed', brow=-18,
                    smile=-0.4, sf=40 * f, sb=40 * f)
        if T < EV['flop'] + 0.25:
            HERO.draw(c, pose, t=T)
        else:
            HERO.draw_head(c, BED_X + BED_W - 140, BED_TOP - 22, dict(turn=0.9, eyes='closed', brow=-16, smile=-0.4),
                           angle=70)
            blanket(c, BED_X + 6, BED_X + BED_W - 170, BED_TOP + 2)
    whisper(c, T, 'too late now.', 36.4, 38.6, 1300, 300, 76, seed=5)


def cam_mountain(t):
    if t < 4.0:
        return (980, 560, 1.25)
    u = smooth(4.0, 9.0, t)
    sx, sy = shake(t, 5 * smooth(5.5, 5.6, t) * (1 - smooth(5.6, 6.6, t)))
    return (1080 + sx, 470 - 40 * u + sy, 1.06 + 0.12 * u)


# --- 5. the shadow rises out of the phone (40-50) ---------------------------------------------------------------

def rise(c, t, T):
    red = smooth(EV['rise'], EV['rise'] + 2.0, T)
    his_room(c, T, day=0.0, lamp=0.0, pile=20, notes=21, mountain=1.0, red=0.6 * red)
    dark = smooth(46.0, 49.0, T)
    hx, hy = BED_X + BED_W - 108, BED_TOP - 30
    curl = smooth(EV['curl'], EV['curl'] + 0.8, T)
    HERO.draw_head(c, hx, hy, dict(turn=-0.2 + 0.9 * curl, eyes='closed' if curl > 0.5 else 'dot', eye=blink(T, 3),
                                   lx=-0.4, ly=-0.6, brow=-14 - 8 * curl, smile=-0.35, bags=0.8), angle=-14 + 30 * curl)
    blanket(c, BED_X + 6, BED_X + BED_W - 160 + 60 * curl, BED_TOP + 2 - 10 * curl)
    # the phone on his chest; the shadow climbs out of it
    px, py = BED_X + 330, BED_TOP - 36
    grow = smooth(EV['rise'], EV['rise'] + 2.2, T)
    light_pool(c, px, py, 260, 200, 'red', 0.35 + 0.3 * red)
    phone(c, px, py, -70, 1.1, glow=0.5, content=phone_eyes(1.0 - grow, T, red=1.0))
    if grow > 0:
        s = 0.25 + 0.95 * grow
        spread = smooth(EV['curl'], EV['curl'] + 1.5, T)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(-400, -400, W + 400, py - 4))
        SHADE.draw(c, dict(x=px + 20, y=py + 30 * s - 140 * grow * s, scale=s, facing=1, turn=0.1,
                           eye=smooth(EV['rise'] + 1.2, EV['rise'] + 1.6, T), lean=10 + 14 * grow, tilt=14,
                           sb=100 + 40 * spread, sf=120 + 40 * spread, eb=-30, ef=-30, **standing(),
                           alpha=smooth(EV['rise'], EV['rise'] + 0.6, T)), t=T)
        c.restore()
    if dark > 0:
        c.drawPaint(paint('#000000', 0.55 * dark))
    whisper(c, T, 'you’re too far behind.', 42.0, 44.4, 1250, 330, 66, seed=6)
    whisper(c, T, 'why even try?', 44.8, 47.0, 1760, 420, 66, seed=7)


def cam_rise(t):
    u = smooth(0, 10, t)
    return (1520, 560 - 30 * u, 1.3 + 0.18 * u)


# --- 6. 5 AM (50-62) ----------------------------------------------------------------------------------------

def clock_5am(c, t, T):
    c.drawPaint(paint('#050608'))
    on = smooth(EV['clock_5am'], EV['clock_5am'] + 0.08, T)
    light_pool(c, 960, 560, 420, 200, '#FF4A3D', 0.18 * on)
    digital_clock(c, 960, 640, '5:00', 3.2, glow=on)


def hall_5am(c, t, T):
    sw = SON_DOOR
    dawn = 0.15 + 0.25 * smooth(51.0, 62.0, T)
    bulb = 1.0 - smooth(EV['light_off'], EV['light_off'] + 0.1, T)
    door = smooth(EV['door_close'] - 0.9, EV['door_close'] - 0.55, T) * (1 - smooth(EV['door_close'] - 0.2,
                                                                                    EV['door_close'], T))
    son_open = 0.38 * smooth(EV['son_door'], EV['son_door'] + 0.5, T) + 0.4 * smooth(60.0, 60.6, T)
    hallway(c, T, dawn=dawn, bulb=bulb, son_door=son_open, front_open=door, son_leaf=False)
    fy = HALL_FLOOR
    stool(c, STOOL_X, fy, 100)
    # the son, half hidden behind his door
    son_x = SON_DOOR[0] + SON_DOOR[1] * 0.3 + 240 * smooth(60.2, 61.4, T)
    from engine.home import front_door
    if T >= 60.2:
        front_door(c, SON_DOOR[0], fy, SON_DOOR[1], 370, open_amt=son_open, hinge='right', part='leaf')
    if son_open > 0.02:
        HERO.draw(c, merge(standing(), walk(T, 0.8, 16) if 60.2 < T < 61.4 else idle(T, 3, 0.6),
                           x=son_x, y=fy - STAND_HIP, facing=1, turn=0.3, lx=0.8, ly=0.1, eye=blink(T, 4),
                           brow=-12 - 6 * smooth(55, 57, T), smile=-0.2 * smooth(55, 58, T), bags=0.6), t=T)
    if T < 60.2:
        front_door(c, SON_DOOR[0], fy, SON_DOOR[1], 370, open_amt=son_open, hinge='right', part='leaf')
    # the father: sitting, tying, standing, the switch, the door
    if T < EV['stand']:
        hip = (STOOL_X + 4, fy - 130)
        taping = T >= EV['tape'] - 0.6
        tie = math.sin(T * 7) * smooth(51.6, 52.0, T) * (0 if taping else 1)
        tape = smooth(EV['tape'] + 0.4, EV['stand'] - 0.6, T)
        lift = smooth(EV['tape'] - 0.6, EV['tape'], T)
        # the shoe: on the floor, then up in his lap while he winds tape round the toe
        sx = STOOL_X + 126 - 40 * lift
        sy = fy - 98 * lift
        a = T * 5.0
        roll = (sx + 34 + 16 * math.cos(a), sy - 20 + 22 * math.sin(a))
        hand_b = to_local(hip, 1, (sx - 30, sy - 22)) if taping else (110 + 6 * tie, 108)
        hand_f = to_local(hip, 1, roll) if taping else (124 - 6 * tie, 112)
        pose = dict(x=hip[0], y=hip[1], facing=1, turn=0.35, hb=88, kb=88, hf=84, kf=84,
                    foot_b=(70, 126), foot_f=(110, 126), lean=36 - 14 * lift, tilt=4 + 8 * lift, eyes='tired',
                    bags=0.9, brow=-8, smile=-0.05, hand_b=hand_b, hand_f=hand_f, eye=blink(T, 6))

        def lap(cc, j):
            # layers draw in the character's frame; step back to world coordinates (facing +1)
            cc.save()
            if j is not None:
                cc.translate(-hip[0], -hip[1])
            shoe(cc, sx, sy, 0.55, 1, torn=1.0 - 0.7 * tape, tape=tape, color='#4A3626')
            if taping:
                cc.drawCircle(*roll, 13, paint('#9A9A9E'))
                cc.drawCircle(*roll, 13, paint('outline', stroke=3))
                cc.drawCircle(*roll, 6, paint('#5A5A60'))
            cc.restore()
        if not taping:
            lap(c, None)
        FATHER.with_look(shoes='#5B5E66').draw(c, pose, {'mid': lap} if taping else None, t=T)
    else:
        walk_t = smooth(EV['light_off'] + 0.3, EV['door_close'] - 0.1, T)
        x = STOOL_X + 40 + 200 * walk_t
        glance = smooth(56.9, 57.3, T) * (1 - smooth(57.9, 58.2, T))
        switching = smooth(EV['light_off'] - 0.35, EV['light_off'], T) * (1 - smooth(EV['light_off'] + 0.1,
                                                                                      EV['light_off'] + 0.4, T))
        pose = merge(standing(), walk(T, 0.9, 18) if 0.02 < walk_t < 0.98 else None,
                     x=x, y=fy - STAND_HIP, facing=-1 if glance > 0.5 else 1, turn=0.3, eyes='tired',
                     bags=0.9, brow=-6, smile=-0.05, lean=6, tilt=6, eye=blink(T, 8))
        if switching > 0:
            pose['hand_f'] = to_local((x, fy - STAND_HIP), 1, (1420, 560))
        alpha = 1.0 - smooth(EV['door_close'] - 0.35, EV['door_close'] - 0.1, T)
        pose['alpha'] = alpha

        def lunch(cc, j):
            hx, hy = j['hand_b']
            lunchbox(cc, hx, hy + 30, 0.7)
        if alpha > 0:
            FATHER.draw(c, pose, {'front': lunch}, t=T)


def cam_hall(t):
    T = 51.2 + t
    if T < 53.0:
        u = smooth(51.2, 53.0, T)
        return (900, 600, 1.05 + 0.1 * u)
    if T < EV['stand']:
        u = smooth(EV['tape'], EV['stand'], T)
        return (STOOL_X + 70, HALL_FLOOR - 170, 2.5 + 0.2 * u)
    if T < 60.0:
        return (1180, 640, 1.45)
    u = smooth(60.0, 62.0, T)
    return (900 - 100 * u, 600, 1.15)


# --- assemble ------------------------------------------------------------------------------------------------

def shots():
    return [
        Shot(0.0, EV['flip'], desk_night, cam_desk, name='desk'),
        Shot(EV['flip'], EV['pickup'], phone_insert, None, name='phone_eyes'),
        Shot(EV['pickup'], 9.0, lean_back, cam_lean, name='lean_back'),
        Shot(9.0, 22.0, lapse, cam_lapse, name='lapse'),
        Shot(22.0, 30.0, quicksand, cam_quick, name='quicksand'),
        Shot(30.0, 40.0, mountain, cam_mountain, name='mountain'),
        Shot(40.0, 50.0, rise, cam_rise, name='rise'),
        Shot(50.0, EV['son_door'], clock_5am, None, name='5am_clock'),
        Shot(EV['son_door'], EV['tape'] - 0.6, hall_5am, cam_hall, name='hall'),
        Shot(EV['tape'] - 0.6, EV['stand'], hall_5am, lambda t: cam_hall(t + EV['tape'] - 0.6 - EV['son_door']),
             name='tape'),
        Shot(EV['stand'], 62.0, hall_5am, lambda t: cam_hall(t + EV['stand'] - EV['son_door']), name='hall2'),
    ]
