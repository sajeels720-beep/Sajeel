"""Posing him in the pool (MPFB default rig).

place() stands him on the pool floor, leaning back with his upper back against the wall.
pose_arm() puts a wrist at a world position and turns the hand (fingers along one direction,
palm facing another), bending the elbow towards a pole direction: the exact two-bone solve
from the sneeze video (sneeze/scenes/acting.py), so there are no IK flips.
lounge() is his opening pose: leaning back in the sun, left arm resting along the stone edge,
right arm floating in the water, head tipped back, eyes closed, a blissful smile.

Rig facts: +X on spine, neck and head bones bends forward (chin down); fingers curl about
their local +X; finger1 is the thumb.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

import acting as A
import character as C
import pool_set as PS

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


def lounge(hero, frame=None):
    """His opening pose (see the module doc). Call after place()."""
    bones(hero, LOUNGE_TORSO, frame)
    sL, sR = joint(hero, "upperarm01.L"), joint(hero, "upperarm01.R")
    # left arm resting along the stone edge, elbow bent, hand relaxed on the stone
    pose_arm(hero, "L", (sL.x + 0.36, PS.WALL_Y + 0.15, PS.COPING_TOP + 0.024),
             fingers=(1.0, 0.35, -0.08), palm=(0.0, 0.0, -1.0), pole=(0.5, 0.5, -1.0), curl=LOUNGE_CURL, frame=frame)
    # right arm down in the water by his side, hand by his thigh
    pose_arm(hero, "R", (sR.x - 0.1, sR.y - 0.16, sR.z - 0.52),
             fingers=(-0.15, -0.35, -1.0), palm=(1.0, 0.0, 0.0), pole=(-0.35, 1.0, -0.2), curl=LOUNGE_CURL, frame=frame)
    C.face(hero["body"], BLISS, frame)
