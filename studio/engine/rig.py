"""Rigged round-head character in the flat 2-D house style.

Local frame: origin at the pelvis, +x is the direction the character faces,
+y is down. Limb angles are measured from straight down, positive toward the
facing direction (90 = pointing forward, 180 = straight up). Knees bend back.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import skia

from .core import hrand, noise1, smooth
from .draw import OUTLINE_W, circle, col, limb, oval, paint, poly, smooth_path, text

BASE_POSE = dict(
    x=0.0, y=0.0, facing=1, scale=1.0, alpha=1.0,
    lean=0.0, tilt=0.0, head_dx=0.0, head_dy=0.0, breathe=0.0,
    sb=10.0, eb=14.0, sf=-8.0, ef=16.0,
    hb=-5.0, kb=2.0, hf=5.0, kf=2.0,
    turn=0.35, eye=1.0, lx=0.0, ly=0.0, brow=0.0, brow_y=0.0,
    smile=0.15, mopen=0.0, mwide=1.0, eyes='dot', mouth='curve',
    sweat=0.0, tears=0.0, blush=0.0, bags=0.0, shiver=0.0,
)


@dataclass(frozen=True)
class Look:
    skin: str = 'skin'
    outline: str = 'outline'
    top: str = 'hoodie'
    sleeves: str | None = None        # defaults to the top colour
    pants: str = 'pants'
    shoes: str = 'shoes'
    hood: bool = True
    pocket: bool = True
    tie: str | None = None
    hat: str | None = None            # 'beanie'
    hat_color: str = 'beanie'
    hair: str | None = None           # 'short' | 'long' | 'bun' | 'spiky'
    hair_color: str = '#3A2E28'
    mustache: str | None = None       # colour of a moustache, if any
    beard: str | None = None          # colour of a full beard, if any
    headband: str | None = None       # colour of a sweatband, if any
    brow_color: str | None = None     # eyebrows (default: the outline colour), e.g. white for an old man
    sleeve: str = 'long'              # 'long', 'short' (t-shirt) or 'none' (vest): bare skin below the sleeve
    shorts: str | None = None         # colour of shorts; the lower legs are then bare
    print_text: str | None = None     # a slogan printed on the chest
    print_color: str = '#2B2416'
    head_r: float = 62.0
    torso: float = 100.0
    upper_arm: float = 54.0
    forearm: float = 50.0
    thigh: float = 58.0
    shin: float = 56.0
    arm_w: float = 15.0
    leg_w: float = 18.0
    shoulder_w: float = 76.0
    hip_w: float = 64.0
    shadow: bool = False              # black silhouette with red rim and red eyes
    rim: str = 'red'
    rim_a: float = 0.85


HERO = Look()
SHADOW = Look(shadow=True, hood=False, pocket=False)


def _dir(deg):
    a = math.radians(deg)
    return math.sin(a), math.cos(a)


def _add(p, d, s=1.0):
    return p[0] + d[0] * s, p[1] + d[1] * s


def two_bone(base, target, l1, l2, bend=1.0):
    dx, dy = target[0] - base[0], target[1] - base[1]
    d = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 1e-3, min(l1 + l2 - 1e-3, d))
    ang = math.atan2(dy, dx)
    cos_a = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    m_ang = ang + bend * a
    mid = (base[0] + l1 * math.cos(m_ang), base[1] + l1 * math.sin(m_ang))
    ex, ey = target[0] - mid[0], target[1] - mid[1]
    el = math.hypot(ex, ey) or 1.0
    return mid, (mid[0] + l2 * ex / el, mid[1] + l2 * ey / el)


def blink(t, seed=0, every=3.6):
    """Eye-openness multiplier with an occasional quick blink."""
    k = math.floor(t / every)
    start = k * every + hrand(k, seed) * (every - 0.4)
    dt = t - start
    if 0 <= dt < 0.16:
        return abs(dt - 0.08) / 0.08
    return 1.0


def solve(look: Look, pose: dict):
    """Joint positions in the local frame."""
    L = look
    br = pose.get('breathe', 0.0)
    torso = L.torso * (1 + 0.025 * br)
    lean = pose['lean']
    spine = _dir(180 - lean)  # unit vector up the body; + lean tips the top toward +x
    hip = (0.0, 0.0)
    neck = _add(hip, spine, torso)
    # unit vector toward the chest (the facing side), rotated with the torso
    perp = (math.cos(math.radians(lean)), math.sin(math.radians(lean)))
    sh = _add(hip, spine, torso - 16)
    sh_b = _add(sh, perp, -L.shoulder_w * 0.3)
    sh_f = _add(sh, perp, L.shoulder_w * 0.3)
    head_dir = _dir(180 - lean - pose['tilt'])
    head = _add(neck, head_dir, L.head_r * 0.9)
    head = (head[0] + pose['head_dx'], head[1] + pose['head_dy'])
    j = dict(hip=hip, neck=neck, sh_b=sh_b, sh_f=sh_f, head=head,
             head_angle=pose['lean'] + pose['tilt'], spine=spine, perp=perp)

    for side, s0 in (('b', sh_b), ('f', sh_f)):
        tgt = pose.get(f'hand_{side}')
        if tgt is not None:
            el, hand = two_bone(s0, tgt, L.upper_arm, L.forearm, bend=pose.get(f'ik_{side}', 1.0))
        else:
            el = _add(s0, _dir(pose[f's{side}']), L.upper_arm)
            hand = _add(el, _dir(pose[f's{side}'] + pose[f'e{side}']), L.forearm)
        j[f'el_{side}'] = el
        j[f'hand_{side}'] = hand

    for side, off in (('b', -L.hip_w * 0.22), ('f', L.hip_w * 0.22)):
        h0 = _add(hip, perp, off)
        tgt = pose.get(f'foot_{side}')
        if tgt is not None:
            kn, ft = two_bone(h0, tgt, L.thigh, L.shin, bend=pose.get(f'ikl_{side}', -1.0))
        else:
            kn = _add(h0, _dir(pose[f'h{side}']), L.thigh)
            ft = _add(kn, _dir(pose[f'h{side}'] - pose[f'k{side}']), L.shin)
        j[f'hj_{side}'] = h0
        j[f'kn_{side}'] = kn
        j[f'ft_{side}'] = ft
    return j


class Character:
    def __init__(self, look: Look = HERO, seed=0):
        self.look = look
        self.seed = seed

    def with_look(self, **kw):
        return Character(replace(self.look, **kw), self.seed)

    # -- public -------------------------------------------------------------
    def draw(self, c, pose_in: dict, layers=None, t=0.0):
        """Draw at pose. layers: optional callbacks keyed by
        'behind', 'mid' (after legs/torso, before head and front arm), 'front', 'over_head'.
        Each is called as fn(canvas, joints) inside the character's local frame."""
        pose = dict(BASE_POSE)
        pose.update(pose_in)
        if pose.get('shiver'):
            pose['x'] += noise1(t * 30, self.seed) * pose['shiver'] * 2.5
        layers = layers or {}
        L = self.look
        j = solve(L, pose)
        alpha = pose.get('alpha', 1.0)
        if alpha <= 0:
            return j
        c.save()
        c.translate(pose['x'], pose['y'])
        if pose.get('rot'):
            c.rotate(pose['rot'])
        s = pose['scale']
        c.scale(s * pose['facing'], s)
        self._facing = pose['facing']
        self._pose = pose
        if alpha < 1:
            c.saveLayerAlpha(None, int(alpha * 255))
        if 'behind' in layers:
            layers['behind'](c, j)
        if L.shadow:
            self._draw_shadow(c, pose, j, layers, t)
        else:
            self._draw_body(c, pose, j, layers)
        if alpha < 1:
            c.restore()
        c.restore()
        return j

    # -- drawing --------------------------------------------------------------
    def _arm(self, c, j, side, top=None):
        L = self.look
        sleeve = L.sleeves or L.top
        sh, el, hand = j[f'sh_{side}'], j[f'el_{side}'], j[f'hand_{side}']
        if L.sleeve == 'long':
            limb(c, [sh, el, hand], sleeve, L.arm_w, L.outline)
        else:
            limb(c, [sh, el, hand], L.skin, L.arm_w * 0.9, L.outline)
            if L.sleeve == 'short':
                cuff = (sh[0] + (el[0] - sh[0]) * 0.6, sh[1] + (el[1] - sh[1]) * 0.6)
                limb(c, [sh, cuff], sleeve, L.arm_w + 6, L.outline)
        if not getattr(self, '_pose', {}).get(f'no_hand_{side}'):
            self._hand(c, hand)

    def arm(self, c, j, side='f'):
        """Draw just one arm (in the character's local frame), e.g. from a layer with an effect applied."""
        self._arm(c, j, side)

    def _hand(self, c, p):
        circle(c, p[0], p[1], 10.5, self.look.skin, self.look.outline, 4.5)

    def _leg(self, c, j, side):
        L = self.look
        hj, kn = j[f'hj_{side}'], j[f'kn_{side}']
        if L.shorts:
            limb(c, [hj, kn, j[f'ft_{side}']], L.skin, L.leg_w * 0.82, L.outline)
            hem = (hj[0] + (kn[0] - hj[0]) * 0.86, hj[1] + (kn[1] - hj[1]) * 0.86)
            limb(c, [hj, hem], L.shorts, L.leg_w + 9, L.outline)
        else:
            limb(c, [hj, kn, j[f'ft_{side}']], L.pants, L.leg_w, L.outline)
        fx, fy = j[f'ft_{side}']
        knee = j[f'kn_{side}']
        # foot points forward; tilt slightly along the shin when the leg is raised
        ang = math.degrees(math.atan2(fy - knee[1], fx - knee[0])) - 90
        ang = max(-35, min(35, ang * 0.35))
        c.save()
        c.translate(fx, fy)
        c.rotate(ang)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-10, -7, 22, 9), 9, 9)
        c.drawRRect(r, paint(L.shoes))
        c.drawRRect(r, paint(L.outline, stroke=4.5))
        c.restore()

    def _torso_path(self, j):
        L = self.look
        hip, neck = j['hip'], j['neck']
        perp = j['perp']
        sw, hw = L.shoulder_w / 2, L.hip_w / 2
        top = _add(neck, j['spine'], -6)
        p1 = _add(top, perp, -sw)
        p2 = _add(top, perp, sw)
        p3 = _add(hip, perp, hw)
        p4 = _add(hip, perp, -hw)
        bot = _add(hip, j['spine'], -10)
        b3 = _add(bot, perp, hw * 0.95)
        b4 = _add(bot, perp, -hw * 0.95)
        path = skia.Path()
        path.moveTo(*_add(top, perp, -sw * 0.55))
        path.quadTo(*p1, *_add(p1, j['spine'], -22))
        path.lineTo(*_add(p4, j['spine'], 6))
        path.quadTo(*b4, *_add(bot, perp, 0))
        path.quadTo(*b3, *_add(p3, j['spine'], 6))
        path.lineTo(*_add(p2, j['spine'], -22))
        path.quadTo(*p2, *_add(top, perp, sw * 0.55))
        path.close()
        return path

    def _torso(self, c, j):
        L = self.look
        path = self._torso_path(j)
        c.drawPath(path, paint(L.top))
        if L.pocket:
            mid = _add(j['hip'], j['spine'], 30)
            pk = poly([_add(_add(mid, j['perp'], -17), j['spine'], -8), _add(_add(mid, j['perp'], 17), j['spine'], -8)])
            c.drawPath(pk, paint(L.outline, 0.55, stroke=3.5))
        if L.print_text:
            # stacked words, set a little toward the back so the front arm doesn't cover them
            chest = _add(_add(j['hip'], j['spine'], L.torso * 0.6), j['perp'], -L.shoulder_w * 0.09)
            lean = math.degrees(math.atan2(j['spine'][0], -j['spine'][1]))
            lines = L.print_text.split('\n')
            size = L.shoulder_w * 0.23
            c.save()
            c.translate(*chest)
            c.rotate(lean)
            if getattr(self, '_facing', 1) < 0:
                c.scale(-1, 1)
            for k, line in enumerate(lines):
                y = (k - (len(lines) - 1) / 2) * size * 0.92 + size * 0.36
                text(c, line, 0, y, size, 'Fredoka-700', L.print_color)
            c.restore()
        if L.tie:
            n = _add(j['neck'], j['spine'], -10)
            tip = _add(n, j['spine'], -62)
            path_t = poly([_add(n, j['perp'], -6), _add(n, j['perp'], 6), _add(tip, j['perp'], 7),
                           _add(tip, j['spine'], -10), _add(tip, j['perp'], -7)], True)
            c.drawPath(path_t, paint(L.tie))
            c.drawPath(path_t, paint(L.outline, stroke=3))
        c.drawPath(path, paint(L.outline, stroke=OUTLINE_W))

    def _hood(self, c, j):
        L = self.look
        if not L.hood:
            return
        n = _add(j['neck'], j['spine'], -2)
        c.save()
        c.translate(*n)
        c.rotate(j['head_angle'])
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-38, -14, 30, 14), 14, 14)
        c.drawRRect(r, paint(L.top))
        c.drawRRect(r, paint(L.outline, stroke=OUTLINE_W))
        c.restore()

    def _body_parts(self, c, pose, j, layers):
        late = pose.get('back_arm_late')
        if not late:
            self._arm(c, j, 'b')
        self._leg(c, j, 'b')
        self._hood(c, j)
        self._torso(c, j)
        self._leg(c, j, 'f')
        if 'mid' in layers:
            layers['mid'](c, j)
        if late:
            # e.g. a strumming arm that crosses in front of a guitar
            self._arm(c, j, 'b')

    def _draw_body(self, c, pose, j, layers):
        self._body_parts(c, pose, j, layers)
        front_arm = not pose.get('no_arm_f')
        if pose.get('arm_over_head'):
            self._head(c, pose, j)
            if 'over_head' in layers:
                layers['over_head'](c, j)
            if front_arm:
                self._arm(c, j, 'f')
        else:
            if front_arm:
                self._arm(c, j, 'f')
            self._head(c, pose, j)
            if 'over_head' in layers:
                layers['over_head'](c, j)
        if 'front' in layers:
            layers['front'](c, j)

    def _draw_shadow(self, c, pose, j, layers, t):
        L = self.look
        rim = L.rim
        w_arm, w_leg = L.arm_w + 2 * OUTLINE_W, L.leg_w + 2 * OUTLINE_W
        glow = paint(rim, L.rim_a * 0.9, stroke=10, blur=7, blend='add')
        black = paint('#040405')
        hx, hy = j['head']
        R = L.head_r
        torso = self._torso_path(j)
        # rim glow pass
        for side in 'bf':
            c.drawPath(poly([j[f'sh_{side}'], j[f'el_{side}'], j[f'hand_{side}']]),
                       paint(rim, L.rim_a * 0.8, stroke=w_arm + 8, blur=7, blend='add'))
            c.drawPath(poly([j[f'hj_{side}'], j[f'kn_{side}'], j[f'ft_{side}']]),
                       paint(rim, L.rim_a * 0.8, stroke=w_leg + 8, blur=7, blend='add'))
        c.drawPath(torso, glow)
        c.drawCircle(hx, hy, R + 2, paint(rim, L.rim_a, stroke=9, blur=7, blend='add'))
        # solid silhouette
        for side in 'bf':
            c.drawPath(poly([j[f'sh_{side}'], j[f'el_{side}'], j[f'hand_{side}']]), paint('#040405', stroke=w_arm))
            c.drawCircle(*j[f'hand_{side}'], 12, black)
            c.drawPath(poly([j[f'hj_{side}'], j[f'kn_{side}'], j[f'ft_{side}']]), paint('#040405', stroke=w_leg))
            fx, fy = j[f'ft_{side}']
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(fx - 12, fy - 9, fx + 24, fy + 11), 10, 10), black)
        c.drawPath(torso, black)
        c.drawCircle(hx, hy, R + 1.5, black)
        if 'mid' in layers:
            layers['mid'](c, j)
        # glowing eyes
        c.save()
        c.translate(hx, hy)
        c.rotate(j['head_angle'])
        shadow_eyes(c, R, pose.get('eye', 1.0), pose.get('turn', 0.3), pose.get('brow', 18.0),
                    pose.get('lx', 0.0), pose.get('ly', 0.0), rim=L.rim)
        c.restore()
        if 'front' in layers:
            layers['front'](c, j)

    # -- head and face ---------------------------------------------------------------
    def _head(self, c, pose, j):
        L = self.look
        hx, hy = j['head']
        R = L.head_r
        c.save()
        c.translate(hx, hy)
        c.rotate(j['head_angle'])
        if L.hair in ('long',):
            hair_back(c, R, L.hair_color)
        circle(c, 0, 0, R, L.skin, L.outline, OUTLINE_W)
        if L.hair:
            hair_front(c, R, L.hair, L.hair_color, L.outline)
        if L.headband:
            headband(c, R, L.headband, L.outline)
        if not pose.get('back'):
            if L.beard:
                beard(c, R, pose, L.beard, L.outline)
            face(c, R, pose, L.outline, L.brow_color)
            if L.mustache:
                mustache(c, R, pose, L.mustache, L.outline)
        else:
            # back of the head: soft shading and the hood drooping over the nape
            c.save()
            clip = skia.Path()
            clip.addCircle(0, 0, R - 2)
            c.clipPath(clip, doAntiAlias=True)
            c.drawCircle(R * 0.35, R * 0.25, R * 0.95, paint('#000000', 0.10, blur=12))
            c.restore()
            if L.hood:
                hood = skia.Path()
                hood.moveTo(-R * 0.95, R * 0.45)
                hood.cubicTo(-R * 0.6, R * 1.25, R * 0.6, R * 1.25, R * 0.95, R * 0.45)
                hood.cubicTo(R * 0.4, R * 0.75, -R * 0.4, R * 0.75, -R * 0.95, R * 0.45)
                hood.close()
                c.drawPath(hood, paint(L.top))
                c.drawPath(hood, paint(L.outline, stroke=OUTLINE_W))
        if L.hat == 'beanie':
            beanie(c, R, L.hat_color, L.outline)
        if pose.get('brows_over_hat') and not pose.get('back'):
            brows(c, R, pose, L.outline, L.brow_color)
        c.restore()

    def draw_head(self, c, x, y, pose_in: dict, angle=0.0, scale=1.0, facing=1):
        """Just the head (e.g. resting on a pillow with the body under a blanket)."""
        pose = dict(BASE_POSE)
        pose.update(pose_in)
        c.save()
        c.translate(x, y)
        c.scale(scale * facing, scale)
        self._head(c, pose, dict(head=(0.0, 0.0), head_angle=angle))
        c.restore()


