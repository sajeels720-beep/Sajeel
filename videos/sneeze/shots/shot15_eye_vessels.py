"""SHOT 15 (23.0-24.4 s, 42 frames @30fps) - "or pop the blood vessels"
Extreme close-up of her bulging right eye: tiny red vessels across the white of her eye swell
and redden in pulses with the pressure. 120 mm, slow push (shot 16 carries straight on).

Run in a NEW Blender file:  blender -b -P shot15_eye_vessels.py -a
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

import eye_set as EYE
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
LENS = 120
SWELL_15 = [(1, 0.05), (8, 0.2), (12, 0.45), (16, 0.35), (24, 0.65), (28, 0.55), (36, 0.85), (42, 0.8)]


def build():
    V.start_fresh()

    def cams(r, aim, look, n):                                 # slow push: 0.25 -> 0.215 m (shot 16 goes on)
        V.cam_keys(r, [(1, aim + look * 0.25, aim, None), (n, aim + look * 0.215, aim, None)])

    st = EYE.close_up("15", SWELL_15, cams, lens=LENS, preview=PREVIEW)
    EYE.ride_on_eye(st["hero"], "R", st["vessels"], st["col"])
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
