"""YouTube thumbnails for 'Everyone Quits in February.' in the house style (studio/THUMBNAILS.md).

A: February, the gym nearly empty: behind him the January crowd is going to smoke under the fallen
   NEW YEAR banner; the shadow's hand is on his shoulder. "EVERYONE QUITS."
B: the same moment, closer, asking the viewer: "WILL YOU?"
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import skia  # noqa: E402

from common import HERO_JAN, SHADE, extra  # noqa: E402
from engine.core import H, W  # noqa: E402
from engine.draw import col, light_pool, paint, vignette  # noqa: E402
from engine.fx import dissolve, snowfall  # noqa: E402
from engine.gym import banner, dumbbell, dumbbell_rack, treadmill  # noqa: E402
from engine.rig import to_local  # noqa: E402
from engine.thumbkit import blurred, brush_title, haze, render, shade_head  # noqa: E402


def backdrop(c):
    shader = skia.GradientShader.MakeLinear(points=[(0, 0), (0, H)], colors=[col('#151B28'), col('#07080C')])
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#000000', shader=shader))

    def far():
        # the windows onto a snowy night, the fallen banner, a rack and a treadmill nobody uses now
        for k in range(3):
            x = 760 + k * 250
            c.drawRect(skia.Rect.MakeXYWH(x, 150, 200, 420), paint('#132036'))
            snowfall(c, x, 150, x + 200, 570, 1.0, n=24, seed=k, size=(2.0, 5.0))
            c.drawRect(skia.Rect.MakeXYWH(x, 150, 200, 420), paint('#2E323C', stroke=14))
        banner(c, 640, 1500, 90, 110, loose=0.8, t=0.0)
        dumbbell_rack(c, 380, 900, w=420, scale=1.3, missing=((0, 1), (1, 3), (0, 4)))
        treadmill(c, 1500, 900, scale=1.3)
    blurred(c, 6, far)
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#05060A', 0.35))
    haze(c, 900, -60, 1300, H, '#9DB7FF', 0.06)


def quitters(c, sigma=4.5):
    """The January crowd going to smoke behind him."""
    def draw():
        for k, (x, s, u, i) in enumerate(((180, 1.9, 0.42, 2), (520, 1.6, 0.6, 5), (840, 1.4, 0.75, 7))):
            feet = 1040
            pose = dict(x=x, y=feet - 123 * s, scale=s, facing=1, turn=0.35, hb=-4, kb=3, hf=5, kf=3,
                        eyes='tired', brow=-8, smile=-0.25, ly=0.4)
            box = (x - 110 * s, feet - 370 * s, x + 110 * s, feet + 6)
            who = extra(i)
            dissolve(c, lambda cc, who=who, pose=pose: who.draw(cc, pose), box, 10.0, 10.0 - 1.7 * u, 1.7,
                     seed=20 + k, smoke_a=0.7, rise=320)
    blurred(c, sigma, draw)


def hero_and_shadow(c, hero_x=1210, feet=1300, scale=3.05, face=None):
    """Him, big and quietly worried, a dumbbell in his hand; the shadow's hand on his shoulder."""
    hip = (hero_x, feet - 123 * scale)
    pose = dict(x=hip[0], y=hip[1], scale=scale, facing=-1, turn=0.32, hb=-4, kb=3, hf=5, kf=3, lean=4, tilt=6,
                eyes='dot', lx=-0.35, ly=0.35, brow=-15, smile=-0.22, mwide=0.75, sb=6, eb=14)
    pose.update(face or {})
    hand = (hero_x - 175, hip[1] - 150)
    pose['hand_f'] = to_local(pose, hand)

    # the shadow looms behind him, mostly out of frame, red eyes on him
    s2 = scale * 1.12
    sh_pose = dict(x=hero_x + 330, y=feet - 123 * s2 + 40, scale=s2, facing=-1, turn=0.2, hb=-4, kb=3, hf=5, kf=3,
                   lean=16, tilt=12, brow=24, eye=1.0, sb=6, eb=10, sf=60, ef=30, rim_a=0.5)
    from engine.rig import BASE_POSE, solve
    j = solve(HERO_JAN.look, dict(BASE_POSE, **pose))
    shoulder = (hip[0] - j['sh_b'][0] * scale, hip[1] + j['sh_b'][1] * scale)
    sh_pose['hand_f'] = to_local(sh_pose, (shoulder[0] + 10, shoulder[1] - 4))
    SHADE.with_look(rim_a=0.55).draw(c, sh_pose)

    jj = HERO_JAN.draw(c, pose, {'front': lambda cc, jt: dumbbell(cc, *jt['hand_f'], size=1.1, angle=-30)})
    hx, hy = hip[0] - scale * jj['head'][0], hip[1] + scale * jj['head'][1]
    R = HERO_JAN.look.head_r * scale
    shade_head(c, hx, hy, R, light=(-0.6, -0.6), rim='#DCE8FF', bounce='red', rim_a=0.22, bounce_a=0.14)
    # his face is the brightest thing in the frame after the words: a soft key light from the windows
    light_pool(c, hx - 60, hy - 40, 420, 380, '#DCE8FF', 0.08)
    # the hand on his shoulder, in front of him
    c.drawCircle(shoulder[0] + 10, shoulder[1] - 4, 44, paint('red', 0.5, blur=14, blend='add'))
    c.drawCircle(shoulder[0] + 10, shoulder[1] - 4, 38, paint('#040405'))
    return hx, hy, R


def finish(c):
    vignette(c, W, H, 0.6)


def variant_a(c):
    backdrop(c)
    quitters(c)
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#05060A', 0.18))
    hero_and_shadow(c)
    finish(c)
    brush_title(c, ['EVERYONE', 'QUITS.'], 64, 230, 205, gap=0.96)


def variant_b(c):
    backdrop(c)
    quitters(c, sigma=6)
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#05060A', 0.22))
    hero_and_shadow(c, hero_x=1240, feet=1380, scale=3.4, face=dict(lx=-0.6, ly=0.1, brow=-13))
    finish(c)
    brush_title(c, ['WILL', 'YOU?'], 70, 290, 250, gap=0.98)


VARIANTS = {'a': variant_a, 'b': variant_b}


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {k: render(fn, out_dir / f'thumbnail_{k}.png') for k, fn in VARIANTS.items()}
    main = out_dir / 'thumbnail.png'
    main.write_bytes(paths['a'].read_bytes())
    return main


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
