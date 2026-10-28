"""Act 2 (1:02-2:02): Day 1, the drawer, the grind, the father at the door, the exam hall."""
from __future__ import annotations

import math

import skia

from act1 import BOOK_X, HIP, buzzing, desk_phone, open_book, to_local
from common import (BED_TOP, BED_W, BED_X, CHAIR_X, DESK_TOP, DESK_W, DESK_X, FATHER, HALL_FLOOR, HERO, PILE_X,
                    ROOM_FLOOR, SEAT_DY, SHADE, SON_DOOR, STAND_HIP, STAND_X, STOOL_X, blanket, extra, hallway,
                    his_room, lying_head_pose, merge, phone_eyes, seated, standing)
from cues import EV
from engine.captions import whisper
from engine.core import H, W, Track, hrand, noise1, out_back, shake, smooth
from engine.draw import circle, col, cone, light_pool, mixc, paint, poly, rrect, text
from engine.fx import dust_motes, puff, shards
from engine.home import alarm_clock, book, book_pile, calendar, exam_paper, shoe, stool, test_result, wall_clock
from engine.props import phone, window
from engine.render import Shot
from engine.rig import blink, idle, walk

DRAWER = (DESK_X + DESK_W - 160, DESK_TOP + 28)   # top-left of the top drawer's face
KEY = (DESK_X + DESK_W - 92, DESK_TOP + 46)


def days_left(T):
    """The countdown during the grind (29 at Day 1, 1 the day before the exam)."""
    marks = [(62.0, 29), (70.0, 27), (76.0, 24), (82.0, 19), (88.0, 14), (96.0, 11), (98.0, 8), (100.0, 5),
             (102.0, 3), (104.0, 2), (106.0, 1), (108.0, 0)]
    left = 29
    for t0, d in marks:
        if T >= t0:
            left = d
    return left


def notebook(c, x, y, w=120, written=0.0):
    """A notebook lying flat on the desk, its page tipped toward us so the writing shows."""
    page = poly([(x - w / 2, y), (x + w / 2, y), (x + w / 2 - 10, y - 26), (x - w / 2 + 6, y - 26)], True)
    c.drawPath(page, paint('#F4F1EA'))
    c.drawPath(page, paint('outline', stroke=3))
    n = int(4 * written)
    for k in range(4):
        yy = y - 6 - k * 6
        c.drawLine(x - w / 2 + 12, yy, x + w / 2 - 14, yy, paint('#C9C2B2', stroke=1.5))
        if k < n:
            c.drawLine(x - w / 2 + 14, yy - 2, x - w / 2 + 14 + (w - 36) * (0.6 + 0.4 * hrand(k, 3)), yy - 2,
                       paint('#3A3F52', stroke=2))


def pencil_in(c, hand, angle=-35, length=46):
    x, y = hand
    a = math.radians(angle)
    tip = (x + math.cos(a) * length * 0.35, y - math.sin(a) * length * 0.35 + 10)
    top = (x - math.cos(a) * length * 0.65, y + math.sin(a) * length * 0.65 - 10)
    c.drawLine(*top, *tip, paint('#E3B341', stroke=7))
    c.drawLine(*top, *tip, paint('outline', stroke=1.5))
    c.drawCircle(*tip, 3, paint('#2B2B30'))


def study_pose(T, intensity=1.0, slump=0.0, tired=0.0):
    """Seated at the desk, writing; slump puts his head down on his arms."""
    w = math.sin(T * 13) * intensity
    hand_f = (128 + 10 * w, -58 + 3 * math.cos(T * 21) * intensity)
    pose = seated(HIP[0], ROOM_FLOOR, facing=1, turn=0.45, lean=22 + 20 * slump, tilt=16 + 24 * slump,
                  hand_b=(76, -54), hand_f=hand_f, lx=0.3, ly=0.6, eyes='closed' if slump > 0.6 else 'dot',
                  eye=blink(T, 11), bags=0.3 + 0.5 * tired, brow=-6 - 10 * slump, smile=-0.1 - 0.3 * slump,
                  breathe=idle(T, 4, 0.8)['breathe'])
    return pose


def desk_study(c, T, *, day=0.0, mountain=1.0, done=0, crossed=0, glow=0.0, jolt=0.0, written=0.5, slump=0.0,
               lamp=1.0, tired=0.0, write=True):
    his_room(c, T, day=day, lamp=lamp, pile=3, notes=0, crossed=crossed, glow=glow, jolt=jolt, mountain=mountain,
             today_note=1.0)
    if done > 0:
        book_pile(c, 96, ROOM_FLOOR, done, seed=21, width=(100, 130))
    open_book(c, BOOK_X - 30, DESK_TOP, 120, flip=0.0)
    notebook(c, BOOK_X + 70, DESK_TOP, 110, written)
    pose = study_pose(T, 1.0 if write else 0.0, slump, tired)

    def pencil(cc, j):
        if slump < 0.5:
            pencil_in(cc, j['hand_f'])
    HERO.draw(c, pose, {'front': pencil}, t=T)


