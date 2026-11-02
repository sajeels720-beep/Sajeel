"""SHOT 04 (4.2-6.3 s, 63 frames @30fps) - "and hold it in."
Close-up: she holds it, nose pinched and lips pressed, the pressure building; then the sneeze
hits inside (frame 12): a muffled jolt through her body, her cheeks balloon, her eyes pop
wide and her face flushes red. 85 mm push-in, a short shake on the jolt. Her acting is shared
with shots 03 and 05 (scenes/hold_in.py).

Run in a NEW Blender file:  blender -b -P shot04_hold.py -a
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
import hold_in as HOLD
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["04"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    take = HOLD.perform("04")
    anchor, _ = HOLD.nose_at(take["hero"], 60 - take["off"])
    hit = HOLD.HIT - take["off"]

    r = V.camera_rig("Cam_Shot04", lens=HOLD.CU_LENS, fstop=8)
    a0 = anchor + HOLD.CU_AIM + Vector((0.0, 0.0, -0.004))
    a1 = anchor + HOLD.CU_AIM
    c0 = a0 + K.look_dir(-26, 4) * 0.70
    c1 = a1 + K.look_dir(*HOLD.CU_LOOK) * HOLD.CU_END_DIST
    V.cam_keys(r, [(1, c0, a0, HOLD.CU_LENS), (n, c1, a1, HOLD.CU_LENS)])
    focus = V.link(bpy.data.objects.new("Focus_Shot04", None), V.collection("CAMERA"))
    focus.location = anchor + Vector((0.0, 0.012, 0.01))              # between the nose and the eyes
    r["cam"].data.dof.focus_object = focus
    V.handheld(r, amount=0.0008, aim_amount=0.0006)
    V.shake(r, hit, hit + 9, strength=0.004, scale=1.4)              # the muffled jolt

    SKY.studio(c0, a0, HOLD.CU_LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, HOLD.CU_LENS), scale=0.45)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
