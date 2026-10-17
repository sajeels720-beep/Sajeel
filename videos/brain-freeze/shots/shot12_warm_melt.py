"""SHOT 12 (20.4-22.0 s, 48 frames @30fps) - "to warm back up,"
Back inside the mouth (normal view): a warm orange glow spreads over the palate as the
frost melts back toward the ice cream, leaving water droplets hanging from the roof of the
mouth. Slow pull-back.
"""
import math
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "shots"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import mouth_set as MS
import shot08_palate_frost as S08
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.6


def frame_when(mat, control, value, frames):
    """First frame where a falling control drops below value."""
    path = f'nodes["{control}"].outputs[0].default_value'
    fc = next(f for f in V.fcurves(mat.node_tree) if f.data_path == path)
    for f in frames:
        if fc.evaluate(f) <= value:
            return f
    return None


def droplets(mat_frost, count=46, seed=11, col=None):
    """Water drops hanging from the palate where the frost melts; each one appears as the
    melting edge passes it."""
    col = col or V.collection("DROPLETS")
    water = V.principled("Water", (0.9, 0.95, 1.0), rough=0.03, transmission=1.0, ior=1.33, spec=0.6)
    rng = np.random.default_rng(seed)
    c = MS.CONTACT
    made = 0
    tries = 0
    while made < count and tries < 4000:
        tries += 1
        ang = rng.uniform(0, 2 * math.pi)
        d = math.sqrt(rng.uniform(0.012 ** 2, 0.023 ** 2))
        x, y = c.x + d * math.cos(ang), c.y + d * math.sin(ang)
        if MS.arch_r(x, y) > 0.93:
            continue
        f = frame_when(mat_frost, "FrostRadius", d, range(1, 49))
        if f is None:
            continue
        r = rng.uniform(0.0004, 0.001)
        z = float(MS.palate_height(x, y))
        drop = K.ellipsoid(f"Droplet_{made:02d}", (x, y, z - r * 0.55), (r, r, r * 1.15), segments=20, col=col)
        V.assign(drop, water)
        drop.visible_shadow = False                                # no dark shadow patch under each drop
        drop.location = (x, y, z)                                  # origin on the roof: drops grow downward
        P = K.co(drop)
        K.set_co(drop, P - np.array([x, y, z]))
        V.key(drop, "scale", [(1, (0.001,) * 3), (f, (0.001,) * 3), (f + 5, (1, 1, 1))], "QUAD", "EASE_OUT")
        made += 1
    return made


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    V.gradient_world(strength=0.6, light_strength=0.3)
    parts = MS.build()
    muc = parts["mucosa"]
    parts["lump"].scale = (1.012, 1.012, 0.975)
    V.animate_socket(MS.control(muc, "FrostRadius"), [(1, 0.024), (6, 0.022), (44, 0.0095)])
    V.animate_socket(MS.control(muc, "FrontGlow"), [(1, 0.45), (8, 0.0)])
    V.animate_socket(MS.control(muc, "Warm"), [(1, 0.0), (12, 1.0), (48, 1.15)])
    droplets(muc)
    S08.mouth_lights(MS.CONTACT + Vector((0, 0, -0.004)))

    r = V.camera_rig("Cam_Shot12", lens=16, fstop=40)
    r["cam"].data.clip_start = 0.0005
    V.cam_keys(r, [(1, Vector((0.002, -0.0165, -0.0012)), Vector((0.0, -0.003, 0.0135)), 16),
                   (48, Vector((0.0045, -0.0235, -0.0045)), Vector((0.0, -0.002, 0.012)), 16)])
    V.handheld(r, amount=0.00015, aim_amount=0.0002)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(bounces=(6, 2, 3, 6, 8))
    return parts


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
