"""Dandelion clock (the fluffy seed head) for shots 1, 2, 19, 21 and 22. Built here because
Poly Haven's dandelion (CC0) only has the yellow flowers. Real-world size: about 170 seeds make
a ball ~36 mm across on a hollow green stem ~3 mm thick.

One seed, built along its own +Z (outward): a ribbed brown achene (3.5 mm), a hair-thin beak
(8.5 mm) and the pappus, ~64 fine white bristles that spread like an umbrella from the tip of
the beak. Bristles and beaks are hair curves (fine strands, cheap in Cycles and EEVEE); the
achenes are one mesh. Loose seeds are separate objects under an empty placed at the pappus,
so they can break off, drift in the breeze and land on her nose.
"""
import math
import zlib

import bpy
import numpy as np
from mathutils import Matrix, Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
ACHENE = 0.0035                 # seed body
BEAK = 0.0085                   # stalk up to the parachute
BRISTLE = 0.0062                # pappus bristle length
BRISTLES = 64                   # bristles per seed
RECEPTACLE = 0.003              # radius of the head the seeds sit on
SEEDS = 170
BRISTLE_RADIUS = 0.000018       # a little thicker than real (~10 um) so the fluff reads at phone size
BEAK_RADIUS = 0.00005
PAPPUS_UP = ACHENE + BEAK       # from a seed's base to its parachute


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
def _translucent_mix(mat, amount):
    """Let thin parts glow when the rim light is behind them."""
    nt = mat.node_tree
    b = V.bsdf(mat)
    out = nt.nodes["Material Output"]
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = b.inputs["Base Color"].default_value
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = amount
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def materials():
    m = {}
    m["pappus"] = _translucent_mix(V.principled("Dandelion_Pappus", H("#EDEFEE"), rough=0.45, spec=0.4), 0.35)
    m["beak"] = _translucent_mix(V.principled("Dandelion_Beak", H("#D9D2BE"), rough=0.5), 0.25)
    ach = V.principled("Dandelion_Achene", H("#8A6040"), rough=0.55)
    V.color_variation(ach, H("#4A2C17"), scale=900.0, amount=0.6)
    V.bump(ach, scale=1400.0, strength=0.3, distance=0.00005)
    m["achene"] = ach
    stem = V.principled("Dandelion_Stem", H("#8FA845"), rough=0.45, sss=0.15, sss_radius=(0.4, 1.0, 0.3),
                        sss_scale=0.002, coat=0.2)
    _streaks(stem, H("#6E8A2E"), H("#B4BF6A"))
    V.bump(stem, scale=700.0, strength=0.12, distance=0.00004)
    m["stem"] = stem
    bract = V.principled("Dandelion_Bract", H("#6F8C35"), rough=0.5, sss=0.1, sss_radius=(0.4, 1.0, 0.3),
                         sss_scale=0.002)
    V.color_variation(bract, H("#7A5A35"), scale=300.0, amount=0.45)
    m["bract"] = bract
    rec = V.principled("Dandelion_Receptacle", H("#D6C7A2"), rough=0.6)
    V.color_variation(rec, H("#A88D60"), scale=2500.0, amount=0.5)
    V.bump(rec, scale=2500.0, strength=0.4, distance=0.00008)
    m["receptacle"] = rec
    return m


def _streaks(mat, dark, light):
    """Fine lengthwise streaks on the stem (noise stretched along Z)."""
    nt = mat.node_tree
    b = V.bsdf(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2600.0, 2600.0, 60.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].color = (*light, 1)
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = tuple(b.inputs["Base Color"].default_value)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])


# --------------------------------------------------------------------------
# One seed, in its own frame: base at the origin, +Z outward
# --------------------------------------------------------------------------
def _bristles(rng, n=BRISTLES):
    """(n, 4, 3) polylines: an umbrella of bristles from the beak tip, tips curling up."""
    phi = (np.arange(n) + rng.uniform(-0.4, 0.4, n)) * 2 * np.pi / n
    theta = np.radians(rng.uniform(56, 86, n))          # from the seed's axis
    lift = np.radians(rng.uniform(4, 16, n))             # cupped: tips bend back up
    length = BRISTLE * rng.uniform(0.82, 1.08, n)
    pts = np.zeros((n, 4, 3))
    for k in range(1, 4):
        th = theta - lift * (k / 3.0) ** 1.5
        step = np.stack([np.sin(th) * np.cos(phi), np.sin(th) * np.sin(phi), np.cos(th)], 1)
        pts[:, k] = pts[:, k - 1] + step * (length / 3.0)[:, None]
    pts[:, :, 2] += PAPPUS_UP
    return pts


