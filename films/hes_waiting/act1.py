"""Act 1 (0:00-1:07): 2:47 AM and the figure at the foot of the bed, the title, the nights he wastes, the mirror,
and the night he turns his back."""
from __future__ import annotations

import math

import skia

from common import (BED, FLOOR, HERO, LIE_HIP, MATT, NIGHTSTAND, SHADE, WINDOW, Room, blanket, cane, draw_room,
                    in_world, lying_blanket_contour, lying_pose, old_man, phone_light, phone_side, phone_spot,
                    pocket_watch, sit_edge_pose, to_world, vitality)
from cues import CHORUS, EV, WHISPERS
from engine.captions import title, whisper
from engine.core import H, W, beat_env, clamp, hrand, hrange, noise1, smooth
from engine.rig import blink
from engine.draw import mixc, oval, paint, poly, text
from engine.motion import CamPath, Curve, settle
from engine.render import Shot

OLD_X = 1040          # where the old man sits on the end of the bed


# --- the people in the night bedroom ---------------------------------------------------------------------------

def hero_in_bed(*, laugh_at=(), sleepy=0.0, phone=True, face_fn=None, swipes=None):
    """Draw fn for the Room: the hero half-reclined under the quilt, scrolling."""
    def draw(c, T, rim_pass=False):
        laugh = sum(math.exp(-max(0.0, T - t0) / 0.35) * (T >= t0) for t0 in laugh_at)
        face = face_fn(T) if face_fn else None
        p = lying_pose(T, phone=phone, face=face, swipes=swipes, laugh=min(1.0, laugh), sleepy=sleepy)
        p['back_arm_late'] = True
        quilt = in_world(c, lambda cc: blanket(cc, p['x'] - 130, lying_blanket_contour(p)))
        if rim_pass:
            c.save()
            from common import under_quilt
            under_quilt(c, p['x'] - 130, lying_blanket_contour(p))
            HERO.draw(c, p, t=T)
            c.restore()
        else:
            HERO.draw(c, p, layers={'mid': quilt}, t=T)
        if phone:
            px, py = phone_spot(T)
            phone_side(c, px, py, 18, T, 1.0, swipes=swipes)
            hand = to_world(p, p['hand_f'])
            c.drawCircle(hand[0] + 4, hand[1] - 14, 7, paint(HERO.look.skin))
            c.drawCircle(hand[0] + 4, hand[1] - 14, 7, paint('outline', stroke=3.5))
        return p
    return draw


def old_on_bed(*, head_up=None, look=None, x=OLD_X, watch=True, flinch_at=(), cough_at=(), extra=None):
    """Draw fn for the Room: the old man on the end of the bed with his watch."""
    def draw(c, T, rim_pass=False):
        v = vitality(T)
        hu = head_up(T) if head_up else 0.0
        lk = look(T) if look else 0.0
        p = sit_edge_pose(x, T, v, head_up=hu, look=lk)
        for t0 in flinch_at:
            if T >= t0:
                k = math.exp(-(T - t0) / 0.45) * smooth(t0, t0 + 0.12, T)
                p['lean'] += 5 * k
                p['tilt'] += 6 * k
                p['eye'] *= 1 - 0.5 * k
        for t0 in cough_at:
            if T >= t0:
                k = math.exp(-(T - t0) / 0.5) * abs(math.sin((T - t0) * 16))
                p['lean'] += 9 * k
                p['tilt'] += 6 * k
                p['mopen'] = max(p.get('mopen', 0.0), 0.4 * k)
                p['eye'] *= 1 - 0.7 * min(1.0, k * 2)
        if extra:
            p.update(extra(T, v) or {})
        who = old_man(v)

        def mid(cc, j):
            if watch:
                wx, wy = to_world(p, (52, -8))
                cc.save()
                cc.setMatrix(m)
                pocket_watch(cc, wx, wy, 11, T, detail=False, open_lid=False, chain=to_world(p, (16, -30)))
                cc.restore()
        m = c.getTotalMatrix()
        who.draw(c, p, layers={'mid': mid}, t=T)
        return p
    return draw


def shade_emissive(c, T, x, y, *, lean=0.0, reach=0.0, eye=1.0, alpha=1.0, scale=1.0, facing=1, clip_head=True):
    """The shadow, unlit, rising from behind the headboard (its body hidden by the headboard and nightstand)."""
    c.save()
    if clip_head:
        c.clipRect(skia.Rect.MakeLTRB(BED[0] - 30, MATT - 192, BED[0] + 10, FLOOR + 50), skia.ClipOp.kDifference)
        c.clipRect(skia.Rect.MakeLTRB(NIGHTSTAND[0] - 4, 786, NIGHTSTAND[1] + 4, FLOOR + 50), skia.ClipOp.kDifference)
        c.clipRect(skia.Rect.MakeLTRB(-2000, FLOOR, 3000, 3000), skia.ClipOp.kDifference)
    p = dict(x=x, y=y, facing=facing, scale=scale, lean=lean, tilt=8 + lean * 0.3, turn=0.3, eye=eye,
             brow=18, sb=10 + 60 * reach, eb=30, sf=20 + 70 * reach, ef=20, alpha=alpha,
             hb=-4, hf=6, kb=2, kf=4)
    SHADE.draw(c, p, t=T)
    c.restore()
    return p


# --- 1. 2:47 AM and the reveal (0-7.6) ----------------------------------------------------------------------------

def head_up_hook(T):
    return smooth(EV['head_up'], EV['head_up'] + 1.4, T) * 0.75


def reveal(c, t, T):
    R = Room(light='night', sky='night', curtain=0.86,
             hero=hero_in_bed(), old=old_on_bed(head_up=head_up_hook, look=lambda T: 0.8 * head_up_hook(T)),
             phone_at=phone_spot(T), old_rim=0.75, hero_rim=0.6)
    R.after = lambda cc, TT: phone_side(cc, *phone_spot(TT), 18, TT, 1.0)
    draw_room(c, T, R)