# --- 7. Day 1: the drawer (62-70) ----------------------------------------------------------------------------

def day1(c, t, T):
    drawer = smooth(EV['drawer_open'], EV['drawer_open'] + 0.3, T) * (1 - smooth(EV['slam'] - 0.12, EV['slam'], T))
    bang = buzzing(T, EV['bangs'], 0.45)
    glow = smooth(EV['slam'], EV['slam'] + 0.3, T) * (0.5 + 0.5 * bang)
    lamp = smooth(EV['lamp_on'], EV['lamp_on'] + 0.08, T)
    r = his_room(c, T, day=0.05, lamp=lamp, pile=22, notes=22, mountain=1.0, drawer=drawer, glow=glow, jolt=bang,
                 crossed=0)
    # the phone, glowing on the desk until he takes it
    if T < EV['grab_phone']:
        desk_phone(c, 452, DESK_TOP, buzzing(T, [62.2], 0.6), glow=0.8, t=T)
    if T >= EV['book_pull']:
        open_book(c, BOOK_X, DESK_TOP, 130, flip=smooth(EV['book_pull'] + 0.5, EV['book_pull'] + 1.0, T))
    # walking in, the phone, the drawer, the key, the bangs, then the chair
    if T < EV['book_pull'] - 0.2:
        x = Track([(62.0, 1080), (62.7, 860, 'out_cubic'), (66.0, 860), (66.3, 905, 'out_cubic'),
                   (67.6, 905), (67.9, 860)])(T)
        crouch = smooth(EV['drawer_open'] - 0.3, EV['drawer_open'], T) * (1 - smooth(EV['lock'] + 0.2,
                                                                                    EV['lock'] + 0.6, T))
        hip = (x, ROOM_FLOOR - STAND_HIP + 28 * crouch)
        if T < EV['grab_phone']:
            hand = None
        elif T < EV['drop_phone']:
            u = smooth(EV['grab_phone'], EV['grab_phone'] + 0.25, T)
            hand = (452 + (DRAWER[0] + 80 - 452) * smooth(EV['drawer_open'], EV['drop_phone'], T),
                    DESK_TOP - 12 - 30 * u)
        elif T < EV['slam']:
            hand = (DRAWER[0] + 120, DRAWER[1] + 10)
        elif T < EV['lock'] + 0.3:
            hand = (KEY[0] + 6, KEY[1] + 4)
        else:
            hand = None
        startle = smooth(EV['bangs'][0], EV['bangs'][0] + 0.15, T) * (1 - smooth(67.6, 68.0, T))
        pose = merge(standing(), walk(T, 1.1, 18) if (62.0 < T < 62.7 or 66.0 < T < 66.3 or 67.6 < T < 67.9) else None,
                     x=hip[0], y=hip[1], facing=-1, turn=0.3, lean=4 + 30 * crouch - 8 * startle,
                     tilt=10 * crouch, lx=0.4 + 0.4 * crouch, ly=0.4 * crouch,
                     eyes='wide' if startle > 0.3 else 'dot', pupil=0.6, eye=blink(T, 12),
                     brow=Track([(62.0, -8), (64.3, -16), (65.2, -20), (66.0, -24), (67.6, -16), (68.0, -10)])(T),
                     smile=Track([(62.0, -0.2), (65.0, -0.35), (67.8, -0.1)])(T),
                     mopen=0.25 * startle)
        if crouch > 0.05:
            pose.update(foot_b=(-14, STAND_HIP - 28 * crouch), foot_f=(16, STAND_HIP - 28 * crouch))
        if hand is not None:
            pose['hand_f'] = to_local(hip, -1, hand)

        def held(cc, j):
            if EV['grab_phone'] <= T < EV['drop_phone']:
                hx, hy = j['hand_f']
                phone(cc, hx, hy - 20, 10, 1.05, glow=0.5, content=phone_eyes(1.0, T, glitch=0.4))
        HERO.draw(c, pose, {'front': held}, t=T)
        # the phone dropping into the drawer
        f = (T - EV['drop_phone']) / 0.25
        if 0 <= f < 1:
            phone(c, DRAWER[0] + 80, DRAWER[1] - 30 + 40 * f * f, 80, 1.0, face_down=True)
    else:
        u = smooth(EV['book_pull'] - 0.2, EV['book_pull'] + 0.4, T)
        pose = seated(HIP[0], ROOM_FLOOR, facing=1, turn=0.45, lean=14 + 8 * u, tilt=10 + 6 * u,
                      hand_b=(76, -54), hand_f=(130, -58) if T > EV['lamp_on'] + 0.2 else to_local(
                          HIP, 1, (DESK_X + DESK_W - 60, DESK_TOP - 30)),
                      lx=0.4, ly=0.3, brow=-10, smile=0.0, eye=blink(T, 13), breathe=idle(T, 5, 0.6)['breathe'])
        HERO.draw(c, pose, t=T)
    whisper(c, T, 'let me out!', 66.2, 67.8, DRAWER[0] + 70, DRAWER[1] - 120, 62, seed=8)


