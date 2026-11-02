"""Act 3 (2:37-3:32): the climb in the dark, the last step, the sunrise, the watch, the old man going into the
light, 2:47 AM again, and the title card."""
from __future__ import annotations

import math

import skia

from act1 import OLD_X, hero_in_bed, tick_angle
from act2 import HIKER, headband_lamp, headlamp, strap_layer
from common import (BED, FLOOR, HERO, MATT, Room, blanket, draw_room, in_world, lying_blanket_contour, lying_pose,
                    old_face, old_man, pocket_watch, to_local, to_world, vitality)
from cues import EV
from engine.captions import title
from engine.core import H, W, clamp, hrand, hrange, noise1, smooth
from engine.draw import mixc, oval, paint, poly, rrect, text
from engine.fx import dissolve, light_rays
from engine.motion import CamPath, Curve, Gait, blend, breath, stand_feet
from engine.render import Shot
from engine.rig import blink
from world import (SUMMIT_X, SUMMIT_Y, cloud_sea, grad, hexmix, mountainside, slope_y, stars, summit_rock,
                   summit_sky, sun_disc)


def stick(c, p, j, ground_y, a=1.0):
    hand = to_world(p, j['hand_f'])
    tip = (hand[0] + 24 * p.get('facing', 1), ground_y - 2)
    c.drawLine(hand[0], hand[1] - 28, tip[0], tip[1], paint('outline', a, stroke=10))
    c.drawLine(hand[0], hand[1] - 28, tip[0], tip[1], paint('#9C7A52', a, stroke=5))


# --- 1. the climb in the dark, alone (157-167) --------------------------------------------------------------------------

A0 = EV['ascent']
ASC_H = Curve([(A0 - 0.5, 380.0), (A0 + 10.5, 1640.0)])
G_ASC_H = Gait(ASC_H, A0 - 0.5, A0 + 10.5, 0, step=74, lean=12, arm=16, ground=slope_y, lift=16)


def ascent(c, t, T):
    cx, cy, z, _ = cam_ascent(t)
    dawn = 0.35 * smooth(A0, A0 + 10, T)
    mountainside(c, T, cx, cy, dawn)
    ph = G_ASC_H.pose(T)
    ph.update(turn=0.3, eye=blink(T, 1, 3.4), lean=ph['lean'] + 6, mopen=0.0, breathe=breath(T, 0.5, 1.0, 1),
              brow=-4)
    jh = HIKER.draw(c, ph, layers={'behind': strap_layer(), 'over_head': headband_lamp}, t=T)
    headlamp(c, ph, jh, T, reach=460)


def cam_ascent(t):
    T = A0 + t
    mx = ASC_H(T) + 40
    return (mx, slope_y(mx) - 210 + noise1(t * 0.4, 91) * 3, 1.12, 0.0)


# --- 2. the last step, alone (167-172) ---------------------------------------------------------------------------------------

LEDGE_X = 980          # the rock step: low ground to the left, the summit to the right
LOW_Y = 920
TOP_Y = 790


def ground_last(x):
    return LOW_Y if x < LEDGE_X else TOP_Y


def step_up_pose(T, keys, facing=1):
    """Keyframed climb: keys [(t, hip_x, hip_y, foot_f world, foot_b world, lean)]."""
    hip = Curve([(k[0], (k[1], k[2])) for k in keys])(T)
    ff = Curve([(k[0], k[3]) for k in keys])(T)
    fb = Curve([(k[0], k[4]) for k in keys])(T)
    lean = Curve([(k[0], k[5]) for k in keys])(T)
    p = dict(x=hip[0], y=hip[1], facing=facing, scale=1.0, lean=lean, ikl_f=-1.0, ikl_b=-1.0)
    p['foot_f'] = to_local(p, (ff[0], ff[1] - 9))
    p['foot_b'] = to_local(p, (fb[0], fb[1] - 9))
    return p


