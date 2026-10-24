"""SHOT 07 (9.9-11.8 s, 57 frames @30fps) - "out of your lungs super fast."
Inside the x-ray: her lungs keep squeezing and a bright blue blast of air streams out of
them, merges at the fork of the windpipe and rushes up it into her throat. The camera
tracks up beside the blast; the airway walls light up as it passes. Streaking comets of
air, motion blur. Continues shot 06 exactly (same comets, same squeeze).

Run in a NEW Blender file:  blender -b -P shot07_blast.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import os
import sys

ROOT = os.environ.get("SNEEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes"),
          os.path.join(ROOT, "shots")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
import numpy as np
from mathutils import Vector

import air_fx as AF
import claude_sculpt_kit as K
import hold_in as HOLD
import sky_set as SKY
import vfx_kit as V
import xray_set as XS

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LEAD = HOLD.SHOTS["07"][0] - HOLD.SHOTS["06"][0]           # 60: shot 06 frames already played
BLAST_LAUNCH, BLAST_SEED = (50, 95), 606                   # the same comets as in shot 06
LUNG_SQUEEZE = [(1, (0.84, 0.88, 0.82)), (26, (0.78, 0.84, 0.75)), (57, (0.77, 0.83, 0.74))]
LENS = 45


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["07"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    st = XS.stage("07")
    aw, nose = st["aw"], st["nose"]

    AF.squeeze_lungs(aw, LUNG_SQUEEZE)
    V.animate_socket(aw["mats"]["bronchi"].node_tree.nodes["Emission"].inputs["Strength"],
                     [(1, 1.7), (20, 1.8), (45, 1.3), (57, 1.2)])
    col = V.collection("FX")
    _, front = AF.blast(aw, n, col, aw["roots"]["chest"], np.random.default_rng(BLAST_SEED), per_lung=64,
                        n_core=12, launch=BLAST_LAUNCH, lead=LEAD)

    # the walls light up round the blast's leading edge as it passes
    carina = aw["carina"]
    pts, last = [], carina
    for p in front:
        last = p if p is not None and p.z > last.z else last
        pts.append(last)
    AF.key_glow(aw, [(f, pts[f - 1], 2.6) for f in range(1, n + 1, 2)], radius=0.035)

    # camera: a tall frame on her windpipe (lungs below, throat above), tilting up with the
    # blast and easing in
    r = V.camera_rig("Cam_Shot07", lens=LENS, fstop=11)
    a0 = Vector((0.0, carina.y - 0.01, nose.z - 0.215))
    a1 = Vector((0.0, carina.y - 0.012, nose.z - 0.15))
    c0 = a0 + K.look_dir(-38, 3) * 0.37
    c1 = a1 + K.look_dir(-30, 4) * 0.34
    V.cam_keys(r, [(1, c0, a0, None), (n, c1, a1, None)])
    V.handheld(r, amount=0.0006, aim_amount=0.0005)

    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.45)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    XS.finish()
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
