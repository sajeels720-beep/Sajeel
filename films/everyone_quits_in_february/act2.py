"""Act 2 (0:44-1:46): February 12th, the tap, the photos by the door, the old man's nod, and a whole year."""
from __future__ import annotations

import math

import skia

from common import (BENCH_X, CORNER_X, DOOR, HERO_JAN, OLD, PHOTO_GAP, PHOTOS_X, PHOTOS_Y, RACK_X, ROW_B, ROW_F,
                    SB, SF, SHADE, STAND_HIP, WINDOWS, bench_press_pose, corner_regular, curl_pose, dropped,
                    dumbbells_layers, gym_props_back, gym_props_front, gym_room, hero_fit, stand)
from cues import EV
from engine.captions import whisper
from engine.core import H, W, Track, hrand, hrange, noise1, out_back, shake, smooth
from engine.draw import circle, col, light_pool, mixc, oval, paint, poly, rrect, text
from engine.fx import crumble, falling_leaves, light_rays, rainfall, snowfall, wisps
from engine.gym import barbell, gym_bag, jump_rope, power_rack, towel
from engine.props import street_lamp
from engine.render import Shot
from engine.rig import blink, idle, run, solve, to_local, walk

FEB_LIGHTS = (0.0, 0.0, 1.0, 0.0)     # only the light over the bench is left on
FEB_FLICKER = (0, 0, 0.35, 0)
SEAT = (BENCH_X - 34, ROW_F - 100 * SF - 6)   # his hip when he sits up on the bench
BAG_X = BENCH_X - 210
STOP_X = 560                          # where the photos stop him


def feb_room(c, T, door=0.0, corner=0.85):
    gym_room(c, T, lights=FEB_LIGHTS, flicker=FEB_FLICKER, banner_loose=1.0, outside='snow_night', hour=21.6,
             corner=corner, door=door)
    gym_props_back(c, T, rack_missing=((0, 2), (1, 4)))
    dropped(c, 60.0)


def world_of(who, pose, joint):
    """World position of a joint of a character drawn at pose (no rotation)."""
    from engine.rig import BASE_POSE
    j = solve(who.look, dict(BASE_POSE, **pose))
    x, y = j[joint]
    s = pose.get('scale', 1.0)
    return pose['x'] + x * s * pose.get('facing', 1), pose['y'] + y * s


def shade_beside(c, T, x, feet_y, s, facing, hand_world=None, alpha=1.0, lean=10.0, eye=1.0, tilt=10.0):
    """The shadow standing at x with its hand resting on someone's shoulder."""
    pose = dict(x=x, y=feet_y - STAND_HIP * s, scale=s, facing=facing, turn=0.15, hb=-4, kb=3, hf=5, kf=3,
                lean=lean, tilt=tilt, alpha=alpha, eye=eye, brow=20, sb=6, eb=10, sf=-4, ef=12)
    if hand_world is not None:
        pose['hand_f'] = to_local(pose, hand_world)
    SHADE.draw(c, pose, t=T)
    return pose


def shade_hand_on(c, hand_world, s, alpha=1.0):
    if alpha <= 0.02:
        return
    c.drawCircle(*hand_world, 14 * s, paint('red', 0.7 * alpha, blur=6, blend='add'))
    c.drawCircle(*hand_world, 12 * s, paint('#040405', alpha))


# --- 1. February 12th: alone on the bench (44-48.6) -------------------------------------------------------------

def hero_bench(c, T, who, press=None, face=None, spot=None):
    face = face or dict(turn=0.3, eye=blink(T, 2), eyes='tired', bags=0.8, brow=-12, smile=-0.2)
    pose, layers = bench_press_pose(BENCH_X, ROW_F, SF, T * 0.55, 3, 1, face, press=press)
    pose.pop('_bar', None)
    who.draw(c, pose, layers, t=T)
    return pose


def feb_wide(c, t, T):
    feb_room(c, T)
    corner_regular(c, T, face=dict(eye=blink(T, 11)))
    gym_props_front(c, T)
    hero_bench(c, T, HERO_JAN)


def cam_feb_wide(t):
    u = smooth(0, 4.6, t)
    return (1170 + 30 * u, 630 + 10 * u, 1.2 + 0.12 * u)


# --- 2. he sits up; the shadow taps his shoulder (48.6-52) and his hand starts to go (52-54.4) ---------------------

def seated_pose(T, look_up=0.0, hand_up=0.0, freeze=None):
    hip = SEAT
    br = idle(T, 4, 1.6)['breathe'] if freeze is None or T < freeze else 0.0
    pose = dict(x=hip[0], y=hip[1], scale=SF, facing=1, turn=0.35, lean=24 - 18 * look_up, tilt=-14 + 12 * look_up,
                breathe=br, eyes='tired', bags=0.8, brow=-10, smile=-0.25, ly=0.7 - 0.9 * look_up, lx=0.3,
                eye=blink(T, 6))
    pose['foot_b'] = to_local(pose, (hip[0] + 64 * SF, ROW_F - 4))
    pose['foot_f'] = to_local(pose, (hip[0] + 84 * SF, ROW_F - 4))
    pose['hand_b'] = to_local(pose, (hip[0] + 70 * SF, hip[1] + 30 * SF))
    rest_f = (hip[0] + 84 * SF, hip[1] + 26 * SF)
    raised = (hip[0] + 118 * SF, hip[1] - 150 * SF)
    pose['hand_f'] = to_local(pose, (rest_f[0] + (raised[0] - rest_f[0]) * hand_up,
                                     rest_f[1] + (raised[1] - rest_f[1]) * hand_up))
    return pose


