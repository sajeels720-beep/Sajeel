"""Act 3 (2:02-2:40): result day, 5 AM again, the title."""
from __future__ import annotations

import math

import skia

from act1 import to_local
from common import (FATHER, HALL_FLOOR, HERO, SON_DOOR, STAND_HIP, STOOL_X, FRONT_DOOR, hallway, merge, seated,
                    standing)
from cues import EV
from engine.captions import narrator, title
from engine.core import H, W, Track, smooth
from engine.draw import circle, col, cone, light_pool, mixc, paint, poly, rrect
from engine.fx import dust_motes
from engine.home import front_door, mug, shoe, sticky, stool
from engine.props import window
from engine.render import Shot
from engine.rig import blink, idle, walk

KITCHEN_FLOOR = 880
ISLAND = (560, 1380)          # x range of the kitchen island
ISLAND_TOP = KITCHEN_FLOOR - 150
SON_X, DAD_X = 760, 1190
LAPTOP_X = 960


def kitchen(c, T, sun=1.0):
    fy = KITCHEN_FLOOR
    wall = mixc('#2A2730', '#4A372C', sun)
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, W + 400, fy), paint(wall))
    c.drawRect(skia.Rect.MakeLTRB(-400, fy, W + 400, H + 400), paint(mixc('#15141A', '#2A211C', sun)))
    c.drawLine(-400, fy, W + 400, fy, paint('#5A4638', stroke=3))
    # cupboards and a shelf of mugs
    for k in range(4):
        x = 1420 + k * 130
        c.drawRRect(rrect(x, 180, 120, 200, 6), paint(mixc('#3A3A44', '#7A5A44', sun)))
        c.drawRRect(rrect(x, 180, 120, 200, 6), paint('outline', stroke=4))
        c.drawCircle(x + (100 if k % 2 == 0 else 20), 360, 6, paint('#C9B48A'))
    # the window: sunrise, and a long beam across the room
    wx, wy = 150, 210
    window(c, wx, wy, 300, 320, sky=mixc('#24304A', '#F6B26B', sun), moon=False, dawn=0.6 * sun, t=T)
    c.drawPath(poly([(wx, wy + 320), (wx + 300, wy + 320), (wx + 900, fy), (wx + 380, fy)], True),
               paint('#FFD08A', 0.16 * sun, blur=40, blend='add'))
    dust_motes(c, 300, 300, 1300, 860, T, n=50, seed=61, color='#FFE6B0', a=0.45 * sun, speed=8)
    # a hanging lamp
    c.drawLine(1000, -60, 1000, 120, paint('#2B2B30', stroke=3))
    c.drawPath(poly([(960, 120), (1040, 120), (1070, 168), (930, 168)], True), paint('#2F5A57'))
    c.drawPath(poly([(960, 120), (1040, 120), (1070, 168), (930, 168)], True), paint('outline', stroke=3.5))