cam_reveal = CamPath([(0.0, (606, 668, 3.35)), (2.2, (614, 672, 3.15)), (4.6, (880, 690, 1.42)),
                      (7.6, (1000, 688, 1.62))], handheld=6, seed=1)


# --- 2. the match cut: his eyes, then the old man's (7.6-12) ---------------------------------------------------------

def eyes_young(c, t, T):
    reveal(c, t, T)


def cam_eyes_young(t):
    return (652 + 3 * t, 684, 5.4 + 0.15 * t, 30.0)


def flare(T):
    """A bright clip lights up the room at the reveal of his face."""
    return 0.6 * smooth(EV['flare'] - 0.1, EV['flare'] + 0.25, T) * (1 - smooth(11.4, 12.2, T))


def eyes_old(c, t, T):
    up = 0.75 + 0.25 * smooth(8.8, 10.2, T)
    wet = smooth(9.6, 11.0, T)

    def extra(TT, v):
        return dict(wet=wet, brow=-12 - 8 * wet, lx=0.85, ly=-0.25, turn=0.42)
    R = Room(light='night', sky='night', curtain=0.86, hero=hero_in_bed(),
             old=old_on_bed(head_up=lambda TT: up, look=lambda TT: 1.0, extra=extra),
             phone_at=phone_spot(T), phone_amt=1.0 + 1.4 * flare(T), old_rim=0.85, hero_rim=0.6)
    R.lights_extra = lambda cc: _face_light(cc, T)
    R.after = lambda cc, TT: phone_side(cc, *phone_spot(TT), 18, TT, 1.0)
    draw_room(c, T, R)


def _face_light(c, T):
    from engine.light import pool
    colr, br = phone_light(T)
    pool(c, OLD_X - 30, 640, 260, 220, mixc(colr, '#FFFFFF', 0.4), (0.25 + 0.75 * flare(T)) * br)


def cam_eyes_old(t):
    u = smooth(0.2, 3.2, t)
    return (1010 - 10 * u, 652 + 10 * u, 4.6 - 1.7 * u, 0.0)


# --- 3. every wasted day (12-16.2) -------------------------------------------------------------------------------------

def drain_motes(c, T, src, dst, pulses, n=44, seed=4):
    """Little warm sparks pulled out of the old man and into the phone, a burst at each pulse."""
    for t0 in pulses:
        if T < t0 or T > t0 + 2.2:
            continue
        for i in range(n):
            delay = hrand(i, seed, int(t0 * 10)) * 0.6
            u = (T - t0 - delay) / 1.2
            if u <= 0 or u >= 1:
                continue
            e = u * u * (3 - 2 * u)
            bend = -55 + hrange(-35, 35, i, seed, 2)
            x = src[0] + (dst[0] - src[0]) * e + hrange(-30, 30, i, seed, 3) * (1 - e)
            y = src[1] + (dst[1] - src[1]) * e + bend * math.sin(math.pi * e) + hrange(-30, 30, i, seed, 4) * (1 - e)
            a = math.sin(math.pi * u) * 0.95
            colr = mixc('#FFC86B', '#9CD8FF', e)
            r = hrange(3.5, 7.0, i, seed, 5) * (1 - 0.45 * e)
            c.drawCircle(x, y, r * 3.6, paint(colr, 0.4 * a, blur=8, blend='add'))
            c.drawCircle(x, y, r, paint(colr, a, blend='add'))
            # a short trail behind each spark
            u2 = max(0.0, u - 0.06)
            e2 = u2 * u2 * (3 - 2 * u2)
            x2 = src[0] + (dst[0] - src[0]) * e2 + hrange(-30, 30, i, seed, 3) * (1 - e2)
            y2 = src[1] + (dst[1] - src[1]) * e2 + bend * math.sin(math.pi * e2) + hrange(-30, 30, i, seed, 4) * (1 - e2)
            c.drawLine(x2, y2, x, y, paint(colr, 0.45 * a, stroke=r * 0.9, blend='add'))
        # the glow leaving his chest
        k = math.exp(-max(0.0, T - t0) / 0.5)
        c.drawCircle(src[0], src[1], 46, paint('#FFC86B', 0.35 * k, blur=18, blend='add'))


def chest(T):
    v = vitality(T)
    return to_world(sit_edge_pose(OLD_X, T, v), (14, -62))


def drain(c, t, T):
    R = Room(light='night', sky='night', curtain=0.86, hero=hero_in_bed(laugh_at=[EV['chuckle']]),
             old=old_on_bed(head_up=lambda TT: 0.55 * (1 - smooth(EV['cough'], EV['cough'] + 0.8, TT)),
                            look=lambda TT: 0.6, cough_at=[EV['cough']], flinch_at=EV['drain']),
             phone_at=phone_spot(T), old_rim=0.7, hero_rim=0.6)

    def after(cc, TT):
        phone_side(cc, *phone_spot(TT), 18, TT, 1.0)
        drain_motes(cc, TT, chest(TT), phone_spot(TT), EV['drain'])
    R.after = after
    draw_room(c, T, R)


cam_drain = CamPath([(0.0, (850, 690, 1.62)), (4.2, (872, 694, 1.74))], handheld=5, seed=3)


# --- 4. the shadow behind the headboard (16.2-19.4) ----------------------------------------------------------------

def shadow_whisper(c, t, T):
    lean = 34 * smooth(16.5, 17.4, T)
    R = Room(light='night', sky='night', curtain=0.86,
             hero=hero_in_bed(face_fn=lambda TT: dict(smile=0.05 + 0.3 * smooth(17.6, 18.4, TT),
                                                      eye=0.7 - 0.25 * smooth(17.8, 18.6, TT))),
             old=old_on_bed(head_up=lambda TT: 0.2, look=lambda TT: 0.3), phone_at=phone_spot(T), old_rim=0.6,
             hero_rim=0.6)

    def after(cc, TT):
        phone_side(cc, *phone_spot(TT), 18, TT, 1.0)
        eye = smooth(EV['eyes_open'], EV['eyes_open'] + 0.3, TT)
        shade_emissive(cc, TT, 452 + 22 * smooth(16.5, 17.4, TT), 792, lean=lean * 0.62, eye=eye, scale=1.22,
                       reach=0.12 * smooth(17.0, 17.8, TT))
    R.after = after
    draw_room(c, T, R)
    w = WHISPERS[0]
    whisper(c, T, w[0], w[1], w[2], 520, 520, 64, seed=1)


