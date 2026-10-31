"""Her eardrum up close (shot 14), as through a doctor's otoscope: we look down the ear canal
(moist pink skin, lit by the otoscope's light beside the lens) at the eardrum closing its
end: a pearly, slightly cone-shaped membrane, the handle of the first ear bone showing
through it as a pale ridge, fine vessels round its rim. Shape key "Bulge" domes it towards
us (the trapped air pushing from behind); then it tears: a ragged hole opens (material value
"HoleRadius"), the torn flaps curl towards us (shape key "Flaps"), and behind it lies the
dark red middle ear, full of glowing blue air.

Stylised scale: eardrum radius 0.08 m (about 18 times life size). It faces -Y (towards
the camera), centred at the origin, up +Z.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
R = 0.08                      # eardrum radius
HOLE_AT = (0.024, -0.02)      # (x, z) where it tears: the lower front quadrant, where real ones usually do
HOLE_R = 0.03                 # radius of the hole once it has torn open
AIR_GLOW = (0.0005, 0.2145, 1.0)   # the trapped air's blue (AgX-solved, as in air_fx), x strength
MALLEUS = ((0.0, 0.0), (0.008, 0.05))   # the bone's handle: from the centre up and a little forward
TEAR = ((5, 0.26, 0.7), (3, 0.17, 2.1), (8, 0.1, 0.3))   # the torn outline: (lobes, size, phase) summed, uneven


def tear_shape(theta):
    """1 + how far the tear reaches out in direction theta (round the hole's centre)."""
    return 1.0 + sum(a * np.sin(k * theta + ph) for k, a, ph in TEAR)


def _seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    t = np.clip(((px - ax) * (bx - ax) + (pz - az) * (bz - az)) / ((bx - ax) ** 2 + (bz - az) ** 2), 0, 1)
    return np.hypot(px - (ax + t * (bx - ax)), pz - (az + t * (bz - az)))


def membrane(col, rings=56, segments=144, cone=0.008, bulge=0.036, name="Eardrum_Macro"):
    """The eardrum as a polar grid: shape keys "Bulge" and "Flaps", point attributes "ridge"
    (the bone's handle) and "rim" (its thick outer edge)."""
    r = np.r_[0.0, (np.arange(1, rings + 1) / rings) ** 0.9 * R]
    a = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    X = np.r_[0.0, (r[1:, None] * np.cos(a)[None, :]).reshape(-1)]
    Z = np.r_[0.0, (r[1:, None] * np.sin(a)[None, :]).reshape(-1)]
    rr = np.hypot(X, Z)
    ridge = np.exp(-(_seg_dist(X, Z, *MALLEUS) / 0.0045) ** 2)
    rim = np.clip((rr / R - 0.86) / 0.14, 0, 1)
    y0 = cone * (1 - rr / R) - 0.0005 * ridge + 0.004 * rim ** 2   # cone drawn in at the centre, ridge barely raised
    yb = y0 - bulge * np.clip(1 - (rr / R) ** 2, 0, 1) ** 1.1       # domed towards us
    # torn flaps: the membrane round the hole curls out towards us and away from the hole
    hx, hz = HOLE_AT
    q = np.hypot(X - hx, Z - hz) / tear_shape(np.arctan2(Z - hz, X - hx))
    f = np.clip(1 - (q - HOLE_R * 0.6) / (HOLE_R * 1.1), 0, 1) ** 2
    ux, uz = (X - hx) / np.maximum(q, 1e-6), (Z - hz) / np.maximum(q, 1e-6)
    fx, fz, fy = X + ux * 0.012 * f, Z + uz * 0.012 * f, y0 - 0.03 * f
    verts = np.stack([X, y0, Z], 1)
    faces = [(0, 1 + k, 1 + (k + 1) % segments) for k in range(segments)]
    for i in range(rings - 1):
        r0, r1 = 1 + i * segments, 1 + (i + 1) * segments
        faces += [(r0 + k, r1 + k, r1 + (k + 1) % segments, r0 + (k + 1) % segments) for k in range(segments)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces)
    for nm, arr in (("ridge", ridge), ("rim", rim)):
        at = me.attributes.new(nm, "FLOAT", "POINT")
        at.data.foreach_set("value", arr.astype(np.float32))
    ob = V.link(bpy.data.objects.new(name, me), col)
    K.shade_smooth(ob)
    ob.shape_key_add(name="Basis")
    for nm, P in (("Bulge", np.stack([X, yb, Z], 1)), ("Flaps", np.stack([fx, fy, fz], 1))):
        sk = ob.shape_key_add(name=nm)
        sk.data.foreach_set("co", P.astype(np.float32).reshape(-1))
    return ob


def _value(nt, name, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.name = n.label = name
    n.outputs[0].default_value = value
    return n.outputs[0]


def _math(nt, op, *inputs):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for i, v in enumerate(inputs):
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def _mix(nt, fac, a, b):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    for sock, v in ((0, fac), (6, a), (7, b)):
        if isinstance(v, (tuple, list)):
            m.inputs[sock].default_value = (*v, 1) if len(v) == 3 else v
        elif isinstance(v, (int, float)):
            m.inputs[sock].default_value = v
        else:
            nt.links.new(v, m.inputs[sock])
    return m.outputs[2]


def membrane_material(name="Eardrum_Macro"):
    """Pearly, wet, a little see-through; red vessels round the rim and along the bone's
    handle that swell with "Stretch" (0..1); a ragged hole of radius "HoleRadius" (m) at
    HOLE_AT with dark torn edges."""
    m = V.principled(name, H("#BFA6A6"), rough=0.34, sss=0.35, sss_radius=(1.0, 0.45, 0.4), sss_scale=0.01,
                     coat=0.25, spec=0.5)
    nt = m.node_tree
    b = V.bsdf(m)

    def attr(nm):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_name = nm
        return n.outputs["Fac"]

    ridge, rim = attr("ridge"), attr("rim")
    stretch, hole_r = _value(nt, "Stretch", 0.0), _value(nt, "HoleRadius", 0.0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    x, z = sep.outputs["X"], sep.outputs["Z"]
    # vessels: thin wavy radial lines, strongest near the rim and along the ridge
    ang = _math(nt, "ARCTAN2", z, x)
    rad = _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", x, x), _math(nt, "MULTIPLY", z, z)))
    wav = nt.nodes.new("ShaderNodeTexNoise")
    wav.inputs["Scale"].default_value = 30.0
    nt.links.new(tc.outputs["Object"], wav.inputs["Vector"])
    lines = _math(nt, "POWER", _math(nt, "ABSOLUTE", _math(nt, "SINE", _math(nt, "ADD", _math(nt, "MULTIPLY", ang, 22.0),
                                                                               _math(nt, "MULTIPLY", wav.outputs["Fac"], 6.0)))),
                  40.0)
    near_rim = _math(nt, "POWER", _math(nt, "DIVIDE", rad, R), 3.0)
    vessels = _math(nt, "MINIMUM", _math(nt, "MULTIPLY", _math(nt, "ADD", _math(nt, "MULTIPLY", lines, near_rim),
                                                                    _math(nt, "MULTIPLY", ridge, 0.5)),
                                          _math(nt, "MULTIPLY_ADD", stretch, 0.8, 0.35)), 1.0)
    col = _mix(nt, _math(nt, "MULTIPLY", ridge, 0.75), H("#BFA6A6"), H("#EADBD0"))     # the bone's pale ridge
    col = _mix(nt, _math(nt, "MULTIPLY", rim, 0.7), col, H("#C7878C"))                 # the thicker pink rim
    col = _mix(nt, _math(nt, "MULTIPLY", stretch, 0.35), col, H("#E3A0A4"))           # stretched: flushed
    col = _mix(nt, vessels, col, H("#B3202C"))
    # the hole: ragged edge from noise, dark torn tissue just outside it
    hx = _math(nt, "SUBTRACT", x, HOLE_AT[0])
    hz = _math(nt, "SUBTRACT", z, HOLE_AT[1])
    rag = nt.nodes.new("ShaderNodeTexNoise")
    rag.inputs["Scale"].default_value = 34.0
    rag.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], rag.inputs["Vector"])
    theta = _math(nt, "ARCTAN2", hz, hx)
    petal = 1.0
    for k, a, ph in TEAR:
        petal = _math(nt, "MULTIPLY_ADD", _math(nt, "SINE", _math(nt, "MULTIPLY_ADD", theta, float(k), ph)), a, petal)
    hd = _math(nt, "ADD", _math(nt, "DIVIDE", _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", hx, hx),
                                                                      _math(nt, "MULTIPLY", hz, hz))), petal),
               _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", rag.outputs["Fac"], 0.5), 0.026))
    open_ = _math(nt, "GREATER_THAN", hole_r, 0.0005)
    edge = _math(nt, "MULTIPLY", open_, _math(nt, "SUBTRACT", 1.0, _math(nt, "MINIMUM", _math(nt, "DIVIDE", _math(
        nt, "MAXIMUM", _math(nt, "SUBTRACT", hd, hole_r), 0.0), 0.004), 1.0)))
    col = _mix(nt, _math(nt, "MULTIPLY", edge, 0.85), col, H("#6E1420"))
    nt.links.new(col, b.inputs["Base Color"])
    alpha = _math(nt, "MAXIMUM", _math(nt, "GREATER_THAN", hd, hole_r), _math(nt, "SUBTRACT", 1.0, open_))
    nt.links.new(alpha, V._inp(b, "Alpha"))
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "DITHERED"
    elif hasattr(m, "blend_method"):
        m.blend_method = "HASHED"
    return m


