"""Act 1 (0:00-0:44): midnight, the January rush, the New Year photo, and six days of people going to smoke."""
from __future__ import annotations

import math

import skia

from common import (CORNER_X, CROWD, DAYS, DOOR, HERO_JAN, OLD, PHOTO_CAM, ROW_B, ROW_F, SB, SF, STAND_HIP,
                    TREADS, WALL_FLOOR, corner_regular, curl_pose, draw_member, dropped, dumbbells_layers, extra,
                    gym_props_back, gym_props_front, gym_room, member_pose, photo_scene, present, shade_hand,
                    shade_tap, shoulder_world, stand)
from cues import EV, WHISPERS
from engine.captions import whisper
from engine.core import H, W, beat_env, hrand, hrange, out_back, shake, smooth
from engine.draw import col, light_pool, mixc, paint, poly, rrect, text
from engine.fx import FIREWORK_COLORS, firework, snowfall
from engine.gym import water_bottle
from engine.props import buildings
from engine.render import Shot
from engine.rig import blink, idle, walk

HERO_X = 860   # the hero's spot in the front row


# --- 1. midnight over the city (0-6.2) ----------------------------------------------------------------------

def countdown(c, t, T):
    sky = skia.GradientShader.MakeLinear(points=[(0, -200), (0, 900)], colors=[col('#04060D'), col('#1B1533')])
    c.drawRect(skia.Rect.MakeLTRB(-200, -300, W + 200, H + 200), paint('#000000', shader=sky))
    for i in range(70):
        sx, sy = hrange(-100, W + 100, i, 3), hrange(-200, 520, i, 4)
        c.drawCircle(sx, sy, 1.5, paint('#FFFFFF', 0.25 + 0.3 * math.sin(T * 2 + i) ** 2))
    glow = 0.0
    for t0, bx, by, k in EV['bursts']:
        if T >= t0:
            glow += math.exp(-(T - t0) / 0.6)
    if glow > 0:
        light_pool(c, 960, 380, 1300, 520, '#C59BFF', 0.12 * min(1.0, glow))
    # far towers, then the near skyline with lit windows
    c.save()
    c.translate(0, 40)
    buildings(c, -200, W + 200, 900, seed=21)
    c.restore()
    c.drawRect(skia.Rect.MakeLTRB(-200, 900, W + 200, H + 300), paint('#07080C'))
    # every window in the city lights up a little brighter on each count
    pulse = beat_env(T, EV['count'], 0.3) + 1.6 * beat_env(T, [EV['midnight']], 0.6)
    for k in range(14):
        bx = -160 + k * 160 + hrange(-30, 30, k, 8)
        bh = hrange(160, 330, k, 9)
        c.drawRect(skia.Rect.MakeLTRB(bx, 960 - bh, bx + 150, 1100), paint('#06070B'))
        for r in range(int(bh / 40)):
            for q in range(3):
                if hrand(k, r, q, 2) > 0.6 - 0.25 * min(1.0, pulse):
                    c.drawRect(skia.Rect.MakeXYWH(bx + 18 + q * 44, 980 - bh + r * 40, 20, 22),
                               paint('#F2C26B', min(1.0, 0.55 + 0.4 * pulse)))
    if pulse > 0.01:
        light_pool(c, 960, 960, 1500, 260, '#F2C26B', 0.08 * min(1.0, pulse))
    for t0, bx, by, k in EV['bursts']:
        for rep in range(2):
            firework(c, bx + rep * 90 * (1 if k % 2 else -1), by + rep * 60, T, t0 + rep * 1.1,
                     FIREWORK_COLORS[(k + rep * 2) % 6], n=60, radius=340 - rep * 80, seed=k + 10 * rep,
                     size=1.25)
    for t0, bx, by, k in EV['volley']:
        firework(c, bx, by, T, t0, FIREWORK_COLORS[k % 6], n=56, radius=300, seed=30 + k, size=1.15)
    snowfall(c, -100, -200, W + 100, H + 100, T, n=60, seed=2, a=0.5)
    street_crowd(c, T)
    # 3 ... 2 ... 1
    from engine.fx import shockwave
    for k, t0 in enumerate(EV['count']):
        shockwave(c, 960, 430, T, t0, max_r=760, life=0.7, color='#FFE7B0', width=26, a=0.45)
        if t0 <= T < t0 + 0.95:
            u = (T - t0) / 0.95
            sc = 1.0 + 0.6 * (1 - out_back(min(1.0, u / 0.28)))
            a = smooth(0.0, 0.08, u) * (1 - smooth(0.7, 1.0, u))
            c.save()
            c.translate(960, 470)
            c.scale(sc, sc)
            text(c, str(3 - k), 0, 165, 470, 'LuckiestGuy', '#FFFFFF', a, glow='#FFE7B0', glow_a=0.45, glow_r=40,
                 outline='#000000', outline_w=18)
            c.restore()