def cam_day1(t):
    T = 62.0 + t
    if T < 68.0:
        sx, sy = shake(t, 4 * buzzing(T, EV['bangs'], 0.3))
        return (700 + sx, 640 + sy, 1.75)
    u = smooth(68.0, 70.0, T)
    return (520 - 80 * u, 600, 1.75 + 0.15 * u)


# --- 8. the grind (70-108) ------------------------------------------------------------------------------------

def grind_desk_night(c, t, T):
    jolt = buzzing(T, [EV['bang_ignored']], 0.5)
    desk_study(c, T, day=0.0, mountain=0.85, done=3, crossed=2, glow=0.55 + 0.45 * jolt, jolt=jolt,
               written=smooth(70.0, 76.0, T))


def cam_desk_close(cx=470, cy=610, z0=1.7, z1=1.85, dur=6.0):
    def cam(t):
        return (cx, cy, z0 + (z1 - z0) * smooth(0, dur, t))
    return cam


def break_free(c, t, T):
    his_room(c, T, day=0.22, lamp=0.0, pile=3, notes=0, crossed=5, mountain=0.7, glow=0.4, today_note=1.0)
    ring = smooth(EV['alarm2'], EV['alarm2'] + 0.1, T) * (1 - smooth(EV['break_free'] + 0.3, EV['break_free'] + 0.5, T))
    alarm_clock(c, STAND_X + 55, ROOM_FLOOR - 110, 1.05, ring=ring, t=T, hour=5.0)
    pull = smooth(EV['alarm2'] + 0.3, EV['break_free'] - 0.2, T)
    free = smooth(EV['break_free'] - 0.15, EV['break_free'] + 0.35, T)
    wave = pull * (1 - free)
    if free < 0.02:
        hip = (BED_X + BED_W - 170, BED_TOP + 10 + 50 * pull - 20 * math.sin(T * 10) * pull)
        pose = dict(x=hip[0], y=hip[1], facing=-1, turn=0.3, hb=88, kb=0, hf=86, kf=0, lean=-6 + 10 * math.sin(T * 9),
                    tilt=-8, eyes='dot', brow=-24, smile=-0.4, mopen=0.2,
                    hand_b=to_local(hip, -1, (hip[0] - 120, hip[1] - 110)),
                    hand_f=to_local(hip, -1, (hip[0] - 60, hip[1] - 40)))
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(-400, -400, W + 400, BED_TOP + 58))
        HERO.draw(c, pose, t=T)
        c.restore()
        blanket(c, BED_X + 6, BED_X + BED_W - 30, BED_TOP + 2, wave=wave, sink=0.3 * pull, t=T, swirl=wave)
    else:
        # he tears out of it and lands on his feet; the blanket flies off
        land = smooth(EV['break_free'] + 0.1, EV['break_free'] + 0.5, T)
        x = BED_X + BED_W - 170 - 260 * land
        y = ROOM_FLOOR - STAND_HIP - 120 * math.sin(math.pi * min(1.0, land)) * (1 - land * 0.6)
        blanket(c, BED_X + 6, BED_X + BED_W - 30, BED_TOP + 2, wave=0.2 * (1 - free), t=T)
        fly = smooth(EV['break_free'] - 0.15, EV['break_free'] + 0.9, T)
        if fly < 1:
            # the blanket thrown off: billowing up and away over the headboard
            bx = BED_X + 300 + 380 * fly
            by = BED_TOP - 40 - 260 * math.sin(math.pi * fly)
            sheet = skia.Path()
            sheet.moveTo(bx - 160, by)
            sheet.cubicTo(bx - 80, by - 60 - 40 * math.sin(T * 9), bx + 80, by + 40, bx + 160, by - 10)
            sheet.lineTo(bx + 140, by + 40)
            sheet.cubicTo(bx + 60, by + 80, bx - 60, by + 10, bx - 150, by + 50)
            sheet.close()
            c.drawPath(sheet, paint('#4B5A7A', 1 - smooth(0.7, 1.0, fly)))
            c.drawPath(sheet, paint('outline', 1 - smooth(0.7, 1.0, fly), stroke=4))
        pose = merge(standing(), walk(T, 1.2, 20) if T > EV['break_free'] + 0.8 else None,
                     x=x - 200 * smooth(EV['break_free'] + 0.8, 82.0, T), y=y, facing=-1, turn=0.3,
                     lean=10, tilt=0, eyes='dot', brow=-14, smile=0.15 * land, sf=-30 + 60 * (1 - land),
                     sb=30, ef=20, eb=20)
        HERO.draw(c, pose, t=T)
        puff(c, BED_X + BED_W - 170, BED_TOP, T, EV['break_free'], n=14, color='#7A88A8', size=24, life=1.0)


