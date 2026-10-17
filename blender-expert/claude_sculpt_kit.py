"""claude_sculpt_kit - code-driven sculpting toolkit for Blender (tested on 4.5 LTS and 5.2 LTS).

Lets Claude (via the Blender connector) sculpt the way a creature artist does:
brushes, layered skin detail, teeth/crystal builders and a clay presentation rig.
Everything is numpy-vectorized and edits mesh data directly (no fragile bpy.ops).

Install / import (the bootstrap in PROMPT.md does this automatically):
    put this file in Downloads, then in Blender:  import claude_sculpt_kit as K

Conventions
    * Coordinates are object-local. Build at the origin, -Y is the creature's front,
      +Z is up, the model is symmetric in X (brushes mirror across X by default).
    * Work in Object Mode on a dense voxel-remeshed mesh (not under Multires).
    * H = head length (snout tip to back of skull). Size detail relative to H.

Tested sizes (Leviathan demo, H = 1.9; ratios transfer to any scale)
    final voxel_remesh ......... H/420  (~1.3M faces for a neck bust)
    belly scutes(path=spine) ... row H/17, col H/11, height H/85, groove 0.1
    side scales ................ size H/27,  height H/190, jitter 0.6
    head pebble scales ......... size H/47,  height H/300, jitter 0.95
    eye-ring micro scales ...... size H/105, height H/600
    back crust skin(ridged) .... size H/17,  height H/85
    pores skin ................. size H/240, height H/2400
    crease (wrinkles/folds) .... radius H/55-H/27, depth H/160-H/63, pinch 0.3-0.5
    teeth ...................... length H/27-H/7, 2 fang positions
    crystals big / small ....... size 0.24H-0.45H (thickness 0.25) / 0.02H-0.07H

API (most used)
    blockout:  ellipsoid, tube, metaball_blockout, join, boolean, voxel_remesh, smooth
    brushes:   dab(mode=draw|inflate|blob|grab|pinch|flatten), stroke, crease, smooth
    paths:     path_spline, path_line, path_ring, resample, snap (project onto surface)
    masks:     mask_normal, mask_axis, mask_sphere, mask_near, mask_noise (multiply them)
    detail:    scutes, scales, folds, skin, bumps, grow_around, displace
    parts:     teeth, crystals, eye, tooth_mesh, crystal_mesh, instance_join
    look-dev:  clay_material, light_rig, camera, dark_world, render_setup, render_still
    viewport:  viewport_clay, frame_view   (then take a connector screenshot)
    utility:   stats, edge_length, bounds, save_version, apply_modifiers, collection,
               archive_others (hide everything else in an OLD collection; never deletes)
"""
import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

VERSION = "1.0"


def install(source_text):
    """Write this kit into Blender's user scripts/modules folder so that
    `import claude_sculpt_kit` works in every future session."""
    import os, sys
    d = bpy.utils.user_resource("SCRIPTS", path="modules", create=True)
    with open(os.path.join(d, "claude_sculpt_kit.py"), "w", encoding="utf-8") as f:
        f.write(source_text)
    if d not in sys.path:
        sys.path.append(d)
    return d


# --------------------------------------------------------------------------
# Scene / mesh basics
# --------------------------------------------------------------------------
def collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def archive_others(keep=("SCULPT", "PARTS", "LIGHTS", "CAMERA")):
    """Move every object outside the `keep` collections into a hidden OLD
    collection (viewport + render). Nothing is deleted; returns moved names."""
    old = collection("OLD")
    old.hide_render = True
    old.hide_viewport = True
    keep_cols = {bpy.data.collections.get(k) for k in keep} - {None}
    moved = []
    for ob in list(bpy.context.scene.objects):
        if not any(c in keep_cols for c in ob.users_collection) and old not in ob.users_collection:
            link(ob, old)
            moved.append(ob.name)
    return moved


def link(obj, col=None):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj


def _object_mode(obj):
    if getattr(obj, "mode", "OBJECT") != "OBJECT":
        try:
            with bpy.context.temp_override(active_object=obj, object=obj):
                bpy.ops.object.mode_set(mode="OBJECT")
        except Exception:
            bpy.ops.object.mode_set(mode="OBJECT")


def co(obj):
    _object_mode(obj)
    me = obj.data
    a = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def set_co(obj, P):
    _object_mode(obj)
    me = obj.data
    me.vertices.foreach_set("co", np.ascontiguousarray(P, np.float64).ravel())
    me.update()


def normals(obj):
    me = obj.data
    n = np.empty(len(me.vertices) * 3, np.float64)
    if hasattr(me, "vertex_normals"):
        me.vertex_normals.foreach_get("vector", n)
    else:  # Blender <= 4.0
        me.vertices.foreach_get("normal", n)
    return n.reshape(-1, 3)


def edges(obj):
    me = obj.data
    e = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", e)
    return e.reshape(-1, 2)


def edge_length(obj):
    """Mean edge length - detail must be >= 6-8x this to read cleanly."""
    P, E = co(obj), edges(obj)
    return float(np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1).mean())


def stats(obj=None):
    objs = [obj] if obj else [o for o in bpy.context.scene.objects if o.type == "MESH"]
    out = {}
    for o in objs:
        out[o.name] = {"verts": len(o.data.vertices), "faces": len(o.data.polygons)}
    return out


def apply_modifiers(obj):
    """Bake the modifier stack into the mesh without bpy.ops."""
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj


def apply_transform(obj):
    """Bake location/rotation/scale into the mesh (kit coordinates are local == world)."""
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj.data.update()
    return obj


