"""SHOT 16 (27.8-29.6 s, 54 frames @30fps) - "also runs to your forehead,"
Pull back to a 3/4 x-ray head: the trigeminal nerve's three branches glow yellow, then the
red signal races up the forehead branch and the forehead flares with red ripple rings.
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
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import park_set as PS
import shot07_xray_explainer as S07
import vfx_kit as V
import xray_head as XH

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.8
N = 54
SIGNAL = (12, 34)


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    PS.world()
    x = XH.build(nerves=True, side=1)
    eyes = x["eyes"]
    S07.studio_lights(eyes)
    v1 = x["nerves"]["V1"]
    mat = v1.data.materials[0]
    pos = mat.node_tree.nodes["Pulse"].outputs[0]
    V.animate_socket(pos, [(1, -0.1), (SIGNAL[0], -0.1), (SIGNAL[1], 1.05)], "LINEAR")
    V.animate_socket(mat.node_tree.nodes["PulseS"].outputs[0], [(1, 0.0), (SIGNAL[0], 3.0), (N, 3.0)])
    pts = [tuple(p.co[:3]) for p in v1.data.splines[0].points]
    tip = Vector(pts[-1])
    rings = V.ripple_rings("Forehead_Flare", tip + Vector((0, -0.004, 0)), (0.1, -1, 0.25), SIGNAL[1] - 1, count=3,
                           interval=6, life=14, radius=0.05, thickness=0.06, color=(1.0, 0.02, 0.01),
                           strength=2.5, col=V.collection("FX"))           # deep red: brighter turns salmon
    for r in rings:
        r.visible_diffuse = r.visible_glossy = False
    glow = x["brain_mat"].node_tree.nodes["Glow"].outputs[0]
    V.animate_socket(glow, [(1, 0.15), (SIGNAL[1], 0.15), (SIGNAL[1] + 4, 0.8), (N, 0.4)])
    r = V.camera_rig("Cam_Shot16", lens=50, fstop=5.6)
    a0 = tip + Vector((0, 0, -0.01))
    a1 = eyes + Vector((0.01, 0.02, -0.02))
    V.cam_keys(r, [(1, a0 + K.look_dir(40, 8) * 0.22, a0, 50), (SIGNAL[0] + 4, a1 + K.look_dir(38, 8) * 0.48, a1, 50),
                   (N, a1 + K.look_dir(34, 8) * 0.56, a1 + Vector((0, 0, 0.01)), 50)])
    V.handheld(r, amount=0.001, aim_amount=0.0008)
    V.compositor(glow=0.55, threshold=0.95, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 4, 16))
    return x


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
