"""SHOT 08 (10.3-11.8 s, 45 frames @30fps) - "which squeeze the blood vessels"
The pulse from shot 07 reaches the web of red blood vessels: the fine nerve fibres wound around
the main vessel light up, and the vessels clamp down and squeeze narrow while the red blood
cells inside slow to a trickle. Crash zoom and a short shake on "squeeze". 35 mm.

Run in a NEW Blender file:  blender -b -P shot08_squeeze.py -a
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
N = 45
LENS = 35
OFF = 33                          # shot 07's length: its pulse carries on here
GO = (7 - OFF, 40 - OFF)          # ...and reaches the vessels on frame 7
LIGHT = (5, 12)                   # the fibres around the vessel light up
SQUEEZE = (8, 22)                 # the vessels clamp down ("squeeze")
ZOOM = (8, 12)
TIGHT = 0.48                      # how narrow they get


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    FI.world()
    nv = FI.build_nerve()
    ves = FI.build_vessels()
    fib = FI.wrap_fibres(ves, nv, squeezed=TIGHT)
    FI.pulse_track(nv, *GO)
    V.animate_socket(nv["glow"], [(1, 5.0), (GO[1] + 2, 5.0), (GO[1] + 10, 0.0)])      # the pulse passes into the fibres
    fmat = FI.nerve_material("Nerve_Fibre")
    for o in fib:
        V.assign(o, fmat)
    V.animate_socket(V._inp(V.bsdf(fmat), "Emission Strength"), [(1, 0.25), (LIGHT[0], 0.25), (LIGHT[1], 2.6), (N, 1.1)])
    fib_pts = []
    for o in fib:
        pts = o.data.splines[0].points
        fib_pts += [Vector(pts[i].co[:3]) for i in range(0, len(pts), 12)]
    FI.sparks(fib_pts, LIGHT[0], LIGHT[1] + 4, count=22, reach=0.12, seed=8)
    FI.squeeze(ves, [(SQUEEZE[0], 1.0), (SQUEEZE[1], TIGHT)], extra=fib)
    thick = lambda f: 1.0 - (1.0 - TIGHT) * FI.smooth((f - SQUEEZE[0]) / (SQUEEZE[1] - SQUEEZE[0]))
    flow = lambda f: 0.004 + 0.026 * (1.0 - FI.smooth((f - SQUEEZE[0]) / 16))
    FI.blood(ves, flow, thick, (1, N))
    # camera: the nerve coming down onto the main vessel; a crash zoom and a shake on "squeeze"
    j = Vector(FI.JOIN)
    aim0, aim1 = j + Vector((0.0, 0.25, -0.12)), j + Vector((0.0, 0.22, -0.12))
    c0, c1, c2 = j + Vector((0.25, -2.0, 0.32)), j + Vector((0.15, -1.3, 0.22)), j + Vector((0.13, -1.16, 0.2))
    r = V.camera_rig("Cam_Shot08", lens=LENS, fstop=2.0)
    V.cam_keys(r, [(1, c0, aim0, LENS), (ZOOM[0], c0.lerp(c1, 0.06), aim0, LENS), (ZOOM[1], c1, aim1, LENS),
                   (N, c2, aim1, LENS)])
    V.handheld(r, amount=0.003, aim_amount=0.002)
    V.shake(r, ZOOM[1] - 1, ZOOM[1] + 7, strength=0.018, scale=1.3)
    FI.background(aim0, (0.0, 1.0, 0.0))
    SKY.tissue_lights(aim0, c0, scale=1.5)
    V.compositor(glow=0.6, threshold=0.9, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return ves


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