cam_shadow = CamPath([(0.0, (600, 650, 2.1)), (3.2, (612, 656, 2.3))], handheld=4, seed=4)


# --- 5. the title (19.4-23) ------------------------------------------------------------------------------------------

def title_drop(c, t, T):
    c.drawPaint(paint('#030305'))
    t0, t1 = 19.7, 22.6
    title(c, T, 'HE’S WAITING.', t0, t1, 590, size=130, underline=t0 + 0.6, ul_color='#D6A23D')
    a = smooth(19.9, 20.6, T) * (1 - smooth(22.2, 22.9, T))
    pocket_watch(c, W / 2, 360, 74, T, open_lid=False, a=a, glow=0.4)


# --- 6. the nights he wastes (23-36.5) ----------------------------------------------------------------------------

LOOP_SWIPES = [23.3, 24.4, 25.6, 26.9, 29.4, 30.5, 31.6, 33.8, 34.7, 35.6]


def night_room(T, *, old_kw=None, hero_kw=None, whisper_at=None, eyes=0.0, **kw):
    hk = dict(swipes=LOOP_SWIPES)
    hk.update(hero_kw or {})
    R = Room(light='night', sky='night', curtain=0.86, hero=hero_in_bed(**hk), old=old_on_bed(**(old_kw or {})),
             phone_at=phone_spot(T), old_rim=0.7, hero_rim=0.5, **kw)

    def after(cc, TT):
        phone_side(cc, *phone_spot(TT), 18, TT, 1.0, swipes=LOOP_SWIPES)
        if eyes > 0:
            from engine.rig import eye_pair
            cc.drawCircle(486, 690, 70, paint('#FF2A22', 0.12 * eyes, blur=30, blend='add'))
            eye_pair(cc, 486, 690, 72, eyes, 18)
    R.after = after
    return R


def corner_eyes(T, t0, t1):
    return smooth(t0 - 0.4, t0, T) * (1 - smooth(t1 + 0.2, t1 + 0.6, T))


def night_shot(k):
    t0 = EV['nights'][k]
    w = WHISPERS[1 + k]
    looks = [0.2, 0.5, 0.9]
    cane_on = k >= 1

    def draw(c, t, T):
        R = night_room(T, old_kw=dict(head_up=lambda TT: 0.25 + 0.25 * k, look=lambda TT: looks[k],
                                      cough_at=[EV['coughs'][k]]), eyes=corner_eyes(T, w[1], w[2]))
        if cane_on:
            R.front = lambda cc, TT: cane(cc, (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2))
        draw_room(c, T, R)
        whisper(c, T, w[0], w[1], w[2], 600, 560, 66, seed=10 + k)
    return draw


def cam_night(k):
    t0 = EV['nights'][k]
    z = [1.32, 1.42, 1.55][k]
    return CamPath([(0.0, (880, 660, z)), (5.0, (900, 664, z + 0.06))], handheld=5, seed=10 + k)


def snooze(c, t, T):
    """1:04 PM: the alarm buzzing on the quilt beside him; a hand slaps it quiet; he sleeps on."""
    reach = smooth(27.8, 28.02, T) * (1 - smooth(28.4, 28.75, T))
    ring = 1.0 - smooth(28.0, 28.06, T)
    spot = (712, MATT - 30)

    def hero(cc, TT, rim_pass=False):
        p = lying_pose(TT, phone=False, face=dict(eyes='closed', smile=-0.1, brow=-6 - 6 * reach), swipes=[])
        p['back_arm_late'] = True
        rest = (740, 770)
        p['hand_f'] = to_local_pose(p, (rest[0] + (spot[0] - rest[0]) * reach, rest[1] - 40 * math.sin(math.pi * reach)
                                        + (spot[1] - rest[1]) * reach))
        p['ik_f'] = -1.0
        quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 130, lying_blanket_contour(p)))
        HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        return p

    def front(cc, TT):
        j = noise1(TT * 80, 3) * 3 * ring
        cc.save()
        cc.translate(spot[0] + j, spot[1] + 4)
        cc.rotate(-8)
        cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-26, -8, 52, 12), 4, 4), paint('#16171C'))
        cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-23, -10, 46, 4), 2, 2), paint('#BFE6FF', 0.3 + 0.7 * ring))
        cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-26, -8, 52, 12), 4, 4), paint('outline', stroke=3))
        cc.restore()

    R = Room(light='day', sky='day', curtain=0.08, hero=hero, ambient='#D9D3CA', front=front)
    R.after = lambda cc, TT: _buzz_at(cc, TT, ring, spot)
    draw_room(c, T, R)
    # his hand comes down on top of the phone
    if reach > 0.85:
        p = lying_pose(T, phone=False, swipes=[])
        p['hand_f'] = to_local_pose(p, spot)


def _buzz_at(c, T, ring, spot):
    if ring <= 0.02:
        return
    x, y = spot
    j = noise1(T * 80, 3) * 3 * ring
    for k in range(2):
        r = 22 + k * 12
        for side in (-1, 1):
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeXYWH(x - r + j, y - 6 - r, 2 * r, 2 * r), -90 + side * 50 - 20, 40)
            c.drawPath(arc, paint('#FFFFFF', 0.7 * ring * (1 - 0.3 * k), stroke=3.5))


def _buzz(c, T, ring):
    if ring <= 0.02:
        return
    x, y = NIGHTSTAND[0] + 80, 784
    j = noise1(T * 80, 3) * 3 * ring
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 21 + j, y - 11, 42, 4), 2, 2), paint('#BFE6FF', ring))
    for k in range(2):
        r = 18 + k * 12
        for side in (-1, 1):
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeXYWH(x - r + j, y - 10 - r, 2 * r, 2 * r), -90 + side * 50 - 20, 40)
            c.drawPath(arc, paint('#FFFFFF', 0.7 * ring * (1 - 0.3 * k), stroke=3.5))


