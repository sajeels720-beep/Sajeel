"""Inside his fingertip (shots 07-08), on the warm tissue backdrop of videos 1 and 2.

A yellow nerve comes down from a nerve ending just under the skin (a spray of fine twigs with
round tips) to a web of red blood vessels, where it splits into fine fibres that wind around
the main vessel. Shot 07: drops of water reach the ending, it sparks, and a bright pulse races
down the nerve. Shot 08: the pulse reaches the vessels, the fibres around them light up, and
the vessels squeeze narrow while the red blood cells inside slow to a trickle.

Stylised large scale in metres (the main vessel is 0.12 m thick, like the artery in video 1's
nerve close-up) so depth of field behaves like a normal macro shot. The camera looks along +Y.
"""
import math

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

import body_set as BS
import claude_sculpt_kit as K
import sky_set as SKY
import vessel_tunnel as VT
import vfx_kit as V

H = V.hex_lin
NERVE = H("#F2A400")
SIGNAL = H("#FFF3C4")              # the pulse: white-hot yellow, like shot 05's
WATER = H("#9FE6FF")

ENDING = np.array([1.55, 0.85, 3.25])            # the nerve ending, up near the skin
JOIN = np.array([0.42, -0.16, 0.36])             # where the nerve reaches the main vessel
NERVE_CTRL = [ENDING, (1.5, 0.72, 2.6), (1.18, 0.45, 1.9), (0.95, 0.12, 1.25), (0.62, -0.1, 0.72), JOIN]
VESSEL_CTRL = [(-2.6, 0.32, -1.1), (-1.3, 0.16, -0.6), (-0.25, 0.04, -0.06), (0.75, 0.12, 0.3), (1.8, 0.04, 0.78),
               (2.8, 0.22, 1.1)]
R_MAIN, R_BRANCH, R_CAP = 0.12, 0.07, 0.032


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def world():
    """The tissue backdrop and its lights are added per shot (they depend on the camera)."""
    return SKY.tissue(turn=40.0, scale=2.0)


# --------------------------------------------------------------------------
# Paths and frames
# --------------------------------------------------------------------------
def frames_along(P):
    """Tangent, normal and binormal along a polyline (parallel transport: no flips)."""
    P = np.asarray(P, float)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    A = np.zeros_like(P)
    a = np.cross(T[0], [0.3, 0.1, 1.0])
    A[0] = a / np.linalg.norm(a)
    for i in range(1, len(P)):
        a = A[i - 1] - A[i - 1].dot(T[i]) * T[i]
        A[i] = a / np.linalg.norm(a)
    B = np.cross(T, A)
    return T, A, B


def lengths(P):
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.asarray(P, float), axis=0), axis=1))])


def point_at(P, L, u):
    """Point at fraction u (0..1) of a polyline's length."""
    s = min(max(u, 0.0), 1.0) * L[-1]
    return np.array([np.interp(s, L, P[:, k]) for k in range(3)])


def nerve_path(n=180):
    return K.path_spline(np.array(NERVE_CTRL, float), n)


def vessel_paths(seed=7):
    """[(points, radius, level)]: the main vessel, its branches and capillary twigs."""
    rng = np.random.default_rng(seed)
    main = K.path_spline(np.array(VESSEL_CTRL, float), 160)
    out = [(main, R_MAIN, 0)]
    Lm = lengths(main)

    def walk(start, d, length, n, bend, depth_bias=0.0):
        d = np.asarray(d, float) / np.linalg.norm(d)
        pts = [np.asarray(start, float)]
        for _ in range(n):
            d = d + rng.normal(0, bend, 3) * np.array([1.0, 0.5, 1.0]) + np.array([0, depth_bias, 0])
            d /= np.linalg.norm(d)
            pts.append(pts[-1] + d * length / n)
        return K.path_spline(np.array(pts), 60)

    for u, d, ln in ((0.22, (-0.35, 0.25, -1.0), 1.7), (0.4, (0.25, 0.35, 1.0), 1.5), (0.62, (0.55, 0.1, -1.0), 1.8),
                     (0.8, (-0.2, 0.45, 1.0), 1.4)):
        br = walk(point_at(main, Lm, u), d, ln, 7, 0.32, 0.04)
        out.append((br, R_BRANCH, 1))
        Lb = lengths(br)
        for v in (0.35, 0.7):
            tw = walk(point_at(br, Lb, v), rng.normal(0, 1, 3) * np.array([1, 0.4, 1]), rng.uniform(0.6, 1.0), 6, 0.5, 0.05)
            out.append((tw, R_CAP, 2))
    return out


