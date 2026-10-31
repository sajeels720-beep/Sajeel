"""Inside her throat (shots 10, 17, 18): a close-up of her windpipe in the warm, dark tissue of
her neck. With the trapped air pushing, every soft gap between the cartilage rings swells a
little (shape key "Swell") and a few spots on its front balloon right out like blisters
(shape key "Balloon"), going thin and pale so the blue air glows through them.

Stylised scale: windpipe radius 0.1 m (about ten times life size) so the camera can get
close. It stands upright along +Z from the origin, swaying a little; the camera side is
the front (-Y). Its C-shaped rings are open at the back (+Y), where soft muscle closes
the tube.
"""
import math

import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
R = 0.1                       # windpipe radius
RING_GAP = 0.066              # ring centre to ring centre
RING_W = 0.032                # ring width along the windpipe
OPEN = 0.6                    # half-width (radians) of the open back of each C-ring
BACK = (0.0, 1.0, 0.0)
AIR_GLOW = (0.0005, 0.2145, 1.0)   # the trapped air's blue (AgX-solved, as in air_fx), x strength
RED_GLOW = (1.0, 0.035, 0.02)      # a weak spot glowing red (x strength)
# blisters that balloon out: (height up the windpipe in m, direction round it in degrees
# from the front, towards +X positive; size)
BALLOONS = ((0.42, -35.0, 1.0), (0.62, 25.0, 0.85), (0.86, -10.0, 0.95), (1.12, 40.0, 0.8))


def path_points(length=3.2, start=-0.25, n=400):
    z = np.linspace(start, start + length, n)
    x = 0.03 * np.sin(z / 0.8 + 0.4)
    y = 0.05 * np.sin(z / 1.3) + 0.03 * z
    return np.stack([x, y, z], 1)


def _frames(P):
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    back = np.asarray(BACK, float)
    N1 = np.zeros_like(P)
    n1 = back - T[0] * (back @ T[0])
    for i in range(len(P)):                                       # parallel transport, starting at the back
        n1 = n1 - T[i] * (n1 @ T[i])
        n1 /= np.linalg.norm(n1)
        N1[i] = n1
    return T, N1, np.cross(T, N1)