def street_crowd(c, T):
    """People in the street below: black shapes against the lit city, fists up on every count, everyone
    jumping at midnight, phones held up, the fireworks catching their edges."""
    mid = EV['midnight']
    after = smooth(mid - 0.05, mid + 0.2, T)
    for i in range(17):
        x = -60 + i * 124 + hrange(-30, 30, i, 1)
        h = hrange(150, 230, i, 2)
        base = H + 60
        jump = 34 * math.sin(math.pi * min(1.0, max(0.0, (T - mid - 0.04 * (i % 4)) / 0.45))) if T > mid else 0.0
        bob = 6 * math.sin(T * 7 + i) * after
        pump = beat_env(T, [t + hrand(i, 4) * 0.06 for t in EV['count']], 0.22)
        y = base - h - jump - bob
        r = hrange(42, 54, i, 3)
        body = rrect(x - r * 1.25, y + r * 0.7, r * 2.5, h + 80, r * 0.9)
        rim = FIREWORK_COLORS[(i + int(T * 2)) % 6]
        if after > 0:
            c.drawCircle(x, y, r + 3, paint(rim, 0.35 * after, stroke=8, blur=6, blend='add'))
        up = max(after, min(1.0, pump * 1.2))
        for side in ((-1, 1) if (i % 3 or after > 0) else (1,)):
            if up < 0.05:
                continue
            sx, sy = x + side * r * 0.95, y + r * 1.1
            hx = sx + side * (16 + 10 * math.sin(T * 9 + i)) * after + side * 12
            hy = sy - (90 + 70 * up)
            c.drawLine(sx, sy, hx, hy, paint('#030305', stroke=r * 0.55))
            c.drawCircle(hx, hy, r * 0.32, paint('#030305'))
            if i % 4 == 1 and side == 1 and after > 0:
                c.drawRRect(rrect(hx - 9, hy - 30, 18, 30, 3), paint('#BFE3FF', 0.9))
                c.drawCircle(hx, hy - 15, 26, paint('#BFE3FF', 0.25, blur=10, blend='add'))
        c.drawRRect(body, paint('#030305'))
        c.drawCircle(x, y, r, paint('#030305'))


def cam_countdown(t):
    u = smooth(0, 6.2, t)
    kick = 10 * beat_env(t, [EV['count'][2]], 0.15) + 16 * beat_env(t, [EV['midnight']], 0.3)
    sx, sy = shake(t, kick)
    return (960 + sx, 560 - 40 * u + sy, 1.0 + 0.04 * u + 0.012 * beat_env(t, EV['count'], 0.2))


# --- 2. the doors burst open (6.2-9) ---------------------------------------------------------------------------

ENTRY = [(HERO_JAN, 6.4)] + [(extra(i), 6.75 + 0.3 * i) for i in (2, 5, 0, 7, 3, 9, 1, 11)]


def doors(c, t, T):
    opened = smooth(EV['doors'], EV['doors'] + 0.18, T)
    gym_room(c, T, door=opened, door_out='#2C3E60', outside='snow_dawn', hour=6.0)
    gym_props_back(c, T)
    dx, dw, dh = DOOR
    for k, (who, t0) in enumerate(ENTRY):
        if T < t0:
            continue
        walked = (T - t0) * 300
        x = dx + dw * 0.5 + walked
        hero = k == 0
        awe = hero and T > 7.2
        pose = dict(x=x, y=ROW_B - STAND_HIP * SB, scale=SB, facing=1, turn=0.5 if hero else 0.4,
                    **walk(T + k * 0.3, 1.25, 24), eyes='wide' if hero and T < 7.2 else 'happy', pupil=0.8,
                    smile=0.75, brow=10, lx=-0.3 if awe else 0.4, ly=-0.6 if awe else -0.1, eye=1.0)
        if hero and T > 7.6:
            pose.update(sb=-140, eb=-20, sf=150, ef=20)   # arms up: let's go
        cap = {'behind': lambda cc, j: water_bottle(cc, j['hand_b'][0], j['hand_b'][1] + 26, '#3F8FD0', 0.7)}
        a = smooth(t0, t0 + 0.12, T)
        pose['alpha'] = a
        who.draw(c, pose, cap if k % 2 else None, t=T)
    gym_props_front(c, T, rack=False, bench_on=False)


