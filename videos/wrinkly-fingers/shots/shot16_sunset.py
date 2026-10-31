"""SHOT 16 (22.9-25.0 s, 63 frames @30fps) - "Built-in rain tyres." (then the music button)
He tosses the marble back into the pool with a proud grin - it plops into the water - and leans
back against the edge, his arm back in the water as in shot 01, eyes closing in bliss, while
the light turns golden: sunset. 35 mm, pulling back and rising above him. The callback: he
started the day lounging in the midday sun and ends it the same way, staying even longer.

Run in a NEW Blender file:  blender -b -P shot16_sunset.py -a
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

import math

import bpy
from mathutils import Vector

import claude_sculpt_kit as K
import closing_take as TAKE
import opening_take as OPEN
import pool_acting as PA
import pool_set as PS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 35
SUNSET = (6, 63)


def build():
    V.start_fresh()
    lo, hi = TAKE.SHOTS["16"]
    n, off = hi - lo + 1, lo - 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts, take = TAKE.pool_scene("16")
    hero = take["hero"]
    m = TAKE.marble(take)
    PS.underwater_materials([bpy.data.materials["Marble_Glass"], bpy.data.materials["Marble_Swirl"]])
    g = TAKE.glint(m["ob"])
    if m["splash"] is not None:
        V.visible(g, [(1, True), (m["splash"], False)])            # the glint goes out under the water
    # the plop: rings on the water and a little crown of drops
    events = []
    if m["splash"] is not None:
        sx, sy = m["splash_at"].x, m["splash_at"].y
        events.append((m["splash"], sx, sy, 1.4))
        for k in range(7):
            a = 2 * math.pi * k / 7
            d = PS.falling_drop(f"Plop_{k}", m["splash"], (sx, sy, PS.WATER_Z + 0.005),
                                vel=(0.35 * math.cos(a), 0.35 * math.sin(a), 1.1 + 0.15 * (k % 3)),
                                radius=0.0035)
            events.append((d[1], d[2][0], d[2][1], 0.35))
    drops = OPEN.drips(hero, range(2, 20, 3))
    events += [(f, x, y, 0.3) for _, f, (x, y) in drops[:4]]
    PS.ripples(parts["water"], events)
    # sunset: the sun sinks and turns orange, the sky's light warms
    PS.key_sun(parts["sun"], [(SUNSET[0], 30, 42, PS.H("#FFE2BC")), (SUNSET[1], 22, 11, PS.H("#FF8A3D"))], interp="BEZIER")
    PS.golden(SUNSET[0], SUNSET[1])
    # camera: in front of him at face height, pulling back and rising above him
    bpy.context.scene.frame_set(1)
    head0 = PA.joint(hero, "head")
    bpy.context.scene.frame_set(n)
    head1 = PA.joint(hero, "head")
    chest1 = PA.joint(hero, "spine03") if "spine03" in hero["rig"].pose.bones else head1 - Vector((0, 0, 0.25))
    a0 = head0 + Vector((-0.12, -0.15, 0.0))
    a1 = head1.lerp(chest1, 0.5)
    c0 = a0 + K.look_dir(-12, 6) * 1.3
    c1 = a1 + K.look_dir(-6, 40) * 2.7
    r = V.camera_rig("Cam_Shot16", lens=LENS, fstop=4.0)
    V.cam_keys(r, [(1, c0, a0, LENS), (14, c0.lerp(c1, 0.12), a0.lerp(a1, 0.2), LENS), (n, c1, a1, LENS)])
    V.handheld(r, amount=0.0015, aim_amount=0.0012)
    PS.rim(head0, from_dir=(0.3, 1.0, 0.6), dist=2.0, power=110.0)
    V.compositor(glow=0.35, threshold=1.2, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