def to_local_pose(p, world):
    from common import to_local
    return to_local(p, world)


cam_snooze = CamPath([(0.0, (680, 712, 2.3)), (1.5, (684, 714, 2.4))], handheld=4, seed=21)


def bed_rot(c, t, T):
    """5:52 PM: sitting up in bed with the laptop; on the wall, one of his goals lets go."""
    from common import laptop_lap, sit_blanket_contour, sit_up_pose

    def hero(cc, TT, rim_pass=False):
        p = sit_up_pose(TT, 1.0, face=dict(eye=0.7 * blink(TT, 1), lx=0.6, ly=0.4, bags=0.7, smile=0.1))
        p['hand_f'] = (66, -36)
        p['hand_b'] = (58, -30)
        p['back_arm_late'] = True
        quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 40, sit_blanket_contour(p)))
        HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        laptop_lap(cc, p, TT)
        return p

    R = Room(light='day', sky='day', curtain=0.3, hero=hero, ambient='#E8E1D6', notes_drop=(0, EV['note_falls']))
    draw_room(c, T, R)


cam_bed_rot = CamPath([(0.0, (560, 650, 1.36)), (1.5, (548, 654, 1.4))], handheld=4, seed=22)


# --- 7. the time-lapse (36.5-43) ------------------------------------------------------------------------------------

def tl_day(T):
    """0 at night, 1 at noon: days and nights flicker past faster and faster."""
    a, b = EV['timelapse']
    if T >= b:
        return 1.0
    u = clamp((T - a) / (b - a))
    cycles = 2.2 * u + 5.0 * u * u            # how many days have gone by
    ph = cycles % 1.0
    return smooth(0.32, 0.42, ph) * (1 - smooth(0.82, 0.92, ph))


def blend_hex(c1, c2, u):
    from engine.draw import mixc as mc
    return '#%02X%02X%02X' % mc(c1, c2, u)


def timelapse(c, t, T):
    from common import laptop_lap, sit_blanket_contour, sit_up_pose
    day = tl_day(T)
    night = 1 - day
    a, b = EV['timelapse']
    k_notes = int(clamp((T - a) / (b - a)) * 5.5)

    def hero(cc, TT, rim_pass=False):
        if night > 0.02:
            p = lying_pose(TT, phone=True, swipes=[a + 0.25 * i for i in range(40)])
            p['back_arm_late'] = True
            p['alpha'] = night
            quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 130, lying_blanket_contour(p)))
            HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        if day > 0.02:
            p = sit_up_pose(TT, 1.0, face=dict(eye=0.6, lx=0.6, ly=0.4, bags=0.9))
            p.update(hand_f=(66, -36), hand_b=(58, -30), back_arm_late=True, alpha=day)
            quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 40, sit_blanket_contour(p)))
            HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
            laptop_lap(cc, p, TT)
        return None

    def old(cc, TT, rim_pass=False):
        if night < 0.05:
            return None
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=0.3, look=0.6)
        pp['alpha'] = night
        old_man(v).draw(cc, pp, t=TT)
        cane(cc, (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2), a=night)
        return pp

    amb = blend_hex('#2A3150', '#E8E1D6', day)
    R = Room(light='night' if day < 0.5 else 'day', sky='night' if day < 0.5 else 'day', curtain=0.86 - 0.5 * day,
             hero=hero, old=old, ambient=amb, phone_at=phone_spot(T), phone_amt=night, moon=night,
             notes_fallen=tuple(range(min(5, k_notes))))
    draw_room(c, T, R)
    if night > 0.2:
        phone_side(c, *phone_spot(T), 18, T, 1.0, swipes=[a + 0.25 * i for i in range(40)])
    for i, t0 in enumerate(CHORUS):
        x = [560, 1240, 760, 1420, 640, 1120, 900][i]
        y = [520, 470, 380, 600, 640, 360, 500][i]
        whisper(c, T, 'you have time.', t0, t0 + 0.9 + 0.1 * i, x, y, 50 + 4 * i, seed=30 + i)


cam_timelapse = CamPath([(0.0, (880, 650, 1.25)), (5.5, (900, 660, 1.42)), (6.5, (900, 660, 1.42))],
                        handheld=3, seed=23)


# --- 8. the mirror (43-57) ------------------------------------------------------------------------------------------

def brush_pose(T, who_old=False, v=0.15, frozen=None, face=None):
    """Facing the mirror (the reflection faces us), brushing; frozen=time the hand stops."""
    tb = T if frozen is None else min(T, frozen)
    rate = 3.2 if not who_old else 2.1
    side = math.sin(tb * rate * math.tau) * (9 if not who_old else 6)
    p = dict(x=0.0, y=0.0, facing=1, turn=0.0, scale=1.0, sb=8, eb=10, lean=0, tilt=0,
             hand_f=(14 + side, -126), ik_f=1.0, eye=blink(T, 4 if not who_old else 6, 3.3), mouth='curve',
             smile=-0.05, foam=1.0)
    if face:
        p.update(face)
    return p


def toothbrush(c, hand, mouth, a=1.0):
    hx_, hy_ = hand
    mx, my = mouth
    c.drawLine(hx_, hy_, mx + 6, my, paint('outline', a, stroke=10))
    c.drawLine(hx_, hy_, mx + 6, my, paint('#4FA3D9', a, stroke=5))


def foam(c, x, y, s, T, a=1.0):
    # a few bubbles at one corner of the mouth
    for k, (dx, dy, r) in enumerate(((13, 2, 3.2), (17, 6, 2.4), (10, 7, 2.0))):
        c.drawCircle(x + dx * s, y + dy * s, r * s, paint('#FFFFFF', 0.95 * a))
        c.drawCircle(x + dx * s, y + dy * s, r * s, paint('outline', 0.35 * a, stroke=1.5))


