"""SHOT 14 (23.8-25.4 s, 48 frames @30fps) - "sets off pain sensors."
Close-up of the swollen artery wrapped in nerve fibres: the nerve endings fire, electric
red sparks crackle along the fibres, red ripple rings pulse out from the endings, and the
fibres glow. Camera orbits around the artery.
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
import nerve_set as NS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.6
FIRE = 6


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    w, nt = V._world()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*V.hex_lin("#0B1236"), 1)
    nt.links.new(bg.outputs[0], out.inputs[0])

    parts = NS.build()
    nmat = parts["nerve_mat"]
    glow = nmat.node_tree.nodes["Glow"].outputs[0]
    V.animate_socket(glow, [(1, 0.0), (FIRE, 0.0), (FIRE + 3, 3.0), (48, 2.2)])
    V.noise_on(nmat.node_tree, 'nodes["Glow"].outputs[0].default_value', 1.2, scale=1.4, start=FIRE + 2, end=48)
    NS.sparks(parts, FIRE, 48)
    rings = V.collection("RINGS")
    for i, (c, n) in enumerate(parts["endings"][:6]):
        V.ripple_rings(f"Ring_{i}", c, n, FIRE + 2 + i * 4, count=2, interval=6, life=14, radius=0.16,
                       thickness=0.03, color=V.hex_lin("#FF2A1A"), strength=12.0, col=rings)

    lights = V.collection("LIGHTS")
    target = Vector(NS.axis_point(0.5))
    for name, az, el, dist, power, size, color in (("Key_lgt", -40, 35, 2.4, 70, 1.2, (1.0, 0.92, 0.85)),
                                                   ("Rim_lgt", 160, 15, 2.4, 140, 1.0, (0.55, 0.65, 1.0)),
                                                   ("Fill_lgt", 60, -10, 2.6, 14, 1.5, (0.8, 0.85, 1.0))):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = power, size, color
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = target + K.look_dir(az, el) * dist
        K._aim(ob, target)

    # camera: orbit around the artery
    r = V.camera_rig("Cam_Shot14", lens=40, fstop=4.0)
    keys = []
    for f in (1, 12, 24, 36, 48):
        t = (f - 1) / 47
        az, el, dist = -60 + 50 * t, 6 - 4 * t, 2.3 - 0.35 * t
        keys.append((f, target + K.look_dir(az, el) * dist, target + Vector((0, 0, 0.05 * t)), 40))
    V.cam_keys(r, keys)
    V.handheld(r, amount=0.004, aim_amount=0.003)
    V.shake(r, FIRE, FIRE + 6, strength=0.01)
    V.compositor(glow=0.7, threshold=0.9, dispersion=0.01)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 2, 4))
    return parts


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