def join(objs, name, col=None):
    """Merge meshes (world space) into one new object; originals are removed."""
    bm = bmesh.new()
    for o in objs:
        tmp = o.data.copy()
        tmp.transform(o.matrix_world)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for o in objs:
        bpy.data.objects.remove(o)
    obj = link(bpy.data.objects.new(name, me), col)
    shade_smooth(obj)
    return obj


def shade_smooth(obj, smooth=True):
    obj.data.polygons.foreach_set("use_smooth", [smooth] * len(obj.data.polygons))
    obj.data.update()


def voxel_remesh(obj, voxel_size, adaptivity=0.0):
    """Uniform re-topology; smaller voxel = more faces (~area / voxel^2)."""
    m = obj.modifiers.new("Remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel_size
    m.adaptivity = adaptivity
    apply_modifiers(obj)
    shade_smooth(obj)
    return obj


def save_version(tag):
    """Snapshot the file as <name>_<tag>.blend next to the current file (or in temp)."""
    import os, tempfile
    base = bpy.data.filepath or os.path.join(tempfile.gettempdir(), "claude_sculpt.blend")
    root, _ = os.path.splitext(base)
    path = f"{root}_{tag}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return path


def bounds(obj):
    M = np.array(obj.matrix_world)
    P = co(obj) @ M[:3, :3].T + M[:3, 3]
    lo, hi = P.min(0), P.max(0)
    return lo, hi, (lo + hi) / 2, float(np.linalg.norm(hi - lo) / 2)


# --------------------------------------------------------------------------
# Falloffs and masks (all return per-vertex weights 0..1)
# --------------------------------------------------------------------------
def falloff(t, kind="smooth"):
    t = np.clip(t, 0.0, 1.0)
    if kind == "smooth":
        return 1 - t * t * (3 - 2 * t)
    if kind == "sphere":
        return np.sqrt(np.maximum(0, 1 - t * t))
    if kind == "sharp":
        return (1 - t) ** 2
    if kind == "root":
        return np.sqrt(1 - t)
    if kind == "linear":
        return 1 - t
    return np.ones_like(t)


def mask_sphere(obj, center, radius, kind="smooth", symmetry_x=True):
    P = co(obj)
    w = falloff(np.linalg.norm(P - np.asarray(center), axis=1) / radius, kind)
    if symmetry_x:
        c2 = np.asarray(center, float) * [-1, 1, 1]
        w = np.maximum(w, falloff(np.linalg.norm(P - c2, axis=1) / radius, kind))
    return w


def mask_normal(obj, direction, lo=0.0, hi=1.0):
    """Weight by how much the surface faces `direction` (dot in [lo, hi] -> 0..1)."""
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    return np.clip((normals(obj) @ d - lo) / max(hi - lo, 1e-6), 0, 1)


def mask_axis(obj, axis, lo, hi, feather):
    """Band along an axis (0=x,1=y,2=z) with soft edges."""
    x = co(obj)[:, axis]
    a = np.clip((x - (lo - feather)) / max(feather, 1e-9), 0, 1)
    b = np.clip(((hi + feather) - x) / max(feather, 1e-9), 0, 1)
    return a * b


def mask_near(obj, points, radius, kind="smooth"):
    """Weight by distance to a point cloud (e.g. crystal bases, eye sockets)."""
    P = co(obj)
    pts = np.asarray(points, float).reshape(-1, 3)
    w = np.zeros(len(P))
    for c in pts:
        w = np.maximum(w, falloff(np.linalg.norm(P - c, axis=1) / radius, kind))
    return w


def mask_noise(obj, size, seed=0, contrast=1.5):
    """Low-frequency breakup so detail is never uniform."""
    n = fbm(co(obj), size, octaves=3, seed=seed)
    return np.clip(0.5 + contrast * n, 0, 1)


# --------------------------------------------------------------------------
# Brushes (local space). strength is a fraction of radius.
# --------------------------------------------------------------------------
def _centers(c, symmetry_x):
    c = np.asarray(c, float)
    out = [(c, 1.0)]
    if symmetry_x and abs(c[0]) > 1e-9:
        out.append((c * [-1, 1, 1], -1.0))
    return out


def dab(obj, center, radius, strength, mode="draw", vector=(0, 0, 0), kind="smooth",
        symmetry_x=True, mask=None):
    """One brush dab. strength is a fraction of radius (0.05 subtle, 0.3 strong).
    mode: draw (area normal), inflate (vertex normals), blob (inflate + pinch),
    grab (move by `vector` * strength), pinch (toward center), flatten (toward area plane)."""
    P, N = co(obj), normals(obj)
    D = np.zeros_like(P)
    for c, sx in _centers(center, symmetry_x):
        d = np.linalg.norm(P - c, axis=1)
        idx = np.nonzero(d < radius)[0]
        if not len(idx):
            continue
        fw = falloff(d[idx] / radius, kind)
        if mask is not None:
            fw = fw * np.asarray(mask)[idx]
        n = (N[idx] * fw[:, None]).sum(0)
        n /= max(np.linalg.norm(n), 1e-12)
        if mode == "draw":
            D[idx] += n * (fw * strength * radius)[:, None]
        elif mode in ("inflate", "blob"):
            D[idx] += N[idx] * (fw * strength * radius)[:, None]
            if mode == "blob":
                D[idx] += (c - P[idx]) * (0.3 * fw * strength)[:, None]
        elif mode == "grab":
            D[idx] += (np.asarray(vector, float) * [sx, 1, 1]) * (fw * strength)[:, None]
        elif mode == "pinch":
            D[idx] += (c - P[idx]) * (0.5 * fw * strength)[:, None]
        elif mode == "flatten":
            cen = (P[idx] * fw[:, None]).sum(0) / max(fw.sum(), 1e-12)
            D[idx] -= n * (((P[idx] - cen) @ n) * fw * min(strength, 1.0))[:, None]
    set_co(obj, P + D)


def stroke(obj, path, radius, strength, mode="draw", spacing=0.35, **kw):
    """Repeated dabs along a polyline (spacing as a fraction of radius)."""
    for p in resample(path, radius * spacing):
        dab(obj, p, radius, strength, mode=mode, **kw)


def crease(obj, path, radius, depth, pinch=0.5, kind="sharp", symmetry_x=True, mask=None):
    """Groove along a polyline (depth > 0) or ridge (depth < 0). pinch sharpens it.
    Use for wrinkles, folds, lip lines, scale borders, cracks, eyelids."""
    P, N = co(obj), normals(obj)
    D = np.zeros_like(P)
    path = np.asarray(path, float)
    paths = [path]
    if symmetry_x and np.abs(path[:, 0]).max() > 1e-9:
        paths.append(path * [-1, 1, 1])
    for pth in paths:
        lo, hi = pth.min(0) - radius, pth.max(0) + radius
        idx = np.nonzero(np.all((P >= lo) & (P <= hi), axis=1))[0]
        if not len(idx):
            continue
        Q = P[idx]
        best = np.full(len(idx), np.inf)
        foot = np.zeros_like(Q)
        for a, b in zip(pth[:-1], pth[1:]):
            ab = b - a
            t = np.clip((Q - a) @ ab / max(ab @ ab, 1e-12), 0, 1)
            f = a + t[:, None] * ab
            d = np.linalg.norm(Q - f, axis=1)
            m = d < best
            best[m], foot[m] = d[m], f[m]
        w = falloff(best / radius, kind)
        if mask is not None:
            w = w * mask[idx]
        D[idx] += -depth * w[:, None] * N[idx] + pinch * 0.5 * w[:, None] * (foot - Q)
    set_co(obj, P + D)


def smooth(obj, iterations=3, factor=0.5, mask=None, taubin=True):
    """Laplacian smoothing (Taubin keeps volume). mask limits where it acts."""
    P, E = co(obj), edges(obj)
    n = len(P)
    deg = np.maximum(np.bincount(E[:, 0], minlength=n) + np.bincount(E[:, 1], minlength=n), 1)
    w = factor if mask is None else factor * np.asarray(mask)[:, None]
    for i in range(iterations * (2 if taubin else 1)):
        S = np.empty_like(P)
        for c in range(3):
            S[:, c] = (np.bincount(E[:, 0], weights=P[E[:, 1], c], minlength=n)
                       + np.bincount(E[:, 1], weights=P[E[:, 0], c], minlength=n))
        step = (S / deg[:, None] - P) * w
        P = P + (step if (not taubin or i % 2 == 0) else -1.04 * step)
    set_co(obj, P)


# --------------------------------------------------------------------------
# Paths (for strokes, creases, placement)
# --------------------------------------------------------------------------
def resample(path, step):
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, L[-1], max(2, int(L[-1] / max(step, 1e-9)) + 1))
    return np.stack([np.interp(s, L, path[:, k]) for k in range(3)], 1)


