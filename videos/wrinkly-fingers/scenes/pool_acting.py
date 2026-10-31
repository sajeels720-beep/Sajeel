"""Posing him in the pool (MPFB default rig).

place() stands him on the pool floor, leaning back with his upper back against the wall.
pose_arm() puts a wrist at a world position and turns the hand (fingers along one direction,
palm facing another), bending the elbow towards a pole direction: the exact two-bone solve
from the sneeze video (sneeze/scenes/acting.py), so there are no IK flips.
lounge() is his opening pose: leaning back in the sun, left arm resting along the stone edge,
right arm floating in the water, head tipped back, eyes closed, a blissful smile.
left_on_stone() lays the left arm on the stone (touching, never in it: checked on the posed mesh)
and plant() keeps that hand where it lies while he moves.

Rig facts: +X on spine, neck and head bones bends forward (chin down); fingers curl about
their local +X; finger1 is the thumb.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

import acting as A
import character as C
import pool_set as PS
import vfx_kit as V
import wrinkles as WR

LEAN = 9.0                     # degrees he leans back against the wall
BACK_GAP = 0.012               # shirt to tiles


def _update():
    bpy.context.view_layer.update()


def place(hero, lean=LEAN, x=0.0):
    """Feet on the pool floor, leaning back, upper back just touching the wall."""
    rig, body = hero["rig"], hero["body"]
    rig.rotation_euler = (math.radians(-lean), 0.0, 0.0)
    rig.location = (x, 0.0, PS.WATER_Z - PS.DEPTH)
    _update()
    rest = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    posed = C.evaluated_points(body)
    top = rest[:, 2].max()
    band = (rest[:, 2] > rest[:, 2].min() + (top - rest[:, 2].min()) * 0.62) & \
           (rest[:, 2] < rest[:, 2].min() + (top - rest[:, 2].min()) * 0.82) & (np.abs(rest[:, 0] - x) < 0.16)
    back = posed[band, 1].max()
    rig.location.y += (PS.WALL_Y - BACK_GAP) - back
    _update()
    return rig.location.copy()


def wrist_matrix(rig, side, loc, fingers, palm):
    """World wrist transform: at loc, fingers pointing along `fingers`, palm facing `palm`."""
    fwd0, palm0, _ = A.palm_frame(rig, side)
    B0 = Matrix((fwd0, palm0, fwd0.cross(palm0))).transposed()
    f1 = Vector(fingers).normalized()
    p1 = Vector(palm)
    p1 = (p1 - f1 * p1.dot(f1)).normalized()
    B1 = Matrix((f1, p1, f1.cross(p1))).transposed()
    W0 = rig.matrix_world @ rig.data.bones[f"wrist.{side}"].matrix_local
    return Matrix.Translation(Vector(loc)) @ ((B1 @ B0.transposed()) @ W0.to_3x3()).to_4x4()


def pose_arm(hero, side, loc, fingers, palm, pole, curl=None, frame=None, twist_share=0.5, together=0.95):
    """Put the wrist at `loc` with the hand turned; key it on `frame` if given. curl: a
    finger shape for hand_shape() (fingers drawn `together`)."""
    rig = hero["rig"]
    W = wrist_matrix(rig, side, loc, fingers, palm)
    for name, basis in A.solve_arm(rig, side, W, Vector(pole), twist_share).items():
        pb = rig.pose.bones[name]
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = basis.to_quaternion()
        if frame is not None:
            pb.keyframe_insert("rotation_quaternion", frame=frame)
    if curl is not None:
        hand_shape(hero, side, curl, together=together, frame=frame)
    _update()


# Finger shapes: degrees of bend at the three joints (thumb first). A relaxed hand bends a
# little more at each finger from the index to the little finger (the cascade); bending them
# all the same, with MPFB's rest-pose spread, made a claw.
RELAXED_HAND = {"thumb": (4, 10, 8), "index": (9, 14, 9), "middle": (13, 18, 11), "ring": (17, 22, 13),
                "little": (21, 26, 15)}
LOOK_HAND = {"thumb": (2, 8, 8), "index": (5, 8, 5), "middle": (7, 10, 6), "ring": (10, 13, 8),
             "little": (13, 16, 10)}      # looking at his fingertips: pads turned to his face


def close_spread(rig, side):
    """Degrees about each finger's base bone's local Z that line it up with the middle finger
    (thumb: with the index). MPFB's rest pose spreads them 10-16 degrees apart."""
    def frame(k):
        return (rig.matrix_world @ rig.data.bones[f"finger{k}-1.{side}"].matrix_local).to_3x3()
    out = {}
    for k, name, ref in ((1, "thumb", 2), (2, "index", 3), (3, "middle", 3), (4, "ring", 3), (5, "little", 3)):
        d = frame(k).inverted() @ frame(ref).col[1].normalized()
        out[name] = math.degrees(math.atan2(-d.x, d.y))
    return out


