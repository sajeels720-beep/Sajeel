"""Act 1 (0:00-1:00): the song, the eyes, the years, the mirror, rock bottom."""
from __future__ import annotations

import math

import skia

from common import (BED_W, BED_X, BEDROOM_FLOOR, G_SCALE, HERO, HERO_OFFICE, SHADE, STAND_HIP, bedroom, extra,
                    eyes_at, play_guitar, room, scatter_spots, seated_legs, standing_legs, void)
from cues import EV, JOY_BPM
from engine.captions import whisper
from engine.core import H, W, Track, clamp, hrand, hrange, noise1, poses, shake, smooth
from engine.draw import col, cone, light_pool, mixc, oval, paint, poly, rrect, text
from engine.fx import dust_motes, eye_field, notes, shards
from engine.props import (chair, cobweb, cracks, cubicle, guitar, mirror_frame, noticeboard, office_desk, phone,
                          shelf, stage_floor, window)
from engine.render import Shot
from engine.rig import blink, idle, walk

HIP_SEAT = (858, 738)  # pelvis on the foot end of the bed, facing the window

# --- 1. bedroom: the song, then the eyes (0-22) --------------------------------------------------

BED_EYES = [(150, 190, 78, 18), (600, 170, 70, 22), (640, 560, 74, 14), (1180, 150, 80, 20),
            (1640, 330, 86, 16), (1730, 650, 72, 24), (470, 660, 64, 20), (1520, 120, 70, 18),
            (90, 560, 82, 15), (1050, 290, 66, 22), (1560, 520, 60, 20), (330, 90, 64, 24)]


def bedroom_night(c, t, T):
    snapped = T >= EV['snap']
    lamp = 1.0 - 0.62 * smooth(15.0, 16.2, T) + (0.08 * noise1(T * 9, 2) if 15.0 < T < 16.6 else 0)
    red = smooth(14.3, 15.8, T)
    bedroom(c, T, lamp=lamp, red=red)

    # pose
    g_start = EV['guitar_down']
    playing = T < EV['snap']
    gp, mid, vib = play_guitar(T - 0.6, bpm=JOY_BPM, strum=playing, strum_amp=0.45)
    base = dict(x=HIP_SEAT[0], y=HIP_SEAT[1], facing=-1, turn=0.42, **seated_legs(94, 40))
    if not snapped:
        bob = math.sin(T * math.pi * JOY_BPM / 60.0)
        pose = dict(base, lean=8 + 2 * math.sin(T * 0.9), tilt=12 + 3 * bob, eyes='happy', smile=0.65,
                    brow=-4, **gp)
    else:
        look = Track([(14.0, 0.0), (14.5, -0.9), (15.4, 0.8), (16.3, -0.6), (17.3, 0.7), (18.4, -0.3),
                      (19.5, 0.2), (20.6, 0.0)])(T)
        react = dict(base, lean=Track([(14.0, 8), (14.3, 2), (20.0, 4), (21.2, 16)])(T),
                     tilt=Track([(14.0, 12), (14.25, -4), (19.8, 0), (21.3, 24)])(T),
                     eye=1.0 * blink(T, 3), lx=look, ly=Track([(14.0, 0), (20.4, 0), (21.3, 0.7)])(T),
                     brow=Track([(14.0, -4), (14.3, -14), (19.0, -18), (21.0, -24)])(T),
                     smile=Track([(14.0, 0.6), (14.3, -0.1), (17.0, -0.35), (21.0, -0.55)])(T),
                     mopen=Track([(14.0, 0.0), (14.15, 0.28), (14.7, 0.0)])(T),
                     sweat=smooth(15.0, 15.8, T), shiver=0.6 * smooth(15.4, 16.0, T))
        # put the guitar down behind him on the bed
        u = smooth(g_start, g_start + 1.2, T)
        if u <= 0:
            pose = dict(react, **gp)
        else:
            from engine.props import guitar_local
            gx = 26 + (-160 - 26) * u
            gy = -34 + (-4 + 34) * u - 40 * math.sin(math.pi * u)
            ang = -22 + (6 + 22) * u
            hand_g = guitar_local(gx, gy, ang, G_SCALE, 30, 0)
            rest_b, rest_f = (34, -6), (52, -4)
            hb = hand_g if u < 0.75 else (rest_b[0] + (hand_g[0] - rest_b[0]) * (1 - smooth(0.75, 1.0, u)),
                                          rest_b[1] + (hand_g[1] - rest_b[1]) * (1 - smooth(0.75, 1.0, u)))
            hf = (rest_f[0] + (hand_g[0] + 40 - rest_f[0]) * (1 - u), rest_f[1] + (hand_g[1] - rest_f[1]) * (1 - u))
            pose = dict(react, hand_b=hb, hand_f=hf, back_arm_late=False)

            def mid(c2, j, gx=gx, gy=gy, ang=ang):
                guitar(c2, gx, gy, ang, G_SCALE)

            if u > 0.55:
                layers = {'behind': mid}
                HERO.draw(c, pose, layers, t=T)
                _bedroom_fx(c, t, T)
                return
    HERO.draw(c, pose, {'mid': mid}, t=T)
    _bedroom_fx(c, t, T)


