"""Her airways for the x-ray shots: the lungs with the bronchial tree branching inside, the
windpipe with its C-shaped cartilage rings, the voice box, the throat (pharynx), the nasal
passage, the mouth cavity (puffed out while she holds the sneeze in) and the thin tubes up to
her middle ears (Eustachian tubes). Stylised anatomy built here and placed inside her posed
body; build() also returns the centre lines the air travels along.

Head parts are placed in her head's own frame (it is bowed in the hold pose), measured from
the tip of her nose: f = forwards (+) / backwards (-), u = up, x = to her left (+).
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

import character as C
import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
NASAL = [(-0.015, -0.006), (-0.027, -0.002), (-0.05, 0.002), (-0.076, -0.002), (-0.1, -0.012)]
NASAL_R = [0.004, 0.006, 0.0075, 0.0075, 0.0075]
NASAL_FLAT = [(1.6, 1.0), (1.3, 1.6), (1.1, 2.1), (1.1, 1.9), (1.0, 1.0)]   # (sideways, up-down): a tall, narrow chamber
PHARYNX = [(-0.1, -0.012), (-0.111, -0.04), (-0.108, -0.072), (-0.098, -0.098)]
ORAL = [(-0.026, -0.036), (-0.045, -0.04), (-0.072, -0.047), (-0.1, -0.055)]   # starts behind the lips (1.3 cm)
LARYNX = [(-0.098, -0.098), (-0.09, -0.112), (-0.084, -0.127)]
EAR_MIDDLE = (-0.099, 0.006, 0.033)                 # middle ear, each side (x mirrored): just inside her ear
                                                    # canal (its opening, the floor of her ear's bowl, is at
                                                    # (-0.101, 0.009, 0.060), measured on her "ears" vertex group)
EUSTACHIAN = [(-0.096, -0.014, 0.011), (-0.098, -0.005, 0.022), EAR_MIDDLE]


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
def _dithered(mat):
    """Order-independent transparency (layers of glass inside glass sort cleanly in EEVEE)."""
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "HASHED"
    return mat


GLOW = "#4FB4FF"                       # the light the rushing air throws on the walls (air_fx tints it)


def _value(nt, name, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.name = n.label = name
    n.outputs[0].default_value = value
    return n.outputs[0]


def add_air_glow(mat, point, radius=0.03, color=GLOW):
    """Light the walls up around a moving point (the air rushing through): an extra cyan
    emission that falls off with the distance from the empty `point`. Keyable values:
    AirGlow (strength) and AirGlowRadius (m)."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial" and n.is_active_output)
    current = out.inputs["Surface"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.object = point
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], dist.inputs[0])
    near = nt.nodes.new("ShaderNodeMapRange")
    near.interpolation_type = "SMOOTHSTEP"
    near.inputs["To Min"].default_value, near.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(dist.outputs["Value"], near.inputs["Value"])
    nt.links.new(_value(nt, "AirGlowRadius", radius), near.inputs["From Max"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = em.label = "AirGlowEmission"
    em.inputs["Color"].default_value = (*H(color), 1)
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = "MULTIPLY"
    nt.links.new(near.outputs["Result"], m.inputs[0])
    nt.links.new(_value(nt, "AirGlow", 0.0), m.inputs[1])
    nt.links.new(m.outputs[0], em.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(current, add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return mat


def materials():
    return {
        "glass": _dithered(V.xray("Airway_Glass", H("#FF6E8A"), strength=1.1, edge=0.38, core=0.035)),
        "lung": _dithered(V.xray("Lung_Glass", H("#FF7890"), strength=1.3, edge=0.5, core=0.1)),
        "bronchi": V.emission("Bronchi_Glow", H("#FFC3CE"), 1.1),
        "cartilage": V.principled("Cartilage", H("#F4C8CF"), rough=0.35, sss=0.2, sss_radius=(1, 0.5, 0.5),
                                  sss_scale=0.002, coat=0.3, emission=H("#F7B5C1"), emission_strength=0.35),
        "eardrum": V.principled("Eardrum", H("#F4C6C2"), rough=0.3, sss=0.4, sss_radius=(1, 0.5, 0.4),
                                sss_scale=0.002, emission=H("#FF9A8E"), emission_strength=0.3),   # a warm pink glow
    }


# --------------------------------------------------------------------------
# Placement
# --------------------------------------------------------------------------
def head_frame(hero, nose):
    """Function (f, u, x) -> world point in her head's frame, from the tip of her nose."""
    rig = hero["rig"]
    M = (rig.matrix_world @ rig.pose.bones["head"].matrix).to_3x3()
    X, Y, Z = (M.col[i].normalized() for i in range(3))
    nose = Vector(nose)
    return lambda f, u, x=0.0: nose + Z * f + Y * u + X * x


def torso_sections(hero, z_levels, arm_limit=0.3):
    """Front, back and half-width of her torso (arms left out) at heights z: {z: (front_y,
    back_y, half_width)}, from the posed body."""
    body = hero["body"]
    P = C.evaluated_points(body)
    arm = [g.index for g in body.vertex_groups if any(k in g.name for k in ("arm", "wrist", "finger", "metacarpal",
                                                                             "shoulder", "clavicle"))]
    w = np.zeros(len(P))
    for v in body.data.vertices:
        for g in v.groups:
            if g.group in arm:
                w[v.index] += g.weight
    torso = w < arm_limit
    out = {}
    for z in z_levels:
        sel = torso & (np.abs(P[:, 2] - z) < 0.008)
        if sel.sum() >= 5:
            Q = P[sel]
            out[z] = (float(Q[:, 1].min()), float(Q[:, 1].max()), float(np.abs(Q[:, 0]).max()))
    return out


def torso_bounds(hero, z_levels, arm_limit=0.3, band=0.006):
    """Her torso's extent (arms left out) at heights z: {z: (x_min, x_max, front_y, back_y)}."""
    body = hero["body"]
    P = C.evaluated_points(body)
    arm = [g.index for g in body.vertex_groups if any(k in g.name for k in ("arm", "wrist", "finger", "metacarpal",
                                                                             "shoulder", "clavicle"))]
    w = np.zeros(len(P))
    for v in body.data.vertices:
        for g in v.groups:
            if g.group in arm:
                w[v.index] += g.weight
    torso = w < arm_limit
    out = {}
    for z in z_levels:
        Q = P[torso & (np.abs(P[:, 2] - z) < band)]
        if len(Q) >= 8:
            out[z] = (float(Q[:, 0].min()), float(Q[:, 0].max()), float(Q[:, 1].min()), float(Q[:, 1].max()))
    return out


def fit_inside(ob, bounds, margin=0.015, step=0.008):
    """Keep a mesh (world coordinates, object at the origin) inside her torso: height by
    height, its sideways and front-to-back extent is mapped into the room between her skin
    (less `margin`), so a lung follows her rib cage as it narrows towards her waist.
    Changes the mesh; returns the same mapping as a function for other points."""
    P = np.array([v.co[:] for v in ob.data.vertices])
    zl = sorted(bounds)
    levels = np.arange(P[:, 2].min(), P[:, 2].max() + step, step)
    maps = []
    for z in levels:
        sel = np.abs(P[:, 2] - z) < step * 0.75
        if sel.sum() < 4:
            maps.append(None)
            continue
        x0, x1 = P[sel, 0].min(), P[sel, 0].max()
        y0, y1 = P[sel, 1].min(), P[sel, 1].max()
        bx0, bx1, by0, by1 = bounds[min(zl, key=lambda k: abs(k - z))]
        tx0, tx1 = max(x0, bx0 + margin), min(x1, bx1 - margin)
        ty0, ty1 = max(y0, by0 + margin), min(y1, by1 - margin)
        tx1, ty1 = max(tx1, tx0 + 0.01), max(ty1, ty0 + 0.01)
        maps.append(((tx1 - tx0) / max(x1 - x0, 1e-6), x0, tx0, (ty1 - ty0) / max(y1 - y0, 1e-6), y0, ty0))
    good = [m for m in maps if m is not None]
    maps = np.array([m if m is not None else good[0] for m in maps])
    k = np.ones(3) / 3                                            # no kinks between heights
    maps = np.stack([np.convolve(np.r_[maps[0, j], maps[:, j], maps[-1, j]], k, mode="valid")
                     for j in range(6)], 1)

    def fit(p):
        p = np.asarray(p, float)
        m = [np.interp(p[2], levels, maps[:, j]) for j in range(6)]
        return Vector((m[2] + (p[0] - m[1]) * m[0], m[5] + (p[1] - m[4]) * m[3], p[2]))

    for v in ob.data.vertices:
        v.co = fit(v.co)
    ob.data.update()
    return fit


# --------------------------------------------------------------------------
# Pieces
# --------------------------------------------------------------------------
def _chain_elements(points, radii, flat=None, step=0.003):
    """Metaball ellipsoids along a polyline (radius per point; flat: per-point (lateral,
    vertical) scale for flattened passages)."""
    P = K.path_spline(points, max(8, int(sum((Vector(a) - Vector(b)).length for a, b in zip(points, points[1:]))
                                          / step)))
    R = np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, len(radii)), radii)
    F = None
    if flat is not None:
        F = np.stack([np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, len(flat)), [f[k] for f in flat])
                      for k in range(2)], 1)
    out = []
    for i, (p, r) in enumerate(zip(P, R)):
        e = {"co": tuple(p), "radius": float(r), "stiffness": 2.0}
        if F is not None:
            t = Vector(P[min(i + 1, len(P) - 1)]) - Vector(P[max(i - 1, 0)])
            # an ellipsoid wide sideways (x) and tall/flat (z), long along the path: as a rotation
            e["size"] = (float(F[i][0]), 1.0, float(F[i][1]))
            e["rot_q"] = t.to_track_quat("Y", "Z")
        out.append(e)
    return out


