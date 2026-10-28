"""YouTube thumbnails for '90 Days Left.' in the house style (studio/THUMBNAILS.md).

A: night, at his desk, the phone in his hand glowing red with the shadow's eyes; the books loom behind him.
B: the same scene, close, with a single word.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import skia  # noqa: E402

from common import HERO, phone_eyes  # noqa: E402
from engine.core import H, W  # noqa: E402
from engine.draw import col, light_pool, paint, vignette  # noqa: E402
from engine.home import book_mountain, book_pile, calendar  # noqa: E402
from engine.props import phone  # noqa: E402
from engine.thumbkit import blurred, brush_title, haze, render, shade_head  # noqa: E402


def scene(c, hero_x=1240, scale=3.0, desk_y=930):
    # the room at night: cool moonlight from the left, the books towering behind him
    shader = skia.GradientShader.MakeLinear(points=[(0, 0), (0, H)], colors=[col('#121725'), col('#07080C')])
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#000000', shader=shader))
    haze(c, 120, -40, 420, H, '#9DB7FF', 0.07)

    def mountain():
        book_mountain(c, 520, desk_y + 40, 980, 900, seed=5, a=0.9)
        calendar(c, 1500, 140, 210, 240, crossed=0, circle_day=29)
    blurred(c, 7, mountain)
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#05060A', 0.45))
    light_pool(c, 1700, 520, 520, 460, 'warm', 0.16)

    # him at the desk, worried, looking down at the phone in his hand
    hip = (hero_x, desk_y + 120)
    hand = (hero_x - 300, desk_y - 70)
    pose = dict(x=hip[0], y=hip[1], scale=scale, facing=-1, turn=0.25, lean=10, tilt=8,
                hb=88, kb=88, hf=84, kf=84, eyes='dot', lx=0.75, ly=0.65, brow=-17, smile=-0.2, mwide=0.75,
                hand_f=((hip[0] - hand[0]) / scale, (hand[1] - hip[1]) / scale), hand_b=(60, -40))
    j = HERO.draw(c, pose)
    hx, hy = hip[0] - scale * j['head'][0], hip[1] + scale * j['head'][1]
    R = HERO.look.head_r * scale
    shade_head(c, hx, hy, R, light=(0.7, -0.5), rim='#FFE3B8', bounce='red', rim_a=0.18, bounce_a=0.22)
    # the phone: the shadow's eyes looking back at him, red light thrown up onto his face
    light_pool(c, hand[0], hand[1] - 120, 460, 400, 'red', 0.34)
    phone(c, hand[0] + 10, hand[1] - 60, 8, 3.1, glow=0.9, content=phone_eyes(1.0, 0.0, size=19))
    c.drawCircle(hand[0] + 40, hand[1] + 30, 40, paint('skin'))
    c.drawCircle(hand[0] + 40, hand[1] + 30, 40, paint('outline', stroke=6))
    # the desk edge and an out-of-focus pile of books in front
    c.drawRect(skia.Rect.MakeLTRB(0, desk_y, W, H), paint('#2A1D14'))
    c.drawRect(skia.Rect.MakeLTRB(0, desk_y, W, desk_y + 16), paint('#7A5638'))
    c.drawLine(0, desk_y, W, desk_y, paint('outline', stroke=6))
    blurred(c, 9, lambda: book_pile(c, 1780, desk_y + 30, 7, seed=4, width=(260, 320), thick=(46, 60)))
    vignette(c, W, H, 0.55)


def variant_a(c):
    scene(c)
    brush_title(c, ['90 DAYS', 'LEFT.'], 70, 250, 230, gap=0.98)


def variant_b(c):
    scene(c, hero_x=1180, scale=3.3)
    brush_title(c, ['TOMORROW.'], 70, 250, 220)


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