def cam_bed(t):
    T = 76.0 + t
    u = smooth(EV['break_free'] + 0.3, 82.0, T)
    return (1460 - 380 * u, 620, 1.55 - 0.25 * u)


def test_insert(score, color, T0):
    def draw(c, t, T):
        c.drawPaint(paint('#14171F'))
        light_pool(c, 960, 520, 900, 520, 'warm', 0.22)
        stamp = smooth(T0, T0 + 0.18, T)
        s = out_back(stamp) if stamp > 0 else 0
        test_result(c, 960, 560, 560, 720, score, color, stamp=s, angle=-3)
        if stamp > 0.5:
            light_pool(c, 960 + 140, 560 - 260, 260, 180, color, 0.18)
    return draw


def fail_desk(c, t, T):
    jolt = buzzing(T, [83.7, 84.5], 0.5)
    slump = smooth(83.0, 83.6, T) * (1 - smooth(EV['pencil_up'] - 0.4, EV['pencil_up'] + 0.2, T))
    desk_study(c, T, day=0.0, mountain=0.7, done=5, crossed=10, glow=0.5 + 0.5 * jolt, jolt=jolt, written=0.3,
               slump=slump, tired=0.6, write=T > EV['pencil_up'] + 0.2)
    whisper(c, T, 'you’re not smart enough.', 83.6, 85.6, 560, 470, 58, seed=9)


def shoes_insert(c, t, T, memory=True):
    """What he remembers: his father's taped shoes by the front door, soft and warm like a memory."""
    from engine.thumbkit import blurred

    def scene():
        c.drawPaint(paint('#1A1E2A'))
        c.drawRect(skia.Rect.MakeLTRB(0, 800, W, H), paint('#141822'))
        c.drawLine(0, 800, W, 800, paint('#283042', stroke=4))
        light_pool(c, 960, 700, 800, 300, 'warm', 0.22)
        shoe(c, 760, 800, 2.4, 1, torn=0.25, tape=1.0, color='#5A4030', tape_color='#D9DADF')
        shoe(c, 1180, 800, 2.4, 1, torn=0.0, tape=0.0, color='#5A4030')
    if memory:
        blurred(c, 3.5, scene)
        c.drawPaint(paint('#FFD9A0', 0.10, blend='add'))
        from engine.draw import vignette
        vignette(c, W, H, 0.9, inner=0.25)
    else:
        scene()


def father_peek(c, t, T):
    """5 AM: the father sees lamplight under his son's door and looks in."""
    dawn = 0.2
    peek = smooth(EV['father_peek'] - 0.4, EV['father_peek'], T) * (1 - smooth(94.6, 95.2, T))
    hallway(c, T, dawn=dawn, bulb=1.0, son_door=0.25 * peek, son_light=1.0, son_leaf=True)
    stool(c, STOOL_X, HALL_FLOOR, 100)
    shoe(c, STOOL_X + 120, HALL_FLOOR, 0.55, 1, torn=0.2, tape=1.0, color='#4A3626') if T < 89.0 else None
    fy = HALL_FLOOR
    # he crosses to the son's door, opens it a little, looks in, smiles, closes it
    x = Track([(88.0, STOOL_X + 40), (89.0, STOOL_X + 40), (90.4, SON_DOOR[0] + SON_DOOR[1] + 70, 'in_out_sine'),
               (95.2, SON_DOOR[0] + SON_DOOR[1] + 70), (96.0, SON_DOOR[0] + SON_DOOR[1] + 140)])(T)
    walking = 89.0 < T < 90.4 or 95.2 < T < 96.0
    smile = smooth(EV['father_smile'] - 0.4, EV['father_smile'] + 0.6, T)
    pose = merge(standing(), walk(T, 0.8, 16) if walking else idle(T, 6, 0.6),
                 x=x, y=fy - STAND_HIP, facing=-1, turn=0.35, eyes='happy' if smile > 0.6 else 'tired', bags=0.9,
                 lx=0.6, ly=0.1, brow=-4 + 6 * smile, smile=-0.05 + 0.33 * smile, mwide=0.8, lean=4 + 6 * peek,
                 tilt=6 * peek, eye=blink(T, 14), tears=0.18 * smooth(93.4, 94.2, T))
    if peek > 0.05:
        pose['hand_f'] = to_local((x, fy - STAND_HIP), -1, (SON_DOOR[0] + SON_DOOR[1] - 26, fy - 200))
    FATHER.draw(c, pose, t=T)
    if peek > 0.05:
        light_pool(c, x - 40, fy - 300, 260, 220, 'warm', 0.3 * peek)


