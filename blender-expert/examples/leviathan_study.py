"""Leviathan study: a reference-matched rebuild of David P's Leviathan bust design
(proportions measured from his turntable views), built phase by phase with
claude_sculpt_kit. Personal study of his design; credit: David P - Digital Art.

Units: H = head length = 1.0. Front = -Y, up = +Z, symmetric in X.
"""
import math

import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K

# Measured from his side view (H = 270 px; Y = (x - 330) / 270, Z = (800 - y) / 270).
# Neck spine: top (behind the jaw) -> bottom, bending back and slightly to -X (the coil).
SPINE = K.path_spline([(0, 0.32, 2.48), (0, 0.27, 2.1), (0, 0.24, 1.6), (0, 0.2, 1.2), (0, 0.25, 0.85),
                       (-0.04, 0.42, 0.5), (-0.14, 0.7, 0.18), (-0.24, 0.98, -0.12)], 100)

# Upper head (skull + upper jaw): y, z_bottom (lip line), z_top (skull outline), half width
HEAD = [(-0.995, 2.22, 2.37, 0.06), (-0.97, 2.18, 2.41, 0.12), (-0.85, 2.17, 2.45, 0.16),
        (-0.67, 2.16, 2.49, 0.20), (-0.48, 2.15, 2.55, 0.25), (-0.30, 2.12, 2.60, 0.29),
        (-0.11, 2.06, 2.64, 0.32), (0.10, 2.0, 2.64, 0.33), (0.30, 1.98, 2.55, 0.32)]
# Lower jaw hinged open: y, z_bottom, z_top, half width
JAW = [(-0.82, 1.7, 1.84, 0.05), (-0.78, 1.66, 1.88, 0.10), (-0.60, 1.67, 1.91, 0.15),
       (-0.48, 1.71, 1.94, 0.18), (-0.30, 1.74, 1.98, 0.23), (-0.11, 1.78, 2.03, 0.28),
       (0.05, 1.80, 2.06, 0.31), (0.15, 1.80, 2.05, 0.31)]
EYE = (0.27, -0.54, 2.41)


def collar_curve(side=1.0, n=12):
    """Line the crystal collar grows from: crown -> back of the head -> down the
    back-lateral edge of the neck (one side; mirror with side=-1)."""
    c = K.path_spline([(0.12, -0.25, 2.66), (0.22, 0.05, 2.7), (0.33, 0.35, 2.5), (0.4, 0.5, 2.1),
                       (0.42, 0.5, 1.65), (0.43, 0.52, 1.25), (0.44, 0.6, 0.9), (0.42, 0.75, 0.62)], 300)
    pts = K.resample(c, np.linalg.norm(np.diff(c, axis=0), axis=1).sum() / (n - 1))[:n]
    return pts * (side, 1, 1)


def phase1_blockout():
    K.archive_others(keep=("LIGHTS", "CAMERA"))
    S = K.collection("SCULPT")
    t = np.linspace(0, 1, len(SPINE))
    rx = np.interp(t, [0, 0.12, 0.35, 0.6, 0.8, 1.0], [0.34, 0.44, 0.47, 0.49, 0.47, 0.44])
    ry = np.interp(t, [0, 0.12, 0.35, 0.6, 0.8, 1.0], [0.24, 0.27, 0.3, 0.32, 0.33, 0.33])
    parts = [K.tube("neck", SPINE, rx, segments=64, squash=np.stack([np.ones_like(t), ry / rx], 1),
                    side=(1, 0, 0), col=S),
             K.loft("head", HEAD, rings=70, power=2.2, col=S),
             K.loft("jaw", JAW, rings=50, power=2.6, col=S),
             K.ellipsoid("throat", (0, 0.05, 1.86), (0.34, 0.3, 0.22), col=S),
             K.ellipsoid("browL", (0.22, -0.5, 2.5), (0.11, 0.27, 0.065), rot=(-6, 0, 10), col=S),
             K.ellipsoid("browR", (-0.22, -0.5, 2.5), (0.11, 0.27, 0.065), rot=(-6, 0, -10), col=S),
             K.ellipsoid("templeL", (0.27, -0.15, 2.38), (0.08, 0.2, 0.12), col=S),
             K.ellipsoid("templeR", (-0.27, -0.15, 2.38), (0.08, 0.2, 0.12), col=S)]
    body = K.join(parts, "Leviathan_BustMain_geo", S)
    K.voxel_remesh(body, 0.016)
    K.smooth(body, iterations=4, factor=0.5)
    cut = K.ellipsoid("base_cut", (0, 0.4, -1.0), (3, 3, 1.0), col=S)       # flat bust base at Z=0
    K.boolean(body, cut)
    K.voxel_remesh(body, 0.012)
    K.smooth(body, iterations=2, factor=0.4)
    return body


