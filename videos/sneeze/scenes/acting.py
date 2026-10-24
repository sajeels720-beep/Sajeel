"""Hand acting for the heroine (MPFB default rig): the right arm reaches by IK, the hand turns
to a world orientation, and the fingers curl into shapes (relaxed, pinch). Used for pinching
her nose shut in shots 03-05 and letting go in shot 20.

Rig facts (MPFB default rig, A-pose rest): fingers bend about their local +X (positive =
towards the palm); finger1 is the thumb, finger2 the index ... finger5 the little finger;
upperarm02/lowerarm02 are twist bones inside the arm chain.
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

import vfx_kit as V

FINGERS = {  # bone chains per finger
    "thumb": ["finger1-1", "finger1-2", "finger1-3"],
    "index": ["finger2-1", "finger2-2", "finger2-3"],
    "middle": ["finger3-1", "finger3-2", "finger3-3"],
    "ring": ["finger4-1", "finger4-2", "finger4-3"],
    "little": ["finger5-1", "finger5-2", "finger5-3"],
}
RELAXED = {"thumb": (10, 10, 10), "index": (12, 18, 12), "middle": (15, 22, 15), "ring": (18, 25, 15),
           "little": (20, 28, 18)}
PINCH = {"thumb": (-25, 25, 30), "index": (30, 60, 35), "middle": (80, 95, 60), "ring": (85, 98, 60),
         "little": (88, 100, 60)}


def _rest_world(rig, name):
    return (rig.matrix_world @ rig.data.bones[name].matrix_local)


def palm_frame(rig, side="R"):
    """Rest-pose hand frame of the wrist bone, in world space: (forward to the fingers,
    palm normal out of the palm, across from index to little finger)."""
    b = lambda n: rig.matrix_world @ rig.data.bones[f"{n}.{side}"].head_local
    fwd = (b("finger3-1") - b("wrist")).normalized()
    across = (b("finger5-1") - b("finger2-1")).normalized()
    palm = fwd.cross(across).normalized()
    if side == "L":
        palm = -palm
    return fwd, palm, across


def curl(rig, side, shape, frame=None, scale=1.0):
    """Set finger curls (degrees per joint about local X; thumb too) and optionally key them."""
    for finger, angles in shape.items():
        for bone, a in zip(FINGERS[finger], angles):
            pb = rig.pose.bones.get(f"{bone}.{side}")
            if pb is None:
                continue
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (math.radians(a * scale), 0.0, 0.0)
            if frame is not None:
                pb.keyframe_insert("rotation_euler", frame=frame)


def hand_rig(hero, side="R", col=None):
    """IK for the arm (target = an empty at the wrist) with an elbow pole, and the wrist bone
    copying the empty's world rotation. Returns {"hand", "pole"}: animate the hand empty's
    location and rotation (quaternion) to move the hand; its frame is the wrist bone's own."""
    rig = hero["rig"]
    col = col or V.collection("RIG_HELPERS")
    hand = V.link(bpy.data.objects.new(f"Hand_{side}", None), col)
    hand.empty_display_size = 0.04
    hand.rotation_mode = "QUATERNION"
    pole = V.link(bpy.data.objects.new(f"Elbow_Pole_{side}", None), col)
    pole.empty_display_size = 0.03
    bpy.context.view_layer.update()
    wrist = rig.pose.bones[f"wrist.{side}"]
    M = rig.matrix_world @ wrist.matrix                         # current (posed) wrist
    hand.location = M.translation
    hand.rotation_quaternion = M.to_quaternion()
    sign = -1.0 if side == "R" else 1.0
    shoulder = rig.matrix_world @ rig.pose.bones[f"upperarm01.{side}"].head
    pole.location = shoulder + Vector((sign * 0.35, 0.25, -0.45))     # elbow out, back and down
    ik = rig.pose.bones[f"lowerarm02.{side}"].constraints.new("IK")
    ik.target, ik.pole_target = hand, pole
    ik.chain_count = 4
    ik.use_tail = True
    ik.pole_angle = math.radians(-90)
    for name in (f"upperarm02.{side}", f"lowerarm02.{side}"):    # twist bones: no twisting inside the IK
        rig.pose.bones[name].lock_ik_y = True
    cr = wrist.constraints.new("COPY_ROTATION")
    cr.target = hand
    cr.target_space = cr.owner_space = "WORLD"
    return {"hand": hand, "pole": pole, "ik": ik}


def wrist_for_tip_gap(rig, side="R"):
    """With the fingers in their current (curled) shape, the pinch gap in the wrist bone's
    frame: (midpoint of thumb tip and index pad, thumb->index direction), wrist-local."""
    bpy.context.view_layer.update()
    W = rig.matrix_world @ rig.pose.bones[f"wrist.{side}"].matrix
    Wi = W.inverted()
    thumb = rig.matrix_world @ rig.pose.bones[f"finger1-3.{side}"].tail
    index = rig.matrix_world @ rig.pose.bones[f"finger2-2.{side}"].tail     # pad between the last two joints
    return Wi @ ((thumb + index) / 2), (Wi.to_3x3() @ (index - thumb)).normalized(), (index - thumb).length


def pinch_pose(rig, nose, up=Vector((0, 0.45, 0.89)), across=Vector((1, 0, 0)), side="R"):
    """World transform for the hand empty (wrist) so that the pinch gap sits on `nose`, the
    gap runs along `across` (thumb on her right side) and the hand rises along `up`."""
    mid_local, gap_local, width = wrist_for_tip_gap(rig, side)
    # wrist-local frame of the pinch: x = across the gap, z = from wrist to the gap
    z_l = mid_local.normalized()
    x_l = (gap_local - z_l * gap_local.dot(z_l)).normalized()
    y_l = z_l.cross(x_l)
    L = Matrix((x_l, y_l, z_l)).transposed()
    z_w = up.normalized()
    x_w = (across - z_w * across.dot(z_w)).normalized()
    y_w = z_w.cross(x_w)
    Wd = Matrix((x_w, y_w, z_w)).transposed()
    R = Wd @ L.transposed()                                   # wrist rotation in world space
    loc = Vector(nose) - R @ mid_local
    return loc, R.to_quaternion(), width


def key_hand(hand, frame, loc, quat):
    hand.location = loc
    hand.rotation_quaternion = quat
    hand.keyframe_insert("location", frame=frame)
    hand.keyframe_insert("rotation_quaternion", frame=frame)