def cam_peek(t):
    T = 88.0 + t
    if T < EV['father_peek'] + 0.4:
        return (900, 600, 1.15)
    u = smooth(EV['father_peek'] + 0.4, 93.0, T)
    return (460 + 40 * u, 560 - 20 * u, 1.9 + 0.5 * u)


def calendar_insert(c, t, T):
    c.drawPaint(paint('#1B2130'))
    light_pool(c, 960, 520, 800, 500, 'warm', 0.18)
    crossed = 16 + int(smooth(96.0, 97.8, T) * 6)
    calendar(c, 960 - 330, 540 - 380, 660, 760, crossed=crossed, circle_day=29, label='FINALS')


def quiet_drawer(c, t, T):
    glow = 0.5 * (1 - smooth(104.2, 105.4, T))
    desk_study(c, T, day=0.0, mountain=0.15, done=12, crossed=26, glow=glow, written=0.8, tired=0.3)


def stack_done(c, t, T):
    desk_study(c, T, day=0.3 + 0.2 * smooth(106.0, 108.0, T), mountain=0.0, done=22, crossed=28, lamp=0.4,
               written=1.0, write=False)


# --- 9. the exam hall (108-122) -------------------------------------------------------------------------------

HALL_Y = 900
ROW = [(260, 1.0), (560, 1.0), (860, 1.0), (1160, 1.0), (1460, 1.0), (1760, 1.0)]
HERO_DESK = 2    # index into ROW: he sits at the third desk; the shadow takes the empty one behind him


def side_desk(c, x, floor_y, scale=1.0, paper=True, written=0.0, a=1.0):
    """A small exam desk in side view, the student sitting to its left facing right."""
    top = floor_y - 122 * scale
    c.drawRect(skia.Rect.MakeLTRB(x + 60 * scale, top + 12 * scale, x + 70 * scale, floor_y), paint('#3E4048', a))
    c.drawRect(skia.Rect.MakeLTRB(x + 30 * scale, top, x + 200 * scale, top + 12 * scale), paint('#8A6A4A', a))
    c.drawRect(skia.Rect.MakeLTRB(x + 30 * scale, top, x + 200 * scale, top + 12 * scale), paint('outline', a, stroke=3))
    if paper:
        c.drawPath(poly([(x + 70 * scale, top), (x + 160 * scale, top), (x + 150 * scale, top - 10 * scale),
                         (x + 76 * scale, top - 10 * scale)], True), paint('#F4F1EA', a))
    chair_x = x - 4 * scale
    c.drawRect(skia.Rect.MakeLTRB(chair_x - 30 * scale, floor_y - 84 * scale, chair_x + 30 * scale,
                                  floor_y - 72 * scale), paint('#3B3E46', a))
    c.drawRect(skia.Rect.MakeLTRB(chair_x - 30 * scale, floor_y - 180 * scale, chair_x - 20 * scale,
                                  floor_y - 72 * scale), paint('#3B3E46', a))
    for lx in (-28, 22):
        c.drawRect(skia.Rect.MakeLTRB(chair_x + lx * scale, floor_y - 72 * scale, chair_x + (lx + 6) * scale, floor_y),
                   paint('#3B3E46', a))
    return top


def exam_room(c, T, dim=0.0, red=0.0):
    fy = HALL_Y
    wall = mixc('#2A3040', '#14161E', dim)
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, W + 400, fy), paint(wall))
    c.drawRect(skia.Rect.MakeLTRB(-400, fy, W + 400, H + 400), paint(mixc('#1A1D26', '#0D0E12', dim)))
    c.drawLine(-400, fy, W + 400, fy, paint('#3A4152', stroke=3))
    for k in range(4):
        wx = 140 + k * 460
        window(c, wx, 150, 220, 250, sky=mixc('#8FB8E2', '#2A3348', dim), moon=False, t=T)
        c.drawPath(poly([(wx, 400), (wx + 220, 400), (wx + 420, fy), (wx + 160, fy)], True),
                   paint('#FFF1D6', 0.07 * (1 - dim), blur=30, blend='add'))
    wall_clock(c, 960, 92, 52, 9.0 + (T - 108.0) / 60.0)
    if red > 0:
        light_pool(c, 860, 600, 1200, 600, 'red', 0.18 * red)


