"""SHOT 01 (0.0-1.5 s, 45 frames @30fps) - "You take a giant bite"
Extreme close-up: a steel spoon plunges into the vanilla scoop of a 3-scoop cup and lifts
out a huge chunk. Sunny park, backlit, 85 mm, slow push-in.

Run in a NEW Blender file:  blender -b -P shot01_big_bite.py  (or exec() it via the connector)
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import math
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
    sun_az, sun_el = V.sun_azimuth(hdri)
    want = 165                                   # sun behind the cup, slightly right: warm rim light
    V.hdri_world(hdri, strength=1.0, rot_deg=270 - sun_az - want, camera_strength=1.1)

    parts = SET.build()
    ctrl = SET.spoon_rig(parts)
    dig = SET.DIG
    d = Vector((-0.5, 0.15, -1.0)).normalized()            # dig direction: down-left into the scoop
    toward_cam = Vector((0.0, -1.0, 0.35))
    SET.key_spoon(ctrl, [
        (1, dig - d * 0.07, d, toward_cam),
        (9, dig - d * 0.082 + Vector((0.004, 0.0, 0.006)), d, toward_cam),       # anticipation: pull back
        (19, dig + d * 0.003, d, toward_cam),                                       # plunge in
        (23, dig + d * 0.004 + Vector((-0.004, -0.002, 0.003)), Vector((-0.6, 0.1, -0.5)), Vector((0, -0.4, 1))),
        (30, dig + Vector((-0.012, -0.032, 0.045)), Vector((-0.45, -0.5, -0.1)), Vector((0, -0.1, 1))),   # clear lift
        (45, dig + Vector((-0.05, -0.25, 0.08)), Vector((-0.35, -0.7, 0.12)), Vector((0, 0.1, 1))),        # toward lens
    ])
    V.visible(parts["scoops"]["Vanilla"], [(1, True), (22, False)])                 # swap while hidden
    V.visible(parts["carved"], [(1, False), (22, True)])
    V.visible(parts["chunk"], [(1, False), (22, True)])

    # light: warm key front-left, cool fill right (sky-tinted), sun rim from the HDRI
    lights = V.collection("LIGHTS")
    target = Vector((0, 0, 0.11))
    for name, az, el, dist, power, size, color in (("Key_lgt", -40, 35, 0.6, 30, 0.3, (1.0, 0.93, 0.85)),
                                                   ("Fill_lgt", 70, 12, 0.7, 7, 0.4, (0.8, 0.9, 1.0)),
                                                   ("Rim_lgt", 160, 25, 0.5, 45, 0.25, (1.0, 0.9, 0.75))):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = power, size, color
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = target + K.look_dir(az, el) * dist
        K._aim(ob, target)

    # camera: 85 mm push-in with a subtle handheld feel
    r = V.camera_rig("Cam_Shot01", lens=85, fstop=4.5)
    a0, a1 = Vector((0, 0, 0.115)), Vector((-0.004, -0.008, 0.13))
    c0, c1 = a0 + K.look_dir(-15, 8) * 0.68, a1 + K.look_dir(-12, 10) * 0.6
    spoon_end = dig + Vector((-0.05, -0.25, 0.09))
    V.cam_keys(r, [(1, c0, a0, 85), (30, c0.lerp(c1, 0.6), a1, 85), (45, c1, spoon_end, 85)])   # rack focus to spoon
    V.handheld(r, amount=0.0006, aim_amount=0.0005)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return parts


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
