"""Act 2 (1:00-1:50): Day 1, posting, the grind, the success montage."""
from __future__ import annotations

import math

import skia

from act1 import BED_EYES, HIP_SEAT, MIRROR, audience_then, bed_phone, cam_push, corner
from common import (BEDROOM_FLOOR, G_SCALE, HERO_BEANIE, HERO_OFFICE_BEANIE, SHADE, STAND_HIP, bedroom, extra,
                    eyes_at, play_guitar, room, seated_legs, standing_legs, void)
from cues import BPM_GRIND, EV
from engine.captions import whisper
from engine.core import H, W, Track, beat_env, clamp, hrand, noise1, out_back, shake, smooth
from engine.draw import circle, col, cone, light_pool, limb, mixc, oval, paint, poly, rrect, text
from engine.fx import (dust_motes, eye_field, notes, puff, shards, sound_waves, word_projectile)
from engine.props import (buildings, cafe_table, chair, cubicle, guitar, guitar_case, guitar_local, mic_stand,
                          mirror_frame, noticeboard, office_desk, phone, riser, street_lamp, string_lights)
from engine.render import Shot
from engine.rig import blink, walk

HERO = HERO_BEANIE  # from Day 1 on he wears the beanie

# --- 7. Day 1: blowing off the dust (60-65) -------------------------------------------------------------

def day1_dust(c, t, T):
    void(c, 860, '#0A0A0D')
    light_pool(c, 980, 830, 700, 160, '#FFD9A0', 0.16)
    dust = 1.0 - 0.92 * smooth(EV['blow'], EV['blow'] + 0.9, T)
    twang = math.exp(-(T - EV['twang']) * 4) if T >= EV['twang'] else 0.0
    guitar(c, 880, 820, -4, 1.0, dust=dust, shine=1 - dust, strum=twang * 2.5, t=T)
    if dust < 0.5:
        for k in range(5):
            sp = beat_env(T, [EV['blow'] + 0.6 + k * 0.17], 0.25)
            if sp > 0.02:
                x, y = 820 + k * 40, 790 - (k % 2) * 20
                c.drawCircle(x, y, 10 * sp, paint('#FFF6E0', 0.9 * sp, blur=4, blend='add'))
    puff(c, 860, 800, T, EV['blow'], n=26, seed=12, color='#BDB6A8', size=36, spread=300, life=1.9, a=0.8,
         wind=(-300, -70))
    # his head leans in from the right
    enter = smooth(60.15, 60.9, T)
    hx = 1480 - 330 * enter + Track([(62.8, 0), (63.4, -30)])(T)
    hy = 745 + Track([(62.8, 0), (63.4, 20)])(T)
    blowing = smooth(EV['blow'] - 0.15, EV['blow'], T) * (1 - smooth(EV['blow'] + 0.8, EV['blow'] + 1.0, T))
    nod = math.sin((T - 63.7) * 8) * 4 * smooth(63.7, 63.9, T) * (1 - smooth(64.4, 64.8, T))
    face = dict(turn=-0.55, lx=-0.8, ly=Track([(60, 0.5), (62.6, 0.5), (63.2, 0.3)])(T),
                brow=Track([(60, 2), (62.6, 10)])(T), eye=blink(T, 12),
                smile=Track([(60, 0.0), (62.6, 0.1), (63.7, 0.45)])(T),
                mopen=0.32 * blowing, mwide=1.0 - 0.6 * blowing)
    HERO.draw_head(c, hx, hy, face, angle=-10 + nod, scale=1.45)
    # his hand turns a tuning peg
    if T > 62.9:
        reach = smooth(62.9, 63.4, T)
        hand = (1080 + 30 * (1 - reach), 800 + 120 * (1 - reach))
        limb(c, [(1210, 1100), (1160, 960), hand], 'hoodie', 22)
        circle(c, hand[0], hand[1], 15, 'skin', 'outline', 5)
    notes(c, 1060, 760, T, start=EV['twang'], end=EV['twang'] + 0.01, rate=1, life=1.6, seed=13, size=24,
          rise=200, drift=-1)


