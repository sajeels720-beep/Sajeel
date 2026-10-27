"""Shared characters, sets and helpers for 'What Will People Say?'."""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'studio'))

import skia  # noqa: E402

from engine.core import H, W, clamp, hrand, hrange, noise1, out_back, smooth  # noqa: E402
from engine.draw import col, light_pool, mixc, paint  # noqa: E402
from engine.fx import eye_field  # noqa: E402
from engine.props import guitar, guitar_local  # noqa: E402
from engine.rig import SHADOW, Character, Look  # noqa: E402

# --- cast ---------------------------------------------------------------------------------

HERO = Character(Look(), seed=1)
HERO_BEANIE = Character(Look(hat='beanie'), seed=1)
HERO_OFFICE = Character(Look(top='#D9DCE2', hood=False, pocket=False, tie='#7A2E3A', sleeves='#D9DCE2'), seed=1)
HERO_OFFICE_BEANIE = Character(Look(top='#D9DCE2', hood=False, pocket=False, tie='#7A2E3A', sleeves='#D9DCE2',
                                    hat='beanie'), seed=1)
SHADE = Character(SHADOW, seed=5)

SKINS = ['#EDE6D9', '#E4CBA9', '#C99A72', '#9C6B48', '#EDE6D9', '#D9B48F']
TOPS = ['#6B4F7A', '#4E7A68', '#8C5A46', '#3F5F8A', '#7A7A84', '#A67C3D', '#5B6E8C', '#7C4A5A']
HAIRS = [None, 'short', 'long', 'bun', 'spiky', 'short', None, 'long']
HAIR_COLS = ['#2E2420', '#5A3A24', '#1E1A18', '#7A5A3A', '#3A2E28']


def extra(i, scale=1.0):
    """A background person with a varied look (deterministic by index)."""
    look = Look(skin=SKINS[i % len(SKINS)], top=TOPS[i % len(TOPS)], hood=False, pocket=False,
                hair=HAIRS[i % len(HAIRS)], hair_color=HAIR_COLS[i % len(HAIR_COLS)],
                pants=['#2B2E36', '#3B3540', '#2F3A44'][i % 3])
    return Character(look, seed=100 + i)


KID = Character(Look(skin='#E4CBA9', top='#E2A13B', hood=False, pocket=False, hair='spiky', hair_color='#2E2420',
                     head_r=58, torso=70, upper_arm=40, forearm=36, thigh=40, shin=40, shoulder_w=58, hip_w=48),
                seed=77)


# --- guitar playing --------------------------------------------------------------------------

G_SCALE = 0.95


def play_guitar(t, *, seated=True, bpm=80, strum=True, strum_amp=1.0, fret_shift=True, gx=None, gy=None,
                angle=None, dust=0.0, gscale=G_SCALE, strum_div=2):
    """Pose fragment + 'mid' layer that keep both hands on the guitar.

    Returns (pose_dict, mid_layer_fn, strum_amount)."""
    if gx is None:
        gx, gy = (26, -34) if seated else (30, -44)
    if angle is None:
        angle = -22 if seated else -26
    beat = t * bpm / 60.0
    # down-up strumming on eighth notes
    s = math.sin(math.pi * beat * strum_div / 1.0) if strum else 0.0
    sy = 13 * s * strum_amp
    strum_hand = guitar_local(gx, gy, angle, gscale, 4, sy)
    pos = 0.0
    if fret_shift:
        step = math.floor(beat / 2)
        pos = (hrand(step, 3) - 0.5) * 22
    fret_hand = guitar_local(gx, gy, angle, gscale, 104 + pos, -2)
    vib = abs(s) if strum else 0.0

    def mid(c, j):
        guitar(c, gx, gy, angle, gscale, dust=dust, strum=vib * strum_amp, t=t)

    pose = dict(hand_b=strum_hand, hand_f=fret_hand, back_arm_late=True, ik_b=1.0, ik_f=1.0)
    return pose, mid, vib


def seated_legs(foot_y=96, foot_x=48):
    """Feet planted on the floor below a seated hip."""
    return dict(foot_b=(foot_x - 14, foot_y), foot_f=(foot_x + 6, foot_y))


def standing_legs():
    return dict(hb=-4, kb=3, hf=5, kf=3)


STAND_HIP = 123  # pelvis height above the floor line for a standing character