UP = 10.0                    # metaballs polygonise no finer than 5 mm: build at 10x, then scale back
CHAIN_GAIN = 1.47            # a chain of metaballs surfaces at ~0.68 of its radius (measured)
BLOB_GAIN = 1.74             # a lone metaball ellipsoid surfaces at ~0.575 of its size (measured)


def _metaball_mesh(name, elements, resolution, col, gain=1.0):
    """Polygonise metaballs into a mesh (built UP times larger, then scaled back, so small
    passages come out smooth). gain scales every radius: a metaball's surface sits well
    inside its nominal radius (see CHAIN_GAIN, BLOB_GAIN)."""
    mb = bpy.data.metaballs.new(name + "_mb")
    mb.resolution = mb.render_resolution = resolution * UP
    mb.threshold = 0.6
    for e in elements:
        el = mb.elements.new(type="ELLIPSOID" if "size" in e else "BALL")
        el.co = tuple(c * UP for c in e["co"])
        el.radius, el.stiffness = e["radius"] * gain * UP, e.get("stiffness", 2.0)
        if "size" in e:
            el.size_x, el.size_y, el.size_z = e["size"]
        if "rot_q" in e:
            el.rotation = e["rot_q"]
        el.use_negative = e.get("negative", False)
    mbo = bpy.data.objects.new(name + "_mb", mb)
    bpy.context.scene.collection.objects.link(mbo)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(mbo.evaluated_get(dg))
    bpy.data.objects.remove(mbo)
    bpy.data.metaballs.remove(mb)
    me.transform(Matrix.Scale(1.0 / UP, 4))
    ob = V.link(bpy.data.objects.new(name, me), col)
    K.shade_smooth(ob)
    return ob