def hand_shape(hero, side, curl, together=0.95, thumb_in=0.5, frame=None):
    """Shape the fingers: curl = degrees per joint (like RELAXED_HAND); together = how far the
    fingers close their rest-pose spread (1 = parallel); thumb_in = the thumb's share."""
    rig = hero["rig"]
    spread = close_spread(rig, side)
    for finger, angles in curl.items():
        z = spread[finger] * (thumb_in if finger == "thumb" else together)
        for j, (bone, a) in enumerate(zip(A.FINGERS[finger], angles)):
            pb = rig.pose.bones.get(f"{bone}.{side}")
            if pb is None:
                continue
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (math.radians(a), 0.0, math.radians(z) if j == 0 else 0.0)
            if frame is not None:
                pb.keyframe_insert("rotation_euler", frame=frame)
    _update()


def arm_path(hero, side, poses, frames, twist_share=0.5):
    """Move a hand along a smooth path: poses = [(frame, loc, fingers, palm, pole), ...].
    The wrist and the elbow's pole are keyed on helper empties (eased Bezier curves through
    the poses, so the hand flows through the middle ones instead of stopping), then the arm
    is solved and keyed on every frame in `frames` (sneeze/scenes/acting.bake_arm)."""
    rig = hero["rig"]
    col = V.collection("RIG_HELPERS")
    hand = V.link(bpy.data.objects.new(f"Wrist_Path.{side}", None), col)
    pole = V.link(bpy.data.objects.new(f"Pole_Path.{side}", None), col)
    hand.rotation_mode = "QUATERNION"
    prev = None
    for f, loc, fingers, palm, pole_dir in poses:
        M = wrist_matrix(rig, side, loc, fingers, palm)
        q = M.to_quaternion()
        if prev is not None and q.dot(prev) < 0:
            q = -q
        prev = q
        hand.location, hand.rotation_quaternion = M.translation, q
        hand.keyframe_insert("location", frame=f)
        hand.keyframe_insert("rotation_quaternion", frame=f)
        pole.location = Vector(pole_dir)
        pole.keyframe_insert("location", frame=f)
    for ob in (hand, pole):
        V.ease_id(ob)

    def wrist(f):
        rot = hand.rotation_quaternion.normalized().to_matrix().to_4x4()
        return Matrix.Translation(hand.location) @ rot
    A.bake_arm(rig, side, frames, wrist, lambda f: pole.location.copy(), twist_share)
    _update()
    return hand


def key_face(hero, keys, off=0):
    """Expressions over time: keys = [(frame, {face unit: value})]; any unit used anywhere
    but not listed at a key is 0 there, so expressions blend cleanly."""
    units = sorted({u for _, d in keys for u in d})
    for f, d in keys:
        C.face(hero["body"], {u: d.get(u, 0.0) for u in units}, f - off)


def key_bones(hero, keys, off=0):
    """Body over time: keys = [(frame, {bone: (x, y, z) degrees})]; any bone used anywhere but
    not listed at a key is at rest (0, 0, 0) there."""
    names = sorted({n for _, d in keys for n in d})
    for f, d in keys:
        bones(hero, {n: d.get(n, (0.0, 0.0, 0.0)) for n in names}, f - off)
    V.ease_id(hero["rig"], data_path="pose.bones")


def bones(hero, rotations, frame=None):
    """Rotate pose bones by Euler degrees: {"head": (-12, 0, 3), ...}."""
    rig = hero["rig"]
    for name, rot in rotations.items():
        pb = rig.pose.bones[name]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = tuple(math.radians(a) for a in rot)
        if frame is not None:
            pb.keyframe_insert("rotation_euler", frame=frame)
    _update()


def joint(hero, name, end="head"):
    rig = hero["rig"]
    pb = rig.pose.bones[name]
    return rig.matrix_world @ (pb.head if end == "head" else pb.tail)


BLISS = {"eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0, "mouthSmileLeft": 0.55, "mouthSmileRight": 0.55,
         "cheekSquintLeft": 0.25, "cheekSquintRight": 0.25, "browInnerUp": 0.15}
LOUNGE_TORSO = {"neck01": (-8, 0, 0), "neck02": (-7, 0, 0), "head": (-12, 0, 4), "spine02": (-2, 0, 0)}
LOUNGE_CURL = RELAXED_HAND


