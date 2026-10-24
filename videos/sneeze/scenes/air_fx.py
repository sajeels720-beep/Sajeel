"""The air inside her in the x-ray shots (06-09): glowing comets of air that rush up out of
her lungs (the blast), slam into her shut lips and pinched nose and bounce back, and swirl
round inside her head.

A comet is a small streak with a white-hot head and a fading cyan tail. Each one is keyed
frame by frame along the airway centre lines that airways.build() returns, pushed sideways
inside its passage (a ray cast measures the room to the wall in 16 directions, so the air
fills flat and narrow passages alike without poking through) and stretched by its speed.
"""
import math

import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
# linear emission that AgX Punchy shows as a royal-blue tail (52, 117, 219) and an ice-blue
# head (182, 215, 246): solved by rendering patches (brighter blues wash out to white)
TAIL = (0.0025, 0.1277, 2.2228)
HEAD = (0.0086, 2.8387, 8.7991)
WALL_GLOW = (0.0005, 0.2145, 1.0)               # x strength: the light it throws on the airway walls
N_DIRS = 16


# --------------------------------------------------------------------------
# Look
# --------------------------------------------------------------------------
def _math(nt, op, *inputs):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for i, v in enumerate(inputs):
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def _emission(nt, lin, gain):
    em = nt.nodes.new("ShaderNodeEmission")
    peak = max(lin)
    em.inputs["Color"].default_value = (*(c / peak for c in lin), 1)
    em.inputs["Strength"].default_value = peak * gain
    return em.outputs[0]


