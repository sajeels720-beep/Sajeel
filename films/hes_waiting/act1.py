"""Act 1 (0:00-1:07): 2:47 AM and the figure at the foot of the bed, the title, the nights he wastes, the mirror,
and the night he turns his back."""
from __future__ import annotations

import math

import skia

from common import (BED, FLOOR, HERO, LIE_HIP, MATT, NIGHTSTAND, POSTER, SHADE, WINDOW, Room, battery_icon, blanket,
                    cane, draw_room, in_world, lying_blanket_contour, lying_pose, old_face, old_man, phone_angle,
                    phone_light, phone_side, phone_spot, pocket_watch, sit_edge_pose, to_world, vitality)
from cues import CHORUS, EV, WHISPERS
from engine.captions import title, whisper
from engine.core import H, W, beat_env, clamp, hrand, hrange, noise1, smooth
from engine.rig import blink
from engine.draw import col, mixc, oval, paint, poly, rrect, text
from engine.motion import CamPath, Curve, settle
from engine.render import Shot

OLD_X = 1040          # where the old man sits on the end of the bed


# --- the people in the night bedroom ---------------------------------------------------------------------------

def hero_in_bed(*, laugh_at=(), sleepy=0.0, phone=True, face_fn=None, swipes=None, screen=None):
    """Draw fn for the Room: the hero half-reclined under the quilt, scrolling.
    screen: (low_fn, dark_fn) for a phone that warns 1% and dies."""
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
            low, dark = (screen[0](T), screen[1](T)) if screen else (0.0, 0.0)
            phone_side(c, px, py, phone_angle(T), T, 1.0, swipes=swipes, low=low, dark=dark)
            hand = to_world(p, p['hand_f'])
            c.drawCircle(hand[0] + 4, hand[1] - 14, 7, paint(HERO.look.skin))
            c.drawCircle(hand[0] + 4, hand[1] - 14, 7, paint('outline', stroke=3.5))
        return p
    return draw


def old_on_bed(*, head_up=None, look=None, x=OLD_X, watch=True, flinch_at=(), cough_at=(), extra=None, young=None):
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
                p['smile'] = min(p.get('smile', 0.0), -0.35 * min(1.0, k * 3))
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
        j = who.draw(c, p, layers={'mid': mid}, t=T)
        ya = young(T) if young else 0.0
        if ya > 0 and not rim_pass:
            # his young face, in exactly the same place, dissolving into the old one
            from engine.rig import BASE_POSE
            face = dict(BASE_POSE)
            face.update(p)
            face.update(wet=0.0, bags=0.3, shiver=0.0)
            c.save()
            c.translate(p['x'], p['y'])
            s_ = p.get('scale', 1.0)
            c.scale(s_ * p['facing'], s_)
            c.saveLayerAlpha(None, int(255 * min(1.0, ya)))
            HERO._head(c, face, j)
            c.restore()
            c.restore()
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
    R.after = lambda cc, TT: phone_side(cc, *phone_spot(TT), phone_angle(TT), TT, 1.0)
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
             old=old_on_bed(head_up=lambda TT: up, look=lambda TT: 1.0, extra=extra,
                            young=lambda TT: 1 - smooth(9.05, 10.25, TT)),
             phone_at=phone_spot(T), phone_amt=1.0 + 1.4 * flare(T), old_rim=0.85, hero_rim=0.6)
    R.lights_extra = lambda cc: _face_light(cc, T)
    R.after = lambda cc, TT: phone_side(cc, *phone_spot(TT), phone_angle(TT), TT, 1.0)
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
    """Warm sparks torn out of the old man's chest and sucked into the phone, a burst at each pulse:
    they leave slowly and speed up as they near the screen (ease-in), go cold on the way, and the screen
    flares as it swallows them."""
    for t0 in pulses:
        if T < t0 or T > t0 + 2.4:
            continue
        # the light tearing out of his chest
        k = math.exp(-max(0.0, T - t0) / 0.45) * smooth(t0, t0 + 0.08, T)
        c.drawCircle(src[0], src[1], 70, paint('#FFC86B', 0.5 * k, blur=26, blend='add'))
        c.drawCircle(src[0], src[1], 22, paint('#FFF1C9', 0.7 * k, blur=6, blend='add'))
        for i in range(n):
            delay = hrand(i, seed, int(t0 * 10)) * 0.45
            u = (T - t0 - delay) / 1.05
            if u <= 0 or u >= 1:
                continue
            e = u ** 2.2                                    # slow to leave him, fast into the phone
            bend = -55 + hrange(-35, 35, i, seed, 2)
            jx, jy = hrange(-30, 30, i, seed, 3) * (1 - e), hrange(-30, 30, i, seed, 4) * (1 - e)
            x = src[0] + (dst[0] - src[0]) * e + jx
            y = src[1] + (dst[1] - src[1]) * e + bend * math.sin(math.pi * e) + jy
            a = min(1.0, u * 6) * (1 - smooth(0.88, 1.0, u)) * 0.95
            colr = mixc('#FFC86B', '#9CD8FF', e)
            r = hrange(3.5, 7.0, i, seed, 5) * (1 - 0.5 * e)
            # a trail back toward where it came from
            u2 = max(0.0, u - 0.09)
            e2 = u2 ** 2.2
            x2 = src[0] + (dst[0] - src[0]) * e2 + hrange(-30, 30, i, seed, 3) * (1 - e2)
            y2 = src[1] + (dst[1] - src[1]) * e2 + bend * math.sin(math.pi * e2) + hrange(-30, 30, i, seed, 4) * (1 - e2)
            c.drawLine(x2, y2, x, y, paint(colr, 0.5 * a, stroke=r * 0.9, blend='add'))
            c.drawCircle(x, y, r * 3.4, paint(colr, 0.4 * a, blur=8, blend='add'))
            c.drawCircle(x, y, r, paint(colr, a, blend='add'))
        # the screen swallows them
        f = smooth(t0 + 0.75, t0 + 1.0, T) * (1 - smooth(t0 + 1.1, t0 + 1.7, T))
        if f > 0:
            c.drawCircle(dst[0], dst[1], 90, paint('#BFE6FF', 0.45 * f, blur=30, blend='add'))
            c.drawCircle(dst[0], dst[1], 34 + 30 * f, paint('#FFFFFF', 0.5 * f, stroke=4, blur=3, blend='add'))


