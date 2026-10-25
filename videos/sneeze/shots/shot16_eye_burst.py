"""SHOT 16 (24.4-26.0 s, 48 frames @30fps) - "in your eyes."
Straight on from shot 15, the same close-up of her right eye: the swollen vessels throb, one
bursts (frame 10) and a red blotch of blood spreads out across the white of her eye. A
little push in, a small jolt on the burst.

Run in a NEW Blender file:  blender -b -P shot16_eye_burst.py -a
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
BURST = 10
SWELL_16 = [(1, 0.8), (6, 0.92), (BURST, 1.0), (BURST + 4, 0.72), (48, 0.66)]
SPREAD = [(1, 0.0), (BURST, 0.0), (BURST + 3, 0.18), (BURST + 12, 0.55), (BURST + 26, 0.85), (48, 0.92)]
AT = (31.0, 6.0)                                   # where it bursts: on the white, towards her outer corner


def build():
    V.start_fresh()

    def cams(r, aim, look, n):                                 # on from shot 15's last framing, a little closer
        V.cam_keys(r, [(1, aim + look * 0.215, aim, None), (n, aim + look * 0.19, aim, None)])

    st = EYE.close_up("16", SWELL_16, cams, lens=LENS, preview=PREVIEW)
    e = st["eye"]
    blot, mat = EYE.blotch(e, st["col"], at=AT)
    V.animate_socket(mat.node_tree.nodes["Spread"].outputs[0], SPREAD)
    for fc in V.fcurves(mat.node_tree):                        # it floods out fast, then creeps
        for kp in fc.keyframe_points:
            kp.interpolation, kp.easing = "QUAD", "EASE_OUT"
    V.ripple_rings("Burst_Ring", EYE.on_eye(e, *AT, 0.0003), (st["aim"] + st["look"] * 0.2) - EYE.on_eye(e, *AT),
                   BURST, count=2, interval=4, life=12, radius=0.004, thickness=0.06, color=V.hex_lin("#B00C08"),
                   strength=3.0, col=st["col"])
    V.shake(st["cam"], BURST, BURST + 6, strength=0.0006, scale=1.2)
    EYE.ride_on_eye(st["hero"], "R", st["vessels"] + [blot], st["col"])
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