L0 = EV['last_step']
SLIP, PUSH2, UP = EV['slip'], EV['push2'], EV['on_top']
# He gathers himself at the foot of the step and pushes up; his foot slips off the edge and he drops back, bent
# over, breathing. He gathers himself again and this time he makes it. The feet stay put from the moment each one
# lands; only the hips travel.
HERO_CLIMB = [
    (L0 + 0.0, 880, LOW_Y - 120.5, (883, LOW_Y), (877, LOW_Y), 6),
    (L0 + 0.4, 884, LOW_Y - 106, (883, LOW_Y), (877, LOW_Y), 18),
    (SLIP - 0.05, 930, LOW_Y - 140, (1000, TOP_Y), (877, LOW_Y), 30),
    (SLIP + 0.3, 912, LOW_Y - 124, (968, LOW_Y - 30), (877, LOW_Y), 26),
    (SLIP + 0.7, 884, LOW_Y - 110, (900, LOW_Y), (877, LOW_Y), 30),
    (PUSH2 - 0.7, 882, LOW_Y - 112, (900, LOW_Y), (877, LOW_Y), 28),
    (PUSH2 - 0.3, 886, LOW_Y - 104, (900, LOW_Y), (877, LOW_Y), 16),
    (PUSH2 + 0.15, 930, LOW_Y - 140, (1000, TOP_Y), (877, LOW_Y), 30),
    (PUSH2 + 0.55, 996, TOP_Y - 100, (1000, TOP_Y), (950, LOW_Y - 46), 22),
    (PUSH2 + 0.85, 1026, TOP_Y - 104, (1000, TOP_Y), (1036, TOP_Y), 10),
    (UP, 1032, TOP_Y - 120, (1028, TOP_Y), (1036, TOP_Y), 4),
]


def hero_last(T):
    p = step_up_pose(T, HERO_CLIMB)
    p.update(facing=1)
    # a hand on the edge of the rock as he pushes
    grab = smooth(SLIP - 0.4, SLIP - 0.15, T) * (1 - smooth(SLIP + 0.05, SLIP + 0.3, T))
    grab = max(grab, smooth(PUSH2 - 0.15, PUSH2 + 0.1, T) * (1 - smooth(PUSH2 + 0.5, PUSH2 + 0.8, T)))
    if grab > 0:
        rest = to_world(p, (30, 20))
        edge = (994.0, TOP_Y - 4.0)
        p['hand_f'] = to_local(p, (rest[0] + (edge[0] - rest[0]) * grab, rest[1] + (edge[1] - rest[1]) * grab))
        p['ik_f'] = 1.0
    # bent over, breathing hard, between the two tries
    pant = smooth(SLIP + 0.5, SLIP + 0.8, T) * (1 - smooth(PUSH2 - 0.4, PUSH2 - 0.2, T))
    p['breathe'] = breath(T, 0.9, 1.0, 1) * (0.4 + 0.6 * pant)
    p['y'] += 3 * math.sin(T * 9.0) * pant
    return p


