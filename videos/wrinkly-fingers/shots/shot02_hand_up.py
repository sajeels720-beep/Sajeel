"""SHOT 02 (2.3-3.6 s, 39 frames @30fps) - "and your fingers turn into"
Over his shoulder: he opens his eyes, lowers his head and lifts his right hand out of the water
to look at it. Water drips off his fingers and rings spread where his hand broke the surface.
35 mm from behind his right shoulder, tilting up with the hand and pushing in.

Run in a NEW Blender file:  blender -b -P shot02_hand_up.py -a
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

import opening_take as TAKE
import pool_acting as PA
import pool_set as PS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 35


def hand_centre(hero, frame):
    bpy.context.scene.frame_set(frame)
    return (PA.joint(hero, "wrist.R") + PA.joint(hero, "finger3-3.R", "tail")) / 2


def build():
    V.start_fresh()
    lo, hi = TAKE.SHOTS["02"]
    n, off = hi - lo + 1, lo - 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts = PS.build(duck_at=(0.38, -0.72), duck_drift=(0.04, 0.0), sun_az=30, sun_el=42)
    parts["sun"].data.color = PS.H("#FFE2BC")                     # the afternoon light shot 01 ends on
    take = TAKE.perform("02")
    hero = take["hero"]
    # where the hand breaks the surface: rings spread from there; drops fall back from his fingers
    bpy.context.scene.frame_set(TAKE.SURFACE - off)
    exit_pt = PA.joint(hero, "finger3-3.R", "tail")
    drops = TAKE.drips(hero, range(TAKE.SURFACE + 3 - off, n + 1, 2))
    events = [(TAKE.SURFACE - off, exit_pt.x, exit_pt.y, 1.0)]
    events += [(f, x, y, 0.3) for _, f, (x, y) in drops[:3]]
    PS.ripples(parts["water"], events)
    # camera: behind his right shoulder, his head blurred at the left of the frame; it tilts up
    # with the hand out of the water and pushes in a little (he faces -Y, his right is -X)
    bpy.context.scene.frame_set(1)
    head0 = PA.joint(hero, "head")
    bpy.context.scene.frame_set(n)
    head = PA.joint(hero, "head")
    top = hand_centre(hero, n)
    mid = hand_centre(hero, TAKE.SURFACE + 6 - off)
    aim0 = Vector((exit_pt.x, exit_pt.y, PS.WATER_Z + 0.03))
    c0 = head0 + Vector((-0.25, 0.31, 0.15))
    c1 = head + Vector((-0.22, 0.27, 0.12))
    r = V.camera_rig("Cam_Shot02", lens=LENS, fstop=4.0)
    V.cam_keys(r, [(1, c0, aim0, LENS), (TAKE.SURFACE + 6 - off, c0.lerp(c1, 0.45), mid, LENS), (n, c1, top, LENS)])
    V.handheld(r, amount=0.0012, aim_amount=0.001)
    PS.rim(top, from_dir=(-0.3, -1.0, 0.6), dist=2.0, power=120.0)
    V.compositor(glow=0.2, threshold=1.4, dispersion=0.005)
    if PREVIEW:
        V.fast_preview(samples=24)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
