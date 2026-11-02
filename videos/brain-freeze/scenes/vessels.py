"""Blood vessel network for the x-ray shots 9-11: palatine arteries running along the roof
of the mouth with branches across it, and two trunks climbing from the back of the
palate to the underside of the frontal lobes, where they fan out. Each generation is its
own curve object so it can grow in turn and squeeze/balloon (animate bevel_depth).
Same coordinates as mouth_set (mouth opening -Y, up +Z, metres)."""
import math

import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import mouth_set as MS
import vfx_kit as V

H = V.hex_lin
BRAIN_C, BRAIN_R = Vector((0.0, 0.022, 0.104)), (0.066, 0.082, 0.048)


def _wiggle(pts, rng, amount, n=None):
    """Resample a polyline to n points and add smooth sideways wiggle."""
    pts = np.asarray(pts, float)
    n = n or max(len(pts) * 3, 8)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, L[-1], n)
    P = np.stack([np.interp(s, L, pts[:, k]) for k in range(3)], 1)
    w = np.zeros_like(P)
    for k in range(3):
        f = rng.uniform(1.5, 3.5)
        ph = rng.uniform(0, 6.3)
        w[:, k] = np.sin(s / max(L[-1], 1e-9) * f * math.pi + ph)
    taper = np.sin(np.linspace(0, math.pi, n)) ** 0.5
    taper[0] = 0.0                                                   # keep the start attached
    return P + w * amount * taper[:, None]


def _in_palate(x, y, depth=0.0013):
    return float(MS.palate_height(x, y)) + depth


def _on_brain(x, y, gap=0.0012):
    """Height just below the underside of the frontal lobes (the vessels hug the brain)."""
    best = None
    for side in (1, -1):
        cx = BRAIN_C.x + side * BRAIN_R[0] * 0.5
        rx = BRAIN_R[0] * 0.52
        q = 1 - ((x - cx) / rx) ** 2 - ((y - BRAIN_C.y) / BRAIN_R[1]) ** 2
        if q > 0:
            z = BRAIN_C.z - BRAIN_R[2] * math.sqrt(q)
            best = z if best is None else min(best, z)
    return (best if best is not None else BRAIN_C.z) - gap


def _branch(rng, start, direction, length, n=6, bend=0.35, lift=None):
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    pts = [np.asarray(start, float)]
    for _ in range(n):
        d = d + rng.normal(0, bend, 3) * np.array([1, 1, 0.4])
        d /= np.linalg.norm(d)
        p = pts[-1] + d * length / n
        if lift is not None:
            p[2] = lift(p[0], p[1])
        pts.append(p)
    return np.array(pts)