# His left arm resting along the stone edge. The edge is only 2.5 cm below his shoulder joint, so
# from a resting shoulder the arm either went into the stone or had to hook over it. The shoulder
# comes up a little (as it does when you prop an arm on a ledge), the upper arm goes out to his
# side and a little back over the edge, the elbow bends a little, and the forearm and hand lie
# along the stone, the hand flat and in line with the forearm. (In a curl, the fingertips went
# into the stone.)
SHRUG = 8.0                        # degrees the left shoulder comes up (about 2.3 cm)
UPPER_ON_STONE = (20.0, 0.0)       # the upper arm's heading (degrees from straight out to his left
FORE_ON_STONE = (45.0, 0.0)        # towards the back) and pitch; the forearm's
STONE_GAP = 0.002                  # the hand lies this far above the stone: it touches
# the hand lying on the stone: how far each finger bends at its joints, from the bone before
# (MPFB's rest pose is already curled 8-25 degrees at the knuckles, so the curl is solved)
STONE_HAND = {"index": (4, 6, 3), "middle": (5, 7, 4), "ring": (6, 8, 5), "little": (7, 10, 6)}
STONE_THUMB = (2, 6, 4)


def _rest_flex(rig, name):
    """How far a bone bends from its parent in the rest pose (degrees, + towards the palm)."""
    b = rig.data.bones[name]
    M, P = b.matrix_local.to_3x3(), b.parent.matrix_local.to_3x3()
    y = M.col[1].normalized()
    return math.degrees(math.atan2(y.dot(P.col[2].normalized()), y.dot(P.col[1].normalized())))


def flat_hand(hero, side, bends=STONE_HAND, thumb=STONE_THUMB, together=0.85, frame=None):
    """A hand lying flat on something, its fingers bending `bends` at each joint."""
    rig = hero["rig"]
    curl = {"thumb": thumb}
    for finger, angles in bends.items():
        curl[finger] = tuple(a - _rest_flex(rig, f"{b}.{side}") for b, a in zip(A.FINGERS[finger], angles))
    hand_shape(hero, side, curl, together=together, frame=frame)


def shrug(hero, side, degrees, frame=None):
    """Raise a shoulder: the clavicle turns up about the body's front-to-back axis."""
    rig = hero["rig"]
    b = rig.data.bones[f"clavicle.{side}"]
    up = Vector((0.0, -1.0 if side == "L" else 1.0, 0.0))          # turning about this lifts the outer end
    pb = rig.pose.bones[b.name]
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = Quaternion((b.matrix_local.to_3x3().inverted() @ up).normalized(), math.radians(degrees))
    if frame is not None:
        pb.keyframe_insert("rotation_quaternion", frame=frame)
    _update()


def arm_parts(hero, side):
    """Indices of the vertices of his hand, forearm and upper arm on one side (cached)."""
    key = f"_arm_parts_{side}"
    if key not in hero:
        body = hero["body"]

        def pick(prefixes, threshold):
            names = [g.name for g in body.vertex_groups if g.name.endswith("." + side) and g.name.startswith(prefixes)]
            sel = np.zeros(len(body.data.vertices), bool)
            for w in WR._group_weights(body, names).values():
                sel |= w > threshold
            return np.where(sel)[0]
        hero[key] = {"hand": pick(("wrist", "finger", "metacarpal"), 0.2), "forearm": pick(("lowerarm",), 0.2),
                     "upperarm": pick(("upperarm", "shoulder"), 0.4)}
    return hero[key]


def arm_points(hero, side):
    """Posed world positions of the vertices of his forearm and hand on one side."""
    parts = arm_parts(hero, side)
    return C.evaluated_points(hero["body"])[np.union1d(parts["forearm"], parts["hand"])]


def arm_clearance(hero, side, parts=("hand", "forearm", "upperarm", "sleeve")):
    """How far each part of an arm (and the shirt's sleeve) stays above the stone edge and the
    deck (pool_set.stone_clearance: negative means in the stone)."""
    out = {}
    idx = arm_parts(hero, side)
    if any(k in idx for k in parts):
        P = C.evaluated_points(hero["body"])
        out.update({k: PS.stone_clearance(P[idx[k]]) for k in parts if k in idx})
    if "sleeve" in parts and hero.get("shirt") is not None:
        Q = C.evaluated_points(hero["shirt"])
        x = joint(hero, f"upperarm01.{side}").x
        out["sleeve"] = PS.stone_clearance(Q[Q[:, 0] > x - 0.02] if side == "L" else Q[Q[:, 0] < x + 0.02])
    return out