def cam_day1_dust(t):
    pan = smooth(2.8, 3.6, t)
    return (1000 + 60 * pan, 790 - 10 * pan, 1.9 + 0.3 * pan)


# --- 8. recording and posting (65-70) ---------------------------------------------------------------------

TRIPOD = (735, 735)


def day1_record(c, t, T):
    bedroom(c, T, dawn=0.55, lamp=0.0, moon=False)
    # tripod and phone, back toward us, red REC light
    tx, ty = TRIPOD
    for dx in (-36, 0, 36):
        c.drawLine(tx, ty + 40, tx + dx, BEDROOM_FLOOR, paint('#2B2B30', stroke=6))
    phone(c, tx, ty, 0, 1.25, face_down=True)
    if T >= EV['rec']:
        on = 0.6 + 0.4 * math.sin((T - EV['rec']) * 6)
        c.drawCircle(tx - 12, ty - 34, 6, paint('#FF3B36', on))
        c.drawCircle(tx - 12, ty - 34, 14, paint('red', 0.6 * on, blur=8, blend='add'))
    eye_field(c, eyes_at(T, BED_EYES[:6], EV['eyes_return'] + [67.4]), T)
    reach = smooth(67.3, 68.4, T)
    press = beat_env(T, [EV['tap_post']], 0.08)
    gp, mid, _ = play_guitar(T, strum=False, fret_shift=False)
    tgt_world = (tx + 8, ty + 6)
    local_tgt = (HIP_SEAT[0] - tgt_world[0], tgt_world[1] - HIP_SEAT[1])  # facing left
    fret = gp['hand_f']
    hand_f = (fret[0] + (local_tgt[0] - 4 * press - fret[0]) * reach, fret[1] + (local_tgt[1] - fret[1]) * reach)
    pose = dict(x=HIP_SEAT[0], y=HIP_SEAT[1], facing=-1, turn=0.4, **seated_legs(94, 40),
                lean=6 + 18 * reach, tilt=4 + 6 * reach, lx=-0.7, ly=0.3,
                brow=Track([(65, -6), (67.0, -12), (69.4, -16), (69.6, 8)])(T),
                smile=Track([(65, -0.1), (69.4, -0.3), (69.6, 0.2)])(T),
                sweat=smooth(66.4, 67.2, T) * (1 - smooth(69.5, 69.7, T)),
                shiver=0.8 * smooth(67.6, 68.2, T) * (1 - smooth(69.4, 69.5, T)),
                eye=blink(T, 14), hand_b=gp['hand_b'], hand_f=hand_f, back_arm_late=True)
    HERO.draw(c, pose, {'mid': mid}, t=T)


def cam_record(t):
    u = smooth(0, 4.6, t)
    return (840 - 30 * u, 640, 1.45 + 0.2 * u)


def post_closeup(c, t, T):
    void(c, None, '#0B0B0E')
    press = smooth(69.68, 69.76, T) * (1 - smooth(69.86, 69.95, T))

    def screen(cc, w, h):
        cc.drawPaint(paint('#151A22'))
        thumb = rrect(4, 8, w - 8, h * 0.42, 3)
        cc.drawRRect(thumb, paint('#0A0A0D'))
        light_pool(cc, w / 2, h * 0.28, w * 0.5, h * 0.2, 'warm', 0.5)
        cc.drawCircle(w / 2, h * 0.24, 4.5, paint('skin'))
        cc.drawRect(skia.Rect.MakeLTRB(w / 2 - 4, h * 0.27, w / 2 + 4, h * 0.38), paint('hoodie'))
        text(cc, 'my first song', w / 2, h * 0.58, 4.4, 'Fredoka', 'white')
        btn = rrect(5, h * 0.72, w - 10, h * 0.16, 5)
        cc.drawRRect(btn, paint(mixc('#F2A33A', '#FFE0A0', press)))
        text(cc, 'POST', w / 2, h * 0.72 + h * 0.16 * 0.72, 6.5, 'Fredoka', '#1A1A1A')

    phone(c, 960, 560, 0, 12.0, content=screen, glow=0.6)
    fx, fy = 1090 - 30 * press, 1010 - 40 * press
    limb(c, [(1400, 1500), (1240, 1200), (fx, fy)], 'hoodie', 70, ow=8)
    circle(c, fx, fy, 62, 'skin', 'outline', 8)
    if press > 0:
        light_pool(c, 960, 960, 400, 140, 'warm', 0.5 * press)


