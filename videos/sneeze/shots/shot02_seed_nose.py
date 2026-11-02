"""SHOT 02 (1.2-2.2 s, 30 frames @30fps) - "sneeze coming,"
Extreme close-up of her nose. A dandelion seed drifts in from the right (carried by the same
breeze as shot 01), lands on the tip of her nose and sticks there while the nose twitches
twice, the nostrils flare and her eyes start to squint: the sneeze is coming.
100 mm, slow push towards the nostrils, the seed riding on the twitching skin.

Run in a NEW Blender file:  blender -b -P shot02_seed_nose.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import math
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
from mathutils import Matrix, Quaternion, Vector

import character as C
import claude_sculpt_kit as K
import dandelion_set as DS
import heroine as HR
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.0
N = 30
LENS = 100
LAND = 14                                              # the seed touches her nose
CALM = {"mouthSmileLeft": 0.15, "mouthSmileRight": 0.15}
TWITCH = [  # (frame, face units): two quick twitches, then the build-up that carries into shot 03
    (1, CALM), (LAND + 1, CALM),
    (LAND + 3, {"noseSneerLeft": 0.6, "noseSneerRight": 0.5, "flare": 0.5, "mouthUpperUpLeft": 0.08,
                "cheekSquintLeft": 0.25, "cheekSquintRight": 0.2, "eyeSquintLeft": 0.15, "eyeSquintRight": 0.1}),
    (LAND + 5, {"noseSneerLeft": 0.1, "noseSneerRight": 0.1, "flare": 0.1}),
    (LAND + 8, {"noseSneerLeft": 0.85, "noseSneerRight": 0.75, "flare": 0.8, "nostrils_wide": 0.25,
                "mouthPressLeft": 0.3, "mouthPressRight": 0.3, "cheekSquintLeft": 0.35, "cheekSquintRight": 0.3,
                "eyeSquintLeft": 0.35, "eyeSquintRight": 0.3, "eyeBlinkLeft": 0.25, "eyeBlinkRight": 0.25,
                "browDownLeft": 0.15, "browDownRight": 0.15}),
    (LAND + 11, {"noseSneerLeft": 0.35, "noseSneerRight": 0.3, "flare": 0.35, "cheekSquintLeft": 0.3,
                 "cheekSquintRight": 0.3, "eyeSquintLeft": 0.3, "eyeSquintRight": 0.3}),
    (N, {"noseSneerLeft": 0.8, "noseSneerRight": 0.8, "flare": 0.9, "nostrils_wide": 0.35, "mouthPressLeft": 0.25,
         "mouthPressRight": 0.25, "cheekSquintLeft": 0.55, "cheekSquintRight": 0.55, "eyeSquintLeft": 0.6,
         "eyeSquintRight": 0.6, "eyeBlinkLeft": 0.5, "eyeBlinkRight": 0.5, "browDownLeft": 0.35, "browDownRight": 0.35,
         "browInnerUp": 0.45}),
]
BLINK = [(4, 0.0), (6, 1.0), (9, 0.0)]


def key_face(body, keys):
    names = sorted({k for _, vals in keys for k in vals})
    for f, vals in keys:
        C.face(body, {k: vals.get(k, 0.0) for k in names}, frame=f)


def head_bone_keys(rig):
    """A tiny jerk on each twitch and a slight lift of the chin at the end (winding up)."""
    pb = rig.pose.bones["head"]
    pb.rotation_mode = "XYZ"
    for f, (x, z) in ((1, (0, 0)), (LAND + 2, (0, 0)), (LAND + 3, (-1.2, 0.6)), (LAND + 6, (0, 0)),
                      (LAND + 8, (-1.8, -0.5)), (LAND + 12, (-0.5, 0)), (N, (-4.0, 0.8))):
        pb.rotation_euler = (math.radians(x), 0.0, math.radians(z))
        pb.keyframe_insert("rotation_euler", frame=f)
    V.ease_id(rig)


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)

    hero = HR.build()
    HR.arms_down(hero)
    HR.nose_shapes(hero)
    body, rig = hero["body"], hero["rig"]
    key_face(body, TWITCH)
    for f, v in BLINK:
        C.face(body, {"eyeBlinkLeft": v, "eyeBlinkRight": v}, frame=f)
    head_bone_keys(rig)
    tip = HR.nose_tip(hero)
    sc = bpy.context.scene
    sc.frame_set(1)
    nose0, n0 = HR.surface_point(hero, tip)

    # camera: 100 mm on her nose, a little from her left, pushing in towards the nostrils
    r = V.camera_rig("Cam_Shot02", lens=LENS, fstop=11)
    a0 = nose0 + Vector((0.0, 0.004, 0.012))                    # nose in the middle, eyes in the top of frame
    a1 = nose0 + Vector((0.0, 0.002, 0.011))                    # keep the squinting eyes in the top of frame
    c0 = a0 + K.look_dir(16, 4) * 0.30
    c1 = a1 + K.look_dir(12, -2) * 0.255
    V.cam_keys(r, [(1, c0, a0, LENS), (N, c1, a1, LENS)])
    focus = V.link(bpy.data.objects.new("Focus_Shot02", None), V.collection("CAMERA"))
    focus.location = nose0 + Vector((0.0, 0.006, 0.0))
    r["cam"].data.dof.focus_object = focus
    V.handheld(r, amount=0.0004, aim_amount=0.0003)

    # the seed: drifts in from the right (her left), lands on the tip of the nose and sticks
    col = V.collection("SET_SEED")
    mats = DS.materials()
    seed = DS.loose_seed(col, mats, DS.seed_slots(count=12, rng_seed=21)[5], "Seed_Nose")
    seed.scale = (1.25, 1.25, 1.25)                             # a touch bigger than life so it reads on a phone
    right = (c0 - a0).cross(Vector((0, 0, 1))).normalized() * -1.0      # camera's right
    toward = (c0 - a0).normalized()
    land_axis = (n0 * 0.55 + Vector((0, 0, 1)) * 0.75 + right * 0.35).normalized()   # parachute up and out
    fly = [nose0 + right * 0.036 + Vector((0, 0, 0.026)) + toward * 0.008,     # already at the right edge on frame 1
           nose0 + right * 0.024 + Vector((0, 0, 0.024)) + toward * 0.006,
           nose0 + right * 0.012 + Vector((0, 0, 0.019)),
           nose0 + land_axis * DS.PAPPUS_UP * 1.25]
    pts = K.path_spline([tuple(p) for p in fly], 80)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    q_land = DS.frame_z(land_axis, 0.6).to_quaternion()
    for f in range(1, LAND + 1):                                # gliding in, parachute up, slowing to land
        u = (f - 1) / (LAND - 1)
        d = (1 - (1 - u) ** 2) * seg[-1]                        # decelerates onto the skin
        j = max(1, min(int(np.searchsorted(seg, d)), len(pts) - 1))
        a = (d - seg[j - 1]) / max(seg[j] - seg[j - 1], 1e-9)
        seed.location = Vector(pts[j - 1]).lerp(Vector(pts[j]), a)
        sway = Matrix.Rotation(0.12 * math.sin(0.6 * f), 3, "X") @ Matrix.Rotation(0.1 * math.sin(0.45 * f + 1), 3, "Y")
        up = (sway @ Matrix.Rotation(0.9 * f / FPS, 3, "Z")).to_quaternion()
        w = max(0.0, (u - 0.55) / 0.45)
        seed.rotation_quaternion = up.slerp(q_land, w * w * (3 - 2 * w))
        seed.keyframe_insert("location", frame=f)
        seed.keyframe_insert("rotation_quaternion", frame=f)
    for f in range(LAND + 1, N + 1):                            # rides on the twitching skin, jiggling a little
        sc.frame_set(f)
        p, n = HR.surface_point(hero, tip)
        jiggle = Matrix.Rotation(0.05 * math.sin(1.3 * f), 3, "X").to_quaternion()
        seed.location = p + land_axis * DS.PAPPUS_UP * 1.25
        seed.rotation_quaternion = q_land @ jiggle
        seed.keyframe_insert("location", frame=f)
        seed.keyframe_insert("rotation_quaternion", frame=f)
    sc.frame_set(1)

    SKY.studio(c0, a0, LENS)
    SKY.lights(nose0, c0, SKY.view_dir(c0, a0, LENS), scale=0.3)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return hero


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
