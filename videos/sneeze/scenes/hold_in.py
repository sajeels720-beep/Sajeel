"""Her performance for shots 03-05, animated once as one continuous take (171 frames) and cut
by three cameras, so the acting carries across the cuts:

  shot 03 (take 1-60)    "so you pinch your nose, shut your mouth,": "ahh... ahh..." (head
                          back, mouth opening), then her right hand snaps up and pinches her
                          nose (frame 34) and her lips press shut; the seed flutters off.
  shot 04 (take 61-123)  "and hold it in.": the sneeze hits inside (frame 72): her body
                          jolts, her cheeks balloon, her eyes pop wide; she goes red.
  shot 05 (take 124-171) "Big mistake.": holding it, eyes bulging, cheeks full.

perform(shot) builds her and keys the take shifted so that the shot's first frame is 1.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

import acting as A
import character as C
import dandelion_set as DS
import heroine as HR
import vfx_kit as V

H = V.hex_lin
SHOTS = {"03": (1, 60), "04": (61, 123), "05": (124, 171)}
CU_LOOK, CU_END_DIST, CU_LENS = (-22, 3), 0.62, 85       # shot 04 ends where shot 05 starts (invisible cut)
CU_AIM = Vector((0.0, 0.0, -0.012))                      # from the nose (at take frame 60)
CONTACT = 34                                   # the fingers close on her nose
PINCH_UP = Vector((0.2, 0.3, 1.0))             # wrist -> fingers: the hand comes up from below the nose, a little from her right
ELBOW_POLE = -75                               # IK pole angle: elbow low in front of her right side
SHRUG = [(1, 0.0), (27, 0.0), (33, 1.0), (60, 1.0), (72, 1.0), (75, 1.3), (85, 1.0), (171, 1.0)]  # 72: the hit
SHRUG_UP, SHRUG_FWD = 9.0, 12.0                # degrees the right collarbone lifts and rolls forward at 1.0
HIT = 72                                       # the sneeze hits inside (also in SHRUG below)

S2_END = {"noseSneerLeft": 0.8, "noseSneerRight": 0.8, "flare": 0.9, "nostrils_wide": 0.35, "mouthPressLeft": 0.25,
          "mouthPressRight": 0.25, "cheekSquintLeft": 0.55, "cheekSquintRight": 0.55, "eyeSquintLeft": 0.6,
          "eyeSquintRight": 0.6, "eyeBlinkLeft": 0.5, "eyeBlinkRight": 0.5, "browDownLeft": 0.35, "browDownRight": 0.35,
          "browInnerUp": 0.45}


def _both(**kv):
    """Same value for the Left and Right face units: _both(eyeBlink=0.5) -> both eyes."""
    out = {}
    for k, v in kv.items():
        if k in ("jawOpen", "browInnerUp", "cheekPuff", "flare", "nostrils_wide", "mouthClose", "mouthFunnel",
                 "mouthPucker", "mouthRollLower", "mouthRollUpper", "mouthShrugUpper", "mouthShrugLower"):
            out[k] = v
        else:
            out[k + "Left"], out[k + "Right"] = v, v
    return out


FACE = [  # (take frame, face units); anything not listed is 0 at that key
    (1, S2_END),
    (9, _both(noseSneer=1.0, flare=1.1, nostrils_wide=0.5, jawOpen=0.22, mouthStretch=0.2, eyeBlink=0.72, eyeSquint=0.7,
              cheekSquint=0.6, browInnerUp=0.85, browDown=0.2)),                      # "ahh..."
    (14, _both(noseSneer=0.8, flare=0.8, nostrils_wide=0.35, jawOpen=0.12, eyeBlink=0.6, eyeSquint=0.6, cheekSquint=0.5,
               browInnerUp=0.6, browDown=0.25)),
    (23, _both(noseSneer=1.1, flare=1.3, nostrils_wide=0.6, jawOpen=0.38, mouthStretch=0.3, mouthUpperUp=0.12,
               eyeBlink=0.85, eyeSquint=0.85, cheekSquint=0.75, browInnerUp=1.0, browDown=0.15)),  # "ahh..." bigger
    (30, _both(noseSneer=1.1, flare=1.3, nostrils_wide=0.6, jawOpen=0.42, mouthStretch=0.35, mouthUpperUp=0.12,
               eyeBlink=0.9, eyeSquint=0.9, cheekSquint=0.8, browInnerUp=1.0, browDown=0.15)),     # about to blow
    (CONTACT, _both(noseSneer=0.5, flare=0.2, mouthPress=0.8, mouthRollLower=0.35, mouthRollUpper=0.25, eyeBlink=0.9,
                    eyeSquint=0.9, cheekSquint=0.7, browInnerUp=0.7, browDown=0.5)),          # caught: lips slam shut
    (40, _both(noseSneer=0.45, flare=0.15, mouthPress=0.7, mouthRollLower=0.3, mouthRollUpper=0.2, cheekPuff=0.1,
               eyeBlink=0.88, eyeSquint=0.85, cheekSquint=0.65, browInnerUp=0.75, browDown=0.5)),
    (60, _both(noseSneer=0.45, flare=0.15, mouthPress=0.6, mouthRollLower=0.25, mouthRollUpper=0.15, cheekPuff=0.35,
               eyeBlink=0.9, eyeSquint=0.85, cheekSquint=0.6, browInnerUp=0.85, browDown=0.45)),  # pressure builds
    (70, _both(noseSneer=0.45, flare=0.1, mouthPress=0.6, mouthRollLower=0.2, cheekPuff=0.45, eyeBlink=0.92,
               eyeSquint=0.9, cheekSquint=0.6, browInnerUp=0.9, browDown=0.5)),
    (HIT, _both(noseSneer=0.45, flare=0.1, mouthPress=0.65, mouthRollLower=0.2, cheekPuff=0.5, eyeBlink=0.95,
                eyeSquint=0.95, cheekSquint=0.6, browInnerUp=0.9, browDown=0.55)),
    (HIT + 2, _both(noseSneer=0.3, mouthPress=0.9, mouthRollLower=0.15, cheekPuff=1.75, eyeWide=1.4, browInnerUp=1.0,
                    browOuterUp=1.0)),                                                 # BOOM: cheeks balloon, eyes pop
    (HIT + 5, _both(noseSneer=0.3, mouthPress=0.85, mouthRollLower=0.15, cheekPuff=1.45, eyeWide=1.25, browInnerUp=0.95,
                    browOuterUp=0.9)),
    (HIT + 9, _both(noseSneer=0.3, mouthPress=0.85, mouthRollLower=0.15, cheekPuff=1.55, eyeWide=1.35, browInnerUp=1.0,
                    browOuterUp=0.95)),
    (100, _both(noseSneer=0.3, mouthPress=0.85, mouthRollLower=0.15, cheekPuff=1.5, eyeWide=1.3, browInnerUp=1.0,
                browOuterUp=0.95)),
    (102, _both(noseSneer=0.35, mouthPress=0.9, mouthRollLower=0.15, cheekPuff=1.65, eyeWide=1.5, browInnerUp=1.05,
                browOuterUp=1.0)),                                                     # a second, smaller hiccup
    (106, _both(noseSneer=0.3, mouthPress=0.85, mouthRollLower=0.15, cheekPuff=1.5, eyeWide=1.35, browInnerUp=1.0,
                browOuterUp=0.95)),
    (128, _both(noseSneer=0.3, mouthPress=0.85, mouthRollLower=0.15, cheekPuff=1.6, eyeWide=1.5, browInnerUp=1.05,
                browOuterUp=1.0)),                                                     # "Big mistake.": even bigger
    (171, _both(noseSneer=0.3, mouthPress=0.85, mouthRollLower=0.15, cheekPuff=1.6, eyeWide=1.45, browInnerUp=1.0,
                browOuterUp=1.0)),
]
BONES = {  # pose bone: [(take frame, (x, y, z) degrees)]; +x bends forward (chin down) on head/neck/spine
    # after the pinch she stays bowed a little into her hand, shoulders hunched (holding it in)
    "head": [(1, (-4, 0, 0.8)), (9, (-10, 0, 2)), (14, (-6, 0, 1)), (23, (-15, 0, 2.5)), (29, (-17, 0, 2)),
             (CONTACT, (11, 0, -1)), (38, (8, 0, 0)), (60, (7, 0, 0)), (HIT, (7, 0, 0)), (HIT + 1, (13, 0, 1)),
             (HIT + 4, (4, 0, -0.5)), (HIT + 8, (8, 0, 0)), (HIT + 13, (7, 0, 0)), (100, (7, 0, 0)), (101, (10, 0, 0)),
             (105, (7, 0, 0)), (171, (7, 0, 0))],
    "neck01": [(1, (0, 0, 0)), (23, (-4, 0, 0)), (29, (-5, 0, 0)), (CONTACT, (5, 0, 0)), (40, (4, 0, 0)),
               (HIT, (4, 0, 0)), (HIT + 1, (7, 0, 0)), (HIT + 5, (3, 0, 0)), (HIT + 10, (4, 0, 0)), (171, (4, 0, 0))],
    "spine01": [(1, (0, 0, 0)), (9, (-2, 0, 0)), (14, (-1, 0, 0)), (23, (-4, 0, 0)), (29, (-4.5, 0, 0)),
                (CONTACT, (5, 0, 0)), (40, (4, 0, 0)), (HIT, (4, 0, 0)), (HIT + 1, (9, 0, 0)), (HIT + 4, (2, 0, 0)),
                (HIT + 9, (4, 0, 0)), (101, (6, 0, 0)), (105, (4, 0, 0)), (171, (4, 0, 0))],
}
SKIN_FLUSH = [(1, "#B98466"), (60, "#B98466"), (HIT + 2, "#BF7C62"), (115, "#C76C58"), (171, "#CA6553")]


def _key_face(body, off):
    names = sorted({k for _, vals in FACE for k in vals})
    for g, vals in FACE:
        C.face(body, {k: vals.get(k, 0.0) for k in names}, frame=g - off)


def _key_bones(rig, off):
    for name, keys in BONES.items():
        pb = rig.pose.bones[name]
        pb.rotation_mode = "XYZ"
        for g, rot in keys:
            pb.rotation_euler = tuple(math.radians(a) for a in rot)
            pb.keyframe_insert("rotation_euler", frame=g - off)
    V.ease_id(rig)


def skin_tint_socket(hero):
    """The colour socket of the skin tint (a multiply inside MPFB's skin node group)."""
    for m in hero["body"].data.materials:
        for g in (n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeGroup"):
            for n in g.node_tree.nodes:
                if n.bl_idname == "ShaderNodeMix" and n.blend_type == "MULTIPLY" and n.inputs[6].is_linked:
                    return n.inputs[7]
    return None


def _key_flush(hero, off):
    sock = skin_tint_socket(hero)
    if sock is None:
        return
    for g, hexc in SKIN_FLUSH:
        sock.default_value = (*H(hexc), 1)
        sock.keyframe_insert("default_value", frame=g - off)


def _head_matrix(rig):
    return rig.matrix_world @ rig.pose.bones["head"].matrix


def _same_hemisphere(q, ref):
    return q if q.dot(ref) >= 0 else -q


def _key_shrug(rig, off):
    """Her right shoulder lifts and rolls forward as she pinches (it lets the elbow hang lower).
    The right collarbone runs from the sternum out to -X: turning it about +Y lifts the
    shoulder end, about +Z brings it forward (-Y)."""
    pb = rig.pose.bones["clavicle.R"]
    pb.rotation_mode = "XYZ"
    sc = bpy.context.scene
    sc.frame_set(1 - off)
    rest = rig.matrix_world @ pb.matrix
    for g, k in SHRUG:
        R = Matrix.Rotation(math.radians(SHRUG_FWD * k), 3, "Z") @ Matrix.Rotation(math.radians(SHRUG_UP * k), 3, "Y")
        W = Matrix.Translation(rest.translation) @ (R @ rest.to_3x3()).to_4x4()
        pb.matrix = rig.matrix_world.inverted() @ W
        pb.keyframe_insert("rotation_euler", frame=g - off)
    V.ease_id(rig)


def _key_hand(hero, off, frames):
    """The right hand: hangs, dips (anticipation), snaps up to the nose, pinches at CONTACT
    and from then on rides on her head. frames: the shot's own frame range (to bake)."""
    rig = hero["rig"]
    sc = bpy.context.scene
    A.curl(rig, "R", A.RELAXED, frame=1 - off)
    A.curl(rig, "R", A.RELAXED, frame=26 - off)
    open_pinch = dict(A.PINCH, thumb=(-45, 10, 10), index=(10, 20, 10))
    A.curl(rig, "R", open_pinch, frame=31 - off)
    A.curl(rig, "R", A.PINCH, frame=CONTACT - off)
    squeeze = dict(A.PINCH, thumb=(-22, 30, 36), index=(34, 66, 40))
    A.curl(rig, "R", squeeze, frame=CONTACT + 2 - off)
    A.curl(rig, "R", A.PINCH, frame=CONTACT + 6 - off)
    V.ease_id(rig)

    sc.frame_set(1 - off)
    wrist = rig.pose.bones["wrist.R"]
    hang = rig.matrix_world @ wrist.matrix
    h = A.hand_rig(hero)
    h["ik"].pole_angle = math.radians(ELBOW_POLE)
    hand = h["hand"]
    # the pinch, worked out with her head where it is at the moment of contact
    sc.frame_set(CONTACT - off)
    tip, _ = HR.surface_point(hero, hero["nose_tip"])
    nose = tip + Vector((0.0, 0.008, 0.004))                    # between the nostril wings
    loc_c, q_c = A.pinch_pose(rig, nose, up=PINCH_UP)[:2]
    head_c = _head_matrix(rig)
    contact = Matrix.Translation(loc_c) @ q_c.to_matrix().to_4x4()
    q_h = hang.to_quaternion()
    q_c = _same_hemisphere(q_c, q_h)
    approach = [  # (take frame, location, rotation)
        (1, hang.translation, q_h), (24, hang.translation, q_h),
        (27, hang.translation + Vector((0.0, 0.02, -0.025)), q_h),                         # dips back (anticipation)
        (30, Vector((-0.20, -0.31, 1.08)), _same_hemisphere(q_h.slerp(q_c, 0.6), q_h)),    # in front of her chest
        (33, loc_c + Vector((-0.012, -0.045, -0.03)), q_c),                                # just short of the nose
    ]
    for g, loc, q in approach:
        A.key_hand(hand, g - off, loc, q)
    for fc in V.fcurves(hand):                                  # fast out of the dip, slowing into the face
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.easing = "EASE_OUT"
    # from contact on, the hand rides on her head (baked); a small squeeze-in, then it settles
    lo, hi = frames
    into = Vector((0.0, 0.004, 0.0))
    for g in range(max(CONTACT, lo + off - 2), hi + off + 3):
        sc.frame_set(g - off)
        push = into * (1.0 if g in (CONTACT + 1, CONTACT + 2) else 0.5 if g == CONTACT + 3 else 0.0)
        M = _head_matrix(rig) @ head_c.inverted() @ Matrix.Translation(push) @ contact
        A.key_hand(hand, g - off, M.translation, _same_hemisphere(M.to_quaternion(), q_c))
    return h


def _seed_flies_off(hero, off, frames):
    """Shot 02's seed is still on her nose; the "ahh" tilts her head back and it flutters off."""
    col = V.collection("SET_SEED")
    mats = DS.materials()
    seed = DS.loose_seed(col, mats, DS.seed_slots(count=12, rng_seed=21)[5], "Seed_Nose")
    seed.scale = (1.25, 1.25, 1.25)
    sc = bpy.context.scene
    tip = hero["nose_tip"]
    sc.frame_set(1 - off)
    p0, n0 = HR.surface_point(hero, tip)
    axis = (n0 * 0.55 + Vector((0, 0, 1)) * 0.75 + Vector((1, 0, 0)) * 0.35).normalized()
    q0 = DS.frame_z(axis, 0.6).to_quaternion()
    for g in range(1, 7):                                      # still riding on the nose
        sc.frame_set(g - off)
        p, _ = HR.surface_point(hero, tip)
        seed.location = p + axis * DS.PAPPUS_UP * 1.25
        seed.rotation_quaternion = q0
        seed.keyframe_insert("location", frame=g - off)
        seed.keyframe_insert("rotation_quaternion", frame=g - off)
    start = seed.location.copy()
    for g in range(7, 31):                                     # lifts off up and away to her left
        u = (g - 6) / 24
        seed.location = start + Vector((0.09 * u, -0.03 * u, 0.16 * u * u + 0.03 * u))
        up = (Matrix.Rotation(0.15 * math.sin(0.5 * g), 3, "X") @ Matrix.Rotation(0.8 * u, 3, "Z")).to_quaternion()
        seed.rotation_quaternion = q0.slerp(up, min(1.0, u * 2))
        seed.keyframe_insert("location", frame=g - off)
        seed.keyframe_insert("rotation_quaternion", frame=g - off)
    return seed


def perform(shot):
    """Build her and key the take for one shot. Returns dict(hero, hand, off, n)."""
    lo, hi = SHOTS[shot]
    off = lo - 1
    hero = HR.build()
    HR.arms_down(hero)
    HR.nose_shapes(hero)
    hero["nose_tip"] = HR.nose_tip(hero)
    _key_face(hero["body"], off)
    _key_bones(hero["rig"], off)
    _key_flush(hero, off)
    _key_shrug(hero["rig"], off)
    h = _key_hand(hero, off, (1, hi - lo + 1))
    seed = _seed_flies_off(hero, off, (1, hi - lo + 1)) if shot == "03" else None
    bpy.context.scene.frame_set(1)
    return {"hero": hero, "hand": h, "off": off, "n": hi - lo + 1, "seed": seed}


def nose_at(hero, frame):
    """Where her nose tip is on a frame of the current shot."""
    bpy.context.scene.frame_set(frame)
    p, n = HR.surface_point(hero, hero["nose_tip"])
    return p, n