# --- face parts (head-local: centre (0,0), radius R, facing +x) ----------------------

def mustache(c, R, p, color, outline='outline'):
    """A bushy moustache just above the mouth, scalloped along the bottom, following the face turn."""
    fx = p.get('turn', 0.35) * R * 0.42
    mx, my = fx + R * 0.03, R * (0.25 + p.get('mouth_dy', 0.0)) + p.get('face_dy', 0.0) * R * 0.5
    w, h = R * 0.27, R * 0.1
    path = skia.Path()
    path.moveTo(mx - w, my + h * 0.7)
    path.cubicTo(mx - w * 0.8, my - h * 1.3, mx + w * 0.8, my - h * 1.3, mx + w, my + h * 0.7)
    n = 5
    for k in range(n):
        x0 = mx + w - 2 * w * k / n
        x1 = mx + w - 2 * w * (k + 1) / n
        path.quadTo((x0 + x1) / 2, my + h * 1.25, x1, my + h * 0.55)
    path.close()
    c.drawPath(path, paint(color))
    c.drawPath(path, paint(outline, stroke=3.5))


def beard(c, R, p, color, outline='outline'):
    """A full, rounded beard from temple to temple, hanging a little below the chin; the mouth sits on it."""
    fx = p.get('turn', 0.35) * R * 0.42
    dy = p.get('face_dy', 0.0) * R * 0.5
    path = skia.Path()
    path.moveTo(-R * 0.97, -R * 0.12)
    path.cubicTo(-R * 1.02, R * 0.75, fx - R * 0.55, R * 1.22 + dy, fx + R * 0.05, R * 1.2 + dy)
    path.cubicTo(fx + R * 0.6, R * 1.18 + dy, R * 1.0, R * 0.7, R * 0.97, -R * 0.12)
    path.cubicTo(R * 0.86, R * 0.2, fx + R * 0.5, R * 0.14 + dy, fx + R * 0.32, R * 0.24 + dy)
    path.quadTo(fx, R * 0.18 + dy, fx - R * 0.32, R * 0.24 + dy)
    path.cubicTo(fx - R * 0.5, R * 0.14 + dy, -R * 0.86, R * 0.2, -R * 0.97, -R * 0.12)
    path.close()
    c.drawPath(path, paint(color))
    c.drawPath(path, paint(outline, stroke=4))
    for k in range(5):
        u = (k + 0.5) / 5
        x = fx - R * 0.45 + R * 0.9 * u
        c.drawLine(x, R * 0.62 + dy, x + R * 0.03, R * 0.85 + dy, paint(outline, 0.18, stroke=2.5))