def _beak(rng):
    z = np.linspace(ACHENE * 0.9, PAPPUS_UP, 4)
    wob = rng.normal(0, 0.00012, (4, 2))
    wob[0] = wob[-1] = 0
    return np.column_stack([wob, z])


def _achene_template(sides=10, rings=9):
    """Spindle with lengthwise ribs, tapering into the beak at the top."""
    z = np.linspace(0, ACHENE, rings)
    t = z / ACHENE
    r = 0.00045 * np.clip(np.sin(np.pi * (0.12 + 0.82 * t)), 0.05, 1) ** 0.7
    r[-1] = BEAK_RADIUS * 1.2
    a = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    rib = 1 + 0.14 * np.cos(sides * a / 2) ** 2
    V3 = np.array([[ri * rib[j] * math.cos(a[j]), ri * rib[j] * math.sin(a[j]), zi]
                   for zi, ri in zip(z, r) for j in range(sides)])
    V3 = np.vstack([V3, [[0, 0, -0.00005]]])                     # bottom cap point
    F = [(i * sides + j, i * sides + (j + 1) % sides, (i + 1) * sides + (j + 1) % sides, (i + 1) * sides + j)
         for i in range(rings - 1) for j in range(sides)]
    bottom = len(V3) - 1
    F += [(bottom, (j + 1) % sides, j) for j in range(sides)]
    return V3, F


def _curves_object(name, polylines, radius, mat, col, taper=0.5):
    """One hair-curves object from (n, k, 3) polylines; radius tapers along each strand."""
    P = np.asarray(polylines, np.float32)
    n, k, _ = P.shape
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([k] * n)
    cv.attributes["position"].data.foreach_set("vector", P.reshape(-1))
    if "radius" not in cv.attributes:
        cv.attributes.new("radius", "FLOAT", "POINT")
    rad = np.tile(np.linspace(radius, radius * taper, k), n).astype(np.float32)
    cv.attributes["radius"].data.foreach_set("value", rad)
    cv.materials.append(mat)
    # EEVEE's default draws every strand as a 1-pixel line: the fluff came out thick and grey.
    # Strips use the real (sub-pixel) width, like Cycles.
    bpy.context.scene.render.hair_type = "STRIP"
    return V.link(bpy.data.objects.new(name, cv), col)


def _mesh_object(name, verts, faces, mat, col):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = V.link(bpy.data.objects.new(name, me), col)
    K.shade_smooth(ob)
    V.assign(ob, mat)
    return ob


def _transform(P, R, t):
    return np.asarray(P) @ np.asarray(R).T + np.asarray(t)


# --------------------------------------------------------------------------
# The whole dandelion
# --------------------------------------------------------------------------
def fibonacci_dirs(n):
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    r = np.sqrt(1 - z * z)
    a = np.pi * (1 + 5 ** 0.5) * i
    return np.column_stack([r * np.cos(a), r * np.sin(a), z])


def seed_slots(count=SEEDS, rng_seed=3):
    """Where each seed sits on the head (head frame: centre at the origin, stem along -Z):
    list of dict(base, dir, twist). No seeds in the cone where the stem joins."""
    rng = np.random.default_rng(rng_seed)
    dirs = fibonacci_dirs(int(count / 0.89))
    dirs = dirs[dirs[:, 2] > -0.78][:count]
    out = []
    for d in dirs:
        d = Vector(d) + Vector(rng.normal(0, 0.05, 3))                 # a little untidy, like a real one
        d.normalize()
        out.append({"base": d * RECEPTACLE, "dir": d, "twist": float(rng.uniform(0, 2 * np.pi)),
                    "seed": int(rng.integers(1 << 30))})
    return out


def frame_z(direction, twist=0.0):
    """Proper rotation (no mirroring) taking +Z to direction, turned by twist about it."""
    z = Vector(direction).normalized()
    hint = Vector((0, 0, 1)) if abs(z.z) < 0.9 else Vector((0, 1, 0))
    x = hint.cross(z).normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed() @ Matrix.Rotation(twist, 3, "Z")


def slot_matrix(slot):
    """Head-frame matrix of a seed's pappus point (the loose-seed empty sits there)."""
    R = frame_z(slot["dir"], slot["twist"])
    return Matrix.Translation(slot["base"] + slot["dir"] * PAPPUS_UP) @ R.to_4x4()


