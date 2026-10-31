"""SHOT 11 (14.4-16.5 s, 63 frames @30fps) - "and the skin crumples into wrinkles."
Outside again, on the studio blue: close on the pad of his fingertip, the smooth skin crumples
into deep wrinkles in a couple of seconds, like a time-lapse. 100 mm, a slow push, then a
crash zoom and a short shake on "wrinkles".

Run in a NEW Blender file:  blender -b -P shot11_crumple.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import os
import sys

ROOT = os.environ.get("WRINKLES_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes"),
          os.path.join(ROOT, "..", "sneeze", "scenes")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Vector

import hand_set as HS
import sky_set as SKY
import vfx_kit as V
import wrinkles as WR

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 63
LENS = 100
CRUMPLE = [(1, 0.0), (6, 0.04), (38, 1.0)]          # smooth to deep wrinkles
ZOOM = (39, 44)                                     # crash zoom on "wrinkles"


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hs = HS.build(wrinkled=0.0)
    WR.key(hs["hero"], CRUMPLE)
    pad, n = hs["tips"][3]                                          # the middle fingertip
    up = hs["up"]
    view = (n * 1.0 - hs["along"] * 0.55 + hs["along"].cross(up).normalized() * 0.25).normalized()
    aim = pad - n * 0.002
    c0, c1, c2, c3 = (aim + view * d for d in (0.15, 0.13, 0.085, 0.08))
    r = V.camera_rig("Cam_Shot11", lens=LENS, fstop=11.0)
    V.cam_keys(r, [(1, c0, aim, LENS), (ZOOM[0], c1, aim, LENS), (ZOOM[1], c2, aim, LENS), (N, c3, aim, LENS)])
    V.handheld(r, amount=0.00025, aim_amount=0.0002)
    V.shake(r, ZOOM[1] - 1, ZOOM[1] + 6, strength=0.0009, scale=1.3)
    SKY.studio(c0, aim, LENS)
    SKY.lights(aim, c0, SKY.view_dir(c0, aim, LENS), scale=0.3)
    HS.catch_light(pad, n, c0, dist=0.4, size=0.08, power=4.0)     # a wet sheen on the pad
    V.compositor(glow=0.25, threshold=1.0, dispersion=0.005)
    if PREVIEW:
        V.fast_preview(samples=24)
    return hs


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
