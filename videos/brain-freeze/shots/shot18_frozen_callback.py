"""SHOT 18 (32.0-34.2 s, 66 frames @30fps) - "leaving you with a frozen brain"
Callback to shot 06: the brain sits fully frozen and spiky with ice in the open head, cold
light, slow orbit from the other side.
"""
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "shots"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Vector

import claude_sculpt_kit as K
import shot03_perfect as S03
import shot06_brain_freeze as S06
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 2.2
N = 66


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hero, cut, clusters = S06.build_frozen_head(frozen=True)
    top = cut["top"]
    S03.sun_rim_lights(top, power_key=45)
    cold = bpy.data.lights.new("Cold_Top_lgt", "AREA")
    cold.energy, cold.size, cold.color = 70, 0.5, (0.55, 0.75, 1.0)
    ob = V.link(bpy.data.objects.new("Cold_Top_lgt", cold), V.collection("LIGHTS"))
    ob.location = top + Vector((-0.15, -0.2, 0.55))
    K._aim(ob, top)
    r = V.camera_rig("Cam_Shot18", lens=50, fstop=4.0)
    aim = top + Vector((0, -0.01, -0.03))
    V.cam_keys(r, [(1, aim + K.look_dir(30, 30) * 0.6, aim, 50), (N, aim + K.look_dir(8, 24) * 0.55, aim, 50)])
    V.handheld(r, amount=0.0015, aim_amount=0.001)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 6, 8))
    return {"hero": hero}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
