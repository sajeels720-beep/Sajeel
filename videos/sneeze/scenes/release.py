"""Her performance for shots 19-22, one continuous take that picks up where holding it in left
off (nose pinched, cheeks still full, face flushed), cut by four cameras:

  shot 19 (take 1-66)    "So next time you feel one coming,": another seed breaks off the
                          dandelion in front of her and drifts onto her nose (LAND); her eyes
                          cross down at it, her nose twitches and her face scrunches up, "ahh...".
  shot 20 (take 67-108)  "just let it out.": she lets go of her nose (RELEASE), her hand drops
                          to her side, and her head tips back to wind up, "ahh... ahh...".
  shot 21 (take 109-156) the sneeze in slow motion: her head snaps forward (CHOO), droplets and
                          air blast into the dandelion and its seeds burst off (HIT).
  shot 22 (take 157-210) relief: she straightens up, sniffs, smiles at the bald dandelion;
                          its stem still bobbing, the seeds float up and away.

perform(shot) builds her and the dandelion and keys the take so that the shot's first frame
is 1. Everything that moves in more than one shot (the seed, the blast, the seeds) is a
function of the take frame, so the cuts match.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

import acting as A
import character as C
import dandelion_set as DS
import heroine as HR
import hold_in as HOLD
import vfx_kit as V

H = V.hex_lin
SHOTS = {"19": (1, 66), "20": (67, 108), "21": (109, 156), "22": (157, 210)}
LAND = 30                     # the seed touches her nose
CROSS = (33, 48)              # her eyes cross down at it
RELEASE = 71                  # her fingers let go of her nose
DROP = 86                     # her hand has dropped to her side
TOP = 116                     # the top of the wind-up
CHOO = 126                    # mouth wide, head snapping through
HIT = 129                     # the blast reaches the dandelion
DANDELION_AT = Vector((-0.045, -0.29, -0.085))   # the seed head, from her nose tip (in front, a little low)
STEM = 0.42                   # a long stem: it rises from below the frame
SWAY = (3.5, 22.0, 30.0)      # the stem whips forward on the hit and springs back: degrees, decay, period (frames)


def _both(**kv):
    return HOLD._both(**kv)


HELD = _both(noseSneer=0.3, mouthPress=0.8, mouthRollLower=0.15, cheekPuff=1.3, eyeWide=1.2, browInnerUp=0.9,
             browOuterUp=0.8)
FACE = [  # (take frame, face units); anything not listed is 0 at that key
    (1, HELD), (24, HELD),
    (LAND + 2, _both(noseSneer=0.55, flare=0.4, mouthPress=0.8, mouthRollLower=0.15, cheekPuff=1.2, eyeWide=1.0,
                     browInnerUp=1.0, browOuterUp=0.6)),                              # tickled: a twitch
    (LAND + 5, _both(noseSneer=0.25, mouthPress=0.8, cheekPuff=1.2, eyeWide=0.9, browInnerUp=0.9, browOuterUp=0.5)),
    (CROSS[0], _both(noseSneer=0.3, mouthPress=0.8, cheekPuff=1.15, eyeWide=0.7, eyeLookDown=0.6, eyeLookIn=0.5,
                     browInnerUp=1.0)),                                                # eyes cross down at the seed
    (CROSS[1], _both(noseSneer=0.45, mouthPress=0.75, cheekPuff=1.1, eyeWide=0.5, eyeLookDown=0.6, eyeLookIn=0.5,
                     browInnerUp=1.05)),
    (52, _both(noseSneer=0.9, flare=0.8, nostrils_wide=0.4, mouthPress=0.5, cheekPuff=0.8, eyeSquint=0.6,
               cheekSquint=0.5, eyeBlink=0.4, browInnerUp=0.9, browDown=0.2)),         # here it comes...
    (56, _both(noseSneer=0.5, flare=0.4, mouthPress=0.6, cheekPuff=0.8, eyeSquint=0.4, eyeBlink=0.25,
               browInnerUp=0.9)),
    (62, _both(noseSneer=1.05, flare=1.1, nostrils_wide=0.5, jawOpen=0.18, mouthStretch=0.2, eyeSquint=0.8,
               cheekSquint=0.7, eyeBlink=0.7, browInnerUp=1.0, browDown=0.15)),       # "ahh..."
    (66, _both(noseSneer=1.1, flare=1.2, nostrils_wide=0.55, jawOpen=0.22, mouthStretch=0.25, eyeSquint=0.85,
               cheekSquint=0.75, eyeBlink=0.75, browInnerUp=1.0, browDown=0.15)),
    (RELEASE, _both(noseSneer=1.0, flare=1.2, nostrils_wide=0.6, jawOpen=0.3, mouthStretch=0.3, eyeSquint=0.8,
                    cheekSquint=0.7, eyeBlink=0.7, browInnerUp=1.0)),
    (84, _both(noseSneer=1.1, flare=1.3, nostrils_wide=0.65, jawOpen=0.42, mouthStretch=0.35, mouthUpperUp=0.15,
               eyeSquint=0.9, cheekSquint=0.8, eyeBlink=0.85, browInnerUp=1.05)),     # "ahh..."
    (92, _both(noseSneer=0.9, flare=1.0, nostrils_wide=0.5, jawOpen=0.3, mouthStretch=0.25, eyeSquint=0.8,
               cheekSquint=0.7, eyeBlink=0.75, browInnerUp=1.0)),
    (104, _both(noseSneer=1.2, flare=1.4, nostrils_wide=0.7, jawOpen=0.55, mouthStretch=0.45, mouthUpperUp=0.2,
                eyeSquint=0.95, cheekSquint=0.85, eyeBlink=0.9, browInnerUp=1.1)),    # "AHH..."
    (TOP, _both(noseSneer=1.3, flare=1.5, nostrils_wide=0.75, jawOpen=0.62, mouthStretch=0.5, mouthUpperUp=0.25,
                eyeSquint=1.0, cheekSquint=0.9, eyeBlink=0.95, browInnerUp=1.1)),
    (CHOO - 2, _both(noseSneer=1.2, flare=1.2, jawOpen=0.45, mouthFunnel=0.5, eyeSquint=1.0, cheekSquint=1.0,
                     eyeBlink=1.0, browDown=0.6, browInnerUp=0.6)),
    (CHOO, _both(noseSneer=1.1, flare=1.0, jawOpen=0.75, mouthFunnel=0.35, mouthStretch=0.3, eyeSquint=1.0,
                 cheekSquint=1.0, eyeBlink=1.0, browDown=0.8, browInnerUp=0.4)),        # CHOO!
    (CHOO + 8, _both(noseSneer=0.8, jawOpen=0.6, mouthStretch=0.2, eyeSquint=0.9, cheekSquint=0.8, eyeBlink=1.0,
                     browDown=0.6, browInnerUp=0.4)),
    (150, _both(noseSneer=0.4, jawOpen=0.2, eyeSquint=0.5, cheekSquint=0.4, eyeBlink=0.7, browInnerUp=0.5)),
    (166, _both(noseSneer=0.2, jawOpen=0.05, eyeBlink=0.4, browInnerUp=0.5)),
    (176, _both(eyeBlink=0.1, eyeLookDown=0.25, browInnerUp=0.6, browOuterUp=0.3)),     # eyes open: phew
    (184, _both(noseSneer=0.7, flare=0.6, eyeSquint=0.3, eyeLookDown=0.25, mouthUpperUp=0.1, browInnerUp=0.4)),  # sniff
    (188, _both(noseSneer=0.1, eyeBlink=0.05, eyeLookDown=0.25, browInnerUp=0.4)),
    (198, _both(mouthSmile=1.15, cheekSquint=0.65, eyeSquint=0.4, eyeBlink=0.12, mouthDimple=0.25, eyeLookDown=0.3,
                browInnerUp=0.35, browOuterUp=0.2)),                    # relieved smile, down at the bald dandelion
    (210, _both(mouthSmile=1.35, cheekSquint=0.75, eyeSquint=0.45, eyeBlink=0.15, mouthDimple=0.3, eyeLookDown=0.3,
                browInnerUp=0.3, browOuterUp=0.2)),                     # (big: it must read through the blur)
]
BONES = {  # pose bone: [(take frame, (x, y, z) degrees)]; +x bends forward (chin down)
    "head": [(1, (7.5, 0, 0)), (LAND, (7, 0, 0)), (CROSS[0], (9, 0, 0)), (CROSS[1], (9, 0, 0)), (60, (4, 0, 0)),
             (66, (0, 0, 0.5)), (RELEASE, (-2, 0, 1)), (84, (-12, 0, 2)), (92, (-9, 0, 1.5)), (104, (-20, 0, 2.5)),
             (TOP, (-24, 0, 2)), (CHOO - 4, (-10, 0, 0)), (CHOO, (16, 0, -1)), (CHOO + 6, (30, 0, -2)),
             (CHOO + 12, (32, 0, -1.5)), (150, (26, 0, -1)), (172, (8, 0, 0)), (188, (3, 0, 0)), (210, (2, 0, 0.5))],
    "neck01": [(1, (4, 0, 0)), (60, (3, 0, 0)), (RELEASE, (0, 0, 0)), (84, (-5, 0, 0)), (104, (-8, 0, 0)),
               (TOP, (-10, 0, 0)), (CHOO - 4, (-4, 0, 0)), (CHOO, (8, 0, 0)), (CHOO + 6, (12, 0, 0)), (150, (9, 0, 0)),
               (172, (2, 0, 0)), (210, (0, 0, 0))],
    "spine01": [(1, (5, 0, 0)), (60, (4, 0, 0)), (RELEASE, (1, 0, 0)), (84, (-4, 0, 0)), (104, (-6, 0, 0)),
                (TOP, (-8, 0, 0)), (CHOO - 4, (-3, 0, 0)), (CHOO, (10, 0, 0)), (CHOO + 6, (16, 0, 0)),
                (150, (12, 0, 0)), (174, (3, 0, 0)), (210, (1, 0, 0))],
}
SKIN = [(1, "#CA6553"), (60, "#C86756"), (CHOO, "#C7695A"), (150, "#BF7A62"), (190, "#B98466"), (210, "#B98466")]


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
    for fc in V.fcurves(rig):                                     # the snap through CHOO is fast, the rest eased
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def _key_flush(hero, off):
    sock = HOLD.skin_tint_socket(hero)
    if sock is None:
        return
    for g, hexc in SKIN:
        sock.default_value = (*H(hexc), 1)
        sock.keyframe_insert("default_value", frame=g - off)


def _key_shrug(rig, off):
    """Her right shoulder: up and forward while she pinches, down once her hand drops."""
    pb = rig.pose.bones["clavicle.R"]
    pb.rotation_mode = "XYZ"
    sc = bpy.context.scene
    sc.frame_set(1 - off)
    rest = rig.matrix_world @ pb.matrix
    for g, k in ((1, 1.0), (RELEASE, 1.0), (DROP, 0.0), (210, 0.0)):
        R = Matrix.Rotation(math.radians(HOLD.SHRUG_FWD * k), 3, "Z") @ \
            Matrix.Rotation(math.radians(HOLD.SHRUG_UP * k), 3, "Y")
        pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(rest.translation) @ (R @ rest.to_3x3()).to_4x4())
        pb.keyframe_insert("rotation_euler", frame=g - off)
    V.ease_id(rig, data_path='pose.bones["clavicle.R"]')


def _eyes_cross(hero, nose_fn, off):
    """Her eyes turn in and down to look at the seed on her nose, then back."""
    rig = hero["rig"]
    tgt = V.link(bpy.data.objects.new("Eye_Look_Target", None), V.collection("RIG_HELPERS"))
    sc = bpy.context.scene
    for g in range(CROSS[0] - 3, CROSS[1] + 4):
        sc.frame_set(g - off)
        tgt.location = nose_fn() + Vector((0.0, -0.004, 0.003))
        tgt.keyframe_insert("location", frame=g - off)
    for side in ("L", "R"):
        c = rig.pose.bones[f"eye.{side}"].constraints.new("DAMPED_TRACK")
        c.target, c.track_axis = tgt, "TRACK_Y"
        for g, w in ((1, 0.0), (CROSS[0] - 3, 0.0), (CROSS[0], 0.62), (CROSS[1], 0.62), (CROSS[1] + 4, 0.0)):
            c.influence = w
            c.keyframe_insert("influence", frame=g - off)


def _key_hand(hero, off, frames):
    """Her right hand: pinching her nose (riding on her head) until RELEASE, then the fingers
    open and the hand swings down to hang by her side (riding on her chest)."""
    rig = hero["rig"]
    sc = bpy.context.scene
    A.curl(rig, "R", A.PINCH, frame=1 - off)
    A.curl(rig, "R", A.PINCH, frame=RELEASE - off)
    A.curl(rig, "R", dict(A.PINCH, thumb=(-45, 10, 10), index=(5, 15, 8)), frame=RELEASE + 3 - off)   # let go
    A.curl(rig, "R", A.RELAXED, frame=DROP - off)
    chest = lambda: rig.matrix_world @ rig.pose.bones["spine01"].matrix
    sc.frame_set(210 - off)                                       # shoulder relaxed: her arm hanging (arms_down)
    hang = rig.matrix_world @ rig.pose.bones["wrist.R"].matrix
    chest0 = chest()
    sc.frame_set(1 - off)
    tip, _ = HR.surface_point(hero, hero["nose_tip"])
    loc_c, q_c = A.pinch_pose(rig, tip + Vector((0.0, 0.008, 0.004)), up=HOLD.PINCH_UP)[:2]
    head0 = HOLD._head_matrix(rig)
    contact = Matrix.Translation(loc_c) @ q_c.to_matrix().to_4x4()
    h = A.hand_target(hero)
    hand = h["hand"]
    lo, hi = frames
    q_prev = None
    for g in range(lo + off - 2, hi + off + 3):
        sc.frame_set(g - off)
        on_nose = HOLD._head_matrix(rig) @ head0.inverted() @ contact
        at_side = chest() @ chest0.inverted() @ hang
        if g <= RELEASE:
            M = on_nose
        elif g >= DROP:
            M = at_side
        else:
            u = (g - RELEASE) / (DROP - RELEASE)
            u = 1 - (1 - u) ** 3                                  # quick off the nose, easing down
            loc = on_nose.translation.lerp(at_side.translation, u) + Vector((0.0, -0.06, 0.02)) * math.sin(math.pi * u)
            q = on_nose.to_quaternion().slerp(at_side.to_quaternion(), u)
            M = Matrix.Translation(loc) @ q.to_matrix().to_4x4()
        q = M.to_quaternion()
        if q_prev is not None and q.dot(q_prev) < 0:
            q = -q
        q_prev = q
        A.key_hand(hand, g - off, M.translation, q)

    def pole(f):
        g = f + off
        u = min(max((g - RELEASE) / (DROP - RELEASE), 0.0), 1.0)
        u = u * u * (3 - 2 * u)
        return (HOLD.PINCH_POLE * (1 - u) + HOLD.HANG_POLE * u).normalized()
    A.bake_arm(rig, "R", range(lo - 2, hi + 3), lambda f: hand.matrix_world.copy(), pole, twist_share=0.8)
    return h


# --------------------------------------------------------------------------
# The dandelion in front of her, and its seeds
# --------------------------------------------------------------------------
def dandelion(nose0, lean=None, col_name="SET_DANDELION"):
    """The dandelion standing in front of her face (its head at nose0 + DANDELION_AT), every
    seed loose so the blast can strip it bare. Returns DS.build()'s dict."""
    slots = DS.seed_slots()
    top = nose0 + DANDELION_AT
    dl = DS.build(col_name=col_name, loose=list(range(len(slots))), slots=slots,
                  base=tuple(top - Vector((0.0, 0.0, STEM))), length=STEM)
    bpy.context.view_layer.update()
    dl["head_rest"] = dl["head"].matrix_world.copy()
    dl["root_rest"] = dl["root"].matrix_world.to_quaternion()
    return dl