def reflection(c, T, x, base_y, s, who, pose, foam_a=1.0, brush=True):
    pose = dict(pose)
    pose.update(x=x, y=base_y, scale=s)
    j = who.draw(c, pose, t=T)
    hx_, hy_ = j['head']
    head = (x + hx_ * s, base_y + hy_ * s)
    mouth = (head[0] + 4 * s, head[1] + 0.38 * 62 * s)
    hand = (x + j['hand_f'][0] * s, base_y + j['hand_f'][1] * s)
    if brush:
        toothbrush(c, hand, mouth)
    if foam_a > 0:
        foam(c, mouth[0], mouth[1], s, T, foam_a)
    return head, hand


def mirror_scene(c, t, T):
    from common import MIRROR, back_view, bathroom_wall, mirror_back
    x, y, w, h = MIRROR
    bathroom_wall(c, T)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    mirror_back(c, T, x, y, w, h)
    spit = smooth(EV['spit'], EV['spit'] + 0.35, T) * (1 - smooth(EV['old_in_mirror'] - 0.3, EV['old_in_mirror'], T))
    dip = 260 * spit
    rx, ry, rs = 900, 770 + dip, 2.15
    old_phase = EV['old_in_mirror'] <= T < EV['normal']
    shade_eyes = smooth(EV['shade_mirror'], EV['shade_mirror'] + 0.4, T)
    if shade_eyes > 0:
        SHADE.draw(c, dict(x=rx + 250, y=ry + 30, scale=2.0, turn=0.2, facing=-1, eye=shade_eyes, lean=14,
                           tilt=-10, alpha=shade_eyes), t=T)
    if old_phase:
        v = vitality(T)
        stop = EV['stop_brush']
        look = smooth(EV['look'], EV['look'] + 0.5, T)
        palm = smooth(EV['palm'], EV['palm'] + 0.7, T)
        face = dict(eye=0.75 * blink(T, 6, 5.0), lx=0, ly=0.5 * (1 - look), brow=-10 - 8 * look, wet=look,
                    bags=1.2, smile=-0.2)
        pose = brush_pose(T, True, v, frozen=stop, face=face)
        pose['shiver'] = 0.4
        if palm > 0:
            pose['hand_f'] = (30 + 50 * palm, -126 - 30 * palm)
        reflection(c, T, rx, ry, rs, old_man(v), pose, foam_a=1.0, brush=palm < 0.3)
        if palm > 0.6:
            _palm_on_glass(c, rx + 230, ry - 330, (palm - 0.6) / 0.4, T)
    else:
        scared = smooth(EV['normal'], EV['normal'] + 0.2, T)
        face = dict(eye=(0.6 + 0.4 * scared) * blink(T, 4, 3.3), eyes='wide' if scared > 0.5 else 'dot',
                    mopen=0.3 * scared, brow=-14 * scared, bags=0.8, ly=0.2 * (1 - scared))
        pose = brush_pose(T, False, face=face, frozen=EV['normal'] if T > EV['normal'] else None)
        if T > EV['normal']:
            pose['hand_f'] = (20, -60)
        reflection(c, T, rx, ry, rs, HERO, pose, foam_a=1.0, brush=T < EV['normal'])
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint('#FFFFFF', 0.06))
    c.drawLine(x + 60, y + 30, x + 200, y + 170, paint('#FFFFFF', 0.12, stroke=14))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint('#5D6470', stroke=16))
    c.drawRect(skia.Rect.MakeXYWH(x - 8, y - 8, w + 16, h + 16), paint('outline', stroke=4))
    # the boy, from behind, in the foreground
    back = 1.0 + 0.25 * smooth(EV['step_back'], EV['step_back'] + 0.4, T)
    bob = 230 * spit
    tremble = 3.0 * smooth(EV['old_in_mirror'], EV['old_in_mirror'] + 0.3, T) * (1 - smooth(55.0, 56.0, T))
    back_view(c, 470 - 60 * (back - 1), 700 + bob + 90 * (back - 1), 1.75 * back, HERO.look, T=T, tremble=tremble)
    w_ = WHISPERS[4]
    whisper(c, T, w_[0], w_[1], w_[2], 1230, 250, 66, seed=40)
    dark = smooth(EV['light_off'], EV['light_off'] + 0.05, T)
    if dark > 0:
        c.drawRect(skia.Rect.MakeLTRB(-600, -600, 2600, 1600), paint('#000000', 0.94 * dark))
        if shade_eyes > 0:
            from engine.rig import eye_pair
            eye_pair(c, rx + 250 - 26, ry + 30 - 156 * 2.0 - 4, 62 * 2.0, shade_eyes * (1 - smooth(56.6, 56.9, T)), 18)
    # the blink
    if EV['blink'] <= T < EV['blink'] + 0.14:
        c.drawRect(skia.Rect.MakeLTRB(-600, -600, 2600, 1600), paint('#000000'))


def _palm_on_glass(c, x, y, u, T):
    s = 0.9 + 0.5 * u
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawOval(oval(0, 0, 70, 80), paint('#FFFFFF', 0.25 * u, blur=18))
    skin = old_man(0.15).look.skin
    for k, (dx, ln) in enumerate(((-40, 70), (-14, 86), (12, 84), (36, 70))):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(dx - 11, -40 - ln, 22, ln + 20), 11, 11), paint(skin))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(dx - 11, -40 - ln, 22, ln + 20), 11, 11),
                    paint('outline', stroke=4))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(48, -30, 22, 56), 11, 11), paint(skin))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(48, -30, 22, 56), 11, 11), paint('outline', stroke=4))
    c.drawOval(oval(0, 6, 58, 62), paint(skin))
    c.drawOval(oval(0, 6, 58, 62), paint('outline', stroke=4))
    c.drawOval(oval(0, 6, 40, 44), paint('#000000', 0.06))
    c.restore()