def headband(c, R, color, outline='outline'):
    """A sweatband round the forehead, tied at the back."""
    head = skia.Path()
    head.addCircle(0, 0, R - 1)
    for tail in (((-R * 0.95, -R * 0.5), (-R * 1.32, -R * 0.2)), ((-R * 0.95, -R * 0.48), (-R * 1.25, -R * 0.02))):
        c.drawLine(*tail[0], *tail[1], paint(outline, stroke=13))
        c.drawLine(*tail[0], *tail[1], paint(color, stroke=7))
    c.save()
    c.clipPath(head, doAntiAlias=True)
    band = skia.Rect.MakeLTRB(-R * 1.1, -R * 0.66, R * 1.1, -R * 0.42)
    c.drawRect(band, paint(color))
    c.drawRect(band, paint('#FFFFFF', 0.12))
    for y in (-R * 0.66, -R * 0.42):
        c.drawLine(-R * 1.1, y, R * 1.1, y, paint(outline, stroke=4))
    c.restore()
    c.drawCircle(0, 0, R, paint(outline, stroke=OUTLINE_W))


def brows(c, R, p, outline='outline', color=None):
    turn = p.get('turn', 0.35)
    fx = turn * R * 0.42
    hs = R * 0.30 * (1 - 0.32 * turn)
    lx = p.get('lx', 0.0)
    brow = p.get('brow', 0.0)
    by = -R * 0.33 - p.get('brow_y', 0.0) * R + p.get('face_dy', 0.0) * R
    bl = R * 0.15
    for ex, inner in ((fx - hs + lx * R * 0.07, 1), (fx + hs + lx * R * 0.07, -1)):
        # inner end (toward the nose) drops for anger, rises for worry
        a = math.radians(brow) * inner
        dx, dy = math.cos(a) * bl, math.sin(a) * bl
        if color:
            c.drawLine(ex - dx, by - dy, ex + dx, by + dy, paint(outline, stroke=10.5))
            c.drawLine(ex - dx, by - dy, ex + dx, by + dy, paint(color, stroke=6.5))
        else:
            c.drawLine(ex - dx, by - dy, ex + dx, by + dy, paint(outline, stroke=6.5))