def lung(name, centre, size, side, col, notch=False):
    """One lung: blended ellipsoids (wide base, narrow apex), flattened on the inner side,
    hollowed underneath by the diaphragm's dome (and the heart's notch on the left).
    side: -1 = her right lung, +1 = left. size: (half-width, half-depth, half-height)."""
    a, b, c = size
    cx, cy, cz = centre
    s = side
    E = [{"co": (cx, cy, cz - 0.15 * c), "radius": 1.0, "size": (a, b, 0.78 * c)},
         {"co": (cx - s * 0.18 * a, cy + 0.12 * b, cz + 0.55 * c), "radius": 1.0, "size": (0.62 * a, 0.62 * b, 0.5 * c)},
         {"co": (cx + s * 0.08 * a, cy - 0.04 * b, cz - 0.55 * c), "radius": 1.0, "size": (1.05 * a, 1.04 * b, 0.42 * c)},
         {"co": (cx - s * 1.55 * a, cy, cz), "radius": 1.0, "size": (0.75 * a, 1.3 * b, 1.4 * c), "negative": True},
         {"co": (cx + s * 0.1 * a, cy, cz - 1.25 * c), "radius": 1.0, "size": (0.9 * a, 0.95 * b, 0.42 * c),
          "negative": True}]
    if notch:
        E.append({"co": (cx - s * 0.95 * a, cy - 0.65 * b, cz - 0.45 * c), "radius": 1.0,
                  "size": (0.5 * a, 0.5 * b, 0.45 * c), "negative": True})
    return _metaball_mesh(name, E, 0.004, col, gain=BLOB_GAIN), E


