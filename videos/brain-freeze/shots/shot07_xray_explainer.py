"""SHOT 07 (11.0-12.8 s, 54 frames @30fps) - "You see, when something freezing"
Switch to the clean explainer look: the head in profile as see-through blue glass on a soft
sky-blue backdrop, brain above, the roof of the mouth below with the cold ice cream lump
glowing on it. The camera glides in toward the mouth.
"""
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

import claude_sculpt_kit as K
import vfx_kit as V
import xray_head as XH

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.8
N = 54


def studio_lights(target, power=40):
    lights = V.collection("LIGHTS")
    for name, az, el, dist, pw, size, color in (("Key_lgt", 60, 30, 1.2, power, 1.0, (1.0, 0.97, 0.94)),
                                                ("Fill_lgt", -60, 10, 1.4, power * 0.5, 1.2, (0.85, 0.92, 1.0))):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = pw, size, color
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = target + K.look_dir(az, el) * dist
        K._aim(ob, target)


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    V.gradient_world(strength=1.0, light_strength=0.6)
    x = XH.build(nerves=False)
    eyes = x["eyes"]
    studio_lights(eyes)
    r = V.camera_rig("Cam_Shot07", lens=50, fstop=5.6)
    a0, a1 = eyes + Vector((0, 0.03, -0.035)), eyes + Vector((0, 0.035, -0.06))
    V.cam_keys(r, [(1, a0 + K.look_dir(92, 4) * 0.78, a0, 50), (N, a1 + K.look_dir(88, 2) * 0.5, a1, 50)])
    V.handheld(r, amount=0.001, aim_amount=0.0008)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.005)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 4, 16))
    return x


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
