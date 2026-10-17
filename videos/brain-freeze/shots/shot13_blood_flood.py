"""SHOT 13 (22.0-23.8 s, 54 frames @30fps) - "and that flood of blood"
Flying through the inside of a winding blood vessel while a flood of red blood cells
rushes past the camera (some overtaking it, some passing the other way of the frame),
heavy motion blur. Headlight travels with the camera.
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

import vessel_tunnel as T
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.8
N = 54
CAM_S = (1.5, 6.5)                  # camera travels 5 m along the tunnel
SPEEDS = (2.5, 6.0, 9.0)            # metres each cell group travels during the shot


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    w, nt = V._world()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*V.hex_lin("#2A0306"), 1)
    nt.links.new(bg.outputs[0], out.inputs[0])

    col = V.collection("SET_VESSEL")
    path = T.path_curve(col)
    T.build_wall(col)
    groups = T.build_cells(col, path, groups=tuple((0.0, 95, k) for k in range(3)))
    for ob, dist in zip(groups, SPEEDS):
        V.key(ob, "location", [(1, (0.0, 0, 0)), (N, (dist, 0, 0))], "LINEAR")

    # camera + headlight ride the tunnel centre line
    r = V.camera_rig("Cam_Shot13", lens=18, fstop=5.6)
    r["cam"].data.clip_start = 0.01
    lt = bpy.data.lights.new("Headlight_lgt", "POINT")
    lt.energy, lt.color, lt.shadow_soft_size = 12.0, (1.0, 0.85, 0.8), 0.15
    head = V.link(bpy.data.objects.new("Headlight_lgt", lt), V.collection("LIGHTS"))
    head.parent = r["rig"]
    head.location = (0.12, 0.0, 0.18)
    far = bpy.data.lights.new("Far_lgt", "POINT")
    far.energy, far.color, far.shadow_soft_size = 4.0, (1.0, 0.35, 0.28), 0.3
    far_ob = V.link(bpy.data.objects.new("Far_lgt", far), V.collection("LIGHTS"))
    for f in range(1, N + 1, 2):
        t = (f - 1) / (N - 1)
        s = CAM_S[0] + (CAM_S[1] - CAM_S[0]) * t
        p, _ = T.point_at(s)
        a, _ = T.point_at(s + 1.6)
        q, _ = T.point_at(s + 4.5)
        sway = Vector((0.05 * (t - 0.5), 0.0, 0.035))
        for ob, loc in ((r["rig"], p + sway), (r["aim"], a), (far_ob, q)):
            ob.location = loc
            ob.keyframe_insert("location", frame=f)
    for ob in (r["rig"], r["aim"], far_ob):
        V.ease_id(ob, "LINEAR")
    V.handheld(r, amount=0.006, aim_amount=0.01, speed=1.5)
    r["cam"].data.dof.focus_object = None
    r["cam"].data.dof.focus_distance = 0.9
    V.compositor(glow=0.5, threshold=0.9, dispersion=0.01)
    sc = bpy.context.scene
    sc.render.motion_blur_shutter = 0.6
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 2, 4))
    return {"groups": groups, "path": path, "rig": r}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
