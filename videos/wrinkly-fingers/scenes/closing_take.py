"""His performance for shots 12-16 in the pool, animated once as one take (video frames 496-750)
and cut by the shot cameras (shot 14, the tyre, is a cutaway while he lifts the marble out):

  shot 12 (496-528) "But why?": his right hand up in front of his face, he squints at his
                    wrinkly fingertips, baffled, head tilted; his red "?" pops up over his head.
  shot 13 (529-600) "Scientists think wrinkles grip wet things better,": he reaches down into the
                    water; under water, his fingers pinch the glass marble off the tiled step in
                    front of him and lift it without slipping.
  (shot 14, 601-642: the tyre; meanwhile he brings the marble up out of the water)
  shot 15 (643-687) "So those raisin fingers?": he holds the marble up to the sun between his
                    fingertips, admiring it, water dripping; then a proud grin.
  shot 16 (688-750) "Built-in rain tyres.": he tosses the marble back into the pool and leans
                    back against the edge as in shot 01, eyes closing, as the light turns golden.

perform(shot) builds him in the pool and keys the take shifted so that the shot's first frame is
1. The marble's path (on the step, in his pinch, flying, sinking) is keyed by marble().
"""
import math

import bpy
import numpy as np
from mathutils import Vector

import acting as A
import character as C
import opening_take as OPEN
import pool_acting as PA
import pool_set as PS
import swimmer as SW
import vfx_kit as V
import wrinkles as WR

SHOTS = {"12": (496, 528), "13": (529, 600), "15": (643, 687), "16": (688, 750)}
START, END = 496, 750
QUESTION = 505                     # the "?" on "why?"
DOWN = (527, 557)                  # the hand goes down to the marble
SURFACE_IN, SURFACE_OUT = 541, 611
PINCH = (557, 562)                 # thumb and finger close on it
LIFT = (566, 636)                  # up out of the water and up to the sun
TOSS = (690, 697)                  # wind up ... let go
LEAN = (700, 724)                  # he leans back and his arm goes back in the water
STEP_TOP = -0.45                   # the tiled step the marble lies on (shot 13 builds it)
MARBLE_R = 0.008

BAFFLED = {"browDownLeft": 0.7, "browOuterUpRight": 0.8, "browInnerUp": 0.3, "eyeSquintLeft": 0.75, "eyeSquintRight": 0.35,
           "eyeLookDownLeft": 0.45, "eyeLookDownRight": 0.45, "eyeLookInLeft": 0.15, "eyeLookOutRight": 0.15,
           "mouthLeft": 0.35, "mouthPressLeft": 0.4, "mouthPucker": 0.15, "noseSneerLeft": 0.25}
FOCUS = {"eyeLookDownLeft": 0.75, "eyeLookDownRight": 0.75, "browDownLeft": 0.25, "browDownRight": 0.25,
         "mouthPressLeft": 0.3, "mouthPressRight": 0.3}
ADMIRE = {"eyeLookUpLeft": 0.55, "eyeLookUpRight": 0.55, "browInnerUp": 0.4, "browOuterUpLeft": 0.35,
          "browOuterUpRight": 0.35, "mouthSmileLeft": 0.75, "mouthSmileRight": 0.75, "cheekSquintLeft": 0.35,
          "cheekSquintRight": 0.35, "eyeWideLeft": 0.2, "eyeWideRight": 0.2}
GRIN = {"mouthSmileLeft": 0.95, "mouthSmileRight": 0.95, "mouthUpperUpLeft": 0.25, "mouthUpperUpRight": 0.25,
        "cheekSquintLeft": 0.55, "cheekSquintRight": 0.55, "eyeSquintLeft": 0.3, "eyeSquintRight": 0.3, "jawOpen": 0.08,
        "mouthDimpleLeft": 0.3, "mouthDimpleRight": 0.3}
FACE = [(START, OPEN.CURIOUS), (502, BAFFLED), (526, BAFFLED), (536, FOCUS), (600, FOCUS), (628, ADMIRE), (668, ADMIRE),
        (676, GRIN), (712, GRIN), (726, PA.BLISS), (END, PA.BLISS)]

