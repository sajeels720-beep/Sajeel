"""His performance for shots 01-03, animated once as one continuous take (153 frames) and cut by
three cameras, so the acting carries across the cuts:

  shot 01 (take 1-69)    "You stay in the pool too long,": a time-lapse. He leans back against
                          the pool wall in the sun, eyes closed, blissful; only the light, the water
                          and the duck race around him.
  shot 02 (take 70-108)  "and your fingers turn into": he opens his eyes, lowers his head and lifts
                          his right hand out of the water to look at his fingertips.
  shot 03 (take 109-153) "wrinkly raisins.": his fingertips crumple into wrinkles (WRINKLES).

perform(shot) builds him in the pool and keys the take shifted so that the shot's first frame is 1.
The water-related events (where the hand breaks the surface, the drops that fall from it) are in
take frames too, for the shot scripts.
"""
import math

import bpy
import numpy as np
from mathutils import Vector

import character as C
import pool_acting as PA
import pool_set as PS
import swimmer as SW
import wrinkles as WR

SHOTS = {"01": (1, 69), "02": (70, 108), "03": (109, 153)}
TIMELAPSE = (1, 69)                       # shot 01 runs fast: the sun swings, the water races
OPEN_EYES = 72                            # after the time-lapse he opens his eyes...
LIFT = (74, 100)                          # ...and lifts his right hand out of the water
SURFACE = 84                              # the hand breaks the surface
WRINKLES = [(1, 0.08), (112, 0.1), (141, 1.0)]   # the pads crumple on "wrinkly raisins"

BLISS = PA.BLISS
AWAKE = {"eyeBlinkLeft": 0.15, "eyeBlinkRight": 0.15, "mouthSmileLeft": 0.25, "mouthSmileRight": 0.25,
         "browInnerUp": 0.2}
LOOKING = {"eyeLookDownLeft": 0.55, "eyeLookDownRight": 0.55, "eyeLookInLeft": 0.15, "eyeLookOutRight": 0.15,
           "browInnerUp": 0.45, "browOuterUpLeft": 0.3, "browOuterUpRight": 0.3, "mouthSmileLeft": 0.1,
           "mouthSmileRight": 0.1}
CURIOUS = {"eyeLookDownLeft": 0.5, "eyeLookDownRight": 0.5, "eyeLookInLeft": 0.15, "eyeLookOutRight": 0.15,
           "browInnerUp": 0.7, "browOuterUpLeft": 0.5, "browOuterUpRight": 0.5, "eyeWideLeft": 0.45,
           "eyeWideRight": 0.45, "mouthPucker": 0.2}
FACE = [(1, BLISS), (OPEN_EYES - 4, BLISS), (OPEN_EYES, AWAKE), (80, LOOKING), (98, CURIOUS), (153, CURIOUS)]

LOUNGE = PA.LOUNGE_TORSO
HEAD_UP = {"neck01": (-3, 0, 0), "neck02": (-2, 0, 0), "head": (0, 0, 2), "spine02": (0, 0, 0)}
LOOK_AT_HAND = {"neck01": (6, -3, 0), "neck02": (4, -3, 0), "head": (13, -8, 0), "spine02": (3, 0, 0)}
BODY = [(1, LOUNGE), (OPEN_EYES - 2, LOUNGE), (78, HEAD_UP), (94, LOOK_AT_HAND), (153, LOOK_AT_HAND)]


def raised_hand(hero, frame):
    """Where the right hand ends up: in front of his face, a little below his eyes and to his
    right, fingers up, palm towards him (pads facing his eyes)."""
    bpy.context.scene.frame_set(frame)
    head = PA.joint(hero, "head")
    return head + Vector((-0.07, -0.31, -0.15))


