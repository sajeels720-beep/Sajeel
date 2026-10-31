"""A car wheel for shot 14 ("like tyre treads"), on the studio blue: a clean rain tyre with deep
grooves (three running round it, and V-shaped channels that pump water out to its sides) on a
simple five-spoke alloy wheel, rolling along a strip of wet road through a sheet of water;
water jets out of the grooves at its sides and flicks up behind it.

Everything is modelled here (no logos, no brand). Real size in metres: the tyre is 0.64 m
across; the wheel rolls along +X with its axle along Y; the camera side is -Y.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
R_OUT, HALF_W, R_RIM = 0.32, 0.092, 0.212
GROOVES = (-0.05, 0.0, 0.05)              # round the tyre (centre lines, metres from the middle)
CHEVRONS, SWEEP = 56, 2.4                 # V-shaped channels round the tyre; how far back they sweep (rad/m)
DEPTH = 0.011


def _tread_radius(theta, y):
    """Radius of the tread at angle theta, across position y: grooves cut in, shoulders round off."""
    g = np.zeros_like(theta)
    for c in GROOVES:
        g = np.maximum(g, np.clip(1.0 - (np.abs(y - c) - 0.0045) / 0.0025, 0, 1))
    pitch = 2 * math.pi / CHEVRONS
    ph = (theta - SWEEP * np.abs(y)) % pitch                                # the V sweeps back from the middle
    arc = np.minimum(ph, pitch - ph) * R_OUT
    lateral = np.clip(1.0 - (arc - 0.0028) / 0.002, 0, 1) * (np.abs(y) > 0.012) * (np.abs(y) < 0.084)
    g = np.maximum(g, lateral)
    shoulder = 0.016 * np.clip((np.abs(y) - 0.068) / 0.024, 0, 1) ** 2
    return R_OUT - DEPTH * g - shoulder


def tyre(col, n_theta=900, n_y=90):
    """The tyre: tread (with real grooves) and sidewalls, one closed ring. Returns the object."""
    th = np.linspace(0, 2 * math.pi, n_theta, endpoint=False)
    ys = np.linspace(-HALF_W, HALF_W, n_y)
    T, Y = np.meshgrid(th, ys)                                              # rows: across, cols: round
    R = _tread_radius(T, Y)
    side = [(0.098, 0.292), (0.1015, 0.272), (0.0985, 0.248), (0.09, 0.228), (0.083, R_RIM)]
    rows = [np.stack([R * np.sin(T), Y, -R * np.cos(T)], -1)]               # tread, from -y to +y
    verts = [rows[0].reshape(-1, 3)]
    profile_neg = [(-y, r) for y, r in side]
    profile_pos = side
    rings_neg = [np.stack([r * np.sin(th), np.full_like(th, y), -r * np.cos(th)], -1) for y, r in profile_neg]
    rings_pos = [np.stack([r * np.sin(th), np.full_like(th, y), -r * np.cos(th)], -1) for y, r in profile_pos]
    allrows = rings_neg[::-1] + list(rows[0]) + rings_pos                    # from the inner -y rim edge to the +y one
    V3 = np.vstack(allrows)
    nr = len(allrows)
    faces = []
    for i in range(nr - 1):
        for j in range(n_theta):
            a, b = i * n_theta + j, i * n_theta + (j + 1) % n_theta
            faces.append((a, b, b + n_theta, a + n_theta))
    me = bpy.data.meshes.new("Tyre")
    me.from_pydata([tuple(v) for v in V3], [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = V.link(bpy.data.objects.new("Tyre", me), col)
    me.update()
    f = me.polygons[(n_y // 2 + len(rings_neg)) * n_theta]                 # a tread face: must point outwards
    if f.normal.dot(f.center - Vector((0, f.center.y, 0))) < 0:
        me.flip_normals()
    m = V.principled("Tyre_Rubber", H("#1B1B1D"), rough=0.6, spec=0.4, coat=0.55)
    b = V.bsdf(m)
    if V._inp(b, "Coat Roughness") is not None:
        V._inp(b, "Coat Roughness").default_value = 0.08                    # wet
    V.bump(m, scale=400.0, strength=0.12, distance=0.0008)
    V.assign(ob, m)
    return ob


def _box(name, corners, col, mat):
    """A hexahedron from 8 corners (bottom 4 then top 4, counter-clockwise), bevelled."""
    me = bpy.data.meshes.new(name)
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata([tuple(c) for c in corners], [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = V.link(bpy.data.objects.new(name, me), col)
    bv = ob.modifiers.new("Bevel", "BEVEL")
    bv.width, bv.segments = 0.006, 3
    V.assign(ob, mat)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def wheel(col):
    """A five-spoke alloy wheel (its outside face towards -y). Returns the objects."""
    alloy = V.principled("Alloy", H("#C9CED6"), rough=0.22, metal=1.0, spec=0.5, coat=0.3)
    dark = V.principled("Alloy_Dark", H("#3A3D42"), rough=0.35, metal=1.0)
    obs = []
    barrel = K.tube("Rim_Barrel", [(0, -0.075, 0), (0, 0.075, 0)], [R_RIM - 0.004] * 2, segments=96, col=col)
    V.assign(barrel, dark)
    obs.append(barrel)
    th = np.linspace(0, 2 * math.pi, 129)
    ring = [(R_RIM * math.sin(a), -0.078, -R_RIM * math.cos(a)) for a in th]
    lip = K.tube("Rim_Lip", ring, [0.009] * len(ring), segments=16, col=col)
    V.assign(lip, alloy)
    obs.append(lip)
    hub = K.tube("Hub", [(0, -0.05, 0), (0, -0.082, 0)], [0.068, 0.062], segments=64, col=col)
    V.assign(hub, alloy)
    obs.append(hub)
    cap = K.ellipsoid("Hub_Cap", (0, -0.082, 0), (0.034, 0.012, 0.034), segments=32, col=col)
    V.assign(cap, alloy)
    obs.append(cap)
    for k in range(5):
        a = 2 * math.pi * k / 5
        nut = K.tube(f"Lug_{k}", [(0.045 * math.sin(a + 0.63), -0.08, -0.045 * math.cos(a + 0.63)),
                                  (0.045 * math.sin(a + 0.63), -0.09, -0.045 * math.cos(a + 0.63))], [0.0075] * 2,
                     segments=6, col=col)
        V.assign(nut, dark)
        obs.append(nut)
        u = Vector((math.sin(a), 0, -math.cos(a)))
        s = Vector((math.cos(a), 0, math.sin(a)))
        corners = []
        for ylev, (r0, r1, w0, w1) in ((-0.052, (0.06, R_RIM - 0.008, 0.032, 0.02)),
                                       (-0.078, (0.06, R_RIM - 0.008, 0.026, 0.016))):
            corners += [u * r0 - s * w0 + Vector((0, ylev, 0)), u * r1 - s * w1 + Vector((0, ylev - 0.006, 0)),
                        u * r1 + s * w1 + Vector((0, ylev - 0.006, 0)), u * r0 + s * w0 + Vector((0, ylev, 0))]
        obs.append(_box(f"Spoke_{k}", corners, col, alloy))
    return obs


def road(col, length=12.0, x0=-3.0, y=(-3.0, 1.1)):
    """A strip of wet asphalt (dark, with stones in it and a shine of water)."""
    me = bpy.data.meshes.new("Road")
    me.from_pydata([(x0, y[0], 0), (x0 + length, y[0], 0), (x0 + length, y[1], 0), (x0, y[1], 0)], [], [(0, 1, 2, 3)])
    ob = V.link(bpy.data.objects.new("Road", me), col)
    m = V.principled("Wet_Asphalt", H("#2C2C2E"), rough=0.55, spec=0.5, coat=0.7)
    b = V.bsdf(m)
    nt = m.node_tree
    if V._inp(b, "Coat Roughness") is not None:
        V._inp(b, "Coat Roughness").default_value = 0.05
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 140.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*H("#1D1D1F"), 1)
    ramp.color_ramp.elements[1].color = (*H("#4A4A4C"), 1)
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    V.bump(m, scale=140.0, strength=0.35, distance=0.002)
    V.assign(ob, m)
    return ob


def water_sheet(col, x=(-0.6, 4.5), y=(-2.9, 1.05), z=0.004):
    """A thin sheet of water lying on the road where the wheel rolls through."""
    import pool_set as PS
    me = bpy.data.meshes.new("Water_Sheet")
    me.from_pydata([(x[0], y[0], z), (x[1], y[0], z), (x[1], y[1], z), (x[0], y[1], z)], [], [(0, 1, 2, 3)])
    ob = V.link(bpy.data.objects.new("Water_Sheet", me), col)
    V.assign(ob, PS.water_material("Road_Water", tint=H("#E8F4F4"), ripple=0.35, chop=0.6))
    return ob


def build(col=None):
    """The wheel (tyre + alloy) under a "Wheel" empty at the axle, the road and the water."""
    col = col or V.collection("WHEEL")
    root = V.link(bpy.data.objects.new("Wheel", None), col)
    root.rotation_mode = "XYZ"
    parts = [tyre(col)] + wheel(col)
    for o in parts:
        o.parent = root
    return {"root": root, "parts": parts, "road": road(col), "water": water_sheet(col)}


def roll(root, x_at, frames):
    """Roll the wheel along +X: x_at(frame) -> axle x. It turns as it goes (no slipping)."""
    for f in frames:
        x = x_at(f)
        root.location = (x, 0.0, R_OUT - 0.004)                          # sits a little into the water
        root.rotation_euler = (0.0, x / R_OUT, 0.0)
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
    V.ease_id(root, "LINEAR")


def bow_wave(root_x, frames, col=None):
    """Water piling up in front of the tyre where it ploughs through the sheet: a low crescent
    ridge that travels with the wheel (it does not turn with it)."""
    import pool_set as PS
    col = col or V.collection("SPRAY")
    th = np.linspace(-1.25, 1.25, 41)
    pts = [(0.06 * math.cos(t) + 0.02, 0.105 * math.sin(t), 0.004) for t in th]
    rad = [0.004 + 0.009 * math.cos(t * 0.9) ** 2 for t in th]
    ob = K.tube("Bow_Wave", pts, rad, segments=16, col=col)
    V.assign(ob, bpy.data.materials.get("Road_Water") or PS.water_material("Road_Water"))
    for f in frames:
        ob.location = (root_x(f), 0.0, 0.0)
        ob.keyframe_insert("location", frame=f)
    V.ease_id(ob, "LINEAR")
    return ob


def spray(x_at, frames, col=None, seed=11, side=24, rear=14):
    """Water thrown out of the grooves: fans out of both sides of the tyre where it meets the
    road, and a tail flicked up behind it. Streaky drops (comets) that fall back down."""
    import air_fx as AF
    rng = np.random.default_rng(seed)
    col = col or V.collection("SPRAY")
    mat = V.principled("Spray_Water", H("#F2FAFF"), rough=0.04, spec=0.9, transmission=0.55, ior=1.33,
                       emission=H("#FFFFFF"), emission_strength=0.35)               # white water: reads on the blue
    fps = bpy.context.scene.render.fps
    f0, f1 = frames[0], frames[-1]
    n = 0
    for f in frames:
        x = x_at(f)
        v_wheel = (x_at(f + 1) - x_at(f - 1)) * fps / 2
        jets = []
        for sgn in (-1, 1):
            for _ in range(side):
                p = Vector((x + rng.uniform(-0.04, 0.05), sgn * rng.uniform(0.085, 0.1), rng.uniform(0.003, 0.02)))
                v = Vector((v_wheel * rng.uniform(0.0, 0.3), sgn * rng.uniform(1.0, 2.8), rng.uniform(0.6, 1.9)))
                jets.append((p, v, rng.uniform(0.0025, 0.0065)))
        for _ in range(rear):
            p = Vector((x - rng.uniform(0.04, 0.12), rng.uniform(-0.08, 0.08), rng.uniform(0.01, 0.05)))
            v = Vector((v_wheel * rng.uniform(0.15, 0.5), rng.uniform(-0.35, 0.35), rng.uniform(0.9, 2.1)))
            jets.append((p, v, rng.uniform(0.003, 0.007)))
        for p, v, w in jets:
            track, widths = [], []
            for g in range(f0, f1 + 1):
                t = (g - f + rng.uniform(0, 1)) / fps
                if t < 0:
                    track.append(None)
                    widths.append(0.0)
                    continue
                q = p + v * t + Vector((0, 0, -4.905 * t * t))
                if q.z < 0.0 or t > 0.5:
                    track.append(None)
                    widths.append(0.0)
                    continue
                track.append(q)
                widths.append(w)
            if any(q is not None for q in track):
                AF.comet(f"Spray_{n:04d}", track, widths, mat, col, stretch=0.8, max_len=0.09, first_frame=f0)
                n += 1
    return n