# --------------------------------------------------------------------------
# The nerve
# --------------------------------------------------------------------------
def nerve_material(name="Nerve_Yellow_SSS"):
    """Glossy yellow nerve (as in video 1), glowing a little from inside."""
    m = V.principled(name, NERVE, rough=0.35, sss=0.15, sss_radius=(1.0, 0.8, 0.5), sss_scale=0.03,
                     spec=0.4, coat=0.15, emission=H("#FFA000"), emission_strength=1.6)   # golden yellow in the red light
    V.bump(m, scale=40.0, strength=0.2, distance=0.004)
    return m


def head_glow(mat, head, ahead=0.07, tail=0.4, strength=0.0):
    """Light a material up around an empty riding the pulse (its local +Y = the way it goes):
    a short bright front and a long fading tail, like a comet. Returns the strength value."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    current = out.inputs["Surface"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.object = head
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    m = lambda op, a, b=None: SKY._math(nt, op, a, b)
    y = sep.outputs["Y"]
    side = m("ADD", m("MULTIPLY", sep.outputs["X"], sep.outputs["X"]), m("MULTIPLY", sep.outputs["Z"], sep.outputs["Z"]))
    reach = m("ADD", m("MULTIPLY", m("GREATER_THAN", y, 0.0), ahead - tail), tail)     # ahead: short, behind: long
    k = m("EXPONENT", m("MULTIPLY", m("ADD", m("POWER", m("DIVIDE", y, reach), 2.0), m("DIVIDE", side, 0.012)), -1.0))
    val = nt.nodes.new("ShaderNodeValue")
    val.name = val.label = "Glow"
    val.outputs[0].default_value = strength
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*SIGNAL, 1)
    nt.links.new(m("MULTIPLY", k, val.outputs[0]), em.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(current, add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return val.outputs[0]


def bundle(name, P, mat, col, fibres=5, twist=1.3, spread=0.032, radius=0.017, seed=1, taper=None):
    """A twisted bundle of fibres along the centre line P: one curve, one spline per fibre."""
    rng = np.random.default_rng(seed)
    P = np.asarray(P, float)
    T, A, B = frames_along(P)
    s = lengths(P) / lengths(P)[-1]
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = radius, 4, 2
    cu.use_fill_caps = True
    for k in range(fibres):
        ph = 2 * math.pi * k / fibres + rng.uniform(-0.3, 0.3)
        r = spread * rng.uniform(0.8, 1.15)
        ang = ph + twist * 2 * math.pi * s
        pts = P + (np.cos(ang)[:, None] * A + np.sin(ang)[:, None] * B) * r
        sp = cu.splines.new("NURBS")
        sp.points.add(len(pts) - 1)
        w = rng.uniform(0.8, 1.15)
        for i, p in enumerate(pts):
            sp.points[i].co = (*p, 1.0)
            sp.points[i].radius = w * (1.0 if taper is None else 1.0 + (taper - 1.0) * s[i])
        sp.order_u, sp.use_endpoint_u = 4, True
    ob = V.link(bpy.data.objects.new(name, cu), col)
    V.assign(ob, mat)
    return ob


def ending(P, mat, col, twigs=6, seed=3):
    """The nerve ending: the fibres fan out into fine twigs, each with a round tip.
    Returns (twig curves object, [tip positions])."""
    rng = np.random.default_rng(seed)
    P = np.asarray(P, float)
    T, A, B = frames_along(P)
    base, back = P[0], -T[0]                                 # the nerve runs away from the ending
    cu = bpy.data.curves.new("Nerve_Ending", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = 0.011, 3, 3
    cu.use_fill_caps = True
    tips = []
    for k in range(twigs):
        a = 2 * math.pi * k / twigs + rng.uniform(-0.25, 0.25)
        out = back * 0.85 + (A[0] * math.cos(a) + B[0] * math.sin(a)) * rng.uniform(0.55, 0.9)
        out /= np.linalg.norm(out)
        ln = rng.uniform(0.3, 0.48)
        mid = base + out * ln * 0.5 + rng.normal(0, 0.04, 3)
        tip = base + out * ln
        pts = K.path_spline(np.array([base + back * -0.04, mid, tip]), 16)
        sp = cu.splines.new("NURBS")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*p, 1.0)
            sp.points[i].radius = 1.4 - 0.7 * i / (len(pts) - 1)
        sp.order_u, sp.use_endpoint_u = 4, True
        tips.append(Vector(tip))
    ob = V.link(bpy.data.objects.new("Nerve_Ending", cu), col)
    V.assign(ob, mat)
    bulbs = []
    for i, t in enumerate(tips):
        b = K.ellipsoid(f"Nerve_Bulb_{i}", t, (0.034,) * 3, segments=20, col=col)
        V.assign(b, mat)
        bulbs.append(b)
    return ob, tips, bulbs


def build_nerve(col=None):
    """The nerve and its ending. Returns dict(path, lengths, bundle, ending, tips, bulbs, mat, head)."""
    col = col or V.collection("NERVE")
    P = nerve_path()
    mat = nerve_material()
    head = V.link(bpy.data.objects.new("Pulse_Head", None), col)
    head.location = tuple(P[0])
    glow = head_glow(mat, head)
    bun = bundle("Nerve", P, mat, col)
    end, tips, bulbs = ending(P, mat, col)
    return {"path": P, "lengths": lengths(P), "bundle": bun, "ending": end, "tips": tips, "bulbs": bulbs, "mat": mat,
            "head": head, "glow": glow}


def pulse_track(nv, start, end, ease=0.25):
    """A bright pulse races down the nerve from the ending (frame `start`) to the vessels
    (`end`), speeding up over the first `ease` of the way: the "Pulse_Head" empty rides with
    it, pointing the way it goes, and the nerve glows around it (head_glow). Returns u(frame):
    how far along the nerve the head is (0..1)."""
    P, L = nv["path"], nv["lengths"]
    T, _, _ = frames_along(P)

    def u(f):
        t = min(max((f - start) / (end - start), 0.0), 1.0)
        return (t * t / (2 * ease) if t < ease else ease / 2 + (t - ease)) / (1 - ease / 2)

    head = nv["head"]
    head.rotation_mode = "QUATERNION"
    scene = bpy.context.scene
    for f in range(scene.frame_start - 1, scene.frame_end + 2):
        h = u(f)
        head.location = tuple(point_at(P, L, h))
        j = min(int(round(h * (len(P) - 1))), len(P) - 1)
        head.rotation_quaternion = Vector(T[j]).to_track_quat("Y", "Z")
        head.keyframe_insert("location", frame=f)
        head.keyframe_insert("rotation_quaternion", frame=f)
    V.ease_id(head, "LINEAR")
    return u


def sparks(points, start, end, count=16, reach=0.15, seed=2, col=None):
    """Electric sparks crackling between and around the nerve's tips."""
    import nerve_set as NS
    rng = np.random.default_rng(seed)
    col = col or V.collection("SPARKS")
    core = V.emission("Spark_Core_Y", H("#FFF6D8"), 30.0)
    gold = V.emission("Spark_Gold", H("#FFD04A"), 16.0)
    obs = []
    pts = [np.asarray(p, float) for p in points]
    for i in range(count):
        f = int(rng.uniform(start, end - 1))
        a = pts[int(rng.integers(0, len(pts)))]
        b = pts[int(rng.integers(0, len(pts)))] if rng.random() < 0.5 else a + rng.normal(0, 1, 3) * reach
        if np.linalg.norm(b - a) < 0.02:
            b = a + rng.normal(0, 1, 3) * reach
        ob = NS.lightning(f"Spark_{i:02d}", a, b, rng, col, core if rng.random() < 0.7 else gold,
                          segments=14, jitter=0.012 + 0.012 * rng.random(), radius=0.0014 + 0.0012 * rng.random())
        V.visible(ob, [(1, False), (f, True), (f + int(rng.integers(2, 4)), False)])
        obs.append(ob)
    return obs