def _heading(yaw, pitch):
    """A direction (left side): yaw degrees from straight out to his left towards the back, pitch up."""
    y, p = math.radians(yaw), math.radians(pitch)
    return Vector((math.cos(y) * math.cos(p), math.sin(y) * math.cos(p), math.sin(p)))


def left_on_stone(hero, frame=None):
    """Rest his left arm along the stone edge (see SHRUG) and key it on `frame`. The hand's pitch
    is solved so it lies STONE_GAP above the stone; if the forearm, the upper arm or the sleeve
    would touch the stone, the arm is raised a degree at a time. Returns the wrist's pose
    {loc, fingers, palm, pole} for plant()."""
    rig = hero["rig"]
    upper = sum(rig.data.bones[f"{n}.L"].length for n in ("upperarm01", "upperarm02"))
    fore = sum(rig.data.bones[f"{n}.L"].length for n in ("lowerarm01", "lowerarm02"))
    shrug(hero, "L", SHRUG, frame)
    S = joint(hero, "upperarm01.L")
    palm = Vector((0.0, 0.0, -1.0))

    def lie(W, pole, pitch):                                        # how far the hand is above where it should lie
        pose_arm(hero, "L", W, _heading(FORE_ON_STONE[0], pitch), palm, pole)
        flat_hand(hero, "L")
        return arm_clearance(hero, "L", ("hand",))["hand"] - STONE_GAP

    for lift in range(8):
        E = S + _heading(UPPER_ON_STONE[0], UPPER_ON_STONE[1] + lift) * upper
        W = E + _heading(*FORE_ON_STONE) * fore
        pole = E - S
        p0, p1 = FORE_ON_STONE[1], FORE_ON_STONE[1] - 12.0
        h0, h1 = lie(W, pole, p0), lie(W, pole, p1)
        for _ in range(6):                                          # secant on the hand's pitch
            if abs(h1) < 0.0004 or abs(h1 - h0) < 1e-7:
                break
            p2 = max(-45.0, min(25.0, p1 - h1 * (p1 - p0) / (h1 - h0)))
            p0, h0, p1, h1 = p1, h1, p2, lie(W, pole, p2)
        c = arm_clearance(hero, "L")
        if min(c["forearm"], c["upperarm"], c.get("sleeve", 1.0)) >= 0.001:
            break
    hero["left_clearance"] = dict(c, lift=lift, pitch=p1)
    rest = {"loc": W, "fingers": _heading(FORE_ON_STONE[0], p1), "palm": palm, "pole": pole}
    pose_arm(hero, "L", rest["loc"], rest["fingers"], palm, pole, frame=frame)
    flat_hand(hero, "L", frame=frame)
    return rest


def plant(hero, side, rest, frames, slack=0.004, twist_share=0.5):
    """Keep a resting hand where it lies while he moves: the arm is solved and keyed on every frame
    with the wrist at rest["loc"], turned the same way (rest from left_on_stone()). When he leans
    too far for the arm to reach, the hand slides along the stone towards him instead of lifting."""
    rig = hero["rig"]
    reach = sum(rig.data.bones[f"{n}.{side}"].length
                for n in ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02")) - slack
    turn = wrist_matrix(rig, side, rest["loc"], rest["fingers"], rest["palm"]).to_3x3().to_4x4()
    home = Vector(rest["loc"])

    def wrist(f):
        S = joint(hero, f"upperarm01.{side}")
        d = home - S
        W = home.copy()
        if d.length > reach:
            flat = Vector((d.x, d.y, 0.0)).normalized()
            W = S + flat * math.sqrt(max(reach * reach - d.z * d.z, 0.0)) + Vector((0.0, 0.0, d.z))
        return Matrix.Translation(W) @ turn
    A.bake_arm(rig, side, frames, wrist, lambda f: Vector(rest["pole"]), twist_share)
    _update()


def lounge(hero, frame=None):
    """His opening pose (see the module doc). Call after place()."""
    bones(hero, LOUNGE_TORSO, frame)
    sR = joint(hero, "upperarm01.R")
    # left arm resting along the stone edge, the hand lying on the stone (not in it)
    hero["left_rest"] = left_on_stone(hero, frame)
    # right arm down in the water by his side, hand by his thigh
    pose_arm(hero, "R", (sR.x - 0.1, sR.y - 0.16, sR.z - 0.52),
             fingers=(-0.15, -0.35, -1.0), palm=(1.0, 0.0, 0.0), pole=(-0.35, 1.0, -0.2), curl=LOUNGE_CURL, frame=frame)
    C.face(hero["body"], BLISS, frame)
