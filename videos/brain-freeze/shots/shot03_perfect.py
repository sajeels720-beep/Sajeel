"""SHOT 03 (3.0-5.2 s, 66 frames @30fps) - "and for a second, it's perfect."
The protagonist on a sunny park bench, ice cream cup in his lap, eyes closed, smile
growing, head tipping back in bliss. Backlit by the sun, slow orbit, shallow depth of field.
"""
import math
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
import numpy as np
from mathutils import Euler, Quaternion, Vector

import character as C
import claude_sculpt_kit as K
import icecream_set as ICE
import park_set as PARK
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 2.2
N = 66
POSE = "callharvey3d_sittingnatural"


def bone_world(rig, name, tail=False):
    pb = rig.pose.bones[name]
    return rig.matrix_world @ (pb.tail if tail else pb.head)


def hero_on_bench(pose=POSE):
    """Shared by shots 03, 04 and 19: branded hero seated on the park bench, cup in lap."""
    hero = C.build_hero()
    C.brand(hero)
    C.apply_pose(hero, pose)
    butt, feet = C.seat_heights(hero)
    seat_top = float(np.clip(butt - feet, 0.38, 0.52))
    park = PARK.build(seat_top=seat_top)
    C.place_on_seat(hero, seat_top, seat_y=0.02)
    bpy.context.view_layer.update()
    # ice cream cup (bite already taken) resting in his lap
    ice = ICE.build("SET_CUP")
    for k in ("table", "chunk"):
        bpy.data.objects.remove(ice[k])
    bpy.data.objects.remove(ice["scoops"]["Vanilla"])
    lap = lap_point(hero) + Vector((-0.07, -0.05, 0.03))          # a little to his right, held up off the lap
    ctrl = V.link(bpy.data.objects.new("Cup_ctrl", None), ice["col"])
    for ob in list(ice["col"].objects):
        if ob is not ctrl and ob.parent is None:
            ob.parent = ctrl
    ctrl.location = lap
    ctrl.rotation_euler = (math.radians(-6), 0, math.radians(20))
    # spoon stands in the cup
    ice["spoon"].parent = ctrl
    ice["spoon"].location = (0.012, 0.01, 0.12)
    ice["spoon"].rotation_euler = (math.radians(-70), math.radians(10), 0)
    hold_cup(hero, ctrl)
    return hero, park, ice, ctrl


def hold_cup(hero, cup, side="R"):
    """IK the arm so the hand wraps the side of the cup."""
    rig = hero["rig"]
    tgt = V.link(bpy.data.objects.new(f"Hand_{side}_target", None), V.collection("RIG_TARGETS"))
    out = Vector((-1 if side == "R" else 1, 0, 0))
    tgt.location = cup.location + out * 0.045 + Vector((0, 0.0, 0.035))
    ik = rig.pose.bones[f"lowerarm02.{side}"].constraints.new("IK")
    ik.target, ik.chain_count = tgt, 4
    for i in (1, 2, 3):                                           # curl the fingers round the cup
        for f in ("finger2", "finger3", "finger4", "finger5"):
            name = f"{f}-{i}.{side}"
            if name in rig.pose.bones:
                pb = rig.pose.bones[name]
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = (math.radians(32 if i == 1 else 40), 0, 0)
    bpy.context.view_layer.update()
    return tgt


def lap_point(hero):
    """Top of the lap between the thighs (where the cup rests)."""
    body = hero["body"]
    rest = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    posed = C.evaluated_points(body)
    top = rest[:, 2].max()
    thigh = (rest[:, 2] > top * 0.38) & (rest[:, 2] < top * 0.46) & (np.abs(rest[:, 0]) < 0.14)
    p = posed[thigh]
    return Vector((float(np.median(p[:, 0])), float(np.percentile(p[:, 1], 30)), float(p[:, 2].max()) - 0.005))


def key_head(rig, keys):
    """keys = [(frame, (rx, ry, rz) degrees added to the posed head rotation)]."""
    pb = rig.pose.bones["head"]
    pb.rotation_mode = "QUATERNION"
    base = pb.rotation_quaternion.copy()
    for f, rot in keys:
        pb.rotation_quaternion = base @ Euler([math.radians(a) for a in rot]).to_quaternion()
        pb.keyframe_insert("rotation_quaternion", frame=f)
    V.ease_id(rig, data_path='pose.bones["head"]')


def sun_rim_lights(head, power_key=60, power_rim=150):
    lights = V.collection("LIGHTS")
    out = {}
    for name, az, el, dist, power, size, color in (("Key_lgt", -35, 18, 1.6, power_key, 1.2, (1.0, 0.93, 0.86)),
                                                   ("Rim_lgt", 165, 25, 1.6, power_rim, 0.6, (1.0, 0.86, 0.68)),
                                                   ("Fill_lgt", 60, 5, 2.0, power_key * 0.25, 1.5, (0.8, 0.88, 1.0))):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = power, size, color
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = head + K.look_dir(az, el) * dist
        K._aim(ob, head)
        out[name] = ob
    return out


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hero, park, ice, cup = hero_on_bench()
    rig, body = hero["rig"], hero["body"]
    # bliss: eyes closed, smile grows, head tips back, a slow contented breath
    C.face(body, {"eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0, "mouthSmileLeft": 0.35, "mouthSmileRight": 0.35,
                  "browInnerUp": 0.25, "cheekSquintLeft": 0.15, "cheekSquintRight": 0.15}, frame=1)
    C.face(body, {"eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0, "mouthSmileLeft": 0.8, "mouthSmileRight": 0.8,
                  "browInnerUp": 0.35, "cheekSquintLeft": 0.45, "cheekSquintRight": 0.45}, frame=N)
    key_head(rig, [(1, (0, 0, 0)), (N, (-9, 0, 4))])
    head = (bone_world(rig, "head") + bone_world(rig, "head", tail=True)) / 2
    eyes = (bone_world(rig, "eye.L") + bone_world(rig, "eye.R")) / 2
    sun_rim_lights(head)

    r = V.camera_rig("Cam_Shot03", lens=50, fstop=2.2)
    face_dir = Vector((0, -1, 0))
    low = Vector((0, 0, -0.26))                                   # frame head to lap: the cup sits low in frame
    c0 = eyes + low + K.look_dir(-30, 4) * 1.55
    c1 = eyes + low + K.look_dir(-14, 7) * 1.3
    V.cam_keys(r, [(1, c0, eyes + low, 50), (N, c1, eyes + low + Vector((0, 0, 0.03)), 50)])
    r["cam"].data.dof.focus_object = None
    r["cam"].data.dof.focus_distance = 1.42                      # focus on the face, not the aim point
    V.handheld(r, amount=0.002, aim_amount=0.0015)
    V.compositor(glow=0.35, threshold=1.1, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 4, 8))
    return {"hero": hero, "park": park, "cup": cup}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
