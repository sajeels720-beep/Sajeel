"""YouTube thumbnails for 'He's Waiting.' in the house style (studio/THUMBNAILS.md).

A: 2:47 AM. The old man sits in the dark at the foot of the bed, big and quiet, his pocket watch in his hands;
   behind him, out of focus, the boy scrolls, his face lit by the phone. "HE'S WAITING."
B: the old man alone, looking straight at the viewer, the watch held up. "HE'S YOU."
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import skia  # noqa: E402

from common import HERO, MUSTARD, old_man, pocket_watch, scroll_screen  # noqa: E402
from engine.core import H, W  # noqa: E402
from engine.draw import col, light_pool, oval, paint, rrect, vignette  # noqa: E402
from engine.rig import BASE_POSE, solve  # noqa: E402
from engine.thumbkit import blurred, brush_title, haze, render, shade_head  # noqa: E402

V = 0.3     # how worn out the old man looks


def night_room(c, moon_x=1560):
    sh = skia.GradientShader.MakeLinear(points=[(0, 0), (0, H)], colors=[col('#141A2C'), col('#06070C')])
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#000000', shader=sh))

    def far():
        # the window and its moon behind him, the city asleep
        x, y, w, h = 1340, 90, 420, 470
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint('#0E1730'))
        for k in range(7):
            bx = x + k * 64
            bh = 70 + (k * 37) % 120
            c.drawRect(skia.Rect.MakeXYWH(bx, y + h - bh, 48, bh), paint('#070B16'))
            for r in range(3):
                if (k + r) % 3 == 0:
                    c.drawRect(skia.Rect.MakeXYWH(bx + 14, y + h - bh + 14 + r * 22, 10, 12), paint('#F2C26B', 0.7))
        c.drawCircle(moon_x, 230, 120, paint('#9DB7FF', 0.25, blur=60, blend='add'))
        c.drawCircle(moon_x, 230, 46, paint('#EEF2FF'))
        c.drawCircle(moon_x + 18, 218, 40, paint('#0E1730'))
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint('#2E3346', stroke=22))
        c.drawLine(x + w / 2, y, x + w / 2, y + h, paint('#2E3346', stroke=14))
        # the bed: quilt and pillow, low on the left
        c.drawRect(skia.Rect.MakeLTRB(-50, 900, 1300, 1200), paint('#22324A'))
        c.drawRRect(rrect(60, 760, 360, 120, 50), paint('#3A4258'))
    blurred(c, 7, far)
    haze(c, 1380, -40, 1700, H, '#9DB7FF', 0.07)


def boy_in_bed(c, x=420, y=840, s=1.7, sigma=4.0):
    """The boy, half-reclined, his face lit by the phone; soft focus."""
    def draw():
        p = dict(x=x, y=y, rot=-68, facing=1, scale=s, turn=0.25, hb=24, kb=10, hf=30, kf=18, sb=40, eb=60,
                 tilt=-8, eye=0.75, bags=0.7, smile=0.05, ly=-0.5, lx=0.3, reflect=('#9CD8FF', 0.9))
        from common import to_local, to_world
        phone = (x - 150, y - 300)
        p['hand_f'] = to_local(p, (phone[0] + 4, phone[1] + 50))
        p['ik_f'] = 1.0
        HERO.draw(c, p)
        quilt = skia.Path()
        quilt.moveTo(x - 140, y + 400)
        quilt.lineTo(x - 140, y - 40)
        quilt.cubicTo(x + 60, y - 120, x + 260, y - 60, x + 420, y - 90)
        quilt.cubicTo(x + 560, y - 115, x + 700, y - 40, x + 980, y - 30)
        quilt.lineTo(x + 980, y + 400)
        quilt.close()
        c.drawPath(quilt, paint('#2B4366'))
        c.drawPath(quilt, paint('outline', stroke=6))
        c.save()
        c.translate(*phone)
        c.rotate(18)
        c.scale(s, s)
        c.drawRRect(rrect(-22, -41, 44, 82, 8), paint('#16171C'))
        c.save()
        c.clipRRect(rrect(-19, -37, 38, 74, 5))
        c.translate(-19, -37)
        scroll_screen(c, 38, 74, 3.0, swipes=[1.0, 2.0, 2.9])
        c.restore()
        c.restore()
        light_pool(c, phone[0] + 20, phone[1] + 120, 420, 380, '#9CD8FF', 0.45)
    blurred(c, sigma, draw)


def old_man_big(c, hx=1360, hy=470, s=3.0, look_viewer=False, watch_up=False):
    """The old man, sitting, a third of the frame tall; sad and patient; the watch in his hands."""
    who = old_man(V)
    hip = (hx + (0 if look_viewer else 40), hy + 156 * s + 40)
    pose = dict(BASE_POSE)
    pose.update(x=hip[0], y=hip[1], scale=s, facing=-1, turn=0.42 if not look_viewer else 0.0, lean=8, tilt=-4,
                eye=0.82, bags=1.1, brow=-15, smile=-0.18, mwide=0.8, wet=1.0, lx=0.9 if not look_viewer else 0.0,
                ly=-0.15 if not look_viewer else 0.0, hb=80, kb=60, hf=84, kf=70)
    from common import to_local
    if not watch_up:
        watch_at = (hx - 150, hy + 330)
        pose['hand_f'] = to_local(pose, (watch_at[0] + 30, watch_at[1] + 40))
        pose['hand_b'] = to_local(pose, (watch_at[0] - 20, watch_at[1] + 46))
        chain = (watch_at[0] + 180, watch_at[1] - 40)
    else:
        hold = (hx - 200, hy + 250)
        watch_at = (hold[0], hold[1] + 170)
        pose['hand_f'] = to_local(pose, hold)
        pose['hand_b'] = to_local(pose, (hold[0] + 60, hold[1] + 200))
        chain = hold
    pose['ik_f'] = pose['ik_b'] = 1.0
    j = who.draw(c, pose)
    head = (hip[0] - j['head'][0] * s, hip[1] + j['head'][1] * s)
    R = who.look.head_r * s
    shade_head(c, head[0], head[1], R, light=(0.7, -0.7), rim='#C9D6FF', rim_a=0.16)
    # the watch, the brightest gold in the frame
    pocket_watch(c, watch_at[0], watch_at[1], 58, 0.4, open_lid=False, glow=0.55, chain=chain)
    if watch_up:
        hand = (hx - 200, hy + 250)
        c.drawCircle(hand[0], hand[1], 34, paint(who.look.skin))
        c.drawCircle(hand[0], hand[1], 34, paint('outline', stroke=12))
    c.drawCircle(watch_at[0], watch_at[1], 70, paint('#FFD98A', 0.18, blur=30, blend='add'))
    # a soft key light on his face from the phone, a cold rim from the window
    light_pool(c, head[0] - R * 0.4, head[1], R * 1.6, R * 1.6, '#BFE6FF', 0.1)
    return head, R


def variant_a(c):
    night_room(c)
    boy_in_bed(c)
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#05060A', 0.12))
    old_man_big(c)
    vignette(c, W, H, 0.55)
    brush_title(c, ['HE’S', 'WAITING.'], 70, 250, 220, gap=0.97)


def variant_b(c):
    night_room(c, moon_x=1700)
    boy_in_bed(c, x=360, y=900, s=1.4, sigma=7.0)
    c.drawRect(skia.Rect.MakeWH(W, H), paint('#05060A', 0.2))
    old_man_big(c, hx=1250, hy=520, s=3.25, look_viewer=True, watch_up=True)
    vignette(c, W, H, 0.55)
    brush_title(c, ['HE’S', 'YOU.'], 70, 270, 250, gap=0.98)


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