def sway(g):
    """The stem's bend on take frame g (radians, towards the blast)."""
    t = g - HIT
    if t <= 0:
        return 0.0
    amp, decay, period = SWAY
    return math.radians(amp) * (1 - math.exp(-t / 2.5)) * math.exp(-t / decay) * math.sin(2 * math.pi * t / period)


def head_at(dl, g):
    """The dandelion head's world matrix on take frame g: its rest pose bent about the stem base."""
    base = dl["root"].location
    return Matrix.Translation(base) @ Matrix.Rotation(sway(g), 4, dl["sway_axis"]) @ Matrix.Translation(-base) \
        @ dl["head_rest"]


def key_sway(dl, frames, off):
    root = dl["root"]
    root.rotation_mode = "QUATERNION"
    for f in range(frames[0], frames[1] + 1):
        root.rotation_quaternion = Quaternion(dl["sway_axis"], sway(f + off)) @ dl["root_rest"]
        root.keyframe_insert("rotation_quaternion", frame=f)


LEAVE = -14                   # the nose seed leaves the dandelion (before shot 19 starts: it is already flying)


def nose_seed_index(dl, nose0):
    """The seed on the side of the dandelion facing her: the one that drifts onto her nose."""
    to_her = (nose0 - dl["head"].matrix_world.translation).normalized()
    return DS.facing(dl["slots"], to_her, 1)[0]


