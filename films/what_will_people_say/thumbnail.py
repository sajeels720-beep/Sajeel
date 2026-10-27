"""YouTube thumbnails (three variants for Test & Compare).

The formula from the channels that win this niche: one character, one extreme emotion, big and close,
dramatic light on a dark background, one or two huge words ending in a full stop.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import skia  # noqa: E402

from common import HERO, HERO_BEANIE, SHADE, STAND_HIP, play_guitar  # noqa: E402
from engine.core import H, W, hrand, hrange  # noqa: E402
from engine.draw import col, cone, light_pool, paint, poly, rrect, text, vignette  # noqa: E402
from engine.fx import eye_field  # noqa: E402
from engine.props import phone, stage_floor  # noqa: E402

# --- lighting helpers ------------------------------------------------------------------------------------


def head_world(x, y, scale, facing, j):
    hx, hy = j['head']
    return x + facing * scale * hx, y + scale * hy


def shade_head(c, hx, hy, R, light=(0.45, -0.9), rim='#FFF1D6', bounce='red', rim_a=0.55):
    """Spotlight shading on a round head: soft shadow away from the light, a rim highlight toward it,
    and a red bounce light from the eyes in the dark."""
    lx, ly = light
    clip = skia.Path()
    clip.addCircle(hx, hy, R - 1)
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    shadow = skia.GradientShader.MakeRadial(
        center=(hx + lx * R * 0.35, hy + ly * R * 0.35), radius=R * 1.45,
        colors=[col('#000000', 0.0), col('#000000', 0.0), col('#1A0C10', 0.42)], positions=[0.0, 0.55, 1.0])
    c.drawCircle(hx, hy, R, paint('#000000', 1.0, shader=shadow))
    c.drawCircle(hx + lx * R * 0.12, hy + ly * R * 0.12, R * 0.98,
                 paint(rim, rim_a, stroke=R * 0.1, blur=R * 0.05, blend='add'))
    if bounce:
        c.drawCircle(hx - lx * R * 0.1 - R * 0.15, hy + R * 0.1, R,
                     paint(bounce, 0.35, stroke=R * 0.14, blur=R * 0.08, blend='add'))
    c.restore()


def blurred(c, sigma, fn):
    c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
    fn()
    c.restore()


def flash(c, x, y, size=1.0):
    """A phone camera flash: hot core, glow and star streaks."""
    c.drawCircle(x, y, 60 * size, paint('#CFE4FF', 0.35, blur=30 * size, blend='add'))
    c.drawCircle(x, y, 16 * size, paint('#FFFFFF', 0.95, blur=4 * size, blend='add'))
    for ang in (0, 90):
        a = math.radians(ang)
        dx, dy = math.cos(a) * 110 * size, math.sin(a) * 110 * size
        c.drawLine(x - dx, y - dy, x + dx, y + dy,
                   paint('#E6F0FF', 0.55, stroke=3 * size, blur=2.5 * size, blend='add'))


def filming_shadow(c, x, y, scale, facing, eye=1.0, flash_on=True, lean=6.0, arm=0.0):
    """A shadow figure holding a phone up to film him (we see the back of the phone and its flash)."""
    hand = (70 + arm, -168)
    SHADE.draw(c, dict(x=x, y=y, scale=scale, facing=facing, turn=0.35, eye=eye, lean=lean, tilt=8,
                       hand_f=hand, hand_b=(52 + arm, -150), sb=0, eb=0))
    px = x + facing * scale * (hand[0] + 8)
    py = y + scale * (hand[1] - 34)
    c.save()
    c.translate(px, py)
    c.scale(scale * 0.9, scale * 0.9)
    body = rrect(-21, -37, 42, 74, 9)
    c.drawRRect(body, paint('#0B0B0F'))
    c.drawRRect(body, paint('#2A2A33', stroke=3))
    c.restore()
    if flash_on:
        flash(c, px + facing * scale * 9, py - scale * 22, scale * 0.55)


def crowd_eyes(c, n, seed, region, size_range, avoid=None, slant=(14, 26)):
    x0, y0, x1, y1 = region
    eyes = []
    i = 0
    while len(eyes) < n and i < 5000:
        x, y = hrange(x0, x1, i, seed), hrange(y0, y1, i, seed + 1)
        i += 1
        if avoid and avoid(x, y):
            continue
        if any(abs(x - ex) < 120 and abs(y - ey) < 70 for ex, ey, *_ in eyes):
            continue
        eyes.append((x, y, hrange(*size_range, i, seed + 2), 1.0, hrange(*slant, i, seed + 3), 1.0))
    eye_field(c, eyes, 0.0)


def big_text(c, s, x, y, size, color='white', align='center', name='Fredoka-700'):
    text(c, s, x + 8, y + 12, size, name, '#000000', 0.6, align=align)  # hard drop shadow
    text(c, s, x, y, size, name, color, align=align, outline='#000000', outline_w=size * 0.11)
    text(c, s, x, y, size, name, color, align=align)


def background(c, top='#08070B', bottom='#1C0708'):
    shader = skia.GradientShader.MakeLinear(points=[(0, 0), (0, H)], colors=[col(top), col(bottom)])
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#000000', shader=shader))


def terrified_hero(c, x, y, scale, lx=-0.7, facing=1, guitar=True, light=(0.45, -0.9), who=HERO_BEANIE,
                   face=None, tremble=True):
    gp, mid, _ = play_guitar(0.0, seated=False, strum=False, fret_shift=False) if guitar else ({}, None, 0)
    pose = dict(x=x, y=y, scale=scale, facing=facing, turn=0.12, eyes='wide', pupil=0.5, lx=lx, ly=-0.05,
                brow=-24, brow_y=0.06, mopen=0.62, mwide=1.15, sweat=1.6, lean=-7, tilt=-6,
                hb=-6, kb=4, hf=7, kf=4, **gp)
    pose.update(face or {})
    j = who.draw(c, pose, {'mid': mid} if mid else None)
    hx, hy = head_world(x, y, scale, facing, j)
    R = who.look.head_r * scale
    shade_head(c, hx, hy, R, light)
    # trembling marks beside the head
    for side in ((-1, 1) if tremble else ()):
        for k in range(3):
            r = R * (1.16 + 0.1 * k)
            a0 = (-30 if side > 0 else 150) + k * 4
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeLTRB(hx - r, hy - r, hx + r, hy + r), a0, 26)
            c.drawPath(arc, paint('#F4F1EA', 0.85 - 0.2 * k, stroke=7))
    return hx, hy, R


# --- variant A: "WHAT WILL PEOPLE SAY?" - close-up terror, the crowd leaning in -----------------------------

def variant_a(c):
    background(c)
    crowd_eyes(c, 34, 11, (-40, 230, W + 40, H + 60), (70, 120),
               avoid=lambda x, y: 900 < x < 1650 and y < 1000)
    for i, (x, s, f) in enumerate([(140, 1.7, 1), (420, 1.9, 1), (1820, 1.8, -1), (650, 1.55, 1)]):
        SHADE.draw(c, dict(x=x, y=H + 40 - STAND_HIP * s * 0.35, scale=s, facing=f, turn=0.35, eye=1.0,
                           lean=10, tilt=10 + 4 * i, sb=10, sf=-4))
    cone(c, (1380, -200), 120, H, 540, '#FFF1D6', 0.22, soft=50)
    # bare round head, no beanie; a quiet, uneasy sideways glance at the crowd instead of cartoon terror
    hx, hy, R = terrified_hero(c, 1385, 1175, 3.25, lx=-0.75, who=HERO, tremble=False,
                               face=dict(eyes='dot', ly=0.0, brow=-17, brow_y=0.0, mopen=0.0, smile=-0.2,
                                         mwide=0.75, sweat=0.0, tilt=-1))
    light_pool(c, hx, hy - R * 0.6, R * 2.2, R * 1.6, '#FFF1D6', 0.18)
    light_pool(c, 0, H * 0.75, 900, 700, 'red', 0.22)

    def fg():
        SHADE.draw(c, dict(x=-60, y=H + 330, scale=4.6, facing=1, turn=0.3, eye=1.0, lean=14, tilt=14))
        SHADE.draw(c, dict(x=W + 230, y=H + 380, scale=4.8, facing=-1, turn=0.3, eye=1.0, lean=14, tilt=12))
    blurred(c, 14, fg)
    vignette(c, W, H, 0.6)
    big_text(c, 'WHAT WILL', 70, 215, 180, 'white', align='left')
    big_text(c, 'PEOPLE SAY?', 70, 410, 180, 'white', align='left')


# --- variant B: "CRINGE." - everyone is filming him ------------------------------------------------------------

def variant_b(c):
    background(c, '#07070A', '#150608')
    crowd_eyes(c, 26, 21, (-40, 160, W + 40, 700), (60, 95), avoid=lambda x, y: 640 < x < 1300)
    for x, s, f, arm in [(130, 1.45, 1, 0), (1790, 1.5, -1, 10), (380, 1.3, 1, 20), (1540, 1.35, -1, 0)]:
        filming_shadow(c, x, 1010 - STAND_HIP * s * 0.2, s, f, arm=arm)
    cone(c, (960, -200), 110, H, 480, '#FFF1D6', 0.22, soft=50)
    hx, hy, R = terrified_hero(c, 960, 1200, 2.75, lx=0.0)
    light_pool(c, hx, hy - R * 0.5, R * 2.0, R * 1.5, '#FFF1D6', 0.16)

    def fg():
        filming_shadow(c, 70, H + 360, 3.6, 1, arm=30)
        filming_shadow(c, W - 40, H + 380, 3.7, -1)
    blurred(c, 12, fg)
    vignette(c, W, H, 0.55)
    for word, x, y, rot in (('lol', 360, 330, -10), ('cringe.', 1560, 380, 8)):
        c.save()
        c.translate(x, y)
        c.rotate(rot)
        text(c, word, 0, 0, 92, 'PatrickHand', '#FF8A7E', glow='red', glow_a=0.8, glow_r=18,
             outline='#160404', outline_w=8)
        c.restore()
    big_text(c, 'CRINGE.', W / 2, 205, 230, 'white')


# --- variant C: the stage and the sea of eyes, the film's title --------------------------------------------------

def variant_c(c):
    background(c, '#050507', '#0C0405')
    floor = 760
    stage_floor(c, -100, W + 100, floor, 70)
    cone(c, (1480, -160), 70, floor, 300, '#E8EEFF', 0.24, soft=40)
    light_pool(c, 1480, floor, 380, 60, '#E8EEFF', 0.55)
    gp, mid, _ = play_guitar(0.0, seated=False, strum=False, fret_shift=False)
    y = floor - STAND_HIP * 1.55
    j = HERO_BEANIE.draw(c, dict(x=1480, y=y, scale=1.55, facing=1, turn=0.1, eyes='wide', pupil=0.5, lx=-0.6,
                                 brow=-24, mopen=0.5, sweat=1.5, lean=-5, **gp), {'mid': mid})
    hx, hy = head_world(1480, y, 1.55, 1, j)
    shade_head(c, hx, hy, 62 * 1.55, (0.2, -1.0))
    crowd_eyes(c, 90, 31, (-40, floor + 40, W + 40, H + 40), (60, 110))
    crowd_eyes(c, 26, 41, (-40, -20, W + 40, floor - 60), (55, 80),
               avoid=lambda x, y: 1200 < x < 1760 or (x < 1150 and y < 420))
    vignette(c, W, H, 0.5)
    big_text(c, 'WHAT WILL', 70, 190, 150, 'white', align='left')
    big_text(c, 'PEOPLE SAY?', 70, 350, 150, '#FF4A40', align='left')


# --- variant D: the reference channel's own style ---------------------------------------------------------------
# Flat near-black, one huge head with one emotion, one glowing thing that tells the story, plain white
# hand-lettered words. Here: hiding under the blanket with his guitar, side-eyeing the red eyes in the dark.

def variant_d(c, words=('WHAT WILL', 'PEOPLE SAY?')):
    from engine.draw import circle, oval
    from engine.props import guitar
    from engine.rig import eye_pair
    c.drawPaint(paint('#0E0E11'))
    line = '#4B4F5C'
    # the figure in the dark: a faint silhouette, then its eyes
    sil = skia.Path()
    sil.addCircle(1500, 470, 190)
    sil.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(1330, 600, 1680, 1200), 120, 120))
    c.drawPath(sil, paint('#121217'))
    c.drawPath(sil, paint('red', 0.12, stroke=10, blur=10, blend='add'))
    eye_pair(c, 1500, 470, 330, 1.0, 18)
    eye_pair(c, 1170, 210, 110, 1.0, 22, a=0.8)
    eye_pair(c, 1820, 160, 90, 1.0, 14, a=0.7)
    # pillow and headboard post
    c.drawRRect(rrect(330, 640, 640, 190, 80), paint('#3A3D47'))
    c.drawRRect(rrect(330, 640, 640, 190, 80), paint(line, stroke=7))
    c.drawRRect(rrect(1090, 380, 60, 760, 30), paint('#24252C'))
    c.drawRRect(rrect(1090, 380, 60, 760, 30), paint(line, stroke=7))
    # his guitar, clutched under the blanket, neck sticking out
    guitar(c, 800, 1000, -60, 2.0, shine=0.6)
    # the head
    hx, hy, R = 700, 650, 215
    # full panic: huge eyes with tiny pupils, brows shot up, a shaky mouth, sweat everywhere
    HERO_BEANIE.draw_head(c, hx, hy, dict(turn=0.45, eyes='wide', eye_size=1.3, pupil=0.4, lx=0.95, ly=-0.05,
                                           face_dy=0.12, mouth_dy=0.1, brow=-30, brow_y=0.1,
                                           brows_over_hat=True, mouth='wavy', mwide=1.15, sweat=2.0),
                          angle=-6, scale=R / 62)
    shade_head(c, hx, hy, R, light=(0.7, -0.5), rim='#FFE6E2', bounce=None, rim_a=0.16)
    # tremble marks and flying sweat
    for side, a0 in ((-1, 196), (1, -16)):
        for k in range(3):
            r = R * (1.12 + 0.11 * k)
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeLTRB(hx - r, hy - r, hx + r, hy + r), a0 + k * 3, 24 if side > 0 else -24)
            c.drawPath(arc, paint('#F4F1EA', 0.9 - 0.25 * k, stroke=8))
    for dx, dy, sz in ((-R * 1.25, -R * 0.55, 1.0), (R * 1.3, -R * 0.75, 0.85), (-R * 1.05, -R * 0.95, 0.7)):
        d = sz * 2.6
        x0, y0 = hx + dx, hy + dy
        drop = skia.Path()
        drop.moveTo(x0, y0 - 16 * d)
        drop.cubicTo(x0 + 9 * d, y0 - 2 * d, x0 + 9 * d, y0 + 9 * d, x0, y0 + 9 * d)
        drop.cubicTo(x0 - 9 * d, y0 + 9 * d, x0 - 9 * d, y0 - 2 * d, x0, y0 - 16 * d)
        c.drawPath(drop, paint('#9ED8FF', 0.95))
        c.drawPath(drop, paint('outline', stroke=5))
    # the blanket pulled up to his chin
    bl = skia.Path()
    bl.moveTo(-60, 790)
    bl.cubicTo(250, 760, 450, 820, 620, 830)
    bl.cubicTo(800, 840, 900, 800, 1060, 840)
    bl.lineTo(1080, 1140)
    bl.lineTo(-60, 1140)
    bl.close()
    c.drawPath(bl, paint('#2B3242'))
    c.drawPath(bl, paint(line, stroke=7))
    c.drawLine(120, 900, 520, 960, paint(line, 0.7, stroke=6))
    c.drawLine(640, 930, 960, 980, paint(line, 0.7, stroke=6))
    # fingers gripping the blanket edge and the guitar neck
    for fx, fy in ((560, 832), (610, 836), (660, 838)):
        circle(c, fx, fy, 24, 'skin', 'outline', 6)
    gx, gy = 800 + math.cos(math.radians(-60)) * 150 * 2.0, 1000 + math.sin(math.radians(-60)) * 150 * 2.0
    circle(c, gx, gy, 30, 'skin', 'outline', 6)
    vignette(c, W, H, 0.35)
    # plain white hand-lettered words, like "DAY 1."
    size = 150 if len(words) > 1 else 215
    for k, wline in enumerate(words):
        y = (190 if len(words) > 1 else 230) + k * 170
        text(c, wline, 70, y, size, 'Mali-700', 'white', align='left')


def variant_e(c):
    variant_d(c, ('CRINGE.',))


VARIANTS = {'a': variant_a, 'b': variant_b, 'c': variant_c, 'd': variant_d, 'e': variant_e}


def render(fn, path):
    surface = skia.Surface(W, H)
    c = surface.getCanvas()
    c.clear(col('#000000'))
    fn(c)
    img = surface.makeImageSnapshot()
    img.resize(1280, 720, skia.SamplingOptions(skia.CubicResampler.Mitchell())).save(str(path), skia.kPNG)
    return path


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {k: render(fn, out_dir / f'thumbnail_{k}.png') for k, fn in VARIANTS.items()}
    main = out_dir / 'thumbnail.png'
    main.write_bytes(paths['d'].read_bytes())  # the reference channel's style
    return main


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