def _seed_parts(slot):
    rng = np.random.default_rng(slot["seed"])
    return _bristles(rng), _beak(rng)


def head(col, mats, slots, skip=(), name="Dandelion"):
    """Seeds on the head (all slots except `skip`), in the head frame. Returns the objects."""
    tmpl_v, tmpl_f = _achene_template()
    bristles, beaks, verts, faces = [], [], [], []
    for i, s in enumerate(slots):
        if i in skip:
            continue
        M = slot_matrix(s) @ Matrix.Translation((0, 0, -PAPPUS_UP))
        R, t = np.array(M.to_3x3()), np.array(M.translation)
        b, k = _seed_parts(s)
        bristles.append(_transform(b.reshape(-1, 3), R, t).reshape(b.shape))
        beaks.append(_transform(k, R, t))
        off = len(verts) * len(tmpl_v)
        verts.append(_transform(tmpl_v, R, t))
        faces.extend([tuple(x + off for x in f) for f in tmpl_f])
    if not verts:                                                 # every seed loose: nothing left on the head
        return []
    objs = [_curves_object(f"{name}_Pappus", np.concatenate(bristles), BRISTLE_RADIUS, mats["pappus"], col),
            _curves_object(f"{name}_Beaks", np.array(beaks), BEAK_RADIUS, mats["beak"], col, taper=0.6),
            _mesh_object(f"{name}_Achenes", np.concatenate(verts), faces, mats["achene"], col)]
    return objs


def loose_seed(col, mats, slot, name):
    """A seed that can fly: an empty at its parachute (+Z = from achene to pappus) with the
    bristles, beak and achene as children."""
    root = V.link(bpy.data.objects.new(name, None), col)
    root.empty_display_size = 0.004
    tmpl_v, tmpl_f = _achene_template()
    b, k = _seed_parts(slot)
    down = np.array([0, 0, -PAPPUS_UP])
    parts = [_curves_object(f"{name}_Pappus", b + down, BRISTLE_RADIUS, mats["pappus"], col),
             _curves_object(f"{name}_Beak", (k + down)[None], BEAK_RADIUS, mats["beak"], col, taper=0.6),
             _mesh_object(f"{name}_Achene", tmpl_v + down, tmpl_f, mats["achene"], col)]
    for p in parts:
        p.parent = root
    root.rotation_mode = "QUATERNION"
    return root


def stem_and_base(col, mats, length=0.13, bend=0.012, name="Dandelion"):
    """Hollow green stem rising to the head (head centre at the top, z=length), the reflexed
    bracts curling down under the head and the pale receptacle. Stem frame: base at origin."""
    top = Vector((0, 0, length))
    path = K.path_spline([(0, 0, 0), (bend * 0.6, 0.002, length * 0.45), (bend, 0.001, length * 0.8),
                          (0, 0, length - RECEPTACLE * 0.8)], 40)
    radii = np.linspace(0.0017, 0.0013, len(path))
    stem = K.tube(f"{name}_Stem", path, radii, segments=16, col=col)
    V.assign(stem, mats["stem"])
    rec = K.ellipsoid(f"{name}_Receptacle", top, (RECEPTACLE * 0.95,) * 2 + (RECEPTACLE * 0.8,), segments=24, col=col)
    V.assign(rec, mats["receptacle"])
    bracts = []
    rng = np.random.default_rng(5)
    for i in range(14):                                   # outer bracts, bent back down the stem
        a = 2 * math.pi * i / 14 + rng.uniform(-0.1, 0.1)
        out = Vector((math.cos(a), math.sin(a), 0))
        L = rng.uniform(0.008, 0.012)
        root = top + Vector((0, 0, -RECEPTACLE * 0.7)) + out * 0.0016
        ctrl = [root, root + out * 0.0022 + Vector((0, 0, -0.0012)),
                root + out * 0.0028 + Vector((0, 0, -L * 0.55)), root + out * 0.0018 + Vector((0, 0, -L))]
        p = K.path_spline([tuple(c) for c in ctrl], 14)
        w = np.linspace(0.0007, 0.00018, len(p))
        bracts.append(K.tube(f"{name}_Bract_{i}", p, w, segments=8, squash=(1.0, 0.22), side=tuple(out.cross(Vector((0, 0, 1)))),
                             col=col))
    for b in bracts:
        V.assign(b, mats["bract"])
    return stem, rec, bracts, top