def smoking_arm(who, T, amount, fist=0.0):
    """A 'front' layer (use with pose['no_arm_f']): his front arm going to smoke. Grey creeps down from the
    fingers, the skin goes porous and crumbles, and smoke curls off it. fist squeezes the hand."""
    from engine.fx import _crumble_mask

    def layer(cc, j):
        el, hx, hy = j['el_f'], *j['hand_f']
        xs, ys = (el[0], hx), (el[1], hy)
        box = (min(xs) - 18, min(ys) - 18, max(xs) + 18, max(ys) + 18)
        x0, y0, x1, y1 = box
        k = min(1.0, amount * 2.2)
        cc.saveLayer(skia.Rect.MakeLTRB(x0 - 40, y0 - 40, x1 + 40, y1 + 40), None)
        who.arm(cc, j, 'f')
        if fist > 0:
            jx = noise1(T * 30, 4) * 1.5 * fist
            cc.drawCircle(hx + jx, hy, 10.5 * (1 + 0.15 * fist), paint('skin'))
            cc.drawCircle(hx + jx, hy, 10.5 * (1 + 0.15 * fist), paint('outline', stroke=4.5))
            for i in range(3):
                cc.drawLine(hx - 6 + 6 * i + jx, hy - 5, hx - 6 + 6 * i + jx, hy + 2,
                            paint('outline', 0.7 * fist, stroke=2))
        if k > 0:
            # ash grey, strongest at the fingertips, creeping down the arm as it spreads
            reach = y0 + (y1 - y0) * (0.25 + 0.9 * k)
            sh = skia.GradientShader.MakeLinear(points=[(x0, y0), (x0, reach)],
                                                colors=[col('#6E737C', 0.95 * k), col('#6E737C', 0.0)])
            gp = paint('#6E737C', shader=sh)
            gp.setBlendMode(skia.BlendMode.kSrcATop)
            cc.drawRect(skia.Rect.MakeLTRB(x0 - 40, y0 - 40, x1 + 40, y1 + 40), gp)
            cc.drawRect(skia.Rect.MakeLTRB(x0 - 40, y0 - 40, x1 + 40, y1 + 40),
                        _crumble_mask(box, 1.75 - 2.1 * amount, 7, freq=0.24, k=4.0, from_top=True))
        cc.restore()
        if amount > 0.01:
            pts = [(hx - 8, hy - 8), (hx + 1, hy - 12), (hx + 9, hy - 7),
                   ((hx + el[0]) / 2 - 6, (hy + el[1]) / 2), ((hx + el[0]) / 2 + 6, (hy + el[1]) / 2 + 6)]
            wisps(cc, pts, T, a=k, rise=150, width=9, color='#8E949E')
            for i in range(9):
                ph = (T * 0.9 + i / 9) % 1.0
                px = hx + (hrand(i, 3) - 0.5) * 30 + math.sin(T * 2 + i) * 10 * ph
                py = hy - 10 - 120 * ph
                r = 8 + 18 * ph
                cc.drawCircle(px, py, r, paint('#7E848F', 0.45 * k * (1 - ph), blur=r * 0.6))
    return layer


def feb_tap(c, t, T):
    feb_room(c, T)
    corner_regular(c, T, face=dict(eye=blink(T, 11)))
    gym_props_front(c, T)
    tap = EV['tap_hero']
    froze = smooth(tap, tap + 0.25, T)
    hand_up = smooth(EV['hand_up'], EV['hand_up'] + 0.6, T)
    pose = seated_pose(T, look_up=0.5 * froze, hand_up=hand_up, freeze=tap)
    if T > tap:
        pose.update(eyes='wide', pupil=0.55, brow=-18, smile=-0.35, bags=0.8, lx=0.7 * (1 - hand_up), ly=-0.1)
    if hand_up > 0.3:
        pose.update(lx=0.9, ly=-0.6)
    amount = 0.5 * smooth(EV['smoke'], EV['smoke'] + 2.0, T)
    # the shadow rises behind him and lays a hand on his shoulder
    sh = world_of(HERO_JAN, pose, 'sh_b')
    s = SF * 1.18
    rise = smooth(48.7, 49.3, T)
    reach = smooth(tap - 0.35, tap, T)
    sx = SEAT[0] - 96 * s
    rest = (sx + 40 * s, ROW_F - 140 * s)
    hand = (rest[0] + (sh[0] - rest[0]) * reach, rest[1] + (sh[1] - rest[1]) * reach)
    lean = 14 + 16 * reach
    shade_beside(c, T, sx, ROW_F + 60 * (1 - rise), s, 1, hand_world=hand, alpha=rise, lean=lean,
                 eye=smooth(48.9, 49.2, T))
    layers = {'front': smoking_arm(HERO_JAN, T, amount)} if amount > 0 else None
    if layers:
        pose['no_arm_f'] = True
    HERO_JAN.draw(c, pose, layers, t=T)
    shade_hand_on(c, hand, s, rise)
    whisper(c, T, 'everyone quit.', 50.0, 52.0, SEAT[0] - 30, 575, 64, seed=11)
    whisper(c, T, 'go home.', 52.8, 54.2, SEAT[0] - 60, 590, 46, seed=12)


def cam_feb_tap(t):
    T = 48.6 + t
    if T < EV['hand_up']:
        u = smooth(48.6, 52.0, T)
        return (SEAT[0] - 30, 700 - 10 * u, 2.0 + 0.15 * u)
    u = smooth(EV['hand_up'], EV['hand_up'] + 1.0, T)
    return (SEAT[0] + 20 + 50 * u, 680 + 10 * u, 2.2 + 1.0 * u)


# --- 3. he gives up: up, bag, towards the door; the shadow walks him out (54.4-58) ---------------------------------

def walking_out_x(T):
    return BENCH_X - 40 - (BENCH_X - 40 - STOP_X) * smooth(EV['walk_out'], EV['stop'], T)


def hero_walk_pose(T, x, facing=-1, walking=True, look_up=0.0, speed=0.85):
    pose = dict(x=x, y=ROW_F - STAND_HIP * SF, scale=SF, facing=facing, turn=0.3, hb=-4, kb=3, hf=5, kf=3,
                lean=6 - 10 * look_up, tilt=-12 + 22 * look_up, eyes='tired', bags=0.8, brow=-12, smile=-0.3,
                ly=0.6 - 1.4 * look_up, lx=0.2, eye=blink(T, 8))
    if walking:
        pose.update(walk(T, speed, 16))
        pose['lean'] = 8
    return pose


def walk_out(c, t, T):
    feb_room(c, T)
    corner_regular(c, T, face=dict(eye=blink(T, 11)))
    gym_props_front(c, T)
    up = smooth(EV['stand_up'], EV['stand_up'] + 0.5, T)
    x = walking_out_x(T)
    walking = EV['walk_out'] + 0.1 < T < EV['stop'] - 0.05
    look_up = smooth(EV['stop'] - 0.1, EV['stop'] + 0.3, T)
    if T < EV['walk_out']:
        pose = seated_pose(T, look_up=0.3, hand_up=0.0)
        pose['y'] -= 40 * up
        pose['lean'] = 24 - 20 * up
        bag_held = False
    else:
        pose = hero_walk_pose(T, x, -1, walking, look_up)
        bag_held = True
    # his arm is still smoking a little
    pose['no_arm_f'] = True
    layers = {'front': smoking_arm(HERO_JAN, T, 0.5)}
    if bag_held:
        def bag_layer(cc, j):
            hx, hy = j['hand_b']
            cc.save()
            cc.translate(hx, hy + 70)
            cc.scale(0.62, 0.62)
            gym_bag(cc, 0, 0, '#3B4252')
            cc.restore()
        layers['behind'] = bag_layer
    else:
        gym_bag(c, BAG_X, ROW_F, '#3B4252', scale=0.6)
    # the shadow walks beside him, its hand on his far shoulder
    s = SF * 1.18
    sh = world_of(HERO_JAN, pose, 'sh_b')
    sx = pose['x'] + 92 * s
    spose = dict(walk(T + 0.1, 0.85, 14)) if walking else {}
    spose_all = dict(x=sx, y=ROW_F - STAND_HIP * s, scale=s, facing=-1, turn=0.15, hb=-4, kb=3, hf=5, kf=3,
                     lean=12, tilt=12, brow=20, sb=6, eb=10, sf=-4, ef=12)
    spose_all.update(spose)
    spose_all['lean'] = 12
    spose_all['hand_f'] = to_local(spose_all, sh)
    SHADE.draw(c, spose_all, t=T)
    HERO_JAN.draw(c, pose, layers, t=T)
    shade_hand_on(c, sh, s)