def _set_origin(ob, c=None):
    """Move an object's origin to c (default: the middle of its mesh), so it scales about c."""
    if c is None:
        P = np.array([tuple(v.co) for v in ob.data.vertices])
        c = Vector(((P.min(0) + P.max(0)) / 2).tolist())
    c = Vector(c)
    ob.data.transform(Matrix.Translation(-c))
    ob.location = c
    return c


def _inside(p, E):
    """Is p inside the union of the positive ellipsoids and outside every negative one?"""
    def inn(e):
        d = (np.asarray(p) - np.asarray(e["co"])) / np.asarray(e["size"])
        return float(d @ d) < 0.8
    return any(inn(e) for e in E if not e.get("negative")) and not any(inn(e) for e in E if e.get("negative"))


def bronchial_tree(start, direction, E, rng, n_attr=420, step=0.0045, kill=0.006, reach=0.03):
    """Space colonisation: the airway branches grow from the hilum towards points filling the
    lung. Returns a list of polylines (each a branch from fork to fork/tip) and radii."""
    lo = np.min([np.asarray(e["co"]) - np.asarray(e["size"]) for e in E if not e.get("negative")], 0)
    hi = np.max([np.asarray(e["co"]) + np.asarray(e["size"]) for e in E if not e.get("negative")], 0)
    attr = []
    while len(attr) < n_attr:
        p = rng.uniform(lo, hi)
        if _inside(p, E):
            attr.append(p)
    attr = np.array(attr)
    nodes = [np.asarray(start, float), np.asarray(start, float) + np.asarray(direction) * step]
    parent = [-1, 0]
    for _ in range(140):
        if len(attr) == 0:
            break
        N = np.array(nodes)
        d = np.linalg.norm(attr[:, None, :] - N[None, :, :], axis=2)
        near = d.argmin(1)
        ok = d[np.arange(len(attr)), near] < reach
        grow = {}
        for ai in np.where(ok)[0]:
            ni = near[ai]
            v = attr[ai] - N[ni]
            grow.setdefault(ni, []).append(v / (np.linalg.norm(v) + 1e-9))
        if not grow:
            reach *= 1.4
            continue
        for ni, dirs in grow.items():
            dvec = np.mean(dirs, 0)
            dvec /= np.linalg.norm(dvec) + 1e-9
            nodes.append(N[ni] + dvec * step)
            parent.append(ni)
        N = np.array(nodes)
        d = np.linalg.norm(attr[:, None, :] - N[None, :, :], axis=2).min(1)
        attr = attr[d > kill]
    # pipe model radii: leaves thin, each fork adds up (r^2.5 rule)
    n = len(nodes)
    kids = [[] for _ in range(n)]
    for i, p in enumerate(parent):
        if p >= 0:
            kids[p].append(i)
    rad = np.zeros(n)
    for i in reversed(range(n)):
        rad[i] = 0.00055 if not kids[i] else sum(rad[k] ** 2.5 for k in kids[i]) ** (1 / 2.5)
    # polylines from each fork (or the root) down to the next fork or tip
    lines = []
    for i in range(n):
        if parent[i] == -1 or len(kids[parent[i]]) > 1:
            chain = [parent[i]] if parent[i] >= 0 else []
            j = i
            chain.append(j)
            while len(kids[j]) == 1:
                j = kids[j][0]
                chain.append(j)
            lines.append(([nodes[k] for k in chain], [rad[k] for k in chain]))
    return lines, np.array(nodes), parent