def last_step(c, t, T):
    cx, cy, z, _ = cam_last(t)
    dawn = 0.55 + 0.3 * smooth(L0, L0 + 5, T)
    grad(c, (cx - 2400, cy - 1400, cx + 2400, cy + 700),
         [(0.0, hexmix('#05070F', '#141C44', dawn)), (0.55, hexmix('#0E1630', '#3B3A78', dawn)),
          (0.85, hexmix('#1B2647', '#C0647A', dawn)), (1.0, hexmix('#1B2647', '#FFA86A', dawn))])
    stars(c, T, cx - 1400, cy - 900, cx + 1400, cy - 100, n=120, seed=8, a=1 - 0.8 * dawn)
    cloud_sea(c, T, 980, 0.25 * dawn, cam_x=cx, rows=3)
    # the rock: low ground, the step, the summit
    rock = skia.Path()
    rock.moveTo(-600, 1600)
    rock.lineTo(-600, LOW_Y)
    rock.lineTo(LEDGE_X - 6, LOW_Y)
    rock.lineTo(LEDGE_X - 18, TOP_Y + 40)
    rock.lineTo(LEDGE_X, TOP_Y)
    rock.lineTo(2600, TOP_Y - 10)
    rock.lineTo(2600, 1600)
    rock.close()
    c.drawPath(rock, paint(hexmix('#141826', '#2E2434', dawn)))
    c.drawPath(rock, paint(hexmix('#2A3350', '#E8946A', dawn), 0.9, stroke=6))
    # a few stones knocked loose when his foot slips
    for k in range(3):
        u = (T - SLIP - 0.05 - 0.06 * k) / 0.5
        if 0 < u < 1:
            c.drawCircle(990 - 10 * k - 20 * u, TOP_Y + 6 + (LOW_Y - TOP_Y - 10) * u * u, 5 - k,
                         paint(hexmix('#3A3346', '#8A6A62', dawn)))
    ph = hero_last(T)
    effort = smooth(SLIP - 0.3, SLIP, T) * (1 - smooth(UP - 0.2, UP + 0.3, T))
    ph.update(turn=0.3, eye=blink(T, 1, 3.4) * (1 - 0.25 * effort), mopen=0.0,
              smile=0.2 - 0.5 * effort + 0.4 * smooth(UP, UP + 0.6, T), brow=-10 * effort,
              sweat=0.8 * effort, ly=-0.5 * smooth(UP + 0.2, UP + 0.6, T))
    jh = HIKER.draw(c, ph, layers={'behind': strap_layer(), 'over_head': headband_lamp}, t=T)
    lamp_a = 1 - smooth(EV['sunrise'] - 1.0, EV['sunrise'], T)
    headlamp(c, ph, jh, T, a=lamp_a, reach=380)


def cam_last(t):
    T = L0 + t
    return (960 + 20 * smooth(0, 5, t), 690 - 10 * smooth(0, 5, t), 1.45, 0.0)


# --- 3. the sunrise (172-183) -----------------------------------------------------------------------------------------

def sun_amount(T):
    return smooth(EV['sun_breaks'] - 0.4, EV['sun_breaks'] + 3.5, T)


SUN_X = 1640


def sun_y(T):
    return 860 - 300 * smooth(EV['sun_breaks'] - 0.6, 189.0, T)


def summit_scene(c, T, cx, cy, *, people=True, fade_old=None, give=None, shoulder=0.0, hero_face=None,
                 old_face_kw=None, old_alpha=1.0):
    sun = sun_amount(T)
    summit_sky(c, T, sun, cx, cy)
    sy = sun_y(T)
    sun_disc(c, SUN_X, sy, 48, a=smooth(EV['sun_breaks'] - 0.6, EV['sun_breaks'], T), bloom=0.6 + 0.6 * sun)
    if sun > 0:
        light_rays(c, SUN_X, sy, T, n=18, length=2400, a=0.07 * sun, color='#FFE2A8', spin=0.02, width=0.06)
    cloud_sea(c, T, 880, sun, cam_x=cx, rows=4)
    summit_rock(c, sun)
    flash = math.exp(-max(0.0, T - EV['sun_breaks']) / 0.6) * (T >= EV['sun_breaks'])
    if people:
        draw_pair(c, T, sun, fade_old=fade_old, give=give, shoulder=shoulder, hero_face=hero_face,
                  old_face_kw=old_face_kw, old_alpha=old_alpha)
    if flash > 0.01:
        c.drawRect(skia.Rect.MakeLTRB(cx - 2600, cy - 1600, cx + 2600, cy + 1600), paint('#FFF1D0', 0.45 * flash))
    return sun


HX, OX = 900, 1130       # the boy, facing the sunrise; the old man waiting for him at the edge, in the light


def ox(T):
    """Where the old man stands: he steps closer to the boy as he gives him the watch."""
    return OX - 70 * smooth(EV['watch_give'][0] + 0.2, EV['watch_give'][1] - 0.2, T)


