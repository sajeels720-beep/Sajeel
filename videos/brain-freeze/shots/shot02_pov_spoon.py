"""SHOT 02 (1.5-3.0 s, 45 frames @30fps) - "of ice cream,"
Point of view: the overloaded spoon rushes at the lens, blurry lips close in from the
top and bottom edges, and the frame fades to dark (the bite). Cup blurred behind.
"""
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Vector

import claude_sculpt_kit as K
import icecream_set as SET
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.5


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hdri = V.polyhaven("rooitou_park", "hdris", "2k")
    sun_az, _ = V.sun_azimuth(hdri)
    V.hdri_world(hdri, strength=1.0, rot_deg=270 - sun_az - 165, camera_strength=1.1)

    parts = SET.build()
    V.visible(parts["scoops"]["Vanilla"], [(1, False)])                  # the bite is already taken
    V.visible(parts["carved"], [(1, True)])
    ctrl = SET.spoon_rig(parts)

    cam_pos = Vector((-0.06, -0.42, 0.29))
    look = Vector((0.0, 0.0, 0.12))
    fwd = (look - cam_pos).normalized()
    up = Vector((0, 0, 1)) - fwd * fwd.dot(Vector((0, 0, 1)))
    up.normalize()
    right = fwd.cross(up).normalized()
    hold = cam_pos + fwd * 0.21 - up * 0.035 + right * 0.01
    tip_to_cam = -fwd
    SET.key_spoon(ctrl, [
        (1, hold, tip_to_cam, up),
        (8, hold - up * 0.006, tip_to_cam, up),                                   # small dip (anticipation)
        (22, cam_pos + fwd * 0.12 - up * 0.012, tip_to_cam + up * 0.2, up),
        (36, cam_pos + fwd * 0.035 - up * 0.004, tip_to_cam + up * 0.35, up),    # right at the lens
        (45, cam_pos + fwd * 0.02, tip_to_cam + up * 0.35, up),
    ])

    # lips: soft blurry shapes sliding in from the frame edges
    skin = V.principled("Lip_Skin", V.hex_lin("#C76B6B"), rough=0.4)     # no SSS: only seen as a soft blur
    lips = V.collection("LIPS")
    for name, sign in (("Lip_Upper", 1), ("Lip_Lower", -1)):
        lip = K.ellipsoid(name, (0, 0, 0), (0.05, 0.012, 0.016), segments=48, col=lips)
        V.assign(lip, skin)
        start = cam_pos + fwd * 0.014 + up * (0.045 * sign)
        end = cam_pos + fwd * 0.014 + up * (0.007 * sign)
        lip.rotation_euler = fwd.to_track_quat("Y", "Z").to_euler()
        V.key(lip, "location", [(1, tuple(start)), (30, tuple(start)), (41, tuple(end))], "QUAD", "EASE_IN")

    lights = V.collection("LIGHTS")
    target = Vector((0, 0, 0.11))
    for name, az, el, dist, power, size, color in (("Key_lgt", -40, 35, 0.6, 30, 0.3, (1.0, 0.93, 0.85)),
                                                   ("Rim_lgt", 160, 25, 0.5, 45, 0.25, (1.0, 0.9, 0.75))):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = power, size, color
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = target + K.look_dir(az, el) * dist
        K._aim(ob, target)

    # camera: POV, 35 mm, focus follows the chunk; fade to dark as the mouth closes
    r = V.camera_rig("Cam_Shot02", lens=35, fstop=2.8)
    chunk_at = lambda f_pos: f_pos + up * 0.012
    V.cam_keys(r, [(1, cam_pos, chunk_at(hold), 35),
                   (22, cam_pos + fwd * 0.004, chunk_at(cam_pos + fwd * 0.12 - up * 0.012), 35),
                   (36, cam_pos + fwd * 0.006, chunk_at(cam_pos + fwd * 0.035), 35)])
    V.handheld(r, amount=0.0012, aim_amount=0.001, speed=1.4)
    V.shake(r, 34, 42, strength=0.0025)
    vs = bpy.context.scene.view_settings
    V.key(bpy.context.scene, "view_settings.exposure", [(1, 0.0), (37, 0.0), (45, -9.0)], "QUAD", "EASE_IN")
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.008)
    return parts


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