def path_line(a, b, n=24):
    return np.linspace(np.asarray(a, float), np.asarray(b, float), n)


def path_ring(center, normal, radius, n=48, squash=1.0, closed=True):
    c, z = np.asarray(center, float), Vector(normal).normalized()
    x = z.orthogonal().normalized()
    y = z.cross(x)
    t = np.linspace(0, 2 * math.pi, n + (1 if closed else 0), endpoint=closed)
    return c + np.outer(np.cos(t) * radius, x) + np.outer(np.sin(t) * radius * squash, y)


def path_spline(ctrl, n=64):
    """Catmull-Rom through control points."""
    p = np.asarray(ctrl, float)
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, max(2, n // (len(p) - 3)), endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)


def snap(obj, points, offset=0.0):
    """Project points onto the surface; returns (locations, normals) in local space."""
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(obj, dg)
    locs, nors = [], []
    for p in np.asarray(points, float):
        hit = tree.find_nearest(Vector(p))
        loc, nor = hit[0], hit[1]
        locs.append(np.array(loc + nor * offset))
        nors.append(np.array(nor))
    return np.array(locs), np.array(nors)


# --------------------------------------------------------------------------
# Procedural detail (vectorized noise -> displacement along normals)
# --------------------------------------------------------------------------
def _hash(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761 + 1013904223)
    h = h & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return h


def worley(P, size, jitter=0.9, stretch=(1, 1, 1), seed=0, chunk=400000):
    """Cellular noise. Returns (F1, F2, cell_id) in cell units."""
    Q = np.asarray(P, float) / (size * np.asarray(stretch, float))
    F1 = np.empty(len(Q)); F2 = np.empty(len(Q)); ID = np.empty(len(Q), np.int64)
    for s in range(0, len(Q), chunk):
        q = Q[s:s + chunk]
        b = np.floor(q).astype(np.int64)
        f = q - b
        f1 = np.full(len(q), np.inf); f2 = np.full(len(q), np.inf); cid = np.zeros(len(q), np.int64)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    h = _hash(b[:, 0] + dx, b[:, 1] + dy, b[:, 2] + dz, seed)
                    jx = ((h & 1023) / 1023.0 - 0.5) * jitter
                    jy = (((h >> 10) & 1023) / 1023.0 - 0.5) * jitter
                    jz = (((h >> 20) & 1023) / 1023.0 - 0.5) * jitter
                    d = ((dx + 0.5 + jx - f[:, 0]) ** 2 + (dy + 0.5 + jy - f[:, 1]) ** 2
                         + (dz + 0.5 + jz - f[:, 2]) ** 2)
                    m1 = d < f1
                    f2 = np.where(m1, f1, np.minimum(f2, d))
                    cid = np.where(m1, h, cid)
                    f1 = np.where(m1, d, f1)
        F1[s:s + chunk], F2[s:s + chunk], ID[s:s + chunk] = np.sqrt(f1), np.sqrt(f2), cid
    return F1, F2, ID


def _value_noise(Q, seed):
    b = np.floor(Q).astype(np.int64)
    f = Q - b
    u = f * f * (3 - 2 * f)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                v = (_hash(b[:, 0] + dx, b[:, 1] + dy, b[:, 2] + dz, seed) & 0xFFFF) / 32767.5 - 1.0
                wx = u[:, 0] if dx else 1 - u[:, 0]
                wy = u[:, 1] if dy else 1 - u[:, 1]
                wz = u[:, 2] if dz else 1 - u[:, 2]
                out = out + v * wx * wy * wz
    return out


def fbm(P, size, octaves=5, lacunarity=2.0, gain=0.5, seed=0, ridged=False):
    """Fractal noise in about [-1, 1]; ridged=True gives sharp crests (rock, veins)."""
    Q = np.asarray(P, float) / size
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        n = _value_noise(Q * (lacunarity ** o), seed + 101 * o)
        if ridged:
            n = 1 - 2 * np.abs(n)
        total = total + amp * n
        norm += amp
        amp *= gain
    return total / norm


def displace(obj, h, mask=None):
    """Push vertices along normals by per-vertex height h (local units)."""
    if mask is not None:
        h = h * mask
    set_co(obj, co(obj) + normals(obj) * np.asarray(h)[:, None])


def scales(obj, size, height, groove=0.12, dome=0.7, jitter=0.85, stretch=(1, 1, 1),
           mask=None, seed=0, vary=0.3):
    """Reptile scales / plates: raised cells separated by grooves.
    size: cell diameter (local units). jitter 0.1-0.3 + stretch -> belly scutes;
    jitter 0.8-1.0 -> pebble scales. Needs size >= 6-8 x edge_length."""
    P = co(obj)
    F1, F2, ID = worley(P, size, jitter, stretch, seed)
    edge = F2 - F1
    plate = np.clip(edge / max(groove, 1e-6), 0, 1)
    plate = plate * plate * (3 - 2 * plate)
    bulge = np.clip(1 - F1 / 0.85, 0, 1) ** 0.6
    rnd = 1 + vary * (((ID & 255) / 255.0) - 0.5) * 2
    h = height * plate * ((1 - dome) + dome * bulge) * rnd
    displace(obj, h, mask)
    return h


def path_coords(obj, path, chunk=200000):
    """Per-vertex (s, u, r): arc length along `path`, arc length around it, distance
    from it. Uses parallel-transport frames, so rows stay aligned along curved necks."""
    pth = np.asarray(path, float)
    seg = np.diff(pth, axis=0)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(seg, axis=1))])
    T = seg / np.maximum(np.linalg.norm(seg, axis=1), 1e-12)[:, None]
    Nf = np.zeros_like(T)
    n = np.cross(T[0], [1, 0, 0] if abs(T[0][0]) < 0.9 else [0, 1, 0])
    for i, t in enumerate(T):
        n = n - t * (n @ t)
        n /= np.linalg.norm(n)
        Nf[i] = n
    Bf = np.cross(T, Nf)
    P = co(obj)
    S_, U_, R_ = np.empty(len(P)), np.empty(len(P)), np.empty(len(P))
    for a0 in range(0, len(P), chunk):
        Q = P[a0:a0 + chunk]
        best = np.full(len(Q), np.inf)
        si = np.zeros(len(Q), np.int64)
        tt = np.zeros(len(Q))
        for k in range(len(seg)):
            t = np.clip((Q - pth[k]) @ seg[k] / max(seg[k] @ seg[k], 1e-12), 0, 1)
            d = np.linalg.norm(Q - (pth[k] + t[:, None] * seg[k]), axis=1)
            m = d < best
            best[m], si[m], tt[m] = d[m], k, t[m]
        foot = pth[si] + tt[:, None] * seg[si]
        v = Q - foot
        theta = np.arctan2(np.einsum("ij,ij->i", v, Bf[si]), np.einsum("ij,ij->i", v, Nf[si]))
        S_[a0:a0 + chunk] = L[si] + tt * np.linalg.norm(seg[si], axis=1)
        U_[a0:a0 + chunk] = theta * best
        R_[a0:a0 + chunk] = best
    return S_, U_, R_