def key_nose_seed(hero, dl, i, frames, off, blast_dir):
    """The seed that drifts onto her nose: off the dandelion at LEAVE, up to her nose (lands at
    LAND), riding on it through the wind-up, blown away at CHOO. Keys this shot's frames."""
    sc = bpy.context.scene
    seed = dl["seeds"][i]
    tip = hero["nose_tip"]
    sc.frame_set(LAND - off)
    p_land, n_land = HR.surface_point(hero, tip)
    head = dl["head_rest"].copy()
    start = head @ DS.slot_matrix(dl["slots"][i]).translation
    q_start = head.to_quaternion() @ DS.slot_matrix(dl["slots"][i]).to_quaternion()
    right = Vector((-1.0, 0.0, 0.0))                              # her right: the camera side
    land_axis = (n_land * 0.55 + Vector((0, 0, 1)) * 0.75 + right * 0.3).normalized()
    q_land = DS.frame_z(land_axis, 0.6).to_quaternion()
    end = p_land + land_axis * DS.PAPPUS_UP * 2.0
    ctrl = [start, start.lerp(end, 0.35) + Vector((0.012, 0.0, 0.03)), start.lerp(end, 0.7) + Vector((-0.01, 0.0, 0.03)),
            end]
    import claude_sculpt_kit as K
    pts = K.path_spline([tuple(c) for c in ctrl], 120)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    seed.parent = None
    seed.matrix_parent_inverse = Matrix.Identity(4)
    seed.rotation_mode = "QUATERNION"
    seed.scale = (2.0, 2.0, 2.0)                                  # bigger than life: it must read in a medium shot
    for ch in seed.children:                                      # and fluffier: one seed's bristles are finer
        if ch.type == "CURVES" and "radius" in ch.data.attributes:   # than a pixel at this distance
            r = np.zeros(len(ch.data.attributes["radius"].data), np.float32)
            ch.data.attributes["radius"].data.foreach_get("value", r)
            ch.data.attributes["radius"].data.foreach_set("value", r * 2.5)
    last = None
    for f in range(frames[0], frames[1] + 1):
        g = f + off
        if g <= LEAVE:
            loc, q = start, q_start
        elif g <= LAND:
            u = (g - LEAVE) / (LAND - LEAVE)
            d = (0.35 * u + 0.65 * (1 - (1 - u) ** 2)) * seg[-1]  # drifting, slowing onto her skin
            j = max(1, min(int(np.searchsorted(seg, d)), len(pts) - 1))
            a = (d - seg[j - 1]) / max(seg[j] - seg[j - 1], 1e-9)
            loc = Vector(pts[j - 1]).lerp(Vector(pts[j]), a)
            sway = Matrix.Rotation(0.12 * math.sin(0.6 * g), 3, "X") @ Matrix.Rotation(0.1 * math.sin(0.45 * g + 1), 3, "Y")
            up = (sway @ Matrix.Rotation(0.9 * g / 30, 3, "Z")).to_quaternion()
            w = min(1.0, max(0.0, (u - 0.6) / 0.4))
            q = q_start.slerp(up, min(1.0, u * 4)).slerp(q_land, w * w * (3 - 2 * w))
        elif g < CHOO:
            sc.frame_set(f)
            p, _ = HR.surface_point(hero, tip)
            loc = p + land_axis * DS.PAPPUS_UP * 2.0
            q = q_land @ Matrix.Rotation(0.05 * math.sin(1.3 * g), 3, "X").to_quaternion()
            last = (loc, q)
        else:
            if last is None:
                sc.frame_set(CHOO - 1 - off)
                p, _ = HR.surface_point(hero, tip)
                last = (p + land_axis * DS.PAPPUS_UP * 2.0, q_land)
            t = g - CHOO
            u = max(0.0, t - 18)                                  # and up and away on the breeze, like the rest
            loc = last[0] + blast_dir * 0.011 * 14 * (1 - math.exp(-t / 14)) + Vector((0, 0, 0.0006 * t)) \
                + Vector((0.0008, 0.0, 0.003)) * (u * u / (u + 20))
            q = last[1] @ Quaternion(Vector((1, 0.3, 0)).normalized(), 0.25 * t)
        seed.location, seed.rotation_quaternion = loc, q
        seed.keyframe_insert("location", frame=f)
        seed.keyframe_insert("rotation_quaternion", frame=f)