def network(seed=7):
    """[(points, radius, level)] for the whole network."""
    rng = np.random.default_rng(seed)
    out = []
    for side in (1, -1):
        # level 0: palatine artery along the palate, back to front, just inside the gum ridge
        th = np.linspace(math.radians(125), math.radians(8), 16)
        art = []
        for t in th:
            x = 0.62 * MS.ARCH_A * (1.0 if t > math.pi / 2 else math.sin(t))
            y = MS.ARCH_C - 0.68 * MS.ARCH_B * math.cos(min(t, math.pi / 2)) + max(0.0, t - math.pi / 2) * 0.03
            art.append((side * x, y, _in_palate(side * x, y)))
        art = _wiggle(art, rng, 0.0011, 48)
        art[:, 2] = [_in_palate(p[0], p[1]) for p in art]
        out.append((art, 0.00055, 0))
        # level 1: branches wander across the palate toward the midline
        for k in np.linspace(4, 36, 7).astype(int):
            p = art[k]
            dirn = np.array([-side * 1.0, rng.uniform(-0.9, 0.9), 0.0])
            br = _branch(rng, p, dirn, rng.uniform(0.008, 0.014), n=8, bend=0.5, lift=_in_palate)
            out.append((_wiggle(br, rng, 0.0005, 20), 0.00034, 1))
            # level 2: twigs off each branch
            for j in (2, 4, 6):
                tw = _branch(rng, br[j], np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0]), rng.uniform(0.003, 0.007),
                             n=6, bend=0.6, lift=_in_palate)
                out.append((_wiggle(tw, rng, 0.0003, 12), 0.0002, 2))
        # level 1: trunk climbing from the back of the palate, converging on the midline and
        # rising into the gap between the frontal lobes
        base = art[0] + np.array([0.0, 0.0, 0.0006])                 # leaves the back of the palatine artery
        trunk = np.array([base, base + [side * 0.001, -0.002, 0.012], [side * 0.006, -0.004, 0.034],
                          [side * 0.0035, -0.012, 0.056], [side * 0.0016, -0.02, 0.074], [side * 0.0012, -0.03, 0.098]])
        trunk = _wiggle(K.path_spline(trunk, 40), rng, 0.0006, 48)
        out.append((trunk, 0.0011, 1))
        # level 2-3: branches leave the trunk and spread over the underside of the frontal lobe
        for k, a in ((20, -20), (24, 25), (28, -55), (32, 60), (36, 5)):
            p = trunk[k]
            ang = math.radians(a)
            dirn = np.array([side * math.cos(ang), math.sin(ang), 0.0])
            br = _branch(rng, p, dirn, rng.uniform(0.02, 0.032), n=10, bend=0.22, lift=_on_brain)
            br[0] = p
            br = _wiggle(br, rng, 0.0007, 30)
            br[1:, 2] = [min(_on_brain(q[0], q[1]), q[2] + 0.004) for q in br[1:]]
            out.append((br, 0.0006, 2))
            for j in (9, 15, 22):
                tw = _branch(rng, br[j], np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]),
                             rng.uniform(0.006, 0.012), n=6, bend=0.45, lift=_on_brain)
                out.append((_wiggle(tw, rng, 0.0004, 12), 0.0003, 3))
    return out