TILT = {"neck01": (6, -3, 0), "neck02": (4, -3, 4), "head": (13, -10, 9), "spine02": (3, 0, 0)}
REACH = {"spine01": (7, 0, 0), "spine02": (13, 0, 0), "neck01": (9, 0, 0), "neck02": (6, -4, 0), "head": (15, -10, 0)}
LOOK_UP = {"neck01": (-9, -3, 0), "neck02": (-7, -3, 0), "head": (-12, -9, 0), "spine02": (-2, 0, 0)}
TO_CAMERA = {"neck01": (-3, 0, 0), "neck02": (-2, 0, 0), "head": (-2, -4, 2), "spine02": (0, 0, 0)}
TOSSING = {"spine02": (5, 0, 0), "neck01": (2, 0, 0), "head": (4, -4, 0)}
BODY = [(START, OPEN.LOOK_AT_HAND), (503, TILT), (526, TILT), (545, REACH), (596, REACH), (626, LOOK_UP), (668, LOOK_UP),
        (678, TO_CAMERA), (690, TO_CAMERA), (698, TOSSING), (LEAN[1], PA.LOUNGE_TORSO), (END, PA.LOUNGE_TORSO)]

OPEN_REACH = {"thumb": (0, 4, 4), "index": (4, 6, 4), "middle": (6, 8, 5), "ring": (8, 10, 6), "little": (10, 12, 7)}
GRIP_REST = {"index": (22, 34, 18), "middle": (12, 18, 10), "ring": (16, 22, 12), "little": (20, 26, 14)}
# (an "OK" pinch: the other fingers stay loose; curled in, it read as a fist hiding the marble)


DUCK_REST = (0.172, -0.037)        # where the rubber duck came to rest in shot 01, by his left side


def pool_scene(shot, chop=1.3, dense=False):
    """The pool for one of these shots (built before him), his take, and the duck resting by his
    left side. Returns (pool parts, take)."""
    parts = PS.build(duck_at=None, sun_az=30, sun_el=42, chop=chop)
    parts["sun"].data.color = PS.H("#FFE2BC")                     # the afternoon light of shots 02-03
    take = perform(shot, dense=dense)
    parts["duck"] = PS.duck(at=DUCK_REST, heading=-70, speed=1.0)
    sL, sR = PA.joint(take["hero"], "upperarm01.L"), PA.joint(take["hero"], "upperarm01.R")
    PS.body_waves(parts["water"], ((sL.x + sR.x) / 2, sL.y - 0.05), (abs(sL.x - sR.x) / 2 - 0.03, 0.1))   # as in shot 01
    bpy.context.scene.frame_set(1)
    return parts, take


def step_marble(hero):
    """Where the marble lies on the step, in front of his right side (and the step's centre)."""
    sR = PA.joint(hero, "upperarm01.R")
    return Vector((sR.x - 0.07, sR.y - 0.42, STEP_TOP + MARBLE_R))


def tips(hero, side="R"):
    rig = hero["rig"]
    W = rig.matrix_world
    return W @ rig.pose.bones[f"finger1-3.{side}"].tail, W @ rig.pose.bones[f"finger2-3.{side}"].tail


def pinch(hero, side="R", gap=0.024, frame=None):
    """Thumb and index meet around the marble: the other fingers curl in, and the thumb's
    rotation is searched until its tip is `gap` from the index tip, in front of the palm.
    Keys it on `frame`. Returns the pinch point (between the tips)."""
    rig = hero["rig"]
    PA.hand_shape(hero, side, {**GRIP_REST, "thumb": (10, 20, 15)}, together=0.9, frame=None)
    base, mid, end = (rig.pose.bones[f"finger1-{k}.{side}"] for k in (1, 2, 3))
    for pb in (base, mid, end):
        pb.rotation_mode = "XYZ"
    best, best_x = None, None
    rng = np.random.default_rng(1)

    def cost(x):
        base.rotation_euler = tuple(math.radians(a) for a in x[:3])
        mid.rotation_euler = (math.radians(x[3]), 0.0, 0.0)
        end.rotation_euler = (math.radians(x[4]), 0.0, 0.0)
        bpy.context.view_layer.update()
        t, i = tips(hero, side)
        return abs((t - i).length - gap) + 0.002 * sum(abs(a) for a in x) / 100.0

    x = np.array([20.0, 0.0, 10.0, 25.0, 20.0])
    best, best_x = cost(x), x.copy()
    step = 16.0
    while step > 0.5:                                     # coordinate descent, then finer
        improved = False
        for k in range(5):
            for d in (step, -step):
                y = best_x.copy()
                y[k] = np.clip(y[k] + d, -60, 80)
                c = cost(y)
                if c < best:
                    best, best_x, improved = c, y, True
        if not improved:
            step /= 2
    cost(best_x)
    if frame is not None:
        for pb in rig.pose.bones:
            if pb.name.startswith("finger") and pb.name.endswith("." + side):
                pb.keyframe_insert("rotation_euler", frame=frame)
    t, i = tips(hero, side)
    return (t + i) / 2


