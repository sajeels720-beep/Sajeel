"""SHOT 22 (35.2-37.0 s, 54 frames @30fps) - (no voice: the music button)
Callback to shot 01: the dandelion, now blown bald, sharp in front of us, its stem still
bobbing from the blast; behind it, out of focus, she straightens up, sniffs and smiles down
at it, relieved, as its seeds float up and away. A slow pull-back and tilt up. 100 mm.

Run in a NEW Blender file:  blender -b -P shot22_callback.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import os
import sys

ROOT = os.environ.get("SNEEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Vector

import claude_sculpt_kit as K
import release as REL
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 100


def build():
    V.start_fresh()
    lo, hi = REL.SHOTS["22"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    st = REL.stage("22")
    if PREVIEW:
        V.fast_preview(samples=24)
    dl, off = st["dandelion"], st["off"]
    head = dl["head_rest"].translation.copy()

    # camera: low on the bald head with her face a blur right behind it (shot 01's framing),
    # pulling back and tilting up with the seeds; her face comes clearer as it goes
    r = V.camera_rig("Cam_Shot22", lens=LENS, fstop=11)
    a0, a1 = head + Vector((0.0, 0.0, 0.01)), head + Vector((0.0, 0.0, 0.04))
    c0 = a0 + K.look_dir(-12, -8) * 0.2
    c1 = a1 + K.look_dir(-11, -3) * 0.32
    V.cam_keys(r, [(1, c0, a0, None), (n, c1, a1, None)])
    V.handheld(r, amount=0.0004, aim_amount=0.0003)
    focus = V.link(bpy.data.objects.new("Focus_Shot22", None), V.collection("CAMERA"))
    for f in range(1, n + 1):                                     # on the head as it bobs
        focus.location = REL.head_at(dl, f + off).translation
        focus.keyframe_insert("location", frame=f)
    r["cam"].data.dof.focus_object = focus
    SKY.studio(c0, a0, LENS)
    SKY.lights(a0, c0, SKY.view_dir(c0, a0, LENS), scale=0.35)
    V.compositor(glow=0.25, threshold=1.2, dispersion=0.006)
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
