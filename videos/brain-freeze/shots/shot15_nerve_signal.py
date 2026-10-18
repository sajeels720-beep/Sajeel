"""SHOT 15 (25.9-27.8 s, 57 frames @30fps) - "But the nerve carrying that signal"
A twisted yellow nerve rises through the dark; a glowing red signal races up it with a few
sparks crackling at its head, and the camera tracks beside the signal.
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
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import nerve_set as NS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.9
N = 57
GO = (6, 50)                         # the signal travels from 15% to 92% of the nerve
SPAN = (0.1, 0.6)


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    w, nt = V._world()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*V.hex_lin("#0B1236"), 1)
    nt.links.new(bg.outputs[0], out.inputs[0])

    col = V.collection("SET_NERVE")
    mat = NS.signal_nerve_material()
    bundle, P = NS.nerve_bundle(col, mat)
    pos = mat.node_tree.nodes["Pulse"].outputs[0]
    V.animate_socket(pos, [(1, SPAN[0] - 0.05), (GO[0], SPAN[0]), (GO[1], SPAN[1]), (N, SPAN[1] + 0.03)])
    for fc in V.fcurves(mat.node_tree):                      # constant speed while it races
        if "Pulse" in fc.data_path and "PulseS" not in fc.data_path:
            fc.keyframe_points[1].interpolation = "LINEAR"
    V.animate_socket(mat.node_tree.nodes["PulseS"].outputs[0], [(1, 0.0), (GO[0], 0.0), (GO[0] + 3, 2.4), (N, 2.4)])

    # sparks crackle around the signal's head as it travels
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    rng = np.random.default_rng(3)
    core = V.emission("Spark_Core", V.hex_lin("#FFD2C4"), 30.0)
    red = V.emission("Spark_Red", V.hex_lin("#FF2A16"), 22.0)
    sp_col = V.collection("SPARKS")

    def head_at(f):
        u = SPAN[0] + (SPAN[1] - SPAN[0]) * (f - GO[0]) / (GO[1] - GO[0])
        s = u * L[-1]
        return np.array([np.interp(s, L, P[:, k]) for k in range(3)]), u
    for f in range(GO[0] + 2, GO[1], 2):
        h, _ = head_at(f)
        for j in range(2):
            a = h + rng.normal(0, 0.03, 3)
            b = a + rng.normal(0, 1, 3) * 0.18
            ob = NS.lightning(f"Bolt_{f:02d}_{j}", a, b, rng, sp_col, core if j == 0 else red, jitter=0.03,
                              radius=0.006)
            V.visible(ob, [(1, False), (f, True), (f + 2, False)])

    lights = V.collection("LIGHTS")
    for name, loc, power, size, color in (("Key_lgt", (-2.0, -2.5, 1.5), 260, 2.0, (1.0, 1.0, 1.0)),
                                          ("Rim_lgt", (2.5, 2.5, 0.5), 400, 2.0, (0.55, 0.65, 1.0))):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = power, size, color
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = loc
        K._aim(ob, (0, 0, 0))
        ob.parent = None

    # camera tracks beside the signal: slightly behind and to the side, looking ahead of it
    r = V.camera_rig("Cam_Shot15", lens=30, fstop=2.8)
    keys = []
    for f in list(range(1, N + 1, 4)) + [N]:
        fc = min(max(f, GO[0]), GO[1] + 4)
        h, _ = head_at(fc)
        ahead, _ = head_at(fc + 6)
        keys.append((f, Vector(h) + Vector((0.55, -0.85, -0.45)), Vector(ahead) * 0.45 + Vector(h) * 0.55, 30))
    V.cam_keys(r, keys)
    V.handheld(r, amount=0.006, aim_amount=0.006)
    V.compositor(glow=0.7, threshold=0.9, dispersion=0.01)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 2, 4))
    return {"bundle": bundle}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