def island(c):
    x0, x1 = ISLAND
    top = ISLAND_TOP
    c.drawRect(skia.Rect.MakeLTRB(x0 + 20, top + 18, x1 - 20, KITCHEN_FLOOR), paint('#6B4A33'))
    for k in range(4):
        px = x0 + 40 + k * (x1 - x0 - 80) / 4
        c.drawRect(skia.Rect.MakeLTRB(px + 10, top + 50, px + (x1 - x0 - 80) / 4 - 10, KITCHEN_FLOOR - 30),
                   paint('#000000', 0.15, stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(x0 + 20, top + 18, x1 - 20, KITCHEN_FLOOR), paint('outline', stroke=4))
    c.drawRect(skia.Rect.MakeLTRB(x0, top, x1, top + 20), paint('#C9B79C'))
    c.drawRect(skia.Rect.MakeLTRB(x0, top, x1, top + 20), paint('outline', stroke=4))
    light_pool(c, (x0 + x1) / 2, top, (x1 - x0) * 0.6, 60, '#FFD08A', 0.18)


def laptop_side(c, x, y, face=-1.0, glow=1.0):
    """A laptop in profile on a surface at y. face: -1 screen toward the left, +1 toward the right; values
    in between squash it as it is turned round."""
    c.save()
    c.translate(x, y)
    c.scale(face, 1.0)
    if glow > 0 and abs(face) > 0.3:
        light_pool(c, -60, -70, 200, 140, '#CFE4FF', 0.14 * glow)
    c.drawRRect(rrect(-80, -10, 160, 10, 3), paint('#9BA3AE'))
    c.drawRRect(rrect(-80, -10, 160, 10, 3), paint('outline', stroke=3))
    c.save()
    c.translate(76, -8)
    c.rotate(-104)
    c.drawRRect(rrect(0, -4, 140, 9, 3), paint('#9BA3AE'))
    if glow > 0:
        c.drawRect(skia.Rect.MakeLTRB(6, -6, 134, -4), paint('#DDEBFF', glow))
    c.drawRRect(rrect(0, -4, 140, 9, 3), paint('outline', stroke=3))
    c.restore()
    c.restore()


# --- 10. result day (122-136) ---------------------------------------------------------------------------------

def result(c, t, T):
    kitchen(c, T, sun=1.0)
    fy = KITCHEN_FLOOR
    turn_screen = smooth(EV['turn_screen'], EV['turn_screen'] + 0.6, T)
    face = -1.0 + 2.0 * turn_screen
    opened = smooth(EV['open_result'], EV['open_result'] + 0.4, T)
    reads = smooth(EV['father_reads'], EV['father_reads'] + 0.5, T)
    tears = smooth(EV['tears'], EV['tears'] + 1.0, T)
    hand_on = smooth(EV['shoulder'] - 0.5, EV['shoulder'], T)
    # the son, seated behind the island, facing the laptop
    son_hip = (SON_X, fy - 108)
    look_up = smooth(EV['shoulder'], EV['shoulder'] + 0.6, T)
    tap = (math.sin(math.pi * smooth(EV['open_result'] - 0.3, EV['open_result'], T)) if T < EV['open_result'] + 0.1
           else 0.0)
    son_hand_f = to_local(son_hip, 1, (LAPTOP_X - 50 + 30 * tap, ISLAND_TOP - 16 - 14 * tap)) if T < EV['turn_screen'] \
        else to_local(son_hip, 1, (LAPTOP_X - 40 + 50 * turn_screen, ISLAND_TOP - 30))
    son = dict(x=son_hip[0], y=son_hip[1], facing=1, turn=0.35 - 0.2 * look_up, lean=8 - 6 * look_up,
               tilt=8 - 18 * look_up, hand_b=(70, -40), hand_f=son_hand_f, hb=88, kb=88, hf=84, kf=84,
               eyes='wide' if 0.3 < opened and T < 126.5 else ('happy' if look_up > 0.5 else 'dot'), pupil=0.7,
               lx=0.5 + 0.3 * look_up, ly=0.2 - 0.6 * look_up, brow=Track([(122, -16), (124.3, -20), (124.7, 4),
                                                                         (127, 0)])(T),
               smile=Track([(122, -0.2), (124.3, -0.25), (124.9, 0.45), (129, 0.55), (130, 0.7)])(T),
               mopen=0.3 * opened * (1 - smooth(125.0, 125.6, T)), eye=blink(T, 30))
    from engine.rig import solve
    j_son = solve(HERO.look, dict(__import__('engine.rig', fromlist=['BASE_POSE']).BASE_POSE, **son))
    shoulder = (son_hip[0] + j_son['sh_f'][0], son_hip[1] + j_son['sh_f'][1])
    # the father: reads from across the island, then comes round behind his son
    walk_round = smooth(EV['shoulder'] - 0.9, EV['shoulder'] - 0.1, T)
    dad_hip = (DAD_X - 300 * walk_round, fy - STAND_HIP)
    dad = merge(standing(), walk(T, 0.9, 16) if 0.02 < walk_round < 0.98 else idle(T, 31, 0.6),
                x=dad_hip[0] - 40 * reads * (1 - walk_round), y=dad_hip[1], facing=-1, turn=0.3,
                lean=4 + 14 * reads * (1 - walk_round),
                tilt=4 + 10 * reads, eyes='happy' if tears > 0.5 else 'tired', bags=0.9,
                lx=0.6 if reads > 0.5 else 0.3, ly=0.5 * reads, brow=-10 + 14 * tears,
                smile=-0.1 + 0.75 * tears, tears=0.8 * tears, eye=blink(T, 32),
                hand_b=(40, -40))
    if hand_on > 0:
        dad['hand_f'] = to_local((dad['x'], dad_hip[1]), -1, (shoulder[0] + 16, shoulder[1] - 4))
    else:
        dad['hand_f'] = (50, -70)

    def mug_in_hand(cc, j):
        hx, hy = j['hand_b']
        mug(cc, hx + 6, hy + 18, '#D9D3C4', steam=1.0, t=T)
    FATHER.draw(c, dad, {'front': mug_in_hand}, t=T)
    HERO.draw(c, son, t=T)
    if hand_on > 0:
        # his hand resting on his son's shoulder, in front
        circle(c, shoulder[0] + 16, shoulder[1] - 4, 15, 'skin', 'outline', 4.5)
    island(c)
    laptop_side(c, LAPTOP_X, ISLAND_TOP, face=face, glow=opened)
    if opened > 0 and face < 0:
        light_pool(c, SON_X + 60, ISLAND_TOP - 140, 180, 150, '#CFE4FF', 0.12 * opened)
    if face > 0:
        light_pool(c, dad['x'] - 60, ISLAND_TOP - 160, 180, 150, '#CFE4FF', 0.12 * face * (1 - walk_round))


def cam_result(t):
    T = 122.0 + t
    if T < 126.0:
        return (980, 560, 1.35 + 0.05 * smooth(122.0, 126.0, T))
    if T < 130.0:
        u = smooth(126.0, 128.0, T)
        return (980 + 150 * u, 560 - 70 * u, 1.4 + 0.6 * u)
    u = smooth(130.0, 133.0, T)
    return (1130 - 150 * u, 490 + 60 * u, 2.0 - 0.6 * u)


# --- 11. 5 AM again (136-148) ---------------------------------------------------------------------------------

def morning(c, t, T):
    sun = 0.4 + 0.6 * smooth(136.0, 146.0, T)
    door = smooth(EV['door_sun'], EV['door_sun'] + 0.6, T)
    son_door = smooth(141.6, 142.2, T)
    hallway(c, T, dawn=1.0, bulb=1.0 - smooth(EV['door_sun'] - 0.3, EV['door_sun'], T), son_door=0.75 * son_door,
            son_light=1.0, front_open=door, sun=sun, son_leaf=False)
    fy = HALL_FLOOR
    stool(c, STOOL_X, fy, 100)
    if door > 0:
        light_pool(c, FRONT_DOOR[0] + FRONT_DOOR[1] / 2, fy - 200, 700, 500, '#FFB25A', 0.16 * door)
        cone(c, (FRONT_DOOR[0] + FRONT_DOOR[1] / 2, fy - 380), 90, fy + 40, 520, '#FFC37A', 0.12 * door, soft=40)
    # the son in his doorway, lamplight behind him
    if son_door > 0.05:
        HERO.draw(c, merge(standing(), idle(T, 40, 0.6), x=SON_DOOR[0] + SON_DOOR[1] * 0.45, y=fy - STAND_HIP,
                           facing=1, turn=0.3, eyes='happy' if T > 143.0 else 'dot', lx=0.7, smile=0.5,
                           brow=0, eye=blink(T, 41)), t=T)
    front_door(c, SON_DOOR[0], fy, SON_DOOR[1], 370, open_amt=0.75 * son_door, hinge='right', part='leaf')
    # the father: comes to the stool, finds his shoes, turns, nods, steps out into the sun
    if T < EV['shoes_seen']:
        x = Track([(136.0, 700), (138.6, STOOL_X - 30, 'in_out_sine')])(T)
        pose = merge(standing(), walk(T, 0.85, 18) if T < 138.6 else idle(T, 42, 0.6),
                     x=x, y=fy - STAND_HIP, facing=1, turn=0.3, eyes='tired', bags=0.9, brow=-6, smile=0.0,
                     lean=6 + 30 * smooth(138.8, 139.4, T), tilt=10 * smooth(138.8, 139.4, T), eye=blink(T, 43))
        FATHER.draw(c, pose, t=T)
        shoe(c, STOOL_X + 110, fy, 0.55, 1, stitched=1.0, polish=1.0, color='#4A3626')
        sticky(c, STOOL_X + 110, fy - 46, 'thank you,\ndad.', -8, size=48)
    else:
        turned = smooth(EV['father_turns'], EV['father_turns'] + 0.5, T)
        nod = math.sin(max(0.0, T - 143.2) * 6) * smooth(143.2, 143.4, T) * (1 - smooth(143.9, 144.2, T))
        walk_t = smooth(EV['door_sun'] + 0.4, 147.0, T)
        x = STOOL_X - 30 + 330 * walk_t
        out = smooth(146.2, 147.0, T)
        pose = merge(standing(), walk(T, 0.85, 18) if 0.02 < walk_t < 0.98 else idle(T, 44, 0.6),
                     x=x, y=fy - STAND_HIP, facing=-1 if turned > 0.5 and T < EV['door_sun'] else 1, turn=0.3,
                     eyes='happy' if T > 142.8 else 'dot', bags=0.8, brow=4, smile=0.6, tears=0.5,
                     tilt=8 * nod, lean=4, eye=blink(T, 45), alpha=1.0 - out)
        pose['hand_b'] = (60, -70) if T < EV['door_sun'] else (36, -40)

        def note(cc, j):
            if T < EV['door_sun']:
                hx, hy = j['hand_b']
                sticky(cc, hx + 4, hy - 26, 'thank you,\ndad.', 6, size=50)
        FATHER.draw(c, pose, {'front': note}, t=T)


def cam_morning(t):
    T = 136.0 + t
    if T < EV['shoes_seen']:
        return (1000, 580, 1.2)
    if T < EV['door_sun']:
        u = smooth(EV['father_turns'], EV['father_turns'] + 1.0, T)
        return (1100 - 380 * u, 600, 1.45 - 0.2 * u)
    u = smooth(EV['door_sun'], 148.0, T)
    return (720 + 500 * u, 600 - 30 * u, 1.25 + 0.1 * u)


def shoes_note(c, t, T):
    """Close-up: the shoes, mended and polished, a note on top."""
    c.drawPaint(paint('#2A2420'))
    c.drawRect(skia.Rect.MakeLTRB(0, 820, W, H), paint('#1E1A17'))
    c.drawLine(0, 820, W, 820, paint('#5A4638', stroke=4))
    light_pool(c, 960, 700, 1000, 380, '#FFC37A', 0.3)
    u = smooth(0.0, 2.4, t)
    c.save()
    c.translate(960, 640)
    c.scale(1.0 + 0.08 * u, 1.0 + 0.08 * u)
    c.translate(-960, -640)
    shoe(c, 760, 820, 2.6, 1, stitched=1.0, polish=1.0, color='#4A3626')
    shoe(c, 1200, 820, 2.6, 1, stitched=1.0, polish=1.0, color='#4A3626')
    sticky(c, 800, 640, 'thank you,\ndad.', -7, size=230)
    c.restore()


# --- 12. title (148-160) ----------------------------------------------------------------------------------------

def title_card(c, t, T):
    c.drawPaint(paint('#060608'))
    light_pool(c, W / 2, H * 0.42, 900, 420, 'warm', 0.06 * smooth(148.5, 151, T))


def title_overlay(c, T):
    if T < EV['title_card']:
        return
    title(c, T, '90 DAYS LEFT.', 148.5, 159.2, 420, 124, underline=149.5)
    narrator(c, T, 'How many days do you have left?', 151.2, 159.2, y=600, size=74)
    narrator(c, T, 'Start today.', 154.6, 159.2, y=790, size=92, color='#F6D654')


def overlays(c, T):
    title_overlay(c, T)


def shots():
    return [
        Shot(122.0, 136.0, result, cam_result, name='result'),
        Shot(136.0, EV['shoes_seen'], morning, cam_morning, name='morning'),
        Shot(EV['shoes_seen'], 141.8, shoes_note, None, name='shoes_note'),
        Shot(141.8, 148.0, morning, lambda t: cam_morning(t + 141.8 - 136.0), name='morning2'),
        Shot(148.0, 160.0, title_card, None, name='title'),
    ]