def cam_doors(t):
    u = smooth(0.0, 2.8, t)
    return (430 + 170 * u, 560, 1.75 - 0.05 * u)


# --- 3. the packed gym on January 1st (9-14) and the hero up close (14-16.4) -----------------------------------------

def hero_pose(T, k=None, look=None, victim_x=None, t_tap=None, x=HERO_X):
    """The hero curling in his spot. k: the day of the vanishing (None in the January rush)."""
    face = dict(turn=0.42, eye=blink(T, 1), smile=0.45, brow=8, eyes='dot')
    if k is not None:
        face['smile'] = [0.35, 0.2, 0.05, -0.05, -0.15, -0.2][k]
        face['brow'] = [6, 0, -6, -10, -12, -14][k]
        face['bags'] = [0, 0, 0.2, 0.4, 0.6, 0.8][k]
        if victim_x is not None and t_tap is not None:
            look = smooth(t_tap + 0.4, t_tap + 0.8, T) * (1 - smooth(t_tap + 2.4, t_tap + 2.9, T))
            face['lx'] = (1 if victim_x > x else -1) * 0.9 * look
            face['ly'] = -0.2 * look
            face['brow'] += -6 * look
            face['eyes'] = 'wide' if look > 0.5 and k < 3 else face['eyes']
            face['pupil'] = 0.7
    speed = 1.0 if k is None else [1.0, 1.0, 0.9, 0.85, 0.8, 0.75][k]
    return stand(x, ROW_F, SF, 1, **curl_pose(T, 1, speed), **face)


def crowd(c, T, row, victims=(), day=None):
    """Draw one row of the crowd (sorted left to right), with the shadow tapping today's victims."""
    members = [m for m in CROWD if m.row == row and present(m, T)]
    members.sort(key=lambda m: m.x)
    tapped = [m for m in members if m in victims]
    shade = None
    if tapped:
        pose0, _ = member_pose(tapped[0], T, tapped[0].tap)
        tgt = shoulder_world(tapped[0].who, pose0, 'b' if tapped[0].act != 'bench' else 'f')
        both = None
        if len(tapped) > 1:
            pose1, _ = member_pose(tapped[1], T, tapped[1].tap)
            both = shoulder_world(tapped[1].who, pose1, 'b' if tapped[1].act != 'bench' else 'f')
        side = -tapped[0].facing if tapped[0].act != 'bench' else 1
        grow = 1.0 + 0.05 * (day or 0)
        shade = shade_tap(c, T, tapped[0].tap, tgt, tapped[0].feet, tapped[0].scale, side=side, both=both,
                          grow=grow)
    for m in members:
        face = None
        if tapped and m not in tapped:
            v = tapped[0]
            d = abs(m.x - v.x)
            if d < 700:
                start = v.tap + 0.45 + d / 1400
                look = smooth(start, start + 0.25, T) * (1 - smooth(v.tap + 2.6, v.tap + 3.0, T))
                if look > 0:
                    face = dict(lx=(1 if v.x > m.x else -1) * (0.9 if m.facing > 0 else -0.9) * look,
                                ly=-0.1 * look, brow=-10 * look, smile=0.25 - 0.4 * look)
                    if look > 0.5:
                        face['eyes'] = 'wide'
                        face['pupil'] = 0.7
        draw_member(c, m, T, extra_face=face)
    if shade is not None:
        shade_hand(c, shade, T, 'f')
        if len(tapped) > 1:
            shade_hand(c, shade, T, 'b')


def gym_jan(c, t, T):
    gym_room(c, T, outside='snow_dawn', hour=7.0)
    gym_props_back(c, T, treads=(1.6, 1.6, 1.6), screens=(1, 1, 1))
    crowd(c, T, 'b')
    corner_regular(c, T)
    gym_props_front(c, T)
    crowd(c, T, 'f')
    HERO_JAN.draw(c, hero_pose(T), dumbbells_layers(), t=T)


def cam_gym_jan(t):
    u = smooth(0, 5.0, t)
    return (960, 560 + 10 * u, 1.0 + 0.07 * u)


def hero_close(c, t, T):
    gym_jan(c, t, T)


def cam_hero_close(t):
    u = smooth(0, 2.4, t)
    return (HERO_X + 30, 660, 2.15 + 0.1 * u)


# --- 4. the New Year photo (16.4-20) ----------------------------------------------------------------------------