def scutes(obj, path, row, col, height, groove=0.12, dome=0.75, brick=0.5, vary=0.3,
           mask=None, seed=0, wobble=0.25, corner=3.0):
    """Crocodile/serpent belly plates: rows of rectangular scutes that follow a
    curve (neck/tail spine path). row: plate length along the path, col: plate
    width around it (local units). brick: row offset (0.5 = staggered).
    corner: 2-4 rounds plate corners (higher = squarer). wobble/vary break regularity.
    Combine with mask_normal() so plates stay on the belly/throat side."""
    S_, U_, _ = path_coords(obj, path)
    P = co(obj)
    if wobble:
        S_ = S_ + wobble * row * fbm(P, row * 2.5, octaves=2, seed=seed)
        U_ = U_ + wobble * col * fbm(P, col * 2.5, octaves=2, seed=seed + 7)
    i = np.floor(S_ / row)
    fu = U_ / col + brick * (i % 2)
    j = np.floor(fu)
    a, b = S_ / row - i, fu - j
    ds = np.maximum(np.minimum(a, 1 - a) * row, 1e-9)
    du = np.maximum(np.minimum(b, 1 - b) * col, 1e-9)
    edge = (ds ** -corner + du ** -corner) ** (-1.0 / corner)
    g = groove * min(row, col)
    plate = np.clip(edge / max(g, 1e-9), 0, 1)
    plate = plate * plate * (3 - 2 * plate)
    bulge = 1 - 0.5 * ((2 * a - 1) ** 2 + (2 * b - 1) ** 2)
    rnd = 1 + vary * (((_hash(i.astype(np.int64), j.astype(np.int64), np.zeros_like(i, np.int64), seed) & 255) / 255.0) - 0.5) * 2
    h = height * plate * ((1 - dome) + dome * bulge) * rnd
    displace(obj, h, mask)
    return h