def exam_wide(c, t, T):
    exam_room(c, T)
    fy = HALL_Y
    for i, (x, s) in enumerate(ROW):
        side_desk(c, x, fy)
        if i == HERO_DESK - 1:
            continue   # the empty seat
        if i == HERO_DESK:
            continue
        w = math.sin(T * 12 + i * 2) * 0.6
        extra(i + 1).draw(c, seated(x, fy, facing=1, turn=0.5, lean=24, tilt=18, hand_b=(78, -28),
                                    hand_f=(118 + 6 * w, -28), eyes='dot', ly=0.7, lx=0.4, eye=blink(T, 20 + i)),
                          t=T)
    # the hero takes his seat; the shadow walks in and sits behind him
    hx = ROW[HERO_DESK][0]
    sit = smooth(EV['sit'] - 0.5, EV['sit'], T)
    if sit < 1:
        HERO.draw(c, merge(standing(), walk(T, 1.0, 18), x=hx - 140 * (1 - sit), y=fy - STAND_HIP + 15 * sit,
                           facing=1, turn=0.3, brow=-12, smile=-0.2), t=T)
    else:
        HERO.draw(c, seated(hx, fy, facing=1, turn=0.45, lean=10, tilt=6, hand_b=(78, -28), hand_f=(118, -28),
                            lx=-0.6 * smooth(EV['shade_sits'], EV['shade_sits'] + 0.4, T), brow=-12, smile=-0.2,
                            eye=blink(T, 21)), t=T)
    sx = ROW[HERO_DESK - 1][0]
    arrive = smooth(EV['shade_sits'] - 0.8, EV['shade_sits'], T)
    if arrive > 0:
        if arrive < 1:
            SHADE.draw(c, merge(standing(), walk(T, 1.0, 18), x=sx - 220 * (1 - arrive), y=fy - STAND_HIP,
                                facing=1, turn=0.2, eye=1.0, alpha=arrive), t=T)
        else:
            SHADE.draw(c, seated(sx, fy, facing=1, turn=0.2, lean=24, tilt=10, eye=1.0, hand_b=(70, -60),
                                 hand_f=(100, -60)), t=T)


def cam_exam_wide(t):
    u = smooth(0, 2.0, t)
    return (860, 560, 1.0 + 0.05 * u)


def exam_two(c, t, T):
    """Two-shot: the shadow leans in to whisper; the paper turns over."""
    exam_room(c, T, dim=0.15)
    fy = HALL_Y
    hx, sx = ROW[HERO_DESK][0], ROW[HERO_DESK - 1][0]
    side_desk(c, sx, fy)
    side_desk(c, hx, fy)
    lean = smooth(110.0, 110.6, T)
    SHADE.draw(c, seated(sx, fy, facing=1, turn=0.2, lean=24 + 26 * lean, tilt=10 + 10 * lean, eye=1.0,
                         hand_b=(70, -60), hand_f=(100 + 60 * lean, -90 - 40 * lean)), t=T)
    flip = smooth(EV['paper_flip'], EV['paper_flip'] + 0.4, T)
    HERO.draw(c, seated(hx, fy, facing=1, turn=0.45, lean=12 + 8 * flip, tilt=8 + 10 * flip, hand_b=(78, -28),
                        hand_f=(118, -28 - 20 * math.sin(math.pi * flip)), lx=0.4 * flip - 0.5 * (1 - flip), ly=0.6 * flip,
                        eyes='dot', brow=-14 - 6 * lean, smile=-0.25, eye=blink(T, 22), shiver=0.3 * lean), t=T)
    whisper(c, T, 'you’ll go blank.', 110.0, 112.0, hx - 80, fy - 400, 64, seed=10)


def cam_two(t):
    hx = ROW[HERO_DESK][0]
    return (hx - 110, 640, 2.0 + 0.15 * smooth(0, 2.0, t))


def paper_blank(c, t, T):
    """Close-up of the exam: the questions melt away."""
    c.drawPaint(paint('#14161E'))
    blur = smooth(EV['blank'], EV['blank'] + 1.2, T)
    light_pool(c, 960, 560, 1000, 600, 'red', 0.22 * blur)
    sx, sy = shake(T, 3 * blur)
    exam_paper(c, 960 + sx, 560 + sy, 760, 980, blur=blur, angle=-2, t=T)
    c.drawPaint(paint('#000000', 0.3 * blur))


