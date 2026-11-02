"""SHOT 09 (13.2-14.6 s, 42 frames @30fps) - "it gets trapped inside you,"
X-ray of her head: the trapped air churns round and round inside her nose, mouth and
throat, and her airways glow brighter and swell with the pressure. Slow orbit, 50 mm.

Run in a NEW Blender file:  blender -b -P shot09_swirl.py -a
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

import air_fx as AF
import claude_sculpt_kit as K
import hold_in as HOLD
import sky_set as SKY
import vfx_kit as V
import xray_set as XS

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 50
SWELL = [(1, 1.0), (12, 1.035), (20, 1.02), (30, 1.055), (36, 1.04), (42, 1.065)]   # throbbing with the pressure


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["09"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    st = XS.stage("09")
    aw = st["aw"]
    hf = aw["head"]

    # the trapped air churning, the airways glowing brighter and swelling
    col = V.collection("FX")
    AF.swirl(aw, n, col, aw["roots"]["head"], np.random.default_rng(909))
    V.key(aw["cast"], "scale", [(f, (s, s, s)) for f, s in SWELL])
    V.animate_socket(aw["mats"]["glass"].node_tree.nodes["Emission"].inputs["Strength"],
                     [(1, 1.3), (20, 1.8), (n, 2.4)])
    centre = hf(-0.06, -0.03)                                    # the walls glow pink with the pressure
    AF.key_glow(aw, [(1, centre, 0.8), (12, centre, 1.5), (20, centre, 1.1), (30, centre, 1.9), (36, centre, 1.5),
                     (n, centre, 2.2)], radius=0.06, color="#FF5C7E")

    # camera: a slow orbit round her head
    r = V.camera_rig("Cam_Shot09", lens=LENS, fstop=11)
    a0 = hf(-0.06, -0.035)
    keys = []
    for f in (1, n // 2, n):
        u = (f - 1) / (n - 1)
        keys.append((f, a0 + K.look_dir(-100 + 22 * u, 3 + 3 * u) * (0.38 - 0.03 * u), a0, None))   # round her profile
    V.cam_keys(r, keys)
    V.handheld(r, amount=0.0005, aim_amount=0.0004)

    c0 = keys[0][1]
    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.4)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    XS.finish()
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
