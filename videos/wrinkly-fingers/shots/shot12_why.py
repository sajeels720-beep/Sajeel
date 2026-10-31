"""SHOT 12 (16.5-17.6 s, 33 frames @30fps) - "But why?"
Back in the pool: his wrinkly hand up in front of his face, he squints at his fingertips,
baffled, head tilted, and his red "?" pops up over his head. 50 mm, a quick push in.
His acting is shared with shots 13, 15 and 16 (scenes/closing_take.py).

Run in a NEW Blender file:  blender -b -P shot12_why.py -a
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
import pool_acting as PA
import pool_set as PS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 50


def build():
    V.start_fresh()
    lo, hi = TAKE.SHOTS["12"]
    n, off = hi - lo + 1, lo - 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts, take = TAKE.pool_scene("12")
    hero = take["hero"]
    # camera: in front of him at face height, a little to his left; a quick push in
    bpy.context.scene.frame_set(1)
    head = PA.joint(hero, "head")
    hand = (PA.joint(hero, "wrist.R") + PA.joint(hero, "finger3-3.R", "tail")) / 2
    focus = head.lerp(hand, 0.4)
    c0 = focus + K.look_dir(24, 4) * 1.05                          # on his left: the hand doesn't hide his face
    c1 = focus + K.look_dir(20, 3) * 0.74
    r = V.camera_rig("Cam_Shot12", lens=LENS, fstop=2.8)
    V.cam_keys(r, [(1, c0, focus, LENS), (8, c0.lerp(c1, 0.9), focus, LENS), (n, c1, focus, LENS)])
    V.handheld(r, amount=0.0012, aim_amount=0.001)
    # his red "?" over his head on "why?"
    top = head + Vector((0.02, 0.0, 0.2))
    fwd = (focus - c1).normalized()
    HS.question_icon(V.collection("FX"), c1, focus, LENS, screen=HS.screen_point(c1, focus, LENS, top),
                     depth=(top - c1).dot(fwd), height=0.15, pop=TAKE.QUESTION - off)
    PS.rim(head, from_dir=(0.4, 1.0, 0.5), dist=2.0, power=90.0)
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