def cam_walk_out(t):
    T = EV['stand_up'] + t
    x = walking_out_x(T)
    return (x - 40, 600, 1.6)


# --- 4. the photos by the door (58-63.6) ---------------------------------------------------------------------------

def regular_in_print(k):
    """Where the regular stands in the k-th print on the wall (world coordinates)."""
    from common import PHOTO_H, PHOTO_W, PHOTO_CAM
    x = PHOTOS_X + k * PHOTO_GAP
    m, lab = PHOTO_W * 0.06, PHOTO_H * 0.26
    fh = PHOTO_H + m + lab
    cx, cy, z = PHOTO_CAM
    vw, vh = W / z, H / z
    u = (CORNER_X - (cx - vw / 2)) / vw
    v = (ROW_B - 210 * SB - (cy - vh / 2)) / vh
    return x - PHOTO_W / 2 + u * PHOTO_W, PHOTOS_Y - fh / 2 + m + v * PHOTO_H


def photos_insert(c, t, T):
    feb_room(c, T)
    for k in range(5):
        on = smooth(58.5 + k * 0.85, 59.1 + k * 0.85, T)
        if on > 0:
            rx, ry = regular_in_print(k)
            light_pool(c, rx, ry, 9, 12, '#FFE2A0', 0.55 * on)


def cam_photos(t):
    T = 58.0 + t
    u = smooth(58.1, 59.4, T)
    x = PHOTOS_X + 1.5 * PHOTO_GAP + 1.0 * PHOTO_GAP * u
    return (x, PHOTOS_Y + 2, 4.4 + 0.6 * u)


CLOSE_T0, CLOSE_DUR = 59.4, 0.84


def photo_closeups(c, t, T):
    """Each print in turn, close on the man in the corner: the same pose, forty years apart."""
    from common import ERAS, GRADES, photo_scene
    k = min(4, int((T - CLOSE_T0) / CLOSE_DUR))
    year = 1986 + 10 * k
    u = min(1.0, (T - CLOSE_T0 - k * CLOSE_DUR) / CLOSE_DUR)
    c.drawPaint(paint('#0B0D12'))
    c.save()
    c.translate(W / 2, H / 2)
    c.rotate([-2.0, 1.5, -1.0, 2.0, -0.5][k])
    border = 30
    c.drawRect(skia.Rect.MakeLTRB(-W / 2 - 60, -H / 2 - 60, W / 2 + 60, H / 2 + 60), paint('#F2EEE6'))
    c.clipRect(skia.Rect.MakeLTRB(-W / 2 + border, -H / 2 + border, W / 2 - border, H / 2 - border))
    z = 3.0 + 0.3 * u
    c.scale(z, z)
    c.translate(-(CORNER_X - 70), -(ROW_B - 205))
    grade = ERAS[year]['grade']
    if grade:
        c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(GRADES[grade])))
    slot = (HERO_JAN, 5) if year == 2026 else None
    photo_scene(c, 18.0, year, slot=slot)
    if grade:
        c.restore()
    c.restore()
    if grade:
        c.drawRect(skia.Rect.MakeWH(W, H), paint('#FFF4DC', 0.07))
    text(c, str(year), 120, 180, 130, 'GochiHand', '#FFFFFF', 1.0, align='left', shadow=0.8)
    flash = 1 - smooth(0.0, 0.12, u)
    if flash > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint('#FFFFFF', 0.5 * flash))


# --- 5. he turns; the old man in his corner nods (63.6-67) ----------------------------------------------------------

def hero_at_photos(c, T, turn=0.0, hand_amount=0.5, fist=0.0, shrug=0.0, shade_s=None):
    """The hero by the photos with the shadow at his shoulder."""
    facing = -1 if turn < 0.5 else 1
    pose = hero_walk_pose(T, STOP_X, facing, False, look_up=0.0 if turn else 0.6)
    if turn:
        pose.update(lx=0.9, ly=-0.1, eyes='dot', brow=-6 + 10 * fist, smile=-0.1 + 0.1 * fist, tilt=0)
    if fist > 0:
        pose['bags'] = 0.8 - 0.5 * fist
    rest = (STOP_X + facing * 74 * SF, ROW_F - 214 * SF)
    pose['hand_f'] = to_local(pose, rest)
    pose['no_arm_f'] = True
    hand_layer = smoking_arm(HERO_JAN, T, hand_amount, fist)
    s = shade_s or SF * 1.18
    sh = world_of(HERO_JAN, pose, 'sh_b' if facing < 0 else 'sh_f')
    off = smooth(EV['shrug'], EV['shrug'] + 0.25, T)
    back = smooth(EV['shrug'], EV['shrug'] + 0.7, T)
    sx = STOP_X - facing * (92 + 230 * back) * s
    rest_h = (sx - facing * 30 * s, ROW_F - 150 * s)
    hand = (sh[0] + (rest_h[0] - sh[0]) * off, sh[1] + (rest_h[1] - sh[1]) * off)
    alpha = 1.0 - smooth(EV['shrug'] + 0.45, EV['shrug'] + 1.0, T)
    if alpha > 0:
        flick = 0.3 + 0.7 * (math.sin(T * 40) > 0) if 0.05 < back < 0.8 else 1.0
        shade_beside(c, T, sx, ROW_F, s * (1 - 0.35 * back), -facing if facing < 0 else facing * -1,
                     hand_world=hand, alpha=alpha, lean=12 - 40 * back, tilt=12 - 30 * back, eye=flick)
    pose['y'] -= 16 * shrug
    pose['lean'] = pose.get('lean', 0) - 10 * shrug
    pose['tilt'] = pose.get('tilt', 0) + 8 * shrug
    sweep = math.sin(math.pi * smooth(EV['shrug'] - 0.12, EV['shrug'] + 0.32, T))
    if sweep > 0:
        # a backhand: his far arm swings out behind him into the shadow's hand, and he glares back at it
        pose.update(sb=10 - 100 * sweep, eb=14 + 16 * sweep, lx=0.9 - 1.8 * sweep, brow=-6 + 20 * sweep,
                    smile=-0.1 - 0.15 * sweep)
    HERO_JAN.draw(c, pose, {'front': hand_layer}, t=T)
    if alpha > 0:
        shade_hand_on(c, hand, s * (1 - 0.25 * back), alpha * (1 - off))
    from engine.fx import shards
    shards(c, sh[0] - facing * 20, sh[1], T, EV['shrug'] + 0.08, n=12, seed=4, color='#FF6B60', size=7,
           speed=340, life=0.55, direction=math.pi if facing > 0 else 0.0, spread=2.2)
    return pose


def hero_turns(c, t, T):
    feb_room(c, T)
    corner_regular(c, T)
    gym_props_front(c, T)
    turn = smooth(EV['turn'] + 0.2, EV['turn'] + 0.5, T)
    hero_at_photos(c, T, turn=turn)


def cam_hero_turns(t):
    return (STOP_X + 60, 640, 2.0 + 0.1 * smooth(0, 1.2, t))