def _bedroom_fx(c, t, T):
    gx, gy = HIP_SEAT[0] - 70, HIP_SEAT[1] - 70
    notes(c, gx, gy, T, start=0.7, rate=1.5, life=3.2, seed=11, size=21, rise=300,
          freeze_at=EV['snap'], fall=EV['notes_fall'], drift=-1.0)
    for k in range(5):
        shards(c, gx - 120 + k * 60, BEDROOM_FLOOR - 4, T, EV['notes_fall'] + 0.35 + k * 0.05, n=8, seed=20 + k,
               color='warm', size=7, speed=260, life=0.9)
    eye_field(c, eyes_at(T, BED_EYES, EV['eyes_open'] + [17.8, 18.2]), T)
    whisper(c, T, 'cringe.', 15.0, 17.0, 600, 290, 76, seed=1)
    whisper(c, T, 'who does he think he is?', 16.6, 19.2, 1240, 260, 70, seed=2)
    whisper(c, T, 'everyone’s gonna laugh.', 18.6, 21.0, 520, 975, 70, seed=3)


def cam_bedroom_a(t):
    u = smooth(0, 14, t)
    return (870 - 30 * u, 600 + 10 * u, 1.42 + 0.16 * u)


def cam_bedroom_b(t):
    u = smooth(0, 8, t)
    sx, sy = shake(t, 3 * (1 - smooth(0, 1.2, t)))
    return (960 + sx, 520 + sy, 0.94 + 0.05 * u)


# --- 2. the sign-up sheet (22-29) -------------------------------------------------------------------

HALL_FLOOR = 880
BOARD = (1080, 420)


def lockers(c, x0, x1, floor_y, n=6):
    w = (x1 - x0) / n
    for k in range(n):
        x = x0 + k * w
        r = rrect(x + 4, floor_y - 380, w - 8, 380, 4)
        c.drawRRect(r, paint('#1E2430'))
        c.drawRRect(r, paint('outline', stroke=4))
        for v in range(4):
            c.drawLine(x + w * 0.3, floor_y - 350 + v * 12, x + w * 0.7, floor_y - 350 + v * 12, paint('#11151C', stroke=4))
        c.drawRRect(rrect(x + w - 26, floor_y - 210, 8, 30, 3), paint('#7C8494'))


