"""Build a film end to end.

    .venv/bin/python studio/make_film.py films/what_will_people_say all
    .venv/bin/python studio/make_film.py films/what_will_people_say sheet 0 22 1.5
    .venv/bin/python studio/make_film.py films/what_will_people_say still 15.2

Stages: audio (score, effects, whispers, mix), video (picture), thumb, mux, all.
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'studio'))

from engine import render  # noqa: E402


def load(film_dir: Path):
    sys.path.insert(0, str(film_dir))
    film_mod = importlib.import_module('film')
    return film_mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('film_dir')
    ap.add_argument('stage', choices=['still', 'sheet', 'video', 'audio', 'thumb', 'mux', 'all'])
    ap.add_argument('args', nargs='*', type=float)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()

    film_dir = (ROOT / a.film_dir).resolve() if not Path(a.film_dir).is_absolute() else Path(a.film_dir)
    out_dir = ROOT / 'output' / film_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    mod = load(film_dir)
    t_start = time.time()

    if a.stage == 'still':
        film = mod.build()
        for T in a.args:
            path = out_dir / 'stills' / f'still_{T:07.2f}.png'
            path.parent.mkdir(exist_ok=True)
            render.still(film, T, path)
            print(path)
    elif a.stage == 'sheet':
        film = mod.build()
        t0, t1, step = (a.args + [0, film.duration, 2.0])[:3] if a.args else (0, film.duration, 2.0)
        times = []
        T = t0
        while T < t1 - 1e-6:
            times.append(round(T, 3))
            T += step
        path = Path(a.out) if a.out else out_dir / 'sheets' / f'sheet_{t0:06.1f}_{t1:06.1f}.png'
        path.parent.mkdir(exist_ok=True)
        render.contact_sheet(film, times, path)
        print(path)
    if a.stage in ('audio', 'all'):
        sys.path.insert(0, str(film_dir))
        sound = importlib.import_module('sound')
        print('audio ->', sound.build(out_dir))
    if a.stage in ('video', 'all'):
        film = mod.build()
        t0 = a.args[0] if a.args else 0.0
        t1 = a.args[1] if len(a.args) > 1 else None
        print('video ->', render.render(film, out_dir / 'picture.mp4', workers=a.workers, t0=t0, t1=t1))
    if a.stage in ('thumb', 'all'):
        thumb = importlib.import_module('thumbnail')
        print('thumbnail ->', thumb.build(out_dir))
    if a.stage in ('mux', 'all'):
        final = out_dir / f'{film_dir.name}.mp4'
        print('final ->', render.mux(out_dir / 'picture.mp4', out_dir / 'audio' / 'mix.wav', final))
    print(f'done in {time.time() - t_start:.0f}s')


if __name__ == '__main__':
    main()