def corner_nod(c, t, T):
    feb_room(c, T, corner=1.0)
    nod = EV['nod']
    done = smooth(nod - 0.9, nod - 0.5, T)
    dip = math.sin(math.pi * smooth(nod, nod + 0.8, T))
    face = dict(lx=-0.9 * done, ly=0.1 + 0.5 * dip, eyes='closed' if dip > 0.6 else 'dot', brow=2,
                smile=0.1 + 0.3 * smooth(nod + 0.4, nod + 0.9, T), head_dy=16 * dip, tilt=-17 * dip,
                eye=blink(T, 11))
    if T > nod - 0.5:
        face.update(sf=-4, ef=14, sb=6, eb=14)   # arms down, done with the set
    corner_regular(c, T, face=face)
    gym_props_front(c, T)


def cam_corner(t):
    u = smooth(0, 2.2, t)
    return (CORNER_X - 70, 640, 2.7 + 0.25 * u)


# --- 6. his fingers come back; the fist; the shrug (67-70), and back to the bench (70-72) -----------------------------

def hand_back(c, t, T):
    feb_room(c, T)
    corner_regular(c, T)
    gym_props_front(c, T)
    amount = 0.5 * (1 - smooth(EV['hand_back'], EV['hand_back'] + 0.8, T))
    fist = smooth(EV['fist'], EV['fist'] + 0.35, T)
    shrug = math.sin(math.pi * smooth(EV['shrug'] - 0.1, EV['shrug'] + 0.3, T))
    hero_at_photos(c, T, turn=1.0, hand_amount=amount, fist=fist, shrug=shrug)


def cam_hand_back(t):
    T = 67.0 + t
    u = smooth(67.0, 68.4, T)
    v = smooth(68.8, 69.8, T)
    return (STOP_X + 50 - 80 * v, 600 + 20 * v, 2.6 - 0.3 * u - 0.6 * v)


def back_to_bench(c, t, T):
    feb_room(c, T)
    corner_regular(c, T, face=dict(lx=-0.7, eye=blink(T, 11), smile=0.15))
    gym_props_front(c, T)
    drop = smooth(EV['drop_bag'], EV['drop_bag'] + 0.25, T)
    walk_u = smooth(70.5, 71.95, T)
    x = STOP_X + (BENCH_X - 60 - STOP_X) * walk_u
    pose = hero_walk_pose(T, x, 1, 0.02 < walk_u < 0.98, 0.0, speed=1.1)
    pose.update(eyes='dot', brow=8, smile=0.05, bags=0.3, ly=0.0, lx=0.4)
    if T < EV['drop_bag'] + 0.25:
        def bag_layer(cc, j):
            hx, hy = j['hand_b']
            cc.save()
            cc.translate(hx, hy + 70 + 60 * drop)
            cc.scale(0.62, 0.62)
            gym_bag(cc, 0, 0, '#3B4252')
            cc.restore()
        HERO_JAN.draw(c, pose, {'behind': bag_layer}, t=T)
    else:
        gym_bag(c, STOP_X - 20, ROW_F, '#3B4252', scale=0.6)
        HERO_JAN.draw(c, pose, t=T)


def cam_back(t):
    u = smooth(0, 2.0, t)
    return (STOP_X + 200 + 300 * u, 620, 1.35)


# --- 7. the bench: the old man spots him; lockout = the drop (72-78) -------------------------------------------------------

def spotter_pose(T, bar, x=None, who_scale=SF, arrive=1.0):
    x = BENCH_X - 145 * SF if x is None else x
    pose = dict(x=x, y=ROW_F - STAND_HIP * who_scale, scale=who_scale, facing=1, turn=0.3, hb=-4, kb=3, hf=5, kf=3,
                lean=16 * arrive, tilt=-8, eyes='dot', brow=2, smile=0.1, ly=0.8, lx=0.6, eye=blink(T, 13))
    if arrive > 0.6:
        pose['hand_f'] = to_local(pose, (bar[0] - 8, bar[1] + 24))
        pose['hand_b'] = to_local(pose, (bar[0] + 10, bar[1] + 26))
    return pose


def bench_scene(c, T, who, spotter, press, face, spot_face=None, arrive=1.0, plates=2, room=None):
    (room or feb_room)(c, T)
    if room is None:
        corner_regular(c, T, x=CORNER_X + 400)   # out of shot: he has walked over to spot
    gym_props_front(c, T)
    pose, layers = bench_press_pose(BENCH_X, ROW_F, SF, T, 3, 1, face, press=press, plates=plates)
    bar = pose.pop('_bar')
    if spotter is not None:
        sp = spotter_pose(T, bar, arrive=arrive)
        if arrive < 1:
            sp.update(walk(T, 1.0, 16))
            sp['x'] = BENCH_X - 145 * SF + 300 * (1 - arrive)
            sp['facing'] = -1
        if spot_face:
            sp.update(spot_face)
        spotter.draw(c, sp, t=T)
    who.draw(c, pose, layers, t=T)
    return pose, bar


def bench_drop(c, t, T):
    push = EV['push']
    lock = EV['drop']
    if T < 72.6:
        press = 0.95
    elif T < push:
        press = 0.95 * (1 - smooth(72.6, push, T))          # lowered to his chest
    elif T < push + 0.15:
        press = 0.0                                          # it sits there
    elif T < lock - 0.1:
        press = 0.35 * smooth(push + 0.15, lock - 0.1, T) + noise1(T * 22, 5) * 0.03   # the grind
    elif T < lock:
        press = 0.35 + 0.65 * smooth(lock - 0.1, lock, T)    # and through
    else:
        ph = (T - lock) % 1.0
        press = 1.0 - smooth(0.0, 0.5, ph) if ph < 0.6 else smooth(0.6, 0.95, ph)
    strain = smooth(push + 0.1, push + 0.3, T) * (1 - smooth(lock, lock + 0.15, T))
    face = dict(turn=0.3, eye=blink(T, 2), eyes='closed' if strain > 0.5 else 'dot', brow=-16 + 22 * smooth(lock, lock + 0.3, T),
                smile=-0.3 + 0.5 * smooth(lock, lock + 0.4, T), mouth='teeth' if strain > 0.5 else 'curve', bags=0.4)
    arrive = smooth(EV['lie_down'] + 0.1, EV['lie_down'] + 0.9, T)
    spot_face = dict(smile=0.1 + 0.4 * smooth(lock, lock + 0.6, T), eyes='happy' if T > lock + 0.3 else 'dot')
    pose, bar = bench_scene(c, T, HERO_JAN, OLD, press, face, spot_face, arrive)
    if strain > 0:
        jx, jy = shake(T, 2.0 * strain)
        c.drawCircle(bar[0] + jx, bar[1] + jy, 2, paint('#FFFFFF', 0.0))


def cam_bench(t):
    T = EV['lie_down'] + t
    u = smooth(72.0, 74.0, T)
    grind = smooth(EV['push'] + 0.15, EV['push'] + 0.4, T) * (1 - smooth(74.0, 74.05, T))
    sx, sy = shake(T, 2 * grind + 12 * smooth(74.0, 74.03, T) * (1 - smooth(74.03, 74.5, T)))
    return (BENCH_X - 120 + sx, 720 + sy, 2.0 + 0.35 * u - 0.15 * smooth(74.0, 74.3, T))


