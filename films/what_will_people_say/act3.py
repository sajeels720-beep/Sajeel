"""Act 3 (1:50-2:40): the final stage, the lights come up, the callback, the title card."""
from __future__ import annotations

import math

import skia

from act1 import HIP_SEAT
from common import (HERO_BEANIE, KID, SHADE, STAND_HIP, bedroom, extra, play_guitar, seated_legs,
                    standing_legs)
from cues import EV, ROAR
from engine.captions import envelope, title
from engine.core import H, W, Track, beat_env, clamp, hrand, hrange, noise1, out_back, shake, smooth
from engine.draw import col, cone, light_pool, mixc, oval, paint, rrect, text
from engine.fx import eye_field, light_rays, notes, shockwave, sound_waves
from engine.props import curtains, guitar_local, mic_stand, stage_floor, toy_guitar
from engine.render import Shot
from engine.rig import blink, walk

HERO = HERO_BEANIE
STAGE_TOP = 760
HERO_X = 900

# --- 10. the final stage (110-124) ---------------------------------------------------------------------------


def _stage_eyes():
    spots = []
    i = 0
    # the audience pit below the stage edge (closer to camera = bigger)
    while len(spots) < 210 and i < 5000:
        x, y = hrange(-760, 2680, i, 91), hrange(870, 1560, i, 92)
        i += 1
        if any(abs(x - sx) < 80 and abs(y - sy) < 52 for sx, sy, *_ in spots):
            continue
        size = 46 + (y - 870) * 0.085
        spots.append((x, y, size, hrange(10, 26, i, 93)))
    # the dark above and around the stage
    j = 0
    while len(spots) < 300 and j < 5000:
        x, y = hrange(-760, 2680, j, 94), hrange(-420, 640, j, 95)
        j += 1
        if 520 < x < 1400:
            continue
        if any(abs(x - sx) < 90 and abs(y - sy) < 60 for sx, sy, *_ in spots):
            continue
        spots.append((x, y, hrange(44, 70, j, 96), hrange(10, 26, j, 97)))
    return spots


STAGE_EYES = _stage_eyes()
GUITAR_WORLD = (HERO_X + 30, STAGE_TOP - STAND_HIP - 44)


def _eye_states(T):
    out = []
    t_open0 = EV['eye_wave']
    for i, (x, y, s, slant) in enumerate(STAGE_EYES):
        t_open = t_open0 + hrand(i, 7) * 1.3 + (0.0 if y < 860 else (1560 - y) / 1560 * 0.2)
        if T < t_open:
            continue
        o = out_back(min(1.0, (T - t_open) / 0.22))
        d = math.hypot(x - GUITAR_WORLD[0], y - GUITAR_WORLD[1])
        t_close = EV['strum'] + 0.05 + d / 1500
        if T >= t_close:
            o *= 1 - smooth(t_close, t_close + 0.16, T)
        roar = smooth(ROAR[1], ROAR[1] + 0.2, T) * (1 - smooth(ROAR[2], ROAR[2] + 0.8, T))
        size = s * (1 + 0.3 * roar)
        jx = noise1(T * 10, i) * 8 * roar
        jy = noise1(T * 10, i + 500) * 6 * roar
        k = math.floor((T + i * 0.37) / 3.1)
        bt = (T + i * 0.37) - k * 3.1 - hrand(k, i) * 2.4
        if 0 <= bt < 0.2 and roar < 0.5:
            o *= abs(bt - 0.1) / 0.1
        if o > 0.02:
            out.append((x + jx, y + jy, size, o, slant + 8 * roar, 1.0))
    return out


