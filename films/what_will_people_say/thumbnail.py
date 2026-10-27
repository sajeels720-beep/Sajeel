"""YouTube thumbnail: the hero frozen in a spotlight, a sea of red eyes, two big words."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import skia  # noqa: E402

from common import HERO_BEANIE, STAND_HIP, play_guitar  # noqa: E402
from engine.core import H, W, hrange  # noqa: E402
from engine.draw import col, cone, light_pool, paint, text, vignette  # noqa: E402
from engine.fx import eye_field  # noqa: E402
from engine.props import stage_floor  # noqa: E402

TEXT = 'THEY’RE WATCHING.'


def draw(c):
    c.clear(col('#050507'))
    floor = 975
    stage_floor(c, -100, W + 100, floor, 60)
    cone(c, (1230, -120), 70, floor, 330, '#E8EEFF', 0.2, soft=40)
    light_pool(c, 1230, floor, 420, 70, '#E8EEFF', 0.5)
    eyes = []
    i = 0
    while len(eyes) < 46 and i < 4000:
        x, y = hrange(-40, W + 40, i, 5), hrange(300, H + 40, i, 6)
        i += 1
        if 860 < x < 1560 and y < 1060:
            continue
        if any(abs(x - ex) < 150 and abs(y - ey) < 90 for ex, ey, *_ in eyes):
            continue
        s = 70 + (y - 300) * 0.09
        eyes.append((x, y, s, 1.0, hrange(14, 26, i, 7), 1.0))
    eye_field(c, eyes, 0.0)
    gp, mid, _ = play_guitar(0.0, seated=False, strum=False, fret_shift=False)
    HERO_BEANIE.draw(c, dict(x=1230, y=floor - STAND_HIP * 1.95, scale=1.95, facing=1, turn=0.08,
                             eyes='wide', lx=-0.6, ly=0.1, sweat=1.3, brow=-20, mopen=0.22, mwide=0.8,
                             hb=-6, kb=4, hf=7, kf=4, **gp), {'mid': mid})
    vignette(c, W, H, 0.55)
    text(c, TEXT, W / 2, 205, 168, 'Fredoka-700', 'white', outline='#000000', outline_w=16)
    text(c, TEXT, W / 2, 205, 168, 'Fredoka-700', 'white')


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    surface = skia.Surface(W, H)
    draw(surface.getCanvas())
    img = surface.makeImageSnapshot()
    big = out_dir / 'thumbnail_1920.png'
    img.save(str(big), skia.kPNG)
    small = img.resize(1280, 720, skia.SamplingOptions(skia.CubicResampler.Mitchell()))
    path = out_dir / 'thumbnail.png'
    small.save(str(path), skia.kPNG)
    return path


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