# --- 9a. practising while the eyes close (70-76) ---------------------------------------------------------

def practice(c, t, T):
    bedroom(c, T, lamp=1.0)
    close = [70.6 + k * 0.42 for k in range(len(BED_EYES))]
    eye_field(c, eyes_at(T, BED_EYES, 60.0, close), T)
    for k, (x, y, s, _) in enumerate(BED_EYES):
        shards(c, x, y, T, close[k] + 0.1, n=6, seed=40 + k, color='#FF5A50', size=5, speed=160, life=0.6)
    gp, mid, vib = play_guitar(T, bpm=BPM_GRIND, strum_amp=1.25)
    bob = math.sin(T * math.pi * 2)
    pose = dict(x=HIP_SEAT[0], y=HIP_SEAT[1], facing=-1, turn=0.42, **seated_legs(94, 40), **gp,
                lean=10 + 2 * bob, tilt=8 + 3 * bob, brow=12, smile=0.25, lx=-0.3, ly=0.4, eye=blink(T, 15),
                mouth='teeth' if 72.6 < T < 73.6 else 'curve')
    HERO.draw(c, pose, {'mid': mid}, t=T)
    gx, gy = HIP_SEAT[0] - 70, HIP_SEAT[1] - 60
    sound_waves(c, gx, gy, T, start=70.0, rate=2.0, life=1.2, max_r=420, arc=(140, 90), a=0.5)
    notes(c, gx, gy - 20, T, start=70.1, rate=3.0, life=2.4, seed=17, size=22, rise=320, drift=-1)
    word_projectile(c, 'cringe.', (600, 210), (760, 600), T, 72.5, dur=0.8, size=80, seed=3)


def cam_practice(t):
    u = smooth(0, 6, t)
    sx, sy = shake(t, 10 * (1 - smooth(0.0, 0.5, t)))
    return (860 + sx, 600 + sy, 1.32 + 0.12 * u)


# --- 9b. 12 views, "lol" (76-82) ---------------------------------------------------------------------------

def views_closeup(c, t, T):
    void(c, None, '#0B0B10')
    for k in range(9):
        x, y = 200 + k * 190, 300 + (k % 3) * 220
        c.drawCircle(x, y, 60 + (k % 2) * 30, paint('#FFC35E', 0.04, blur=30, blend='add'))
    tilt = Track([(76.0, 0), (77.8, 0), (78.6, 25)])(T)
    drop = Track([(76.0, 0), (77.8, 0), (78.6, 500)])(T)
    lol = out_back(clamp((T - EV['ding_lol']) / 0.3))

    def screen(cc, w, h):
        cc.drawPaint(paint('#151A22'))
        thumb = rrect(3, 6, w - 6, h * 0.38, 3)
        cc.drawRRect(thumb, paint('#0A0A0D'))
        light_pool(cc, w / 2, h * 0.24, w * 0.5, h * 0.2, 'warm', 0.5)
        cc.drawCircle(w / 2, h * 0.2, 4, paint('skin'))
        text(cc, 'my first song', 4, h * 0.5, 4.4, 'Fredoka', 'white', align='left')
        text(cc, '12 views', 4, h * 0.58, 3.8, 'Inter-Bold', '#9AA3B2', align='left')
        cc.drawLine(4, h * 0.63, w - 4, h * 0.63, paint('#2A3140', stroke=0.6))
        if lol > 0:
            cc.save()
            cc.translate(4, h * 0.72)
            cc.scale(lol, lol)
            cc.drawCircle(3.5, -1.5, 3.2, paint('#7A7A84'))
            text(cc, 'user_4471', 9, -2.5, 2.9, 'Inter-Bold', '#9AA3B2', align='left')
            text(cc, 'lol', 9, 2.6, 4.6, 'Inter', 'white', align='left')
            cc.restore()

    phone(c, 960, 520 + drop, tilt, 11.0, content=screen, glow=0.5)
    limb(c, [(1500, 1400), (1300, 1150), (1180 - tilt * 3, 900 + drop)], 'hoodie', 66, ow=8)
    circle(c, 1180 - tilt * 3, 900 + drop, 58, 'skin', 'outline', 8)


