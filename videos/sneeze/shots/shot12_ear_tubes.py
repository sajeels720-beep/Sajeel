"""SHOT 12 (18.2-19.8 s, 48 frames @30fps) - "That air shoots up the tiny tubes"
X-ray side profile of her head: glowing air streams up from her throat into the thin tubes
that run up to her ears (the Eustachian tubes) and piles up in her middle ears, pushing her
eardrums out. The camera follows it up from her throat to her ear. 50 mm.

Run in a NEW Blender file:  blender -b -P shot12_ear_tubes.py -a
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


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["12"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    st = XS.stage("12", ears=True)
    aw = st["aw"]
    hf, P, ear = aw["head"], aw["paths"], aw["ears"]["R"]

    # the air: up her throat, into both ear tubes, piling up in her middle ears
    col = V.collection("FX")
    up = P["larynx"] + P["pharynx"][:-1]
    _, first = AF.stream(aw, [up + P["ear_R"], up + P["ear_L"]], n, col, aw["roots"]["head"],
                         np.random.default_rng(1212), count=72, launch=(-14, 30))
    arrive = int(min(f for f in first if f is not None)) if any(first) else 16
    for d in aw["ears"].values():                                 # the eardrums bulge as it piles up behind them
        V.key(d["drum"].data.shape_keys, 'key_blocks["Bulge"].value', [(1, 0.0), (arrive, 0.04), (n, 0.55)])
    drum = V._inp(V.bsdf(aw["mats"]["eardrum"]), "Emission Strength")
    V.animate_socket(drum, [(1, 0.6), (arrive, 0.9), (n, 3.5)])
    AF.key_glow(aw, [(1, hf(-0.105, -0.085), 2.2), (arrive - 6, hf(-0.098, -0.02), 2.6), (arrive, ear["middle"], 3.0),
                     (n, ear["middle"], 4.2)], radius=0.028)

    # camera: her profile, rising with the air from her throat to her ear
    r = V.camera_rig("Cam_Shot12", lens=LENS, fstop=8)
    a0, a1 = hf(-0.1, -0.07), ear["middle"] + (hf(-0.012, -0.004) - hf(0, 0))
    c0 = a0 + K.look_dir(-90, 2) * 0.31
    c1 = a1 + K.look_dir(-96, 4) * 0.12
    V.cam_keys(r, [(1, c0, a0, None), (int(arrive) + 4, a1 + K.look_dir(-94, 3) * 0.17, a1, None), (n, c1, a1, None)])
    V.handheld(r, amount=0.0004, aim_amount=0.0003)

    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.35)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    XS.finish()
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