def face(c, R, p, outline='outline', brow_color=None):
    turn = p.get('turn', 0.35)
    fx = turn * R * 0.42
    hs = R * 0.30 * (1 - 0.32 * turn)
    lx, ly = p.get('lx', 0.0), p.get('ly', 0.0)
    ex_b, ex_f = fx - hs + lx * R * 0.07, fx + hs + lx * R * 0.07
    ey = -R * 0.05 + ly * R * 0.06 + p.get('face_dy', 0.0) * R
    er = R * 0.105 * p.get('eye_size', 1.0)
    eyes = p.get('eyes', 'dot')
    openness = max(0.0, min(1.0, p.get('eye', 1.0)))
    ink = paint(outline)

    if p.get('bags', 0) > 0:
        for ex in (ex_b, ex_f):
            path = skia.Path()
            path.moveTo(ex - er * 1.3, ey + er * 1.5)
            path.quadTo(ex, ey + er * 2.6, ex + er * 1.3, ey + er * 1.5)
            c.drawPath(path, paint(outline, 0.45 * p['bags'], stroke=3))

    for i, ex in enumerate((ex_b, ex_f)):
        size = er * (0.92 if i == 0 and turn > 0.5 else 1.0)
        if eyes == 'happy' or (eyes == 'closed'):
            path = skia.Path()
            if eyes == 'happy':
                path.moveTo(ex - size * 1.3, ey + size * 0.5)
                path.quadTo(ex, ey - size * 1.6, ex + size * 1.3, ey + size * 0.5)
            else:
                path.moveTo(ex - size * 1.3, ey)
                path.quadTo(ex, ey + size * 1.3, ex + size * 1.3, ey)
            c.drawPath(path, paint(outline, stroke=4.5))
        elif eyes == 'wide':
            sr = size * 2.05
            c.drawOval(oval(ex, ey, sr, sr * max(0.12, openness)), paint('#FFFFFF'))
            c.drawOval(oval(ex, ey, sr, sr * max(0.12, openness)), paint(outline, stroke=3.5))
            if openness > 0.3:
                c.drawCircle(ex + lx * sr * 0.45, ey + ly * sr * 0.45, size * 0.95 * p.get('pupil', 1.0), ink)
        else:
            ry = size * openness
            if ry < size * 0.18:
                c.drawLine(ex - size * 1.1, ey, ex + size * 1.1, ey, paint(outline, stroke=4))
            else:
                c.drawOval(oval(ex, ey, size, ry), ink)
                if size > 4:
                    c.drawCircle(ex + size * 0.35, ey - ry * 0.4, size * 0.28, paint('#FFFFFF', 0.85))
            if eyes == 'tired':
                c.drawLine(ex - size * 1.5, ey - size * 0.35, ex + size * 1.5, ey - size * 0.15,
                           paint(outline, stroke=4))

    if not p.get('brows_over_hat'):
        brows(c, R, p, outline, brow_color)

    mx, my = fx + R * 0.03, R * (0.38 + p.get('mouth_dy', 0.0))
    mw = R * 0.2 * p.get('mwide', 1.0)
    mopen = p.get('mopen', 0.0)
    mouth = p.get('mouth', 'curve')
    if mouth == 'wavy':
        # a shaky, scared squiggle
        path = skia.Path()
        n = 24
        for k in range(n + 1):
            u = k / n
            x = mx - mw * 1.15 + u * mw * 2.3
            y = my + math.sin(u * math.pi * 4) * R * 0.035 + R * 0.02
            path.moveTo(x, y) if k == 0 else path.lineTo(x, y)
        c.drawPath(path, paint(outline, stroke=5))
    elif mouth == 'teeth':
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(mx - mw * 1.2, my - R * 0.08, mx + mw * 1.2, my + R * 0.1), 6, 6)
        c.drawRRect(r, paint('#FFFFFF'))
        c.drawRRect(r, paint(outline, stroke=3.5))
        c.drawLine(mx - mw * 1.1, my + R * 0.01, mx + mw * 1.1, my + R * 0.01, paint(outline, stroke=2.5))
        for k in (-0.5, 0.0, 0.5):
            c.drawLine(mx + mw * k, my - R * 0.07, mx + mw * k, my + R * 0.09, paint(outline, stroke=2))
    elif mopen > 0.04:
        h = R * 0.3 * mopen
        r = oval(mx, my + h * 0.3, mw * (0.75 + 0.35 * (1 - mopen)), h)
        c.drawOval(r, paint('#3A1F22'))
        c.save()
        c.clipRect(r)
        c.drawOval(oval(mx, my + h * 1.05, mw * 0.6, h * 0.55), paint('#D9707A'))
        c.restore()
        c.drawOval(r, paint(outline, stroke=4))
    else:
        smile = p.get('smile', 0.15)
        path = skia.Path()
        path.moveTo(mx - mw, my - smile * R * 0.04)
        path.quadTo(mx, my + smile * R * 0.26, mx + mw, my - smile * R * 0.04)
        c.drawPath(path, paint(outline, stroke=4.5))

    if p.get('blush', 0) > 0:
        for ex in (ex_b, ex_f):
            c.drawOval(oval(ex, ey + er * 2.6, er * 1.5, er * 0.7), paint('#F28C8C', 0.45 * p['blush'], blur=3))
    if p.get('sweat', 0) > 0:
        s = p['sweat']
        # one drop at the temple; heavy sweat adds drops on the other side and the cheek
        drops = [(R * 0.8, -R * 0.45, 1.0)]
        if s > 1.1:
            drops += [(-R * 0.82, -R * 0.3, 0.8), (R * 0.9, R * 0.1, 0.65)]
        for x0, y0, k in drops:
            d = s * k
            path = skia.Path()
            path.moveTo(x0, y0 - 16 * d)
            path.cubicTo(x0 + 9 * d, y0 - 2 * d, x0 + 9 * d, y0 + 9 * d, x0, y0 + 9 * d)
            path.cubicTo(x0 - 9 * d, y0 + 9 * d, x0 - 9 * d, y0 - 2 * d, x0, y0 - 16 * d)
            c.drawPath(path, paint('#9ED8FF', 0.95))
            c.drawCircle(x0 - 2.5 * d, y0 + 2 * d, 2.2 * d, paint('#FFFFFF', 0.8))
            c.drawPath(path, paint(outline, stroke=3))
    if p.get('tears', 0) > 0:
        tl = p['tears']
        for ex in (ex_b, ex_f):
            path = poly([(ex, ey + er), (ex - 2, ey + er + R * 0.45 * tl)])
            c.drawPath(path, paint('#8FD0FF', 0.85, stroke=5))