def branch_paths(nodes, parent, count, rng):
    """Paths from `count` branch tips back to the root (the hilum), as point lists."""
    kids = set(p for p in parent if p >= 0)
    tips = [i for i in range(len(nodes)) if i not in kids]
    out = []
    for i in rng.choice(tips, size=min(count, len(tips)), replace=False):
        chain = [int(i)]
        while parent[chain[-1]] >= 0:
            chain.append(parent[chain[-1]])
        out.append([Vector(nodes[k]) for k in chain])
    return out


def _curves(name, lines, mat, col, min_points=2):
    lines = [(p, r) for p, r in lines if len(p) >= min_points]
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([len(p) for p, _ in lines])
    P = np.concatenate([np.asarray(p, np.float32) for p, _ in lines])
    R = np.concatenate([np.asarray(r, np.float32) for _, r in lines])
    cv.attributes["position"].data.foreach_set("vector", P.reshape(-1))
    if "radius" not in cv.attributes:
        cv.attributes.new("radius", "FLOAT", "POINT")
    cv.attributes["radius"].data.foreach_set("value", R)
    cv.materials.append(mat)
    bpy.context.scene.render.hair_type = "STRIP"
    return V.link(bpy.data.objects.new(name, cv), col)


def _body_bvh(hero):
    """Her posed skin as a BVH (world space), for finding where things reach the surface."""
    from mathutils.bvhtree import BVHTree
    body = hero["body"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    M = body.matrix_world
    bvh = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    return bvh


def eardrum(name, centre, normal, radius=0.0045, cone=0.0012, bulge=0.0034, rings=10, segments=40, col=None):
    """The eardrum: a thin round membrane facing `normal` (out of her head), drawn in a little
    at its centre like a shallow cone (as a real one is); shape key "Bulge" domes it out
    towards the ear canal (the trapped air pushing from inside)."""
    n = Vector(normal).normalized()
    t1 = n.orthogonal().normalized()
    t2 = n.cross(t1)
    c = Vector(centre)
    base, out = [c - n * cone], [c + n * bulge]
    for i in range(1, rings + 1):
        t = i / rings
        for k in range(segments):
            a = 2 * math.pi * k / segments
            p = c + (t1 * math.cos(a) + t2 * math.sin(a)) * radius * t
            base.append(p - n * cone * (1 - t))
            out.append(p + n * bulge * (1 - t * t))
    faces = [(0, 1 + k, 1 + (k + 1) % segments) for k in range(segments)]
    for i in range(rings - 1):
        r0, r1 = 1 + i * segments, 1 + (i + 1) * segments
        faces += [(r0 + k, r1 + k, r1 + (k + 1) % segments, r0 + (k + 1) % segments) for k in range(segments)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in base], [], faces)
    ob = V.link(bpy.data.objects.new(name, me), col)
    K.shade_smooth(ob)
    ob.shape_key_add(name="Basis")
    sk = ob.shape_key_add(name="Bulge")
    for v, p in zip(sk.data, out):
        v.co = p
    return ob