def final_stage(c, t, T):
    c.drawPaint(paint('#050507'))
    strum = EV['strum']
    warm = smooth(strum, strum + 2.5, T)
    breath = smooth(EV['breath'], EV['breath'] + 1.2, T) * (1 - smooth(strum, strum + 0.1, T))
    # back wall glow once he plays
    if warm > 0:
        light_pool(c, HERO_X, 420, 1500, 800, 'warm', 0.22 * warm)
    stage_floor(c, -800, 2700, STAGE_TOP, 70)
    half = 250 - 100 * breath + 500 * warm
    cone(c, (HERO_X + 20, -160), 70 + 60 * warm, STAGE_TOP, half, mixc('#DDE6FF', '#FFD9A0', warm),
         0.15 + 0.1 * warm, soft=40)
    light_pool(c, HERO_X + 20, STAGE_TOP, half * 1.25, 60, mixc('#DDE6FF', '#FFD9A0', warm), 0.42 + 0.2 * warm)
    if T >= strum:
        light_rays(c, GUITAR_WORLD[0], GUITAR_WORLD[1], T, n=16, length=2600, a=0.10 * warm, spin=0.03)

    # hero walks on, freezes, breathes, plays
    walking = T < 113.2
    playing = T >= strum
    gp, mid, vib = play_guitar(T, seated=False, bpm=120, strum=playing, strum_amp=1.4, fret_shift=playing)
    hx = Track([(110.8, -200), (113.2, HERO_X, 'out_quad')])(T)
    roar = smooth(ROAR[1], ROAR[1] + 0.15, T) * (1 - smooth(117.6, 118.2, T))
    if walking:
        legs = walk(T, 0.85, 22)
        legs = {k: legs[k] for k in ('hf', 'kf', 'hb', 'kb', 'head_dy')}
    else:
        legs = standing_legs()
    look_x = Track([(113.2, 0.0), (113.8, -0.6), (114.4, 0.6), (116.6, -0.8), (117.2, 0.7), (117.8, 0.0)])(T)
    pose = dict(x=hx, y=STAGE_TOP - STAND_HIP, facing=1, **legs, **gp,
                turn=Track([(110.8, 0.4), (113.0, 0.4), (113.5, 0.06)])(T),
                lean=-6 * roar, shiver=1.0 * roar, sweat=smooth(114.2, 114.8, T) * (1 - smooth(118.0, 119.0, T)),
                eyes='wide' if roar > 0.3 and T < 118.0 else ('closed' if EV['breath'] <= T < strum else 'dot'),
                lx=look_x * (1 - breath), ly=Track([(113.2, 0.0), (113.8, 0.3)])(T) * (1 - breath),
                brow=Track([(110.8, 4), (114.0, 4), (114.3, -20), (117.9, -20), (118.4, 0), (119.9, 0), (120.0, 16)])(T),
                smile=Track([(110.8, 0.1), (114.0, 0.0), (114.3, -0.5), (117.9, -0.5), (118.6, 0.0), (120.6, 0.35)])(T),
                tilt=Track([(118.0, 0), (119.2, -8), (120.0, -8), (120.3, 2)])(T) + (3 * math.sin(T * math.pi * 2) if playing else 0),
                breathe=breath, eye=blink(T, 21) if not (roar > 0.3) else 1.0,
                mouth='teeth' if strum <= T < strum + 0.5 else 'curve',
                mopen=(0.2 + 0.5 * abs(math.sin(T * 5.1))) * smooth(strum + 0.6, strum + 0.9, T))
    HERO.draw(c, pose, {'mid': mid}, t=T)
    mic_stand(c, hx + 92, STAGE_TOP, 200)

    # the sea of eyes, closing in a wave from his guitar
    eye_field(c, _eye_states(T), T)
    if T >= strum:
        shockwave(c, GUITAR_WORLD[0], GUITAR_WORLD[1], T, strum, max_r=2900, life=1.7, width=70)
        shockwave(c, GUITAR_WORLD[0], GUITAR_WORLD[1], T, strum + 0.25, max_r=2400, life=1.5, width=40, a=0.6)
        notes(c, GUITAR_WORLD[0] + 40, GUITAR_WORLD[1] - 20, T, start=strum + 0.2, rate=4.0, life=2.8, seed=61,
              size=26, rise=420)
        sound_waves(c, GUITAR_WORLD[0], GUITAR_WORLD[1], T, start=strum + 0.4, rate=2.0, life=1.6, max_r=900,
                    arc=(-200, 220), a=0.35)

    # curtains open at the start
    c.save()
    c.translate(-460, -60)
    curtains(c, 2840, 900, open_amt=smooth(EV['curtain'], EV['curtain'] + 1.6, T), t=T)
    c.restore()