def shadow_eyes(c, R, openness=1.0, turn=0.3, slant=18.0, lx=0.0, ly=0.0, rim='red', scale=1.0, a=1.0):
    """Two glowing, mocking red eyes (half-closed lids slanting inward)."""
    if openness <= 0.02 or a <= 0:
        return
    fx = turn * R * 0.42
    hs = R * 0.3 * (1 - 0.3 * turn)
    ey = -R * 0.04 + ly * R * 0.05
    ew, eh = R * 0.17 * scale, R * 0.085 * scale * openness
    path = skia.Path()
    for ex, inner in ((fx - hs + lx * R * 0.06, 1), (fx + hs + lx * R * 0.06, -1)):
        sl = math.radians(slant) * inner
        # lower lid is a half ellipse; upper lid is a slanted line
        top_l = (ex - ew, ey - eh * 0.2 - math.tan(sl) * ew * 0.6)
        top_r = (ex + ew, ey - eh * 0.2 + math.tan(sl) * ew * 0.6)
        path.moveTo(*top_l)
        path.lineTo(*top_r)
        path.quadTo(ex + ew * 0.9, ey + eh * 1.6, ex, ey + eh * 1.5)
        path.quadTo(ex - ew * 0.9, ey + eh * 1.6, *top_l)
        path.close()
    c.drawPath(path, paint(rim, 0.9 * a, blur=10, blend='add'))
    c.drawPath(path, paint('#FF2A22', a))
    c.save()
    c.scale(1, 1)
    c.drawPath(path, paint('#FFB3A6', 0.55 * a, blur=2.5, blend='add'))
    c.restore()