def _smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def windpipe(col, length=3.2, start=-0.25, n_around=144, step=0.004, swell=0.12, balloon=0.62, balloons=BALLOONS,
             seed=3, name="Windpipe_Close"):
    """The windpipe as one mesh: UVs (u along, v around), point attributes "ring" (1 on the
    cartilage), "gap" (1 midway between rings) and "balloon" (1 at the top of a blister), and
    shape keys "Swell" (every gap out by `swell` x the radius) and "Balloon" (the blisters
    out by up to `balloon` x the radius). Returns the object."""
    rng = np.random.default_rng(seed)
    P = path_points(length, start, int(length / step))
    T, N1, N2 = _frames(P)
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    n_along = len(P)
    th = np.linspace(0, 2 * math.pi, n_around, endpoint=False)    # 0 = back (+Y), pi = front
    # along the windpipe: phase within each ring period (0 = ring centre, 0.5 = middle of a gap)
    k = np.round(s / RING_GAP)
    u = np.abs(s / RING_GAP - k)
    w = RING_W / (2 * RING_GAP)
    ring_s = 1.0 - _smoothstep(w - 0.06, w + 0.04, u)
    v = np.clip((u - w) / (0.5 - w), 0.0, 1.0)
    gap_s = np.sin(v * math.pi / 2) ** 2
    gi = np.floor(s / RING_GAP).astype(int)                      # gap index: changes at a ring, where nothing bulges
    amp = rng.uniform(0.75, 1.0, gi.max() + 2)[gi]                # each gap swells a little differently
    # around: the C-ring is open at the back
    back = np.abs(np.angle(np.exp(1j * th)))                     # 0 at the back, pi at the front
    ring_t = _smoothstep(OPEN, OPEN + 0.3, back)
    ring = ring_s[:, None] * ring_t[None, :]
    gap = np.clip(gap_s[:, None] * (0.75 + 0.25 * ring_t[None, :]) + (1 - ring_t[None, :]) * 0.6, 0.0, 1.0)
    # blisters: each sits in the middle of one gap, on the front, and stays between its rings
    z0 = P[:, 2]
    bl = np.zeros((n_along, n_around))
    for zc, deg, size in balloons:
        i0 = int(np.argmin(np.abs(z0 - zc)))
        sc = (np.floor(s[i0] / RING_GAP) + 0.5) * RING_GAP           # snap to the middle of its gap
        dth = np.angle(np.exp(1j * (th - (math.pi + math.radians(deg)))))
        along = np.exp(-((s - sc) / (0.24 * RING_GAP)) ** 2) * (np.abs(s - sc) < 0.5 * RING_GAP)
        bl = np.maximum(bl, size * along[:, None] * np.exp(-(dth / 0.55) ** 2)[None, :])
    ripple = 1.0 + 0.012 * np.sin(th[None, :] * 7 + s[:, None] * 40) * (1 - ring)
    r0 = R * (1.0 + 0.055 * ring) * ripple
    r_swell = r0 + R * swell * gap * amp[:, None] + R * 0.02 * ring
    r_ball = r0 + R * balloon * bl ** 1.3
    d = (np.cos(th)[None, :, None] * N1[:, None, :] + np.sin(th)[None, :, None] * N2[:, None, :])
    pts = lambda r: (P[:, None, :] + d * r[..., None]).reshape(-1, 3)
    faces = []
    for i in range(n_along - 1):
        for j in range(n_around):
            a, b = i * n_around + j, i * n_around + (j + 1) % n_around
            faces.append((a, b, b + n_around, a + n_around))
    me = bpy.data.meshes.new(name)
    me.from_pydata(pts(r0).tolist(), [], faces)
    uv = me.uv_layers.new(name="UVMap")
    U = (s / (2 * math.pi * R))[:, None] * np.ones((1, n_around))
    Vv = np.ones((n_along, 1)) * (np.arange(n_around) / n_around)[None, :]
    loops = np.array([l.vertex_index for l in me.loops])
    vv = Vv.reshape(-1)[loops]                                    # the wrap-around column gets v = 1, not 0
    corner = np.tile(np.arange(4), len(faces))
    first_j = np.repeat(np.array([f[0] % n_around for f in faces]), 4)
    vv = np.where((first_j == n_around - 1) & ((corner == 1) | (corner == 2)), 1.0, vv)
    uv.data.foreach_set("uv", np.stack([U.reshape(-1)[loops], vv], 1).reshape(-1))
    S_, TH_ = np.meshgrid(s, th, indexing="ij")
    for nm, arr in (("ring", ring), ("gap", gap * amp[:, None]), ("balloon", np.clip(bl, 0, 1)), ("s_along", S_),
                    ("theta", TH_)):
        at = me.attributes.new(nm, "FLOAT", "POINT")
        at.data.foreach_set("value", arr.reshape(-1).astype(np.float32))
    ob = V.link(bpy.data.objects.new(name, me), col)
    K.shade_smooth(ob)
    ob.shape_key_add(name="Basis")
    for nm, r in (("Swell", r_swell), ("Balloon", r_ball)):
        sk = ob.shape_key_add(name=nm)
        sk.data.foreach_set("co", pts(r).astype(np.float32).reshape(-1))
    ob["path"] = P[::8].reshape(-1).tolist()                       # centre line, for cameras and effects
    ob["balloon_at"] = [((math.floor(s[int(np.argmin(np.abs(z0 - zc)))] / RING_GAP) + 0.5) * RING_GAP,
                         math.pi + math.radians(deg)) for zc, deg, _ in balloons]   # (s, theta) of each blister
    return ob


def centre_line(ob):
    return np.asarray(ob["path"], float).reshape(-1, 3)


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