def roar(c, t, T):
    """Wide: the hall goes dark, and the shadow towers over him at his desk."""
    r = smooth(EV['roar'], EV['roar'] + 0.3, T)
    exam_room(c, T, dim=0.9, red=0.8 * r)
    fy = HALL_Y
    hx = ROW[HERO_DESK][0]
    for i, (x, s_) in enumerate(ROW):
        side_desk(c, x, fy, a=0.35 if i != HERO_DESK else 1.0)
    grow = smooth(EV['roar'] - 0.2, EV['roar'] + 0.6, T)
    SHADE.draw(c, dict(x=hx - 40, y=fy + 420 - 260 * grow, scale=2.4 + 1.2 * grow, facing=1, turn=0.1, eye=1.0,
                       lean=18, tilt=16, sb=130, sf=150, eb=-30, ef=-30, alpha=0.95, **standing()), t=T)
    HERO.draw(c, seated(hx, fy, facing=1, turn=0.2, lean=-6, tilt=-8, hand_b=(60, -90), hand_f=(80, -110),
                        eyes='wide', pupil=0.5, lx=-0.3, ly=-0.4, brow=-22, smile=-0.4, mopen=0.3, shiver=0.8,
                        eye=1.0), t=T)


def roar_text(c, T):
    from engine.draw import text as draw_text
    t0, t1 = 114.0, 116.6
    if not (t0 <= T < t1):
        return
    a = smooth(t0, t0 + 0.08, T) * (1 - smooth(t1 - 0.3, t1, T))
    s = out_back(min(1.0, (T - t0) / 0.3))
    jx, jy = noise1(T * 30, 1) * 8, noise1(T * 30, 2) * 8
    c.save()
    c.translate(960 + jx, 300 + jy)
    c.scale(s, s)
    draw_text(c, 'YOU’LL GO BLANK.', 0, 0, 150, 'PatrickHand', '#FF6A5E', a, glow='red', glow_a=0.9, glow_r=24,
              outline='#160404', outline_w=12)
    c.restore()


def eyes_shut(c, t, T):
    """His face, close: eyes shut, a breath."""
    exam_room(c, T, dim=0.85, red=0.4 * (1 - smooth(EV['breath'], EV['breath'] + 0.8, T)))
    hx = ROW[HERO_DESK][0]
    side_desk(c, hx, HALL_Y)
    open_ = smooth(EV['eyes_open'] - 0.1, EV['eyes_open'] + 0.1, T)
    breath = math.sin(max(0.0, T - EV['breath']) * 3) * smooth(EV['breath'], EV['breath'] + 0.3, T)
    HERO.draw(c, seated(hx, HALL_Y, facing=1, turn=0.15, lean=6, tilt=-4 + 4 * breath, hand_b=(78, -28),
                        hand_f=(118, -28), eyes='closed' if open_ < 0.5 else 'dot', brow=-14 + 10 * open_,
                        smile=-0.2 + 0.2 * open_, breathe=0.8 * breath, lx=0.2, ly=0.3 * open_), t=T)


def cam_face(t):
    hx = ROW[HERO_DESK][0]
    return (hx + 10, HALL_Y - 260, 3.2 + 0.2 * smooth(0, 2.0, t))


def memory(kind):
    def draw(c, t, T):
        if kind == 'desk':
            desk_study(c, T, day=0.22, mountain=0.5, done=8, crossed=14, written=0.6)
        else:
            shoes_insert(c, t, T)
        c.drawPaint(paint('#FFE7B0', 0.18))
    return draw