def chest(T):
    v = vitality(T)
    return to_world(sit_edge_pose(OLD_X, T, v), (14, -62))


def drain(c, t, T):
    R = Room(light='night', sky='night', curtain=0.86, hero=hero_in_bed(laugh_at=[EV['chuckle']]),
             old=old_on_bed(head_up=lambda TT: 0.55 * (1 - smooth(EV['cough'], EV['cough'] + 0.8, TT)),
                            look=lambda TT: 0.6, cough_at=[EV['cough']], flinch_at=EV['drain']),
             phone_at=phone_spot(T), old_rim=0.7, hero_rim=0.6)

    def after(cc, TT):
        phone_side(cc, *phone_spot(TT), phone_angle(TT), TT, 1.0)
        drain_motes(cc, TT, chest(TT), phone_spot(TT), EV['drain'])
    R.after = after
    draw_room(c, T, R)


cam_drain = CamPath([(0.0, (850, 690, 1.62)), (4.8, (876, 694, 1.76))], handheld=5, seed=3)


# --- 4. the shadow behind the headboard (16.8-20.4) ----------------------------------------------------------------

def shadow_whisper(c, t, T):
    lean = 34 * smooth(17.8, 18.7, T)
    R = Room(light='night', sky='night', curtain=0.86,
             hero=hero_in_bed(face_fn=lambda TT: dict(smile=0.05 + 0.3 * smooth(19.0, 19.7, TT),
                                                      eye=0.7 - 0.25 * smooth(19.1, 19.8, TT))),
             old=old_on_bed(head_up=lambda TT: 0.2, look=lambda TT: 0.3), phone_at=phone_spot(T), old_rim=0.6,
             hero_rim=0.6)

    def after(cc, TT):
        phone_side(cc, *phone_spot(TT), phone_angle(TT), TT, 1.0)
        eye = smooth(EV['eyes_open'], EV['eyes_open'] + 0.3, TT)
        shade_emissive(cc, TT, 452 + 22 * smooth(17.8, 18.7, TT), 792, lean=lean * 0.62, eye=eye, scale=1.22,
                       reach=0.12 * smooth(18.3, 19.1, TT))
    R.after = after
    draw_room(c, T, R)
    w = WHISPERS[0]
    whisper(c, T, w[0], w[1], w[2], 520, 520, 64, seed=1)


cam_shadow = CamPath([(0.0, (600, 650, 2.1)), (3.6, (614, 657, 2.34))], handheld=4, seed=4)


# --- 5. the title (20.4-23) ------------------------------------------------------------------------------------------

def title_drop(c, t, T):
    c.drawPaint(paint('#030305'))
    from cues import TITLE_CARD
    _, t0, t1 = TITLE_CARD[0]
    title(c, T, 'HE’S WAITING.', t0, t1, 590, size=130, underline=t0 + 0.6, ul_color='#D6A23D')
    a = smooth(t0 + 0.2, t0 + 0.8, T) * (1 - smooth(t1 - 0.4, t1 + 0.2, T))
    pocket_watch(c, W / 2, 360, 74, T, open_lid=False, a=a, glow=0.4)


# --- 6. the nights he wastes (23-36.5) ----------------------------------------------------------------------------

LOOP_SWIPES = [23.3, 24.4, 25.6, 26.9, 29.4, 30.5, 31.6, 33.8, 34.7, 35.6]