def material(name="Air", gain=1.0):
    """Comet shader: an ice-blue head (local +Y) fading into a royal-blue tail (-Y), soft at
    the edges, see-through elsewhere. gain brightens it (the big core comets). Its
    'AirAmount' value (0..1) dims every comet using it."""
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    along = nt.nodes.new("ShaderNodeMapRange")                 # 0 at the tail, 1 at the head
    along.inputs["From Min"].default_value, along.inputs["From Max"].default_value = -1.0, 1.0
    nt.links.new(sep.outputs["Y"], along.inputs["Value"])
    head = nt.nodes.new("ShaderNodeMapRange")                  # tail colour -> head colour
    head.interpolation_type = "SMOOTHSTEP"
    head.inputs["From Min"].default_value, head.inputs["From Max"].default_value = 0.5, 0.95
    nt.links.new(along.outputs["Result"], head.inputs["Value"])
    colour = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(head.outputs["Result"], colour.inputs[0])
    nt.links.new(_emission(nt, TAIL, gain), colour.inputs[1])
    nt.links.new(_emission(nt, HEAD, gain), colour.inputs[2])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.3
    edge = _math(nt, "POWER", _math(nt, "SUBTRACT", 1.0, lw.outputs["Facing"]), 1.3)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    vary = _math(nt, "MULTIPLY_ADD", info.outputs["Random"], 0.45, 0.55)
    amount = nt.nodes.new("ShaderNodeValue")
    amount.name = amount.label = "AirAmount"
    amount.outputs[0].default_value = 1.0
    alpha = _math(nt, "MULTIPLY", _math(nt, "POWER", along.outputs["Result"], 1.5), edge)
    alpha = _math(nt, "MINIMUM", _math(nt, "MULTIPLY", alpha, _math(nt, "MULTIPLY", vary, amount.outputs[0])), 1.0)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alpha, mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(colour.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    V._blended(mat)
    return mat


def haze_material(name, amount=0.35):
    """A faint version of the comet shader for big soft comets: a blue glow filling the passage."""
    mat = material(name, 0.9)
    mat.node_tree.nodes["AirAmount"].outputs[0].default_value = amount
    return mat


def key_amount(mat, keys):
    """Fade every comet with this material: keys = [(frame, 0..1)]."""
    V.animate_socket(mat.node_tree.nodes["AirAmount"].outputs[0], keys)


def comet_mesh():
    """One shared unit sphere (comets stretch it with their scale); its material slot is
    filled per object."""
    me = bpy.data.meshes.get("Air_Comet")
    if me is None:
        ob = K.ellipsoid("Air_Comet", (0, 0, 0), (1, 1, 1), segments=16)
        K.shade_smooth(ob)
        me = ob.data
        bpy.data.objects.remove(ob)
        me.materials.append(None)
    return me


# --------------------------------------------------------------------------
# Passages
# --------------------------------------------------------------------------
def _dedup(points, eps=1e-5):
    out = []
    for p in points:
        p = Vector(p)
        if not out or (p - out[-1]).length > eps:
            out.append(p)
    return out


def walls(objs):
    """The airway walls in world space, for measuring the room inside the passages."""
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        M = ob.matrix_world
        base = len(verts)
        verts += [M @ v.co for v in me.vertices]
        polys += [tuple(base + i for i in p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


class Channel:
    """A passage the air runs along: its centre line resampled by arc length (s, metres),
    a frame around it and the room to the wall in N_DIRS directions at every point."""

    def __init__(self, points, bvh=None, n=200, side=(1.0, 0.0, 0.0), fallback=0.003, max_room=0.03):
        pts = _dedup(points)
        P = np.asarray(K.path_spline([tuple(p) for p in pts], n), float)
        self.n = len(P)
        self.s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        self.length = float(self.s[-1])
        T = np.gradient(P, axis=0)
        T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
        ref = np.asarray(side, float)
        if abs(ref @ T[0]) > 0.9:
            ref = np.array([0.0, 0.0, 1.0])
        N1 = np.zeros_like(P)
        n1 = ref - T[0] * (ref @ T[0])
        for i in range(self.n):                                  # parallel transport: no twisting
            n1 = n1 - T[i] * (n1 @ T[i])
            n1 /= np.linalg.norm(n1) + 1e-12
            N1[i] = n1
        self.P, self.T, self.N1, self.N2 = P, T, N1, np.cross(T, N1)
        self.room = np.full((self.n, N_DIRS), fallback)
        if bvh is not None:
            ang = np.linspace(0, 2 * math.pi, N_DIRS, endpoint=False)
            for i in range(self.n):
                o = Vector(P[i])
                for k, a in enumerate(ang):
                    hit = bvh.ray_cast(o, Vector(math.cos(a) * N1[i] + math.sin(a) * self.N2[i]), max_room)
                    if hit[0] is not None:
                        self.room[i, k] = hit[3]

    def _idx(self, s):
        x = float(np.interp(min(max(s, 0.0), self.length), self.s, np.arange(self.n)))
        i = min(int(x), self.n - 2)
        return i, x - i

    def at(self, s, theta=0.0, rho=0.0):
        """World point at arc length s, pushed towards the wall in direction theta (radians
        around the centre line) by rho (0 = on the centre line, 1 = at the wall)."""
        i, t = self._idx(s)
        P = self.P[i] * (1 - t) + self.P[i + 1] * t
        if rho == 0.0:
            return Vector(P)
        a = (theta / (2 * math.pi)) % 1.0 * N_DIRS
        k, u = int(a) % N_DIRS, a - int(a)
        k2 = (k + 1) % N_DIRS
        room = ((self.room[i, k] * (1 - u) + self.room[i, k2] * u) * (1 - t)
                + (self.room[i + 1, k] * (1 - u) + self.room[i + 1, k2] * u) * t)
        n1 = self.N1[i] * (1 - t) + self.N1[i + 1] * t
        n2 = self.N2[i] * (1 - t) + self.N2[i + 1] * t
        return Vector(P + (math.cos(theta) * n1 + math.sin(theta) * n2) * rho * room)


class Route:
    """Channels end to end (a branch inside the lung, then the bronchus and windpipe...),
    with one arc length over all of them."""

    def __init__(self, channels):
        self.channels = channels
        self.length = sum(c.length for c in channels)

    def at(self, s, theta=0.0, rho=0.0):
        for c in self.channels[:-1]:
            if s <= c.length:
                return c.at(s, theta, rho)
            s -= c.length
        return self.channels[-1].at(s, theta, rho)


def _smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------
# Comets
# --------------------------------------------------------------------------
def comet(name, track, widths, mat, col, parent=None, stretch=0.9, max_len=0.03, first_frame=1):
    """A comet flying along `track` (a point per frame from first_frame on; None where it
    is not there yet / any more). Keys location, rotation (head along its motion) and
    scale (widths per frame, stretched by its speed)."""
    alive = [i for i, p in enumerate(track) if p is not None]
    if not alive:
        return None
    a, b = alive[0], alive[-1]
    ob = V.link(bpy.data.objects.new(name, comet_mesh()), col)
    ob.material_slots[0].link = "OBJECT"
    ob.material_slots[0].material = mat
    ob.rotation_mode = "QUATERNION"
    if parent is not None:
        ob.parent = parent
    y, q_prev = Vector((0, 1, 0)), None
    for i in range(a, b + 1):
        p = track[i] if track[i] is not None else track[i - 1]
        lo, hi = max(i - 1, a), min(i + 1, b)
        v = (track[hi] - track[lo]) / max(hi - lo, 1) if hi > lo else Vector((0, 0, 0))
        speed = v.length
        if speed > 1e-6:
            d = v.normalized()
            q = y.rotation_difference(d) if q_prev is None else (q_prev @ y).rotation_difference(d) @ q_prev
        else:
            q = q_prev if q_prev is not None else Quaternion()
        if q_prev is not None and q.dot(q_prev) < 0:
            q = -q
        q_prev = q
        w = widths[i]
        f = first_frame + i
        ob.location, ob.rotation_quaternion = p, q
        ob.scale = (w, min(w + stretch * speed, max_len), w)
        for path in ("location", "rotation_quaternion", "scale"):
            ob.keyframe_insert(path, frame=f)
    for fc in V.fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    vis = []
    if a > 0:
        vis += [(first_frame, False), (first_frame + a, True)]
    if b < len(track) - 1:
        vis += [(first_frame + b + 1, False)]
    if vis:
        V.visible(ob, vis)
    return ob


def lung_scale(lung, f):
    """The lung's (keyed) scale on frame f."""
    s = list(lung.scale)
    for fc in V.fcurves(lung):
        if fc.data_path == "scale":
            s[fc.array_index] = fc.evaluate(f)
    return s


def squeeze_lungs(aw, keys):
    """Squeeze both lungs towards their hila: keys = [(frame, (sx, sy, sz))] (x mirrored
    needs nothing: each lung scales about its own hilum)."""
    for lung in aw["lungs"].values():
        V.key(lung, "scale", keys)


def key_glow(aw, keys, radius=None, color=None):
    """The light that travels with the air: keys = [(frame, location or None, strength)].
    color: hex, to tint it (default blue; pink for the airways glowing with pressure)."""
    lin = WALL_GLOW if color is None else H(color) if isinstance(color, str) else color
    for m in (aw["mats"]["glass"], aw["mats"]["lung"]):
        m.node_tree.nodes["AirGlowEmission"].inputs["Color"].default_value = (*lin, 1)
    socks = [m.node_tree.nodes["AirGlow"].outputs[0] for m in (aw["mats"]["glass"], aw["mats"]["lung"])]
    for f, loc, strength in keys:
        if loc is not None:                                      # its root sits at the origin on the build frame
            aw["glow"].location = Vector(loc)
            aw["glow"].keyframe_insert("location", frame=f)
        for sk in socks:
            sk.default_value = strength
            sk.keyframe_insert("default_value", frame=f)
    if radius is not None:
        for m in (aw["mats"]["glass"], aw["mats"]["lung"]):
            m.node_tree.nodes["AirGlowRadius"].outputs[0].default_value = radius
    for m in (aw["mats"]["glass"], aw["mats"]["lung"]):
        V.ease_id(m.node_tree)
    V.ease_id(aw["glow"])


# --------------------------------------------------------------------------
# Choreography
# --------------------------------------------------------------------------
def blast(aw, n_frames, col, parent, rng, per_lung=30, n_core=10, launch=(1, 30), speed=0.0065, ramp=10,
          width=(0.0012, 0.002), core_width=0.0032, lead=0, n_haze=14, haze_width=0.0055):
    """The blast out of her lungs: comets stream from branch tips deep in both lungs to the
    hila (squeezed with the lungs), merge at the carina and rush up the windpipe into her
    throat. Each one speeds up over `ramp` frames, then rushes on at about `speed` m per
    frame; launches crowd towards the start of the window. Returns (comets, front):
    front[i] = the leading bright comet on frame i + 1 (None before one is out of a
    lung). lead: frames already played before frame 1 (shot 07 continues shot 06)."""
    bvh = walls(aw["walls"])
    P = aw["paths"]
    up = {side: Channel(P[f"bronchus_{side}"] + P["windpipe"] + P["larynx"] + P["pharynx"][:2], bvh)
          for side in ("R", "L")}
    mat, mat_core = material("Air_Blast"), material("Air_Blast_Core", 1.3)
    comets, front_s, front_p = [], [-1.0] * n_frames, [None] * n_frames
    for side in ("R", "L"):
        hilum, lung = aw["hila"][side], aw["lungs"][side]
        branches = aw["branches"][side]
        for k in range(per_lung + n_core // 2):
            core = k >= per_lung
            br = Channel(branches[k % len(branches)], None, n=24)
            route = Route([br, up[side]])
            t0 = launch[0] + (launch[1] - launch[0]) * rng.uniform() ** 1.6 - lead
            v = speed * rng.uniform(0.85, 1.2)
            th0, helix = rng.uniform(0, 2 * math.pi), rng.uniform(-40, 40)
            rho = rng.uniform(0.0, 0.25) if core else rng.uniform(0.2, 0.75)
            w0 = core_width if core else rng.uniform(*width)
            track, widths = [], []
            for i in range(n_frames):
                tau = i + 1 - t0
                s = -1.0 if tau <= 0 else v * tau * tau / (2 * ramp) if tau < ramp else v * (tau - ramp / 2)
                if s < 0 or s >= route.length:
                    track.append(None)
                    widths.append(0.0)
                    continue
                out_of_lung = _smooth((s - br.length) / 0.02)
                p = route.at(s, th0 + helix * s, rho * out_of_lung)
                if s < br.length:                                   # still in the lung: squeezed with it
                    sc = lung_scale(lung, i + 1)
                    d = p - hilum
                    p = hilum + Vector((d.x * sc[0], d.y * sc[1], d.z * sc[2]))
                track.append(p)
                birth = _smooth(tau / 4.0)
                widths.append(w0 * birth * (0.35 + 0.65 * out_of_lung if core else 1.0))
                if core and s > br.length and s - br.length > front_s[i]:
                    front_s[i], front_p[i] = s - br.length, p
            ob = comet(f"Air_{side}_{k:02d}", track, widths, mat_core if core else mat, col, parent)
            if ob is not None:
                comets.append(ob)
    # a soft blue glow filling the windpipe behind the streaks
    mat_haze = haze_material("Air_Blast_Haze")
    for k in range(n_haze):
        side = ("R", "L")[k % 2]
        ch = up[side]
        t0 = launch[0] + (launch[1] - launch[0]) * rng.uniform() ** 1.6 - lead + ramp
        v, rho, th0 = speed * rng.uniform(0.9, 1.1), rng.uniform(0.0, 0.15), rng.uniform(0, 2 * math.pi)
        track, widths = [], []
        for i in range(n_frames):
            tau = i + 1 - t0
            s_ = -1.0 if tau <= 0 else v * tau
            if s_ < 0 or s_ >= ch.length:
                track.append(None)
                widths.append(0.0)
                continue
            track.append(ch.at(s_, th0, rho))
            widths.append(haze_width * _smooth(tau / 5.0))
        ob = comet(f"Air_Haze_{k:02d}", track, widths, mat_haze, col, parent, stretch=2.2, max_len=0.05)
        if ob is not None:
            comets.append(ob)
    return comets, front_p


def slam(aw, n_frames, col, parent, rng, hit=13, per_route=34, n_core=6, speed=(0.008, 0.012),
         width=(0.0011, 0.0019), core_width=0.0032, stretch=1.4, n_haze=5, haze_width=0.0055):
    """The air shoots up her throat, splits into her nose and mouth, slams into the pinched
    nostrils and the shut lips on frame `hit` (the first ones; the rest pile up behind) and
    bounces back, scattering towards the walls and starting to churn. Returns the comets
    and the two end points (nose, lips)."""
    bvh = walls(aw["walls"])
    P = aw["paths"]
    base = P["windpipe"][-3:] + P["larynx"]
    routes = {"nose": Channel(base + P["pharynx"] + P["nasal"], bvh, n=260),
              "mouth": Channel(base + P["pharynx"][:2] + P["oral"], bvh, n=240)}
    mat, mat_core = material("Air_Slam"), material("Air_Slam_Core", 1.3)
    mat_haze = haze_material("Air_Slam_Haze")
    comets = []
    for name, ch in routes.items():
        L = ch.length
        for k in range(per_route + n_core + n_haze):
            core, haze = per_route <= k < per_route + n_core, k >= per_route + n_core
            t_arr = hit + (rng.uniform(-0.3, 1.2) if core else rng.uniform(-0.5, 4.0))
            margin = 0.002 + max(t_arr - hit, 0.0) * 0.004 + rng.uniform(0, 0.004)
            v = rng.uniform(*speed)
            back, tau = rng.uniform(0.03, 0.08), rng.uniform(2.5, 5.0)
            th0, helix, spin = rng.uniform(0, 2 * math.pi), rng.uniform(-30, 30), rng.choice([-1, 1]) * rng.uniform(0.15, 0.45)
            rho0 = rng.uniform(0.0, 0.3) if core or haze else rng.uniform(0.15, 0.7)
            wob, ph = rng.uniform(0.002, 0.006), rng.uniform(0, 2 * math.pi)
            w0 = haze_width if haze else core_width if core else rng.uniform(*width)
            track, widths = [], []
            for i in range(n_frames):
                t = i + 1
                if t <= t_arr:
                    s = L - margin - v * (t_arr - t)
                    after = 0.0
                else:
                    after = t - t_arr
                    s = (L - margin - back * (1 - math.exp(-after / tau))
                         + wob * math.sin(0.6 * after + ph) * math.exp(-after / 15.0))
                if s < 0:
                    track.append(None)
                    widths.append(0.0)
                    continue
                rho = rho0 + ((0.3 if haze else 0.8) - rho0) * (1 - math.exp(-after / 6.0))
                track.append(ch.at(s, th0 + helix * s + spin * after, rho))
                widths.append(w0 * (1.0 if not (core or haze) else 1.0 - 0.45 * _smooth(after / 10.0)))
            ob = comet(f"Air_{name}_{k:02d}", track, widths, mat_haze if haze else mat_core if core else mat, col,
                       parent, stretch=2.0 if haze else stretch, max_len=0.045 if haze else 0.03)
            if ob is not None:
                comets.append(ob)
    return comets, (P["nose_end"], P["lips_end"])


def swirl(aw, n_frames, col, parent, rng, count=72, width=(0.0011, 0.0019), core=8, core_width=0.0028, stretch=1.6):
    """The trapped air churning round inside her head: comets sweep back and forth along
    her nose, mouth and throat passages, spiralling round them."""
    bvh = walls(aw["walls"])
    P = aw["paths"]
    routes = [Channel(P["pharynx"] + P["nasal"], bvh), Channel(P["pharynx"][:2] + P["oral"], bvh),
              Channel(P["larynx"] + P["pharynx"], bvh)]
    weights = np.array([0.42, 0.4, 0.18])
    mat, mat_core = material("Air_Swirl"), material("Air_Swirl_Core", 1.25)
    comets = []
    for k in range(count + core):
        is_core = k >= count
        ch = routes[int(rng.choice(3, p=weights))]
        L = ch.length
        sc, amp = rng.uniform(0.25, 0.75) * L, rng.uniform(0.15, 0.32) * L
        om, ph, ph2 = rng.uniform(0.16, 0.3), rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)
        th0, spin = rng.uniform(0, 2 * math.pi), rng.choice([-1, 1]) * rng.uniform(0.25, 0.5)
        ph3 = rng.uniform(0, 2 * math.pi)
        w0 = core_width if is_core else rng.uniform(*width)
        track = []
        for i in range(n_frames):
            t = i + 1
            s = sc + amp * math.sin(om * t + ph) + 0.3 * amp * math.sin(2.3 * om * t + ph2)
            s = min(max(s, 0.003), L - 0.004)
            rho = (0.15 if is_core else 0.5) + 0.28 * math.sin(0.17 * t + ph3)
            track.append(ch.at(s, th0 + spin * t, max(rho, 0.0)))
        ob = comet(f"Air_Swirl_{k:02d}", track, [w0] * n_frames, mat_core if is_core else mat, col, parent,
                   stretch=stretch)
        comets.append(ob)
    return comets
