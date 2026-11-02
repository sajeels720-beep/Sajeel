"""SHOT 08 (12.8-14.8 s, 60 frames @30fps) - "hits the roof of your mouth,"
Inside the mouth, low angle: the tongue pushes the ice cream lump up against the palate;
on contact, frost spreads across the roof of the mouth with icy ripple rings racing ahead.
16 mm, slow push-in, small impact shake.
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
import mouth_set as MS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 2.0
HIT = 9                                          # frame the lump touches the palate


def mouth_lights(target):
    lights = V.collection("LIGHTS")
    for name, loc, power, size, color in (("MouthOpening_lgt", (0.0, -0.065, 0.004), 0.5, 0.05, (1.0, 0.95, 0.88)),
                                          ("CamFill_lgt", (0.007, -0.027, -0.001), 0.02, 0.012, (1.0, 0.9, 0.9))):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = power, size, color
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = loc
        K._aim(ob, target)
    return lights


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    V.gradient_world(strength=0.6, light_strength=0.3)
    parts = MS.build()
    parts["teeth"].hide_render = True                              # only a stray tip showed in a corner
    C = MS.CONTACT
    lump, tongue, muc = parts["lump"], parts["tongue"], parts["mucosa"]

    # the tongue pushes the lump up into the palate, then it squashes and settles
    drop = Vector((0, 0, -0.0035))
    V.key(lump, "location", [(1, tuple(C + drop)), (HIT, tuple(C))], "QUAD", "EASE_IN")
    V.key(lump, "scale", [(HIT - 1, (1, 1, 1)), (HIT + 3, (1.035, 1.035, 0.94)), (HIT + 10, (1.012, 1.012, 0.975))])
    V.key(tongue, "location", [(1, tuple(drop)), (HIT, (0, 0, 0))], "QUAD", "EASE_IN")

    # frost grows from the contact; glowing front and three ripple rings run ahead of it
    # the frost pops out past the lump's silhouette on the hit, then keeps spreading to the end
    V.animate_socket(MS.control(muc, "FrostRadius"), [(HIT - 1, 0.0), (HIT + 2, 0.0085), (60, 0.024)], "LINEAR")
    V.animate_socket(MS.control(muc, "FrontGlow"), [(HIT - 1, 0.0), (HIT + 2, 1.0), (60, 0.45)])
    for i in range(3):
        f0 = HIT + i * 10                                              # born outside the lump, last ring ends f53
        V.animate_socket(MS.control(muc, f"Ring{i}_R"), [(f0, 0.008), (f0 + 24, 0.026)])
        V.animate_socket(MS.control(muc, f"Ring{i}_S"), [(1, 0.0), (f0 - 1, 0.0), (f0 + 1, 1.4 - 0.25 * i),
                                                         (f0 + 24, 0.0)])

    mouth_lights(C + Vector((0, 0, -0.004)))

    # camera: low inside the mouth behind the front teeth, looking up at the contact; slow push
    r = V.camera_rig("Cam_Shot08", lens=18, fstop=40)
    r["cam"].data.clip_start = 0.0005
    aim0, aim1 = Vector((0.0, -0.002, 0.0125)), Vector((0.0, -0.001, 0.0135))
    V.cam_keys(r, [(1, Vector((0.0035, -0.0235, -0.0025)), aim0, 18),
                   (60, Vector((0.0025, -0.0205, -0.0015)), aim1, 18)], "LINEAR")   # keeps moving into shot 09
    V.handheld(r, amount=0.00015, aim_amount=0.0002)
    V.shake(r, HIT, HIT + 7, strength=0.0008)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview()
    return parts


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