def _rows(rows, y):
    r = np.asarray(sorted(rows), float)
    return [np.interp(y, r[:, 0], r[:, k]) for k in (1, 2, 3)]


def _spine_center(z):
    sp = SPINE[np.argsort(SPINE[:, 2])]
    return np.array([np.interp(z, sp[:, 2], sp[:, 0]), np.interp(z, sp[:, 2], sp[:, 1]), z])


def phase2_forms(body):
    """Secondary forms: eye sockets, brow ridge, rictus fold, nostrils, nape ridges."""
    eye, _ = K.snap(body, [EYE])
    K.dab(body, eye[0], 0.09, -0.4, mode="inflate")
    K.crease(body, K.path_spline([(0.1, -0.82, 2.49), (0.19, -0.64, 2.56), (0.26, -0.46, 2.6), (0.3, -0.28, 2.62)], 40),
             0.045, -0.028, pinch=0.3)
    K.crease(body, K.path_spline([(0.24, -0.4, 2.13), (0.3, -0.18, 2.06), (0.34, 0.05, 1.98)], 30), 0.035, 0.014)
    nos, _ = K.snap(body, [(0.07, -0.92, 2.46)])
    K.dab(body, nos[0], 0.035, -0.5, mode="inflate")
    back = K.mask_normal(body, (0, 1, 0.1), 0.05, 0.5)
    for z in np.linspace(0.7, 2.3, 12):
        c = _spine_center(z)
        K.crease(body, K.path_ring(c, (0, 0, 1), 0.48, 72), 0.05, -0.016, pinch=0.3, symmetry_x=False, mask=back)
    K.smooth(body, iterations=1, factor=0.3)


def phase3_detail_resolution(body):
    K.voxel_remesh(body, 0.0028)
    print("detail mesh", K.stats(body), "edge", round(K.edge_length(body), 4))


def phase4_tertiary(body):
    P = K.co(body)
    z, y = P[:, 2], P[:, 1]
    head = np.clip((z - 1.97) / 0.08, 0, 1) * np.clip((0.25 - y) / 0.15, 0, 1)
    front = K.mask_normal(body, (0, -1, 0), 0.25, 0.6) * (1 - head)
    back = K.mask_normal(body, (0, 1, 0.1), 0.0, 0.45) * (1 - head)
    side = np.clip(1 - front - back, 0, 1) * (1 - head)
    eye_m = K.mask_sphere(body, EYE, 0.15)
    K.scutes(body, SPINE, row=0.095, col=0.105, height=0.018, groove=0.09, brick=0.0, dome=0.8, wobble=0.12,
             mask=front, seed=1)
    K.scales(body, 0.062, 0.009, groove=0.1, jitter=0.7, mask=side, seed=2)
    K.scales(body, 0.034, 0.006, groove=0.12, jitter=0.95, mask=head * (1 - eye_m), seed=3)
    K.scales(body, 0.015, 0.003, groove=0.15, jitter=0.95, mask=eye_m, seed=4)
    top = head * K.mask_normal(body, (0, 0, 1), 0.3, 0.8)
    pts, _ = K.scatter(body, 70, mask=top, seed=5, min_dist=0.045)
    K.bumps(body, pts, np.random.default_rng(5).uniform(0.015, 0.03, len(pts)), 0.012, symmetry_x=False)
    K.skin(body, 0.09, 0.02, octaves=5, ridged=True, mask=back * K.mask_noise(body, 0.3, seed=6), seed=7)
    lumps, _ = K.scatter(body, 160, mask=back, seed=8, min_dist=0.05)
    rng = np.random.default_rng(8)
    K.bumps(body, lumps, rng.uniform(0.025, 0.06, len(lumps)), rng.uniform(0.01, 0.03, len(lumps)), symmetry_x=False)
    K.skin(body, 0.006, 0.0006, octaves=3, seed=9)