def eye_pair(c, x, y, size, openness=1.0, slant=16.0, a=1.0, rim='red'):
    """Free-floating pair of red eyes in the dark (no body)."""
    c.save()
    c.translate(x, y)
    shadow_eyes(c, size, openness, 0.0, slant, rim=rim, a=a)
    c.restore()


def beanie(c, R, color, outline):
    dome = skia.Path()
    dome.addArc(skia.Rect.MakeLTRB(-R - 3, -R - 5, R + 3, R + 1), 180, 180)
    dome.close()
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-R * 2, -R * 2, R * 2, -R * 0.28))
    c.drawPath(dome, paint(color))
    c.drawPath(dome, paint(outline, stroke=OUTLINE_W))
    c.restore()
    band = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-R * 1.04, -R * 0.5, R * 1.04, -R * 0.2), 10, 10)
    c.drawRRect(band, paint(color))
    c.drawRRect(band, paint('#000000', 0.18))
    c.drawRRect(band, paint(outline, stroke=OUTLINE_W))
    for k in range(-4, 5):
        x = k * R * 0.21
        c.drawLine(x, -R * 0.46, x, -R * 0.24, paint(outline, 0.35, stroke=2.5))
    c.drawCircle(0, -R * 1.07, R * 0.17, paint(color))
    c.drawCircle(0, -R * 1.07, R * 0.17, paint(outline, stroke=4))