def seed_flight(dl, i, g, blast_dir, rng_seed=2121):
    """Where seed i is on take frame g (None = still on the head): it bursts off at HIT (the
    side facing the blast first), shoots away with the blast, slows in the air and drifts
    up and away, slowly turning, parachute up. Returns (world location, quaternion) or None."""
    rng = np.random.default_rng(rng_seed + i)
    slot = dl["slots"][i]
    d = Vector(slot["dir"])
    facing = max(0.0, -d.dot(blast_dir))
    t0 = HIT + (1 - facing) * 4 + rng.uniform(0, 2.5)
    if g < t0:
        return None
    t = g - t0
    head = head_at(dl, t0)
    start = head @ (DS.slot_matrix(slot).translation)
    v0 = (blast_dir * rng.uniform(0.006, 0.012) + (head.to_3x3() @ d).normalized() * rng.uniform(0.002, 0.006))
    tau = rng.uniform(10, 18)                                     # slow motion: they coast, then float
    drift = Vector((rng.uniform(-0.0004, 0.0008), rng.uniform(-0.0006, 0.0002), rng.uniform(0.0006, 0.0012)))
    swirl = rng.uniform(0.01, 0.03)
    ph = rng.uniform(0, 2 * math.pi)
    u = max(0.0, t - 18)                                          # once the blast has spent itself, a breeze
    p = start + v0 * tau * (1 - math.exp(-t / tau)) + drift * t + Vector((math.sin(0.09 * t + ph),     # lifts them
                                                                           math.cos(0.07 * t + ph), 0)) * swirl * min(1.0, t / 30) \
        + Vector((0.0008, 0.0, 0.003)) * (u * u / (u + 20))
    tumble = Quaternion((math.cos(0.08 * t + ph), 0.3, 0.2, 0.0)).normalized()
    q0 = head.to_quaternion() @ DS.slot_matrix(slot).to_quaternion()
    up = DS.frame_z(Vector((0.1 * math.sin(0.05 * t + ph), 0.1 * math.cos(0.04 * t), 1.0)), 0.02 * t + ph).to_quaternion()
    w = min(1.0, t / 24.0)
    return p, q0.slerp(up @ tumble, w * w * (3 - 2 * w))