def _arm_poses(hero, off):
    """The right hand's path (take frames): from his face down to the marble, up to the sun,
    the toss, and back into the water."""
    bpy.context.scene.frame_set(START - off)
    sR = PA.joint(hero, "upperarm01.R")
    head = PA.joint(hero, "head")
    m = step_marble(hero)
    face = (OPEN.raised_hand(hero, START - off) + Vector((-0.06, 0.0, -0.035)), (0.05, 0.1, 1.0), (0.22, 1.0, -0.02),
            (-1.0, 0.3, -1.0))                                    # a little to his right and lower: his face shows
    face2 = (face[0] + Vector((0.004, 0.0, -0.01)),) + face[1:]
    lower = (Vector((sR.x - 0.1, sR.y - 0.36, 0.06)), (0.0, -0.6, -0.8), (0.0, -0.3, -1.0), (-1.0, 0.3, -0.6))
    above = (m + Vector((0.004, 0.02, 0.105)), (0.0, -0.15, -1.0), (0.2, -1.0, 0.0), (-1.0, 0.6, -0.2))
    at = (m + Vector((0.004, 0.02, 0.078)), (0.0, -0.12, -1.0), (0.2, -1.0, 0.0), (-1.0, 0.6, -0.2))
    lift1 = (m + Vector((0.0, 0.03, 0.2)), (0.0, -0.2, -1.0), (0.2, -1.0, 0.0), (-1.0, 0.6, -0.2))
    surface = (Vector((sR.x - 0.12, sR.y - 0.38, -0.02)), (0.0, -0.5, 0.6), (0.2, 0.9, 0.3), (-1.0, 0.3, -0.8))
    up = (head + Vector((-0.1, -0.3, 0.1)), (0.1, -0.1, 1.0), (0.1, 1.0, 0.1), (-1.0, 0.0, -1.0))     # elbow a little bent
    up2 = (up[0] + Vector((0.01, 0.0, 0.012)), (0.18, -0.12, 1.0), (0.05, 1.0, 0.12), (-1.0, 0.0, -1.0))
    wind = (up[0] + Vector((0.02, 0.08, -0.04)), (0.1, 0.2, 1.0), (0.1, 1.0, -0.1), (-1.0, 0.0, -1.0))
    throw = (up[0] + Vector((-0.02, -0.16, -0.12)), (0.0, -0.8, 0.5), (0.0, -0.5, -1.0), (-1.0, 0.0, -1.0))
    rest = (Vector((sR.x - 0.1, sR.y - 0.16, sR.z - 0.52)), (-0.15, -0.35, -1.0), (1.0, 0.0, 0.0), (-0.35, 1.0, -0.2))
    keys = [(START, face), (DOWN[0], face2), (SURFACE_IN - 4, lower), (DOWN[1] - 5, above), (DOWN[1], at), (PINCH[1] + 2, at),
            (LIFT[0] + 14, lift1), (SURFACE_OUT - 2, surface), (LIFT[1], up), (668, up2), (TOSS[0], up2), (TOSS[0] + 4, wind),
            (TOSS[1], throw), (LEAN[1], rest), (END, rest)]
    return [(f - off,) + p for f, p in keys]