def phone_down(c, t, T):
    bedroom(c, T, lamp=1.0)
    eye_field(c, eyes_at(T, BED_EYES[6:10], 78.0, [80.4, 80.9, 81.3, 81.7]), T)
    put = smooth(78.7, 79.3, T)
    resume = smooth(79.5, 79.9, T)
    gp, mid, vib = play_guitar(T, bpm=BPM_GRIND, strum=T > 79.9, strum_amp=1.1)
    bed_spot = (-80, -6)
    if T < 79.4:
        start = (54, -110)
        hand_f = (start[0] + (bed_spot[0] - start[0]) * put, start[1] + (bed_spot[1] - start[1]) * put)
        ph = hand_f
    else:
        hand_f = (bed_spot[0] + (gp['hand_f'][0] - bed_spot[0]) * resume, bed_spot[1] + (gp['hand_f'][1] - bed_spot[1]) * resume)
        ph = bed_spot
    pose = dict(x=HIP_SEAT[0], y=HIP_SEAT[1], facing=-1, turn=0.42, **seated_legs(94, 40),
                lean=8, tilt=Track([(78.6, 14), (79.6, 4)])(T), hand_b=gp['hand_b'], hand_f=hand_f,
                back_arm_late=True, brow=Track([(78.6, -6), (79.2, 12)])(T),
                smile=Track([(78.6, -0.2), (79.4, 0.0), (80.2, 0.3)])(T), lx=Track([(78.6, 0.2), (79.4, -0.4)])(T),
                ly=0.3, eye=blink(T, 16))

    def front(cc, j):
        if T < 79.4:
            phone(cc, ph[0], ph[1] - 10, 90 * put, 1.0, face_down=put > 0.5, glow=0.5 * (1 - put))

    def behind(cc, j):
        if T >= 79.4:
            phone(cc, ph[0], ph[1] - 4, 90, 1.0, face_down=True)

    HERO.draw(c, pose, {'mid': mid, 'front': front, 'behind': behind}, t=T)
    if T > 79.9:
        gx, gy = HIP_SEAT[0] - 70, HIP_SEAT[1] - 60
        notes(c, gx, gy - 20, T, start=80.0, rate=3.0, life=2.2, seed=19, size=22, rise=300, drift=-1)
        sound_waves(c, gx, gy, T, start=80.0, rate=2.0, life=1.2, max_r=420, arc=(140, 90), a=0.45)


# --- 9c. busking (82-90) ---------------------------------------------------------------------------------

STREET_FLOOR = 900


