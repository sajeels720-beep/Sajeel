"""SHOT 07 (9.2-10.3 s, 33 frames @30fps) - "sets off your nerves,"
Inside his fingertip, on the warm tissue backdrop: drops of water reach a nerve ending just
under the skin (a spray of fine twigs with round tips), it sparks, and a bright pulse races
down the yellow nerve towards the web of blood vessels below; the camera tracks beside the
pulse. 35 mm. The nerve, the vessels and the pulse's timing are shared with shot 08.

Run in a NEW Blender file:  blender -b -P shot07_spark.py -a
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
import numpy as np
from mathutils import Vector

import finger_inside as FI
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 33
LENS = 35
TOUCH = 6                     # the water reaches the nerve's tips: it sparks
GO = (7, 40)                  # the pulse leaves the ending ... reaches the vessels (in shot 08)


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    FI.world()
    nv = FI.build_nerve()
    ves = FI.build_vessels()
    FI.wrap_fibres(ves, nv)
    u = FI.pulse_track(nv, *GO)
    FI.water_beads(nv["tips"][:4], 1, travel=TOUCH - 1)
    FI.sparks(nv["tips"], TOUCH, TOUCH + 8)
    V.animate_socket(nv["glow"], [(1, 0.0), (TOUCH, 0.0), (TOUCH + 1, 7.0), (TOUCH + 5, 5.0), (N, 5.0)])
    # camera: beside the ending as it sparks, then racing beside the pulse, a little behind it
    P, L = nv["path"], nv["lengths"]
    d = Vector(P[-1] - P[0]).normalized()
    side = Vector((d.y, -d.x, 0.0)).normalized()
    if side.y > 0:
        side = -side                                            # stay on the viewer's side (-Y)
    off = (side + Vector((0.0, 0.0, 0.25))).normalized()
    tips = Vector(np.mean([tuple(t) for t in nv["tips"]], axis=0))
    r = V.camera_rig("Cam_Shot07", lens=LENS, fstop=2.0)
    keys = []
    for f in range(0, N + 2):
        w = FI.smooth((f - TOUCH) / 9)
        aim = tips.lerp(Vector(FI.point_at(P, L, u(f) + 0.04)), w)
        keys.append((f, aim + off * (1.05 - 0.15 * w) - d * 0.22 * w, aim, LENS))
    V.cam_keys(r, keys, "LINEAR")
    V.handheld(r, amount=0.003, aim_amount=0.002)
    V.shake(r, TOUCH, TOUCH + 5, strength=0.012, scale=1.2)
    FI.background(tips, (-off.x, -off.y, -off.z))
    SKY.tissue_lights(tips, keys[0][1], scale=1.5)
    V.compositor(glow=0.6, threshold=0.9, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return nv


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