def hair_front(c, R, style, color, outline):
    if style == 'sides':
        # greying hair left only at the temples: soft patches clipped to the head
        head = skia.Path()
        head.addCircle(0, 0, R)
        c.save()
        c.clipPath(head, doAntiAlias=True)
        for sx in (-1, 1):
            r = oval(sx * R * 1.02, -R * 0.12, R * 0.3, R * 0.46)
            c.drawOval(r, paint(color))
            c.drawOval(r, paint(outline, stroke=3))
        c.restore()
        c.drawCircle(0, 0, R, paint(outline, stroke=OUTLINE_W))
        return
    if style == 'short':
        path = skia.Path()
        path.addArc(skia.Rect.MakeLTRB(-R - 2, -R - 4, R + 2, R), 195, 150)
        path.quadTo(R * 0.2, -R * 0.55, -R * 0.95, -R * 0.25)
        path.close()
        c.drawPath(path, paint(color))
        c.drawPath(path, paint(outline, stroke=4.5))
    elif style == 'spiky':
        pts = []
        for k in range(9):
            a = math.radians(200 + k * 17.5)
            r = R * (1.18 if k % 2 else 0.98)
            pts.append((math.cos(a) * r, math.sin(a) * r))
        pts += [(R * 0.8, -R * 0.35), (-R * 0.9, -R * 0.3)]
        path = poly(pts, True)
        c.drawPath(path, paint(color))
        c.drawPath(path, paint(outline, stroke=4.5))
    elif style in ('long', 'bun'):
        path = skia.Path()
        path.addArc(skia.Rect.MakeLTRB(-R - 3, -R - 4, R + 3, R + 2), 185, 170)
        path.quadTo(0, -R * 0.62, -R * 1.0, -R * 0.15)
        path.close()
        c.drawPath(path, paint(color))
        c.drawPath(path, paint(outline, stroke=4.5))
        if style == 'bun':
            c.drawCircle(-R * 0.25, -R * 1.12, R * 0.3, paint(color))
            c.drawCircle(-R * 0.25, -R * 1.12, R * 0.3, paint(outline, stroke=4.5))