def pair_poses(T, give=None, shoulder=0.0, hero_face=None, old_face_kw=None):
    from engine.motion import sway
    v = vitality(T)
    look_o = smooth(EV['look_proud'], EV['look_proud'] + 0.6, T)
    awe = smooth(EV['sun_breaks'], EV['sun_breaks'] + 0.5, T) * (1 - smooth(EV['sees'] - 0.2, EV['sees'] + 0.4, T))
    seen = smooth(EV['sees'], EV['sees'] + 0.3, T)
    wonder = seen * (1 - smooth(EV['sees'] + 0.9, EV['sees'] + 1.6, T))
    ph = stand_feet(HX, SUMMIT_Y, 1.0, 1)
    ph.update(turn=0.3, eye=blink(T, 1, 3.6) * (1 - 0.45 * awe) * (1 - 0.3 * wonder) + 0.3 * wonder,
              smile=0.35 - 0.3 * wonder + 0.15 * seen, ly=-0.3 * (1 - seen), lx=0.4 + 0.5 * seen,
              brow=-8 * wonder, breathe=breath(T, 0.3, 0.9, 1))
    for k, val in sway(T, 1.0, 3).items():
        ph[k] = ph.get(k, 0.0) + val
    ph['lean'] = ph.get('lean', 0.0) - 5 * awe
    if awe > 0:
        # a hand up against the light
        ph['hand_f'] = (34 + 10 * awe, -140 - 40 * awe)
        ph['ik_f'] = 1.0
        ph['ef'] = 90
    if hero_face:
        ph.update(hero_face)
    # the old man faces him: he has been waiting up here
    po = stand_feet(ox(T), SUMMIT_Y, 1.0, -1)
    po.update(old_face(v, T))
    for k, val in sway(T + 4.0, 0.8, 9).items():
        po[k] = po.get(k, 0.0) + val
    po.update(turn=0.3, smile=0.5 + 0.2 * look_o, eye=0.95 * blink(T, 2, 3.8), ly=0.05, lx=0.7,
              wet=look_o * 0.8, tilt=4 * look_o)
    if old_face_kw:
        po.update(old_face_kw)
    if shoulder > 0:
        sh = to_world(ph, (18, -(100 - 16)))
        rest = to_world(po, (10, 30))
        target = (rest[0] + (sh[0] + 4 - rest[0]) * shoulder, rest[1] + (sh[1] - 6 - rest[1]) * shoulder)
        po['hand_f'] = to_local(po, target)
        po['ik_f'] = 1.0
    return ph, po, v


def sunlit(c, fn, x, sun):
    """Draw a figure with the sunrise on it: warm on the side facing the sun, cool and dim on the other."""
    c.saveLayer(None, None)
    fn(c)
    sh = skia.GradientShader.MakeLinear(points=[(x - 110, 0), (x + 110, 0)],
                                        colors=[skia.Color(42, 34, 80, int(255 * (0.34 - 0.12 * sun))),
                                                skia.Color(255, 176, 112, int(255 * (0.06 + 0.26 * sun)))])
    p = skia.Paint(Shader=sh)
    p.setBlendMode(skia.BlendMode.kSrcATop)
    c.drawRect(skia.Rect.MakeLTRB(x - 400, -2000, x + 400, 3000), p)
    c.restore()