def folds(obj, direction, spacing, depth, width=0.18, wobble=0.35, mask=None, seed=0):
    """Parallel creases across `direction` every `spacing` units (neck rings,
    palate ridges, belly folds). wobble bends them organically."""
    P = co(obj)
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    ph = P @ d / spacing + wobble * fbm(P, spacing * 3, octaves=3, seed=seed)
    frac = ph - np.floor(ph) - 0.5
    line = np.exp(-(frac / width) ** 2)
    displace(obj, -depth * line, mask)


def skin(obj, size, height, octaves=4, ridged=False, mask=None, seed=0):
    """Organic surface noise: pores (small size), rocky crust (ridged), lumps (large)."""
    displace(obj, height * fbm(co(obj), size, octaves=octaves, seed=seed, ridged=ridged), mask)


def bumps(obj, points, radius, height, kind="sphere", symmetry_x=True):
    """Nodules / bead rows / warts at given points."""
    for p in np.asarray(points, float):
        dab(obj, p, radius, height / radius, mode="inflate", kind=kind, symmetry_x=symmetry_x)


def grow_around(obj, points, radius, height, kind="smooth"):
    """Raise flesh around embedded parts (crystal bases, horn roots, teeth)."""
    displace(obj, height * mask_near(obj, points, radius, kind))


# --------------------------------------------------------------------------
# Parts
# --------------------------------------------------------------------------
def metaball_blockout(name, elements, resolution=0.04, threshold=0.6, col=None):
    """Organic block-out from ellipsoids. element dict: co, radius, size=(sx,sy,sz),
    rot=(deg x,y,z), negative=False, stiffness=2.0. Returns a mesh object."""
    mb = bpy.data.metaballs.new(name + "_mb")
    mb.resolution = mb.render_resolution = resolution
    mb.threshold = threshold
    for e in elements:
        el = mb.elements.new(type="ELLIPSOID" if "size" in e else "BALL")
        el.co = e["co"]
        el.radius = e["radius"]
        if "size" in e:
            el.size_x, el.size_y, el.size_z = e["size"]
        if "rot" in e:
            el.rotation = Euler([math.radians(a) for a in e["rot"]]).to_quaternion()
        el.use_negative = e.get("negative", False)
        el.stiffness = e.get("stiffness", 2.0)
    mbo = bpy.data.objects.new(name + "_mb", mb)
    bpy.context.scene.collection.objects.link(mbo)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(mbo.evaluated_get(dg))
    bpy.data.objects.remove(mbo)
    bpy.data.metaballs.remove(mb)
    obj = link(bpy.data.objects.new(name, me), col)
    shade_smooth(obj)
    return obj