def hair_back(c, R, color):
    path = skia.Path()
    path.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-R * 1.1, -R * 0.6, R * 0.6, R * 1.35), R * 0.5, R * 0.5))
    c.drawPath(path, paint(color))
    c.drawPath(path, paint('outline', stroke=4.5))


# --- canned motion helpers ---------------------------------------------------------

def walk(t, speed=1.0, stride=26.0, phase=0.0):
    """Procedural walk cycle angles (merge into a pose)."""
    w = (t * speed * 2.0 + phase) * math.pi * 2 / 2.0
    s = math.sin(w)
    return dict(
        hf=stride * s, kf=max(0.0, -s) * 38 + 6,
        hb=-stride * s, kb=max(0.0, s) * 38 + 6,
        sf=-stride * 0.7 * s - 4, ef=18, sb=stride * 0.7 * s + 6, eb=18,
        head_dy=-abs(math.cos(w)) * 5, breathe=0.0,
    )


def run(t, speed=1.0, stride=38.0, phase=0.0):
    """Procedural run cycle angles (merge into a pose); 'dy' is the hip bounce to add to y.
    Same phase as walk(): a leg reaches full stride at t = (0.25 + 0.5 k) / speed."""
    w = (t * speed * 2.0 + phase) * math.pi
    s, co = math.sin(w), math.cos(w)
    return dict(
        hf=stride * s + 6, kf=12 + 78 * max(0.0, co) ** 1.4,
        hb=-stride * s + 6, kb=12 + 78 * max(0.0, -co) ** 1.4,
        sf=-stride * 1.0 * s, ef=95 + 10 * s, sb=stride * 1.0 * s, eb=95 - 10 * s,
        lean=11.0, head_dy=0.0, breathe=0.0, dy=-9 * abs(s),
    )


def to_local(pose, world):
    """A world point -> the character's local frame (undoing x/y, rot, scale and facing), for IK targets."""
    dx, dy = world[0] - pose.get('x', 0.0), world[1] - pose.get('y', 0.0)
    rot = math.radians(pose.get('rot', 0.0))
    cr, sr = math.cos(-rot), math.sin(-rot)
    dx, dy = dx * cr - dy * sr, dx * sr + dy * cr
    s = pose.get('scale', 1.0)
    return dx / s * pose.get('facing', 1), dy / s


def idle(t, seed=0, amount=1.0):
    """Subtle breathing sway for standing or sitting characters."""
    return dict(breathe=(math.sin(t * 2.1 + seed) * 0.5 + 0.5) * amount,
                tilt=noise1(t * 0.5, seed) * 2.5 * amount)