def key_seeds(dl, frames, off, blast_dir, skip=()):
    """Key every seed of the dandelion over this shot's frames (take = frame + off). Call it
    before key_sway: the seeds still on the head ride on it from their rest pose."""
    sc = bpy.context.scene
    for i, seed in dl["seeds"].items():
        if i in skip:
            continue
        flying = [(f, seed_flight(dl, i, f + off, blast_dir)) for f in range(frames[0], frames[1] + 1)]
        if all(x is None for _, x in flying):
            continue
        sc.frame_set(frames[0])
        on_head = dl["head_rest"].inverted() @ seed.matrix_world
        seed.parent = None
        seed.matrix_parent_inverse = Matrix.Identity(4)
        seed.rotation_mode = "QUATERNION"
        for f, x in flying:
            if x is None:
                M = head_at(dl, f + off) @ on_head
                seed.location, seed.rotation_quaternion = M.translation, M.to_quaternion()
            else:
                seed.location, seed.rotation_quaternion = x
            seed.keyframe_insert("location", frame=f)
            seed.keyframe_insert("rotation_quaternion", frame=f)


def blast_dir(nose0):
    """The way the sneeze goes: from her mouth into the dandelion."""
    mouth = nose0 + Vector((0.0, -0.004, -0.035))
    return (nose0 + DANDELION_AT - mouth).normalized()


