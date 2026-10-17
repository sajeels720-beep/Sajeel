"""SHOT 11 (18.8-20.4 s, 48 frames @30fps) - "then suddenly rush wide open"
Starts on the squeezed, cold-blue vessels; they balloon open past their normal width with
a bright red flash while glowing pulses race along them. Fast push along the artery,
impact shake, motion blur.
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

import mouth_set as MS
import shot09_xray_vessels as S09
import vessels as VS
import vfx_kit as V

FPS, SECONDS = 30, 1.6
OPEN = (4, 13)


def build():
    parts, ves, brain = S09.build_xray_set(SECONDS, xray=1.0)
    mat = ves["mat"]
    for ob in ves["levels"]:                                       # rush open past normal width, then settle
        cu = ob.data
        base = cu.bevel_depth
        for f, k in ((1, 0.45), (OPEN[0], 0.45), (OPEN[1], 1.75), (OPEN[1] + 12, 1.5)):
            cu.bevel_depth = base * k
            cu.keyframe_insert("bevel_depth", frame=f)
        for fc in V.fcurves(cu):
            if fc.data_path == "bevel_depth":
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
                    kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
                fc.keyframe_points[1].interpolation = "EXPO"
                fc.keyframe_points[1].easing = "EASE_OUT"
    V.animate_socket(MS.control(mat, "Cold"), [(1, 1.0), (OPEN[0], 1.0), (OPEN[0] + 6, 0.0)])
    V.animate_socket(MS.control(mat, "Clear"), [(1, 1.0), (OPEN[0], 1.0), (OPEN[0] + 5, 0.0)])
    V.animate_socket(MS.control(mat, "Glow"), [(1, 0.25), (OPEN[0], 0.25), (OPEN[0] + 5, 0.9), (48, 0.45)])
    # two glowing waves rush along every vessel as they open
    V.animate_socket(MS.control(mat, "Pulse"), [(OPEN[0], -0.1), (OPEN[0] + 13, 1.15)], "LINEAR")
    V.animate_socket(MS.control(mat, "PulseS"), [(1, 0.0), (OPEN[0], 0.0), (OPEN[0] + 2, 3.0), (OPEN[0] + 13, 3.0),
                                                 (OPEN[0] + 14, 0.0)])

    brain.hide_render = brain.hide_viewport = True
    r = V.camera_rig("Cam_Shot11", lens=20, fstop=40)
    r["cam"].data.clip_start = 0.0005
    V.cam_keys(r, [(1, Vector((0.0095, -0.0175, -0.002)), Vector((0.0155, -0.002, 0.0135)), 20),
                   (OPEN[0], Vector((0.0098, -0.0168, -0.0016)), Vector((0.0156, -0.0015, 0.0136)), 20),
                   (36, Vector((0.0122, -0.0085, 0.0035)), Vector((0.0168, 0.009, 0.0138)), 20),
                   (48, Vector((0.0128, -0.0065, 0.0042)), Vector((0.017, 0.011, 0.0138)), 20)])
    V.handheld(r, amount=0.0001, aim_amount=0.00012)
    V.shake(r, OPEN[0], OPEN[0] + 8, strength=0.0004)
    V.compositor(glow=0.7, threshold=0.9, dispersion=0.008)
    S09.preview_settings()
    return {"mouth": parts, "vessels": ves, "brain": brain}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