def ellipsoid(name, center, radii, rot=(0, 0, 0), segments=48, col=None):
    """Exact-size ellipsoid primitive for block-outs (radii = semi-axes, rot in degrees)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=1.0)
    M = (Matrix.Translation(Vector(center)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
         @ Matrix.Diagonal(Vector((*radii, 1.0))))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me), col)
    shade_smooth(obj)
    return obj


def tube(name, path, radii, segments=32, squash=None, col=None):
    """Sweep a circle along a polyline with per-point radius (necks, tails, tentacles,
    horns). squash: optional per-point (sx, sy) to flatten the section (e.g. hood)."""
    pts = [Vector(p) for p in np.asarray(path, float)]
    rad = np.broadcast_to(np.asarray(radii, float), (len(pts),))
    bm = bmesh.new()
    tang = [(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(len(pts))]
    nrm = tang[0].orthogonal().normalized()
    loops = []
    for i, (p, t) in enumerate(zip(pts, tang)):
        nrm = (nrm - t * nrm.dot(t)).normalized()          # parallel transport
        bin_ = t.cross(nrm)
        sx, sy = squash[i] if squash is not None else (1.0, 1.0)
        loops.append([bm.verts.new(p + (nrm * math.cos(a) * sx + bin_ * math.sin(a) * sy) * rad[i])
                      for a in np.linspace(0, 2 * math.pi, segments, endpoint=False)])
    for a, b in zip(loops[:-1], loops[1:]):
        for s in range(segments):
            bm.faces.new((a[s], a[(s + 1) % segments], b[(s + 1) % segments], b[s]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me), col)
    shade_smooth(obj)
    return obj


def boolean(obj, cutter, operation="DIFFERENCE", keep_cutter=False):
    """Exact boolean (DIFFERENCE / UNION / INTERSECT) baked into obj."""
    m = obj.modifiers.new("Bool", "BOOLEAN")
    m.operation = operation
    m.solver = "EXACT"
    m.object = cutter
    cutter.hide_render = cutter.hide_viewport = True
    apply_modifiers(obj)
    if not keep_cutter:
        bpy.data.objects.remove(cutter)
    return obj


def tooth_mesh(length=1.0, radius=0.12, bend=0.25, rings=10, segments=12, tip=0.03):
    """Curved conical tooth along +Z, bending toward +Y."""
    bm = bmesh.new()
    loops = []
    for i in range(rings):
        t = i / (rings - 1)
        r = radius * ((1 - t) ** 0.85 * (1 - tip) + tip)
        y0 = bend * length * t * t
        loops.append([bm.verts.new((r * math.cos(a), y0 + r * math.sin(a), length * t))
                      for a in np.linspace(0, 2 * math.pi, segments, endpoint=False)])
    for a, b in zip(loops[:-1], loops[1:]):
        for s in range(segments):
            bm.faces.new((a[s], a[(s + 1) % segments], b[(s + 1) % segments], b[s]))
    apex = bm.verts.new((0, bend * length * 1.02, length * 1.04))
    for s in range(segments):
        bm.faces.new((loops[-1][s], loops[-1][(s + 1) % segments], apex))
    bm.faces.new(list(reversed(loops[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def crystal_mesh(radius=0.1, height=0.5, tip=0.35, sides=6, flare=0.06, broken=False, seed=0):
    """Hexagonal quartz column: pointed (off-centre apex) or broken (slanted flat top)."""
    rng = random.Random(seed)
    bm = bmesh.new()
    ang = [2 * math.pi * i / sides + rng.uniform(-0.08, 0.08) for i in range(sides)]
    low = [bm.verts.new((radius * (1 + flare) * math.cos(a), radius * (1 + flare) * math.sin(a), -0.25 * height))
           for a in ang]
    tilt = (rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35))
    top = []
    for a in ang:
        x, y = radius * math.cos(a), radius * math.sin(a)
        z = height * (1 + rng.uniform(-0.05, 0.05)) + (x * tilt[0] + y * tilt[1] if broken else 0)
        top.append(bm.verts.new((x, y, z)))
    for s in range(sides):
        bm.faces.new((low[s], low[(s + 1) % sides], top[(s + 1) % sides], top[s]))
    if broken:
        bm.faces.new(top)
    else:
        apex = bm.verts.new((rng.uniform(-0.3, 0.3) * radius, rng.uniform(-0.3, 0.3) * radius,
                             height * (1 + tip * rng.uniform(0.7, 1.2))))
        for s in range(sides):
            bm.faces.new((top[s], top[(s + 1) % sides], apex))
    bm.faces.new(list(reversed(low)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for e in bm.edges:
        e.smooth = False          # sharp: normals split at every crystal edge
    for f in bm.faces:
        f.smooth = True           # but stay smooth inside each facet
    return bm


def _frame(direction, up_hint):
    z = Vector(direction).normalized()
    y = Vector(up_hint) - z * Vector(up_hint).dot(z)
    if y.length < 1e-6:
        y = z.orthogonal()
    y.normalize()
    return Matrix((z.cross(y).normalized(), y, z)).transposed()


def instance_join(name, make_bm, placements, col=None, smooth=True, symmetry_x=True):
    """Build one mesh from many generated parts.
    placements: list of dict(loc, dir, up=(0,1,0), scale=1, twist=0deg, seed).
    make_bm(seed) -> bmesh in local +Z orientation."""
    out = bmesh.new()
    items = list(placements)
    if symmetry_x:
        for p in list(items):
            if abs(p["loc"][0]) > 1e-6:
                q = dict(p)
                q["loc"] = (-p["loc"][0], p["loc"][1], p["loc"][2])
                q["dir"] = (-p["dir"][0], p["dir"][1], p["dir"][2])
                u = p.get("up", (0, 1, 0))
                q["up"] = (-u[0], u[1], u[2])
                q["mirror"] = True
                q["twist"] = -p.get("twist", 0)
                items.append(q)
    for p in items:
        part = make_bm(p.get("seed", 0))
        R = _frame(p["dir"], p.get("up", (0, 1, 0))) @ Matrix.Rotation(math.radians(p.get("twist", 0)), 3, "Z")
        if p.get("mirror"):
            R = R @ Matrix.Scale(-1, 3, Vector((1, 0, 0)))
        s = p.get("scale", 1.0)
        S = Matrix.Diagonal(Vector(s if isinstance(s, (tuple, list)) else (s, s, s)))
        M = Matrix.Translation(Vector(p["loc"])) @ (R @ S).to_4x4()
        bmesh.ops.transform(part, matrix=M, verts=part.verts)
        if p.get("mirror"):
            bmesh.ops.reverse_faces(part, faces=part.faces)
        tmp = bpy.data.meshes.new("_tmp")
        part.to_mesh(tmp)
        part.free()
        out.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name)
    out.to_mesh(me)
    out.free()
    obj = link(bpy.data.objects.new(name, me), col)
    if smooth is not None:
        shade_smooth(obj, smooth)
    return obj


def teeth(name, gum_path, body, length=(0.05, 0.12), radius_ratio=0.16, direction=(0, 0, -1),
          inward=(0, 1, 0), bend=0.25, count=None, fang_at=(0.15,), seed=0, col=None, embed=0.25):
    """Teeth along a gum line (local points on `body`), mirrored in X.
    length: (min, max); fang_at: positions 0..1 along the path that get the longest teeth."""
    rng = random.Random(seed)
    pts = np.asarray(gum_path, float)
    if count:
        pts = resample(pts, np.linalg.norm(np.diff(pts, axis=0), axis=1).sum() / max(count - 1, 1))
    locs, nors = snap(body, pts)
    plc = []
    for i, (p, n) in enumerate(zip(locs, nors)):
        t = i / max(len(locs) - 1, 1)
        fang = max(math.exp(-((t - f) / 0.08) ** 2) for f in fang_at)
        L = length[0] + (length[1] - length[0]) * (0.35 * rng.random() + 0.65 * fang)
        d = Vector(direction).normalized() * 0.8 + Vector(n) * -0.2
        plc.append({"loc": tuple(Vector(p) - d.normalized() * L * embed), "dir": tuple(d),
                    "up": inward, "scale": L, "twist": rng.uniform(-12, 12), "seed": i + seed})
    obj = instance_join(name, lambda s: tooth_mesh(1.0, radius_ratio, bend * random.Random(s).uniform(0.7, 1.3)),
                        plc, col)
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.levels, sub.render_levels = 1, 2
    return obj


def crystals(name, body, points, size=(0.05, 0.3), direction=None, tilt=20, broken=0.4,
             embed=0.25, seed=0, col=None, facet_noise=0.012, thickness=0.22):
    """Quartz clusters erupting from a surface. Returns (object, base_locations);
    pass base_locations to grow_around() so flesh climbs the bases.
    points: local positions on/near body.
    direction: None (surface normal), one vector, or one vector per point.
    Modifier stack like the video: Bevel -> Subdivision (Simple) -> Displace (Voronoi)
    for subtly irregular facets; edges are marked sharp so facets stay clean."""
    rng = random.Random(seed)
    locs, nors = snap(body, points)
    plc = []
    for i, (p, n) in enumerate(zip(locs, nors)):
        L = rng.uniform(*size)
        if direction is None:
            d = Vector(n)
        else:
            dd = np.asarray(direction, float)
            d = Vector(dd[i] if dd.ndim == 2 else dd).normalized()
        d = (d + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * math.tan(math.radians(tilt))).normalized()
        plc.append({"loc": tuple(Vector(p) - d * L * embed), "dir": tuple(d), "up": (0, 0, 1),
                    "scale": L, "twist": rng.uniform(0, 60), "seed": seed * 997 + i})
    obj = instance_join(name, lambda s: crystal_mesh(thickness, 1.0, 0.35, 6, 0.06,
                                                     random.Random(s).random() < broken, s),
                        plc, col, smooth=None)
    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.006 * size[1]
    bev.segments = 2
    bev.limit_method = "ANGLE"
    bev.harden_normals = False
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 2
    tex = bpy.data.textures.new(name + "_facets", "VORONOI")
    tex.distance_metric = "DISTANCE"
    tex.color_mode = "INTENSITY"
    tex.noise_scale = max(size[1], 1e-3) * 0.25
    tex.weight_1, tex.weight_2, tex.weight_3, tex.weight_4 = 1.0, 0.0, 0.0, 0.0
    dsp = obj.modifiers.new("Facets", "DISPLACE")
    dsp.texture = tex
    dsp.texture_coords = "LOCAL"
    dsp.direction = "NORMAL"
    dsp.strength = facet_noise * size[1]
    dsp.mid_level = 0.5
    return obj, locs


def eye(name, center, radius, col=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=radius)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me), col)
    obj.location = center
    shade_smooth(obj)
    obj.data.materials.append(glossy_eye_material())
    return obj


# --------------------------------------------------------------------------
# Look-dev: clay, lights, camera, world, render (Cycles)
# --------------------------------------------------------------------------
def _nodes(idblock):
    if getattr(idblock, "node_tree", None) is None and hasattr(idblock, "use_nodes"):
        idblock.use_nodes = True
    return idblock.node_tree


def _inp(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    return None


def clay_material(name="Clay", color=(0.22, 0.22, 0.215), roughness=0.5, ao_distance=0.15,
                  cavity=0.85, edges=0.2):
    """Grey sculpt clay with AO-darkened crevices and lit ridges (needs Cycles for
    Pointiness). ao_distance in scene units (~2-5% of model height)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = _nodes(mat)
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _inp(bsdf, "Roughness").default_value = roughness
    s = _inp(bsdf, "Specular IOR Level", "Specular")
    if s:
        s.default_value = 0.35
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = ao_distance
    ao.samples = 16
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.46, 0.56
    base = nt.nodes.new("ShaderNodeRGB")
    base.outputs[0].default_value = (*color, 1)
    mix_ao = nt.nodes.new("ShaderNodeMix")
    mix_ao.data_type = "RGBA"
    mix_ao.blend_type = "MULTIPLY"
    mix_ao.inputs[0].default_value = cavity
    mix_edge = nt.nodes.new("ShaderNodeMix")
    mix_edge.data_type = "RGBA"
    mix_edge.blend_type = "SCREEN"
    nt.links.new(base.outputs[0], ao.inputs["Color"])
    nt.links.new(base.outputs[0], mix_ao.inputs[6])
    nt.links.new(ao.outputs["AO"], mix_ao.inputs[7])
    nt.links.new(geo.outputs["Pointiness"], ramp.inputs[0])
    edge_amt = nt.nodes.new("ShaderNodeMath")
    edge_amt.operation = "MULTIPLY"
    edge_amt.inputs[1].default_value = edges
    nt.links.new(ramp.outputs[0], edge_amt.inputs[0])
    nt.links.new(edge_amt.outputs[0], mix_edge.inputs[0])
    nt.links.new(mix_ao.outputs[2], mix_edge.inputs[6])
    mix_edge.inputs[7].default_value = (1, 1, 1, 1)
    nt.links.new(mix_edge.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return mat


def glossy_eye_material(name="Eye_Glossy", color=(0.05, 0.004, 0.002)):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = _nodes(mat).nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        bsdf.inputs["Roughness"].default_value = 0.05
        c = _inp(bsdf, "Coat Weight", "Clearcoat")
        if c:
            c.default_value = 1.0
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def look_dir(az, el):
    """Unit vector from the target toward a viewer at azimuth az (0 = front/-Y,
    90 = right/+X) and elevation el (degrees)."""
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def _aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(name, target, az, el, dist, power, size, color=(1, 1, 1), col=None):
    lt = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
    lt.energy, lt.size, lt.color = power, size, color
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, lt)
    if ob.data is not lt:
        ob.data = lt
    link(ob, col or collection("LIGHTS"))
    ob.location = Vector(target) + look_dir(az, el) * dist
    _aim(ob, target)
    return ob