def paper_clear(c, t, T):
    c.drawPaint(paint('#1C2030'))
    light_pool(c, 960, 520, 1100, 640, 'warm', 0.26 * smooth(EV['eyes_open'], EV['eyes_open'] + 0.6, T))
    blur = 1 - smooth(EV['eyes_open'], EV['eyes_open'] + 0.5, T)
    written = smooth(EV['write'], EV['write'] + 2.4, T)
    exam_paper(c, 960, 560, 760, 980, blur=blur, written=written, angle=-2, t=T)
    # his pencil racing along the lines
    if written > 0:
        k = int(written * 6) % 6
        px = 960 - 300 + 560 * ((written * 6) % 1)
        py = 560 - 980 / 2 + 120 + (k // 2) * 130 + 40 + (k % 2) * 30
        pencil_in(c, (px + 30, py - 50), -55, 160)
        circle(c, px + 40, py - 30, 34, 'skin', 'outline', 5)


def exam_release(c, t, T):
    exam_room(c, T, dim=0.0)
    fy = HALL_Y
    for i, (x, s) in enumerate(ROW):
        side_desk(c, x, fy)
        if i in (HERO_DESK - 1, HERO_DESK):
            continue
        w = math.sin(T * 12 + i * 2) * 0.6
        extra(i + 1).draw(c, seated(x, fy, facing=1, turn=0.5, lean=24, tilt=18, hand_b=(78, -28),
                                    hand_f=(118 + 6 * w, -28), eyes='dot', ly=0.7, lx=0.4, eye=blink(T, 20 + i)),
                          t=T)
    hx, sx = ROW[HERO_DESK][0], ROW[HERO_DESK - 1][0]
    w = math.sin(T * 15)
    HERO.draw(c, seated(hx, fy, facing=1, turn=0.5, lean=24, tilt=16, hand_b=(78, -28), hand_f=(122 + 10 * w, -28),
                        eyes='dot', ly=0.7, lx=0.5, brow=-4, smile=0.1, eye=blink(T, 23)), t=T)
    gone = smooth(EV['shade_gone'] - 0.6, EV['shade_gone'] + 0.2, T)
    if gone < 1:
        SHADE.draw(c, seated(sx, fy, facing=1, turn=0.2, lean=24 - 10 * gone, tilt=10, eye=1 - gone,
                             hand_b=(70, -60), hand_f=(100, -60), scale=1.0 - 0.6 * gone, alpha=1 - gone), t=T)
    puff(c, sx + 20, fy - 200, T, EV['shade_gone'] - 0.3, n=18, color='#2A2A30', size=30, life=1.4, a=0.8)


def cam_release(t):
    u = smooth(0, 2.0, t)
    return (840, 560, 1.15 - 0.05 * u)


# --- assemble ---------------------------------------------------------------------------------------------------

def overlays(c, T):
    roar_text(c, T)


def shots():
    m = EV['memories']
    return [
        Shot(62.0, 70.0, day1, cam_day1, name='day1'),
        Shot(70.0, 76.0, grind_desk_night, cam_desk_close(), name='grind_night'),
        Shot(76.0, 82.0, break_free, cam_bed, name='break_free'),
        Shot(82.0, 83.0, test_insert('42%', '#D23A2E', EV['fail']), None, name='fail_42'),
        Shot(83.0, EV['look_door'], fail_desk, cam_desk_close(470, 620, 1.9, 2.0, 2.6), name='slump'),
        Shot(EV['look_door'], EV['pencil_up'], shoes_insert, None, name='shoes'),
        Shot(EV['pencil_up'], 88.0, fail_desk, cam_desk_close(470, 620, 2.0, 2.05, 1.0), name='pencil_up'),
        Shot(88.0, 96.0, father_peek, cam_peek, name='father_peek'),
        Shot(96.0, 98.0, calendar_insert, None, name='calendar'),
        Shot(98.0, 100.0, test_insert('61%', '#D9822B', 98.2), None, name='61'),
        Shot(100.0, 102.0, test_insert('78%', '#B5A22E', 100.2), None, name='78'),
        Shot(102.0, 104.0, test_insert('91%', '#2E8B57', 102.2), None, name='91'),
        Shot(104.0, 106.0, quiet_drawer, cam_desk_close(600, 640, 1.8, 1.9, 2.0), name='quiet'),
        Shot(106.0, 108.0, stack_done, lambda t: (700, 520, 1.0 + 0.03 * t), name='stack_done'),
        Shot(108.0, 110.0, exam_wide, cam_exam_wide, name='exam_wide'),
        Shot(110.0, 112.0, exam_two, cam_two, name='exam_two'),
        Shot(112.0, EV['roar'], paper_blank, None, name='blank'),
        Shot(EV['roar'], 116.6, roar, lambda t: (ROW[HERO_DESK][0] + 60, 520, 1.05 + 0.08 * t),
             name='roar'),
        Shot(116.6, m[0], eyes_shut, cam_face, name='shut'),
        Shot(m[0], m[0] + 0.3, memory('desk'), cam_desk_close(470, 610, 1.9, 1.95, 0.3), name='mem_desk'),
        Shot(m[0] + 0.3, m[1], eyes_shut, cam_face, name='shut2'),
        Shot(m[1], m[1] + 0.3, memory('shoes'), None, name='mem_shoes'),
        Shot(m[1] + 0.3, EV['write'] - 0.2, eyes_shut, cam_face, name='open'),
        Shot(EV['write'] - 0.2, EV['release'], paper_clear, None, name='write'),
        Shot(EV['release'], 122.0, exam_release, cam_release, name='release'),
    ]