def cam_mirror(t):
    u = smooth(0, 14, t)
    kick = 14 * math.exp(-max(0.0, t - (EV['step_back'] - 43.0)) / 0.25) * (t > EV['step_back'] - 43.0)
    from engine.core import shake
    sx, sy = shake(t, kick)
    push = 0.14 * smooth(3.0, 6.0, t) + 0.22 * smooth(6.0, 9.0, t)
    return (900 + sx, 470 + sy - 10 * u, 1.18 + push - 0.18 * smooth(8.2, 8.6, t), 0.0)


# --- 9. he turns his back (57-63) -------------------------------------------------------------------------------------

def tent_glow(c, T, x0, x1, top):
    from engine.light import pool as lp
    colr, br = phone_light(T, LOOP_SWIPES2)
    c.save()
    path = _mound_path(x0, x1, top)
    c.clipPath(path, doAntiAlias=True)
    c.drawCircle((x0 + x1) / 2 - 40, top + 40, 150, paint(colr, 0.55 * br, blur=40, blend='add'))
    c.restore()


LOOP_SWIPES2 = [57.4, 58.6, 59.9, 61.1, 62.0]


def _mound_path(x0, x1, top):
    path = skia.Path()
    path.moveTo(x0, MATT + 34)
    path.cubicTo(x0 - 10, top - 10, x0 + 120, top - 30, (x0 + x1) / 2, top)
    path.cubicTo(x1 - 120, top + 20, x1 - 30, MATT - 40, x1, MATT - 4)
    path.lineTo(x1 + 10, MATT + 50)
    path.lineTo(x0, MATT + 50)
    path.close()
    return path


def avoid(c, t, T):
    reach = smooth(EV['reach'][0], EV['reach'][1], T) * (1 - smooth(EV['drop_hand'], EV['drop_hand'] + 0.6, T))

    def hero(cc, TT, rim_pass=False):
        path = _mound_path(BED[0] + 8, 1000, MATT - 96 + 3 * math.sin(TT * 1.4))
        cc.drawPath(path, paint('#3F5E86'))
        cc.save()
        cc.clipPath(path, doAntiAlias=True)
        for k in range(-6, 30):
            xx = BED[0] - 100 + k * 36
            cc.drawLine(xx, MATT - 160, xx + 70, MATT + 70, paint('#FFFFFF', 0.06, stroke=3))
        cc.restore()
        cc.drawPath(path, paint('outline', stroke=4))
        return None

    def extra(TT, v):
        if reach <= 0:
            return dict(look=0)
        target = (948 - 30 * reach, 742 - 10 * reach)
        return dict(hand_f=None, lean=12 + 10 * reach)

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=0.35 + 0.3 * reach, look=0.8)
        if reach > 0:
            pp['hand_f'] = to_local_pose(pp, (OLD_X - 70 - 60 * reach, 760 - 20 * reach + 6 * math.sin(TT * 14)))
            pp['ik_f'] = 1.0
            pp['lean'] += 8 * reach
        m = cc.getTotalMatrix()

        def mid(c2, j):
            if reach < 0.3:
                c2.save()
                c2.setMatrix(m)
                wx, wy = to_world(pp, (52, -8))
                pocket_watch(c2, wx, wy, 11, TT, detail=False, open_lid=False, chain=to_world(pp, (16, -30)))
                c2.restore()
        old_man(v).draw(cc, pp, layers={'mid': mid}, t=TT)
        cane(cc, (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2))
        return pp

    R = Room(light='night', sky='night', curtain=0.86, hero=hero, old=old, phone_at=(820, 760), phone_amt=0.45,
             old_rim=0.8)
    R.after = lambda cc, TT: tent_glow(cc, TT, BED[0] + 8, 1000, MATT - 96)
    draw_room(c, T, R)
    w = WHISPERS[5]
    whisper(c, T, w[0], w[1], w[2], 760, 560, 54, seed=50)


cam_avoid = CamPath([(0.0, (850, 680, 1.55)), (6.0, (930, 700, 1.9))], handheld=4, seed=31)


# --- 10. the watch, slowing (63-67) ------------------------------------------------------------------------------------

def tick_angle(T, times, settle_amp=0.12):
    k = sum(1 for x in times if T >= x)
    last = max([x for x in times if T >= x], default=None)
    frac = 0.0
    if last is not None:
        dt = T - last
        frac = -(math.exp(-dt * 40)) + settle(dt, 0.0, settle_amp, 10.0, 0.05)
    return (k + frac) / 60 * math.tau


def watch_insert(c, t, T):
    c.drawPaint(paint('#06080F'))
    c.drawCircle(1500, 260, 260, paint('#9DB7FF', 0.12, blur=110, blend='add'))
    v = vitality(T)
    skin = old_man(v).look.skin
    jx, jy = 4 * noise1(T * 8, 2), 4 * noise1(T * 8, 5)
    cx, cy = 960 + jx, 560 + jy
    # the palm from above, the wrist coming in from the bottom left
    wrist = poly([(cx - 520, cy + 700), (cx - 300, cy + 250), (cx - 60, cy + 300), (cx - 160, cy + 700)], True)
    c.drawPath(wrist, paint(old_man(v).look.top))
    c.drawPath(wrist, paint('outline', stroke=8))
    palm = skia.Path()
    palm.addOval(oval(cx - 30, cy + 120, 330, 270))
    c.drawPath(palm, paint(skin))
    c.drawPath(palm, paint('#000000', 0.1))
    c.drawPath(palm, paint('outline', stroke=8))
    for k, (dx, dy, ang) in enumerate(((230, -150, -30), (300, -40, -8), (300, 80, 14), (250, 190, 36))):
        c.save()
        c.translate(cx + dx, cy + dy)
        c.rotate(ang)
        f = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-40, -38, 120, 76), 38, 38)
        c.drawRRect(f, paint(skin))
        c.drawRRect(f, paint('outline', stroke=7))
        c.restore()
    ang = tick_angle(T, [62.0] + EV['watch_slow'])
    pocket_watch(c, cx, cy - 10, 250, T, hand_angle=ang, glow=0.12, open_lid=False, chain=(cx - 560, cy - 300))
    # the thumb over the edge of the case
    c.save()
    c.translate(cx - 250, cy + 120)
    c.rotate(-50)
    th = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-46, -40, 150, 80), 40, 40)
    c.drawRRect(th, paint(skin))
    c.drawRRect(th, paint('outline', stroke=7))
    c.restore()
    c.drawCircle(cx + 110, cy - 150, 70, paint('#C9D6FF', 0.12, blur=30, blend='add'))