# --- 8. the year: struggle (78-82), the seasons run (82-94), strong (94-102) -----------------------------------------

YEAR_ROOM = dict(lights=(1, 1, 1, 0), banner_a=0.0)


def year_room(c, T, outside='snow_night', hour=19.0, string=0.0, corner=1.0):
    gym_room(c, T, lights=(1, 1, 1, 1), banner_a=0.0, outside=outside, hour=hour, string=string, corner=corner)
    gym_props_back(c, T)
    light_pool(c, 1000, ROW_F - 180, 900, 420, '#DCEBFF', 0.08)


def pullup(c, T, u_fit, ease_up, old_face=None, reps=1.4):
    year_room(c, T, outside='snow_night' if ease_up < 0.5 else 'fog')
    top = power_rack(c, RACK_X, ROW_F, scale=SF * 0.92)
    who = hero_fit(u_fit)
    s = SF
    hang = top + 6 + (84 + 104) * s
    if ease_up < 0.5:
        # can barely move: up a little, shaking, back down
        lift = 26 * s * max(0.0, math.sin(min(1.0, (T % 2.0) / 1.6) * math.pi)) + noise1(T * 25, 3) * 2
        face = dict(eyes='closed', mouth='teeth', brow=-18, smile=-0.3)
    else:
        ph = (T * reps) % 1.0
        lift = 84 * s * math.sin(ph * math.pi)
        face = dict(eyes='dot', brow=8, smile=0.1, mouth='curve')
    hip = (RACK_X - 6, hang - lift)
    pose = dict(x=hip[0], y=hip[1], scale=s, facing=1, turn=0.35, hb=8, kb=40, hf=14, kf=34, lean=0,
                tilt=-6 if lift > 30 else 0, eye=blink(T, 4), **face)
    pose['hand_b'] = to_local(pose, (RACK_X - 30, top + 6))
    pose['hand_f'] = to_local(pose, (RACK_X + 26, top + 6))
    pose['ik_b'] = pose['ik_f'] = -1.0
    # the old man beside the rack
    op = stand(RACK_X + 230, ROW_F, SF, -1, turn=0.3, eye=blink(T, 13), brow=0, smile=0.15, lx=0.4, ly=-0.6,
               sb=12, eb=78, sf=8, ef=82, lean=-2)   # arms folded
    if old_face:
        op.update(old_face)
    OLD.draw(c, op, t=T)
    who.draw(c, pose, t=T)
    c.drawLine(RACK_X - 180, top + 6, RACK_X + 180, top + 6, paint('outline', 0.0))


def struggle_pullup(c, t, T):
    pullup(c, T, 0.05, 0.0, old_face=dict(head_dy=4 * math.sin(T * 6), smile=0.2))


def strong_pullup(c, t, T):
    pullup(c, T, 0.95, 1.0, old_face=dict(eyes='happy', smile=0.45))


def cam_pullup(t):
    return (RACK_X + 110, 690, 1.75 + 0.05 * smooth(0, 2, t))


def rope_scene(c, T, u_fit, good):
    year_room(c, T, outside='snow_night' if not good else 'fog')
    who = hero_fit(u_fit)
    x = 900
    rate = 1.4 if not good else 3.2
    ph = (T * rate) % 1.0
    tangled = (not good) and T > 81.0
    hop = 0 if tangled else abs(math.sin(T * math.pi * rate)) * 16
    trip = smooth(81.0, 81.3, T) if tangled else 0.0
    pose = stand(x, ROW_F - hop, SF, 1, sb=18, eb=40, sf=-14, ef=40, turn=0.4, eye=blink(T, 5))
    pose['hand_b'] = (-26, 30)
    pose['hand_f'] = (34, 26)
    if good:
        cross = math.sin(T * math.pi * rate * 0.5) > 0.6
        if cross:
            pose['hand_b'] = (34, 20)
            pose['hand_f'] = (-20, 22)
        pose.update(brow=8, smile=0.3, eyes='dot')
    else:
        pose.update(brow=-6 - 8 * trip, smile=0.1 - 0.4 * trip, eyes='wide' if trip > 0.5 else 'dot', pupil=0.6,
                    lean=22 * trip, tilt=10 * trip, sb=18 - 130 * trip, sf=-14 + 150 * trip, ef=40 + 30 * trip,
                    mopen=0.4 * trip)
        if trip > 0:
            pose.pop('hand_b')
            pose.pop('hand_f')
            pose['x'] -= 10 * trip
            pose['hf'] = 5 - 30 * trip

    def rope_layer(cc, j):
        if tangled:
            hb, hf = j['hand_b'], j['hand_f']
            fb, ff = j['ft_b'], j['ft_f']
            for h, f, bend in ((hb, ff, -50), (hf, fb, 40)):
                path = skia.Path()
                path.moveTo(*h)
                path.cubicTo(h[0] + bend, h[1] + 60, f[0] + bend, f[1] - 20, *f)
                cc.drawPath(path, paint('outline', stroke=7))
                cc.drawPath(path, paint('#D9DCE2', stroke=3.5))
            for f in (fb, ff):
                cc.drawOval(oval(f[0] + 4, f[1] - 4, 16, 5), paint('outline', stroke=6))
                cc.drawOval(oval(f[0] + 4, f[1] - 4, 16, 5), paint('#D9DCE2', stroke=3))
        else:
            if good:
                for k in range(1, 4):
                    jump_rope(cc, j['hand_b'], j['hand_f'], (ph - 0.05 * k) % 1.0, a=0.28 / k, low=0)
            jump_rope(cc, j['hand_b'], j['hand_f'], ph, low=0)
    who.draw(c, pose, {'front': rope_layer}, t=T)
    laugh = smooth(81.2, 81.5, T) if not good else 0.0
    op = stand(x + 330, ROW_F, SF, -1, turn=0.3, eye=blink(T, 13), lx=0.5,
               eyes='happy' if (laugh > 0.5 or good) else 'dot', smile=0.2 + 0.5 * max(laugh, 1.0 if good else 0),
               head_dy=4 * math.sin(T * 16) * laugh, lean=-6 * laugh, sb=12, eb=78, sf=8, ef=82,
               mopen=0.35 * laugh * (0.5 + 0.5 * math.sin(T * 16)))
    if good:
        clap = abs(math.sin(T * 6))
        op.update(sb=60, eb=60, sf=60, ef=60)
        op['hand_f'] = (54 - 8 * clap, -50)
        op['hand_b'] = (36 + 8 * clap, -52)
    OLD.draw(c, op, t=T)


def struggle_rope(c, t, T):
    rope_scene(c, T, 0.1, False)


def strong_rope(c, t, T):
    rope_scene(c, T, 0.95, True)


def cam_rope(t):
    return (1060, 640, 1.65)


# the seasons run --------------------------------------------------------------------------------------------------

RUN_SPEED = 440.0     # how fast the world slides past (px/s): the speed of his planted foot, so he doesn't skate
RUN_X = 760           # where he stays on screen
GROUND = 900