def canal(col, length=1.6, r_end=0.0795, r_near=0.13, n_along=120, n_around=96):
    """The ear canal: a gently curving tube of moist skin from behind the camera to the
    eardrum's rim (at y = 0), just inside the rim so no light leaks round it."""
    y = np.linspace(-length, 0.004, n_along)
    t = (y + length) / length
    path = np.stack([0.006 * np.sin(t * 3) * (1 - t), y, -0.01 * np.sin(t * 2.2) * (1 - t)], 1)   # ends centred on it
    radii = r_near + (r_end - r_near) * t ** 0.7
    tube = K.tube("Ear_Canal_Macro", path, radii, segments=n_around, col=col)
    m = V.principled("Ear_Canal_Skin", H("#D68E8A"), rough=0.4, sss=0.4, sss_radius=(1.0, 0.35, 0.25), sss_scale=0.02,
                     coat=0.3)
    V.color_variation(m, H("#B0585A"), scale=18.0, amount=0.5)
    V.bump(m, scale=55.0, strength=0.25, distance=0.003)
    V.assign(tube, m)
    bm = bmesh.new()                                              # open at both ends (the tube kit caps them)
    bm.from_mesh(tube.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if len(f.verts) > 4], context="FACES")
    bm.to_mesh(tube.data)
    bm.free()
    for p in tube.data.polygons:                                  # seen from inside
        p.flip()
    tube.data.update()
    return tube


