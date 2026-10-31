"""SHOT 14 (21.2-23.0 s, 54 frames @30fps) - "and can burst your eardrums,"
Her eardrum up close, as through a doctor's otoscope, down her ear canal: the trapped air
stretches it like a drum skin, domed out towards us, its vessels swelling red, quivering;
then it tears with a pop (frame 34): a ragged hole bursts open, the torn flaps curl out,
shreds and blue air blast out at the lens, a red ripple ring, a crash zoom into the hole
and a shake. 100 mm.

Run in a NEW Blender file:  blender -b -P shot14_eardrum_pop.py -a
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
import eardrum_set as ES
import sky_set as SKY
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 54
POP = 34
HR = ES.HOLE_R
DRUM = [(1, 0.15, 0.0, 0.0), (8, 0.3, 0.0, 0.0), (14, 0.52, 0.0, 0.0), (18, 0.46, 0.0, 0.0), (24, 0.74, 0.0, 0.0),
        (28, 0.68, 0.0, 0.0), (32, 0.96, 0.0, 0.0), (POP - 1, 1.0, 0.0, 0.0), (POP, 0.9, 0.25, 0.005),
        (POP + 2, 0.7, 0.85, HR * 0.8), (POP + 4, 0.55, 1.0, HR), (POP + 8, 0.46, 1.0, HR * 1.05),
        (N, 0.42, 1.0, HR * 1.08)]          # (frame, bulge, flaps, hole radius): stretch, stretch... POP
LENS = 100


def air_burst(col, rng, count=36, haze=8):
    """Blue air blasting out of the hole at the lens."""
    hx, hz = ES.HOLE_AT
    mat, mat_haze = AF.material("Air_Burst", 1.2), AF.haze_material("Air_Burst_Haze", 0.4)
    for k in range(count + haze):
        soft = k >= count
        t0 = POP + rng.uniform(0, 3 if soft else 12)
        a, rr = rng.uniform(0, 2 * math.pi), HR * 0.6 * math.sqrt(rng.uniform())
        start = Vector((hx + math.cos(a) * rr, 0.03, hz + math.sin(a) * rr))
        d = (Vector((0, -1, 0)) + Vector((math.cos(a), 0, math.sin(a))) * rng.uniform(0.1, 0.5)).normalized()
        v = rng.uniform(0.025, 0.05) * (0.6 if soft else 1.0)
        track, widths = [], []
        for i in range(N):
            t = i + 1 - t0
            if t <= 0 or t > 14:
                track.append(None)
                widths.append(0.0)
                continue
            track.append(start + d * v * t * (1 - 0.025 * t))
            widths.append((0.016 if soft else rng.uniform(0.003, 0.006)) * min(1.0, t / 2) * (1 - max(0, t - 9) / 6))
        AF.comet(f"Air_Burst_{k:02d}", track, widths, mat_haze if soft else mat, col, stretch=2.0, max_len=0.09)


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    col = V.collection("SET_EARDRUM")
    drum = ES.membrane(col)
    mat = ES.membrane_material()
    V.assign(drum, mat)
    ES.key_drum(drum, mat, DRUM)
    V.noise_on(drum.data.shape_keys, 'key_blocks["Bulge"].value', 0.035, scale=1.4, start=20, end=POP - 1)   # quivering
    ES.canal(col)
    _, cave_mat = ES.middle_ear(col)
    V.animate_socket(cave_mat.node_tree.nodes["Air"].outputs[0], [(1, 1.0), (POP, 2.6), (POP + 6, 1.7), (N, 1.5)])
    fx = V.collection("FX")
    rng = np.random.default_rng(1414)
    ES.fragments(fx, POP, rng)
    air_burst(fx, rng)
    hx, hz = ES.HOLE_AT
    V.ripple_rings("Pop_Ring", (hx, -0.035, hz), (0, -1, 0), POP, count=3, interval=4, life=16, radius=0.055,
                   thickness=0.07, color=V.hex_lin("#B00C08"), strength=3.2, col=fx)
    if PREVIEW:
        V.fast_preview(samples=24)

    # camera: down the ear canal, creeping in, then a crash zoom into the hole as it pops
    r = V.camera_rig("Cam_Shot14", lens=LENS, fstop=4)
    a0, c0 = Vector((0.004, 0.0, -0.002)), Vector((0.006, -0.8, 0.004))
    a_pre, c_pre = Vector((0.006, 0.0, -0.004)), Vector((0.008, -0.72, 0.0))
    a1, c1 = Vector((hx * 0.8, 0.0, hz * 0.8)), Vector((hx * 0.9, -0.36, hz * 0.9))
    V.cam_keys(r, [(1, c0, a0, None), (POP - 1, c_pre, a_pre, None), (POP + 4, c1, a1, None),
                   (N, c1 + Vector((0, 0.025, 0)), a1, None)])
    V.handheld(r, amount=0.0015, aim_amount=0.001)
    V.shake(r, POP, POP + 10, strength=0.008, scale=1.3)
    focus = V.link(bpy.data.objects.new("Focus_Shot14", None), V.collection("CAMERA"))
    focus.location = (hx * 0.5, -0.02, hz * 0.5)
    r["cam"].data.dof.focus_object = focus
    # the otoscope's light, beside the lens
    sd = bpy.data.lights.new("Otoscope_Light", "SPOT")
    sd.energy, sd.color, sd.spot_size, sd.spot_blend = 10.0, V.hex_lin("#FFF1E2"), math.radians(45), 0.6
    sd.shadow_soft_size = 0.02
    light = V.link(bpy.data.objects.new("Otoscope_Light", sd), V.collection("LIGHTS"))
    light.parent = r["cam"]
    light.location = (0.03, 0.02, 0.0)

    SKY.tissue(turn=10, light_strength=0.15)
    V.compositor(glow=0.4, threshold=1.0, dispersion=0.006)
    return drum


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