def signup(c, t, T):
    room(c, HALL_FLOOR, wall='#13131A')
    light_pool(c, 1340, 340, 520, 320, 'warm', 0.18)
    cone(c, (1340, -20), 40, HALL_FLOOR, 360, 'warm', 0.07, soft=40)
    lockers(c, 60, 760, HALL_FLOOR, 6)
    noticeboard(c, BOARD[0], BOARD[1], names=3, t=T)

    # shadow crowd behind him
    for i, (sx, sc_) in enumerate([(380, 1.06), (520, 1.14), (660, 1.02), (800, 1.12), (930, 1.05)]):
        lean_in = smooth(22.0, 26.0, T) * 10
        o = smooth(22.4 + i * 0.2, 22.7 + i * 0.2, T)
        SHADE.draw(c, dict(x=sx + lean_in * 3, y=HALL_FLOOR - STAND_HIP * sc_, scale=sc_, lean=4 + lean_in,
                           tilt=6 + 4 * math.sin(T * 1.3 + i), eye=o, turn=0.2, sb=6, sf=-6,
                           alpha=0.4 + 0.6 * smooth(22.0, 23.0 + i * 0.2, T)), t=T)

    hip_x = 1180 + Track([(27.3, 0), (29.0, -420, 'linear')])(T)
    walking = T >= EV['walk_away']
    pen_tgt = (82 + noise1(T * 12, 4) * 4 * smooth(23.0, 24.0, T), -131 + noise1(T * 12, 5) * 4)
    base = dict(x=hip_x, y=HALL_FLOOR - STAND_HIP, **standing_legs())
    if T < 27.15:
        down = smooth(EV['pen_down'], EV['pen_down'] + 0.5, T)
        hand = (pen_tgt[0] + (24 - pen_tgt[0]) * down, pen_tgt[1] + (-12 - pen_tgt[1]) * down)
        pose = dict(base, facing=1, hand_f=hand, sb=4, eb=10, lean=2 + 6 * down,
                    turn=Track([(22.0, 0.35), (23.5, 0.35), (23.9, 0.05), (24.6, 0.3), (25.4, 0.05), (26.0, 0.35)])(T),
                    lx=Track([(22.0, 0.3), (23.5, 0.3), (23.9, -0.9), (24.6, 0.4), (25.4, -0.9), (26.0, 0.0)])(T),
                    brow=Track([(22.0, 0), (23.8, -16), (26.6, -22)])(T),
                    smile=Track([(22.0, 0.2), (23.8, -0.2), (26.6, -0.5)])(T),
                    tilt=10 * down, sweat=smooth(24.0, 24.8, T), eye=blink(T, 4))
        layers = {'front': lambda cc, j: _pen(cc, j['hand_f'])}
    else:
        pose = dict(base, facing=-1, **walk(T - 27.15, 0.8, 22), lean=10, tilt=16, brow=-22, smile=-0.5,
                    turn=0.3, ly=0.6)
        layers = None
    HERO.draw(c, pose, layers, t=T)
    whisper(c, T, 'you? on stage?', 23.6, 25.6, 470, 420, 56, seed=4)
    whisper(c, T, 'don’t embarrass yourself.', 25.4, 27.6, 800, 380, 54, seed=5)


def _pen(c, hand):
    x, y = hand
    c.drawLine(x - 4, y + 4, x + 20, y - 22, paint('#2E4FA0', stroke=7))
    c.drawLine(x + 20, y - 22, x + 25, y - 28, paint('#D9D3C4', stroke=4))


def cam_signup(t):
    u = smooth(0, 7, t)
    follow = smooth(5.2, 7.0, t)
    return (1000 - 260 * follow, 590, 1.24 + 0.08 * u)


# --- 3. the wasted years montage (29-40) ----------------------------------------------------------------

CORNER_FLOOR = 900


def corner(c, t, T, dust, web, broken=False, eyes=True):
    room(c, CORNER_FLOOR, wall='#101016')
    # the side wall falls into shadow gradually (no hard seam at the corner)
    shade = skia.GradientShader.MakeLinear(points=[(1120, 0), (1400, 0)],
                                          colors=[col('#000000', 0.0), col('#000000', 0.35)])
    c.drawRect(skia.Rect.MakeLTRB(1120, -100, 2400, CORNER_FLOOR), paint('#000000', shader=shade))
    light_pool(c, 980, 700, 420, 380, 'moon', 0.10)
    c.drawPath(poly([(400, -50), (700, -50), (1240, CORNER_FLOOR), (820, CORNER_FLOOR)], True),
               paint('moon', 0.05, blur=40, blend='add'))
    guitar(c, 1060, 810, -78, 1.0, dust=dust, shine=1 - dust)
    if broken:
        path = skia.Path()
        path.moveTo(1092, 600)
        path.cubicTo(1130, 640, 1080, 690, 1120, 720)
        c.drawPath(path, paint('#EDE7DA', 0.8, stroke=1.4))
    if web > 0:
        cobweb(c, 1180, 470, 150 * web, a=0.75 * web, corner='tr')
        cobweb(c, 1180, CORNER_FLOOR, 90 * web, a=0.5 * web, corner='br')
    dust_motes(c, 600, 300, 1300, 880, T, n=40, seed=31, color='#C9D4FF', a=0.35, speed=6)
    if eyes:
        eye_field(c, eyes_at(T, [(1420, 260, 64, 20)], [EV['montage_cuts'][0] - 0.1]), T)