def busking(c, t, T):
    sky = skia.GradientShader.MakeLinear(points=[(0, -200), (0, STREET_FLOOR)],
                                        colors=[col('#05060B'), col('#141A2A')])
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, W + 400, STREET_FLOOR), paint('#000000', shader=sky))
    buildings(c, -400, W + 400, 800, seed=5, t=T)
    c.drawRect(skia.Rect.MakeLTRB(-400, 800, W + 400, STREET_FLOOR), paint('#1C1D23'))
    c.drawRect(skia.Rect.MakeLTRB(-400, STREET_FLOOR, W + 400, H + 400), paint('#0E0E12'))
    c.drawLine(-400, STREET_FLOOR, W + 400, STREET_FLOOR, paint('#3A3B44', stroke=4))
    eye_field(c, eyes_at(T, [(120, 520, 60, 18), (260, 640, 54, 24)], 82.0, [88.3, 88.7]), T)
    street_lamp(c, 760, STREET_FLOOR, 560)
    coin_t = T - EV['coin'] if T >= EV['coin'] else None
    guitar_case(c, 1090, STREET_FLOOR, coins=3 + (1 if T > EV['coin'] + 0.6 else 0), coin_t=coin_t, t=T)
    # passers-by
    walkers = [
        (4, Track([(82.0, -250), (88.0, 2250, 'linear')]), 1, True),
        (5, Track([(83.0, 2250), (89.6, -250, 'linear')]), -1, True),
    ]
    for idx, xt, facing, on_phone in walkers:
        x = xt(T)
        pose = walk(T, 0.9, 24, idx)
        pose.update(x=x, y=STREET_FLOOR - STAND_HIP, facing=facing, turn=0.3, tilt=16, ly=0.7, smile=0.0,
                    hand_f=(40, -70))
        extra(idx).draw(c, pose, {'front': (lambda cc, j: phone(cc, j['hand_f'][0] + 4, j['hand_f'][1] - 30, 0, 0.8, glow=0.7))}, t=T)
    # the listener who stops
    lx = Track([(84.0, -250), (86.0, 1330, 'out_quad')])(T)
    stopped = T >= 86.0
    lp = dict(x=lx, y=STREET_FLOOR - STAND_HIP, facing=-1, turn=0.45)
    if not stopped:
        lp.update(walk(T, 0.9, 24, 3))
    else:
        toss = smooth(87.0, 87.4, T) * (1 - smooth(87.6, 88.0, T))
        lp.update(standing_legs(), eyes='happy', smile=0.6, tilt=-4 + 3 * math.sin(T * 3.2), sb=6,
                  sf=10 + 90 * toss, ef=20 - 10 * toss)
    extra(6).draw(c, lp, t=T)
    # the hero
    gp, mid, vib = play_guitar(T, seated=False, bpm=BPM_GRIND)
    noticed = smooth(87.7, 88.0, T)
    HERO.draw(c, dict(x=900, y=STREET_FLOOR - STAND_HIP, facing=1, turn=0.42, **standing_legs(), **gp,
                      eyes='happy' if noticed > 0.5 else 'dot', smile=0.25 + 0.4 * noticed, brow=6 - 6 * noticed,
                      lx=0.4, ly=0.2, tilt=4 * math.sin(T * math.pi * 2), eye=blink(T, 17)), {'mid': mid}, t=T)
    notes(c, 960, 700, T, start=82.1, rate=2.5, life=2.6, seed=21, size=22, rise=320)


def cam_busking(t):
    u = smooth(0, 8, t)
    return (980, 610, 1.18 + 0.1 * u)


# --- 9d. open mic: his music shatters their words (90-98) ----------------------------------------------------

CAFE_FLOOR = 900