# --- sets --------------------------------------------------------------------------------------

def room(c, floor_y, wall='#111118', floor='#0D0D11', x0=-400, x1=W + 400, glow=None):
    c.drawRect(skia.Rect.MakeLTRB(x0, -400, x1, floor_y), paint(wall))
    shader = skia.GradientShader.MakeLinear(points=[(0, floor_y - 500), (0, floor_y)],
                                           colors=[col('#000000', 0.0), col('#000000', 0.35)])
    c.drawRect(skia.Rect.MakeLTRB(x0, floor_y - 500, x1, floor_y), paint('#000000', shader=shader))
    c.drawRect(skia.Rect.MakeLTRB(x0, floor_y, x1, H + 400), paint(floor))
    c.drawRect(skia.Rect.MakeLTRB(x0, floor_y - 14, x1, floor_y), paint('#18181F'))
    c.drawLine(x0, floor_y, x1, floor_y, paint('floor_line', stroke=3))


def void(c, floor_y=None, color='#08080B'):
    c.drawPaint(paint(color))
    if floor_y is not None:
        c.drawLine(-400, floor_y, W + 400, floor_y, paint('#1C1C22', stroke=3))


BEDROOM_FLOOR = 840
BED_X = 800
BED_W = 430


def bedroom(c, T, *, dawn=0.0, lamp=1.0, poster='singer', moon=True, red=0.0, tiny_shadow=None, beanie_peg=False):
    """The hero's bedroom in cross-section. Returns the mattress top y."""
    from engine.props import bed, moonbeam, nightstand, poster as poster_fn, shelf, window
    fy = BEDROOM_FLOOR
    room(c, fy, wall=mixc('#111118', '#2A1C1A', dawn * 0.6))
    window(c, 190, 250, 240, 270, dawn=dawn, moon=moon, t=T)
    moonbeam(c, 190, 250, 240, 270, fy, slant=260, a=0.07 * (1 - dawn) + 0.1 * dawn,
             color=mixc('moon', '#FFB27A', dawn))
    shelf(c, 900, 430, 250)
    poster_fn(c, 1260, 250, 140, 190, kind=poster, t=T)
    top = bed(c, BED_X, fy, BED_W)
    nightstand(c, 1262, fy, lamp_on=lamp)
    if tiny_shadow:
        tiny_shadow(c)
    if red > 0:
        light_pool(c, W / 2, fy - 200, 1100, 500, 'red', 0.10 * red)
    return top


# --- the red eyes ------------------------------------------------------------------------------

def eyes_at(T, spots, open_times, close_times=None, pop=0.25):
    """Build eye_field tuples. spots: [(x, y, size, slant)]."""
    out = []
    for i, (x, y, s, slant) in enumerate(spots):
        t_open = open_times[i % len(open_times)] if isinstance(open_times, (list, tuple)) else open_times
        if T < t_open:
            continue
        o = out_back(min(1.0, (T - t_open) / pop))
        if close_times is not None:
            t_close = close_times[i] if isinstance(close_times, (list, tuple)) else close_times
            if T >= t_close:
                o *= 1 - smooth(t_close, t_close + 0.18, T)
        # an occasional slow blink
        k = math.floor((T + i * 0.7) / 3.3)
        bt = (T + i * 0.7) - k * 3.3 - hrand(k, i) * 2.5
        if 0 <= bt < 0.22:
            o *= abs(bt - 0.11) / 0.11
        drift_x = noise1(T * 0.4, i) * 6
        drift_y = noise1(T * 0.4, i + 50) * 4
        out.append((x + drift_x, y + drift_y, s, o, slant, 1.0))
    return out


def scatter_spots(n, x0, y0, x1, y1, seed, size=(40, 70), slant=(12, 26), avoid=None):
    spots = []
    i = 0
    while len(spots) < n and i < n * 20:
        x, y = hrange(x0, x1, i, seed), hrange(y0, y1, i, seed, 1)
        i += 1
        if avoid and any(abs(x - ax) < aw and abs(y - ay) < ah for ax, ay, aw, ah in avoid):
            continue
        if any(math.hypot(x - sx, y - sy) < 70 for sx, sy, *_ in spots):
            continue
        spots.append((x, y, hrange(size[0], size[1], i, seed, 2), hrange(slant[0], slant[1], i, seed, 3)))
    return spots
