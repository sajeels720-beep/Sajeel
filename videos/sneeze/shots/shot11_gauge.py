"""SHOT 11 (16.6-18.2 s, 48 frames @30fps) - "jumps about twenty times higher."
A brass pressure gauge on the studio blue: the needle trembles near 1, then slams round past
20 into the red zone, the glass cracks with the force, the camera crash-zooms in on the
needle and shakes; the needle bounces and settles, quivering, on 20 ("x NORMAL").

Run in a NEW Blender file:  blender -b -P shot11_gauge.py -a
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
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import gauge_set as G
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 48
SLAM = 12                                        # the needle hits and the glass cracks
NEEDLE = [(1, 1.0), (5, 1.6), (8, 1.3), (10, 2.4), (SLAM, 24.4), (SLAM + 2, 19.2), (SLAM + 4, 22.3), (SLAM + 6, 20.2),
          (SLAM + 8, 21.6), (SLAM + 11, 20.7), (SLAM + 15, 21.2), (N, 21.0)]   # settles just past 20, the "20" in view
LENS = 85


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    g = G.build()
    G.key_needle(g["needle"], NEEDLE, jitter=0.6)
    tip = G.dial_point(20.0, 0.036)
    impact = (tip.x + 0.004, tip.z + 0.006)                      # the glass gives way near the needle's tip
    G.cracks(g, impact, SLAM, np.random.default_rng(11))
    if PREVIEW:
        V.fast_preview(samples=24)

    # camera: the whole gauge, then a crash zoom onto the needle in the red zone
    r = V.camera_rig("Cam_Shot11", lens=LENS, fstop=5.6)
    a0 = Vector((0.0, 0.0, -0.03))                               # the gauge high, its pipe running down
    c0 = a0 + K.look_dir(-12, 6) * 0.56
    a1 = Vector((tip.x * 0.75, 0.0, tip.z * 0.75 - 0.002))
    c1 = a1 + K.look_dir(-14, 7) * 0.25
    c_pre = a0 + K.look_dir(-12, 6) * 0.53
    V.cam_keys(r, [(1, c0, a0, None), (SLAM - 1, c_pre, a0, None), (SLAM + 3, c1, a1, None),
                   (N, a1 + K.look_dir(-14, 7) * 0.235, a1, None)])
    for fc in V.fcurves(r["rig"]) + V.fcurves(r["aim"]):          # the crash zoom snaps in, then eases
        for kp in fc.keyframe_points:
            if int(round(kp.co[0])) == SLAM - 1:
                kp.interpolation = "QUAD"
                kp.easing = "EASE_IN"
    V.handheld(r, amount=0.0006, aim_amount=0.0004)
    V.shake(r, SLAM, SLAM + 9, strength=0.0025, scale=1.3)
    focus = V.link(bpy.data.objects.new("Focus_Shot11", None), V.collection("CAMERA"))
    focus.location = Vector((tip.x * 0.6, G.GLASS_Y[1], tip.z * 0.6))
    r["cam"].data.dof.focus_object = focus

    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.18, key=1.2)
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    return g


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