SEASON_KEYS = [(82.0, 0.0), (83.8, 0.085), (84.0, 0.1), (85.3, 0.2), (86.6, 0.3), (94.0, 1.0)]


def season_at(T):
    """0 = March snow ... 1 = bare November; snow to 84 s, April rain to 85.3, May blossom to 86.6."""
    for (t0, s0), (t1, s1) in zip(SEASON_KEYS, SEASON_KEYS[1:]):
        if t0 <= T <= t1:
            return s0 + (s1 - s0) * (T - t0) / (t1 - t0)
    return 0.0 if T < SEASON_KEYS[0][0] else 1.0


def _keyed(keys, s):
    for (s0, v0), (s1, v1) in zip(keys, keys[1:]):
        if s0 <= s <= s1:
            return mixc(v0, v1, (s - s0) / (s1 - s0) if s1 > s0 else 0.0)
    return keys[-1][1] if s > keys[-1][0] else keys[0][1]


SKY_TOP = [(0.0, '#7D8DA3'), (0.12, '#4A5568'), (0.24, '#6FA8D8'), (0.5, '#3F8FD6'), (0.68, '#D98A4E'),
           (0.82, '#C9773E'), (1.0, '#6F7886')]
SKY_BOT = [(0.0, '#C9D3DE'), (0.12, '#7C8796'), (0.24, '#CFE6F2'), (0.5, '#BDE3F7'), (0.68, '#F2C98F'),
           (0.82, '#F0B070'), (1.0, '#AEB5BE')]
GRASS = [(0.0, '#E6ECF3'), (0.1, '#7F8C6A'), (0.24, '#6FAE5A'), (0.5, '#4E9A45'), (0.66, '#8FA04A'),
         (0.8, '#B98A3E'), (1.0, '#857A62')]
LEAF = [(0.0, '#E9EEF5'), (0.12, '#5B6A4E'), (0.22, '#F2B8CB'), (0.34, '#6FBF5A'), (0.55, '#3F8F3A'),
        (0.7, '#D9822E'), (0.84, '#C9572B'), (0.92, '#7A5A3A'), (1.0, '#E9EEF5')]
HILL = [(0.0, '#B9C3CF'), (0.12, '#5E6A6A'), (0.3, '#5F9A6A'), (0.6, '#4F8A55'), (0.8, '#A0703E'),
        (1.0, '#8A8F98')]


def leafiness(s):
    """How full the trees are: bare in March and November, full in summer."""
    if s < 0.16:
        return 0.15 * s / 0.16
    if s < 0.3:
        return 0.15 + 0.85 * (s - 0.16) / 0.14
    if s < 0.78:
        return 1.0
    if s < 0.95:
        return 1.0 - 0.95 * (s - 0.78) / 0.17
    return 0.05


def park_tree(c, x, ground, s, seed, size=1.0):
    h = 300 * size
    c.drawLine(x, ground, x, ground - h, paint('outline', stroke=26 * size))
    c.drawLine(x, ground, x, ground - h, paint('#5A4434', stroke=18 * size))
    for k, (dx, dy, ang) in enumerate(((-60, -230, -40), (60, -250, 40), (-20, -300, -10))):
        c.drawLine(x, ground - h * 0.55, x + dx * size, ground + dy * size, paint('#5A4434', stroke=9 * size))
    full = leafiness(s)
    color = _keyed(LEAF, s)
    if full > 0.02:
        for k in range(7):
            cx = x + hrange(-110, 110, k, seed) * size
            cy = ground - h * 0.95 + hrange(-80, 60, k, seed, 1) * size
            r = hrange(60, 95, k, seed, 2) * size * (0.45 + 0.55 * full)
            c.drawCircle(cx, cy, r + 5, paint('outline', min(1.0, full * 2)))
        for k in range(7):
            cx = x + hrange(-110, 110, k, seed) * size
            cy = ground - h * 0.95 + hrange(-80, 60, k, seed, 1) * size
            r = hrange(60, 95, k, seed, 2) * size * (0.45 + 0.55 * full)
            c.drawCircle(cx, cy, r, paint(color, min(1.0, full * 2)))
            c.drawCircle(cx - r * 0.3, cy - r * 0.3, r * 0.45, paint('#FFFFFF', 0.08 * min(1.0, full * 2)))
    if s < 0.08 or s > 0.96:
        snow = 1.0 - smooth(0.04, 0.08, s) if s < 0.5 else smooth(0.96, 1.0, s)
        for dx, dy, w in ((-60, -230, 50), (60, -250, 50), (0, -h - 2, 30)):
            c.drawOval(oval(x + dx * size * 0.9, ground + dy * size, w * size, 9 * size), paint('#F4F6FF', snow))


def park(c, T, s, scroll):
    sky = skia.GradientShader.MakeLinear(points=[(0, -100), (0, GROUND)],
                                         colors=[col(_keyed(SKY_TOP, s)), col(_keyed(SKY_BOT, s))])
    c.drawRect(skia.Rect.MakeLTRB(-200, -300, W + 200, GROUND + 10), paint('#000000', shader=sky))
    if 0.3 < s < 0.7:
        sun = smooth(0.3, 0.4, s) * (1 - smooth(0.62, 0.7, s))
        light_rays(c, 1500, 160, T, n=12, length=900, a=0.06 * sun, color='#FFF1C2')
        c.drawCircle(1500, 160, 70, paint('#FFF1C2', 0.6 * sun, blur=30, blend='add'))
        c.drawCircle(1500, 160, 46, paint('#FFF8E1', sun))
    if s > 0.6:
        glow = smooth(0.6, 0.72, s) * (1 - smooth(0.9, 1.0, s))
        c.drawCircle(1500, 520, 90, paint('#FFE0A0', 0.5 * glow, blur=40, blend='add'))
    # far hills and a skyline (slow), a row of small trees (medium), the near park (full speed)
    hill = _keyed(HILL, s)
    path = skia.Path()
    path.moveTo(-200, GROUND)
    for k in range(40):
        x = -200 + k * 70
        y = GROUND - 170 - 60 * math.sin((x + scroll * 0.12) * 0.004) - 30 * math.sin((x + scroll * 0.12) * 0.011 + 2)
        path.lineTo(x, y)
    path.lineTo(W + 200, GROUND)
    path.close()
    c.drawPath(path, paint(mixc(hill, '#FFFFFF', 0.25)))
    for k in range(-1, 12):
        bx = ((k * 230 - scroll * 0.35) % (12 * 230)) - 200
        park_tree(c, bx, GROUND - 40, s, 100 + k, size=0.45)
    c.drawRect(skia.Rect.MakeLTRB(-200, GROUND - 46, W + 200, H + 200), paint(_keyed(GRASS, s)))
    # the path
    c.drawRect(skia.Rect.MakeLTRB(-200, GROUND - 6, W + 200, GROUND + 40), paint(mixc('#8C8F96', '#E9EEF5',
                                                                                     1 - smooth(0.0, 0.1, s))))
    c.drawLine(-200, GROUND - 6, W + 200, GROUND - 6, paint('outline', stroke=3))
    for k in range(-1, 12):
        lx = ((k * 200 - scroll) % (12 * 200)) - 200
        c.drawLine(lx, GROUND + 16, lx + 60, GROUND + 16, paint('#FFFFFF', 0.15, stroke=4))
    if 0.08 < s < 0.2:
        for k in range(4):
            px = ((k * 520 + 260 - scroll) % (4 * 520)) - 200
            c.drawOval(oval(px, GROUND + 22, 70, 10), paint('#9FB3C8', 0.6))
    # near trees and lamp posts
    for k in range(-1, 8):
        tx = ((k * 470 + 120 - scroll) % (8 * 470)) - 260
        park_tree(c, tx, GROUND - 4, s, k, size=1.0)
    for k in range(-1, 6):
        lx = ((k * 610 + 400 - scroll) % (6 * 610)) - 200
        street_lamp(c, lx, GROUND - 4, height=430, on=1.0 if (s < 0.1 or s > 0.9) else 0.0)