def office(c, t, T):
    room(c, 900, wall='#0F1015')
    cubicle(c, 300, 1500, 900)
    eye_field(c, eyes_at(T, [(500, 420, 46, 18), (1560, 300, 52, 22)], [30.8]), T)
    top = office_desk(c, 820, 900, 460, t=T)
    chair(c, 760, 900, 1, '#2A2C33')
    typing = math.sin(T * 26)
    HERO_OFFICE.draw(c, dict(x=770, y=900 - 108, facing=1, lean=16, tilt=14, turn=0.4, eyes='tired', bags=1,
                             brow=-12, smile=-0.3, hb=88, kb=88, hf=84, kf=84,
                             hand_b=(118, -70 + 4 * typing), hand_f=(150, -72 - 4 * typing),
                             foot_b=(50, 104), foot_f=(66, 104)), t=T)


def audience_then(c, t, T, hero_on_stage=False):
    """Hero watches someone else perform (or, later, performs himself)."""
    void(c, 760, '#09090C')
    stage_floor(c, 1040, 2100, 700, 50)
    cone(c, (1480, -40), 30, 700, 260, 'warm', 0.18, soft=30)
    light_pool(c, 1480, 700, 300, 50, 'warm', 0.4)
    from common import HERO_BEANIE
    perf = HERO_BEANIE if hero_on_stage else extra(3)
    gp, mid, vib = play_guitar(T, seated=False, bpm=100 if hero_on_stage else 90)
    perf.draw(c, dict(x=1480, y=700 - STAND_HIP, facing=-1, turn=0.3, eyes='closed' if not hero_on_stage else 'happy',
                      smile=0.5, mopen=0.4 + 0.3 * math.sin(T * 7), **standing_legs(), **gp), {'mid': mid}, t=T)
    # two rows of seated silhouettes; the hero sits in the back row, the front row hides his legs
    rows = [(930, 1.0, '#1A1B21'), (1010, 1.08, '#141519')]

    def row_of(row):
        y, s, shade = rows[row]
        for k in range(7):
            x = 80 + k * 170 + row * 70
            if row == 0 and k == 3:
                continue
            c.drawRRect(rrect(x - 50, y - 120 * s, 100, 160, 30), paint(shade))
            c.drawCircle(x, y - 160 * s, 46 * s, paint(shade))

    row_of(0)
    clap = abs(math.sin(T * (5 if not hero_on_stage else 6)))
    if not hero_on_stage:
        light_pool(c, 640, 700, 260, 240, 'warm', 0.14)
        HERO.draw(c, dict(x=590, y=880, facing=1, turn=0.55, hb=88, kb=88, hf=86, kf=86, lean=-4, tilt=-4,
                          hand_b=(70, -62 - 8 * clap), hand_f=(84 - 14 * clap, -64), eyes='tired', bags=0.8,
                          brow=-14, smile=-0.25, lx=0.6), t=T)
        eye_field(c, eyes_at(T, [(300, 640, 60, 18), (870, 610, 56, 24)], [32.7]), T)
    else:
        extra(2).draw(c, dict(x=590, y=880, facing=1, turn=0.55, hb=88, kb=88, hf=86, kf=86,
                              hand_b=(70, -62 - 8 * clap), hand_f=(84 - 14 * clap, -64), eyes='happy', smile=0.6),
                      t=T)
    row_of(1)


def bed_phone(c, t, T, happy=False):
    """Lying in bed at night, face lit by the phone (head on the pillow, body under the blanket)."""
    from common import HERO_BEANIE
    from engine.props import bed
    fy = 880
    room(c, fy, wall='#0F0F15')
    window(c, 260, 220, 240, 270, t=T)
    if not happy:
        eye_field(c, eyes_at(T, [(380, 330, 64, 18)], [36.2]), T)
    top = bed(c, 700, fy, 620, height=110)
    who = HERO_BEANIE if happy else HERO
    hx, hy = 1150, top - 34
    scroll = math.sin(T * 3.0)
    face = dict(turn=-0.25, eyes='happy' if happy else 'tired', bags=0 if happy else 1,
                smile=0.65 if happy else -0.25, brow=2 if happy else -12, lx=-0.7, ly=0.2,
                eye=1.0 if happy else blink(T, 9))
    who.draw_head(c, hx, hy, face, angle=-18)
    # blanket over the body, tucked under the chin
    path = skia.Path()
    path.moveTo(760, top + 6)
    path.cubicTo(860, top - 70, 1010, top - 60, 1080, top - 20)
    path.cubicTo(1120, top + 6, 1150, top + 14, 1200, top + 10)
    path.lineTo(1200, top + 62)
    path.lineTo(760, top + 62)
    path.close()
    c.drawPath(path, paint('#4B4F7A'))
    c.drawPath(path, paint('outline', stroke=4.5))
    c.drawLine(820, top - 8, 1040, top - 30, paint('#3B3F66', stroke=4))
    # hand and phone in front of the face; we see the back of the phone and the glow on his face
    px, py = 1030 + 2 * scroll, top - 70
    light_pool(c, hx - 20, hy, 180, 150, '#9CC8FF', 0.32 if not happy else 0.26)
    phone(c, px, py, -12, 1.15, face_down=True)
    from engine.draw import circle
    circle(c, px + 6, py + 34, 13, 'skin', 'outline', 4.5)
    c.drawRRect(rrect(px - 21, py - 40, 6, 6, 2), paint('#9CC8FF', 0.9, blur=4, blend='add'))
    if happy:
        _views_bubble(c, px - 160, py - 190, T)