_CAM = Track([(0.0, (960, 470, 1.0)), (2.6, (900, 470, 1.04)), (3.0, (930, 560, 1.0)),
              (4.0, (960, 720, 0.66, ), 'out_cubic'), (6.6, (960, 700, 0.68)),
              (7.6, (HERO_X + 30, 520, 1.45)), (9.9, (HERO_X + 30, 500, 1.8), 'in_out_sine'),
              (11.6, (960, 600, 0.78), 'out_expo'), (14.0, (960, 580, 0.86))])


def cam_final(t):
    cx, cy, z = _CAM(t)
    T = 110.0 + t
    amt = 14 * smooth(ROAR[1], ROAR[1] + 0.1, T) * (1 - smooth(ROAR[2] - 0.4, ROAR[2] + 0.4, T))
    amt += 22 * beat_env(T, [EV['strum']], 0.35)
    sx, sy = shake(t, amt)
    return (cx + sx, cy + sy, z)


def roar_overlay(c, T):
    s, t0, t1 = ROAR
    a = envelope(T, t0, t1, 0.08, 0.5)
    if a <= 0:
        return
    pop = out_back(min(1.0, (T - t0) / 0.3))
    c.save()
    jx, jy = noise1(T * 22, 3) * 9, noise1(T * 22, 8) * 9
    c.translate(W / 2 + jx, H * 0.47 + jy)
    c.scale(pop, pop)
    for k, (dx, dy, aa) in enumerate(((-6, 4, 0.35), (6, -4, 0.35), (0, 0, 1.0))):
        text(c, s, dx, dy + 52, 150, 'PatrickHand', '#FF4A40', a * aa, glow='red', glow_a=0.8, glow_r=26)
    c.restore()


# --- 11. the lights come up (124-136) ----------------------------------------------------------------------

BEHAVIOURS = ['phone', 'chat', 'bored', 'smile', 'phone', 'clap', 'chat', 'sleep', 'phone', 'smile', 'bored',
              'clap', 'phone', 'chat', 'smile', 'phone', 'bored', 'clap', 'chat', 'phone', 'smile', 'phone', 'bored']


def _audience_member(c, idx, x, y, scale, behaviour, T, neighbour_dir=1):
    who = extra(idx)
    pose = dict(x=x, y=y, scale=scale, facing=1, turn=hrange(-0.15, 0.15, idx, 1), hb=88, kb=88, hf=86, kf=86,
                eye=blink(T, 200 + idx), tilt=noise1(T * 0.6, idx) * 4)
    layers = None
    clap = abs(math.sin(T * 7 + idx))
    if behaviour == 'phone':
        pose.update(tilt=18, ly=0.8, lx=0.0, smile=0.0, hand_b=(18, -58), hand_f=(36, -60), turn=0.0)
        layers = {'front': lambda cc, j: _held_phone(cc, j)}
    elif behaviour == 'chat':
        pose.update(turn=0.6, facing=neighbour_dir, smile=0.4,
                    mopen=0.25 * abs(math.sin(T * 6 + idx)), brow=4)
    elif behaviour == 'sleep':
        pose.update(eyes='closed', tilt=20, smile=0.0, mopen=0.15, lean=-4)
    elif behaviour == 'clap':
        pose.update(eyes='happy', smile=0.6, hand_b=(30, -62 - 6 * clap), hand_f=(52 - 16 * clap, -64))
    elif behaviour == 'smile':
        pose.update(smile=0.5, tilt=4 * math.sin(T * 2 + idx), lx=0.0, ly=-0.2)
    else:
        pose.update(lx=hrange(-0.8, 0.8, idx, 3), smile=-0.05, brow=-2)
    who.draw(c, pose, layers, t=T)
    if behaviour == 'sleep':
        for k in range(3):
            u = ((T * 0.6 + k / 3) % 1.0)
            text(c, 'z', x + 40 * scale + 30 * u * scale, y - 220 * scale - 90 * u * scale, 30 * scale * (0.7 + u),
                 'Fredoka', '#BFC6D6', 1 - u)


