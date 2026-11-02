"""SHOT 06 (8.0-9.2 s, 36 frames @30fps) - "You see, water"
Macro glide over the skin of his fingertip: the fingerprint ridges roll away like hills, with
sweat pores along their tops, and beads of water sitting on the pores seep down into them one
after another as the camera glides past. 100 mm, low over the ridges, shallow focus that
travels with the camera (each bead is sharp as it seeps).

Run in a NEW Blender file:  blender -b -P shot06_pores.py -a
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
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import hand_set as HS
import skin_macro as SM
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 36
LENS = 100
CAM = (Vector((0.0, 0.0, 0.245)), Vector((0.03, 0.2, 0.238)))     # glides forward, low over the ridges
FOCUS = 1.0                                                        # metres ahead
SEEPS = [(3, -0.045), (7, 0.05), (11, -0.02), (15, 0.07), (19, -0.065), (23, 0.02)]   # (start, x offset in frame)


def cam_at(f):
    return CAM[0].lerp(CAM[1], (f - 1) / (N - 1))


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    sk = SM.build()
    SM.world()
    look = Vector((0.0, 1.0, -0.225)).normalized()          # the horizon stays above the frame
    r = V.camera_rig("Cam_Shot06", lens=LENS, fstop=8.0)
    V.cam_keys(r, [(1, cam_at(1), cam_at(1) + look * FOCUS, LENS), (N, cam_at(N), cam_at(N) + look * FOCUS, LENS)], "LINEAR")
    V.handheld(r, amount=0.0008, aim_amount=0.0006)
    # each bead sits on the pore that is in focus while it seeps
    pores = np.array(sk["pores"])
    mat = HS.drop_material()
    for i, (start, dx) in enumerate(SEEPS):
        c = cam_at(start + 6)
        target = (c + look * FOCUS * 0.995)
        d = np.hypot(pores[:, 0] - (target.x + dx), pores[:, 1] - target.y)
        k = int(np.argmin(d))
        SM.seep(f"Bead_{i}", tuple(pores[k]), start, radius=0.022 + 0.004 * (i % 3), mat=mat)
        pores[k] = (99, 99, 0)                                     # one bead per pore
    # light: a warm key grazing across the ridges, a glow from behind on the wet crests
    centre = cam_at(N // 2) + look * FOCUS
    lights = V.collection("LIGHTS")
    for name, off, power, size, color in (("Key", (1.1, -0.3, 0.32), 70, 0.35, "#FFE6D2"),
                                          ("Back", (-0.3, 2.2, 0.55), 110, 0.6, "#FFD2BA"),
                                          ("Fill", (-0.6, -0.9, 0.4), 18, 0.8, "#FFE9E0")):
        lt = bpy.data.lights.new(name, "AREA")
        lt.energy, lt.size, lt.color = power, size, V.hex_lin(color)
        lt.shape = "DISK"                                          # round highlights in the beads
        ob = V.link(bpy.data.objects.new(name, lt), lights)
        ob.location = centre + Vector(off)
        K._aim(ob, centre)
    HS.catch_light(centre, (0, 0, 1), cam_at(N // 2), dist=0.8, size=0.08, power=10.0)
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return sk


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