def _views_bubble(c, x, y, T):
    """Pop-up card: his video's views and a kind comment."""
    from engine.core import out_back
    s = out_back(min(1.0, max(0.0, (T - 104.3) / 0.35)))
    if s <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    card = rrect(-150, -70, 300, 140, 22)
    c.drawRRect(card, paint('#F4F1EA'))
    c.drawRRect(card, paint('outline', stroke=4.5))
    text(c, '1,204 views', 0, -18, 40, 'Fredoka', '#222222')
    text(c, '"this gave me chills"', 0, 34, 30, 'PatrickHand', '#C2413A')
    c.restore()


def montage_shot(kind):
    def draw(c, t, T):
        if kind == 'corner1':
            corner(c, t, T, 0.35, 0.0)
        elif kind == 'office':
            office(c, t, T)
        elif kind == 'audience':
            audience_then(c, t, T)
        elif kind == 'corner2':
            corner(c, t, T, 0.7, 0.5)
        elif kind == 'phone':
            bed_phone(c, t, T)
        elif kind == 'corner3':
            corner(c, t, T, 1.0, 1.0, broken=True)
    return draw


def cam_push(cx, cy, z0, z1, dur):
    def cam(t):
        u = smooth(0, dur, t)
        return (cx, cy, z0 + (z1 - z0) * u)
    return cam


# --- 4. the mirror (40-50) -----------------------------------------------------------------------------

MIRROR = (960, 410, 270, 330)


def mirror(c, t, T):
    room(c, 940, wall='#121418')
    for gx in range(0, W + 1, 96):
        c.drawLine(gx, -100, gx, 940, paint('#1A1D22', stroke=2))
    for gy in range(-100, 940, 96):
        c.drawLine(0, gy, W, gy, paint('#1A1D22', stroke=2))
    cone(c, (960, -60), 60, 940, 520, '#CFE0FF', 0.06, soft=40)
    mx, my, rx, ry = MIRROR
    crack = smooth(EV['crack'], EV['crack'] + 0.25, T)
    clip = skia.Path()
    clip.addOval(oval(mx, my, rx, ry))
    c.drawPath(clip, paint('#0B0D10'))
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    light_pool(c, mx, my - 40, rx * 1.3, ry, '#CFE0FF', 0.10)
    crowd_a = smooth(41.0, 43.0, T)
    for i, (dx, s) in enumerate([(-200, 0.74), (-105, 0.82), (125, 0.8), (210, 0.72), (0, 0.9)]):
        SHADE.draw(c, dict(x=mx + dx, y=my + 175 + (0.9 - s) * 130, scale=s, turn=0.0,
                           eye=smooth(41.2 + i * 0.3, 41.5 + i * 0.3, T), tilt=6 * math.sin(T + i),
                           alpha=crowd_a * (0.9 if i < 4 else 0.0)), t=T)
    refl = dict(x=mx, y=my + 245, scale=0.98, facing=1, turn=0.0, eyes='tired', bags=1,
                brow=Track([(40, -10), (42.0, -18), (46.8, -20), (47.2, -26)])(T),
                smile=Track([(40, -0.3), (47.0, -0.5)])(T), sb=6, sf=-6, **standing_legs(),
                tilt=Track([(40, 0), (47.6, 0), (48.8, 14)])(T), eye=blink(T, 6))
    HERO.draw(c, refl, t=T)
    c.restore()
    cracks(c, mx + 6, my - 30, crack, seed=7, reach=320)
    if crack > 0:
        light_pool(c, mx, my - 30, 260, 260, '#FFFFFF', 0.12 * (1 - smooth(EV['crack'], EV['crack'] + 1.2, T)))
    mirror_frame(c, mx, my, rx, ry, glow=0.5 * smooth(41, 43, T))
    c.drawRRect(rrect(mx - 260, my + ry + 40, 520, 40, 10), paint('#D9DCE2'))
    c.drawRRect(rrect(mx - 260, my + ry + 40, 520, 40, 10), paint('outline', stroke=4))
    whisper(c, T, 'stay quiet.', 42.0, 44.2, mx - 380, my - 150, 72, seed=6)
    whisper(c, T, 'know your place.', 44.4, 46.8, mx + 400, my - 80, 72, seed=7)