def cam_watch(t):
    u = smooth(0, 4, t)
    return (960, 520, 1.0 + 0.12 * u, 0.0)


# --- 11. rock bottom (67-90.6) -----------------------------------------------------------------------------------------

BOTTOM_SWIPES = [67.3, 68.9, 70.6, 71.9]


def watch_fall(T):
    """0 while he holds it; then it slips and swings on its chain."""
    t0 = EV['watch_stops']
    return T >= t0


def slumped(T, extra_head=0.0, look=0.0):
    def draw(cc, TT, rim_pass=False):
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=extra_head, look=look)
        pp['lean'] += 10 * (1 - extra_head)
        pp['tilt'] += 8 * (1 - extra_head)
        m = cc.getTotalMatrix()
        dropped = TT >= EV['watch_stops']
        if dropped:
            pp['hand_f'] = (34, 18)

        def mid(c2, j):
            c2.save()
            c2.setMatrix(m)
            anchor = to_world(pp, (16, -30))
            if not dropped:
                wx, wy = to_world(pp, (52, -8))
            else:
                dt = TT - EV['watch_stops']
                drop = min(1.0, dt / 0.25)
                ang = math.radians(28 * math.exp(-dt / 1.6) * math.cos(dt * 5.4))
                hand = to_world(pp, (34, 18))
                L = 70 * drop + 10
                wx, wy = hand[0] + math.sin(ang) * L, hand[1] + math.cos(ang) * L
                anchor = hand
            pocket_watch(c2, wx, wy, 11, TT, detail=False, open_lid=False, chain=anchor,
                         stopped=EV['watch_stops'])
            c2.restore()
        old_man(v).draw(cc, pp, layers={'mid': mid}, t=TT)
        cane(cc, (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2))
        return pp
    return draw


def slump(c, t, T):
    R = Room(light='night', sky='night', curtain=0.86, hero=hero_in_bed(swipes=BOTTOM_SWIPES), old=slumped(T),
             phone_at=phone_spot(T), old_rim=0.7, hero_rim=0.5)

    def after(cc, TT):
        phone_side(cc, *phone_spot(TT), 18, TT, 1.0, swipes=BOTTOM_SWIPES)
        from engine.rig import eye_pair
        eye_pair(cc, 486, 690, 72, corner_eyes(TT, WHISPERS[6][1], WHISPERS[6][2]), 18)
    R.after = after
    draw_room(c, T, R)
    w = WHISPERS[6]
    whisper(c, T, w[0], w[1], w[2], 600, 540, 56, seed=60)


cam_slump = CamPath([(0.0, (880, 668, 1.4)), (5.6, (930, 690, 1.7))], handheld=4, seed=41)


def lowered_phone(T):
    u = smooth(EV['lower_phone'], EV['lower_phone'] + 1.4, T)
    px, py = phone_spot(T)
    return (px + 50 * u, py + 120 * u), u


def silence(c, t, T):
    def hero(cc, TT, rim_pass=False):
        (px, py), u = lowered_phone(TT)
        face = dict(eye=(0.78 + 0.22 * u) * blink(TT, 1, 3.6), lx=0.3 + 0.7 * u, ly=-0.5 + 0.7 * u, brow=6 * u,
                    smile=0.05 - 0.15 * u, reflect=None if u > 0.5 else (phone_light(TT, BOTTOM_SWIPES)[0], 0.8))
        p = lying_pose(TT, phone=True, face=face, swipes=BOTTOM_SWIPES)
        p['hand_f'] = to_local_pose(p, (px + 2, py + 30))
        p['back_arm_late'] = True
        p['tilt'] = -8 + 14 * u
        quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 130, lying_blanket_contour(p)))
        if rim_pass:
            from common import under_quilt
            cc.save()
            under_quilt(cc, p['x'] - 130, lying_blanket_contour(p))
            HERO.draw(cc, p, t=TT)
            cc.restore()
            return p
        HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        phone_side(cc, px, py, 18 + 40 * u, TT, 1.0, swipes=BOTTOM_SWIPES)
        return p

    (px, py), u = lowered_phone(T)
    R = Room(light='night', sky='night', curtain=0.86, hero=hero, old=slumped(T), phone_at=(px, py),
             phone_amt=1.0 - 0.4 * u, old_rim=0.7, hero_rim=0.5)
    R.after = lambda cc, TT: phone_side(cc, px, py, 18 + 40 * u, TT, 1.0, swipes=BOTTOM_SWIPES)
    draw_room(c, T, R)


cam_silence = CamPath([(0.0, (690, 680, 2.5)), (3.0, (700, 684, 2.6))], handheld=3, seed=42)


def sitting_hero(up_fn, face_fn=None, phone_dead=None):
    from common import sit_blanket_contour, sit_up_pose

    def draw(cc, TT, rim_pass=False):
        up = up_fn(TT)
        face = face_fn(TT) if face_fn else {}
        p = sit_up_pose(TT, up, face=face)
        p['back_arm_late'] = True
        p['hand_b'] = (44, -20)
        p['hand_f'] = (52, -26)
        from common import quilt_contour, under_quilt
        quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 60, quilt_contour(p, up)))
        if rim_pass:
            cc.save()
            under_quilt(cc, p['x'] - 60, quilt_contour(p, up))
            HERO.draw(cc, p, t=TT)
            cc.restore()
        else:
            HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        hand = to_world(p, p['hand_f'])
        phone_side(cc, hand[0] + 6, hand[1] - 6, 70, TT, 0.9, on=phone_dead is None or TT < phone_dead,
                   swipes=BOTTOM_SWIPES)
        return p
    return draw


