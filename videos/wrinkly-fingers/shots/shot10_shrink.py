"""SHOT 10 (13.1-14.4 s, 39 frames @30fps) - "Your fingertips shrink,"
Closer on the cutaway of his fingertip (the vessels already drained): the fatty pad shrinks
inwards, and the skin on top of it, now too big for it, buckles into folds. 100 mm, a push in
on the pad.

Run in a NEW Blender file:  blender -b -P shot10_shrink.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import os
import sys

ROOT = os.environ.get("WRINKLES_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes"),
          os.path.join(ROOT, "..", "sneeze", "scenes"), os.path.join(ROOT, "shots")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Vector

import cutaway as CA
import shot09_cutaway as S09
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 39
LENS = 100
SHRINK = (4, 30)
PAD = Vector((0.17, 0.0, 0.3))                    # the middle of the pad (the fingertip stands at the origin)


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts = CA.build()
    CA.drain(parts, -10, -1)                       # drained in shot 09
    CA.shrink(parts, [(SHRINK[0], 0.0), (SHRINK[1], 1.0)])
    c0 = PAD + S09.K.look_dir(-12, 5) * 1.75
    c1 = PAD + S09.K.look_dir(-8, 4) * 1.45
    r = V.camera_rig("Cam_Shot10", lens=LENS, fstop=8.0)
    V.cam_keys(r, [(1, c0, PAD, LENS), (N, c1, PAD + Vector((0.0, 0.0, -0.01)), LENS)])
    V.handheld(r, amount=0.001, aim_amount=0.0007)
    SKY.studio(c0, S09.AIM, LENS)
    SKY.lights(S09.AIM, c0, SKY.view_dir(c0, S09.AIM, LENS), scale=0.8)
    V.compositor(glow=0.25, threshold=1.0, dispersion=0.005)
    if PREVIEW:
        V.fast_preview(samples=24)
    return parts


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
