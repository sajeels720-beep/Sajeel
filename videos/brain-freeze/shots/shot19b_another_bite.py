"""SHOT 19b (35.4-36.8 s, 42 frames @30fps) - "...at all."
Callback ending: back on the bench, he shrugs with a "whatever" smile, lifts the cup and
opens wide for another giant bite. Camera eases back.
"""
import math
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "shots"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Euler, Vector

import character as C
import claude_sculpt_kit as K
import shot03_perfect as S03
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.4
N = 42
SHRUG, LIFT = (2, 12), (14, 36)


def key_bone(rig, name, keys):
    """keys = [(frame, (rx, ry, rz) degrees added to the posed rotation)]."""
    pb = rig.pose.bones[name]
    pb.rotation_mode = "QUATERNION"
    base = pb.rotation_quaternion.copy()
    for f, rot in keys:
        pb.rotation_quaternion = base @ Euler([math.radians(a) for a in rot]).to_quaternion()
        pb.keyframe_insert("rotation_quaternion", frame=f)
    V.ease_id(rig, data_path=f'pose.bones["{name}"]')


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hero, park, ice, cup = S03.hero_on_bench()
    rig, body = hero["rig"], hero["body"]
    tgt = bpy.data.objects["Hand_R_target"]
    cup.parent = tgt                                              # the cup rides with the hand target
    cup.location = cup.location - tgt.location
    # shrug: shoulders up, head tilts, "whatever" brows and smile
    for side, sgn in (("L", 1), ("R", -1)):
        key_bone(rig, f"clavicle.{side}", [(1, (0, 0, 0)), (SHRUG[0], (0, 0, 0)), (SHRUG[1] - 4, (0, 0, 14 * sgn)),
                                           (SHRUG[1] + 6, (0, 0, 3 * sgn)), (N, (0, 0, 0))])
    S03.key_head(rig, [(1, (0, 0, 0)), (SHRUG[1] - 4, (2, 0, 8)), (LIFT[0] + 6, (-4, 0, 2)), (N, (-8, 0, 0))])
    C.face(body, {"browOuterUpLeft": 0.0, "browOuterUpRight": 0.0, "browInnerUp": 0.0, "mouthSmileLeft": 0.2,
                  "mouthSmileRight": 0.2, "jawOpen": 0.0}, frame=1)
    C.face(body, {"browOuterUpLeft": 0.8, "browOuterUpRight": 0.8, "browInnerUp": 0.5, "mouthSmileLeft": 0.6,
                  "mouthSmileRight": 0.6, "jawOpen": 0.0}, frame=SHRUG[1])
    C.face(body, {"browOuterUpLeft": 0.5, "browOuterUpRight": 0.5, "browInnerUp": 0.3, "mouthSmileLeft": 0.2,
                  "mouthSmileRight": 0.2, "jawOpen": 0.55}, frame=LIFT[1])
    C.face(body, {"jawOpen": 0.6}, frame=N)
    # lift the cup up toward the open mouth
    sc = bpy.context.scene
    sc.frame_set(N)
    mouth = (S03.bone_world(rig, "jaw") + S03.bone_world(rig, "jaw", tail=True)) / 2
    start = tgt.location.copy()
    near_mouth = mouth + Vector((-0.02, -0.16, -0.12))
    V.key(tgt, "location", [(1, tuple(start)), (LIFT[0], tuple(start)), (LIFT[1], tuple(near_mouth)),
                            (N, tuple(near_mouth + Vector((0, 0.01, 0.01))))])
    sc.frame_set(1)
    eyes = (S03.bone_world(rig, "eye.L") + S03.bone_world(rig, "eye.R")) / 2
    head = (S03.bone_world(rig, "head") + S03.bone_world(rig, "head", tail=True)) / 2
    S03.sun_rim_lights(head)
    r = V.camera_rig("Cam_Shot19b", lens=50, fstop=2.4)
    low = Vector((0, 0, -0.22))
    V.cam_keys(r, [(1, eyes + low + K.look_dir(-16, 6) * 1.25, eyes + low, 50),
                   (N, eyes + low + K.look_dir(-20, 6) * 1.45, eyes + low + Vector((0, 0, 0.02)), 50)])
    r["cam"].data.dof.focus_object = None
    r["cam"].data.dof.focus_distance = 1.35
    V.handheld(r, amount=0.002, aim_amount=0.0015)
    V.compositor(glow=0.35, threshold=1.1, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 4, 8))
    return {"hero": hero}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