def windpipe(path, col, mats, radius=0.0085, ring_gap=0.0042):
    """Windpipe: a see-through tube with C-shaped cartilage rings (open at the back, +Y)."""
    P = K.path_spline(path, 60)
    tube = K.tube("Windpipe", P, radius, segments=24, col=col)
    V.assign(tube, mats["glass"])
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    rings = []
    for s in np.arange(ring_gap, L[-1] - ring_gap, ring_gap):
        i = int(np.searchsorted(L, s))
        c = Vector(P[i])
        t = (Vector(P[min(i + 1, len(P) - 1)]) - Vector(P[max(i - 1, 0)])).normalized()
        back = (Vector((0, 1, 0)) - t * t.y).normalized()
        side = t.cross(back).normalized()
        arc = [c + (back * math.cos(a) + side * math.sin(a)) * (radius * 1.05)
               for a in np.linspace(math.radians(35), math.radians(325), 18)]
        rings.append(K.tube(f"Windpipe_Ring_{len(rings)}", [tuple(p) for p in arc], radius * 0.17, segments=8, col=col,
                            squash=(1.0, 0.45)))
    ring_obj = K.join(rings, "Windpipe_Rings", col)
    V.assign(ring_obj, mats["cartilage"])
    return tube, ring_obj


# --------------------------------------------------------------------------
# Everything
# --------------------------------------------------------------------------
def build(hero, nose, col_name="XRAY_AIRWAYS", puffed=1.0, seed=7, ears=True):
    """Build her airways inside her posed body. nose: tip of her nose (world). puffed: how
    blown-up the mouth cavity is (her cheeks). ears: show the ear tubes and eardrums.
    Returns dict of objects and air paths."""
    col = V.collection(col_name)
    mats = materials()
    hf = head_frame(hero, nose)
    rng = np.random.default_rng(seed)
    rig = hero["rig"]
    shoulder_z = (rig.matrix_world @ rig.pose.bones["upperarm01.R"].head).z
    z_car = shoulder_z - 0.06
    secs = torso_sections(hero, [round(z, 3) for z in np.arange(z_car - 0.15, z_car + 0.1, 0.01)])
    bounds = torso_bounds(hero, [round(z, 3) for z in np.arange(z_car - 0.2, z_car + 0.12, 0.01)])
    back_at = lambda z: secs[min(secs, key=lambda k: abs(k - z))][1]
    half_at = lambda z: secs[min(secs, key=lambda k: abs(k - z))][2]

    # head and throat passages (one smooth cast)
    nasal = [hf(f, u) for f, u in NASAL]
    nostrils = [hf(NASAL[0][0] + 0.002, NASAL[0][1] - 0.002, sx * 0.005) for sx in (-1, 1)]   # pinched shut, inside the nose
    pharynx = [hf(f, u) for f, u in PHARYNX]
    oral = [hf(f, u) for f, u in ORAL]
    larynx = [hf(f, u) for f, u in LARYNX]
    E = []
    E += _chain_elements(nasal, NASAL_R, flat=NASAL_FLAT)
    E += _chain_elements(pharynx, [0.0075, 0.0085, 0.008, 0.0075])
    # the mouth: a wide, flat pocket of air behind the shut lips, out into the puffed cheeks
    E += _chain_elements(oral, [0.0045, 0.0065 + 0.002 * puffed, 0.006 + 0.0015 * puffed, 0.0065],
                         flat=[(2.6, 0.75), (2.3 + 0.5 * puffed, 0.8 + 0.1 * puffed), (1.6, 0.85), (1.2, 0.95)])
    E += _chain_elements(larynx, [0.0075, 0.009, 0.0075])
    cast = _metaball_mesh("Airway_Cast", E, 0.0022, col, gain=CHAIN_GAIN)
    V.assign(cast, mats["glass"])
    _set_origin(cast)

    # windpipe from the voice box down into the chest, branching at the carina
    top = larynx[-1]
    y_car = back_at(z_car) - 0.095
    trachea = [top, Vector((0, top.y + 0.002, top.z - 0.03)), Vector((0, (top.y + y_car) / 2, (top.z + z_car) / 2 - 0.01)),
               Vector((0, y_car, z_car))]
    tube, rings = windpipe(trachea, col, mats)

    # lungs and bronchi
    lungs, trees, hila, branches, mains = {}, {}, {}, {}, {}
    for name, s in (("R", -1), ("L", 1)):
        hw = half_at(z_car - 0.04) * (0.84 if s < 0 else 0.8)
        centre = (s * (0.022 + hw) / 2 + s * 0.006, y_car - 0.002, z_car - 0.035)
        size = ((hw - 0.022) / 2, 0.058 if s < 0 else 0.055, 0.1 if s < 0 else 0.095)
        lungs[name], Elung = lung(f"Lung_{name}", centre, size, s, col, notch=(s > 0))
        V.assign(lungs[name], mats["lung"])
        fit = fit_inside(lungs[name], bounds)
        grow_from = Vector((s * 0.03, y_car + 0.004, z_car - 0.02))
        lines, nodes, parent = bronchial_tree(grow_from, (s * 0.7, 0.0, -0.3), Elung, rng)
        nodes = np.array([tuple(fit(p)) for p in nodes])                # the tree bends with its lung
        lines = [([tuple(fit(p)) for p in pts], r) for pts, r in lines]
        hilum = fit(grow_from)
        hila[name] = hilum
        main = [Vector((0, y_car, z_car)), Vector((s * 0.014, y_car + 0.002, z_car - 0.008)), hilum]
        mb = K.tube(f"Bronchus_{name}", K.path_spline([tuple(p) for p in main], 16), [0.0062, 0.0055, 0.005][-1],
                    segments=16, col=col)
        V.assign(mb, mats["glass"])
        branches[name] = branch_paths(nodes, parent, 40, rng)
        c = _set_origin(lungs[name], hilum)                      # the lung deflates towards its hilum
        trees[name] = _curves(f"Bronchial_Tree_{name}", [([p - np.asarray(c) for p in pts], r) for pts, r in lines],
                              mats["bronchi"], col)
        trees[name].parent = lungs[name]
        mains[name] = [Vector(p) for p in reversed(main)]        # hilum -> carina

    # ear tubes, middle ears and eardrums (for the ear shots)
    ears_on, ears = ears, {}
    body_bvh = _body_bvh(hero)
    for name, sx in (("R", -1), ("L", 1)):
        pts = [hf(f, u, sx * x) for f, u, x in EUSTACHIAN]
        et = K.tube(f"Eustachian_{name}", K.path_spline([tuple(p) for p in pts], 24), 0.0022, segments=10, col=col)
        V.assign(et, mats["glass"])
        mid = hf(*EAR_MIDDLE[:2], sx * EAR_MIDDLE[2])
        out = (hf(0, 0, sx) - hf(0, 0, 0)).normalized()               # out of her head on this side
        cavity = K.ellipsoid(f"Middle_Ear_{name}", tuple(mid), (0.0042, 0.0042, 0.0042), segments=24, col=col)
        V.assign(cavity, mats["glass"])
        drum_c = mid + out * 0.0055
        drum = eardrum(f"Eardrum_{name}", drum_c, out, col=col)
        V.assign(drum, mats["eardrum"])
        hit = body_bvh.ray_cast(drum_c + out * 0.004, out, 0.06)       # where the ear canal reaches her skin
        opening = hit[0] - out * 0.0012 if hit[0] is not None else drum_c + out * 0.022
        up = (hf(0, 1, 0) - hf(0, 0, 0)).normalized()
        bend = drum_c + (opening - drum_c) * 0.55 + up * 0.0015 + (hf(1, 0, 0) - hf(0, 0, 0)).normalized() * 0.0012
        canal = K.tube(f"Ear_Canal_{name}", K.path_spline([tuple(drum_c + out * 0.0004), tuple(bend), tuple(opening)], 24),
                       0.0034, segments=16, col=col)
        V.assign(canal, mats["glass"])
        ears[name] = {"tube": et, "drum": drum, "cavity": cavity, "canal": canal, "path": pts, "middle": mid,
                      "drum_centre": drum_c, "out": out, "opening": opening}
        for o in (et, drum, cavity, canal):
            o.hide_render = o.hide_viewport = not ears_on

    # the air's routes (centre lines, world space), all running the way the air goes
    fwd = (hf(1, 0) - hf(0, 0)).normalized()
    paths = {
        "bronchus_R": mains["R"], "bronchus_L": mains["L"],              # hilum -> carina
        "windpipe": [Vector(p) for p in reversed(trachea)],                # carina -> voice box
        "larynx": [Vector(p) for p in reversed(larynx)],                   # voice box -> throat
        "pharynx": [Vector(p) for p in reversed(pharynx)],                 # throat -> back of the nose
        "nasal": [Vector(p) for p in reversed(nasal)],                     # back of the nose -> pinched nostrils
        "oral": [pharynx[2]] + [Vector(p) for p in reversed(oral)],        # throat -> shut lips
        "nostrils": nostrils, "nose_end": nasal[0] + fwd * 0.004, "lips_end": oral[0] + fwd * 0.004,
        "ear_R": ears["R"]["path"], "ear_L": ears["L"]["path"],         # top of the throat -> middle ear
    }
    glow = V.link(bpy.data.objects.new("Air_GlowPoint", None), col)
    glow.empty_display_size = 0.01
    glow.location = Vector((0, y_car, z_car))
    for m in (mats["glass"], mats["lung"]):
        add_air_glow(m, glow)
    walls = [cast, tube] + [o for o in col.objects if o.name.startswith("Bronchus_")]
    if ears_on:
        walls += [o for d in ears.values() for o in (d["tube"], d["cavity"])]
    return {"col": col, "mats": mats, "cast": cast, "windpipe": tube, "rings": rings, "lungs": lungs,
            "trees": trees, "ears": ears, "paths": paths, "head": hf, "carina": Vector((0, y_car, z_car)),
            "hila": hila, "branches": branches, "glow": glow, "walls": walls, "forward": fwd}


