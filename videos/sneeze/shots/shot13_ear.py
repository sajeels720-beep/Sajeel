"""SHOT 13 (19.8-21.2 s, 42 frames @30fps) - "to your ears,"
Close-up of her right ear: a glowing scan line sweeps down over it and her skin turns
see-through, showing her ear canal with her eardrum at the end of it; the trapped air glows
in the middle ear behind it and the eardrum bulges outwards in pulses. 85 mm, push-in.

Run in a NEW Blender file:  blender -b -P shot13_ear.py -a
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
import xray_body as XB
import xray_set as XS

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 85
SCAN = (3, 15)                                    # the scan line passes over her ear
BULGE = [(1, 0.55), (14, 0.6), (18, 0.78), (21, 0.7), (27, 0.9), (30, 0.82), (36, 1.0), (42, 0.96)]


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["13"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    st = XS.stage("13", xray=False, ears=True)
    aw = st["aw"]
    hf, P, ear = aw["head"], aw["paths"], aw["ears"]["R"]
    z = ear["middle"].z
    XB.key_sweep(st["mats"], [(1, z + 0.07, 1.0), (SCAN[0], z + 0.07, 1.0), (SCAN[1], z - 0.06, 1.0), (30, -0.1, 1.0)])

    # the eardrum bulging in pulses, glowing; the trapped air jostling behind it
    for d in aw["ears"].values():
        V.key(d["drum"].data.shape_keys, 'key_blocks["Bulge"].value', BULGE)
    drum = V._inp(V.bsdf(aw["mats"]["eardrum"]), "Emission Strength")
    V.animate_socket(drum, [(1, 3.5), (SCAN[1], 4.0), (18, 5.5), (21, 4.6), (27, 6.0), (30, 5.2), (36, 7.0), (n, 6.6)])
    V.animate_socket(aw["mats"]["glass"].node_tree.nodes["Emission"].inputs["Strength"], [(1, 0.55)])   # the ear first
    col = V.collection("FX")
    AF.stream(aw, [P["ear_R"]], n, col, aw["roots"]["head"], np.random.default_rng(1313), count=26, launch=(-40, 20),
              speed=(0.003, 0.005), pile=0.01)
    AF.key_glow(aw, [(1, ear["middle"], 3.0), (18, ear["middle"], 4.5), (27, ear["middle"], 3.8), (n, ear["middle"], 5.2)],
                radius=0.022)

    # camera: just behind her right ear, looking in along the ear canal, pushing in
    r = V.camera_rig("Cam_Shot13", lens=LENS, fstop=8)
    a0 = (ear["drum_centre"] + ear["opening"]) / 2
    c0 = a0 + K.look_dir(-102, 5) * 0.3
    c1 = a0 + K.look_dir(-106, 7) * 0.17
    V.cam_keys(r, [(1, c0, a0, None), (n, c1, a0, None)])
    V.handheld(r, amount=0.0003, aim_amount=0.0002)

    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.3)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    XS.finish()
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