def park_weather(c, T, s):
    if s < 0.1 or s > 0.94:
        a = (1 - smooth(0.06, 0.1, s)) if s < 0.5 else smooth(0.94, 0.98, s)
        snowfall(c, -100, -100, W + 100, H + 100, T, n=120, seed=31, wind=-160, speed=120, a=0.9 * a)
    if 0.08 < s < 0.22:
        a = smooth(0.08, 0.11, s) * (1 - smooth(0.18, 0.22, s))
        rainfall(c, -100, -100, W + 100, H + 100, T, n=150, seed=32, slant=-0.25, a=0.4 * a)
    if 0.2 < s < 0.34:
        a = smooth(0.2, 0.24, s) * (1 - smooth(0.3, 0.34, s))
        falling_leaves(c, -100, -100, W + 100, H + 100, T, n=30, seed=33, colors=('#F6B8C8', '#FFD7E0', '#F2A0B8'),
                       petals=True, a=a, size=8)
    if 0.66 < s < 0.92:
        a = smooth(0.66, 0.72, s) * (1 - smooth(0.88, 0.92, s))
        falling_leaves(c, -100, -100, W + 100, H + 100, T, n=40, seed=34, a=a, size=13)


def run_shot(c, t, T):
    s = season_at(T)
    scroll = RUN_SPEED * (T - EV['run'][0])
    park(c, T, s, scroll)
    # the shadow tries twice: a snowy bench, then the shade of a summer tree
    for t_pass, kind, size in ((83.6, 'bench', 1.0), (88.7, 'tree', 0.78)):
        wx = RUN_X + RUN_SPEED * (t_pass - EV['run'][0])
        sx = wx - scroll
        if -300 < sx < W + 300:
            near = smooth(t_pass - 1.1, t_pass - 0.2, T) * (1 - smooth(t_pass + 0.2, t_pass + 0.9, T))
            fade = 1 - smooth(t_pass + 0.4, t_pass + 1.2, T)
            sz = SF * 1.05 * size * (1 - 0.3 * smooth(t_pass, t_pass + 1.0, T))
            if kind == 'bench':
                c.drawRect(skia.Rect.MakeLTRB(sx - 110, GROUND - 70, sx + 110, GROUND - 56), paint('#6B4E3A'))
                c.drawRect(skia.Rect.MakeLTRB(sx - 110, GROUND - 120, sx + 110, GROUND - 108), paint('#6B4E3A'))
                for lx in (sx - 90, sx + 90):
                    c.drawRect(skia.Rect.MakeLTRB(lx - 5, GROUND - 60, lx + 5, GROUND), paint('#3A2E26'))
                c.drawOval(oval(sx, GROUND - 74, 112, 8), paint('#F4F6FF', 1 - smooth(0.06, 0.1, s)))
                pose = dict(x=sx + 10, y=GROUND - 64 - 10 * sz, scale=sz, facing=-1, turn=0.15, hb=86, kb=86,
                            hf=82, kf=82, lean=10 + 20 * near, tilt=10, brow=20, alpha=fade, eye=1.0)
                pose['foot_b'] = (40, 104)
                pose['foot_f'] = (60, 104)
            else:
                pose = dict(x=sx + 40, y=GROUND - 40 * sz, rot=-80, facing=-1, scale=sz, turn=0.1, hb=0, kb=20,
                            hf=10, kf=30, brow=20, alpha=fade, eye=0.6 + 0.4 * near)
            hero_x = RUN_X + 60
            if near > 0.01:
                tgt = (hero_x, GROUND - 260 * SF)
                rest = (pose['x'] - 60 * sz, pose['y'] - 40 * sz)
                pose['hand_f'] = to_local(pose, (rest[0] + (tgt[0] - rest[0]) * near * 0.8,
                                                 rest[1] + (tgt[1] - rest[1]) * near * 0.8))
            SHADE.draw(c, pose, t=T)
    # him, running through the year
    u = 0.1 + 0.8 * s
    r = run(T, 1.65, 40)
    dy = r.pop('dy')
    focus = 1.0
    pose = dict(x=RUN_X, y=GROUND - 2 - STAND_HIP * SF + dy, scale=SF, facing=1, turn=0.45, eye=blink(T, 3),
                eyes='dot', brow=6 + 4 * s, smile=-0.05 + 0.2 * s, **r)
    pose['lean'] = 12
    hero_fit(u).draw(c, pose, t=T)
    if 0.08 < s < 0.2:
        for k, ft in enumerate(_run_strikes(T)):
            age = T - ft
            if 0 <= age < 0.35:
                for j in range(6):
                    ang = math.pi + (j / 5) * math.pi
                    d = 40 * age / 0.35
                    c.drawCircle(RUN_X + 30 + math.cos(ang) * d, GROUND + 4 + math.sin(ang) * d * 0.6 - 40 * age,
                                 4, paint('#BFD3EA', 0.7 * (1 - age / 0.35)))
    park_weather(c, T, s)
    whisper(c, T, 'too cold.', 82.8, 84.3, 1240, 600, 70, seed=21)
    whisper(c, T, 'too hot.', 87.8, 89.2, 1220, 640, 70, seed=22)


def _run_strikes(T, speed=1.65):
    k0 = math.floor(T * speed * 2 - 0.5)
    return [(0.25 + 0.5 * k) / speed for k in range(k0 - 1, k0 + 2)]


def cam_run(t):
    return (900, 640 + 5 * math.sin(t * 2), 1.3)


# --- 9. December: deadlift and spotting him (98-102), the goodbye (102-106) ------------------------------------------

