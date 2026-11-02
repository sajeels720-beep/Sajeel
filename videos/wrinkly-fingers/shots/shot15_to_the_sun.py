"""SHOT 15 (21.4-22.9 s, 45 frames @30fps) - "So those raisin fingers?"
He holds the marble up to the sun between his wrinkly fingertips, admiring it, water dripping
from his hand; then he looks down at us with a proud grin. 85 mm: it starts close on the
marble between his fingertips (his wrinkly thumb pad under it), from his left, and pulls back to
his grinning face in one smooth move, widening to 50 mm.

Run in a NEW Blender file:  blender -b -P shot15_to_the_sun.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import math
import os
import sys

ROOT = os.environ.get("WRINKLES_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes"),
          os.path.join(ROOT, "..", "sneeze", "scenes")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Quaternion, Vector

import claude_sculpt_kit as K
import closing_take as TAKE
import hand_set as HS
import opening_take as OPEN
import pool_acting as PA
import pool_set as PS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 85


def build():
    V.start_fresh()
    lo, hi = TAKE.SHOTS["15"]
    n, off = hi - lo + 1, lo - 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts, take = TAKE.pool_scene("15")
    hero = take["hero"]
    m = TAKE.marble(take)
    PS.underwater_materials([bpy.data.materials["Marble_Glass"], bpy.data.materials["Marble_Swirl"]])
    drops = OPEN.drips(hero, range(2, n + 1, 3))
    PS.ripples(parts["water"], [(f, x, y, 0.3) for _, f, (x, y) in drops[:6]])
    # camera: close on the marble between his fingertips, from his left (the marble shows between
    # his index finger and his wrinkly thumb pad), then it pulls back to his grinning face, still
    # from his left, where his raised arm stays off his face. The view turns only 15 degrees on
    # the way (a swing round from his right side, as before, was a whip pan on this 85 mm lens),
    # and the lens widens to 50 mm as it pulls back, so the marble and his face, side by side from
    # here, both fit the tall frame. The pull-back is even in how fast he shrinks (the distance
    # grows geometrically); the aim leaves the marble for the point between the marble and his
    # eyes only as fast as the widening frame allows, so the marble never leaves the shot and the
    # frame is never empty.
    rig = hero["rig"]
    d0, d1 = K.look_dir(70, -6), K.look_dir(55, -8)            # from the subject towards the camera
    near, far, lens1 = 0.14, 1.15, 50.0
    turn = d0.rotation_difference(d1)
    frames = list(range(0, n + 2))
    progress = V.glide([(1, 0.0), (6, 0.02), (22, 0.5), (38, 0.96), (n, 1.0)], frames)[:, 0]
    keys = []
    for f, s in zip(frames, progress):
        bpy.context.scene.frame_set(f)
        T, I = TAKE.tips(hero)
        marble = (T + I) / 2
        eye = sum((rig.matrix_world @ rig.pose.bones[f"eye.{k}"].head for k in "LR"), Vector()) / 2
        u = min(max(s, 0.0), 1.0)
        d = Quaternion().slerp(turn, u) @ d0
        lens = LENS + (lens1 - LENS) * u * u * (3 - 2 * u)
        dist = near * (far / near) ** s
        view = -d
        right = view.cross(Vector((0.0, 0.0, 1.0))).normalized()
        up = right.cross(view)
        h_half = dist * 18.0 / lens                                # the sensor's 36 mm spans the frame height
        w_half = h_half * 9.0 / 16.0
        mid = marble.lerp(eye, 0.56)
        reach = 0.7 * min(1.0, u / 0.3) ** 2                       # how far off-centre the marble may sit
        cap = reach * min(w_half / max(abs((mid - marble).dot(right)), 1e-6),
                          h_half / max(abs((mid - marble).dot(up)), 1e-6))
        t = cap / (1.0 + cap ** 10) ** 0.1                         # (a smooth min(cap, 1))
        aim = marble.lerp(mid, t)
        keys.append((f, aim + d * dist, aim, lens))
    bpy.context.scene.frame_set(1)
    T, I = TAKE.tips(hero)
    held = (T + I) / 2
    head = PA.joint(hero, "head")
    c0 = keys[1][1]
    r = V.camera_rig("Cam_Shot15", lens=LENS, fstop=5.6)
    V.cam_glide(r, keys)
    V.handheld(r, amount=0.0006, aim_amount=0.0005)                # it starts 13 cm from the marble
    TAKE.glint(m["ob"])
    HS.catch_light(held, (0.0, -0.4, 1.0), c0, dist=0.5, size=0.04, power=6.0)     # a sun glint in the marble
    PS.rim(head, from_dir=(0.3, 1.0, 0.6), dist=2.0, power=110.0)
    V.compositor(glow=0.4, threshold=1.2, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