def light_rig(target_obj, key=3.0, fill=0.8, back=6.0, top=1.5, flip=False):
    """Video rig: soft white key (front-left high), pale cyan fill (HSV .526/.31/1)
    from the other side, strong back/rim light and a light above the head.
    Values are irradiance ratios; powers scale with distance so any model size works."""
    lo, hi, c, R = bounds(target_obj)
    col = collection("LIGHTS")
    s = -1 if flip else 1
    d = 3.0 * R

    def watts(irr):  # area light, irradiance ~ P / (pi d^2)
        return irr * math.pi * d * d
    rig = [
        area_light("Key_lgt", c, -55 * s, 40, d, watts(key), 1.2 * R, (1, 0.98, 0.95), col),
        area_light("Fill_lgt", c, 70 * s, 5, d, watts(fill), 0.6 * R, (0.69, 0.95, 1.0), col),
        area_light("Back_lgt", c, 160 * s, 30, d, watts(back), 0.5 * R, (1, 1, 1), col),
        area_light("Top_lgt", c + Vector((0, 0, R * 0.5)), 0, 85, d, watts(top), 0.5 * R, (1, 1, 1), col),
    ]
    return rig


def camera(target_obj, az=-35, el=8, lens=85, res=(1080, 1268), fill=0.9, name="Camera"):
    lo, hi, c, R = bounds(target_obj)
    cam = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam.lens = lens
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, cam)
    if ob.data is not cam:
        ob.data = cam
    link(ob, collection("CAMERA"))
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    half = math.atan(18.0 * min(res) / max(res) / lens)
    ob.location = c + look_dir(az, el) * (R / math.sin(half) / fill)
    _aim(ob, c)
    sc.camera = ob
    return ob


