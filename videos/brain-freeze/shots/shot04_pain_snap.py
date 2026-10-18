"""SHOT 04 (5.6-7.0 s, 42 frames @30fps) - "Then a stabbing pain"
Same bench: the blissful face, then a crash zoom into the eyes as they snap wide open,
brows shoot up and the smile drops. Camera shake and a chromatic flash on the hit.
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
from mathutils import Vector

import character as C
import claude_sculpt_kit as K
import shot03_perfect as S03
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.4
N = 42
HIT = 7                                       # the pain hits: eyes snap open


def flash_dispersion(keys):
    """Keyframe the compositor's lens-fringe amount (chromatic flash)."""
    sc = bpy.context.scene
    ng = getattr(sc, "compositing_node_group", None) or sc.node_tree
    ld = next(n for n in ng.nodes if n.bl_idname == "CompositorNodeLensdist")
    sock = ld.inputs["Dispersion"]
    for f, v in keys:
        sock.default_value = v
        sock.keyframe_insert("default_value", frame=f)


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hero, park, ice, cup = S03.hero_on_bench()
    rig, body = hero["rig"], hero["body"]
    bliss = {"eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0, "mouthSmileLeft": 0.8, "mouthSmileRight": 0.8,
             "browInnerUp": 0.35, "cheekSquintLeft": 0.45, "cheekSquintRight": 0.45, "eyeWideLeft": 0.0,
             "eyeWideRight": 0.0, "browOuterUpLeft": 0.0, "browOuterUpRight": 0.0, "jawOpen": 0.0,
             "mouthFrownLeft": 0.0, "mouthFrownRight": 0.0, "mouthStretchLeft": 0.0, "mouthStretchRight": 0.0}
    shock = {"eyeBlinkLeft": 0.0, "eyeBlinkRight": 0.0, "mouthSmileLeft": 0.0, "mouthSmileRight": 0.0,
             "browInnerUp": 1.0, "cheekSquintLeft": 0.0, "cheekSquintRight": 0.0, "eyeWideLeft": 1.0,
             "eyeWideRight": 1.0, "browOuterUpLeft": 0.7, "browOuterUpRight": 0.7, "jawOpen": 0.22,
             "mouthFrownLeft": 0.5, "mouthFrownRight": 0.5, "mouthStretchLeft": 0.4, "mouthStretchRight": 0.4}
    C.face(body, bliss, frame=1)
    C.face(body, bliss, frame=HIT - 1)
    C.face(body, shock, frame=HIT + 2)
    C.face(body, shock, frame=N)
    S03.key_head(rig, [(1, (-9, 0, 4)), (HIT - 1, (-9, 0, 4)), (HIT + 3, (3, 0, -2)), (N, (2, 0, -1))])

    sc = bpy.context.scene

    def eyes_at(f):
        sc.frame_set(f)
        return (S03.bone_world(rig, "eye.L") + S03.bone_world(rig, "eye.R")) / 2
    e0, e1 = eyes_at(1), eyes_at(HIT + 3)
    head = (S03.bone_world(rig, "head") + S03.bone_world(rig, "head", tail=True)) / 2
    sc.frame_set(1)
    S03.sun_rim_lights(head)
    r = V.camera_rig("Cam_Shot04", lens=50, fstop=2.8)
    d0 = K.look_dir(-14, 7)
    V.cam_keys(r, [(1, e0 + Vector((0, 0, -0.06)) + d0 * 1.05, e0 + Vector((0, 0, -0.05)), 50),
                   (HIT - 1, e0 + Vector((0, 0, -0.05)) + d0 * 1.0, e0 + Vector((0, 0, -0.04)), 50),
                   (HIT + 3, e1 + d0 * 0.5, e1, 120),                 # crash zoom
                   (N, e1 + d0 * 0.47, e1, 125)])
    for idd in (r["rig"], r["aim"], r["cam"].data):                   # snap, don't drift, into the zoom
        for fc in V.fcurves(idd):
            for kp in fc.keyframe_points:
                if int(kp.co.x) == HIT - 1:
                    kp.interpolation, kp.easing = "EXPO", "EASE_OUT"
    V.handheld(r, amount=0.0015, aim_amount=0.001)
    V.shake(r, HIT, HIT + 9, strength=0.006, scale=1.2)
    V.compositor(glow=0.35, threshold=1.1, dispersion=0.006)
    flash_dispersion([(HIT - 1, 0.006), (HIT + 1, 0.07), (HIT + 6, 0.006)])
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 4, 8))
    return {"hero": hero}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