def draw_pair(c, T, sun, fade_old=None, give=None, shoulder=0.0, hero_face=None, old_face_kw=None, old_alpha=1.0):
    ph, po, v = pair_poses(T, give, shoulder, hero_face, old_face_kw)
    rim_a = 0.35 + 0.55 * sun
    hero_gear = {'behind': strap_layer(), 'over_head': headband_lamp}

    def old_draw(cc):
        # no pack, no lamp, no stick: he did not climb, he was waiting
        sunlit(cc, lambda c2: old_man(v).draw(c2, dict(po, alpha=old_alpha), t=T), ox(T), sun)

    sunlit(c, lambda cc: HIKER.draw(cc, ph, layers=hero_gear, t=T), HX, sun)
    _sun_rim(c, lambda cc: HIKER.draw(cc, ph, layers=hero_gear, t=T), rim_a)
    form = smooth(EV['appear'], EV['appear'] + 1.1, T)
    if form <= 0:
        return
    if form < 1:
        # he takes shape out of the sunlight
        gather_motes(c, T, EV['appear'], 1.1)
        c.saveLayerAlpha(None, int(255 * form))
        old_draw(c)
        glow = paint('#FFEBC2', (1 - form) ** 1.5)
        glow.setBlendMode(skia.BlendMode.kSrcATop)
        c.drawRect(skia.Rect.MakeLTRB(OX - 200, SUMMIT_Y - 400, OX + 200, SUMMIT_Y + 40), glow)
        c.restore()
        c.drawCircle(OX, SUMMIT_Y - 150, 170, paint('#FFE2A8', 0.5 * (1 - form), blur=60, blend='add'))
    elif fade_old is None:
        old_draw(c)
        _sun_rim(c, old_draw, rim_a)
    else:
        x = ox(T)
        dissolve(c, old_draw, (x - 120, SUMMIT_Y - 330, x + 120, SUMMIT_Y + 10), T, fade_old, dur=4.0, seed=17,
                 smoke='#FFD49A', smoke_a=0.6, grey=0.0, rise=320, embers='#FFF1C9', n=60, drift=70)
        golden_motes(c, T, fade_old)


def gather_motes(c, T, t0, dur, n=46, seed=29):
    """Specks of sunlight drawn together into the shape of a man."""
    for i in range(n):
        delay = hrand(i, seed) * dur * 0.5
        u = (T - t0 - delay) / (dur * 0.8)
        if u <= 0 or u >= 1:
            continue
        ang = hrange(0, math.tau, i, seed, 1)
        r0 = hrange(160, 380, i, seed, 2)
        e = u ** 1.7
        tx, ty = OX + hrange(-40, 40, i, seed, 3), SUMMIT_Y - hrange(30, 290, i, seed, 4)
        x = tx + math.cos(ang) * r0 * (1 - e)
        y = ty + math.sin(ang) * r0 * 0.7 * (1 - e)
        a = math.sin(math.pi * u) * 0.9
        r = hrange(2.5, 5.0, i, seed, 5)
        c.drawCircle(x, y, r * 3, paint('#FFD49A', 0.35 * a, blur=6, blend='add'))
        c.drawCircle(x, y, r, paint('#FFF6DD', a, blend='add'))


def _sun_rim(c, fn, a):
    from engine.light import rim
    rim(c, fn, 4, -2, '#FFC98A', a, blur=1.5)


def golden_motes(c, T, t0, n=70, seed=23):
    """Sparks drifting up out of him and away toward the sun."""
    for i in range(n):
        born = t0 + 3.6 * hrand(i, seed)
        age = T - born
        if age < 0 or age > 3.2:
            continue
        u = age / 3.2
        x0 = ox(t0) + hrange(-60, 60, i, seed, 1)
        y0 = SUMMIT_Y - 40 - hrange(0, 260, i, seed, 2) * min(1.0, (born - t0) / 3.6 + 0.2)
        x = x0 + (SUN_X - x0) * (u ** 1.6) * 0.75 + 30 * noise1(age * 1.3 + i, seed)
        y = y0 - 220 * u + 20 * noise1(age + i, seed + 3)
        a = math.sin(math.pi * min(1.0, u * 1.2)) * 0.9
        r = hrange(2.5, 5.5, i, seed, 4)
        c.drawCircle(x, y, r * 3, paint('#FFD49A', 0.35 * a, blur=6, blend='add'))
        c.drawCircle(x, y, r, paint('#FFF6DD', a, blend='add'))


def sunrise_wide(c, t, T):
    cx, cy, z, _ = cam_sunrise_wide(t)
    summit_scene(c, T, cx, cy)


cam_sunrise_wide = CamPath([(0.0, (1000, 600, 1.35)), (3.4, (1060, 560, 1.12))], handheld=3, seed=101)


def sunrise_two(c, t, T):
    cx, cy, z, _ = cam_sunrise_two(t)
    summit_scene(c, T, cx, cy, hero_face=dict(lx=0.9, ly=0.0, smile=0.3 + 0.2 * smooth(176.4, 177.0, T),
                                              wet=0.5 * smooth(175.6, 176.6, T)))