def _lift_poses(hero, off):
    """The right hand's path out of the water and up to his face (take frames)."""
    bpy.context.scene.frame_set(OPEN_EYES - off)
    sR = PA.joint(hero, "upperarm01.R")
    rest = (Vector((sR.x - 0.1, sR.y - 0.16, sR.z - 0.52)), (-0.15, -0.35, -1.0), (1.0, 0.0, 0.0), (-0.35, 1.0, -0.2))
    dip = (rest[0] + Vector((0.0, 0.015, -0.03)),) + rest[1:]
    out_of_water = (Vector((sR.x - 0.15, sR.y - 0.36, PS.WATER_Z + 0.07)), (-0.15, -0.55, 0.8), (0.55, 0.75, 0.35),
                    (-0.8, 0.6, -0.8))
    top = raised_hand(hero, LIFT[1] - off)
    up = (top, (0.12, 0.05, 1.0), (0.1, 1.0, -0.05), (-1.0, 0.3, -1.0))
    settle = (top + Vector((0.0, 0.006, -0.01)), (0.1, 0.06, 1.0), (0.12, 1.0, -0.04), (-1.0, 0.3, -1.0))
    turn = (top + Vector((0.004, 0.0, -0.006)), (0.05, 0.1, 1.0), (0.22, 1.0, -0.02), (-1.0, 0.3, -1.0))
    return [(f - off,) + p for f, p in ((OPEN_EYES, rest), (LIFT[0], dip), (SURFACE + 2, out_of_water),
                                        (LIFT[1], up), (LIFT[1] + 5, settle), (153, turn))]


def perform(shot, dense=False):
    """Build him and key the take for one shot. Returns dict(hero, off, n)."""
    lo, hi = SHOTS[shot]
    off = lo - 1
    hero = SW.build()
    WR.setup(hero)
    PA.place(hero)
    PA.lounge(hero, frame=1 - off)                         # keys the lounge pose (arms, fingers, face)
    PA.lounge(hero, frame=OPEN_EYES - off)
    PS.underwater_hero(hero)
    SW.set_waterline(hero, PS.WATER_Z)
    PA.key_bones(hero, BODY, off)
    PA.key_face(hero, FACE, off)
    PA.plant(hero, "L", hero["left_rest"], range(1 - off, 153 - off + 1))   # his left hand stays put on the stone
    PA.hand_shape(hero, "R", PA.RELAXED_HAND, frame=OPEN_EYES - off)
    PA.hand_shape(hero, "R", PA.LOOK_HAND, frame=LIFT[1] - 4 - off)
    if hi >= LIFT[0]:
        PA.arm_path(hero, "R", _lift_poses(hero, off), range(OPEN_EYES - off, 153 - off + 1))
    WR.key(hero, [(f - off, a) for f, a in WRINKLES])
    if dense:                                              # after the bake: the dense mesh is slow to pose
        WR.dense(hero, levels=3)
    bpy.context.scene.frame_set(1)
    return {"hero": hero, "off": off, "n": hi - lo + 1}


def hand_points(hero, frame, count=6, seed=0):
    """World positions of the lowest points of his right hand (where water drips from) on a
    frame (shot frames)."""
    body = hero["body"]
    bpy.context.scene.frame_set(frame)
    if "_hand_idx" not in hero:
        W = WR._group_weights(body, [g.name for g in body.vertex_groups
                                     if g.name.endswith(".R") and g.name.startswith(("finger", "wrist", "metacarpal"))])
        sel = np.zeros(len(body.data.vertices), bool)
        for arr in W.values():
            sel |= arr > 0.3
        hero["_hand_idx"] = np.where(sel)[0]
    P = C.evaluated_points(body)[hero["_hand_idx"]]
    low = P[np.argsort(P[:, 2])[:40]]
    rnd = np.random.default_rng(seed + frame)
    return [Vector(low[i]) for i in rnd.choice(len(low), size=min(count, len(low)), replace=False)]


def drips(hero, frames, per_frame=1, radius=0.0021):
    """Drops of water falling from the lowest points of his hand on these shot frames.
    Returns [(object, landing frame, (x, y))] for ripples where they land."""
    out = []
    for f in frames:
        for i, p in enumerate(hand_points(hero, f, count=per_frame, seed=7 * f)):
            if p.z <= PS.WATER_Z + 0.01:
                continue
            out.append(PS.falling_drop(f"Drop_{f}_{i}", f, p, vel=(0.0, 0.0, -0.15), radius=radius * (0.8 + 0.4 * ((f + i) % 3) / 2)))
    return out
