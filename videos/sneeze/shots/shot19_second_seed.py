"""SHOT 19 (30.0-32.2 s, 66 frames @30fps) - "So next time you feel one coming,"
Back to her on the studio blue, still holding it in: another seed breaks off the dandelion in
front of her and drifts onto her nose; her eyes cross down at it, her nose twitches and her
face scrunches up, "ahh...". The dandelion is a soft blur in the foreground. 50 mm, slow
push-in. Her performance for shots 19-22 is one take (scenes/release.py).

Run in a NEW Blender file:  blender -b -P shot19_second_seed.py -a
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
LENS = 50


def build():
    V.start_fresh()
    lo, hi = REL.SHOTS["19"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    st = REL.stage("19")
    if PREVIEW:
        V.fast_preview(samples=24)
    nose = st["nose0"]
    r = V.camera_rig("Cam_Shot19", lens=LENS, fstop=4)
    a0 = nose + Vector((0.0, 0.01, 0.0))
    a1 = nose + Vector((0.0, 0.01, 0.004))
    c0 = a0 + K.look_dir(-20, 2) * 0.62
    c1 = a1 + K.look_dir(-16, 1) * 0.5
    V.cam_keys(r, [(1, c0, a0, None), (n, c1, a1, None)])
    V.handheld(r, amount=0.0008, aim_amount=0.0006)
    focus = V.link(bpy.data.objects.new("Focus_Shot19", None), V.collection("CAMERA"))
    focus.location = nose + Vector((0.0, 0.01, 0.0))
    r["cam"].data.dof.focus_object = focus
    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.45)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