def water_beads(targets, start, travel=5, col=None, seed=4):
    """Drops of water arrive down the sweat duct and touch the nerve's tips (where it sparks):
    small clear-blue glowing beads drifting in, gone on contact."""
    rng = np.random.default_rng(seed)
    col = col or V.collection("FX")
    mat = V.principled("Water_Bead", H("#CFF1FF"), rough=0.05, spec=0.8, transmission=0.4, ior=1.33,
                       emission=WATER, emission_strength=3.0)
    obs = []
    for i, t in enumerate(targets):
        f0 = start + i % 3
        come = Vector(rng.normal(0, 1, 3)).normalized() * 0.12 + Vector((0, 0, 0.42))
        b = K.ellipsoid(f"Water_Bead_{i}", (0, 0, 0), (0.036,) * 3, segments=16, col=col)     # moved by its keys
        V.assign(b, mat)
        V.key(b, "location", [(f0 - 1, tuple(Vector(t) + come)), (f0 + travel, tuple(Vector(t) + come * 0.12))], "LINEAR")
        V.key(b, "scale", [(f0 - 1, (0.001,) * 3), (f0, (1.0,) * 3), (f0 + travel, (1.0,) * 3), (f0 + travel + 2, (0.001,) * 3)])
        obs.append(b)
    return obs


