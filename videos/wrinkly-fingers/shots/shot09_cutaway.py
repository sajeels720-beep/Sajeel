"""SHOT 09 (11.8-13.1 s, 39 frames @30fps) - "under your skin."
His fingertip cut in half on the studio blue, like a textbook cutaway: the skin, the yellow
fatty pad, the bone, the nail, and the blood vessels in the pad. The vessels narrow and drain,
and their red fades. 85 mm, a slow orbit.

Run in a NEW Blender file:  blender -b -P shot09_cutaway.py -a
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

import claude_sculpt_kit as K
import cutaway as CA
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 39
LENS = 85
DRAIN = (6, 30)
AIM = Vector((0.03, 0.0, 0.3))                     # the middle of the fingertip (it stands at the origin)


def cam(az, el, dist):
    return AIM + K.look_dir(az, el) * dist


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts = CA.build()
    CA.drain(parts, *DRAIN)
    c0, c1 = cam(-24, 8, 2.45), cam(-10, 6, 2.3)
    r = V.camera_rig("Cam_Shot09", lens=LENS, fstop=8.0)
    V.cam_keys(r, [(1, c0, AIM, LENS), (N, c1, AIM, LENS)])
    V.handheld(r, amount=0.0012, aim_amount=0.0008)
    SKY.studio(c0, AIM, LENS)
    SKY.lights(AIM, c0, SKY.view_dir(c0, AIM, LENS), scale=0.8)
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
