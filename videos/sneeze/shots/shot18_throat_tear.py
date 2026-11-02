"""SHOT 18 (28.0-30.0 s, 60 frames @30fps) - "tear a hole in your throat."
Back inside her neck at the windpipe from shot 10, still ballooned out: the blister at its
weak spot glows red and swells further, then rips open (frame 24): a ragged hole bursts open,
the torn flaps curl out, blue air blasts out of it, a red ripple ring, a shake. Push in.

Run in a NEW Blender file:  blender -b -P shot18_throat_tear.py -a
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
import sky_set as SKY
import throat_set as TS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 60
RIP = 24
LENS = 50
SPOT = 1                                         # which blister gives way (throat_set.BALLOONS)
PRESSURE = [(1, 1.0, 1.0), (10, 0.96, 1.06), (16, 1.0, 1.1), (22, 1.02, 1.16), (RIP, 1.0, 1.18), (RIP + 3, 0.8, 0.62),
            (RIP + 10, 0.72, 0.5), (N, 0.7, 0.48)]          # (frame, swell, balloon): it gives way and sags
TEAR = [(1, 0.4, 0.0, 0.0), (8, 1.6, 0.0, 0.0), (12, 1.0, 0.0, 0.0), (18, 2.8, 0.0, 0.0), (21, 2.0, 0.0, 0.0),
        (RIP - 1, 4.5, 0.0, 0.0), (RIP, 4.0, 0.25, 0.004), (RIP + 3, 2.2, 0.9, 0.017), (RIP + 7, 1.3, 1.0, 0.021),
        (N, 0.9, 1.0, 0.023)]                                  # (frame, red glow, flaps, tear radius m)


def air_burst(col, at, normal, rng, count=34, haze=8):
    """Blue air blasting out of the tear."""
    n = Vector(normal).normalized()
    t1 = n.orthogonal().normalized()
    t2 = n.cross(t1)
    mat, mat_haze = AF.material("Air_Tear", 1.15), AF.haze_material("Air_Tear_Haze", 0.4)
    for k in range(count + haze):
        soft = k >= count
        t0 = RIP + rng.uniform(0, 4 if soft else 20)
        a = rng.uniform(0, 2 * math.pi)
        spread = rng.uniform(0.15, 0.6)
        d = (n + (t1 * math.cos(a) + t2 * math.sin(a)) * spread).normalized()
        start = Vector(at) - n * 0.02 + (t1 * math.cos(a) + t2 * math.sin(a)) * rng.uniform(0, 0.008)
        v = rng.uniform(0.018, 0.035) * (0.6 if soft else 1.0)
        track, widths = [], []
        for i in range(N):
            t = i + 1 - t0
            if t <= 0 or t > 16:
                track.append(None)
                widths.append(0.0)
                continue
            track.append(start + d * v * t * (1 - 0.02 * t))
            widths.append((0.03 if soft else rng.uniform(0.004, 0.008)) * min(1.0, t / 2) * (1 - max(0, t - 11) / 6))
        AF.comet(f"Air_Tear_{k:02d}", track, widths, mat_haze if soft else mat, col, stretch=2.0, max_len=0.1)


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    col = V.collection("SET_THROAT")
    pipe = TS.windpipe(col)
    mat = TS.wall_material()
    V.assign(pipe, mat)
    s_c, th_c = pipe["balloon_at"][SPOT]
    TS.add_tear(pipe, mat, s_c, th_c)
    pipe.data.shape_keys.key_blocks["Balloon"].slider_max = 1.5
    TS.key_pressure(pipe, mat, PRESSURE)
    TS.key_tear(pipe, mat, TEAR)
    V.noise_on(pipe.data.shape_keys, 'key_blocks["Balloon"].value', 0.025, scale=1.5, start=8, end=RIP - 1)  # straining
    base, normal = TS.surface_point(pipe, s_c, th_c)
    spot = base + normal * TS.R * 0.62 * 1.18                       # the top of the blister, where it rips
    line = TS.centre_line(pipe)
    TS.surroundings(col, Vector(line[np.argmin(np.abs(line[:, 2] - 0.75))]))
    fx = V.collection("FX")
    rng = np.random.default_rng(1818)
    air_burst(fx, spot, normal, rng)
    V.ripple_rings("Tear_Ring", spot + normal * 0.004, normal, RIP, count=3, interval=4, life=16, radius=0.07,
                   thickness=0.05, color=V.hex_lin("#B00C08"), strength=3.2, col=fx)
    if PREVIEW:
        V.fast_preview(samples=24)

    # camera: in front of and below the weak spot, pushing in on it; a jolt as it rips
    r = V.camera_rig("Cam_Shot18", lens=LENS, fstop=3.5)
    view = (normal * 0.75 + Vector((0.0, 0.0, -0.55)) + Vector((-0.12, -0.2, 0.0))).normalized()
    a0, a1 = spot + Vector((0, 0, 0.02)), spot
    V.cam_keys(r, [(1, a0 + view * 0.78, a0, None), (RIP, a1 + view * 0.52, a1, None), (N, a1 + view * 0.47, a1, None)])
    V.handheld(r, amount=0.002, aim_amount=0.0015)
    V.shake(r, RIP, RIP + 9, strength=0.007, scale=1.4)
    focus = V.link(bpy.data.objects.new("Focus_Shot18", None), V.collection("CAMERA"))
    focus.location = spot
    r["cam"].data.dof.focus_object = focus

    SKY.tissue(turn=40)
    SKY.tissue_lights(spot, a0 + view * 0.78, scale=0.8, rim=0.6)
    V.compositor(glow=0.4, threshold=1.0, dispersion=0.006)
    return pipe


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
