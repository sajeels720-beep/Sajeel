"""The brass pressure gauge (shot 11): a round brass case on a brass pipe, a cream dial marked
0-25 "x NORMAL" with a red zone from 15 up, a black needle, and a domed glass cover that
cracks (crack lines race out across it from where it gives way).

Real size: dial radius 5 cm. The gauge faces -Y (towards the camera), centred at the origin,
up +Z. Needle angles: 0 = straight up, positive = clockwise as you look at it (a turn about
+Y). value_angle() converts a reading to an angle.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import vfx_kit as V

H = V.hex_lin
DIAL_R = 0.05
MAX = 25.0
SWEEP = (-135.0, 135.0)          # needle angle at 0 and at MAX
RED_FROM = 15.0
DIAL_Y = -0.004                  # the dial face
GLASS_Y = (-0.0152, -0.0176)     # the glass at its rim and at its centre (domed towards the camera)
GLASS_R = 0.0522


def value_angle(v):
    return SWEEP[0] + (SWEEP[1] - SWEEP[0]) * v / MAX


def dial_point(v, r, y=DIAL_Y):
    a = math.radians(value_angle(v))
    return Vector((r * math.sin(a), y, r * math.cos(a)))


def glass_y(r):
    """Height of the glass dome (y) at a distance r from the centre."""
    t = min(r / GLASS_R, 1.0)
    return GLASS_Y[1] + (GLASS_Y[0] - GLASS_Y[1]) * t * t


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def lathe(name, profile, segments=128, col=None, smooth=True):
    """Revolve a profile [(radius, y), ...] round the gauge's axis (Y). A radius of 0 closes
    the shape at that end."""
    bm = bmesh.new()
    rings = []
    for r, y in profile:
        r = max(r, 1e-6)
        rings.append([bm.verts.new((r * math.sin(2 * math.pi * k / segments), y, r * math.cos(2 * math.pi * k / segments)))
                      for k in range(segments)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(segments):
            bm.faces.new((r0[k], r1[k], r1[(k + 1) % segments], r0[(k + 1) % segments]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = V.link(bpy.data.objects.new(name, me), col)
    me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
    return ob


def _box(bm, centre, size, rot):
    """A box in a bmesh: centre, size (x, y, z), rotation matrix (3x3)."""
    res = bmesh.ops.create_cube(bm, size=1.0)
    M = Matrix.Translation(Vector(centre)) @ rot.to_4x4() @ Matrix.Diagonal(Vector((*size, 1.0)))
    bmesh.ops.transform(bm, matrix=M, verts=res["verts"])


def _turn(deg):
    return Matrix.Rotation(math.radians(deg), 3, "Y")


def _text(name, body, at, size, mat, col, bold=False):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    if bold:
        cu.offset = 0.0
        cu.extrude = 0.0
        cu.bevel_depth = size * 0.012                             # a little heavier strokes
    ob = V.link(bpy.data.objects.new(name, cu), col)
    ob.location = at
    ob.rotation_euler = (math.radians(90), 0.0, 0.0)              # lie on the dial, facing -Y, upright
    V.assign(ob, mat)
    return ob


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
def materials():
    brass = V.principled("Gauge_Brass", H("#C99A3A"), rough=0.24, metal=1.0, spec=0.5)
    V.color_variation(brass, H("#8E6A26"), scale=180.0, amount=0.35)
    V.bump(brass, scale=900.0, strength=0.06, distance=0.0002)
    glass = bpy.data.materials.new("Gauge_Glass")
    if getattr(glass, "node_tree", None) is None:
        glass.use_nodes = True
    nt = glass.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    fr = nt.nodes.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.25
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.03
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.97, 0.98, 1.0, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = "MULTIPLY_ADD"
    nt.links.new(fr.outputs["Fresnel"], m.inputs[0])
    m.inputs[1].default_value, m.inputs[2].default_value = 0.85, 0.06    # always a faint sheen
    nt.links.new(m.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    V._blended(glass)
    crack = V.principled("Gauge_Crack", H("#FFFFFF"), rough=0.1, spec=0.9, emission=H("#E8F4FF"),
                         emission_strength=0.35)                  # hairlines that catch the light
    return {
        "brass": brass,
        "dark_brass": V.principled("Gauge_Brass_Dark", H("#8F6A27"), rough=0.32, metal=1.0),
        "dial": V.principled("Gauge_Dial", H("#F2EADB"), rough=0.55),
        "ink": V.principled("Gauge_Ink", H("#161616"), rough=0.6),
        "red": V.principled("Gauge_Red", H("#B5121B"), rough=0.5),
        "needle": V.principled("Gauge_Needle", H("#121212"), rough=0.3, coat=0.4),
        "glass": glass,
        "crack": crack,
    }


# --------------------------------------------------------------------------
# The gauge
# --------------------------------------------------------------------------
def build(col_name="SET_GAUGE", pipe_length=0.5):
    """Build the gauge. Returns dict(root, needle (turns about its local Y), glass, mats)."""
    col = V.collection(col_name)
    mats = materials()
    root = V.link(bpy.data.objects.new("Gauge", None), col)
    parts = []

    # case: a brass cup with a rounded bezel holding the glass
    case = lathe("Gauge_Case", [(0.0, 0.013), (0.054, 0.013), (0.0575, 0.010), (0.0585, 0.004), (0.0585, -0.009),
                                (0.0602, -0.0115), (0.061, -0.0155), (0.0595, -0.0192), (0.0565, -0.0205),
                                (0.0538, -0.0196), (0.0528, -0.0172), (0.0525, -0.012), (0.0518, -0.006),
                                (0.0512, DIAL_Y - 0.0004)], col=col)
    V.assign(case, mats["brass"])
    parts.append(case)
    # the dial
    dial = lathe("Gauge_Dial", [(0.0, DIAL_Y), (0.0513, DIAL_Y)], col=col)
    V.assign(dial, mats["dial"])
    parts.append(dial)
    # ticks: every 1, longer every 5
    bm = bmesh.new()
    for v in range(0, int(MAX) + 1):
        major = v % 5 == 0
        length, width = (0.0075, 0.0011) if major else (0.0038, 0.00045)
        c = dial_point(v, 0.0455 - length / 2, DIAL_Y - 0.00012)
        _box(bm, c, (width, 0.0002, length), _turn(value_angle(v)))
    for v in np.arange(0.5, MAX, 1.0):                            # half ticks
        c = dial_point(v, 0.0455 - 0.0012, DIAL_Y - 0.00012)
        _box(bm, c, (0.0003, 0.0002, 0.0024), _turn(value_angle(v)))
    me = bpy.data.meshes.new("Gauge_Ticks")
    bm.to_mesh(me)
    bm.free()
    ticks = V.link(bpy.data.objects.new("Gauge_Ticks", me), col)
    V.assign(ticks, mats["ink"])
    parts.append(ticks)
    # the red zone: an arc band under the outer end of the ticks
    bm = bmesh.new()
    steps = 60
    inner, outer = 0.0418, 0.0472
    ring = []
    for i in range(steps + 1):
        v = RED_FROM + (MAX - RED_FROM) * i / steps
        ring.append((bm.verts.new(dial_point(v, inner, DIAL_Y - 0.00006)), bm.verts.new(dial_point(v, outer, DIAL_Y - 0.00006))))
    for (a, b), (c, d) in zip(ring, ring[1:]):
        bm.faces.new((a, c, d, b))
    me = bpy.data.meshes.new("Gauge_Red_Zone")
    bm.to_mesh(me)
    bm.free()
    red = V.link(bpy.data.objects.new("Gauge_Red_Zone", me), col)
    V.assign(red, mats["red"])
    parts.append(red)
    # numbers and labels
    for v in range(0, int(MAX) + 1, 5):
        parts.append(_text(f"Gauge_Num_{v}", str(v), dial_point(v, 0.0322, DIAL_Y - 0.0002), 0.0072, mats["ink"], col,
                           bold=True))
    parts.append(_text("Gauge_Label", "AIR PRESSURE", Vector((0.0, DIAL_Y - 0.0002, 0.0165)), 0.0042, mats["ink"], col,
                       bold=True))
    parts.append(_text("Gauge_Unit", "x NORMAL", Vector((0.0, DIAL_Y - 0.0002, -0.0225)), 0.0048, mats["red"], col,
                       bold=True))
    # stop pin just past the end of the scale
    pin = lathe("Gauge_Stop_Pin", [(0.0, DIAL_Y - 0.0045), (0.0011, DIAL_Y - 0.0045), (0.0011, DIAL_Y)], segments=24,
                col=col)
    pin.location = dial_point(MAX + 1.1, 0.0405, 0.0)
    V.assign(pin, mats["brass"])
    parts.append(pin)
    # the needle: a tapered black pointer with a short tail, on a brass hub
    needle = V.link(bpy.data.objects.new("Gauge_Needle", None), col)
    needle.location = (0.0, DIAL_Y - 0.0034, 0.0)
    needle.rotation_mode = "XYZ"
    bm = bmesh.new()
    outline = [(0.0, 0.0432), (0.0009, 0.03), (0.0019, 0.0), (0.0024, -0.0085), (0.0, -0.0118), (-0.0024, -0.0085),
               (-0.0019, 0.0), (-0.0009, 0.03)]
    front = [bm.verts.new((x, -0.0004, z)) for x, z in outline]
    back = [bm.verts.new((x, 0.0004, z)) for x, z in outline]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Gauge_Pointer")
    bm.to_mesh(me)
    bm.free()
    pointer = V.link(bpy.data.objects.new("Gauge_Pointer", me), col)
    pointer.parent = needle
    V.assign(pointer, mats["needle"])
    hub = lathe("Gauge_Hub", [(0.0, -0.0026), (0.0028, -0.0022), (0.0036, -0.0008), (0.0037, 0.0030)], segments=48,
                col=col)
    hub.location = (0.0, DIAL_Y - 0.0034, 0.0)
    V.assign(hub, mats["brass"])
    parts.append(hub)
    # the glass cover, domed towards the camera
    prof = [(GLASS_R * (1 - t), glass_y(GLASS_R * (1 - t))) for t in np.linspace(0, 1, 24)]
    glass = lathe("Gauge_Glass", prof, col=col)
    V.assign(glass, mats["glass"])
    # the stem: a hex nut and a pipe going down out of shot
    nut = lathe("Gauge_Nut", [(0.0, 0.006), (0.0125, 0.006), (0.0125, -0.006), (0.0, -0.006)], segments=6, col=col,
                smooth=False)
    nut.rotation_euler = (math.radians(-90), 0.0, 0.0)            # the lathe's axis turned to point down
    nut.location = (0.0, 0.0, -0.064)
    V.assign(nut, mats["brass"])
    stem = lathe("Gauge_Stem", [(0.0, 0.0), (0.0075, 0.0), (0.0075, 0.014), (0.0, 0.014)], segments=48, col=col)
    stem.rotation_euler = (math.radians(-90), 0.0, 0.0)
    stem.location = (0.0, 0.0, -0.058)
    V.assign(stem, mats["brass"])
    pipe = lathe("Gauge_Pipe", [(0.0, 0.0), (0.0062, 0.0), (0.0062, pipe_length), (0.0, pipe_length)], segments=48, col=col)
    pipe.rotation_euler = (math.radians(-90), 0.0, 0.0)
    pipe.location = (0.0, 0.0, -0.07)
    V.assign(pipe, mats["dark_brass"])
    for o in parts + [needle, glass, nut, stem, pipe]:
        if o.parent is None:
            o.parent = root
    return {"root": root, "needle": needle, "glass": glass, "mats": mats, "col": col}


def key_needle(needle, keys, jitter=0.0):
    """keys = [(frame, reading)]; the needle turns to each reading (eased), with an optional
    nervous quiver (degrees) on top."""
    for f, v in keys:
        needle.rotation_euler = (0.0, math.radians(value_angle(v)), 0.0)
        needle.keyframe_insert("rotation_euler", frame=f, index=1)
    V.ease_id(needle)
    if jitter:
        V.noise_on(needle, "rotation_euler", math.radians(jitter), scale=2.5, seed=7)


# --------------------------------------------------------------------------
# Cracks
# --------------------------------------------------------------------------
def _on_glass(x, z):
    return Vector((x, glass_y(math.hypot(x, z)) - 0.00025, z))


def cracks(g, impact, start, rng, radial=7, mat=None, col=None, width=0.00007):
    """Crack lines racing out across the glass from `impact` (x, z on the dial plane) on
    frame `start`: jagged radial cracks to the rim, then the web of cross cracks between
    them a frame or two later. Returns the crack objects."""
    col = col or g["col"]
    mat = mat or g["mats"]["crack"]
    p0 = np.asarray(impact, float)
    lines = []
    dirs = np.sort(rng.uniform(0, 2 * math.pi, radial) + np.linspace(0, 2 * math.pi, radial, endpoint=False) * 0.6)
    rad_paths = []
    for a in dirs:
        p, d = p0.copy(), np.array([math.cos(a), math.sin(a)])
        pts = [p.copy()]
        while np.linalg.norm(p) < GLASS_R - 0.0015 and len(pts) < 40:
            d = d + rng.normal(0, 0.35, 2)
            d /= np.linalg.norm(d)
            p = p + d * rng.uniform(0.0025, 0.0055)
            pts.append(p.copy())
        rad_paths.append(pts)
        lines.append((pts, start + rng.uniform(0, 1.5), rng.uniform(2.0, 3.5), width * rng.uniform(0.8, 1.3)))
    for i in range(len(rad_paths)):                               # the web: cross cracks between neighbours
        a, b = rad_paths[i], rad_paths[(i + 1) % len(rad_paths)]
        for frac in (0.18, 0.4):
            ia, ib = int(frac * (len(a) - 1)), int(frac * (len(b) - 1))
            if rng.uniform() < 0.6:
                mid = (a[ia] + b[ib]) / 2 + rng.normal(0, 0.0012, 2)
                lines.append(([a[ia], mid, b[ib]], start + 2 + rng.uniform(0, 1.5), 1.5, width * 0.7))
    obs = []
    for k, (pts, f0, dur, width) in enumerate(lines):
        cu = bpy.data.curves.new(f"Gauge_Crack_{k:02d}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = width
        cu.bevel_resolution = 1
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, (x, z) in enumerate(pts):
            sp.points[i].co = (*_on_glass(x, z), 1.0)
        cu.bevel_factor_mapping_end = "SPLINE"
        cu.bevel_factor_end = 0.0
        cu.keyframe_insert("bevel_factor_end", frame=int(f0))
        cu.bevel_factor_end = 1.0
        cu.keyframe_insert("bevel_factor_end", frame=int(f0 + dur))
        V.ease_id(cu, "QUAD", "EASE_OUT")
        ob = V.link(bpy.data.objects.new(cu.name, cu), col)
        V.assign(ob, mat)
        ob.parent = g["root"]
        obs.append(ob)
    # a frosted chip where it gave way
    chip = lathe("Gauge_Crack_Chip", [(0.0, 0.0), (0.0013, 0.0001), (0.0, 0.0002)], segments=7, col=col, smooth=False)
    chip.location = _on_glass(*p0)
    chip.rotation_euler = (0.0, rng.uniform(0, 6.28), 0.0)
    V.assign(chip, mat)
    chip.parent = g["root"]
    V.visible(chip, [(1, False), (start, True)])
    obs.append(chip)
    return obs