def perform(shot, dense=False):
    """Build him and key the take for one shot. Returns dict(hero, off, n, pinch_frames)."""
    lo, hi = SHOTS[shot]
    off = lo - 1
    hero = SW.build()
    WR.setup(hero)
    WR.set_amount(hero, 1.0)                                    # his fingers are wrinkly by now
    PA.place(hero)
    PA.lounge(hero, frame=START - off)                          # the left arm stays on the stone edge
    PS.underwater_hero(hero)
    SW.set_waterline(hero, PS.WATER_Z)
    PA.key_bones(hero, BODY, off)
    PA.key_face(hero, FACE, off)
    # right hand: looking, open on the way down, the pinch, open after the toss
    PA.hand_shape(hero, "R", PA.LOOK_HAND, frame=START - off)
    PA.hand_shape(hero, "R", PA.LOOK_HAND, frame=DOWN[0] - off)
    PA.hand_shape(hero, "R", OPEN_REACH, frame=DOWN[1] - 6 - off)
    PA.hand_shape(hero, "R", OPEN_REACH, frame=PINCH[0] - off)
    PA.arm_path(hero, "R", _arm_poses(hero, off), range(START - off, END - off + 1))
    bpy.context.scene.frame_set(PINCH[1] - off)
    pinch(hero, "R", frame=PINCH[1] - off)
    bpy.context.scene.frame_set(TOSS[1] - off)
    pinch(hero, "R", frame=TOSS[1] - off)
    PA.hand_shape(hero, "R", OPEN_REACH, frame=TOSS[1] + 2 - off)
    PA.hand_shape(hero, "R", PA.RELAXED_HAND, frame=LEAN[1] - off)
    if dense:
        WR.dense(hero, levels=3)
    bpy.context.scene.frame_set(1)
    return {"hero": hero, "off": off, "n": hi - lo + 1}


def pinch_point(hero, frame):
    bpy.context.scene.frame_set(frame)
    t, i = tips(hero)
    return (t + i) / 2


def marble(take, col=None):
    """The marble: it lies where his fingertips close on it (on the step) until he pinches it,
    stays in his fingertips until he lets go, then flies, plops into the pool and sinks. Keys
    it on every frame of the shot (shot frames). Returns dict(ob, rest (where it lay),
    splash (frame or None), splash_at)."""
    hero, off = take["hero"], take["off"]
    sc = bpy.context.scene
    grab, release = PINCH[1] - off, TOSS[1] - off
    rest = pinch_point(hero, grab)
    ob = PS.marble(col, at=tuple(rest))
    fps = sc.render.fps
    frames = list(range(sc.frame_start - 1, sc.frame_end + 2))
    need = {f for f in frames if grab <= f <= release}
    if max(frames) > release:
        need |= {release - 1, release, release + 1}
    hold = {f: pinch_point(hero, f) for f in sorted(need)}
    splash, splash_at = None, None
    if max(frames) > release:
        p0 = hold[release]
        v = (hold[release + 1] - hold[release - 1]) * fps / 2 + Vector((0.0, -0.4, 0.9))   # a flick up and out
    for f in frames:
        if f < grab:
            p = rest
        elif f <= release:
            p = hold[f]
        else:
            t = (f - release) / fps
            p = p0 + v * t + Vector((0, 0, -4.905 * t * t))
            if p.z < PS.WATER_Z:
                if splash is None:
                    splash, splash_at = f, p.copy()
                p = Vector((splash_at.x, splash_at.y, PS.WATER_Z - 0.01 - 0.35 * (f - splash) / fps))
        ob.location = p
        ob.keyframe_insert("location", frame=f)
    V.ease_id(ob, "LINEAR")
    sc.frame_set(1)
    return {"ob": ob, "rest": rest, "splash": splash, "splash_at": splash_at}


def glint(marble_ob, toward=(0.0, -0.4, 0.9), strength=40.0):
    """A sun glint on the marble (a tiny bright spot on its sunny side) that rides with it: the
    marble is only 16 mm, and the glint is what you see when it is held up or thrown."""
    import claude_sculpt_kit as K
    d = Vector(toward).normalized() * MARBLE_R * 0.75
    g = K.ellipsoid("Marble_Glint", (0, 0, 0), (MARBLE_R * 0.22,) * 3, segments=12, col=marble_ob.users_collection[0])
    V.assign(g, V.emission("Marble_Glint", (1.0, 0.95, 0.85), strength))
    g.parent = marble_ob
    g.location = d
    return g