def phase5_parts(body):
    PARTS = K.collection("PARTS")
    ys = np.linspace(-0.93, -0.2, 16)
    zb, zt, hw = _rows(HEAD, ys)
    upper = np.stack([0.82 * hw, ys, zb + 0.02], 1)
    K.teeth("Leviathan_TeethUpper_geo", upper, body, length=(0.07, 0.2), radius_ratio=0.1,
            direction=(0, -0.15, -1), count=26, fang_at=(0.06, 0.4), bend=0.15, seed=1, col=PARTS)
    ys2 = np.linspace(-0.7, -0.15, 14)
    jzb, jzt, jhw = _rows(JAW, ys2)
    lower = np.stack([0.82 * jhw, ys2, jzt - 0.01], 1)
    K.teeth("Leviathan_TeethLower_geo", lower, body, length=(0.06, 0.16), radius_ratio=0.1,
            direction=(0, -0.2, 1), count=22, fang_at=(0.1,), bend=0.15, seed=2, col=PARTS)
    tongue = K.tube("Leviathan_Tongue_geo", K.path_spline([(0, -0.05, 1.99), (0, -0.35, 1.95), (0, -0.62, 1.9)], 30),
                    np.linspace(0.13, 0.06, 30), segments=32, squash=(1, 0.35), side=(1, 0, 0), col=PARTS)
    K.voxel_remesh(tongue, 0.008)
    K.crease(tongue, K.path_line((0, -0.05, 2.02), (0, -0.6, 1.93), 30), 0.025, 0.01, symmetry_x=False)
    eye_c = np.array(EYE) + (-0.045, 0, 0)
    K.eye("Leviathan_Eye_L", tuple(eye_c), 0.04, col=PARTS)
    K.eye("Leviathan_Eye_R", tuple(eye_c * (-1, 1, 1)), 0.04, col=PARTS)
    # crystal collar: thick, mostly flat-topped hexagonal columns along both sides,
    # main row + an offset row of smaller columns, with jittered angles and lengths
    rng = np.random.default_rng(3)
    n = 14
    pts = collar_curve(1.0, n)
    k = np.linspace(0, 1, n)
    dirs = np.stack([np.interp(k, [0, 0.25, 1], [0.75, 0.95, 1.0]),
                     np.interp(k, [0, 0.3, 1], [0.15, 0.2, 0.1]),
                     np.interp(k, [0, 0.2, 0.5, 1], [0.9, 0.55, 0.05, -0.3])], 1)
    lengths = np.interp(k, [0, 0.2, 0.45, 1], [0.62, 0.8, 0.55, 0.2]) * rng.uniform(0.85, 1.12, n)
    thick = np.interp(k, [0, 1], [0.21, 0.34]) * rng.uniform(0.9, 1.12, n)
    pts2 = (pts[:-1] + pts[1:]) / 2 + (-0.06, 0.1, 0)              # second row, offset back/inward
    k2 = (k[:-1] + k[1:]) / 2
    dirs2 = (dirs[:-1] + dirs[1:]) / 2 + (0, 0.3, 0.15)
    len2 = np.interp(k2, [0, 1], [0.38, 0.16]) * rng.uniform(0.7, 1.1, n - 1)
    collar, bases = K.crystals("Leviathan_Collar_geo", body, np.vstack([pts, pts2]),
                               lengths=np.concatenate([lengths, len2]), direction=np.vstack([dirs, dirs2]),
                               tilt=12, broken=0.97, thickness=np.concatenate([thick, np.full(n - 1, 0.3)]),
                               embed=0.3, seed=3, col=PARTS)
    crown_pts = [(0.08, -0.1, 2.68), (0.12, 0.08, 2.7), (0.07, 0.24, 2.64), (0.24, 0.22, 2.6), (0.1, -0.3, 2.62),
                 (0.2, -0.08, 2.66)]
    crown_dirs = [(0.35, 0.05, 1), (0.45, 0.25, 1), (0.3, 0.5, 0.85), (0.8, 0.35, 0.6), (0.3, -0.2, 1), (0.75, 0.05, 0.8)]
    crown, cb = K.crystals("Leviathan_Crown_geo", body, crown_pts, lengths=[0.5, 0.62, 0.6, 0.56, 0.3, 0.5],
                           direction=crown_dirs, tilt=8, broken=0.95, thickness=0.22, embed=0.3, seed=4, col=PARTS)
    # cracks on the big columns (needs a dense mesh)
    for obj in (collar, crown):
        for m in obj.modifiers:
            if m.type == "SUBSURF":
                m.levels = m.render_levels = 4
        K.apply_modifiers(obj)
        K.cracks(obj, 0.11, width=0.07, depth=0.006, coverage=0.5, seed=7)
    # shards and rock-flesh around the bases
    allb = np.vstack([bases, bases * (-1, 1, 1), cb, cb * (-1, 1, 1)])
    near = K.mask_near(body, allb, 0.28)
    sp, _ = K.scatter(body, 70, mask=near * K.mask_normal(body, (0, 1, 0.3), -0.2, 0.4), seed=9, min_dist=0.06)
    K.crystals("Leviathan_Shards_geo", body, sp, size=(0.03, 0.11), tilt=40, broken=0.5, thickness=0.3,
               seed=5, col=PARTS, symmetry_x=False)
    K.grow_around(body, allb, 0.16, 0.035)
    lumps, _ = K.scatter(body, 120, mask=near, seed=10, min_dist=0.04)
    rng = np.random.default_rng(10)
    K.bumps(body, lumps, rng.uniform(0.025, 0.05, len(lumps)), rng.uniform(0.012, 0.03, len(lumps)), symmetry_x=False)