def attach(hero, aw):
    """Make the airways ride on her (posed when they were built): the head passages and ears
    on her head bone, the windpipe and lungs on her chest. Each group hangs from an empty
    that sits exactly at the world origin on the current frame, so nothing moves now."""
    rig = hero["rig"]
    bpy.context.view_layer.update()
    roots = {}
    for key, bone in (("head", "head"), ("chest", "spine01")):
        e = V.link(bpy.data.objects.new(f"Airways_{key}_root", None), aw["col"])
        e.parent, e.parent_type, e.parent_bone = rig, "BONE", bone
        bpy.context.view_layer.update()
        e.matrix_world = Matrix.Identity(4)
        roots[key] = e
    bpy.context.view_layer.update()
    head = [aw["cast"]] + [o for d in aw["ears"].values() for o in (d["tube"], d["drum"], d["cavity"], d["canal"])]
    chest = [aw["windpipe"], aw["rings"], aw["glow"]] + list(aw["lungs"].values()) + \
            [o for o in aw["col"].objects if o.name.startswith("Bronchus_")]
    for group, objs in (("head", head), ("chest", chest)):
        for o in objs:
            M = o.matrix_world.copy()
            o.parent = roots[group]
            o.matrix_world = M
    aw["roots"] = roots
    return roots
