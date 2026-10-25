"""SHOT 20 (32.2-33.6 s, 42 frames @30fps) - "just let it out."
She lets go of her nose (her hand drops to her side) and tips her head back to wind up the
sneeze, "ahh... ahh...", the seed still on her nose. 35 mm, a slight pull-back.

Run in a NEW Blender file:  blender -b -P shot20_let_go.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import os
import sys

ROOT = os.environ.get("SNEEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Vector

import claude_sculpt_kit as K
import release as REL
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 35


def build():
    V.start_fresh()
    lo, hi = REL.SHOTS["20"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    st = REL.stage("20")
    if PREVIEW:
        V.fast_preview(samples=24)
    nose = st["nose0"]
    r = V.camera_rig("Cam_Shot20", lens=LENS, fstop=4)
    a0 = nose + Vector((0.0, 0.03, -0.1))
    a1 = nose + Vector((0.0, 0.03, -0.08))
    c0 = a0 + K.look_dir(-24, 3) * 0.78
    c1 = a1 + K.look_dir(-26, 4) * 0.9
    V.cam_keys(r, [(1, c0, a0, None), (n, c1, a1, None)])
    V.handheld(r, amount=0.0008, aim_amount=0.0006)
    focus = V.link(bpy.data.objects.new("Focus_Shot20", None), V.collection("CAMERA"))
    focus.location = nose + Vector((0.0, 0.01, 0.0))
    r["cam"].data.dof.focus_object = focus
    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.6)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
