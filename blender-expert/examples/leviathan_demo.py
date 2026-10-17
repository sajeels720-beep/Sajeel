"""Worked example: a Leviathan-style serpent bust built phase by phase with claude_sculpt_kit.

Run inside Blender (Text Editor > Run Script, or through the Blender connector one
phase per call). Every size is derived from H, the head length, so the same ratios
work at any scale. Tested headless on Blender 4.5.14 LTS and 5.2.2 LTS.
"""
import math
import os
import tempfile

import bpy
import numpy as np

import claude_sculpt_kit as K

H = 1.9                       # head length: snout tip to back of skull
NECK = K.path_spline([(0, 0.35, 0.0), (0, 0.0, 0.8), (0, 0.35, 1.6), (0, 0.1, 2.3), (0, -0.25, 2.8)], 60)


def phase1_blockout():
    """Gesture block-out from exact primitives, mouth cut with a boolean."""
    K.archive_others(keep=("LIGHTS", "CAMERA"))   # hide what's already there (default cube, older runs); never delete
    S = K.collection("SCULPT")
    t = np.linspace(0, 1, len(NECK))
    parts = [
        K.tube("neck", NECK, 0.62 - 0.22 * t, segments=48, col=S),
        K.ellipsoid("hood", (0, 0.28, 2.5), (0.95, 0.2, 0.78), rot=(-12, 0, 0), col=S),
        K.ellipsoid("skull", (0, -0.55, 2.95), (0.42, 0.6, 0.34), col=S),
        K.ellipsoid("snout", (0, -1.2, 2.88), (0.26, 0.62, 0.17), rot=(8, 0, 0), col=S),
        K.ellipsoid("browL", (0.22, -0.78, 3.14), (0.12, 0.32, 0.08), rot=(6, 0, 10), col=S),
        K.ellipsoid("browR", (-0.22, -0.78, 3.14), (0.12, 0.32, 0.08), rot=(6, 0, -10), col=S),
        K.ellipsoid("cheekL", (0.32, -0.45, 2.78), (0.16, 0.28, 0.2), col=S),
        K.ellipsoid("cheekR", (-0.32, -0.45, 2.78), (0.16, 0.28, 0.2), col=S),
        K.ellipsoid("jaw", (0, -0.91, 2.375), (0.28, 0.65, 0.12), rot=(30, 0, 0), col=S),
        K.ellipsoid("throat", (0, -0.45, 2.48), (0.3, 0.35, 0.26), col=S),
    ]
    body = K.join(parts, "Leviathan_BustMain_geo", S)
    K.voxel_remesh(body, H / 63)
    K.smooth(body, iterations=6, factor=0.5)
    mouth = K.ellipsoid("mouth_cut", (0, -1.05, 2.63), (0.2, 0.8, 0.075), rot=(14, 0, 0), col=S)
    K.boolean(body, mouth)
    K.voxel_remesh(body, H / 86)
    K.smooth(body, iterations=3, factor=0.5)
    return body


def phase2_forms(body):
    """Primary/secondary forms: sockets, brow ridge, cheek fold, nostrils, throat rings."""
    eye_pos, eye_n = K.snap(body, [(0.38, -0.85, 3.02)])
    K.dab(body, eye_pos[0], 0.14, -0.22, mode="inflate")
    K.crease(body, K.path_spline([(0.06, -1.7, 2.98), (0.2, -1.2, 3.08), (0.3, -0.8, 3.2), (0.36, -0.4, 3.1)], 48),
             H / 27, -H / 63, pinch=0.25)
    K.crease(body, K.path_spline([(0.27, -0.6, 2.7), (0.36, -0.35, 2.85), (0.42, -0.1, 3.05)], 32), H / 38, H / 95)
    nostril, _ = K.snap(body, [(0.09, -1.78, 2.95)])
    K.dab(body, nostril[0], 0.05, -0.5, mode="inflate")
    throat = K.mask_normal(body, (0, -1, 0), -0.2, 0.4)
    for z in np.linspace(0.35, 2.15, 14):
        K.crease(body, K.path_ring((0, 0.2, z), (0, 0, 1), 0.75, 64), H / 54, H / 158, pinch=0.4,
                 symmetry_x=False, mask=throat)
    K.smooth(body, iterations=1, factor=0.3)
    return eye_pos[0] - eye_n[0] * 0.03, eye_n[0]


def phase3_detail_resolution(body):
    K.save_version("v02_forms")
    K.voxel_remesh(body, H / 420)
    print(K.stats(body), "edge", K.edge_length(body))