def stage(shot):
    """Her take for `shot`, the dandelion in front of her with its seeds keyed for this shot
    (the nose seed included). Returns perform()'s dict plus dandelion, blast, nose_seed."""
    p = perform(shot)
    dl = dandelion(p["nose0"])
    b = blast_dir(p["nose0"])
    dl["sway_axis"] = Vector((0.0, 0.0, 1.0)).cross(Vector((b.x, b.y, 0.0))).normalized()
    k = nose_seed_index(dl, p["nose0"])
    key_nose_seed(p["hero"], dl, k, (1, p["n"]), p["off"], b)
    key_seeds(dl, (1, p["n"]), p["off"], b, skip={k})
    key_sway(dl, (1, p["n"]), p["off"])
    bpy.context.scene.frame_set(1)
    p.update({"dandelion": dl, "blast": b, "nose_seed": dl["seeds"][k]})
    return p


def perform(shot):
    """Build her and key the take for one shot. Returns dict(hero, hand, off, n, nose0)."""
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
    sc = bpy.context.scene
    sc.frame_set(1 - off)
    nose0, _ = HR.surface_point(hero, hero["nose_tip"])
    _eyes_cross(hero, lambda: HR.surface_point(hero, hero["nose_tip"])[0], off)
    sc.frame_set(1)
    return {"hero": hero, "hand": h, "off": off, "n": hi - lo + 1, "nose0": nose0}