def look_up_fn(T):
    return smooth(EV['sit_up'], EV['sit_up'] + 1.6, T)


def look_shot(c, t, T):
    R = Room(light='night', sky='night', curtain=0.86,
             hero=sitting_hero(look_up_fn, lambda TT: dict(lx=0.9, ly=0.4, brow=-6, eye=blink(TT, 1, 3.4),
                                                           smile=-0.1)),
             old=slumped(T), phone_at=(800, 740), phone_amt=0.5, old_rim=0.75, hero_rim=0.3)
    draw_room(c, T, R)


cam_look = CamPath([(0.0, (860, 690, 1.45)), (3.0, (880, 694, 1.55))], handheld=4, seed=43)


def speak_mouth(T):
    """Rough syllables for the old man's two lines."""
    from cues import SPEECH
    m = 0.0
    for text_, t0, t1, who in SPEECH[:2]:
        if t0 <= T <= t1:
            env = smooth(t0, t0 + 0.1, T) * (1 - smooth(t1 - 0.25, t1, T))
            m = max(m, env * (0.08 + 0.2 * abs(math.sin((T - t0) * 9.5)) * (0.6 + 0.4 * noise1(T * 4, 7))))
    return m


def speak_two(c, t, T):
    lift = smooth(EV['old_lifts'], EV['old_lifts'] + 1.8, T)
    R = Room(light='night', sky='night', curtain=0.86,
             hero=sitting_hero(lambda TT: 1.0, lambda TT: dict(lx=0.9, ly=0.4, brow=-8, eye=blink(TT, 1, 3.4))),
             old=slumped(T, extra_head=0.85 * lift, look=1.0), phone_at=(800, 740), phone_amt=0.5, old_rim=0.8)
    draw_room(c, T, R)


cam_speak_two = CamPath([(0.0, (900, 690, 1.6)), (2.4, (930, 680, 1.75))], handheld=3, seed=44)


def speak_close(c, t, T):
    lift = 0.85 + 0.15 * smooth(81.0, 82.0, T)

    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=lift, look=1.0)
        pp.update(wet=smooth(81.0, 83.0, TT), mopen=speak_mouth(TT), brow=-16, eye=0.8 * blink(TT, 2, 5.0),
                  smile=-0.15 + 0.25 * smooth(86.6, 87.6, TT), lx=0.9, ly=-0.3, turn=0.42,
                  tears=0.6 * smooth(85.6, 87.4, TT))
        if TT >= EV['watch_stops']:
            pp['hand_f'] = (34, 18)
        old_man(v).draw(cc, pp, t=TT)
        return pp

    R = Room(light='night', sky='night', curtain=0.86, hero=None, old=old, phone_at=(800, 740), phone_amt=0.55,
             old_rim=0.9)
    R.lights_extra = lambda cc: _soft_face(cc)
    draw_room(c, T, R)


def _soft_face(c):
    from engine.light import pool
    pool(c, OLD_X - 40, 650, 220, 200, '#9DB7FF', 0.35)


cam_speak_close = CamPath([(0.0, (1004, 650, 3.2)), (9.0, (1000, 652, 3.6))], handheld=3, seed=45)


def tear_shot(c, t, T):
    dead = EV['phone_dies']

    def face(TT):
        return dict(lx=0.9, ly=0.2, brow=-14, eye=0.85 * blink(TT, 1, 6.0), tears=0.8 * smooth(EV['tear'], EV['tear'] + 1.6, TT),
                    wet=1.0, smile=-0.2, mouth='curve')
    on = 1.0 - smooth(dead, dead + 0.08, T)
    R = Room(light='night', sky='night', curtain=0.86, hero=sitting_hero(lambda TT: 1.0, face, phone_dead=dead),
             old=None, phone_at=(820, 730), phone_amt=0.9 * on, hero_rim=0.45 * on, moon=0.85)
    draw_room(c, T, R)


cam_tear = CamPath([(0.0, (800, 640, 3.4)), (3.0, (804, 642, 3.65))], handheld=3, seed=46)


# --- assemble -------------------------------------------------------------------------------------------------------------

def shots():
    n = EV['nights']
    return [
        Shot(0.0, 7.6, reveal, cam_reveal, name='reveal'),
        Shot(7.6, 8.8, eyes_young, cam_eyes_young, name='eyes_young'),
        Shot(8.8, 12.0, eyes_old, cam_eyes_old, name='eyes_old'),
        Shot(12.0, 16.2, drain, cam_drain, name='drain'),
        Shot(16.2, 19.4, shadow_whisper, cam_shadow, name='shadow'),
        Shot(19.4, 23.0, title_drop, None, name='title'),
        Shot(n[0], 27.5, night_shot(0), cam_night(0), name='night1'),
        Shot(27.5, 29.0, snooze, cam_snooze, name='snooze'),
        Shot(n[1], 32.0, night_shot(1), cam_night(1), name='night2'),
        Shot(32.0, 33.5, bed_rot, cam_bed_rot, name='bed_rot'),
        Shot(n[2], EV['timelapse'][0], night_shot(2), cam_night(2), name='night3'),
        Shot(EV['timelapse'][0], EV['mirror'], timelapse, cam_timelapse, name='timelapse'),
        Shot(EV['mirror'], EV['avoid'], mirror_scene, cam_mirror, name='mirror'),
        Shot(EV['avoid'], 63.0, avoid, cam_avoid, name='avoid'),
        Shot(63.0, EV['slump'], watch_insert, cam_watch, name='watch'),
        Shot(EV['slump'], 72.6, slump, cam_slump, name='slump'),
        Shot(72.6, 75.6, silence, cam_silence, name='silence'),
        Shot(75.6, 78.6, look_shot, cam_look, name='look'),
        Shot(78.6, 81.0, speak_two, cam_speak_two, name='speak_two'),
        Shot(81.0, 87.6, speak_close, cam_speak_close, name='speak_close'),
        Shot(87.6, EV['black'], tear_shot, cam_tear, name='tear'),
    ]