def middle_ear(col):
    """Behind the eardrum: the dark red middle ear, a deep bowl open towards the eardrum,
    the trapped air glowing blue in it (material value "Air" is how bright)."""
    cave = K.ellipsoid("Middle_Ear_Macro", (0.0, 0.03, 0.0), (0.11, 0.24, 0.11), segments=48, col=col)
    bm = bmesh.new()
    bm.from_mesh(cave.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y < 0.012], context="FACES")
    bm.to_mesh(cave.data)
    bm.free()
    for p in cave.data.polygons:                                  # seen from inside
        p.flip()
    cave.data.update()
    m = V.principled("Middle_Ear_Wall", H("#36090F"), rough=0.35, sss=0.2, sss_radius=(1, 0.3, 0.2), sss_scale=0.03,
                     coat=0.4, emission=AIR_GLOW, emission_strength=0.0)
    V.bump(m, scale=25.0, strength=0.3, distance=0.004)
    nt = m.node_tree
    air = _value(nt, "Air", 0.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")                      # wisps of glowing air, dark in between
    nz.inputs["Scale"].default_value = 5.0
    nz.inputs["Detail"].default_value = 3.0
    wisp = _math(nt, "POWER", _math(nt, "MAXIMUM", _math(nt, "SUBTRACT", nz.outputs["Fac"], 0.42), 0.0), 1.5)
    nt.links.new(_math(nt, "MULTIPLY", _math(nt, "MULTIPLY", wisp, 6.0), air), V._inp(V.bsdf(m), "Emission Strength"))
    V.assign(cave, m)
    return cave, m


def key_drum(drum, mat, keys):
    """keys = [(frame, bulge 0..1, flaps 0..1, hole radius m)]."""
    kb = drum.data.shape_keys.key_blocks
    nodes = mat.node_tree.nodes
    for f, bl, fl, hr in keys:
        for key, val in ((kb["Bulge"], bl), (kb["Flaps"], fl)):
            key.value = val
            key.keyframe_insert("value", frame=f)
        for nm, val in (("Stretch", bl), ("HoleRadius", hr)):
            sock = nodes[nm].outputs[0]
            sock.default_value = val
            sock.keyframe_insert("default_value", frame=f)
    V.ease_id(drum.data.shape_keys)
    V.ease_id(mat.node_tree)


def fragments(col, pop, rng, count=16, toward=(0.0, -1.0, 0.0)):
    """Torn shreds of eardrum blown out of the hole towards the camera on frame `pop`."""
    hx, hz = HOLE_AT
    mat = V.principled("Eardrum_Shred", H("#C9A3A3"), rough=0.3, sss=0.3, sss_radius=(1.0, 0.45, 0.4), sss_scale=0.01,
                       coat=0.6)
    out = []
    for i in range(count):
        bm = bmesh.new()
        s = rng.uniform(0.004, 0.011)
        pts = [bm.verts.new((s * math.cos(a) * rng.uniform(0.5, 1.0), rng.uniform(-0.0006, 0.0006),
                             s * math.sin(a) * rng.uniform(0.5, 1.0))) for a in np.sort(rng.uniform(0, 2 * math.pi, 5))]
        bm.faces.new(pts)
        me = bpy.data.meshes.new(f"Eardrum_Shred_{i}")
        bm.to_mesh(me)
        bm.free()
        ob = V.link(bpy.data.objects.new(me.name, me), col)
        V.assign(ob, mat)
        a = rng.uniform(0, 2 * math.pi)
        start = Vector((hx + math.cos(a) * HOLE_R * 0.8, -0.01, hz + math.sin(a) * HOLE_R * 0.8))
        d = (Vector(toward) + Vector((math.cos(a), 0, math.sin(a))) * rng.uniform(0.3, 0.9)).normalized()
        speed, spin = rng.uniform(0.012, 0.03), rng.uniform(-0.6, 0.6, 3)
        ob.rotation_euler = tuple(rng.uniform(0, 6.28, 3))
        r0 = ob.rotation_euler.copy()
        for k in range(0, 16):
            f = pop + k
            ob.location = start + d * speed * k * (1 - 0.02 * k) + Vector((0, 0, -0.0004 * k * k))
            ob.rotation_euler = (r0.x + spin[0] * k, r0.y + spin[1] * k, r0.z + spin[2] * k)
            sc = 1.0 if k < 10 else max(0.0, 1 - (k - 10) / 6)
            ob.scale = (sc, sc, sc)
            for path in ("location", "rotation_euler", "scale"):
                ob.keyframe_insert(path, frame=f)
        V.visible(ob, [(1, False), (pop, True), (pop + 16, False)])
        out.append(ob)
    return out
