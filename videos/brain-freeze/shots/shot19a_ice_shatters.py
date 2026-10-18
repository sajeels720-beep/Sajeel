"""SHOT 19a (34.2-35.4 s, 36 frames @30fps) - "that isn't frozen"
The ice on the brain shatters: crystal clusters burst outward and spin away, the frost melts
back in a flash and a healthy pink brain is left. Small pull-back.
"""
import math
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "shots"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
import numpy as np
from mathutils import Vector

import character as C
import claude_sculpt_kit as K
import shot03_perfect as S03
import shot06_brain_freeze as S06
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.2
N = 36
BREAK = 6


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    relief = {"eyeBlinkLeft": 0.0, "eyeBlinkRight": 0.0, "browInnerUp": 0.6, "browOuterUpLeft": 0.5,
              "browOuterUpRight": 0.5, "mouthSmileLeft": 0.25, "mouthSmileRight": 0.25}
    hero, cut, clusters = S06.build_frozen_head(frozen=True, face=relief)
    frost = cut["brain_mat"].node_tree.nodes["Frost"].outputs[0]
    V.animate_socket(frost, [(1, 0.2), (BREAK, 0.2), (BREAK + 8, 0.0)])
    centre = cut["top"] - Vector((0, 0, 0.04))
    rng = np.random.default_rng(9)
    for ob, base, _ in clusters:                                   # burst outward and tumble away
        out = (base - centre).normalized() + Vector((0, 0, 0.6))
        dist = rng.uniform(0.12, 0.3)
        V.key(ob, "location", [(BREAK, tuple(ob.location)), (BREAK + 18, tuple(ob.location + out * dist))],
              "QUAD", "EASE_OUT")
        rot = Vector(rng.uniform(-4, 4, 3))
        V.key(ob, "rotation_euler", [(BREAK, (0, 0, 0)), (BREAK + 18, tuple(rot))], "QUAD", "EASE_OUT")
        V.key(ob, "scale", [(BREAK, (1, 1, 1)), (BREAK + 10, (0.8, 0.8, 0.8)), (BREAK + 18, (0.001,) * 3)],
              "QUAD", "EASE_IN")
    flash = cut["brain_mat"].node_tree.nodes["Glow"].outputs[0]    # a quick warm flash as the ice breaks
    V.animate_socket(flash, [(1, 0.0), (BREAK, 0.0), (BREAK + 2, 1.5), (BREAK + 10, 0.0)])
    top = cut["top"]
    S03.sun_rim_lights(top, power_key=55)
    r = V.camera_rig("Cam_Shot19a", lens=50, fstop=4.0)
    aim = top + Vector((0, -0.01, -0.035))
    V.cam_keys(r, [(1, aim + K.look_dir(-20, 26) * 0.52, aim, 50), (N, aim + K.look_dir(-16, 22) * 0.66, aim, 50)])
    V.handheld(r, amount=0.0015, aim_amount=0.001)
    V.shake(r, BREAK, BREAK + 6, strength=0.004)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 6, 8))
    return {"hero": hero}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
