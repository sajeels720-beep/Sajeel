"""SHOT 08 (11.8-13.2 s, 42 frames @30fps) - "With nowhere to go,"
X-ray side profile of her head: the blast shoots up her throat, splits into her nose and
mouth and slams into her pinched nostrils and shut lips (frame 13): red ripple rings burst
out where it hits, her cheeks balloon, the camera jolts, and the air bounces back and starts
to churn. 50 mm, push-in.

Run in a NEW Blender file:  blender -b -P shot08_slam.py -a
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
import xray_set as XS

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
HIT = HOLD.SLAM - (HOLD.SHOTS["08"][0] - 1)                 # 13: the air slams into her lips and nose
LENS, AZ = 50, -90                                          # her right side (the pinching hand nearest us)


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["08"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    st = XS.stage("08")
    aw = st["aw"]
    hf = aw["head"]

    # camera: side profile of her head, pushing in
    r = V.camera_rig("Cam_Shot08", lens=LENS, fstop=11)
    a0 = hf(-0.065, -0.05)
    a1 = hf(-0.06, -0.042)
    c0 = a0 + K.look_dir(AZ, 2) * 0.5
    c1 = a1 + K.look_dir(AZ + 4, 2) * 0.41
    V.cam_keys(r, [(1, c0, a0, None), (n, c1, a1, None)])
    V.handheld(r, amount=0.0005, aim_amount=0.0004)
    V.shake(r, HIT - 1, HIT + 8, strength=0.004, scale=1.4)

    # the air: up the throat, into the nose and mouth, SLAM, bounce back
    col = V.collection("FX")
    _, (nose_end, lips_end) = AF.slam(aw, n, col, aw["roots"]["head"], np.random.default_rng(808), hit=HIT)
    throat, mid = hf(-0.1, -0.09), (nose_end + lips_end) / 2
    AF.key_glow(aw, [(1, throat, 2.4), (HIT - 4, hf(-0.085, -0.03), 2.8), (HIT, mid, 5.0), (HIT + 6, mid, 2.6),
                     (n, hf(-0.06, -0.03), 1.8)], radius=0.045)
    V.animate_socket(aw["mats"]["glass"].node_tree.nodes["Emission"].inputs["Strength"],
                     [(1, 1.1), (HIT - 1, 1.1), (HIT + 1, 2.2), (HIT + 8, 1.35), (n, 1.3)])
    cam_dir = (c1 - a1).normalized()
    for name, at in (("Slam_Ring_Nose", nose_end), ("Slam_Ring_Lips", lips_end)):
        V.ripple_rings(name, at, cam_dir, HIT, count=3, interval=4, life=16, radius=0.026, thickness=0.11,
                       color=V.hex_lin("#B00C08"), strength=3.2, col=col)

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