# --------------------------------------------------------------------------
# The vessels and the blood
# --------------------------------------------------------------------------
def vessel_material(name="Vessel_Clear"):
    """Wet red vessel wall, partly see-through so the blood cells show inside."""
    m = V.principled(name, H("#B0121E"), rough=0.3, sss=0.4, sss_radius=(1.0, 0.25, 0.2), sss_scale=0.05,
                     spec=0.5, coat=0.5, emission=H("#FF2414"), emission_strength=0.08)
    V.bump(m, scale=30.0, strength=0.15, distance=0.004)
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    current = out.inputs["Surface"].links[0].from_socket
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    clear = SKY._math(nt, "MULTIPLY", SKY._math(nt, "SUBTRACT", 1.0, lw.outputs["Facing"]), 0.8)    # clearest face-on
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*H("#FF9A90"), 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(clear, mix.inputs[0])
    nt.links.new(current, mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    for prop, val in (("surface_render_method", "DITHERED"), ("use_transparent_shadow", True)):
        if hasattr(m, prop):
            setattr(m, prop, val)
    return m


def build_vessels(col=None, seed=7):
    """One curve object per level (so each level squeezes by its own amount). Returns
    dict(paths, levels, mat)."""
    col = col or V.collection("VESSELS")
    mat = vessel_material()
    paths = vessel_paths(seed)
    levels = []
    for lev, base in enumerate((R_MAIN, R_BRANCH, R_CAP)):
        cu = bpy.data.curves.new(f"Vessels_L{lev}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = base, 6, 3
        cu.use_fill_caps = True
        for pts, r, lv in paths:
            if lv != lev:
                continue
            sp = cu.splines.new("NURBS")
            sp.points.add(len(pts) - 1)
            for i, p in enumerate(pts):
                t = i / (len(pts) - 1)
                sp.points[i].co = (*p, 1.0)
                sp.points[i].radius = (1.0 - 0.35 * t) if lev else 1.0
            sp.order_u, sp.use_endpoint_u = 4, True
        ob = V.link(bpy.data.objects.new(f"Vessels_L{lev}", cu), col)
        V.assign(ob, mat)
        levels.append(ob)
    return {"paths": paths, "levels": levels, "mat": mat, "col": col}


def squeeze(ves, keys, extra=()):
    """keys = [(frame, factor)]: every vessel's thickness (capillaries squeeze a little less).
    extra: shape-keyed objects (the fibres around the vessel) whose "Squeeze" key follows."""
    for lev, ob in enumerate(ves["levels"]):
        cu = ob.data
        base = cu.bevel_depth
        soft = (1.0, 1.0, 0.85)[lev]
        V.key(cu, "bevel_depth", [(f, base * (1 - (1 - k) * soft)) for f, k in keys], "BEZIER", "EASE_IN_OUT")
    for ob in extra:
        kb = ob.data.shape_keys.key_blocks["Squeeze"]
        k_min = min(k for _, k in keys)
        for f, k in keys:
            kb.value = (1 - k) / (1 - k_min) if k_min < 1 else 0.0
            kb.keyframe_insert("value", frame=f)
        V.ease_id(ob.data.shape_keys, "BEZIER", "EASE_IN_OUT")


def wrap_fibres(ves, nv, squeezed=0.45, col=None, seed=5):
    """The nerve splits where it reaches the main vessel into fine fibres that wind around it
    (up and down the vessel) and follow two branches. Each is shape-keyed ("Squeeze") to hug
    the vessel when it squeezes. Returns the fibre objects (material: the nerve's)."""
    col = col or V.collection("NERVE")
    rng = np.random.default_rng(seed)
    main, _, _ = ves["paths"][0]
    Lm = lengths(main)
    s_join = np.argmin(np.linalg.norm(main - nv["path"][-1], axis=1)) / (len(main) - 1)
    T, A, B = frames_along(main)
    obs = []
    for k, (u0, u1, turns) in enumerate(((s_join, s_join - 0.15, 2.4), (s_join, s_join + 0.14, -2.2),
                                         (s_join, s_join - 0.1, -1.6), (s_join, s_join + 0.11, 1.7))):
        n = 90
        us = np.linspace(u0, u1, n)
        idx = np.clip((us * (len(main) - 1)).astype(int), 0, len(main) - 1)
        ph0 = rng.uniform(0, 2 * math.pi)
        ang = ph0 + turns * 2 * math.pi * np.linspace(0, 1, n)
        ring = np.cos(ang)[:, None] * A[idx] + np.sin(ang)[:, None] * B[idx]
        lead = np.clip(np.linspace(0, 1, n) / 0.12, 0, 1)[:, None]          # leaves the nerve's end smoothly
        start = nv["path"][-1]
        c = np.array([point_at(main, Lm, x) for x in us])
        rest = c + ring * (R_MAIN + 0.016)
        tight = c + ring * (R_MAIN * squeezed + 0.014)
        rest = start * (1 - lead) + rest * lead
        tight = start * (1 - lead) + tight * lead
        cu = bpy.data.curves.new(f"Nerve_Wrap_{k}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = 0.0075, 3, 2
        cu.use_fill_caps = True
        sp = cu.splines.new("NURBS")
        sp.points.add(n - 1)
        for i, p in enumerate(rest):
            sp.points[i].co = (*p, 1.0)
            sp.points[i].radius = 1.0 - 0.5 * i / (n - 1)
        sp.order_u, sp.use_endpoint_u = 4, True
        ob = V.link(bpy.data.objects.new(f"Nerve_Wrap_{k}", cu), col)
        ob.shape_key_add(name="Basis", from_mix=False)
        kb = ob.shape_key_add(name="Squeeze", from_mix=False)
        for i, p in enumerate(tight):
            kb.data[i].co = Vector(p)
        V.assign(ob, nv["mat"])
        obs.append(ob)
    return obs


def blood(ves, flow, thick, frames, col=None, seed=4, spacing=(0.13, 0.11)):
    """Red blood cells tumbling along the main vessel and its branches. flow(f): metres per
    frame; thick(f): the vessels' thickness factor (the cells stay inside as they squeeze)."""
    rng = np.random.default_rng(seed)
    col = col or V.collection("BLOOD")
    mesh = VT.rbc_mesh("RBC", radius=1.0, segments=28)
    mat = VT.cell_material()
    V._inp(V.bsdf(mat), "Emission Strength").default_value = 0.6       # they glow through the clear walls
    mesh.materials.append(mat)
    f0, f1 = frames
    travelled = {f0 - 1: 0.0}
    for f in range(f0, f1 + 2):
        travelled[f] = travelled[f - 1] + flow(f)
    obs = []
    for pi, (P, R, lev) in enumerate(ves["paths"]):
        if lev > 1:
            continue
        T, A, B = frames_along(P)
        L = lengths(P)
        rc = (0.04, 0.026)[lev]
        n = int(L[-1] / spacing[lev])
        for i in range(n):
            ob = V.link(bpy.data.objects.new(f"RBC_{pi}_{i:02d}", mesh), col)
            s0 = rng.uniform(0, L[-1])
            a, rr = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform(0, 1))
            rot0 = Euler(rng.uniform(0, 2 * math.pi, 3)).to_matrix()
            spin = rng.normal(0, 0.05, 3)
            for f in range(f0 - 1, f1 + 2):
                s = (s0 + travelled[f]) % L[-1]
                j = min(int(np.searchsorted(L, s)), len(P) - 1)
                taper = (1.0 - 0.35 * j / (len(P) - 1)) if lev else 1.0
                room = max(R * taper * thick(f) - rc * 0.9, 0.0) * 0.8
                c = point_at(P, L, s / L[-1]) + (A[j] * math.cos(a) + B[j] * math.sin(a)) * rr * room
                edge = min(s, L[-1] - s) / (0.07 * L[-1])                     # vanish at the ends (they wrap)
                sc = max(rc * min(1.0, edge) * min(1.0, 0.75 + 0.25 * thick(f)), 1e-4)
                ob.matrix_world = Matrix.Translation(Vector(c)) @ (Euler(spin * (f - f0)).to_matrix() @ rot0).to_4x4() \
                    @ Matrix.Scale(sc, 4)
                ob.keyframe_insert("location", frame=f)
                ob.keyframe_insert("rotation_euler", frame=f)
                ob.keyframe_insert("scale", frame=f)
            V.ease_id(ob, "LINEAR")
            obs.append(ob)
    return obs


def background(centre, away, col=None):
    """Out-of-focus vessels far behind the subject, so it sits inside living tissue."""
    mat = V.principled("Vessel_Far_Lit", H("#7A1019"), rough=0.35, sss=0.4, sss_radius=(1.0, 0.2, 0.15), sss_scale=0.05,
                       coat=0.4, emission=H("#5E0A10"), emission_strength=0.8)       # dark tubes read as cables
    return BS.background_vessels(col or V.collection("TISSUE"), centre, count=4, spread=(7.0, 3.0, 7.0),
                                 away=away, distance=(6.0, 10.0), mat=mat)