def phase4_tertiary(body, eye_c, eye_n):
    """Layered, masked detail from big to small."""
    P = K.co(body)
    z = P[:, 2]
    front = K.mask_normal(body, (0, -1, -0.1), 0.15, 0.6) * np.clip((2.55 - z) / 0.15, 0, 1)
    side = np.clip(1 - front, 0, 1) * np.clip((2.6 - z) / 0.2, 0, 1)
    head = np.clip((z - 2.45) / 0.15, 0, 1) * np.clip((-P[:, 1] - 0.25) / 0.2, 0, 1)
    eye_m = K.mask_sphere(body, eye_c, 0.2)
    back = K.mask_normal(body, (0, 1, 0.2), -0.1, 0.5) * np.clip(1 - head, 0, 1)
    K.scutes(body, NECK, row=H / 17, col=H / 11, height=H / 85, groove=0.1, mask=front, seed=1)
    K.scales(body, H / 27, H / 190, groove=0.1, jitter=0.6, stretch=(1, 1, 1.2), mask=side * (1 - back), seed=2)
    K.scales(body, H / 47, H / 300, groove=0.12, jitter=0.95, mask=head * (1 - eye_m), seed=3)
    K.scales(body, H / 105, H / 600, groove=0.15, jitter=0.95, mask=eye_m * head, seed=4)
    for r in (0.1, 0.125, 0.15):
        K.crease(body, K.path_ring(eye_c, eye_n, r, 48), 0.012, 0.004, pinch=0.4)
    K.skin(body, H / 17, H / 85, octaves=5, ridged=True, mask=back * K.mask_noise(body, 0.4, seed=7), seed=5)
    K.skin(body, H / 5.4, H / 76, octaves=2, mask=back, seed=6)
    K.skin(body, H / 240, H / 2400, octaves=3, seed=8)


def phase5_parts(body, eye_c):
    """Teeth on gum lines, eyes, crystal fan + shards, flesh grown around bases."""
    PARTS = K.collection("PARTS")
    up = K.path_spline([(0.06, -1.74, 2.76), (0.17, -1.45, 2.75), (0.24, -1.1, 2.73), (0.29, -0.75, 2.7), (0.3, -0.55, 2.68)], 40)
    lo = K.path_spline([(0.06, -1.5, 2.2), (0.15, -1.3, 2.28), (0.21, -1.05, 2.42), (0.24, -0.8, 2.55), (0.25, -0.62, 2.62)], 40)
    for pth in (up, lo):
        K.crease(body, pth, 0.03, -0.012, pinch=0.2)
    beads, _ = K.snap(body, K.resample(up, 0.07))
    K.bumps(body, beads + (0, 0, 0.03), 0.028, 0.012)
    K.teeth("Leviathan_TeethUpper_geo", up, body, length=(H / 27, H / 7), direction=(0, -0.25, -1),
            count=16, fang_at=(0.1, 0.5), seed=1, col=PARTS)
    K.teeth("Leviathan_TeethLower_geo", lo, body, length=(H / 32, H / 9.5), direction=(0, -0.35, 1),
            count=13, fang_at=(0.12,), seed=2, col=PARTS)
    K.eye("Leviathan_Eye_L", tuple(eye_c), 0.075, col=PARTS)
    K.eye("Leviathan_Eye_R", tuple(eye_c * (-1, 1, 1)), 0.075, col=PARTS)
    ang = np.radians(np.linspace(-15, 195, 13))
    rim = np.array((0, 0.3, 2.5)) + np.stack([0.8 * np.cos(ang), np.full_like(ang, 0.12), 0.62 * np.sin(ang)], 1)
    fan = np.stack([np.cos(ang), np.full_like(ang, 0.45), np.sin(ang) * 0.9], 1)
    _, bases = K.crystals("Leviathan_CrystalsBig_geo", body, rim, size=(0.24 * H, 0.45 * H), direction=fan,
                          tilt=8, thickness=0.25, seed=3, col=PARTS)
    rng = np.random.default_rng(5)
    shards = np.vstack([rim[rng.integers(0, 13, 40)] + rng.normal(0, 0.1, (40, 3)),
                        np.stack([rng.uniform(-0.3, 0.3, 30), np.full(30, 0.55), rng.uniform(0.6, 2.2, 30)], 1)])
    _, sb = K.crystals("Leviathan_CrystalsSmall_geo", body, shards, size=(0.02 * H, 0.07 * H), tilt=35,
                       seed=4, col=PARTS)
    K.grow_around(body, np.vstack([bases, sb]), 0.13, 0.03)


def phase7_present(body, preview=True):
    clay = K.clay_material(ao_distance=0.1)
    for col in ("SCULPT", "PARTS"):
        for o in K.collection(col).objects:
            if o.type == "MESH" and not o.name.startswith("Leviathan_Eye"):
                K.assign(o, clay)
    K.light_rig(body)
    K.camera(body, az=-42, el=4, lens=85, res=(540, 634) if preview else (1080, 1268))
    K.dark_world()
    K.render_setup(samples=64 if preview else 1024, noise=0.02 if preview else 0.01)
    K.viewport_clay()
    K.frame_view(body, az=-42, el=6)


def run_all(render_path=None):
    body = phase1_blockout()
    eye_c, eye_n = phase2_forms(body)
    phase3_detail_resolution(body)
    phase4_tertiary(body, eye_c, eye_n)
    phase5_parts(body, eye_c)
    phase7_present(body)
    if render_path:
        K.render_still(render_path)
    return body


if __name__ == "__main__":
    run_all(os.path.join(tempfile.gettempdir(), "leviathan_demo.png"))
