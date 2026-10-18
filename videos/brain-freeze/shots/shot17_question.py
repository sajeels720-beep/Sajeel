"""SHOT 17 (29.6-32.0 s, 72 frames @30fps) - "so that's where your brain feels it,"
His red "?" device: the open head with a healthy brain, a big glowing red question mark
pops up above it, an arrow snaps down to the forehead, and the forehead pulses with red
ripple rings while the front of the brain glows.
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
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import claude_sculpt_kit as K
import shot03_perfect as S03
import shot06_brain_freeze as S06
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 2.4
N = 72
POP, ARROW, PULSE = 3, (24, 34), 36
RED = V.hex_lin("#FF2A22")


def surface_hit(ob, origin, direction):
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(ob, dg)
    mw = ob.matrix_world
    inv = mw.inverted()
    loc, nrm, _, _ = tree.ray_cast(inv @ Vector(origin), (inv.to_3x3() @ Vector(direction)).normalized())
    if loc is None:
        return None, None
    return mw @ loc, (mw.to_3x3() @ nrm).normalized()


def question_mark(col, at, size=0.15):
    cu = bpy.data.curves.new("Question_Mark", "FONT")
    cu.body = "?"
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.size, cu.extrude, cu.bevel_depth, cu.offset = size, 0.012, 0.003, size * 0.03
    ob = V.link(bpy.data.objects.new("Question_Mark", cu), col)
    ob.location = at
    ob.rotation_euler = (math.radians(90), 0, 0)
    mat = V.principled("Question_Red", RED, rough=0.25, coat=0.6, emission=RED, emission_strength=1.4)
    V.assign(ob, mat)
    return ob


def arrow(col, a, b, bulge, radius=0.006):
    pts = K.path_spline([a, (a + b) / 2 + bulge, b], 40)
    mat = V.emission("Arrow_Red", (1.0, 0.06, 0.04), 2.0)
    shaft = V.glow_curve("Arrow_Shaft", pts, radius, mat, col=col, grow=ARROW)
    tip_dir = Vector(pts[-1]) - Vector(pts[-4])
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=radius * 3.2, depth=radius * 7, location=tuple(b))
    head = bpy.context.active_object
    head.name = "Arrow_Head"
    V.link(head, col)
    head.rotation_mode = "QUATERNION"
    head.rotation_quaternion = tip_dir.normalized().to_track_quat("Z", "Y")
    V.assign(head, mat)
    V.key(head, "scale", [(1, (0.001,) * 3), (ARROW[1] - 1, (0.001,) * 3), (ARROW[1] + 3, (1, 1, 1))], "BACK",
          "EASE_OUT")
    return shaft, head


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    puzzled = {"browInnerUp": 0.85, "browOuterUpLeft": 0.3, "browOuterUpRight": 0.3, "mouthFrownLeft": 0.35,
               "mouthFrownRight": 0.35, "eyeSquintLeft": 0.2, "eyeSquintRight": 0.2}
    hero, cut, _ = S06.build_frozen_head(crystals=False, face=puzzled)
    body, top, eyes = hero["body"], cut["top"], cut["eyes"]
    col = V.collection("ICONS")

    q = question_mark(col, top + Vector((0.0, -0.01, 0.15)))
    V.key(q, "scale", [(1, (0.001,) * 3), (POP, (0.001,) * 3), (POP + 7, (1.15, 1.15, 1.15)), (POP + 12, (1, 1, 1))])
    V.key(q, "rotation_euler", [(1, (math.radians(90), 0, math.radians(-12))), (N, (math.radians(90), 0, math.radians(14)))])
    V.noise_on(q, "location", 0.004, scale=18.0)

    fh, fn = surface_hit(body, eyes + Vector((0, -0.3, 0.038)), (0, 1, 0))
    fh = fh if fh is not None else eyes + Vector((0, -0.09, 0.038))
    fn = fn if fn is not None else Vector((0, -1, 0.2)).normalized()
    start = q.location + Vector((0.0, -0.02, -0.09))
    arrow(col, np.array(start), np.array(fh + fn * 0.02), np.array((0.06, -0.08, 0.0)))
    rings = V.ripple_rings("Forehead_Ring", fh + fn * 0.003, fn, PULSE, count=3, interval=8, life=16, radius=0.045,
                           thickness=0.06, color=RED, strength=6.0, col=col)
    for r in rings:
        r.visible_diffuse = r.visible_glossy = False
    glow = cut["brain_mat"].node_tree.nodes["Glow"].outputs[0]
    V.animate_socket(glow, [(1, 0.0), (PULSE - 2, 0.0), (PULSE + 4, 1.2), (PULSE + 12, 0.4), (PULSE + 20, 1.1),
                            (PULSE + 28, 0.4), (N, 0.9)])

    S03.sun_rim_lights(top, power_key=55)
    r = V.camera_rig("Cam_Shot17", lens=40, fstop=4.0)
    aim = top + Vector((0, 0, 0.0))
    V.cam_keys(r, [(1, aim + K.look_dir(-10, 14) * 0.85, aim, 40), (N, aim + K.look_dir(-4, 12) * 0.74, aim, 40)])
    V.handheld(r, amount=0.0015, aim_amount=0.001)
    V.compositor(glow=0.6, threshold=0.9, dispersion=0.008)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 6, 8))
    return {"hero": hero}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