def night_room(T, *, old_kw=None, hero_kw=None, whisper_at=None, eyes=0.0, **kw):
    hk = dict(swipes=LOOP_SWIPES)
    hk.update(hero_kw or {})
    R = Room(light='night', sky='night', curtain=0.86, hero=hero_in_bed(**hk), old=old_on_bed(**(old_kw or {})),
             phone_at=phone_spot(T), old_rim=0.7, hero_rim=0.5, **kw)

    def after(cc, TT):
        phone_side(cc, *phone_spot(TT), phone_angle(TT), TT, 1.0, swipes=LOOP_SWIPES)
        if eyes > 0:
            from engine.rig import eye_pair
            cc.drawCircle(486, 690, 70, paint('#FF2A22', 0.12 * eyes, blur=30, blend='add'))
            eye_pair(cc, 486, 690, 72, eyes, 18)
    R.after = after
    return R


def corner_eyes(T, t0, t1):
    return smooth(t0 - 0.4, t0, T) * (1 - smooth(t1 + 0.2, t1 + 0.6, T))


CANE_TOP, CANE_TIP = (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2)


def new_cane(c, T):
    """Night 2, the morning after he snoozed his run: the old man has a walking stick now. It is the first thing we
    see; it slips on the floor and knocks against the bed as he shifts his weight onto it."""
    t0 = EV['cane'] + 0.3
    k = math.exp(-max(0.0, T - t0) / 0.18) * math.sin(max(0.0, T - t0) * 26) * (T >= t0)
    slide = 6 * smooth(t0 - 0.05, t0 + 0.08, T)
    cane(c, (CANE_TOP[0] + 5 * k, CANE_TOP[1] - 2 * abs(k)), (CANE_TIP[0] + slide, CANE_TIP[1]))


def night_shot(k):
    t0 = EV['nights'][k]
    w = WHISPERS[1 + k]
    looks = [0.2, 0.5, 0.9]
    cane_on = k >= 1

    def draw(c, t, T):
        R = night_room(T, old_kw=dict(head_up=lambda TT: 0.25 + 0.25 * k, look=lambda TT: looks[k],
                                      cough_at=[EV['coughs'][k]]), eyes=corner_eyes(T, w[1], w[2]))
        if k == 1:
            R.front = new_cane
        elif cane_on:
            R.front = lambda cc, TT: cane(cc, CANE_TOP, CANE_TIP)
        draw_room(c, T, R)
        whisper(c, T, w[0], w[1], w[2], 600, 560, 66, seed=10 + k)
    return draw


def cam_night(k):
    t0 = EV['nights'][k]
    z = [1.32, 1.42, 1.55][k]
    if k == 1:
        # close on the stick first, then back to the room: the old man is worse
        return CamPath([(0.0, (1100, 806, 3.1)), (0.4, (1098, 802, 3.0)), (1.15, (890, 662, z)),
                        (3.0, (900, 664, z + 0.04))], handheld=4, seed=11)
    return CamPath([(0.0, (880, 660, z)), (5.0, (900, 664, z + 0.06))], handheld=5, seed=10 + k)


