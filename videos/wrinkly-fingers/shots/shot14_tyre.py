"""SHOT 14 (20.0-21.4 s, 42 frames @30fps) - "like tyre treads."
On the studio blue: a car wheel with a clean rain tyre rolls along a strip of wet road through a
sheet of water, and water jets out of its tread grooves at both sides and flicks up behind it.
35 mm, low, ahead of the wheel and to its side (the tread faces the lens), travelling with it.

Run in a NEW Blender file:  blender -b -P shot14_tyre.py -a
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

import sky_set as SKY
import tyre_set as TS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 42
LENS = 35
SPEED = 2.4                                  # metres a second
X0 = 0.2                                     # where the axle is on frame 1


def x_at(f):
    return X0 + SPEED * (f - 1) / FPS


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts = TS.build()
    TS.roll(parts["root"], x_at, range(-2, N + 3))
    TS.spray(x_at, list(range(-6, N + 1)))
    TS.bow_wave(x_at, range(-2, N + 3))
    # camera: low, ahead of the wheel and to its side, travelling with it: the tread and its V
    # grooves face the lens as it rolls in, the water jetting out to the sides
    keys = []
    for f in (1, N):
        aim = Vector((x_at(f) + 0.12, -0.02, 0.2))
        keys.append((f, aim + Vector((0.95, -0.9, -0.06)), aim, LENS))
    r = V.camera_rig("Cam_Shot14", lens=LENS, fstop=4.0)
    V.cam_keys(r, keys, "LINEAR")
    V.handheld(r, amount=0.004, aim_amount=0.003)
    c0, a0 = keys[0][1], keys[0][2]
    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.9, rim=1.6)        # backlit spray sparkles
    for ob in V.collection("LIGHTS").objects:                                  # the lights travel with the wheel
        start = ob.location.copy()
        for f in (1, N):
            ob.location = start + Vector((x_at(f) - x_at(1), 0.0, 0.0))
            ob.keyframe_insert("location", frame=f)
        V.ease_id(ob, "LINEAR")
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return parts


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