def _held_phone(c, j):
    hx = (j['hand_b'][0] + j['hand_f'][0]) / 2
    hy = (j['hand_b'][1] + j['hand_f'][1]) / 2
    from engine.props import phone
    phone(c, hx, hy - 24, 0, 0.75, face_down=True)
    light_pool(c, hx, hy - 60, 90, 70, '#9CC8FF', 0.25)


def lights_up(c, t, T):
    on = smooth(EV['lights_up'], EV['lights_up'] + 0.6, T)
    c.drawPaint(paint(mixc('#08080A', '#2A1E17', on)))
    light_pool(c, 960, -200, 1600, 700, '#FFD9A0', 0.25 * on)
    rows = [(520, 0.74, 9, -40), (700, 0.86, 8, 60), (900, 1.0, 7, -10)]
    idx = 0
    for r, (y, s, n, offset) in enumerate(rows):
        span = 1900 + r * 120
        for k in range(n):
            x = W / 2 - span / 2 + (k + 0.5) * span / n + offset
            if r == 2 and k == n // 2:
                _kid(c, x, y, T)
                idx += 1
                continue
            seat = rrect(x - 66 * s, y - 210 * s, 132 * s, 230 * s, 26 * s)
            c.drawRRect(seat, paint('#5A1E26'))
            c.drawRRect(seat, paint('outline', stroke=4))
            beh = BEHAVIOURS[idx % len(BEHAVIOURS)]
            _audience_member(c, 20 + idx, x, y, s, beh, T, neighbour_dir=1 if k % 2 == 0 else -1)
            idx += 1
    # stage edge in the foreground
    c.drawRect(skia.Rect.MakeLTRB(-400, 975, W + 400, H + 400), paint('#2E2018'))
    c.drawLine(-400, 975, W + 400, 975, paint('#6B4E3A', stroke=6))
    if on < 1:
        c.drawPaint(paint('#000000', 0.85 * (1 - on)))


def _kid(c, x, y, T):
    seat = rrect(x - 66, y - 210, 132, 230, 26)
    c.drawRRect(seat, paint('#5A1E26'))
    c.drawRRect(seat, paint('outline', stroke=4))
    playing = T > 133.0
    gp, mid, _ = play_guitar(T, bpm=140, strum=playing, strum_amp=1.2, gx=16, gy=-28, angle=-24, gscale=0.55,
                             fret_shift=False)

    def toy(cc, j):
        toy_guitar(cc, 16, -28, -24, 0.55)

    clap = abs(math.sin(T * 9)) * (1 - smooth(132.6, 133.0, T))
    pose = dict(x=x, y=y + 6, facing=1, turn=0.0, hb=88, kb=88, hf=86, kf=86, eyes='wide', lx=0.0, ly=-0.4,
                smile=0.7, mopen=0.25 + 0.1 * math.sin(T * 8), brow=-8, tilt=-6 + 3 * math.sin(T * 4),
                hand_b=gp['hand_b'] if playing else (26, -40 - 8 * clap),
                hand_f=gp['hand_f'] if playing else (44 - 14 * clap, -44), back_arm_late=True, blush=0.8)
    KID.draw(c, pose, {'mid': toy}, t=T)
    if T > 132.4:
        for k in range(4):
            sp = 0.5 + 0.5 * math.sin(T * 6 + k * 1.7)
            c.drawCircle(x - 70 + k * 46, y - 250 - (k % 2) * 30, 4 + 4 * sp, paint('#FFF3C4', 0.8 * sp, blur=2, blend='add'))
    if playing:
        notes(c, x + 30, y - 60, T, start=133.0, rate=3.0, life=2.0, seed=71, size=18, rise=200)