cam_sunrise_two = CamPath([(0.0, (990, 560, 2.1)), (1.6, (994, 556, 2.2))], handheld=3, seed=102)


def finger(c, x, y, ang, length, width, color):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    f = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-width / 2, -width / 2, length + width / 2, width), width / 2, width / 2)
    c.drawRRect(f, paint(color))
    c.drawRRect(f, paint('outline', stroke=7))
    c.restore()


def hands_insert(c, t, T):
    """The old hand (from the right, where he stands) lowers the watch on its chain into the boy's open palm,
    lets go, and folds the boy's fingers over it. Drawn mirrored; the watch itself is not."""
    c.save()
    c.translate(W, 0)
    c.scale(-1, 1)
    grad(c, (-200, -200, W + 200, H + 200), [(0.0, '#F7C08A'), (1.0, '#E07A5A')])
    c.drawCircle(1500, 160, 460, paint('#FFF1C9', 0.45, blur=170, blend='add'))
    t0, t1 = EV['watch_give']
    lower = smooth(t0 + 0.1, t0 + 1.2, T)
    let_go = smooth(t0 + 1.2, t0 + 1.5, T)
    close = smooth(t0 + 1.5, t1 + 0.2, T)
    young = '#EDE6D9'
    old = old_man(vitality(T)).look.skin
    # the boy's hand, palm up, from the right
    c.drawPath(poly([(W + 300, 980), (1440, 760), (1400, 900), (W + 300, 1200)], True), paint('#36586C'))
    c.drawPath(poly([(W + 300, 980), (1440, 760), (1400, 900), (W + 300, 1200)], True), paint('outline', stroke=8))
    finger(c, 1260, 700, 200 - 40 * close, 120, 56, young)                # thumb
    c.drawOval(oval(1180, 800, 240, 130), paint(young))
    c.drawOval(oval(1180, 800, 240, 130), paint('outline', stroke=8))
    c.drawOval(oval(1170, 790, 150, 70), paint('#000000', 0.06))
    # the watch, swinging on its chain from the old fingers, then resting in the palm
    hold = (720 + 330 * lower, 260 + 230 * lower)
    sw = math.radians(14 * math.sin(T * 3.2) * (1 - lower * 0.8))
    chain = 210 - 40 * lower
    wx = hold[0] + math.sin(sw) * chain
    wy = hold[1] + math.cos(sw) * chain
    if let_go > 0:
        wx, wy = wx + (1150 - wx) * let_go, wy + (770 - wy) * let_go
    anchor = (hold[0], hold[1]) if let_go < 0.5 else (1000, 700)
    c.save()
    c.translate(wx, wy)
    c.scale(-1, 1)
    c.translate(-wx, -wy)
    pocket_watch(c, wx, wy, 100, T, open_lid=False, glow=0.35, chain=(2 * wx - anchor[0], anchor[1]))
    c.restore()
    # the boy's four fingers curl over the watch
    for k in range(4):
        finger(c, 1000 - 10 * k, 760 + 34 * k, 180 + (150 - 12 * k) * close * 1.0 - 10, 150 - 14 * k, 54, young)
    # the old hand from the left: a fist holding the chain, then open over the boy's fingers
    ox = hold[0] - 90 + 140 * close
    oy = hold[1] - 40 + 200 * close
    c.drawPath(poly([(ox - 60, oy - 40), (-300, oy - 300), (-300, oy + 80), (ox - 40, oy + 90)], True), paint('#4E6170'))
    c.drawPath(poly([(ox - 60, oy - 40), (-300, oy - 300), (-300, oy + 80), (ox - 40, oy + 90)], True),
               paint('outline', stroke=8))
    c.drawOval(oval(ox, oy + 20, 120, 100), paint(old))
    c.drawOval(oval(ox, oy + 20, 120, 100), paint('outline', stroke=8))
    open_ = max(let_go, close)
    for k in range(4):
        finger(c, ox + 70, oy - 20 + 26 * k, 90 - 80 * open_ + 6 * k, 70 + 40 * open_, 44, old)
    for k in range(3):
        c.drawLine(ox - 30 + 24 * k, oy - 10, ox - 20 + 24 * k, oy + 40, paint('outline', 0.25, stroke=3))
    c.restore()


