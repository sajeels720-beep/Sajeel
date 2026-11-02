"""SHOT 03 (2.2-4.2 s, 60 frames @30fps) - "so you pinch your nose, shut your mouth,"
Medium close-up on the studio blue: "ahh... ahh...", her head tips back and her mouth opens,
the seed flutters off her nose, then her right hand snaps up and pinches her nose shut and her
lips press together. 50 mm, slow orbit to the left. Her acting is shared with shots 04-05
(scenes/hold_in.py), so it carries across the cuts.

Run in a NEW Blender file:  blender -b -P shot03_pinch.py -a
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
LENS = 50


def build():
    V.start_fresh()
    n = HOLD.SHOTS["03"][1] - HOLD.SHOTS["03"][0] + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    take = HOLD.perform("03")
    nose, _ = HOLD.nose_at(take["hero"], 1)

    # camera: head and shoulders, her right hand rising from the bottom of frame
    r = V.camera_rig("Cam_Shot03", lens=LENS, fstop=5.6)
    a0 = nose + Vector((0.0, 0.0, -0.035))
    a1 = nose + Vector((0.0, 0.0, -0.03))
    c0 = a0 + K.look_dir(-18, 4) * 0.60
    c1 = a1 + K.look_dir(-34, 2) * 0.56
    V.cam_keys(r, [(1, c0, a0, LENS), (n, c1, a1, LENS)])
    focus = V.link(bpy.data.objects.new("Focus_Shot03", None), V.collection("CAMERA"))
    focus.location = nose + Vector((0.0, 0.02, 0.0))
    r["cam"].data.dof.focus_object = focus
    V.handheld(r, amount=0.0012, aim_amount=0.0008)

    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.6)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