def cam_mirror(t):
    u = smooth(0, 10, t)
    sx, sy = shake(t, 9 * (1 - smooth(7.0, 7.9, t)) * smooth(6.95, 7.0, t))
    return (960 + sx, 470 + sy - 20 * u, 1.14 + 0.16 * u)


# --- 5. rock bottom (50-60) -------------------------------------------------------------------------------

def rock_bottom(c, t, T):
    void(c)
    floor_y = 860
    warm = smooth(EV['look_up'] - 0.4, EV['look_up'] + 1.2, T)
    beam = mixc('#BFD0FF', '#FFD9A0', warm)
    cone(c, (960, -80), 70, floor_y, 360, beam, 0.13 + 0.07 * warm, soft=36)
    light_pool(c, 960, floor_y, 420, 70, beam, 0.35 + 0.2 * warm)
    dust_motes(c, 700, 0, 1220, floor_y, T, n=70, seed=41, color=mixc('#DDE6FF', '#FFE6B0', warm), a=0.5, speed=10)
    guitar(c, 790, floor_y - 18, -4, 0.86, dust=1.0, shine=0)
    up = smooth(EV['look_up'], EV['look_up'] + 1.0, T)
    sob = math.sin(T * 9) * (1 - up) * smooth(50.5, 51.5, T)
    pose = dict(x=990, y=floor_y - 22, facing=-1, turn=0.3,
                hb=150, kb=150, hf=142, kf=146,
                lean=30 - 22 * up, tilt=26 - 34 * up + sob * 1.5,
                hand_b=(64 - 10 * up, -40), hand_f=(70 - 10 * up, -34),
                eyes='closed' if up < 0.3 else 'dot', eye=1.0 if up >= 0.3 else 1.0,
                brow=-24 + 34 * up, smile=-0.5 + 0.5 * up, ly=-0.7 * up, tears=0.7 * (1 - up) * smooth(51, 52, T),
                shiver=0.25 * (1 - up))
    HERO.draw(c, pose, t=T)


def cam_bottom(t):
    u = smooth(0, 10, t)
    return (935, 700 - 30 * u, 1.38 + 0.24 * u)


# --- assemble -------------------------------------------------------------------------------------------------

def shots():
    cuts = EV['montage_cuts'] + [40.0]
    kinds = ['corner1', 'office', 'audience', 'corner2', 'phone', 'corner3']
    cams = [cam_push(1070, 690, 1.75, 1.92, 1.8), cam_push(930, 660, 1.38, 1.48, 1.8), cam_push(990, 640, 1.12, 1.2, 1.8),
            cam_push(1090, 660, 1.95, 2.15, 1.8), cam_push(1060, 720, 1.6, 1.72, 1.8), cam_push(1110, 620, 2.15, 2.5, 2.0)]
    out = [Shot(0.0, 14.0, bedroom_night, cam_bedroom_a, name='bedroom'),
           Shot(14.0, 22.0, bedroom_night, cam_bedroom_b, name='eyes'),
           Shot(22.0, 29.0, signup, cam_signup, name='signup')]
    for k, kind in enumerate(kinds):
        out.append(Shot(cuts[k], cuts[k + 1], montage_shot(kind), cams[k], name=kind))
    out += [Shot(40.0, 50.0, mirror, cam_mirror, name='mirror'),
            Shot(50.0, 60.0, rock_bottom, cam_bottom, name='bottom')]
    return out