def open_mic(c, t, T):
    room(c, CAFE_FLOOR, wall='#18120F', floor='#100C0A')
    string_lights(c, -100, W + 100, 120, sag=50, n=22, t=T)
    text(c, 'OPEN MIC', 470, 330, 84, 'Fredoka', '#FFB347', 0.85, glow='warm', glow_a=0.6, glow_r=18)
    for k, sx in enumerate((-40, 90, 220)):
        SHADE.draw(c, dict(x=sx, y=CAFE_FLOOR - STAND_HIP * 1.05, scale=1.05, turn=0.4, eye=1.0,
                           lean=6, tilt=6 + 4 * math.sin(T * 1.4 + k), sf=40 + 30 * math.sin(T * 2 + k), ef=40),
                   t=T)
    top = riser(c, 1120, 2100, CAFE_FLOOR, 44)
    cone(c, (1400, -40), 40, top, 260, 'warm', 0.14, soft=34)
    light_pool(c, 1400, top, 300, 40, 'warm', 0.35)
    mic = mic_stand(c, 1470, top, 300)
    # audience
    seated = dict(hb=88, kb=88, hf=86, kf=86)
    clap = abs(math.sin(T * 7)) * smooth(96.6, 96.8, T)
    for x in (430, 800):
        cafe_table(c, x, CAFE_FLOOR)
    people = [
        (7, 340, 1, dict(tilt=16, ly=0.7, hand_f=(56, -58), smile=0.0)),
        (8, 520, -1, dict(eyes='happy', smile=0.5, tilt=4 * math.sin(T * 3), turn=0.5,
                          hand_b=(60, -60 - 6 * clap), hand_f=(74 - 14 * clap, -62))),
        (9, 700, 1, dict(turn=0.5, smile=0.4, mopen=0.2 * abs(math.sin(T * 6)), lx=0.4)),
        (10, 900, -1, dict(eyes='happy' if clap > 0 else 'dot', smile=0.35, turn=0.5,
                           hand_b=(60, -60 - 6 * clap), hand_f=(74 - 14 * clap, -62))),
    ]
    for idx, x, facing, extra_pose in people:
        chair(c, x, CAFE_FLOOR, -facing, '#3A2E26')
        pose = dict(x=x, y=CAFE_FLOOR - 104, facing=facing, **seated, **extra_pose)
        layers = None
        if idx == 7:
            layers = {'front': lambda cc, j: phone(cc, j['hand_f'][0] + 4, j['hand_f'][1] - 30, -10, 0.8, glow=0.8)}
        extra(idx).draw(c, pose, layers, t=T)
    gp, mid, vib = play_guitar(T, seated=False, bpm=BPM_GRIND)
    HERO.draw(c, dict(x=1390, y=top - STAND_HIP, facing=-1, turn=0.4, **standing_legs(), **gp,
                      eyes='closed' if (T % 4) < 1.6 else 'dot', smile=0.3, mopen=0.15 + 0.35 * abs(math.sin(T * 5.3)),
                      brow=8, tilt=-4 + 3 * math.sin(T * math.pi * 2)), {'mid': mid}, t=T)
    gx, gy = 1320, top - 160
    sound_waves(c, gx, gy, T, start=90.0, rate=2.0, life=1.4, max_r=760, arc=(150, 60), a=0.55)
    notes(c, gx - 20, gy - 40, T, start=90.1, rate=2.4, life=2.6, seed=23, size=22, rise=300, drift=-1)
    for k, (word, t0) in enumerate((('nobody cares.', 91.6), ('embarrassing.', 93.2), ('quit.', 94.8))):
        word_projectile(c, word, (260, 420 + k * 50), (820, 470 + k * 30), T, t0, dur=0.85, size=76, seed=50 + k)


def cam_open_mic(t):
    u = smooth(0, 8, t)
    return (900, 590, 1.08 + 0.08 * u)


# --- 9e. success montage, mirroring the wasted years (98-110) --------------------------------------------------

def corner_happy(c, t, T):
    corner(c, t, T, 0.0, 0.0, eyes=False)
    light_pool(c, 1060, 640, 380, 360, 'warm', 0.22)
    notes(c, 1060, 640, T, start=97.9, rate=2.0, life=2.2, seed=29, size=22, rise=260)


def office_happy(c, t, T):
    room(c, 900, wall='#0F1015')
    cubicle(c, 300, 1500, 900)
    top = office_desk(c, 820, 900, 460, t=T)
    chair(c, 760, 900, 1, '#2A2C33')
    pad = rrect(880, top - 10, 120, 10, 2)
    c.drawRRect(pad, paint('#F4F0E6'))
    write = math.sin(T * 14)
    HERO_OFFICE_BEANIE.draw(c, dict(x=770, y=900 - 108, facing=1, lean=10, tilt=8, turn=0.45, eyes='happy',
                                    smile=0.6, brow=4, hb=88, kb=88, hf=84, kf=84,
                                    hand_b=(118, -72), hand_f=(136 + 10 * write, -82),
                                    foot_b=(50, 104), foot_f=(66, 104)), t=T)
    notes(c, 930, top - 30, T, start=100.0, rate=2.5, life=1.8, seed=31, size=18, rise=200)