def cam_hands(t):
    return (W / 2, H / 2, 1.0 + 0.04 * smooth(0, 2.6, t), 0.0)


def sunrise_shoulder(c, t, T):
    cx, cy, z, _ = cam_shoulder(t)
    sh = smooth(EV['shoulder'][0], EV['shoulder'][0] + 0.6, T)
    summit_scene(c, T, cx, cy, shoulder=sh,
                 hero_face=dict(lx=0.9, ly=-0.1, smile=0.4, wet=0.6),
                 old_face_kw=dict(lx=1.0, eyes='happy' if T > EV['shoulder'][0] + 0.8 else 'dot'))


cam_shoulder = CamPath([(0.0, (990, 560, 2.0)), (3.4, (996, 556, 2.1))], handheld=3, seed=103)


# --- 4. into the light (183-189) ------------------------------------------------------------------------------------

def fade_shot(c, t, T):
    cx, cy, z, _ = cam_fade(t)
    t0 = EV['fade'][0]
    sh = 1 - smooth(t0 + 1.4, t0 + 2.2, T)
    summit_scene(c, T, cx, cy, fade_old=t0 + 0.8, shoulder=sh,
                 hero_face=dict(lx=0.9, ly=-0.1, smile=0.3, wet=0.8, tears=0.5 * smooth(t0 + 2.0, t0 + 3.6, T)),
                 old_face_kw=dict(lx=0.9, eyes='happy', smile=0.75))


cam_fade = CamPath([(0.0, (996, 560, 1.75)), (6.0, (1060, 520, 1.45))], handheld=3, seed=104)


def alone(c, t, T):
    cx, cy, z, _ = cam_alone(t)
    sun = sun_amount(T)
    summit_sky(c, T, sun, cx, cy)
    sy = sun_y(T)
    sun_disc(c, SUN_X, sy, 48, a=1.0, bloom=1.2)
    light_rays(c, SUN_X, sy, T, n=18, length=2600, a=0.07, color='#FFE2A8', spin=0.02, width=0.06)
    cloud_sea(c, T, 880, sun, cam_x=cx, rows=4)
    summit_rock(c, sun)
    golden_motes(c, T, EV['fade'][0] + 0.8)
    look = smooth(190.0, 190.6, T) * (1 - smooth(191.6, 192.2, T))
    ph = stand_feet(HX, SUMMIT_Y, 1.0, 1)
    ph.update(turn=0.3, eye=blink(T, 1, 3.6), smile=0.45, ly=-0.3 + 0.9 * look, lx=0.4, tilt=14 * look,
              hand_f=(30, -30 + 10 * look), ik_f=1.0, breathe=breath(T, 0.3, 0.9, 1))
    gear = {'behind': strap_layer(), 'over_head': headband_lamp}
    holder = {}

    def me(cc):
        holder['j'] = HIKER.draw(cc, ph, layers=gear, t=T)
    sunlit(c, me, HX, sun)
    j = holder['j']
    hand = to_world(ph, j['hand_f'])
    pocket_watch(c, hand[0] + 6, hand[1] - 14, 12, T, open_lid=False, detail=False, glow=0.6)
    from engine.light import rim
    rim(c, lambda cc: HIKER.draw(cc, ph, layers=gear, t=T), 4, -2, '#FFC98A', 0.9, blur=1.5)


cam_alone = CamPath([(0.0, (980, 600, 1.5)), (4.0, (1080, 520, 0.98))], handheld=3, seed=105)


# --- 5. 2:47 AM again (193-203) -------------------------------------------------------------------------------------