def snooze(c, t, T):
    """6:00 AM: his RUN 5K alarm buzzing on the quilt, seen from above. His hand slaps SNOOZE and the screen goes
    dark. (The next night the old man needs a stick.)"""
    t0 = EV['snooze']
    ring = 1.0 - smooth(t0, t0 + 0.05, T)
    # the quilt from above in grey morning light
    c.drawPaint(paint('#3D5A80'))
    for k in range(-3, 9):
        y0 = -200 + k * 170 + 30 * math.sin(k * 1.7)
        fold = skia.Path()
        fold.moveTo(-100, y0)
        fold.cubicTo(500, y0 + 90, 1300, y0 - 60, 2100, y0 + 40)
        c.drawPath(fold, paint('#000000', 0.10, stroke=26, blur=10))
        c.drawPath(fold, paint('#FFFFFF', 0.05, stroke=8, blur=4))
    jx, jy = noise1(T * 70, 3) * 7 * ring, noise1(T * 70, 7) * 5 * ring
    cx, cy = 980 + jx, 540 + jy
    c.save()
    c.translate(cx, cy)
    c.rotate(-7)
    w, h = 380, 760
    c.drawRRect(rrect(-w / 2 + 14, -h / 2 + 22, w, h, 52), paint('#000000', 0.35, blur=24))
    c.drawRRect(rrect(-w / 2, -h / 2, w, h, 52), paint('#16171C'))
    scr = rrect(-w / 2 + 16, -h / 2 + 16, w - 32, h - 32, 40)
    c.save()
    c.clipRRect(scr, doAntiAlias=True)
    sh = skia.GradientShader.MakeLinear(points=[(0, -h / 2), (0, h / 2)], colors=[col('#1E2A44'), col('#0E1220')])
    c.drawRRect(scr, skia.Paint(Shader=sh))
    glow = 0.5 + 0.5 * math.sin(T * 14)
    text(c, '6:00', 0, -150, 150, 'Inter-Bold', '#FFFFFF')
    text(c, 'RUN 5K', 0, -60, 58, 'Inter-Bold', '#FFB36B')
    bw, bh, by = w * 0.74, 112, 120
    if ring > 0:
        c.drawRRect(rrect(-bw / 2 - 10, by - bh / 2 - 10, bw + 20, bh + 20, 64), paint('#F2A33A', 0.35 * glow * ring,
                                                                                      blur=10))
    c.drawRRect(rrect(-bw / 2, by - bh / 2, bw, bh, 56), paint('#F2A33A'))
    text(c, 'SNOOZE', 0, by + 20, 52, 'Inter-Bold', '#1A1208')
    text(c, 'stop', 0, by + 150, 40, 'Inter-Bold', '#8D97AD')
    # snoozed: the screen dims, says so, and goes dark
    off = smooth(t0 + 0.02, t0 + 0.12, T)
    if off > 0:
        c.drawRRect(scr, paint('#05060A', 0.8 * off))
        text(c, 'Snoozed', 0, 10, 48, 'Inter-Bold', '#8D97AD', off * (1 - smooth(t0 + 0.7, t0 + 0.9, T)))
        c.drawRRect(scr, paint('#05060A', smooth(t0 + 0.7, t0 + 0.9, T)))
    c.restore()
    c.drawRRect(rrect(-w / 2, -h / 2, w, h, 52), paint('outline', stroke=7))
    c.restore()
    # it buzzes against the quilt
    if ring > 0.02:
        for k in range(2):
            for side in (-1, 1):
                r = 250 + k * 50
                arc = skia.Path()
                arc.addArc(skia.Rect.MakeXYWH(cx - r + side * 200, cy - r, 2 * r, 2 * r), (0 if side > 0 else 180) - 18,
                           36)
                c.drawPath(arc, paint('#FFFFFF', 0.55 * ring * (1 - 0.35 * k) * glow, stroke=7))
    # his hand comes down on SNOOZE, rests there, and slides away
    come = smooth(t0 - 0.24, t0, T) ** 1.6
    leave = smooth(t0 + 0.55, t0 + 0.95, T)
    if come > 0 and leave < 1:
        bx, byw = cx + 30, cy + 140
        off_pos = (1750.0, -250.0)
        u = come * (1 - leave)
        hx = off_pos[0] + (bx - off_pos[0]) * u
        hy = off_pos[1] + (byw - off_pos[1]) * u
        squash = 1.0 + 0.06 * math.exp(-max(0.0, T - t0) / 0.08) * (T >= t0)
        _slap_hand(c, hx, hy, 2.5 * squash)
    # morning greyness at the edges
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 1300), paint('#0A0E18', 0.0))
    vg = skia.GradientShader.MakeRadial((960, 540), 1150, [col('#000000', 0.0), col('#000000', 0.55)], [0.55, 1.0])
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 1300), skia.Paint(Shader=vg))


def _slap_hand(c, x, y, s):
    """A hand, palm down, fingers toward the bottom left, the blue sleeve running off to the top right."""
    skin = HERO.look.skin
    c.save()
    c.translate(x, y)
    c.rotate(35)
    c.scale(s, s)
    c.drawLine(10, -60, 60, -460, paint('outline', stroke=74))
    c.drawLine(10, -60, 60, -460, paint(HERO.look.top, stroke=66))
    for dx, ln in ((-40, 70), (-14, 86), (12, 84), (36, 70)):
        f = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(dx - 11, 10, 22, ln), 11, 11)
        c.drawRRect(f, paint(skin))
        c.drawRRect(f, paint('outline', stroke=4))
    th = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(46, -20, 22, 56), 11, 11)
    c.drawRRect(th, paint(skin))
    c.drawRRect(th, paint('outline', stroke=4))
    c.drawOval(oval(0, -6, 60, 52), paint(skin))
    c.drawOval(oval(0, -6, 60, 52), paint('outline', stroke=4))
    c.restore()


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


cam_snooze = CamPath([(0.0, (960, 540, 1.0)), (1.5, (966, 546, 1.07))], handheld=3, seed=21)


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

    R = Room(light='day', sky='day', curtain=0.3, hero=hero, ambient='#E8E1D6')
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
             hero=hero, old=old, ambient=amb, phone_at=phone_spot(T), phone_amt=night, moon=night)
    draw_room(c, T, R)
    if night > 0.2:
        phone_side(c, *phone_spot(T), phone_angle(T), T, 1.0, swipes=[a + 0.25 * i for i in range(40)])
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
    dip = 230 * spit
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
                    mouth='wavy' if scared > 0.5 else 'curve', brow=-14 * scared, bags=0.8, ly=0.2 * (1 - scared))
        pose = brush_pose(T, False, face=face, frozen=EV['normal'] if T > EV['normal'] else None)
        pose['lean'] = 26 * spit
        pose['tilt'] = 18 * smooth(EV['spit'] + 0.05, EV['spit'] + 0.4, T) * (1 - smooth(EV['old_in_mirror'] - 0.35, EV['old_in_mirror'] - 0.05, T))
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