def vessel_material(name="Vessel"):
    """Wet red artery with controls: Glow (red emission), Cold (0..1: shrinks to dim blue)."""
    m = V.principled(name, H("#A8101C"), rough=0.3, sss=0.35, sss_radius=(1.0, 0.25, 0.2), sss_scale=0.002,
                     spec=0.5, coat=0.5)
    nt = m.node_tree
    b = V.bsdf(m)
    cold = MS._value(nt, "Cold", 0.0)
    glow = MS._value(nt, "Glow", 0.0)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*H("#A8101C"), 1)
    mix.inputs[7].default_value = (*H("#3A4F9A"), 1)
    nt.links.new(cold, mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    emix = nt.nodes.new("ShaderNodeMix")
    emix.data_type = "RGBA"
    emix.inputs[6].default_value = (*H("#FF1A12"), 1)
    emix.inputs[7].default_value = (*H("#4A78FF"), 1)
    nt.links.new(cold, emix.inputs[0])
    nt.links.new(emix.outputs[2], V._inp(b, "Emission Color", "Emission"))
    nt.links.new(glow, V._inp(b, "Emission Strength"))
    V.bump(m, scale=1500, strength=0.15, distance=0.0001)
    # Clear (0..1): walls turn partly see-through so the trapped warm sparks show inside
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*H("#9DB4FF"), 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(MS._math(nt, "MULTIPLY", MS._value(nt, "Clear", 0.0), 0.65), mx.inputs[0])
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    # Pulse (0..1+) / PulseS: a glowing wave that runs along every vessel (curve U = length)
    uv = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    band = MS._band(nt, sep.outputs["X"], MS._value(nt, "Pulse", -1.0), 0.07)
    pe = nt.nodes.new("ShaderNodeEmission")
    pe.inputs["Color"].default_value = (*H("#FF3214"), 1)
    nt.links.new(MS._math(nt, "MULTIPLY", band, MS._value(nt, "PulseS", 0.0)), pe.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mx.outputs[0], add.inputs[0])
    nt.links.new(pe.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def path_point(pts, t):
    """Point at fraction t of a polyline's length."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    s = t * L[-1]
    return np.array([np.interp(s, L, pts[:, k]) for k in range(3)])


def sparks(paths, count=24, radius=0.0002, seed=5, col=None, start=1, end=60, drift=0.08):
    """Warm orange glowing sparks inside the vessels (trapped heat), drifting slowly along
    their path. paths: list of polylines."""
    col = col or V.collection("SPARKS")
    rng = np.random.default_rng(seed)
    mat = V.emission("Spark_Warm", H("#FF7A1E"), 6.0)
    obs = []
    for i in range(count):
        pts = paths[i % len(paths)]
        t0 = rng.uniform(0.08, 0.85)
        s = K.ellipsoid(f"Spark_{i:02d}", (0, 0, 0), (radius,) * 3, segments=12, col=col)
        V.assign(s, mat)
        keys = [(start, tuple(path_point(pts, t0))), (end, tuple(path_point(pts, min(t0 + drift, 0.98))))]
        V.key(s, "location", keys, "LINEAR")
        obs.append(s)
    return obs


def build(col_name="VESSELS", seed=7, mat=None):
    """One curve object per generation. Returns {"levels": [obj...], "paths": [...], "mat": mat}."""
    col = V.collection(col_name)
    mat = mat or vessel_material()
    paths = network(seed)
    levels = []
    for lev in range(4):
        cu = bpy.data.curves.new(f"Vessels_L{lev}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_resolution = 4
        cu.resolution_u = 6
        cu.use_fill_caps = True
        base = max([r for _, r, lv in paths if lv == lev] or [0.0005])
        cu.bevel_depth = base
        for pts, r, lv in paths:
            if lv != lev:
                continue
            sp = cu.splines.new("NURBS")
            sp.points.add(len(pts) - 1)
            for i, p in enumerate(pts):
                t = i / (len(pts) - 1)
                sp.points[i].co = (*p, 1.0)
                sp.points[i].radius = (r / base) * (1.0 - 0.45 * t)
            sp.order_u = 4
            sp.use_endpoint_u = True
        cu.bevel_factor_mapping_end = "SPLINE"
        ob = V.link(bpy.data.objects.new(f"Vessels_L{lev}", cu), col)
        V.assign(ob, mat)
        levels.append(ob)
    return {"col": col, "levels": levels, "paths": paths, "mat": mat}


def grow(levels, spans):
    """spans: [(start, end), ...] per level - each generation draws on in turn."""
    for ob, (s, e) in zip(levels, spans):
        cu = ob.data
        cu.bevel_factor_end = 0.0
        cu.keyframe_insert("bevel_factor_end", frame=s)
        cu.bevel_factor_end = 1.0
        cu.keyframe_insert("bevel_factor_end", frame=e)
        V.ease_id(cu, "SINE", "EASE_IN_OUT", "bevel_factor_end")


def thickness(levels, keys, interp="BEZIER", easing="EASE_IN_OUT"):
    """Scale every generation's radius: keys = [(frame, factor), ...]."""
    for ob in levels:
        cu = ob.data
        base = cu.bevel_depth
        V.key(cu, "bevel_depth", [(f, base * k) for f, k in keys], interp, easing)


def brain_underside(col=None, mat=None):
    """Stylised frontal brain seen from below in x-ray: two hemispheres with meandering
    sulci (grooves along noise zero-crossings)."""
    col = col or V.collection("BRAIN")
    halves = []
    for side in (1, -1):
        c = (BRAIN_C.x + side * BRAIN_R[0] * 0.5, BRAIN_C.y, BRAIN_C.z)
        h = K.ellipsoid(f"Brain_{'L' if side > 0 else 'R'}", c, (BRAIN_R[0] * 0.52, BRAIN_R[1], BRAIN_R[2]),
                        segments=96, col=col)
        halves.append(h)
    brain = K.join(halves, "Brain_Xray_geo", col)
    K.voxel_remesh(brain, 0.0012)
    P = K.co(brain)
    n1 = K.fbm(P, 0.011, octaves=2, seed=3)                       # about [-1, 1]
    sulci = np.exp(-(n1 / 0.09) ** 2)
    K.displace(brain, -0.0045 * sulci)
    K.smooth(brain, iterations=2, factor=0.4)
    if mat is None:
        mat = V.principled("Brain_Pink", H("#E27386"), rough=0.4, sss=0.5, sss_radius=(1.0, 0.4, 0.35),
                           sss_scale=0.004, coat=0.2, emission=H("#FF6F8A"), emission_strength=0.3)
    V.assign(brain, mat)
    return brain
