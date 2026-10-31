"""SHOT 15 (21.4-22.9 s, 45 frames @30fps) - "So those raisin fingers?"
He holds the marble up to the sun between his wrinkly fingertips, admiring it, water dripping
from his hand; then he looks down at us with a proud grin. 85 mm: it starts close on the
fingertips and the marble against the sky and pulls back to his grinning face.

Run in a NEW Blender file:  blender -b -P shot15_to_the_sun.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
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
from mathutils import Vector

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
    # camera: beside the pinch, looking along the gap between thumb and finger so the marble sits
    # between them against the sky; then it pulls back to his face
    bpy.context.scene.frame_set(1)
    T, I = TAKE.tips(hero)
    held = (T + I) / 2
    head = PA.joint(hero, "head")
    f = (held - PA.joint(hero, "wrist.R")).normalized()
    v = (I - T).normalized().cross(f).normalized()
    if v.y > 0:
        v = -v                                                     # in front of him
    v = (v + Vector((0.0, 0.0, -0.75))).normalized()               # from below: the sky behind it
    c0, a0 = held + v * 0.13, held
    a1 = held.lerp(head, 0.55)
    c1 = a1 + K.look_dir(28, -6) * 1.25                            # on his left: the raised arm stays off his face
    r = V.camera_rig("Cam_Shot15", lens=LENS, fstop=5.6)
    V.cam_keys(r, [(1, c0, a0, LENS), (9, c0.lerp(c1, 0.03), a0.lerp(a1, 0.03), LENS), (32, c1.lerp(c0, 0.05), a1, LENS),
                   (n, c1, a1, LENS)])
    V.handheld(r, amount=0.0012, aim_amount=0.001)
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