def epilogue(c, t, T):
    def hero(cc, TT, rim_pass=False):
        p = lying_pose(TT, phone=False, face=dict(eyes='closed', smile=0.25, brow=2, bags=0.0), swipes=[])
        p['rot'] = -78
        p['back_arm_late'] = True
        p['hand_f'] = to_local(p, (760, 800))
        p['ik_f'] = 1.0
        p['breathe'] = breath(TT, 0.18, 1.0, 1)
        quilt = in_world(cc, lambda c2: blanket(c2, p['x'] - 140, [(p['x'] - 140, p['y'] - 44), (p['x'] - 40, p['y'] - 46),
                                                                    (p['x'] + 60, p['y'] - 36), (p['x'] + 160, MATT - 30),
                                                                    (p['x'] + 210, MATT - 8)]))
        HERO.draw(cc, p, layers={'mid': quilt}, t=TT)
        return p

    R = Room(light='night', sky='night', curtain=0.86, hero=hero, old=None, stand_watch=True, stand_phone=None,
             moon=1.1, ambient='#2A3150')
    R.lights_extra = lambda cc: _watch_glint(cc, T)
    draw_room(c, T, R)
    # the watch on the nightstand ticks in the moonlight
    pocket_watch(c, 500, 774, 13, T, open_lid=False, detail=False, glow=0.5, crack=False)


def _watch_glint(c, T):
    from engine.light import pool
    pool(c, 500, 774, 120, 90, '#C9D6FF', 0.5)
    pool(c, 650, 730, 210, 170, '#9DB7FF', 0.55)


cam_epilogue = CamPath([(0.0, (606, 690, 3.0)), (2.0, (614, 694, 2.9)), (5.0, (880, 700, 1.5)),
                        (10.0, (1020, 700, 1.62))], handheld=4, seed=111)


# --- 6. the title card (203-212) --------------------------------------------------------------------------------------

def title_card(c, t, T):
    c.drawPaint(paint('#040406'))
    ghost = 0.28 * smooth(203.4, 205.0, T)
    if ghost > 0:
        c.save()
        p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(10, 10))
        p.setAlphaf(ghost)
        c.saveLayer(None, p)
        c.translate(W / 2, H / 2)
        c.scale(1.0, 1.0)
        c.translate(-1060, -540)
        summit_sky(c, T, 1.0, 1060, 540)
        sun_disc(c, SUN_X, sun_y(T), 48, 1.0, 1.0)
        cloud_sea(c, T, 880, 1.0, cam_x=1060, rows=4)
        summit_rock(c, 1.0)
        c.restore()
        c.restore()
    t0 = EV['title_card']
    title(c, T, 'HE’S WAITING.', t0 + 0.4, 211.6, 600, size=130, underline=t0 + 1.2, ul_color='#D6A23D')
    a = smooth(t0 + 0.8, t0 + 1.8, T) * (1 - smooth(210.8, 211.6, T))
    pocket_watch(c, W / 2, 360, 74, T, open_lid=False, a=a, glow=0.5)


# --- assemble -------------------------------------------------------------------------------------------------------------

def shots():
    return [
        Shot(EV['ascent'], EV['last_step'], ascent, cam_ascent, name='ascent'),
        Shot(EV['last_step'], EV['sunrise'], last_step, cam_last, name='last_step'),
        Shot(EV['sunrise'], EV['look_proud'], sunrise_wide, cam_sunrise_wide, name='sunrise_wide'),
        Shot(EV['look_proud'], EV['watch_give'][0], sunrise_two, cam_sunrise_two, name='sunrise_two'),
        Shot(EV['watch_give'][0], EV['watch_give'][1] + 0.6, hands_insert, cam_hands, name='hands'),
        Shot(EV['watch_give'][1] + 0.6, EV['fade'][0], sunrise_shoulder, cam_shoulder, name='shoulder'),
        Shot(EV['fade'][0], EV['alone'], fade_shot, cam_fade, name='fade'),
        Shot(EV['alone'], EV['epilogue'], alone, cam_alone, name='alone'),
        Shot(EV['epilogue'], EV['title_card'], epilogue, cam_epilogue, name='epilogue'),
        Shot(EV['title_card'], 212.0, title_card, None, name='title_card'),
    ]