def build(col_name="SET_DANDELION", loose=(), slots=None, base=(0, 0, 0), length=0.13, name="Dandelion"):
    """The dandelion standing at `base`. loose: indices of seeds that are separate objects
    (they start in their slots; animate them with drift()). Returns a dict with "root" (the
    empty to sway or carry it), "head" (empty at the head centre), "seeds" {index: empty},
    "slots" and the parts."""
    col = V.collection(col_name)
    mats = materials()
    slots = slots or seed_slots()
    root = V.link(bpy.data.objects.new(f"{name}_Root", None), col)
    root.location = base
    stem, rec, bracts, top = stem_and_base(col, mats, length, name=name)
    hd = V.link(bpy.data.objects.new(f"{name}_Head", None), col)
    hd.location = top
    seeds_on_head = head(col, mats, slots, skip=set(loose), name=name)
    for o in [stem, rec] + bracts:
        o.parent = root
    hd.parent = root
    for o in seeds_on_head:
        o.parent = hd
    loose_objs = {}
    for i in loose:
        e = loose_seed(col, mats, slots[i], f"{name}_Seed_{i:03d}")
        e.parent = hd
        e.matrix_parent_inverse = Matrix.Identity(4)
        M = slot_matrix(slots[i])
        e.location = M.translation
        e.rotation_quaternion = M.to_quaternion()
        loose_objs[i] = e
    return {"root": root, "head": hd, "seeds": loose_objs, "slots": slots, "mats": mats, "col": col,
            "parts": [stem, rec] + bracts + seeds_on_head}


def facing(slots, direction, count, min_up=-0.2):
    """Indices of the `count` seeds pointing most towards a direction (head frame)."""
    d = Vector(direction).normalized()
    order = sorted(range(len(slots)), key=lambda i: -slots[i]["dir"].dot(d))
    return [i for i in order if slots[i]["dir"].z > min_up][:count]


def drift(seed_obj, frames, path, spin=1.5, upright_by=14, flutter=0.08):
    """Break a loose seed off and let the breeze carry it. Until frames[0] it rides on its
    (swaying) head; then it follows `path` (world points after its start) with eased timing,
    turning parachute-up over `upright_by` frames, slowly spinning and fluttering.
    Everything is baked to world-space keys on every frame, so the parenting is dropped."""
    sc = bpy.context.scene
    f0, f1 = frames
    ride = []
    for f in range(sc.frame_start, f0 + 1):                       # world transform while still on the head
        sc.frame_set(f)
        ride.append((f, seed_obj.matrix_world.copy()))
    start = ride[-1][1]
    q0 = start.to_quaternion()
    seed_obj.parent = None
    seed_obj.matrix_parent_inverse = Matrix.Identity(4)
    for f, M in ride[:-1]:
        seed_obj.location = M.translation
        seed_obj.rotation_quaternion = M.to_quaternion()
        seed_obj.keyframe_insert("location", frame=f)
        seed_obj.keyframe_insert("rotation_quaternion", frame=f)
    pts = K.path_spline([tuple(start.translation)] + [tuple(p) for p in path], 120) if len(path) > 1 \
        else np.array([tuple(start.translation), tuple(path[-1])])
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    rng = np.random.default_rng(zlib.crc32(seed_obj.name.encode()))  # same flutter in every render run
    ph = rng.uniform(0, 6.28, 3)
    for f in range(f0, f1 + 1):
        u = (f - f0) / max(f1 - f0, 1)
        s = 0.5 * (u * u * (3 - 2 * u)) + 0.5 * u                   # mostly steady drift, eased at the start
        d = s * seg[-1]
        j = min(int(np.searchsorted(seg, d)), len(pts) - 1)
        a = (d - seg[j - 1]) / max(seg[j] - seg[j - 1], 1e-9) if j > 0 else 0.0
        p = Vector(pts[j - 1]).lerp(Vector(pts[j]), a) if j > 0 else Vector(pts[0])
        w = min(1.0, (f - f0) / max(upright_by, 1))
        w = w * w * (3 - 2 * w)
        tilt = Matrix.Rotation(flutter * math.sin(0.5 * f + ph[0]), 3, "X") @ \
            Matrix.Rotation(flutter * math.sin(0.37 * f + ph[1]), 3, "Y")
        up = (tilt @ Matrix.Rotation(spin * (f - f0) / 30.0 + ph[2], 3, "Z")).to_quaternion()
        seed_obj.location = p
        seed_obj.rotation_quaternion = q0.slerp(up, w)
        seed_obj.keyframe_insert("location", frame=f)
        seed_obj.keyframe_insert("rotation_quaternion", frame=f)
    return seed_obj
