"""SHOT 04 (5.1-6.5 s, 42 frames @30fps) - "It's not just the water."
His hand alone on the studio blue, open and palm up, the fingertips already wrinkled. Close on
the fingertips, drops of water land on the pads and soak into the skin (what most people think
happens); then the camera pulls back to his whole hand and on "water" his red "?" pops up with
red ripple rings, in the corner away from his hand. 50 mm.

Run in a NEW Blender file:  blender -b -P shot04_soak.py -a
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
from mathutils import Vector

import hand_set as HS
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 42
LENS = 50
DROPS = [(3, 1), (2, 5), (4, 9), (5, 13)]                # (finger, frame the drop starts falling)
POP = 25                                                  # the "?" on "water"
PULL = (21, 34)                                           # the camera pulls back from the fingertips


def camera_path(hs):
    """Shared with shot 05 (it starts on this shot's last framing): an orbit over his palm
    from his right side towards the front, looking down onto the fingertips."""
    palm, along, up = hs["palm"], hs["along"], hs["up"]
    aim = palm + along * 0.035 + up * 0.01
    side = along.cross(up).normalized()                 # towards his thumb side
    def at(t):
        d = (-along * 0.35 + side * (0.95 - 0.5 * t) + up * 1.05).normalized()
        return aim + d * (0.42 - 0.03 * t)
    return aim, at(0.0), at(1.0)


def close_view(hs):
    """Close above his fingertip pads, where the drops land: (aim, camera)."""
    pads = sum((hs["tips"][k][0] for k in (2, 3, 4, 5)), Vector()) / 4
    n = sum((hs["tips"][k][1] for k in (2, 3, 4, 5)), Vector()).normalized()
    side = hs["along"].cross(hs["up"]).normalized()
    return pads, pads + (n - hs["along"] * 0.45 + side * 0.35).normalized() * 0.2


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hs = HS.build(wrinkled=1.0)
    aim, c0, c1 = camera_path(hs)
    pads, close = close_view(hs)
    r = V.camera_rig("Cam_Shot04", lens=LENS, fstop=5.6)
    V.cam_keys(r, [(1, close, pads, LENS), (PULL[0], close.lerp(pads, 0.08), pads, LENS), (PULL[1], c1.lerp(c0, 0.1), aim, LENS),
                   (N, c1, aim, LENS)])
    V.handheld(r, amount=0.0006, aim_amount=0.0005)
    col = V.collection("FX")
    for k, f in DROPS:
        p, z = hs["tips"][k]
        HS.soak_drop(f"Drop_{k}", f, p, z, col=col)
    # a highlight in the drops, seen from the close-up
    HS.catch_light(pads, sum((hs["tips"][k][1] for k in (2, 3, 4, 5)), Vector()), close)
    # the "?" goes in the corner of the frame furthest from his hand
    hand = [hs["wrist"], hs["palm"]] + [hs["tips"][k][0] for k in HS.FINGERS] + [hs["ends"][k] for k in HS.FINGERS]
    HS.question_icon(col, c1, aim, LENS, screen=HS.free_spot(c1, aim, LENS, hand), pop=POP)
    SKY.studio(c1, aim, LENS)
    SKY.lights(aim, c1, SKY.view_dir(c1, aim, LENS), scale=0.4)
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return hs


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
