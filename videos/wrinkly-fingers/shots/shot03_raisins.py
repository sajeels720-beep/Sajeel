"""SHOT 03 (3.6-5.1 s, 45 frames @30fps) - "wrinkly raisins."
Extreme close-up of his fingertips, pads towards us, the pool and garden blurred behind: the
smooth skin crumples into deep wrinkles in seconds. 100 mm, slow push-in, then a crash zoom
and a short shake on "raisins". Only his arms are built at full detail (wrinkles.dense), so the
furrows are real geometry.

Run in a NEW Blender file:  blender -b -P shot03_raisins.py -a
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

import opening_take as TAKE
import pool_acting as PA
import pool_set as PS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 100
RAISINS = 136                    # take frame of "raisins": the crash zoom


def pads(hero, frame):
    """Middle of the index, middle and ring finger pads, and the way they face (world)."""
    bpy.context.scene.frame_set(frame)
    rig = hero["rig"]
    pts, nrm = Vector(), Vector()
    for k in (2, 3, 4):
        pb = rig.pose.bones[f"finger{k}-3.R"]
        M = rig.matrix_world @ pb.matrix
        z = M.to_3x3().col[2].normalized()                       # out of the pad
        pts += (rig.matrix_world @ pb.head).lerp(rig.matrix_world @ pb.tail, 0.5) + z * 0.006
        nrm += z
    return pts / 3, nrm.normalized()


def build():
    V.start_fresh()
    lo, hi = TAKE.SHOTS["03"]
    n, off = hi - lo + 1, lo - 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    parts = PS.build(duck_at=(0.4, -0.95), duck_drift=(0.04, 0.0), sun_az=30, sun_el=42)
    parts["sun"].data.color = PS.H("#FFE2BC")
    take = TAKE.perform("03", dense=True)
    hero = take["hero"]
    # camera: square onto the pads, following the hand, pushing in; crash zoom on "raisins"
    hit = RAISINS - off
    keys = []
    for f, dist in ((1, 0.22), (hit - 2, 0.16), (hit + 3, 0.085), (n, 0.078)):
        p, z = pads(hero, f)
        up = Vector((0.0, 0.0, 1.0))
        keys.append((f, p + z * dist + up * dist * 0.3, p, LENS))     # a little above: garden and pool, not sky, behind
    r = V.camera_rig("Cam_Shot03", lens=LENS, fstop=9.0)
    V.cam_keys(r, keys)
    V.handheld(r, amount=0.0004, aim_amount=0.0003)
    V.shake(r, hit, hit + 7, strength=0.0012)
    # cheated for the close-up: the sun from behind his right shoulder rakes across the pads,
    # so the furrows cast shadows (from the front it left the pads flat in shade)
    PS.key_sun(parts["sun"], [(1, -125, 32, None)])
    p, z = pads(hero, hit)
    PS.fill(p, z + Vector((0.3, 0.0, 0.6)), dist=0.35, power=6.0, size=0.3)   # soft fill from the camera side
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
