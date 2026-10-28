"""SHOT 01 (0.0-2.3 s, 69 frames @30fps) - "You stay in the pool too long,"
A sunny backyard pool, as a time-lapse: he leans back against the pool wall, head tipped back to
the sun, eyes closed, blissful (left arm on the stone edge, right arm in the water), while the
sun swings over, palm shadows sweep across him, the water's light patterns race and the rubber
duck drifts past. 28 mm, low just above the water, slow push-in. His acting is shared with
shots 02-03 (scenes/opening_take.py).

Run in a NEW Blender file:  blender -b -P shot01_lounge.py -a
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
import opening_take as TAKE
import pool_acting as PA
import pool_set as PS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 28
SPEED = 6.0                      # the time-lapse: the water and the duck run this much faster


def build():
    V.start_fresh()
    lo, hi = TAKE.SHOTS["01"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts = PS.build(duck_at=(-0.25, -0.15), duck_drift=(0.3, 0.0), duck_speed=SPEED, sun_az=-80, sun_el=58)
    PS.set_time_speed(SPEED)
    take = TAKE.perform("01")
    head = PA.joint(take["hero"], "head")
    # the sun swings across from his right to his left (the light crosses his face), the
    # shadows of palm fronds (out of shot) sweep over him, and clouds race over the sun
    sun = parts["sun"]
    sun.data.angle = 0.0096                                       # the real sun's 0.55 degrees: crisp shadows
    PS.key_sun(sun, [(1, -80, 58, PS.H("#FFF6E8")), (n, 70, 44, PS.H("#FFE2BC"))])
    PS.palm_fronds(head, PS.sun_dir(-5, 56))
    PS.cloud_flicker(sun, [(12, 6, 0.7), (40, 7, 0.75), (59, 4, 0.55)])
    # camera: low over the water, pushing in on him
    aim0 = head + Vector((0.0, -0.02, -0.15))
    aim1 = head + Vector((0.0, -0.02, -0.12))
    c0 = aim0 + K.look_dir(18, -6) * 0.98
    c1 = aim1 + K.look_dir(15, -5) * 0.78
    c0.z, c1.z = max(c0.z, 0.11), max(c1.z, 0.11)
    r = V.camera_rig("Cam_Shot01", lens=LENS, fstop=2.8)
    V.cam_keys(r, [(1, c0, aim0, LENS), (n, c1, aim1, LENS)])
    V.handheld(r, amount=0.002, aim_amount=0.0015)
    PS.rim(aim0)
    V.compositor(glow=0.2, threshold=1.4, dispersion=0.005)
    if PREVIEW:
        V.fast_preview(samples=24)
    return take


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
