"""SHOT 10 (14.6-16.6 s, 60 frames @30fps) - "and the pressure in your airways"
Inside her neck (warm tissue backdrop): a close-up of her windpipe. With every push of the
trapped air, the soft wall between its cartilage rings balloons out a little further, going
thin and pale, its fine vessels stretching, and the blue air glowing through it. Low push
along the windpipe, a small jolt on the biggest pulses.

Run in a NEW Blender file:  blender -b -P shot10_bulge.py -a
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

import claude_sculpt_kit as K
import sky_set as SKY
import throat_set as TS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 60
PRESSURE = [(1, 0.1, 0.0), (8, 0.2, 0.05), (12, 0.5, 0.25), (16, 0.35, 0.2), (24, 0.65, 0.45), (28, 0.5, 0.38),
            (36, 0.8, 0.68), (40, 0.65, 0.6), (48, 0.95, 0.9), (52, 0.8, 0.84), (60, 1.0, 1.0)]
# (frame, swell, balloon): each push swells the wall and blows the blisters out further
LENS = 35


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    col = V.collection("SET_THROAT")
    pipe = TS.windpipe(col)
    mat = TS.wall_material()
    V.assign(pipe, mat)
    TS.key_pressure(pipe, mat, PRESSURE)
    line = TS.centre_line(pipe)
    at = lambda z: Vector(line[np.argmin(np.abs(line[:, 2] - z))])
    mid = at(0.75)
    TS.surroundings(col, mid)
    if PREVIEW:
        V.fast_preview(samples=24)

    # camera: low in front of the windpipe, looking up along it, rising slowly with it
    r = V.camera_rig("Cam_Shot10", lens=LENS, fstop=2.8)
    a0, a1 = at(0.72), at(0.84)
    c0 = a0 + K.look_dir(-14, -47) * 0.86
    c1 = a1 + K.look_dir(-10, -45) * 0.8
    V.cam_keys(r, [(1, c0, a0, None), (N, c1, a1, None)])
    V.handheld(r, amount=0.002, aim_amount=0.0015)
    for f in (36, 48):                                    # the biggest pushes jolt the view a little
        V.shake(r, f - 1, f + 5, strength=0.004, scale=1.5)
    focus = V.link(bpy.data.objects.new("Focus_Shot10", None), V.collection("CAMERA"))
    focus.location = at(0.62) + Vector((0.0, -TS.R, 0.0))             # the front of the wall, at a blister
    r["cam"].data.dof.focus_object = focus

    SKY.tissue(turn=40)
    SKY.tissue_lights(mid, c0, scale=0.8, rim=0.6)
    V.compositor(glow=0.35, threshold=1.0, dispersion=0.006)
    return pipe


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