# --- 11. rock bottom (67-92.6) -----------------------------------------------------------------------------------------
#
# 4:12 AM. The watch stops; the phone warns 1% and dies. In the black glass he sees his own face, and it is the old
# man's. He lowers the phone and, for the first time, looks up: the old man is there. "I'm you." The old man looks at
# the poster on the wall, ONE DAY.: "One day never came." "I waited for you... my whole life." The boy cries. Black.

BOTTOM_SWIPES = [67.3, 68.9, 70.6, 71.65]
LOW_BATT = (71.0, 71.65)            # the 1% warning comes up over the clip; he swipes it away


def batt_low(T):
    return smooth(LOW_BATT[0], LOW_BATT[0] + 0.12, T) * (1 - smooth(LOW_BATT[1], LOW_BATT[1] + 0.1, T))


def screen_dark(T):
    """0 while the phone is alive, 1 once it has died."""
    return smooth(EV['phone_dies'], EV['phone_dies'] + 0.14, T)


def bottom_phone(c, x, y, angle, T, scale=1.0):
    phone_side(c, x, y, angle, T, scale, swipes=BOTTOM_SWIPES, low=batt_low(T), dark=screen_dark(T))


def slumped(T, extra_head=0.0, look=0.0, face=None):
    def draw(cc, TT, rim_pass=False):
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=extra_head, look=look)
        pp['lean'] += 10 * (1 - extra_head)
        pp['tilt'] += 8 * (1 - extra_head)
        if face:
            pp.update(face(TT) if callable(face) else face)
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
                fall = min(1.0, (dt / 0.3) ** 2)                      # it drops under its own weight...
                jerk = settle(dt, 0.3, 9.0, 5.5, 0.14) if dt > 0.3 else 0.0   # ...and bounces on the chain
                ang = math.radians(28 * math.exp(-dt / 1.6) * math.cos(dt * 5.4) * min(1.0, dt / 0.3))
                hand = to_world(pp, (34, 18))
                L = 10 + 70 * fall + jerk
                wx, wy = hand[0] + math.sin(ang) * L, hand[1] + math.cos(ang) * L
                anchor = hand
            pocket_watch(c2, wx, wy, 11, TT, detail=False, open_lid=False, chain=anchor,
                         stopped=EV['watch_stops'])
            c2.restore()
        old_man(v).draw(cc, pp, layers={'mid': mid}, t=TT)
        cane(cc, (OLD_X + 74, MATT - 70), (OLD_X + 92, FLOOR - 2))
        return pp
    return draw


def _bottom_face(TT):
    d = screen_dark(TT)
    if d <= 0:
        return None
    # the screen goes black and he keeps staring at it
    return dict(reflect=None, brow=-5 * d, eye=0.92 * blink(TT, 1, 5.0), ly=-0.6, lx=0.25)


def slump(c, t, T):
    dark = screen_dark(T)
    low = batt_low(T)
    R = Room(light='night', sky='night', curtain=0.86,
             hero=hero_in_bed(swipes=BOTTOM_SWIPES, face_fn=_bottom_face, screen=(batt_low, screen_dark)),
             old=slumped(T), phone_at=phone_spot(T), phone_amt=(1 - 0.45 * low) * (1 - dark), old_rim=0.7,
             hero_rim=0.5 * (1 - dark))

    def after(cc, TT):
        bottom_phone(cc, *phone_spot(TT), phone_angle(TT), TT)
        from engine.rig import eye_pair
        eye_pair(cc, 486, 690, 72, corner_eyes(TT, WHISPERS[6][1], WHISPERS[6][2]), 18)
    R.after = after
    draw_room(c, T, R)
    w = WHISPERS[6]
    whisper(c, T, w[0], w[1], w[2], 600, 540, 56, seed=60)


cam_slump = CamPath([(0.0, (880, 668, 1.4)), (4.0, (900, 676, 1.6)), (5.6, (840, 652, 1.86))], handheld=4, seed=41)


# --- the black glass (72.6-76.2) ----------------------------------------------------------------------------------------

BLACK_PHONE = (960, 520, 520, 1040)       # centre x, centre y, width, height of the phone in the close-up


def phone_drop(T):
    """The phone sinks out of the frame as he lowers it."""
    u = smooth(74.95, 75.6, T)
    return 1180 * u * u