def deadlift(c, t, T):
    year_room(c, T, outside='snow_night', string=0.6)
    who = hero_fit(0.95)
    x = 900
    t0 = 98.4
    lift = smooth(t0, t0 + 0.8, T) * (1 - smooth(99.6, 100.0, T))
    plate_r = 46 * SF
    bar = (x + 18, ROW_F - plate_r * 0.95 - (ROW_F - plate_r - (ROW_F - 132 * SF)) * lift)
    hip_y = ROW_F - (92 + 31 * lift) * SF
    pose = dict(x=x - 30 * (1 - lift), y=hip_y, scale=SF, facing=1, turn=0.35, lean=52 * (1 - lift) + 2, tilt=-20 * (1 - lift),
                eye=blink(T, 5), eyes='dot', brow=10, smile=0.0 + 0.25 * lift, mouth='teeth' if 0.2 < lift < 0.9 else 'curve')
    pose['foot_b'] = to_local(pose, (x - 6, ROW_F - 4))
    pose['foot_f'] = to_local(pose, (x + 14, ROW_F - 4))
    pose['hand_b'] = to_local(pose, (bar[0] + 6, bar[1] + 2))
    pose['hand_f'] = to_local(pose, (bar[0] - 6, bar[1] + 4))
    barbell(c, *bar, plates=3, length=200 * SF, plate_r=plate_r, part='far', depth=(0.18, -0.2))
    who.draw(c, pose, t=T)
    barbell(c, *bar, plates=3, length=200 * SF, plate_r=plate_r, part='near', depth=(0.18, -0.2))
    op = stand(x + 360, ROW_F, SF, -1, turn=0.3, eye=blink(T, 13), lx=0.5, ly=0.2, sb=12, eb=78, sf=8, ef=82,
               smile=0.1 + 0.35 * smooth(t0 + 0.9, t0 + 1.3, T),
               head_dy=4 * math.sin(math.pi * smooth(99.3, 99.8, T)))
    OLD.draw(c, op, t=T)


def cam_deadlift(t):
    return (1060, 650, 1.6)


def spot_old(c, t, T):
    def room(cc, TT):
        year_room(cc, TT, outside='snow_night', string=0.8)
    face = dict(turn=0.3, eye=blink(T, 13), eyes='dot', brow=4, smile=0.35)
    press = 0.5 + 0.5 * math.cos((T - 100.0) * math.pi * 1.1)
    pose, layers = bench_press_pose(BENCH_X, ROW_F, SF, T, 3, 1, face, press=press, plates=3)
    bar = pose.pop('_bar')
    room(c, T)
    gym_props_front(c, T)
    sp = spotter_pose(T, bar)
    sp.update(eyes='happy', smile=0.4, brow=4)
    hero_fit(1.0).draw(c, sp, t=T)
    OLD.draw(c, pose, layers, t=T)


def goodbye(c, t, T):
    door = smooth(104.4, 104.8, T) * (1 - smooth(105.5, 105.9, T))
    gym_room(c, T, lights=(1, 1, 1, 0.6), banner_a=0.0, outside='snow_night', hour=20.5, string=1.0, door=door,
             door_out='#22385C')
    gym_props_back(c, T)
    gym_props_front(c, T)
    hero = hero_fit(1.0)
    hx = 860
    # the old man: towel on its hook, then out past the hero, a pat on the shoulder, a wave at the door
    path = Track([(102.0, CORNER_X - 40), (102.6, CORNER_X - 40), (103.3, hx + 110), (103.9, hx + 110),
                  (104.7, DOOR[0] + DOOR[1] * 0.6), (106.0, DOOR[0] + DOOR[1] * 0.6)], 'linear')
    ox = path(T)
    walking = 102.6 < T < 103.3 or 103.9 < T < 104.7
    pat = smooth(EV['pat'] - 0.25, EV['pat'], T) * (1 - smooth(EV['pat'] + 0.4, EV['pat'] + 0.7, T))
    hpose = stand(hx, ROW_F, SF, 1, turn=0.35, eye=blink(T, 1), lx=0.8 * smooth(102.8, 103.2, T), ly=-0.1,
                  eyes='happy' if 103.4 < T < 104.4 else 'dot', smile=0.2 + 0.4 * pat + 0.2 * smooth(104.4, 104.7, T),
                  brow=0)
    if T > 104.5:
        hpose['facing'] = -1
        hpose.update(sf=150, ef=20 + 25 * math.sin(T * 10), lx=0.6)
    sh = world_of(hero, hpose, 'sh_b' if hpose['facing'] > 0 else 'sh_f')
    opose = stand(ox, ROW_B + 40, SF * 0.95, -1, turn=0.3, eye=blink(T, 13), smile=0.3, brow=2, lx=0.3, ly=0.1,
                  **(walk(T, 0.9, 18) if walking else {}))
    if pat > 0:
        opose['hand_f'] = to_local(opose, (sh[0] + 4, sh[1] + 2))
    if T > 104.6:
        opose.update(facing=1, sf=150, ef=20 + 25 * math.sin(T * 9), lx=0.5, eyes='happy')
    opose['alpha'] = 1 - smooth(105.3, 105.6, T)
    if T < 102.6:
        towel(c, CORNER_X + 90, 400, '#E9E6DF', sway=4 * math.sin(T * 3))
        opose['hand_b'] = to_local(opose, (CORNER_X + 90, 420 + 60 * (1 - smooth(102.0, 102.5, T))))
    else:
        towel(c, CORNER_X + 90, 400, '#E9E6DF', sway=6 * math.exp(-(T - 102.6) * 2) * math.sin(T * 9))
    hero.draw(c, hpose, t=T)
    OLD.with_look(top='#3F4A5A', sleeve='long').draw(c, opose, t=T)


def cam_goodbye(t):
    T = 102.0 + t
    u = smooth(102.0, 105.5, T)
    return (1200 - 650 * u, 600, 1.3)


def overlays(c, T):
    pass


# --- assemble ---------------------------------------------------------------------------------------------------------

def shots():
    return [
        Shot(44.0, 48.6, feb_wide, cam_feb_wide, name='feb_wide'),
        Shot(48.6, EV['stand_up'], feb_tap, cam_feb_tap, name='feb_tap'),
        Shot(EV['stand_up'], EV['photos'], walk_out, cam_walk_out, name='walk_out'),
        Shot(EV['photos'], CLOSE_T0, photos_insert, cam_photos, name='photos'),
        Shot(CLOSE_T0, EV['turn'], photo_closeups, None, name='photo_closeups'),
        Shot(EV['turn'], 64.8, hero_turns, cam_hero_turns, name='hero_turns'),
        Shot(64.8, 67.0, corner_nod, cam_corner, name='corner_nod'),
        Shot(67.0, 70.0, hand_back, cam_hand_back, name='hand_back'),
        Shot(70.0, EV['lie_down'], back_to_bench, cam_back, name='back_to_bench'),
        Shot(EV['lie_down'], 78.0, bench_drop, cam_bench, name='bench_drop'),
        Shot(78.0, 80.0, struggle_pullup, cam_pullup, name='struggle_pullup'),
        Shot(80.0, 82.0, struggle_rope, cam_rope, name='struggle_rope'),
        Shot(82.0, 94.0, run_shot, cam_run, name='run'),
        Shot(94.0, 96.0, strong_pullup, cam_pullup, name='strong_pullup'),
        Shot(96.0, 98.0, strong_rope, cam_rope, name='strong_rope'),
        Shot(98.0, 100.0, deadlift, cam_deadlift, name='deadlift'),
        Shot(100.0, 102.0, spot_old, lambda t: (BENCH_X - 120, 720, 2.0), name='spot_old'),
        Shot(102.0, 106.0, goodbye, cam_goodbye, name='goodbye'),
    ]