def mirror_happy(c, t, T):
    room(c, 940, wall='#121418')
    for gx in range(0, W + 1, 96):
        c.drawLine(gx, -100, gx, 940, paint('#1A1D22', stroke=2))
    for gy in range(-100, 940, 96):
        c.drawLine(0, gy, W, gy, paint('#1A1D22', stroke=2))
    cone(c, (960, -60), 60, 940, 520, '#FFE2B0', 0.07, soft=40)
    mx, my, rx, ry = MIRROR
    clip = skia.Path()
    clip.addOval(oval(mx, my, rx, ry))
    c.drawPath(clip, paint('#0E1013'))
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    light_pool(c, mx, my - 40, rx * 1.3, ry, 'warm', 0.14)
    nod = math.sin((T - 106.4) * 9) * 5 * smooth(106.4, 106.6, T) * (1 - smooth(107.0, 107.3, T))
    HERO.draw(c, dict(x=mx, y=my + 245, scale=0.98, facing=1, turn=0.0, eyes='dot', smile=0.6, brow=6,
                      tilt=nod, sb=6, sf=-6, **standing_legs(), eye=blink(T, 18)), t=T)
    c.restore()
    mirror_frame(c, mx, my, rx, ry)
    c.drawRRect(rrect(mx - 260, my + ry + 40, 520, 40, 10), paint('#D9DCE2'))
    c.drawRRect(rrect(mx - 260, my + ry + 40, 520, 40, 10), paint('outline', stroke=4))


def signup_again(c, t, T):
    from act1 import BOARD, HALL_FLOOR, lockers
    room(c, HALL_FLOOR, wall='#13131A')
    light_pool(c, 1340, 340, 520, 320, 'warm', 0.24)
    lockers(c, 60, 760, HALL_FLOOR, 6)
    write = smooth(108.3, 109.6, T)
    noticeboard(c, BOARD[0], BOARD[1], names=3, extra_name=write, t=T)
    for i, sx in enumerate((520, 660, 800)):
        s = 0.42 - 0.1 * smooth(108.0, 110.0, T)
        SHADE.draw(c, dict(x=sx, y=HALL_FLOOR - STAND_HIP * s, scale=s, turn=0.2, eye=0.7, tilt=10,
                           alpha=1 - smooth(108.8, 110.0, T)), t=T)
    scrib = math.sin(T * 18) * 6 * (write > 0 and write < 1)
    hand = (90 + 90 * write * 0.9, -131 + scrib)
    from act1 import _pen
    HERO.draw(c, dict(x=1180, y=HALL_FLOOR - STAND_HIP, facing=1, **standing_legs(), hand_f=hand, sb=4, eb=10,
                      turn=0.35, brow=10, smile=0.55, lx=0.4, ly=-0.1, eye=blink(T, 19)),
              {'front': lambda cc, j: _pen(cc, j['hand_f'])}, t=T)


# --- assemble -------------------------------------------------------------------------------------------------

def shots():
    def bp(happy):
        return lambda c, t, T: bed_phone(c, t, T, happy=happy)

    def aud(on_stage):
        return lambda c, t, T: audience_then(c, t, T, hero_on_stage=on_stage)

    return [
        Shot(60.0, 65.0, day1_dust, cam_day1_dust, name='day1_dust'),
        Shot(65.0, 69.6, day1_record, cam_record, name='record'),
        Shot(69.6, 70.0, post_closeup, None, name='post'),
        Shot(70.0, 76.0, practice, cam_practice, name='practice'),
        Shot(76.0, 78.6, views_closeup, cam_push(960, 560, 1.0, 1.05, 2.6), name='views'),
        Shot(78.6, 82.0, phone_down, cam_push(860, 610, 1.4, 1.5, 3.4), name='phone_down'),
        Shot(82.0, 90.0, busking, cam_busking, name='busking'),
        Shot(90.0, 98.0, open_mic, cam_open_mic, name='open_mic'),
        Shot(98.0, 100.0, corner_happy, cam_push(1070, 690, 1.75, 1.9, 2.0), name='corner_happy'),
        Shot(100.0, 102.0, office_happy, cam_push(930, 660, 1.38, 1.46, 2.0), name='office_happy'),
        Shot(102.0, 104.0, aud(True), cam_push(990, 640, 1.12, 1.18, 2.0), name='stage_then'),
        Shot(104.0, 106.0, bp(True), cam_push(1060, 700, 1.5, 1.6, 2.0), name='phone_happy'),
        Shot(106.0, 108.0, mirror_happy, cam_push(960, 470, 1.14, 1.22, 2.0), name='mirror_happy'),
        Shot(108.0, 110.0, signup_again, cam_push(1060, 590, 1.3, 1.4, 2.0), name='signup_again'),
    ]
