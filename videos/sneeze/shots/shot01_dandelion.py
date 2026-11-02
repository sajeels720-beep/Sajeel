"""SHOT 01 (0.0-1.2 s, 36 frames @30fps) - "You feel a giant"
Extreme close-up of a fluffy dandelion clock on the studio blue. A breeze sways it and lifts
six seeds off, one after another; they drift past the lens on the left (towards her, so shot
02 picks one up coming in from the right). 100 mm, slow push-in, very shallow focus.

Run in a NEW Blender file:  blender -b -P shot01_dandelion.py -a
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
import dandelion_set as DS
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.2
N = 36
LENS = 100
BREAK_OFF = (3, 7, 11, 15, 20, 25)                     # frames the seeds let go
WIND = Vector((-0.034, -0.10, 0.018))                  # m/s: towards the lens and to the left
END_LOOK = (-10, 7)                                    # camera direction at the end (az, el) and distance
END_DIST = 0.215


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)

    slots = DS.seed_slots()
    loose = DS.facing(slots, K.look_dir(-55, 28), len(BREAK_OFF))
    dl = DS.build(loose=loose, slots=slots)
    root, head = dl["root"], dl["head"]
    # the breeze: a gentle sway at the stem base
    root.rotation_mode = "XYZ"
    V.key(root, "rotation_euler", [(1, (0.0, 0.0, 0.0)), (14, (np.radians(-1.4), np.radians(0.9), 0.0)),
                                   (30, (np.radians(0.5), np.radians(-0.6), 0.0)), (N, (np.radians(0.2), 0.0, 0.0))])
    bpy.context.view_layer.update()
    centre = head.matrix_world.translation.copy()

    rng = np.random.default_rng(11)
    for k, (i, f0) in enumerate(zip(loose, BREAK_OFF)):
        seed = dl["seeds"][i]
        bpy.context.scene.frame_set(f0)
        start = seed.matrix_world.translation.copy()
        T = (N + 4 - f0) / FPS
        jitter = Vector(rng.normal(0, 0.004, 3))
        out = (start - centre).normalized() * 0.006                # first it lifts away from the head
        path = [start + out + WIND * (0.15 * T),
                start + out * 1.5 + WIND * (0.5 * T) + jitter * 0.5 + Vector((0, 0, 0.004)),
                start + out * 2 + WIND * T + jitter]
        DS.drift(seed, (f0, N + 4), path, spin=1.2 + 0.3 * k, upright_by=12)

    # camera: 100 mm push-in, focus on the front of the fluff
    r = V.camera_rig("Cam_Shot01", lens=LENS, fstop=11)                # the backdrop is smooth anyway: keep the fluff crisp
    a0 = centre + Vector((0.0, 0.0, 0.002))
    a1 = centre + Vector((-0.002, -0.003, 0.003))
    c0 = a0 + K.look_dir(-12, 6) * 0.27
    c1 = a1 + K.look_dir(*END_LOOK) * END_DIST
    V.cam_keys(r, [(1, c0, a0, LENS), (N, c1, a1, LENS)])
    focus = V.link(bpy.data.objects.new("Focus_Shot01", None), V.collection("CAMERA"))
    focus.location = centre + (c0 - a0).normalized() * 0.01                 # between the core and the front fluff
    r["cam"].data.dof.focus_object = focus
    V.handheld(r, amount=0.0003, aim_amount=0.0002)

    SKY.studio(c0, a0, LENS)
    SKY.lights(centre, c0, SKY.view_dir(c0, a0, LENS), scale=0.12, key=1.4, rim=1.5)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return dl


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