def nose_at(hero, frame):
    bpy.context.scene.frame_set(frame)
    return HR.surface_point(hero, hero["nose_tip"])


def droplets(col, mouth, direction, start, n_frames, rng, count=110, speed=(0.005, 0.011), spread=0.32):
    """The spray of the sneeze, in slow motion: glassy droplets from her mouth fanning out
    along `direction` from frame `start` on (shot frames), sinking a little as they go."""
    import air_fx as AF
    mat = V.principled("Sneeze_Droplet", H("#EAF6FF"), rough=0.04, spec=0.8, transmission=1.0, ior=1.33)
    d0 = Vector(direction).normalized()
    t1 = d0.orthogonal().normalized()
    t2 = d0.cross(t1)
    for k in range(count):
        t0 = start + rng.uniform(-1.0, 6.0)
        a, r = rng.uniform(0, 2 * math.pi), spread * math.sqrt(rng.uniform())
        d = (d0 + (t1 * math.cos(a) + t2 * math.sin(a)) * r).normalized()
        v = rng.uniform(*speed)
        p0 = Vector(mouth) + (t1 * math.cos(a) + t2 * math.sin(a)) * rng.uniform(0, 0.006)
        w0 = rng.uniform(0.0006, 0.0022)
        track, widths = [], []
        for i in range(n_frames):
            t = i + 1 - t0
            if t <= 0:
                track.append(None)
                widths.append(0.0)
                continue
            track.append(p0 + d * v * t * (1 - 0.006 * t) + Vector((0, 0, -0.00004 * t * t)))
            widths.append(w0 * min(1.0, t / 2))
        AF.comet(f"Sneeze_Droplet_{k:03d}", track, widths, mat, col, stretch=0.35, max_len=0.006)
