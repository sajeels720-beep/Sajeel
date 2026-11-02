"""Her bloodshot eye (shots 15-16): tiny red vessels on the white of her eye that swell with the
pressure, then one bursts and a red blotch spreads across the white (a burst blood vessel,
as doctors see after a held-in sneeze). Built on her own eyeball: a sphere is fitted to it
and the iris direction found from the bulge of the cornea; the vessels lie on the white,
between the edge of the iris and the corners of her eye, and ride on her eye bone.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

import vfx_kit as V

H = V.hex_lin
LIMBUS = 21.0            # degrees from the eye's axis where the white begins (the edge of the iris; measured)


def eyeball(hero, side="R"):
    """Fit a sphere to one of her eyeballs on the current frame. Returns dict(centre,
    radius, axis (where the iris looks), across (towards the outer corner), up)."""
    eye = next(o for o in hero["parts"] if "high-poly" in o.name)
    dg = bpy.context.evaluated_depsgraph_get()
    me = eye.evaluated_get(dg).to_mesh()
    P = np.array([tuple(eye.matrix_world @ v.co) for v in me.vertices])
    P = P[P[:, 0] < 0] if side == "R" else P[P[:, 0] > 0]
    keep = np.ones(len(P), bool)
    for _ in range(3):                                            # least squares, then drop the cornea and refit
        A = np.c_[2 * P[keep], np.ones(keep.sum())]
        sol = np.linalg.lstsq(A, (P[keep] ** 2).sum(1), rcond=None)[0]
        c, r = sol[:3], math.sqrt(sol[3] + sol[:3] @ sol[:3])
        res = np.linalg.norm(P - c, axis=1) - r
        keep = res < 0.0004
    apex = P[np.argmax(np.linalg.norm(P - c, axis=1))]
    axis = Vector(apex - c).normalized()
    out = Vector((-1.0 if side == "R" else 1.0, 0.0, 0.0))
    across = (out - axis * out.dot(axis)).normalized()
    # the eye is two layers (eyeball, clear shell), neither quite a sphere: things go on the
    # outermost surface, found by casting in from outside
    from mathutils.bvhtree import BVHTree
    W = [eye.matrix_world @ v.co for v in me.vertices]
    sgn = -1.0 if side == "R" else 1.0
    polys = [tuple(p_.vertices) for p_ in me.polygons if all(W[i].x * sgn > 0 for i in p_.vertices)]
    bvh = BVHTree.FromPolygons(W, polys)
    return {"centre": Vector(c), "radius": r, "axis": axis, "across": across, "up": axis.cross(across).normalized()
            if side == "L" else across.cross(axis).normalized(), "side": side, "bvh": bvh}


def direction(e, polar, theta):
    """Unit direction from the eye's centre: polar = degrees from the axis, theta = degrees
    round it (0 = towards the outer corner, 90 = up)."""
    p, t = math.radians(polar), math.radians(theta)
    return (e["axis"] * math.cos(p) + (e["across"] * math.cos(t) + e["up"] * math.sin(t)) * math.sin(p)).normalized()


def surface(e, d, lift=0.00015):
    """The outermost point of the eye in direction d (from its centre), lifted a hair."""
    d = Vector(d).normalized()
    hit = e["bvh"].ray_cast(e["centre"] + d * 0.04, -d, 0.05)
    p = hit[0] if hit[0] is not None else e["centre"] + d * e["radius"] * 1.08
    return p + d * lift


def on_eye(e, polar, theta, lift=0.00015):
    """A point on the surface of the eye (see direction())."""
    return surface(e, direction(e, polar, theta), lift)


def white_window(e, hero, cam, step=10):
    """How far out (degrees from the axis) her white is in view from `cam`, round the eye:
    {theta: polar}, found by casting rays from the camera past her eyelids."""
    import airways as AW
    body = AW._body_bvh(hero)
    out = {}
    for theta in range(0, 360, step):
        lo, hi = LIMBUS, 80.0
        for _ in range(12):                                       # the last polar angle still in view
            mid = (lo + hi) / 2
            p = on_eye(e, mid, theta, 0.0)
            d = p - Vector(cam)
            hit = body.ray_cast(Vector(cam), d.normalized(), d.length)
            if hit[0] is None or (hit[0] - Vector(cam)).length > d.length - 0.0004:
                lo = mid
            else:
                hi = mid
        out[theta] = lo
    return out


def _walk(e, rng, polar, theta, steps, dpolar, wiggle):
    """A wandering vessel across the white: starts near a corner, works in towards the iris."""
    pts = []
    for _ in range(steps):
        pts.append((polar, theta))
        polar = max(LIMBUS + 1.5, polar + dpolar + rng.normal(0, 1.2))
        theta += rng.normal(0, wiggle)
    return pts


def vessels(e, col, rng, window, count=20, name="Eye_Vessel"):
    """Red vessels on the white of the eye, mostly coming in from the corners, branching:
    each comes out from under her eyelid (window: white_window()) and runs in towards the
    iris. Each is a curve whose bevel (thickness) can be keyed. Returns the curve objects."""
    mat = V.principled(name, H("#9C0F1C"), rough=0.35, spec=0.4, emission=H("#E0202C"), emission_strength=0.0)
    mat.node_tree.nodes["Principled BSDF"].name = "Vessel_BSDF"
    obs = []
    for k in range(count):
        corner = (0.0, 180.0, 0.0, 180.0, 90.0, 270.0)[k % 6]    # mostly from the corners, a few from above/below
        theta = (corner + rng.normal(0, 24)) % 360
        edge = window[min(window, key=lambda t: min(abs(t - theta), 360 - abs(t - theta)))]
        if edge < LIMBUS + 6:
            continue
        start = edge + 3.0                                        # from just under the eyelid
        steps = int(rng.integers(7, 11))
        main = _walk(e, rng, start, theta, steps, -(start - LIMBUS - 2.0) / steps, 3.0)
        paths = [main]
        for _ in range(int(rng.integers(1, 3))):                  # a branch or two
            j = int(rng.integers(2, len(main) - 3))
            p0, t0 = main[j]
            paths.append(_walk(e, rng, p0, t0, int(rng.integers(3, 6)), -1.2, 6.0))
        for i, path in enumerate(paths):
            cu = bpy.data.curves.new(f"{name}_{k:02d}_{i}", "CURVE")
            cu.dimensions = "3D"
            cu.bevel_depth = 1.0
            cu.bevel_resolution = 2
            cu.use_fill_caps = True
            sp = cu.splines.new("NURBS")
            sp.points.add(len(path) - 1)
            for n, (pl, th) in enumerate(path):
                sp.points[n].co = (*on_eye(e, pl, th), 1.0)
                sp.points[n].radius = 1.0 - 0.55 * n / (len(path) - 1)   # thinning towards the iris
            sp.order_u, sp.use_endpoint_u = min(4, len(path)), True
            ob = V.link(bpy.data.objects.new(cu.name, cu), col)
            V.assign(ob, mat)
            ob["width"] = float(rng.uniform(0.6, 1.0)) * (1.0 if i == 0 else 0.7)
            obs.append(ob)
    return obs, mat


def key_swell(vessel_obs, mat, keys, base=0.00011):
    """keys = [(frame, swell 0..1)]: the vessels thicken and glow redder."""
    em = V._inp(mat.node_tree.nodes["Vessel_BSDF"], "Emission Strength")
    for f, s in keys:
        for ob in vessel_obs:
            ob.data.bevel_depth = base * ob["width"] * (1.0 + 1.3 * s)
            ob.data.keyframe_insert("bevel_depth", frame=f)
        em.default_value = 0.6 * s
        em.keyframe_insert("default_value", frame=f)
    for ob in vessel_obs:
        V.ease_id(ob.data)
    V.ease_id(mat.node_tree)


def blotch(e, col, at=(30.0, 8.0), reach=40.0, name="Eye_Blotch"):
    """A burst vessel's blood under the white of the eye: a thin red layer on the eyeball
    round `at` (polar, theta degrees), spreading out to `reach` degrees as its material value
    "Spread" (0..1) rises. It stops at the edge of the iris. Returns (object, material)."""
    rings, segs = 40, 96
    c = direction(e, *at)
    t1 = c.orthogonal().normalized()
    t2 = c.cross(t1)
    verts = [surface(e, c, 0.0001)]
    for i in range(1, rings + 1):
        a = math.radians(reach * i / rings)
        for k in range(segs):
            b = 2 * math.pi * k / segs
            d = c * math.cos(a) + (t1 * math.cos(b) + t2 * math.sin(b)) * math.sin(a)
            verts.append(surface(e, d, 0.0001))
    faces = [(0, 1 + k, 1 + (k + 1) % segs) for k in range(segs)]
    for i in range(rings - 1):
        r0, r1 = 1 + i * segs, 1 + (i + 1) * segs
        faces += [(r0 + k, r1 + k, r1 + (k + 1) % segs, r0 + (k + 1) % segs) for k in range(segs)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    # per point: angle from the burst point (0..1 of reach) and from the eye's axis (degrees)
    P = np.array([tuple(v - e["centre"]) for v in verts])
    P /= np.linalg.norm(P, axis=1)[:, None]
    from_burst = np.degrees(np.arccos(np.clip(P @ np.asarray(c), -1, 1))) / reach
    from_axis = np.degrees(np.arccos(np.clip(P @ np.asarray(e["axis"]), -1, 1)))
    for nm, arr in (("burst", from_burst), ("polar", from_axis)):
        at_ = me.attributes.new(nm, "FLOAT", "POINT")
        at_.data.foreach_set("value", arr.astype(np.float32))
    ob = V.link(bpy.data.objects.new(name, me), col)
    ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    m = V.principled(name, H("#B3101C"), rough=0.3, sss=0.2, sss_radius=(1, 0.2, 0.15), sss_scale=0.001, spec=0.5)
    nt = m.node_tree
    b = V.bsdf(m)

    def node(kind, **kw):
        n = nt.nodes.new(kind)
        for k_, v in kw.items():
            setattr(n, k_, v)
        return n

    burst, polar = node("ShaderNodeAttribute", attribute_name="burst"), node("ShaderNodeAttribute", attribute_name="polar")
    spread = nt.nodes.new("ShaderNodeValue")
    spread.name = spread.label = "Spread"
    spread.outputs[0].default_value = 0.0
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 900.0
    nz.inputs["Detail"].default_value = 3.0

    def math_(op, a, b=None):
        mm = nt.nodes.new("ShaderNodeMath")
        mm.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                mm.inputs[i].default_value = v
            else:
                nt.links.new(v, mm.inputs[i])
        return mm.outputs[0]

    ragged = math_("ADD", burst.outputs["Fac"], math_("MULTIPLY", math_("SUBTRACT", nz.outputs["Fac"], 0.5), 0.35))
    inside = math_("SUBTRACT", spread.outputs[0], ragged)                      # > 0 inside the blotch
    edge = nt.nodes.new("ShaderNodeMapRange")
    edge.interpolation_type = "SMOOTHSTEP"
    edge.inputs["From Min"].default_value, edge.inputs["From Max"].default_value = -0.02, 0.06
    nt.links.new(inside, edge.inputs["Value"])
    white = nt.nodes.new("ShaderNodeMapRange")                                  # only on the white
    white.interpolation_type = "SMOOTHSTEP"
    white.inputs["From Min"].default_value, white.inputs["From Max"].default_value = LIMBUS, LIMBUS + 4
    nt.links.new(polar.outputs["Fac"], white.inputs["Value"])
    alpha = math_("MULTIPLY", math_("MULTIPLY", edge.outputs["Result"], white.outputs["Result"]), 0.92)
    nt.links.new(alpha, V._inp(b, "Alpha"))
    deep = nt.nodes.new("ShaderNodeMix")                                        # darker where the blood is thick
    deep.data_type = "RGBA"
    deep.inputs[6].default_value = (*H("#D0222C"), 1)
    deep.inputs[7].default_value = (*H("#8A0A14"), 1)
    nt.links.new(math_("MINIMUM", math_("MULTIPLY", inside, 2.5), 1.0), deep.inputs[0])
    nt.links.new(deep.outputs[2], b.inputs["Base Color"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "DITHERED"
    elif hasattr(m, "blend_method"):
        m.blend_method = "HASHED"
    V.assign(ob, m)
    return ob, m


def ride_on_eye(hero, side, objs, col):
    """Hang objects (built in world space on the current frame) from her eye bone."""
    rig = hero["rig"]
    root = V.link(bpy.data.objects.new(f"Eye_{side}_root", None), col)
    root.parent, root.parent_type, root.parent_bone = rig, "BONE", f"eye.{side}"
    bpy.context.view_layer.update()
    root.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for o in objs:
        M = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = M
    return root


def close_up(shot, swell, cams, lens=120, seed=1515, fps=30, preview=False):
    """Shots 15 and 16, one continuous close-up: her take for `shot`, her right eye with the
    same vessels in both shots (the same seed, and the eyelid window seen from the same
    place), the camera (cams(rig, aim, look, n) keys it), backdrop and lights."""
    import hold_in as HOLD
    import sky_set as SKY
    lo, hi = HOLD.SHOTS[shot]
    n = hi - lo + 1
    V.setup_shot(n / fps, fps=fps, engine="CYCLES" if preview else "EEVEE", samples=24 if preview else 64,
                 scale=50 if preview else 100)
    take = HOLD.perform(shot)
    hero = take["hero"]
    bpy.context.scene.frame_set(1)
    e = eyeball(hero, "R")
    r = V.camera_rig(f"Cam_Shot{shot}", lens=lens, fstop=11)
    aim = e["centre"] + e["axis"] * e["radius"] * 0.9 + e["across"] * 0.002
    look = (e["axis"] + e["across"] * 0.32 + e["up"] * 0.06).normalized()   # from a little to her right
    cams(r, aim, look, n)
    col = V.collection("FX")
    window = white_window(e, hero, aim + look * 0.24)
    vs, vmat = vessels(e, col, np.random.default_rng(seed), window)
    key_swell(vs, vmat, swell)
    if preview:
        V.fast_preview(samples=24)
    V.handheld(r, amount=0.0002, aim_amount=0.00015)
    bpy.context.scene.frame_set(1)
    c0 = r["rig"].matrix_world.translation.copy()
    SKY.studio(c0, aim, lens)
    SKY.lights(aim, c0, SKY.view_dir(c0, aim, lens), scale=0.3)
    V.compositor(glow=0.3, threshold=1.0, dispersion=0.006)
    return {"take": take, "hero": hero, "eye": e, "vessels": vs, "col": col, "cam": r, "n": n, "window": window,
            "aim": aim, "look": look}
