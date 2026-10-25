"""SHOT 21 (33.6-35.2 s, 48 frames @30fps) - (the sneeze: "Ahh... CHOO!")
The giant sneeze in slow motion: at the top of the wind-up her head snaps forward, a spray of
droplets and a blast of air shoot out of her mouth into the dandelion in front of her, and
its seeds burst off in every direction; the camera crash-zooms into the dandelion as it is
hit, with a shake. 35 mm.

Run in a NEW Blender file:  blender -b -P shot21_sneeze.py -a
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
from mathutils import Vector

import air_fx as AF
import claude_sculpt_kit as K
import release as REL
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 35


def air(col, mouth, direction, start, n, rng, count=30):
    """The blast of air: blue streaks shooting from her mouth into the dandelion."""
    mat = AF.material("Sneeze_Air", 1.1)
    d0 = Vector(direction).normalized()
    t1 = d0.orthogonal().normalized()
    t2 = d0.cross(t1)
    for k in range(count):
        t0 = start + rng.uniform(0, 5)
        a, r = rng.uniform(0, 2 * math.pi), 0.25 * math.sqrt(rng.uniform())
        d = (d0 + (t1 * math.cos(a) + t2 * math.sin(a)) * r).normalized()
        v = rng.uniform(0.012, 0.02)
        track, widths = [], []
        for i in range(n):
            t = i + 1 - t0
            if t <= 0 or t > 26:
                track.append(None)
                widths.append(0.0)
                continue
            track.append(Vector(mouth) + d * v * t)
            widths.append(rng.uniform(0.0012, 0.0022) * min(1.0, t / 2) * (1 - max(0, t - 20) / 6))
        AF.comet(f"Sneeze_Air_{k:02d}", track, widths, mat, col, stretch=1.6, max_len=0.04)


def build():
    V.start_fresh()
    lo, hi = REL.SHOTS["21"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    st = REL.stage("21")
    off, hero, dl = st["off"], st["hero"], st["dandelion"]
    choo, hit = REL.CHOO - off, REL.HIT - off
    nose_c, _ = REL.nose_at(hero, choo)
    mouth = nose_c + Vector((0.0, -0.006, -0.036))
    head = dl["head_rest"].translation.copy()
    col = V.collection("FX")
    rng = np.random.default_rng(2121)
    REL.droplets(col, mouth, head - mouth, choo - 1, n, rng)
    air(col, mouth, head - mouth, choo - 1, n, rng)
    if PREVIEW:
        V.fast_preview(samples=24)
    bpy.context.scene.frame_set(1)

    # camera: at her front-right, her face left and the dandelion right; crash zoom into it on the hit
    r = V.camera_rig("Cam_Shot21", lens=LENS, fstop=5.6)
    a0 = mouth.lerp(head, 0.45) + Vector((0.0, 0.0, 0.05))         # her whole face left, the dandelion right
    c0 = a0 + K.look_dir(-33, 2) * 0.75
    a1, c1 = head + Vector((0.0, 0.02, 0.0)), head + K.look_dir(-42, 6) * 0.2
    V.cam_keys(r, [(1, c0, a0, None), (hit - 2, a0 + K.look_dir(-33, 2) * 0.7, a0, None), (hit + 3, c1, a1, None),
                   (n, head + K.look_dir(-40, 7) * 0.19, a1, None)])
    for fc in V.fcurves(r["rig"]) + V.fcurves(r["aim"]):
        for kp in fc.keyframe_points:
            if int(round(kp.co[0])) == hit - 2:
                kp.interpolation, kp.easing = "QUAD", "EASE_IN"
    V.handheld(r, amount=0.0008, aim_amount=0.0006)
    V.shake(r, hit, hit + 10, strength=0.006, scale=1.3)
    focus = V.link(bpy.data.objects.new("Focus_Shot21", None), V.collection("CAMERA"))
    face = mouth.lerp(head, 0.2)                                   # on her face for the wind-up
    for f in range(1, n + 1):                                     # racks onto the dandelion and rides its whip
        u = min(max((f - hit + 2) / 5, 0.0), 1.0)
        focus.location = face.lerp(REL.head_at(dl, f + off).translation, u * u * (3 - 2 * u))
        focus.keyframe_insert("location", frame=f)
    r["cam"].data.dof.focus_object = focus

    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.5)
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