def phase7_present(body, preview=True):
    """His presentation: bright grey clay with dark crevices, navy backdrop, strong white
    key from the front-left, faint cyan fill from camera-right, strong rim from behind,
    light above the head; camera from the creature's left so the collar's flat
    column ends face the lens."""
    clay = K.clay_material(color=(0.36, 0.36, 0.35), roughness=0.42, ao_distance=0.06, cavity=0.95, edges=0.22)
    for col in ("SCULPT", "PARTS"):
        for o in K.collection(col).objects:
            if o.type == "MESH" and not o.name.startswith("Leviathan_Eye"):
                K.assign(o, clay)
    K.light_rig(body, key=4.0, fill=0.35, back=7.0, top=1.2, key_az=15, key_el=45, fill_az=140, fill_el=10,
                back_az=215, back_el=30, fill_color=(0.85, 0.96, 1.0))
    K.dark_world(top=(0.03, 0.045, 0.075), bottom=(0.003, 0.004, 0.008))
    cam = K.camera(body, az=58, el=15, lens=45, res=(880, 1080) if preview else (1760, 2160))
    target = Vector((0.0, 0.0, 1.85))
    cam.location = target + K.look_dir(58, 15) * 5.3
    K._aim(cam, target)
    key = bpy.data.objects["Key_lgt"]                      # focus the key on the head; body falls off
    head_c = Vector((0.0, -0.35, 2.3))
    key.location = head_c + K.look_dir(15, 45) * 4.5
    K._aim(key, head_c)
    key.data.spread = math.radians(70)
    key.data.energy *= 0.3
    K.render_setup(samples=96 if preview else 512, noise=0.02 if preview else 0.01)
