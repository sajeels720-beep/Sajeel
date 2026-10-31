"""SHOT 13 (17.6-20.0 s, 72 frames @30fps) - "Scientists think wrinkles grip wet things better,"
Under the water: his wrinkly hand comes down to the glass marble lying on a tiled step, his
fingertips pinch it and lift it without slipping, up towards the bright surface. 50 mm, under
water beside the step, then following the hand up.

Run in a NEW Blender file:  blender -b -P shot13_grip.py -a
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

import closing_take as TAKE
import pool_set as PS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 50


def build():
    V.start_fresh()
    lo, hi = TAKE.SHOTS["13"]
    n, off = hi - lo + 1, lo - 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts, take = TAKE.pool_scene("13")
    m = TAKE.marble(take)
    rest = m["rest"]
    PS.step((rest.x + 0.03, rest.y - 0.06, 0.0), top=m["step_top"])
    PS.underwater_materials([bpy.data.materials["Marble_Glass"], bpy.data.materials["Marble_Swirl"]])
    PS.water_haze()
    # camera: low beside the step, looking at the marble as the hand comes down; then it rises
    # with the hand and tilts up towards the bright surface
    grab = TAKE.PINCH[1] - off
    keys = []
    for f in range(1, n + 1, 3):
        bpy.context.scene.frame_set(f)
        held = m["ob"].matrix_world.translation.copy()
        w = min(max((f - grab) / (n - grab), 0.0), 1.0)
        aim = rest.lerp(held, 0.6 * w) + Vector((0.0, 0.0, 0.025 + 0.03 * w))           # the hand rises out of frame
        cam = rest + Vector((0.2, -0.22, 0.04)) + Vector((0.0, 0.02, 0.12)) * w
        keys.append((f, cam, aim, LENS))
    r = V.camera_rig("Cam_Shot13", lens=LENS, fstop=4.0)
    V.cam_keys(r, keys)
    V.handheld(r, amount=0.0015, aim_amount=0.0012)
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