def dark_world(top=(0.020, 0.030, 0.050), bottom=(0.002, 0.002, 0.004), strength=1.0):
    """Studio void: navy-to-black gradient seen by the camera, near-black for lighting."""
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    nt = _nodes(w)
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.3, 0.75
    ramp.color_ramp.elements[0].color = (*bottom, 1)
    ramp.color_ramp.elements[1].color = (*top, 1)
    remap = nt.nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value, remap.inputs["From Max"].default_value = -1.0, 1.0
    cam_bg = nt.nodes.new("ShaderNodeBackground")
    cam_bg.inputs["Strength"].default_value = strength
    amb = nt.nodes.new("ShaderNodeBackground")
    amb.inputs["Color"].default_value = (0.01, 0.012, 0.016, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], remap.inputs["Value"])
    nt.links.new(remap.outputs["Result"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], cam_bg.inputs["Color"])
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(amb.outputs[0], mix.inputs[1])
    nt.links.new(cam_bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return w


def render_setup(samples=512, noise=0.01, denoise=True, device="CPU", look="Medium High Contrast"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = device
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = noise
    sc.cycles.use_denoising = denoise
    for vt, lk in (("AgX", look), ("AgX", "AgX - " + look), ("Filmic", look)):
        try:
            sc.view_settings.view_transform = vt
            sc.view_settings.look = lk
            break
        except Exception:
            continue
    return sc


def render_still(path, samples=None):
    sc = bpy.context.scene
    if samples:
        sc.cycles.samples = samples
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


# --------------------------------------------------------------------------
# Live viewport helpers (interactive Blender only; no-ops in background)
# --------------------------------------------------------------------------
def _views3d():
    wm = bpy.context.window_manager
    for win in (wm.windows if wm else []):
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                yield area


def viewport_clay(matcap=None, cavity=True):
    """Matcap + cavity so fine scales/wrinkles are visible in screenshots.
    Picks a neutral grey matcap that exists in this Blender version."""
    names = [l.name for l in bpy.context.preferences.studio_lights if l.type == "MATCAP"]
    pick = matcap if matcap in names else next(
        (n for n in ("basic_grey.exr", "basic_1.exr", "clay_studio.exr", "basic_2.exr") if n in names),
        names[0] if names else None)
    for area in _views3d():
        sh = area.spaces.active.shading
        sh.type = "SOLID"
        sh.light = "MATCAP"
        if pick:
            sh.studio_light = pick
        sh.show_cavity = cavity
        sh.cavity_type = "BOTH"
        sh.curvature_ridge_factor = sh.curvature_valley_factor = 1.5
    return pick


def frame_view(target_obj, az=-35, el=10, zoom=2.4, focus=None):
    """Point every 3D view at the model from a repeatable angle (for screenshots).
    focus=(x,y,z) local point + smaller zoom for close-ups."""
    lo, hi, c, R = bounds(target_obj)
    center = Vector(focus) if focus is not None else c
    for area in _views3d():
        r3d = area.spaces.active.region_3d
        r3d.view_perspective = "PERSP"
        r3d.view_location = center
        r3d.view_rotation = Euler((math.radians(90 - el), 0, math.radians(az))).to_quaternion()
        r3d.view_distance = R * zoom