def wall_material(name="Windpipe_Wall"):
    """Wet pink-red wall with pale cartilage rings and fine vessels. Keyable values:
    "Stretch" (0..1: the wall thins and pales between the rings, its vessels stand out)
    and "Glow" (the blue air shining through the thin wall)."""
    m = V.principled(name, H("#B9475A"), rough=0.34, sss=0.45, sss_radius=(1.0, 0.3, 0.22), sss_scale=0.02,
                     coat=0.55, emission=AIR_GLOW, emission_strength=0.0)
    nt = m.node_tree
    b = V.bsdf(m)
    def attr(nm):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_name = nm
        return n.outputs["Fac"]

    ring, gap, ball = attr("ring"), attr("gap"), attr("balloon")
    stretch, glow = _value(nt, "Stretch", 0.0), _value(nt, "Glow", 0.0)
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    uvo = uvn.outputs["UV"]
    # soft blotches of deeper red (they stretch with the wall: UV space)
    blot = nt.nodes.new("ShaderNodeTexNoise")
    blot.inputs["Scale"].default_value = 3.0
    blot.inputs["Detail"].default_value = 4.0
    nt.links.new(uvo, blot.inputs["Vector"])
    base = _mix(nt, _math(nt, "MULTIPLY", blot.outputs["Fac"], 0.55), H("#C25366"), H("#8E2F3A"))
    # fine vessels: the edges of a cell pattern
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 9.0
    nt.links.new(uvo, vor.inputs["Vector"])
    vessel = nt.nodes.new("ShaderNodeMapRange")
    vessel.inputs["From Min"].default_value, vessel.inputs["From Max"].default_value = 0.0, 0.035
    vessel.inputs["To Min"].default_value, vessel.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(vor.outputs["Distance"], vessel.inputs["Value"])
    soft = _math(nt, "SUBTRACT", 1.0, ring)
    vessels = _math(nt, "MULTIPLY", vessel.outputs["Result"], _math(nt, "MULTIPLY", soft,
                                                                      _math(nt, "MULTIPLY_ADD", stretch, 0.5, 0.45)))
    blister = _math(nt, "MULTIPLY", _math(nt, "POWER", ball, 1.4), _value(nt, "Balloon", 0.0))
    thin = _math(nt, "MINIMUM", _math(nt, "ADD", blister, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", gap, soft),
                                                                     _math(nt, "MULTIPLY", stretch, 0.3))), 1.0)
    col = _mix(nt, _math(nt, "MULTIPLY", thin, 0.75), base, H("#F4B4C0"))        # stretched thin: paler
    col = _mix(nt, vessels, col, H("#6E0F24"))
    col = _mix(nt, _math(nt, "MULTIPLY", ring, 0.85), col, H("#D9AEB2"))          # cartilage, pearly pink
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(_math(nt, "MULTIPLY_ADD", ring, -0.04, 0.34), b.inputs["Roughness"])
    # the blue air glowing through the thinnest wall (the blisters' tops)
    glow_mask = _math(nt, "MULTIPLY", _math(nt, "POWER", thin, 2.0), glow)
    nt.links.new(glow_mask, V._inp(b, "Emission Strength"))
    # fine wet bumps
    bn = nt.nodes.new("ShaderNodeTexNoise")
    bn.inputs["Scale"].default_value = 60.0
    bn.inputs["Detail"].default_value = 6.0
    nt.links.new(uvo, bn.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.12
    bp.inputs["Distance"].default_value = 0.002
    nt.links.new(bn.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def key_pressure(ob, mat, keys, glow=2.2):
    """The trapped air pushing: keys = [(frame, swell 0..1, balloon 0..1)] drive the swelling,
    the blisters, the thinning and the glow together (the glow follows a frame behind)."""
    kb = ob.data.shape_keys.key_blocks
    nodes = mat.node_tree.nodes
    for f, a, b in keys:
        for key, val in ((kb["Swell"], a), (kb["Balloon"], b)):
            key.value = val
            key.keyframe_insert("value", frame=f)
        for nm, val, at in (("Stretch", a, f), ("Balloon", b, f), ("Glow", glow * b * b, f + 1)):
            sock = nodes[nm].outputs[0]
            sock.default_value = val
            sock.keyframe_insert("default_value", frame=at)
    V.ease_id(ob.data.shape_keys)
    V.ease_id(mat.node_tree)


def surroundings(col, centre, seed=5):
    """Out-of-focus neighbours in the dark behind the windpipe: the gullet (a flattened pink
    tube) and two big red vessels, so it sits inside a neck, not in empty space."""
    rng = np.random.default_rng(seed)
    c = np.asarray(centre, float)
    gullet = K.tube("Gullet", K.path_spline([c + (-0.05, 0.3, -1.0), c + (0.02, 0.34, 0.2), c + (0.08, 0.3, 1.6)], 80),
                    0.12, segments=32, squash=[(1.0, 0.55)] * 80, col=col, side=(1, 0, 0))
    V.assign(gullet, V.principled("Gullet", H("#9E3B4C"), rough=0.4, sss=0.3, sss_radius=(1, 0.3, 0.2),
                                   sss_scale=0.03, coat=0.3))
    vessel_mat = V.principled("Neck_Vessel", H("#5E0C17"), rough=0.5, sss=0.4, sss_radius=(1.0, 0.2, 0.15),
                              sss_scale=0.05, coat=0.2)
    out = [gullet]
    for i, side in enumerate((-1, 1)):                            # behind the windpipe (+Y), to either side
        x, y = side * rng.uniform(0.5, 0.6), rng.uniform(0.7, 0.85)
        pts = [c + (x, y, -1.0), c + (x * 1.15, y * 1.1, 0.4), c + (x, y, 1.8)]
        t = K.tube(f"Neck_Vessel_{i}", K.path_spline(pts, 80), 0.07, segments=24, col=col)
        V.assign(t, vessel_mat)
        out.append(t)
    return out


def surface_point(ob, s_c, th_c, out=0.0):
    """World point and outward normal on the windpipe (as built, before shape keys) at arc
    length s_c and angle th_c (0 = back, pi = front)."""
    P = np.asarray(ob["path"], float).reshape(-1, 3)
    sP = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    i = int(np.clip(np.searchsorted(sP, s_c), 1, len(P) - 1))
    T, N1, N2 = _frames(P)
    d = math.cos(th_c) * N1[i] + math.sin(th_c) * N2[i]
    return Vector(P[i] + d * (R + out)), Vector(d)


def add_tear(ob, mat, s_c, th_c, glow_r=0.05, flap=0.03):
    """Make one spot of the wall a weak spot that can glow red and rip open: shape key "Tear"
    (the torn flaps curl out), and material values "WeakGlow" (red glow round it) and
    "TearRadius" (m: the ragged hole, dark torn edges)."""
    me = ob.data
    S_ = np.zeros(len(me.vertices)); TH = np.zeros(len(me.vertices))
    me.attributes["s_along"].data.foreach_get("value", S_)
    me.attributes["theta"].data.foreach_get("value", TH)
    ds = S_ - s_c
    dt = np.angle(np.exp(1j * (TH - th_c))) * R
    d = np.hypot(ds, dt)
    ang = np.arctan2(dt, ds)
    q = d / (1 + 0.28 * np.sin(4 * ang + 0.6) + 0.15 * np.sin(7 * ang + 2.0))
    f = np.clip(1 - (q - 0.012) / 0.03, 0, 1) ** 2
    basis = np.zeros(len(me.vertices) * 3)
    me.shape_keys.key_blocks["Basis"].data.foreach_get("co", basis)
    B = basis.reshape(-1, 3)
    P = np.asarray(ob["path"], float).reshape(-1, 3)
    # outward normal ~ from the nearest centre-line point
    near = np.argmin(np.linalg.norm(B[:, None, :] - P[None, ::4, :], axis=2), axis=1) * 4
    nrm = B - P[np.minimum(near, len(P) - 1)]
    nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-9
    sk = ob.shape_key_add(name="Tear", from_mix=False)
    sk.data.foreach_set("co", (B + nrm * (flap * f)[:, None]).astype(np.float32).reshape(-1))
    # material: red weak spot, ragged hole
    nt = mat.node_tree
    b = V.bsdf(mat)

    def attr(nm):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_name = nm
        return n.outputs["Fac"]

    sa, ta = attr("s_along"), attr("theta")
    ds_ = _math(nt, "SUBTRACT", sa, s_c)
    dt_ = _math(nt, "MULTIPLY", _math(nt, "WRAP", _math(nt, "SUBTRACT", ta, th_c), math.pi, -math.pi), R)  # (value, max, min)
    dist = _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", ds_, ds_), _math(nt, "MULTIPLY", dt_, dt_)))
    angle = _math(nt, "ARCTAN2", dt_, ds_)
    petal = _math(nt, "MULTIPLY_ADD", _math(nt, "SINE", _math(nt, "MULTIPLY_ADD", angle, 4.0, 0.6)), 0.28, 1.0)
    petal = _math(nt, "MULTIPLY_ADD", _math(nt, "SINE", _math(nt, "MULTIPLY_ADD", angle, 7.0, 2.0)), 0.15, petal)
    rag = nt.nodes.new("ShaderNodeTexNoise")
    rag.inputs["Scale"].default_value = 40.0
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    nt.links.new(uvn.outputs["UV"], rag.inputs["Vector"])
    hd = _math(nt, "ADD", _math(nt, "DIVIDE", dist, petal), _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", rag.outputs["Fac"], 0.5),
                                                                      0.008))
    tear_r, weak = _value(nt, "TearRadius", 0.0), _value(nt, "WeakGlow", 0.0)
    open_ = _math(nt, "GREATER_THAN", tear_r, 0.0005)
    nt.links.new(_math(nt, "MAXIMUM", _math(nt, "GREATER_THAN", hd, tear_r), _math(nt, "SUBTRACT", 1.0, open_)),
                 V._inp(b, "Alpha"))
    edge = _math(nt, "MULTIPLY", open_, _math(nt, "SUBTRACT", 1.0, _math(nt, "MINIMUM", _math(nt, "DIVIDE", _math(
        nt, "MAXIMUM", _math(nt, "SUBTRACT", hd, tear_r), 0.0), 0.006), 1.0)))
    col_in = b.inputs["Base Color"].links[0].from_socket
    nt.links.new(_mix(nt, _math(nt, "MULTIPLY", edge, 0.85), col_in, H("#5A0D18")), b.inputs["Base Color"])
    # the red glow, mixed with the blue air glow already there
    spot = _math(nt, "MULTIPLY", _math(nt, "POWER", _math(nt, "MAXIMUM", _math(nt, "SUBTRACT", 1.0,
                                                                                _math(nt, "DIVIDE", dist, glow_r)), 0.0), 1.6), weak)
    blue = V._inp(b, "Emission Strength").links[0].from_socket
    total = _math(nt, "ADD", blue, spot)
    share = _math(nt, "DIVIDE", spot, _math(nt, "ADD", total, 0.001))
    nt.links.new(_mix(nt, share, AIR_GLOW, RED_GLOW), _inp_color(b))
    nt.links.new(total, V._inp(b, "Emission Strength"))
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "HASHED"
    return sk


def _inp_color(b):
    return V._inp(b, "Emission Color", "Emission")


def key_tear(ob, mat, keys):
    """keys = [(frame, weak glow, flaps 0..1, tear radius m)]."""
    kb = ob.data.shape_keys.key_blocks["Tear"]
    nodes = mat.node_tree.nodes
    for f, g, fl, tr in keys:
        kb.value = fl
        kb.keyframe_insert("value", frame=f)
        for nm, val in (("WeakGlow", g), ("TearRadius", tr)):
            sock = nodes[nm].outputs[0]
            sock.default_value = val
            sock.keyframe_insert("default_value", frame=f)
    V.ease_id(ob.data.shape_keys)
    V.ease_id(mat.node_tree)