_CAM_LIGHTS = Track([(0.0, (960, 560, 1.0)), (5.4, (960, 560, 1.03)), (6.2, (1260, 600, 1.3)),
                     (8.2, (1240, 600, 1.34)), (9.0, (W / 2 - 10, 780, 1.85)), (12.0, (W / 2 - 10, 760, 2.15), 'in_out_sine')])


def cam_lights(t):
    cx, cy, z = _CAM_LIGHTS(t)
    return (cx, cy, z)


# --- 12. callback: the same bedroom, the same song, finished (136-144) ----------------------------------------

def callback(c, t, T):
    g = EV['glance']
    gives_up = smooth(g + 0.5, g + 1.3, T)

    def tiny(cc):
        bob = math.sin(T * math.pi * 90 / 60) * (1 - gives_up)
        SHADE.draw(cc, dict(x=1292, y=722 + 4 * gives_up, scale=0.22, facing=-1, turn=0.3, hb=90, kb=80, hf=88,
                            kf=84, tilt=10 * bob + 26 * gives_up, eye=0.55 * (1 - 0.85 * gives_up),
                            lean=-4 + 14 * gives_up), t=T)
    bedroom(c, T, lamp=1.0, poster='gig', tiny_shadow=tiny)
    gp, mid, _ = play_guitar(T - 136.2, bpm=90, strum_amp=0.45)
    bob = math.sin(T * math.pi * 90 / 60)
    look = smooth(g, g + 0.5, T) * (1 - smooth(g + 2.2, g + 2.8, T))
    HERO.draw(c, dict(x=HIP_SEAT[0], y=HIP_SEAT[1], facing=-1, turn=0.42 - 0.3 * look, **seated_legs(94, 40), **gp,
                      lean=8, tilt=10 + 3 * bob - 8 * look, eyes='dot' if look > 0.5 else 'happy',
                      lx=-0.9 * look, ly=-0.2 * look, smile=0.75, brow=-2 + 4 * look, eye=blink(T, 31)),
              {'mid': mid}, t=T)
    notes(c, HIP_SEAT[0] - 130, HIP_SEAT[1] - 70, T, start=136.2, rate=1.6, life=3.2, seed=81, size=21, rise=300,
          drift=-1)


def cam_callback(t):
    u = smooth(0, 12, t)
    return (900 + 90 * u, 560 - 20 * u, 1.3 + 0.16 * u)


# --- 13. title card (144-160) ---------------------------------------------------------------------------------

def title_card(c, t, T):
    c.drawPaint(paint('#060608'))
    light_pool(c, W / 2, H * 0.42, 900, 420, 'warm', 0.06 * smooth(148.5, 151, T))


def title_overlay(c, T):
    if T < EV['title_card']:
        return
    title(c, T, 'WHAT WILL PEOPLE SAY?', 148.5, 159.2, 420, 124, underline=149.5)
    from engine.captions import narrator
    narrator(c, T, 'Their opinion lasts a minute.', 151.0, 159.2, y=590, size=74)
    narrator(c, T, 'Your regret lasts a lifetime.', 152.8, 159.2, y=690, size=74)
    narrator(c, T, 'Start anyway.', 155.2, 159.2, y=850, size=92, color='beanie')


def overlays(c, T):
    roar_overlay(c, T)
    title_overlay(c, T)


# --- assemble -------------------------------------------------------------------------------------------------

def shots():
    return [
        Shot(110.0, 124.0, final_stage, cam_final, name='final_stage'),
        Shot(124.0, 136.0, lights_up, cam_lights, name='lights_up'),
        Shot(136.0, 148.0, callback, cam_callback, name='callback'),
        Shot(148.0, 160.0, title_card, None, name='title'),
    ]
