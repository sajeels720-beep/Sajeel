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


def hand_target(hero, side="R", col=None):
    """An empty at her wrist (location and rotation = the wrist bone's own frame). Animate it,
    then bake_arm() poses the arm to follow it."""
    rig = hero["rig"]
    col = col or V.collection("RIG_HELPERS")
    hand = V.link(bpy.data.objects.new(f"Hand_{side}", None), col)
    hand.empty_display_size = 0.04
    hand.rotation_mode = "QUATERNION"
    bpy.context.view_layer.update()
    M = rig.matrix_world @ rig.pose.bones[f"wrist.{side}"].matrix
    hand.location = M.translation
    hand.rotation_quaternion = M.to_quaternion()
    return {"hand": hand}


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


ARM = ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist")


def solve_arm(rig, side, wrist_world, pole_world, twist_share=0.5):
    """Exact two-bone arm: pose the upper arm and forearm (and their twist bones) so the wrist
    sits at wrist_world (a world 4x4: its head and rotation), with the elbow bending towards
    pole_world (a world direction). The forearm's twist bone rolls with a share of the hand's
    turn, like a real forearm, so the wrist never wrings like a candy wrapper. Uses the parent
    (shoulder) as evaluated on the current frame. Returns {bone name: basis matrix}."""
    A = rig.matrix_world
    Ai = A.inverted()
    bones, pbs = rig.data.bones, rig.pose.bones
    names = [f"{b}.{side}" for b in ARM]
    parent = pbs[names[0]].parent
    rel, prev = {}, parent.name
    for n in names:
        rel[n] = bones[prev].matrix_local.inverted() @ bones[n].matrix_local
        prev = n
    L1 = bones[names[0]].length + bones[names[1]].length
    L2 = bones[names[2]].length + bones[names[3]].length
    W = Ai @ wrist_world
    Mp = parent.matrix.copy()
    S = (Mp @ rel[names[0]]).translation
    to_w = W.translation - S
    d = min(max(to_w.length, abs(L1 - L2) + 1e-4), L1 + L2 - 1e-4)
    axis = to_w.normalized()
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    p = Ai.to_3x3() @ Vector(pole_world)
    p = p - axis * p.dot(axis)
    p = p.normalized() if p.length > 1e-6 else axis.orthogonal().normalized()
    elbow = S + axis * a + p * h
    wrist_at = S + axis * d

    def aim(name, Mpar, target):                               # shortest turn from the rest relation
        Mz = Mpar @ rel[name]
        y = Mz.to_3x3().col[1].normalized()
        R = y.rotation_difference((target - Mz.translation).normalized()).to_matrix()
        M = Matrix.Translation(Mz.translation) @ (R @ Mz.to_3x3()).to_4x4()
        return M

    M = {}
    M[names[0]] = aim(names[0], Mp, elbow)
    M[names[1]] = aim(names[1], M[names[0]], elbow)
    M[names[2]] = aim(names[2], M[names[1]], wrist_at)
    M[names[3]] = aim(names[3], M[names[2]], wrist_at)
    D = W.to_3x3().normalized()
    Z = (M[names[3]] @ rel[names[4]]).to_3x3().normalized()
    q = (Z.inverted() @ D).to_quaternion()                     # the hand's turn beyond the forearm's
    if q.w < 0:
        q = -q
    twist = 2 * math.atan2(q.y, q.w)
    l2 = M[names[3]]
    roll = Matrix.Rotation(twist_share * twist, 4, l2.to_3x3().col[1].normalized())
    M[names[3]] = Matrix.Translation(l2.translation) @ roll @ Matrix.Translation(-l2.translation) @ l2
    head = (M[names[3]] @ rel[names[4]]).translation
    M[names[4]] = Matrix.Translation(head) @ D.to_4x4()
    out, Mpar = {}, Mp
    for n in names:
        out[n] = rel[n].inverted() @ Mpar.inverted() @ M[n]
        Mpar = M[n]
    return out


def bake_arm(rig, side, frames, wrist_fn, pole_fn, twist_share=0.5):
    """Key the arm on every frame so the wrist follows wrist_fn(frame) (a world 4x4) with the
    elbow towards pole_fn(frame) (a world direction). Replaces IK: no solver flips, exact
    contact, and the forearm rolls with the hand."""
    sc = bpy.context.scene
    last = {}
    for f in frames:
        sc.frame_set(f)
        for name, basis in solve_arm(rig, side, wrist_fn(f), pole_fn(f), twist_share).items():
            pb = rig.pose.bones[name]
            pb.rotation_mode = "QUATERNION"
            q = basis.to_quaternion()
            if name in last and q.dot(last[name]) < 0:
                q = -q
            last[name] = q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f)
