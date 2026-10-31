"""SHOT 06 (7.9-9.9 s, 60 frames @30fps) - "You see, a sneeze blasts air"
X-ray reveal, front three-quarter: a glowing scan line sweeps down over her and her skin and
clothes turn to glass, showing her lungs (the bronchial tree glowing inside), windpipe,
throat and nose. Then her lungs squeeze, the air in them lights up and the first of it
starts to stream out (shot 07 carries on with the blast). 35 mm, smooth glide in.
Her acting continues the held-in take (scenes/hold_in.py).

Run in a NEW Blender file:  blender -b -P shot06_xray.py -a
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

import air_fx as AF
import claude_sculpt_kit as K
import hold_in as HOLD
import sky_set as SKY
import vfx_kit as V
import xray_body as XB
import xray_set as XS

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
SWEEP = (6, 32, 46)                              # the scan line: above her head -> her waist -> on down out of shot
OFF = HOLD.SHOTS["06"][0] - 1
SQUEEZE = (HOLD.SQUEEZE[0] - OFF, HOLD.SQUEEZE[1] - OFF)   # (34, 47): her lungs squeeze
BLAST_LAUNCH = (50, 95)                          # the blast's comets leave the branch tips (shot 06 frames)
BLAST_SEED = 606                                 # shot 07 replays the same comets from frame 61 on
LUNG_SQUEEZE = [(1, (1.0, 1.0, 1.0)), (SQUEEZE[0], (1.0, 1.0, 1.0)), (SQUEEZE[1], (0.86, 0.9, 0.84)),
                (60, (0.84, 0.88, 0.82))]


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["06"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    st = XS.stage("06", xray=False)
    aw, nose = st["aw"], st["nose"]

    # the scan: a glowing line sweeps down from above her head to her waist
    top, low = nose.z + 0.2, nose.z - 0.62
    XB.key_sweep(st["mats"], [(1, top, 1.0), (SWEEP[0], top, 1.0), (SWEEP[1], low, 1.0), (SWEEP[2], -0.1, 1.0)])

    # her lungs squeeze, the bronchial tree and the air inside light up, the first air moves
    AF.squeeze_lungs(aw, LUNG_SQUEEZE)
    centre = (aw["hila"]["R"] + aw["hila"]["L"]) / 2
    AF.key_glow(aw, [(1, centre, 0.0), (SQUEEZE[0], centre, 0.0), (SQUEEZE[1], centre, 1.8), (60, aw["carina"], 2.4)],
                radius=0.07)
    V.animate_socket(aw["mats"]["bronchi"].node_tree.nodes["Emission"].inputs["Strength"],
                     [(1, 1.1), (SQUEEZE[0], 1.1), (SQUEEZE[1], 1.6), (60, 1.7)])
    col = V.collection("FX")
    AF.blast(aw, n, col, aw["roots"]["chest"], np.random.default_rng(BLAST_SEED), per_lung=64, n_core=12,
             launch=BLAST_LAUNCH)

    # camera: front three-quarter, gliding in as the scan reveals her airways
    r = V.camera_rig("Cam_Shot06", lens=35, fstop=11)
    a0 = nose + Vector((0.0, 0.035, -0.16))
    a1 = nose + Vector((0.0, 0.035, -0.175))
    c0 = a0 + K.look_dir(-30, 4) * 0.82
    c1 = a1 + K.look_dir(-26, 3) * 0.62
    V.cam_keys(r, [(1, c0, a0, None), (n, c1, a1, None)])
    V.handheld(r, amount=0.0008, aim_amount=0.0006)

    SKY.studio(c0, a0, 35)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, 35), scale=0.6)
    V.compositor(glow=0.4, threshold=1.0, dispersion=0.006)
    XS.finish()
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