def _beyond(c, T, blur):
    """Past the phone, out of focus: the moonlit end of the room and the old man sitting at the foot of the bed."""
    pnt = skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur, blur)) if blur > 0.3 else None
    c.saveLayer(None, pnt)
    c.drawPaint(paint('#0D1019'))
    # the window on the far wall, the moon's light coming through it
    c.drawRect(skia.Rect.MakeLTRB(170, 150, 520, 600), paint('#1B2238'))
    c.drawRect(skia.Rect.MakeLTRB(196, 176, 494, 574), paint('#2C3A5E'))
    c.drawLine(345, 176, 345, 574, paint('#1B2238', stroke=16))
    c.drawLine(196, 375, 494, 375, paint('#1B2238', stroke=16))
    c.drawCircle(345, 330, 300, paint('#7F95D6', 0.14, blur=110, blend='add'))
    c.drawRect(skia.Rect.MakeLTRB(-200, 780, 2200, 1300), paint('#121522'))
    # the old man on the end of the bed, facing him, slumped, the stopped watch hanging from his hand
    v = vitality(T)
    p = dict(x=1030, y=880, scale=2.1, facing=-1, turn=0.12, lean=16, tilt=18, sb=2, eb=8, sf=6, ef=12,
             hand_f=(30, 30), hand_b=(-30, 30), ik_f=1.0, ik_b=1.0, hb=-90, kb=0, hf=-90, kf=0)
    p.update(old_face(v, T))
    p.update(shiver=0.0, eye=0.45, ly=0.8, lx=0.0, alpha=1.0)
    old_man(v).draw(c, p, t=T)
    # moonlight: the far side of the room and the old man in a cold half-light
    moon = skia.GradientShader.MakeRadial((700, 420), 1100, [col('#A9B6DC'), col('#5D6A8E'), col('#262C40')],
                                          [0.0, 0.5, 1.0])
    ml = skia.Paint(Shader=moon)
    ml.setBlendMode(skia.BlendMode.kModulate)
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 1400), ml)
    c.drawCircle(860, 560, 360, paint('#9DB7FF', 0.06, blur=90, blend='add'))
    # the quilt over his own legs, a dark hump close to the lens
    hump = skia.Path()
    hump.moveTo(-200, 1200)
    hump.cubicTo(200, 900, 700, 880, 980, 950)
    hump.cubicTo(1260, 1010, 1700, 930, 2200, 1030)
    hump.lineTo(2200, 1300)
    hump.lineTo(-200, 1300)
    hump.close()
    c.drawPath(hump, paint('#1C2740'))
    c.restore()


def _reflection(c, T, gx, gy, gw, gh):
    """His face in the dead glass, lit by the moon from the window, turning into the old man's."""
    a = 0.7 * smooth(73.05, 73.6, T)
    if a <= 0:
        return
    from engine.rig import BASE_POSE, solve
    age = smooth(EV['reflection'], EV['reflection'] + 1.1, T)
    shock = smooth(74.3, 74.6, T)
    rect = skia.Rect.MakeXYWH(gx, gy, gw, gh)
    c.saveLayerAlpha(rect, int(255 * a))
    s = 3.1
    base = dict(facing=-1, turn=0.0, lean=0.0, tilt=0.0, sb=4.0, eb=4.0, sf=4.0, ef=4.0, shiver=0.0, lx=0.0,
                ly=-0.1, breathe=0.0, head_dx=0.0, head_dy=0.0)
    pp = dict(BASE_POSE)
    pp.update(base)
    hx_, hy_ = solve(HERO.look, pp)['head']
    head = (gx + gw * 0.5, gy + gh * 0.31)
    base.update(x=head[0] + hx_ * s, y=head[1] - hy_ * s, scale=s, hand_f=(84, 150), hand_b=(-84, 150), ik_f=1.0,
                ik_b=1.0)
    if age < 1:
        young = dict(base, eye=0.82 * blink(T, 1, 4.5), bags=0.9, brow=-3, smile=-0.04)
        if age > 0:
            c.saveLayerAlpha(rect, int(255 * (1 - age)))
        HERO.draw(c, young, t=T)
        if age > 0:
            c.restore()
    if age > 0:
        v = vitality(T)
        old = dict(base)
        old.update(old_face(v, T))
        old.update(shiver=0.0, eye=(0.72 + 0.28 * shock) * blink(T, 3, 6.0), brow=-10 - 6 * shock, wet=age,
                   smile=-0.2, bags=1.1, lx=0.0, ly=-0.1, breathe=0.0)
        c.saveLayerAlpha(rect, int(255 * age))
        old_man(v).draw(c, old, t=T)
        c.restore()
    # moonlight from the left on the face in the glass, the rest of it lost in the dark
    sh = skia.GradientShader.MakeLinear(points=[(gx, gy), (gx + gw, gy)],
                                        colors=[col('#C8D4F2'), col('#6A7690'), col('#232838')])
    lit = skia.Paint(Shader=sh)
    lit.setBlendMode(skia.BlendMode.kModulate)
    c.drawRect(rect, lit)
    # only the face catches the light; below it the reflection sinks into the black glass
    fall = skia.GradientShader.MakeRadial(head, 62 * s * 2.2, [col('#FFFFFF'), col('#FFFFFF'), col('#000000')],
                                          [0.0, 0.45, 1.0])
    lit2 = skia.Paint(Shader=fall)
    lit2.setBlendMode(skia.BlendMode.kModulate)
    c.drawRect(rect, lit2)
    c.restore()