def photo_shot(c, t, T):
    flash = EV['photo_flash']
    Tf = min(T, flash)
    pop = smooth(EV['photo_call'], EV['photo_call'] + 0.5, T)
    shrink = smooth(flash + 0.35, flash + 1.3, T)
    k = 1.0 - 0.4 * shrink
    rot = -4 * shrink
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
        text(c, '2026', 0, H / 2 + m * 2.4, 120 * shrink, 'GochiHand', '#2C2A26', shrink)
    c.clipRect(skia.Rect.MakeLTRB(-W / 2, -H / 2, W / 2, H / 2))
    cx, cy, z = PHOTO_CAM
    c.scale(z, z)
    c.translate(-cx, -cy)
    photo_scene(c, Tf, 2026, slot=(HERO_JAN, 5), pop=pop)
    c.restore()


# --- 5. the vanishing: one day every two bars (20-44) -------------------------------------------------------------

def day_of(T):
    return max(i for i, d in enumerate(DAYS) if T >= d - 1e-6)


def victims(k):
    t_tap = DAYS[k] + EV['tap']
    return [m for m in CROWD if m.tap is not None and abs(m.tap - t_tap) < 1e-6]


BANNER_TEAR = 42.5


def banner_loose(T, k):
    """The NEW YEAR banner sags a little more each week; on the last day its right hook gives and it swings."""
    if k < 4:
        return 0.0
    if k == 4 or T < BANNER_TEAR:
        return 0.12 if k == 4 else 0.22
    u = T - BANNER_TEAR
    fall = 0.22 + 0.78 * smooth(0.0, 0.3, u)
    return fall + 0.22 * math.exp(-u * 2.2) * math.sin(u * 8.0) * smooth(0.2, 0.35, u)


def vanish(c, t, T):
    k = day_of(T)
    vs = victims(k)
    lights = [(1, 1, 1, 1)] * 4 + [(0.0, 1, 1, 1), (0.0, 1, 1, 0.0)]
    gym_room(c, T, lights=lights[k], outside='snow_night', hour=18.5 + 0.25 * k,
             banner_loose=banner_loose(T, k), flicker=(0, 0, 0.6 if k == 5 else 0, 0))
    belts = []
    for i, key in enumerate(('runner1', 'runner2', 'runner3')):
        m = next(mm for mm in CROWD if mm.key == key)
        running = present(m, T) or (m.tap is not None and DAYS[0] <= T < DAYS[1] and key == 'runner1')
        belts.append(1.6 if running else 0.0)
    gym_props_back(c, T, treads=belts, screens=[1.0 if b else 0.0 for b in belts],
                   rack_missing=((0, 2),) if k >= 2 else ())
    crowd(c, T, 'b', vs, k)
    corner_regular(c, T)
    dropped(c, T)
    gym_props_front(c, T)
    crowd(c, T, 'f', vs, k)
    vx = vs[0].x if vs else None
    HERO_JAN.draw(c, hero_pose(T, k, victim_x=vx, t_tap=vs[0].tap if vs else None), dumbbells_layers(), t=T)
    # today's whisper over the victim
    text_, w0, w1, _ = WHISPERS[k]
    if vs:
        m = vs[0] if len(vs) == 1 else vs[1]
        wx = sum(v.x for v in vs) / len(vs)
        wy = m.feet - (410 if m.act not in ('bench', 'pushup') else 300) * m.scale
        whisper(c, T, text_, w0, w1, wx, wy, 60, seed=k + 1)


def cam_vanish(t):
    T = DAYS[0] + t
    k = day_of(T)
    u = smooth(DAYS[k] + 0.2, DAYS[k] + 2.4, T)
    vs = victims(k)
    vx = sum(v.x for v in vs) / len(vs)
    vy = vs[0].feet - 190 * vs[0].scale
    tx = vx * 0.72 + HERO_X * 0.28
    return (960 + (tx - 960) * u, 540 + (vy - 540) * u, 1.0 + 0.42 * u)


def overlays(c, T):
    pass


# --- assemble ------------------------------------------------------------------------------------------------------

def shots():
    return [
        Shot(0.0, EV['doors'], countdown, cam_countdown, name='countdown'),
        Shot(EV['doors'], EV['gym_wide'], doors, cam_doors, name='doors'),
        Shot(EV['gym_wide'], EV['hero_close'], gym_jan, cam_gym_jan, name='gym_jan'),
        Shot(EV['hero_close'], EV['photo_call'], hero_close, cam_hero_close, name='hero_close'),
        Shot(EV['photo_call'], DAYS[0], photo_shot, None, name='photo'),
        Shot(DAYS[0], 44.0, vanish, cam_vanish, name='vanish'),
    ]
