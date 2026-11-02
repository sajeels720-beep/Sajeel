"""SHOT 05 (6.3-7.9 s, 48 frames @30fps) - "Big mistake."
Starts exactly on shot 04's last framing, then a crash zoom into her bulging eyes (cheeks
full, nose pinched); a glowing red "!" pops up beside her face with red ripple rings behind
it (his warning icon, the same deep red as the "?" in video 1). Her acting is shared with
shots 03-04 (scenes/hold_in.py).

Run in a NEW Blender file:  blender -b -P shot05_mistake.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import math
import os
import sys

ROOT = os.environ.get("SNEEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
import numpy as np
from mathutils import Matrix, Vector

import claude_sculpt_kit as K
import hold_in as HOLD
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
ZOOM = (1, 6)                                    # crash zoom frames
POP = 5                                          # the "!" appears
ZOOM_LENS = 100


def warning_icon(col, cam, aim, lens, screen=(0.7, 0.38), depth=0.48, height=0.25):
    """His red "!": a chunky, glossy 3D exclamation mark (a rounded tapered bar and a ball)
    facing the camera at a screen position (x right, y up, -1..1), `depth` meters in front of
    the lens, `height` of the frame tall. Returns (empty, location, normal towards camera)."""
    f = (aim - cam).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f)
    t = 18.0 / lens
    at = cam + f * depth + r * (screen[0] * depth * t * 9 / 16) + u * (screen[1] * depth * t)
    h = height * 2 * depth * t                                 # icon height in meters
    root = V.link(bpy.data.objects.new("Warning_Mark", None), col)
    root.location = at
    root.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
    mat = V.principled("Warning_Red", V.hex_lin("#8E040C"), rough=0.3, coat=0.5, emission=V.hex_lin("#FF0A04"),
                       emission_strength=0.35)                  # deep red: brighter reds turn salmon under AgX
    path = [(0, h * (0.5 - 0.62 * k / 8), 0) for k in range(9)]  # bar from the top down, in the icon's plane
    bar = K.tube("Warning_Bar", path, np.linspace(h * 0.11, h * 0.07, 9), segments=24, col=col)
    caps = [K.ellipsoid("Warning_Cap_Top", path[0], (h * 0.11,) * 3, segments=24, col=col),
            K.ellipsoid("Warning_Cap_Low", path[-1], (h * 0.07,) * 3, segments=24, col=col)]
    dot = K.ellipsoid("Warning_Dot", (0, -h * 0.4, 0), (h * 0.1,) * 3, segments=24, col=col)
    for o in [bar, dot] + caps:
        V.assign(o, mat)
        o.parent = root
    return root, at, -f


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["05"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    take = HOLD.perform("05")
    anchor, _ = HOLD.nose_at(take["hero"], 60 - take["off"])

    # start on shot 04's last framing, crash in on her eyes, then a slow push
    r = V.camera_rig("Cam_Shot05", lens=HOLD.CU_LENS, fstop=8)
    a0 = anchor + HOLD.CU_AIM
    c0 = a0 + K.look_dir(*HOLD.CU_LOOK) * HOLD.CU_END_DIST
    right = K.look_dir(-18 + 90, 0)                                  # the camera's right, roughly
    a1 = anchor + Vector((0.0, 0.01, 0.016)) + right * 0.016        # her eyes, with blue to the right of her head
    c1 = a1 + K.look_dir(-18, 3) * 0.60                              # crash: about 1.25x tighter in 5 frames
    a2 = a1 + Vector((0.0, 0.0, 0.001))
    c2 = a2 + K.look_dir(-17, 3) * 0.58
    V.cam_keys(r, [(ZOOM[0], c0, a0, HOLD.CU_LENS), (ZOOM[1], c1, a1, ZOOM_LENS), (n, c2, a2, ZOOM_LENS + 5)])
    focus = V.link(bpy.data.objects.new("Focus_Shot05", None), V.collection("CAMERA"))
    focus.location = anchor + Vector((0.0, 0.016, 0.018))
    r["cam"].data.dof.focus_object = focus
    V.handheld(r, amount=0.0006, aim_amount=0.0005)
    V.shake(r, ZOOM[1] - 1, ZOOM[1] + 8, strength=0.003, scale=1.3)  # the crash zoom lands with a jolt

    # the red "!" with ripple rings
    col = V.collection("FX")
    icon, at, normal = warning_icon(col, c1, a1, ZOOM_LENS)
    V.key(icon, "scale", [(1, (0.001,) * 3), (POP, (0.001,) * 3), (POP + 4, (1.25,) * 3), (POP + 7, (0.94,) * 3),
                          (POP + 9, (1.0,) * 3)])
    base = icon.rotation_euler.copy()
    tilt = [(POP + 4, 9), (POP + 7, -6), (POP + 10, 3), (POP + 13, 0)]
    for f, deg in tilt:                                              # a little wobble as it lands
        icon.rotation_euler = (base.to_matrix() @ Matrix.Rotation(math.radians(deg), 3, "Z")).to_euler()
        icon.keyframe_insert("rotation_euler", frame=f)
    V.ease_id(icon)
    V.ripple_rings("Warning_Ring", at - normal * 0.015, normal, POP + 1, count=3, interval=6, life=18,
                   radius=0.035, thickness=0.05, color=V.hex_lin("#B00C08"), strength=2.5, col=col)

    SKY.studio(c0, a0, HOLD.CU_LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, HOLD.CU_LENS), scale=0.45)
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