def black_mirror(c, t, T):
    drop = phone_drop(T)
    focus = smooth(75.3, 76.0, T)
    _beyond(c, T, 16.0 * (1 - focus) + 0.2)
    cx, cy, w, h = BLACK_PHONE
    cy += drop
    c.save()
    c.translate(cx, cy)
    c.rotate(-3.0 + 2.0 * noise1(T * 0.5, 6))
    body = rrect(-w / 2, -h / 2, w, h, 64)
    c.drawRRect(body, paint('#000000', 0.5, blur=30))
    c.drawRRect(body, paint('#17181D'))
    gx, gy, gw, gh = -w / 2 + 18, -h / 2 + 18, w - 36, h - 36
    glass = rrect(gx, gy, gw, gh, 50)
    c.save()
    c.clipRRect(glass, doAntiAlias=True)
    c.drawRRect(glass, paint('#050609'))
    _reflection(c, T, gx, gy, gw, gh)
    # a dead battery, once, as he presses the button
    ba = smooth(72.62, 72.7, T) * (1 - smooth(72.95, 73.15, T))
    if ba > 0:
        battery_icon(c, 0, -60, 130, ba, level=0.0)
    # the glass: a cold sheen across it
    sheen = skia.GradientShader.MakeLinear(points=[(gx, gy), (gx + gw, gy + gh * 0.6)],
                                           colors=[col('#FFFFFF', 0.0), col('#BFD0FF', 0.10), col('#FFFFFF', 0.0)],
                                           positions=[0.25, 0.42, 0.6])
    c.drawRect(skia.Rect.MakeXYWH(gx, gy, gw, gh), skia.Paint(Shader=sheen))
    c.restore()
    c.drawRRect(glass, paint('#2A2C33', stroke=3))
    c.drawRRect(body, paint('outline', stroke=6))
    # his thumbs on the edges
    skin = HERO.look.skin
    for side in (-1, 1):
        c.save()
        c.translate(side * (w / 2 - 6), h * 0.2)
        c.rotate(-side * 18)
        th = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-42, -30, 84, 60), 30, 30)
        c.drawRRect(th, paint(skin))
        c.drawRRect(th, paint('#000000', 0.35))
        c.drawRRect(th, paint('outline', stroke=6))
        c.restore()
    c.restore()


def cam_black(t):
    from engine.core import shake
    k = 3.0 * smooth(1.9, 2.3, t) * (1 - smooth(2.8, 3.3, t))
    sx, sy = shake(t, k)
    return (960 + sx, 540 + sy, 1.0 + 0.1 * smooth(0.0, 3.0, t), 0.0)


# --- he looks up (76.2-78.8) ---------------------------------------------------------------------------------------------

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


def old_lift(T):
    return smooth(EV['old_lifts'], EV['old_lifts'] + 1.8, T)


def _moon_on_bed(c):
    from engine.light import pool
    pool(c, 760, 650, 300, 260, '#9DB7FF', 0.28)


def _seeing(TT):
    """Wide awake, staring at the old man; the shock softening as he sits up."""
    soft = smooth(EV['sit_up'] + 1.2, EV['sit_up'] + 2.4, TT)
    return dict(lx=0.9, ly=0.35, brow=-9 - 3 * soft, eye=(1.0 - 0.1 * soft) * blink(TT, 1, 4.2), smile=-0.06,
                bags=0.7, reflect=None)


def look_shot(c, t, T):
    R = Room(light='night', sky='night', curtain=0.86,
             hero=sitting_hero(look_up_fn, _seeing, phone_dead=EV['phone_dies']),
             old=slumped(T, extra_head=0.85 * old_lift(T), look=old_lift(T), face=dict(shiver=0.08)),
             old_rim=0.8)
    R.lights_extra = _moon_on_bed
    draw_room(c, T, R)


cam_look = CamPath([(0.0, (860, 690, 1.45)), (2.6, (884, 692, 1.56))], handheld=4, seed=43)


# --- "I'm you." (78.8-81) -------------------------------------------------------------------------------------------------

def speak_two(c, t, T):
    R = Room(light='night', sky='night', curtain=0.86,
             hero=sitting_hero(lambda TT: 1.0, lambda TT: dict(lx=0.9, ly=0.4, brow=-12, eye=0.95 * blink(TT, 1, 3.4),
                                                               smile=-0.06, reflect=None),
                               phone_dead=EV['phone_dies']),
             old=slumped(T, extra_head=0.85 * old_lift(T), look=1.0, face=dict(shiver=0.06, smile=-0.25)),
             old_rim=0.8)
    R.lights_extra = _moon_on_bed
    draw_room(c, T, R)


cam_speak_two = CamPath([(0.0, (900, 690, 1.6)), (2.2, (930, 680, 1.75))], handheld=3, seed=44)


# --- "One day never came." (81-84.4): he looks up at the poster ------------------------------------------------------

def _poster_face(TT):
    up = smooth(EV['poster_look'] + 0.1, EV['poster_look'] + 0.9, TT)
    back = smooth(84.0, 84.4, TT)
    u = up * (1 - back)
    return dict(lx=0.9 - 0.3 * u, ly=-0.3 - 0.75 * u, tilt=-6 - 10 * u, wet=0.6, brow=-14, smile=-0.25,
                shiver=0.05, eye=0.85 * blink(TT, 2, 5.5))


def poster_shot(c, t, T):
    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=1.0, look=1.0)
        pp.update(_poster_face(TT))
        pp['turn'] = 0.42
        if TT >= EV['watch_stops']:
            pp['hand_f'] = (34, 18)
        old_man(v).draw(cc, pp, t=TT)
        return pp

    R = Room(light='night', sky='night', curtain=0.86, hero=None, old=old, old_rim=0.85)

    def lights(cc):
        from engine.light import pool
        x, y, w, h = POSTER
        pool(cc, x + w / 2, y + h / 2, w * 1.9, h * 1.6, '#B8C8FF', 0.55)
        pool(cc, OLD_X - 40, 650, 220, 200, '#9DB7FF', 0.35)
    R.lights_extra = lights
    draw_room(c, T, R)


cam_poster = CamPath([(0.0, (1010, 640, 3.0)), (0.5, (1006, 638, 3.0)), (1.8, (850, 520, 2.85)),
                      (3.4, (836, 508, 3.05))], handheld=3, seed=47)


# --- "I waited for you... my whole life." (84.4-89.6) -----------------------------------------------------------------

def speak_close(c, t, T):
    def old(cc, TT, rim_pass=False):
        v = vitality(TT)
        pp = sit_edge_pose(OLD_X, TT, v, head_up=1.0, look=1.0)
        # a still face: the words are captions, his mouth never moves
        pp.update(wet=1.0, mopen=0.0, brow=-16, eye=0.8 * blink(TT, 2, 5.0), smile=-0.22, lx=0.9, ly=-0.3,
                  turn=0.42, tears=0.6 * smooth(86.9, 88.7, TT), shiver=0.0)
        if TT >= EV['watch_stops']:
            pp['hand_f'] = (34, 18)
        old_man(v).draw(cc, pp, t=TT)
        return pp

    R = Room(light='night', sky='night', curtain=0.86, hero=None, old=old, old_rim=0.9)
    R.lights_extra = lambda cc: _soft_face(cc)
    draw_room(c, T, R)


def _soft_face(c):
    from engine.light import pool
    pool(c, OLD_X - 40, 650, 220, 200, '#9DB7FF', 0.42)


cam_speak_close = CamPath([(0.0, (1004, 650, 3.2)), (5.2, (1000, 652, 3.6))], handheld=3, seed=45)


# --- his tear (89.6-91.6) ----------------------------------------------------------------------------------------------

def tear_shot(c, t, T):
    def face(TT):
        return dict(lx=0.9, ly=0.2, brow=-14, eye=0.85 * blink(TT, 1, 6.0), wet=1.0, smile=-0.2, reflect=None,
                    tears=0.8 * smooth(EV['tear'], EV['tear'] + 1.4, TT))
    R = Room(light='night', sky='night', curtain=0.86, hero=sitting_hero(lambda TT: 1.0, face,
                                                                          phone_dead=EV['phone_dies']),
             old=None, moon=0.9)

    def lights(cc):
        from engine.light import pool
        pool(cc, 700, 560, 240, 220, '#9DB7FF', 0.45)
    R.lights_extra = lights
    draw_room(c, T, R)


cam_tear = CamPath([(0.0, (690, 612, 3.3)), (2.0, (694, 614, 3.5))], handheld=3, seed=46)


# --- assemble -------------------------------------------------------------------------------------------------------------

def shots():
    n = EV['nights']
    return [
        Shot(0.0, 7.6, reveal, cam_reveal, name='reveal'),
        Shot(7.6, 8.8, eyes_young, cam_eyes_young, name='eyes_young'),
        Shot(8.8, 12.0, eyes_old, cam_eyes_old, name='eyes_old'),
        Shot(12.0, 16.8, drain, cam_drain, name='drain'),
        Shot(16.8, EV['title'], shadow_whisper, cam_shadow, name='shadow'),
        Shot(EV['title'], 23.0, title_drop, None, name='title'),
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
        Shot(72.6, EV['turn'], black_mirror, cam_black, name='black_glass'),
        Shot(EV['turn'], 78.8, look_shot, cam_look, name='look'),
        Shot(78.8, EV['poster_look'], speak_two, cam_speak_two, name='im_you'),
        Shot(EV['poster_look'], 84.4, poster_shot, cam_poster, name='one_day'),
        Shot(84.4, 89.6, speak_close, cam_speak_close, name='waited'),
        Shot(89.6, EV['black'], tear_shot, cam_tear, name='tear'),
    ]
