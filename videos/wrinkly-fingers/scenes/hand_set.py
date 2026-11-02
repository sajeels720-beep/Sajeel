"""His hand alone on the studio blue (shots 04-05): palm up, the fingertips already wrinkled.

build() makes him with only his right forearm and hand kept (at full detail), holds the hand out
open, palm up, in front of him and returns where the fingertip pads are. For shot 04,
soak_drop() drops water on a fingertip that soaks into the skin (the idea most people have), and
question_icon() pops up his red "?". For shot 05, xray() turns the skin to glass with a scan
line running from the wrist to the fingertips, bones() builds the glowing bones inside (they
show where the line has passed) and nerves() the yellow nerves that light up from the wrist
into every fingertip, with pulses racing along them. Bones and nerves are fitted inside his
skin with ray casts (skin_bvh), so nothing pokes out of the fingertips.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import acting as A
import claude_sculpt_kit as K
import pool_acting as PA
import swimmer as SW
import vfx_kit as V
import wrinkles as WR
import xray_body as XB

H = V.hex_lin
FINGERS = (1, 2, 3, 4, 5)
NERVE = H("#FFC93A")                # warm yellow (brighter yellows turn white under AgX)
BONE = H("#E8F1F7")
RED = H("#8E040C")                  # his warning red, as in videos 1 and 2

# An open hand held out palm up: how far each finger bends at its three joints (degrees, from
# the bone before it). MPFB's rest pose is already curled 8-25 degrees at the knuckles, so
# open_hand() works out the curl that gives these bends (RELAXED_HAND on top of the rest pose
# cupped this hand, the fingertips pointing up).
OPEN_HAND = {"index": (6, 8, 5), "middle": (8, 10, 6), "ring": (10, 12, 7), "little": (12, 14, 8)}
OPEN_THUMB = (4, 10, 8)


def build(wrinkled=1.0, levels=3):
    """Him, but only his right forearm and hand, palm up in front of his chest. Returns
    dict(hero, skin (BVH of his skin), wrist, palm (centre of the palm), up (out of the palm),
    along (towards the fingertips), across, tips {finger: (pad point, pad normal)},
    ends {finger: the fingertip's end})."""
    hero = SW.build(brand=False)
    WR.setup(hero)
    WR.set_amount(hero, wrinkled)
    bpy.context.view_layer.update()
    sR = PA.joint(hero, "upperarm01.R")
    PA.pose_arm(hero, "R", (sR.x + 0.02, sR.y - 0.38, sR.z - 0.3), fingers=(0.08, -1.0, 0.06), palm=(0.0, 0.05, 1.0),
                pole=(-0.7, 0.3, -1.0))
    open_hand(hero, "R")
    bpy.context.view_layer.update()
    skin = skin_bvh(hero)                      # before dense(): the same surface, far fewer faces
    frame = hand_frame(hero, "R", skin)
    WR.dense(hero, levels=levels, sides=("R",))
    bpy.context.view_layer.update()
    return {"hero": hero, "skin": skin, **frame}


def _flex(rig, name):
    """How far a bone bends from its parent in the rest pose (degrees, + towards the palm)."""
    b = rig.data.bones[name]
    M, P = b.matrix_local.to_3x3(), b.parent.matrix_local.to_3x3()
    y = M.col[1].normalized()
    return math.degrees(math.atan2(y.dot(P.col[2].normalized()), y.dot(P.col[1].normalized())))


def open_hand(hero, side="R", bends=OPEN_HAND, thumb=OPEN_THUMB, together=0.7):
    """Shape the fingers so they bend `bends` at each joint (fingers a little apart)."""
    rig = hero["rig"]
    curl = {"thumb": thumb}
    for finger, angles in bends.items():
        curl[finger] = tuple(a - _flex(rig, f"{b}.{side}") for b, a in zip(A.FINGERS[finger], angles))
    PA.hand_shape(hero, side, curl, together=together)


def skin_bvh(hero):
    """His skin as it is now (evaluated, world space), for ray casts."""
    body = hero["body"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    M = body.matrix_world
    verts = [M @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def _section(skin, p, x, z, reach=0.06):
    """Distances from p (inside him) to his skin along +x, -x, +z, -z."""
    out = []
    for d in (x, -x, z, -z):
        hit = skin.ray_cast(p, d, reach)
        out.append(hit[3] if hit[0] is not None else reach)
    return out


def _inside(skin, p, x, z, dorsal=0.2):
    """Centre a point in the flesh around it: side to side, and `dorsal` of the way towards the
    back of the hand (-z), like real bones. Returns (point, room to the nearest skin)."""
    dx1, dx2, dz1, dz2 = _section(skin, p, x, z)
    hw, ht = (dx1 + dx2) / 2, (dz1 + dz2) / 2
    c = p + x * ((dx1 - dx2) / 2) + z * ((dz1 - dz2) / 2 - dorsal * ht)
    return c, min(hw, ht * (1.0 - dorsal))


def hand_frame(hero, side="R", skin=None):
    rig = hero["rig"]
    W = rig.matrix_world
    j = lambda n: W @ rig.pose.bones[f"{n}.{side}"].head
    wrist = j("wrist")
    knuckles = sum((j(f"finger{k}-1") for k in (2, 3, 4, 5)), Vector()) / 4
    along = (knuckles - wrist).normalized()
    across = (j("finger2-1") - j("finger5-1")).normalized()
    up = along.cross(across).normalized()
    if up.z < 0:
        up = -up
    tips, ends = {}, {}
    for k in FINGERS:
        pb = rig.pose.bones[f"finger{k}-3.{side}"]
        M = (W @ pb.matrix).to_3x3()
        y, z = M.col[1].normalized(), M.col[2].normalized()
        h, t = W @ pb.head, W @ pb.tail
        mid = h.lerp(t, 0.5)
        hit = skin.ray_cast(mid, z, 0.04) if skin else (None,)
        if hit[0] is not None:                                   # the middle of the pad, on the skin
            n = hit[1].normalized()
            tips[k] = (hit[0], n if n.dot(z) > 0 else -n)
        else:
            tips[k] = (mid + z * 0.0065, z)
        e = skin.ray_cast(h, y, 0.06) if skin else (None,)
        ends[k] = e[0] if e[0] is not None else t
    return {"wrist": wrist, "palm": wrist.lerp(knuckles, 0.55) + up * 0.012, "up": up, "along": along,
            "across": across, "tips": tips, "ends": ends}


# --------------------------------------------------------------------------
# Shot 04: water soaking in, and the "?"
# --------------------------------------------------------------------------
def drop_material(name="Skin_Drop"):
    """Clear water for drops seen up close: real refraction (they magnify the skin under them)
    and sharp highlights, in both engines."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = V.principled(name, H("#E6F5FF"), rough=0.01, spec=1.0, transmission=1.0, ior=1.33)
        for prop, val in (("surface_render_method", "DITHERED"), ("use_raytrace_refraction", True),
                          ("thickness_mode", "SPHERE")):
            if hasattr(mat, prop):
                setattr(mat, prop, val)
    return mat


def soak_drop(name, start, target, normal, height=0.2, radius=0.004, col=None):
    """A drop falls onto the skin at `target` and soaks in: it spreads flat and sinks away.
    Returns the frame it lands."""
    col = col or V.collection("FX")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=24, ring_count=14, location=target)
    ob = bpy.context.active_object
    ob.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(drop_material())
    n = Vector(normal).normalized()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = n.to_track_quat("Z", "Y")
    fps = bpy.context.scene.render.fps
    fall = math.sqrt(2 * height / 9.81)
    land = start + max(2, round(fall * fps))
    ob.scale = (0, 0, 0)
    ob.keyframe_insert("scale", frame=start - 1)
    for f in range(start, land + 1):
        t = min((f - start) / fps, fall)
        ob.location = target + Vector((0, 0, height - 4.905 * t * t)) + n * radius * 0.6
        st = 1.0 + min(1.5, 9.81 * t * 0.4)
        ob.scale = (1 / math.sqrt(st), 1 / math.sqrt(st), st)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("scale", frame=f)
    for f, s, dz in ((land + 1, (1.4, 1.4, 0.62), 0.15), (land + 3, (1.3, 1.3, 0.58), 0.05), (land + 9, (0.9, 0.9, 0.28), -0.25),
                     (land + 13, (0.0, 0.0, 0.0), -0.5)):          # lands as a dome, then soaks away
        ob.location = target + n * radius * dz
        ob.scale = s
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("scale", frame=f)
    V.ease_id(ob, "LINEAR")
    return land


def catch_light(target, normal, cam, dist=0.6, size=0.06, power=6.0):
    """A small light that only shows in reflections (no diffuse light): it puts a bright
    highlight in the drops (and the wet skin) at `target`, seen from `cam`."""
    n, v = Vector(normal).normalized(), (Vector(cam) - Vector(target)).normalized()
    r = 2 * n.dot(v) * n - v
    li = bpy.data.lights.new("Catch_Light", "AREA")
    li.size, li.energy = size, power
    if hasattr(li, "diffuse_factor"):
        li.diffuse_factor, li.volume_factor = 0.0, 0.0
    ob = V.link(bpy.data.objects.new("Catch_Light", li), V.collection("LIGHTS"))
    ob.location = Vector(target) + r * dist
    ob.rotation_euler = (-r).to_track_quat("-Z", "Y").to_euler()
    for prop in ("visible_diffuse", "visible_volume_scatter", "visible_camera"):
        if hasattr(ob, prop):
            setattr(ob, prop, False)
    return ob


def screen_point(cam, aim, lens, p):
    """Where a world point lands on screen (x right, y up, -1..1) for a camera at `cam` looking
    at `aim` (the same frame as question_icon)."""
    f = (aim - cam).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f)
    d = Vector(p) - cam
    t = 18.0 / lens
    return (d.dot(r) / d.dot(f) / (t * 9 / 16), d.dot(u) / d.dot(f) / t)


def free_spot(cam, aim, lens, points, spots=((0.5, 0.58), (-0.5, 0.58), (0.0, 0.66), (0.5, -0.55), (-0.5, -0.55))):
    """The screen spot (from `spots`) furthest from all `points` (world): where the "?" goes."""
    sp = [screen_point(cam, aim, lens, p) for p in points]
    return max(spots, key=lambda s: min(math.hypot(s[0] - x, s[1] - y) for x, y in sp))


def question_icon(col, cam, aim, lens, screen=(0.55, 0.42), depth=0.35, height=0.2, pop=10):
    """His red "?" popping up at a screen position (x right, y up, -1..1), `depth` metres in
    front of the lens, `height` of the frame tall, with red ripple rings. Returns the icon."""
    f = (aim - cam).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f)
    t = 18.0 / lens
    at = cam + f * depth + r * (screen[0] * depth * t * 9 / 16) + u * (screen[1] * depth * t)
    size = height * 2 * depth * t
    cu = bpy.data.curves.new("Question_Mark", "FONT")
    cu.body = "?"
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.size, cu.extrude, cu.bevel_depth, cu.offset = size, size * 0.09, size * 0.025, size * 0.03
    ob = V.link(bpy.data.objects.new("Question_Mark", cu), col)
    ob.location = at
    ob.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
    mat = V.principled("Question_Red", RED, rough=0.3, coat=0.5, emission=H("#FF0A04"), emission_strength=0.35)
    V.assign(ob, mat)
    V.key(ob, "scale", [(1, (0.001,) * 3), (pop, (0.001,) * 3), (pop + 4, (1.25,) * 3), (pop + 7, (0.94,) * 3),
                        (pop + 9, (1.0,) * 3)])
    base = ob.rotation_euler.copy()
    for fr, deg in ((pop + 4, 10), (pop + 7, -7), (pop + 10, 3), (pop + 13, 0)):   # a little wobble as it lands
        ob.rotation_euler = (base.to_matrix() @ Matrix.Rotation(math.radians(deg), 3, "Z")).to_euler()
        ob.keyframe_insert("rotation_euler", frame=fr)
    V.ease_id(ob)
    V.ripple_rings("Question_Ring", at + f * 0.012, -f, pop + 1, count=3, interval=6, life=18,
                   radius=size * 0.9, thickness=0.05, color=H("#B00C08"), strength=2.5, col=col)
    return ob


# --------------------------------------------------------------------------
# Shot 05: the x-ray, the bones and the nerves
# --------------------------------------------------------------------------
def _progress(nt, origin, axis, length):
    """0 at `origin` (the wrist), 1 at `length` along `axis` (the fingertips)."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    d = nt.nodes.new("ShaderNodeVectorMath")
    d.operation = "SUBTRACT"
    d.inputs[1].default_value = tuple(origin)
    nt.links.new(geo.outputs["Position"], d.inputs[0])
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = tuple(Vector(axis).normalized() / length)
    nt.links.new(d.outputs[0], dot.inputs[0])
    return dot.outputs["Value"]


def _behind(nt, s, sweep, amount):
    """1 where the scan line has passed (times the x-ray amount), 0 ahead of it."""
    m = nt.nodes.new("ShaderNodeMapRange")
    m.interpolation_type = "SMOOTHSTEP"
    nt.links.new(s, m.inputs["Value"])
    nt.links.new(XB._math(nt, "ADD", sweep, 0.02), m.inputs["From Min"])
    nt.links.new(XB._math(nt, "SUBTRACT", sweep, 0.02), m.inputs["From Max"])
    return XB._math(nt, "MULTIPLY", m.outputs["Result"], amount)


def _glass(nt, rim, strength, tint):
    """xray_body's glass shell (clear, with a bright outline), with its own tint: a light blue
    that darkens what is behind the hand a little, so the white bones stand out against the
    pale studio blue."""
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1)
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (0.85, 0.85, 0.85, 1)
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*H(rim), 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*H(tint), 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ramp.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    return mix.outputs[0]


def xray(hero, origin, axis, length, rim=XB.RIM, strength=1.0, tint="#C9E0EF", band=0.022):
    """Skin to glass with a glowing scan line from `origin` (the wrist) along `axis` (to the
    fingertips). Key it with key_xray(). Returns the materials."""
    mats = []
    for m in hero["body"].data.materials:
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial" and n.is_active_output)
        current = out.inputs["Surface"].links[0].from_socket
        shell = _glass(nt, rim, strength, tint)
        sweep, amount = XB._value(nt, "XRaySweep", -1.0), XB._value(nt, "XRayAmount", 0.0)
        s = _progress(nt, origin, axis, length)
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(_behind(nt, s, sweep, amount), mix.inputs[0])
        nt.links.new(current, mix.inputs[1])
        nt.links.new(shell, mix.inputs[2])
        near = XB._math(nt, "ABSOLUTE", XB._math(nt, "SUBTRACT", s, sweep))
        line = nt.nodes.new("ShaderNodeMapRange")
        line.interpolation_type = "SMOOTHSTEP"
        line.inputs["From Min"].default_value, line.inputs["From Max"].default_value = 0.0, band
        line.inputs["To Min"].default_value, line.inputs["To Max"].default_value = 1.0, 0.0
        nt.links.new(near, line.inputs["Value"])
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*H(XB.SCAN), 1)
        nt.links.new(XB._math(nt, "MULTIPLY", line.outputs["Result"], XB._math(nt, "MULTIPLY", amount, 2.5)),
                     em.inputs["Strength"])
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(mix.outputs[0], add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], out.inputs["Surface"])
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "DITHERED"
        mats.append(m)
    return mats


def key_xray(mats, keys):
    """keys: [(frame, scan line 0..1 from wrist to fingertips, amount 0..1)]."""
    XB.key_sweep(mats, keys)


# The skeleton of his hand, built like the real thing so it reads as an x-ray: each long bone has
# its base, a waisted shaft and a rounded head (PROFILES), with joint spaces between the bones
# (JOINT_GAP); the end bones of the fingers finish in a flattened tuft; eight carpal bones sit in
# two rows at the wrist (CARPALS), on the flared end of the radius and the knob of the ulna. The
# material glows brightest at the bone edges (the cortex), dimmer in the middle, with a fine
# spongy texture. (They were smooth capsules whose round ends merged at the joints, and the
# palm bones were all pulled to the middle of the palm: white lines, the user said.)
JOINT_GAP = 0.0016                   # the dark joint space between two bones (m)
# per kind: width along the bone [(t, factor)], base cap and head cap (as a share of the half
# width), and height/width of the section along the bone [(t, factor)]
PROFILES = {
    "metacarpal": ([(0, 0.95), (0.1, 0.88), (0.3, 0.62), (0.62, 0.6), (0.82, 0.8), (0.93, 0.98), (1, 0.95)],
                   0.25, 0.85, [(0, 0.9), (0.5, 0.85), (1, 0.95)]),
    "thumb_metacarpal": ([(0, 1.0), (0.15, 0.86), (0.4, 0.66), (0.65, 0.66), (0.85, 0.84), (1, 0.84)],
                         0.3, 0.8, [(0, 0.85), (1, 0.9)]),
    "proximal": ([(0, 1.0), (0.12, 0.92), (0.35, 0.66), (0.65, 0.62), (0.85, 0.74), (0.95, 0.8), (1, 0.74)],
                 0.22, 0.55, [(0, 0.8), (0.5, 0.75), (1, 0.75)]),
    "middle": ([(0, 1.0), (0.15, 0.9), (0.4, 0.66), (0.65, 0.64), (0.85, 0.76), (1, 0.7)],
               0.22, 0.55, [(0, 0.8), (0.5, 0.75), (1, 0.72)]),
    "distal": ([(0, 1.0), (0.15, 0.84), (0.4, 0.55), (0.62, 0.52), (0.8, 0.66), (0.9, 0.7), (1, 0.6)],
               0.22, 0.6, [(0, 0.8), (0.5, 0.7), (0.85, 0.5), (1, 0.45)]),
    "radius": ([(0, 0.46), (0.7, 0.48), (0.85, 0.62), (0.95, 0.9), (1, 1.0)], 0.6, 0.2, [(0, 0.95), (0.85, 0.72), (1, 0.6)]),
    "ulna": ([(0, 0.82), (0.7, 0.72), (0.88, 0.84), (0.97, 1.0), (1, 0.95)], 0.6, 0.6, [(0, 0.95), (1, 0.9)]),
}
# half widths at the base (m), from a real adult hand of his size (19 cm), before the fit
HALF = {"metacarpal": {1: 0.0062, 2: 0.0064, 3: 0.0056, 4: 0.0054}, "proximal": {2: 0.0068, 3: 0.007, 4: 0.0066, 5: 0.0058},
        "middle": {2: 0.0056, 3: 0.0058, 4: 0.0055, 5: 0.0048}, "distal": {2: 0.0047, 3: 0.0049, 4: 0.0046, 5: 0.0041}}
# where the metacarpals start at the wrist (mm along the hand from the wrist joint, mm across
# towards the thumb): side by side, fanning out to the knuckles (the rig starts them in pairs)
METACARPAL_BASE = {1: (34.0, 16.5), 2: (34.0, 5.0), 3: (37.0, -6.0), 4: (38.0, -16.0)}
# the carpals: name, centre (mm along, across, towards the palm), half sizes (mm along, across,
# deep), turn (degrees about the palm's normal), waist (a pinch in the middle, along)
CARPALS = [("scaphoid", (11, 15, 0), (12, 6.5, 7), 45, 0.18), ("lunate", (9, 3.5, 0), (8.5, 8, 8), 0, 0.0),
           ("triquetrum", (12, -8.5, 0), (7.5, 7.5, 7), -15, 0.0), ("pisiform", (14, -11.5, 6), (5, 5, 5), 0, 0.0),
           ("trapezium", (25, 22.5, 0), (8.5, 8, 7.5), 35, 0.0), ("trapezoid", (27, 14, 0), (7, 5.5, 6.5), 10, 0.0),
           ("capitate", (24.5, 4, 0), (11.5, 7.5, 8.5), 0, 0.1), ("hamate", (26.5, -9.5, 0), (10, 7.5, 8.5), -10, 0.0),
           ("hamate_hook", (28, -12, 7), (3.5, 3, 4), 0, 0.0)]


def _lerp_table(table, t):
    """Piecewise-linear lookup in [(t, value)], smoothed (smoothstep between the points)."""
    if t <= table[0][0]:
        return table[0][1]
    for (t0, v0), (t1, v1) in zip(table, table[1:]):
        if t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-9)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return table[-1][1]


def _bone_mesh(name, rings, cap0, cap1, mat, col, ring=24, square=2.3, rough=0.035, seed=0):
    """A bone surface from section rings [(centre, x, z, half width, half height)] along its
    length, with domed ends cap0 / cap1 (dome height as a share of the end's half width). The
    section is a rounded rectangle (superellipse `square`); `rough` adds a slight irregularity."""
    from mathutils import noise
    n = len(rings)
    tangents = []
    for i in range(n):
        a, b = rings[max(i - 1, 0)][0], rings[min(i + 1, n - 1)][0]
        tangents.append((b - a).normalized())
    full = []                                                   # (centre, tangent, x, z, hw, hh)

    def cap(end, sign, k):
        c, x, z, hw, hh = rings[end]
        t = tangents[end]
        out = []
        for j in range(1, 6):
            u = j / 6.0                                         # towards the tip
            sc = math.sqrt(max(0.0, 1.0 - u * u))
            out.append((c + t * (sign * k * hw * u), t, x, z, hw * sc, hh * sc))
        return out, c + t * (sign * k * hw)

    start, pole0 = cap(0, -1, cap0)
    end, pole1 = cap(n - 1, 1, cap1)
    full = list(reversed(start)) + [(c, tangents[i], x, z, hw, hh) for i, (c, x, z, hw, hh) in enumerate(rings)] + end
    verts, faces = [pole0], []
    off = Vector((seed * 1.37, seed * 2.11, seed * 0.73))
    for c, t, x, z, hw, hh in full:
        x = (x - t * x.dot(t)).normalized()
        zz = t.cross(x)
        if zz.dot(z) < 0:
            zz = -zz
        for k in range(ring):
            th = 2 * math.pi * k / ring
            cx, sz = math.cos(th), math.sin(th)
            ex = math.copysign(abs(cx) ** (2.0 / square), cx)
            ez = math.copysign(abs(sz) ** (2.0 / square), sz)
            p = c + x * (hw * ex) + zz * (hh * ez)
            bump = 1.0 + rough * noise.noise((p + off) * 180.0)
            verts.append(c + (p - c) * bump)
    verts.append(pole1)
    m = len(full)
    for k in range(ring):
        faces.append((0, 1 + (k + 1) % ring, 1 + k))
    for i in range(m - 1):
        for k in range(ring):
            a0, a1 = 1 + i * ring + k, 1 + i * ring + (k + 1) % ring
            b0, b1 = a0 + ring, a1 + ring
            faces.append((a0, a1, b1, b0))
    last = len(verts) - 1
    for k in range(ring):
        faces.append((1 + (m - 1) * ring + k, 1 + (m - 1) * ring + (k + 1) % ring, last))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    V.assign(ob, mat)
    return ob


def _long_bone(name, skin, a, b, x, z, kind, half, dorsal, gap0, gap1, mat, col, centre_sides=True, stations=16,
               end=None, seed=0):
    """A long bone between joint centres a and b (its base at a), fitted inside his skin: the
    centre line runs through the flesh (side to side too if centre_sides: fingers, not palm), the
    outline follows PROFILES[kind] from the half width `half` at the base, never wider than the
    flesh allows, and the bone stops gap0 / gap1 short of the joints. end: stop the head there
    instead (the fingertips)."""
    width, cap0, cap1, height = PROFILES[kind]
    a, b = Vector(a), Vector(b)
    if end is not None:
        b = Vector(end)
    L = (b - a).length

    def fit(ts):
        centres, rooms = [], []
        for t in ts:
            p = a.lerp(b, t)
            dx1, dx2, dz1, dz2 = _section(skin, p, x, z)
            ht = (dz1 + dz2) / 2
            c = p + z * ((dz1 - dz2) / 2 - dorsal * ht)
            if centre_sides:                                    # (by at most 2.5 mm: at a finger web a ray
                shift = (dx1 - dx2) / 2                         # escapes into the gap and pulls it aside)
                c = c + x * max(-0.0025, min(0.0025, shift))
                side = min(dx1, dx2) + abs(max(-0.0025, min(0.0025, shift)))
            else:
                side = min(dx1, dx2)
            centres.append(c)
            rooms.append((side, ht * (1.0 - dorsal)))
        T = np.array(ts)                                        # a smooth, gently curved centre line
        Wt = np.where((T > T[0] + 0.15 * (T[-1] - T[0])) & (T < T[-1] - 0.1 * (T[-1] - T[0])), 1.0, 0.35)
        D = np.stack([np.ones_like(T), T, T * T], axis=1) * Wt[:, None]
        coef = np.linalg.lstsq(D, np.array([tuple(c) for c in centres]) * Wt[:, None], rcond=None)[0]
        rings = []
        for t, (side, deep) in zip(ts, rooms):
            c = Vector(tuple(coef[0] + coef[1] * t + coef[2] * t * t))
            u = (t - ts[0]) / max(ts[-1] - ts[0], 1e-9)
            hw = min(half * _lerp_table(width, u), 0.7 * side)
            hh = min(hw * _lerp_table(height, u), 0.7 * deep)
            rings.append([c, x, z, hw, hh])
        return rings

    rings = fit(np.linspace(0.0, 1.0, stations))
    t0 = (gap0 + cap0 * rings[0][3]) / L
    t1 = 1.0 - (gap1 + cap1 * rings[-1][3]) / L
    rings = _inside_skin(skin, fit(np.linspace(t0, t1, stations)))
    return _bone_mesh(name, [tuple(r) for r in rings], cap0, cap1, mat, col, seed=seed)


def _inside_skin(skin, rings, margin=0.0015, square=2.3):
    """Shrink any section ring that would reach his skin (checked on its rounded-square outline,
    with room for the surface's irregularity)."""
    for r in rings:
        c, x, z = r[0], r[1], r[2]
        for _ in range(10):
            ok = True
            for k in range(16):
                th = 2 * math.pi * k / 16
                cx, sz = math.cos(th), math.sin(th)
                ex = math.copysign(abs(cx) ** (2.0 / square), cx)
                ez = math.copysign(abs(sz) ** (2.0 / square), sz)
                p = c + x * (r[3] * 1.07 * ex) + z * (r[4] * 1.07 * ez)
                hit = skin.find_nearest(p)
                if hit[0] is not None and ((p - hit[0]).dot(hit[1]) > 0 or (p - hit[0]).length < margin):
                    ok = False
                    break
            if ok:
                break
            r[3] *= 0.9
            r[4] *= 0.9
    return rings


def bone_material(name="XRay_Bone", sweep=None):
    """X-ray bone: it glows brightest at its edges (the dense outer layer, seen edge on) and
    dimmer through the middle, with a fine spongy texture; nearly solid, so it shows through his
    glass skin, and overlapping bones add up brighter, as on a real x-ray. sweep=(origin, axis,
    length): it only shows where the scan line has passed (key it with key_xray, like the skin)."""
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.3
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.26, 0.26, 0.26, 1)
    els[1].position, els[1].color = 0.92, (1.0, 1.0, 1.0, 1)
    mid = els.new(0.55)
    mid.color = (0.46, 0.46, 0.46, 1)
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    tex = nt.nodes.new("ShaderNodeTexNoise")                     # the spongy inside of the bone
    tex.inputs["Scale"].default_value = 1400.0
    tex.inputs["Detail"].default_value = 4.0
    tex.inputs["Roughness"].default_value = 0.62
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nt.links.new(geo.outputs["Position"], tex.inputs["Vector"])
    sponge = nt.nodes.new("ShaderNodeMapRange")
    sponge.inputs["From Min"].default_value, sponge.inputs["From Max"].default_value = 0.35, 0.65
    sponge.inputs["To Min"].default_value, sponge.inputs["To Max"].default_value = 0.86, 1.1
    nt.links.new(tex.outputs["Fac"], sponge.inputs["Value"])
    glow = XB._math(nt, "MULTIPLY", XB._math(nt, "MULTIPLY", ramp.outputs["Color"], sponge.outputs["Result"]), 9.0)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*BONE, 1)
    nt.links.new(glow, em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    solid = nt.nodes.new("ShaderNodeMixShader")
    solid.inputs[0].default_value = 0.85
    nt.links.new(tr.outputs[0], solid.inputs[1])
    nt.links.new(em.outputs[0], solid.inputs[2])
    current = solid.outputs[0]
    if sweep:
        amount = XB._value(nt, "XRayAmount", 0.0)
        shown = _behind(nt, _progress(nt, *sweep), XB._value(nt, "XRaySweep", -1.0), amount)
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(shown, mix.inputs[0])
        nt.links.new(nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
        nt.links.new(current, mix.inputs[2])
        current = mix.outputs[0]
    nt.links.new(current, out.inputs["Surface"])
    V._blended(mat)
    return mat


def _carpal(name, centre, frame, half, turn, waist, mat, col, seed):
    """One wrist bone: a rounded, slightly irregular block (half sizes along the hand, across,
    deep), turned `turn` degrees about the palm's normal, pinched in the middle by `waist`."""
    along, across, up = frame
    t = math.radians(turn)
    ax = along * math.cos(t) + across * math.sin(t)
    cx = across * math.cos(t) - along * math.sin(t)
    rings = []
    for u in np.linspace(-1.0, 1.0, 11)[1:-1]:
        sc = math.sqrt(max(0.0, 1.0 - u * u)) ** 0.8 * (1.0 - waist * math.exp(-(u / 0.35) ** 2))
        rings.append((centre + ax * (half[0] * u), cx, up, half[1] * sc, half[2] * sc))
    end = half[0] * (1.0 - abs(np.linspace(-1.0, 1.0, 11)[1]))
    return _bone_mesh(name, rings, end / max(rings[0][3], 1e-6), end / max(rings[-1][3], 1e-6), mat, col,
                      ring=20, square=2.2, rough=0.06, seed=seed)


def bones(hs, side="R", col=None, sweep=None):
    """The bones of his hand and wrist and the ends of the two forearm bones, built like the real
    skeleton and fitted inside his skin (hs: from build()). Returns (objects, material)."""
    col = col or V.collection("XRAY")
    hero, skin = hs["hero"], hs["skin"]
    rig = hero["rig"]
    W = rig.matrix_world
    mat = bone_material(sweep=sweep)
    w0, along, across, up = hs["wrist"], hs["along"], hs["across"], hs["up"]
    out = []

    def hand(al, ac, deep=0.0):
        return w0 + along * (al / 1000.0) + across * (ac / 1000.0) + up * (deep / 1000.0)

    def frame_of(name):
        pb = rig.pose.bones[f"{name}.{side}"]
        M = (W @ pb.matrix).to_3x3()
        return W @ pb.head, W @ pb.tail, M.col[0].normalized(), M.col[2].normalized()

    # the fingers: three bones each (the thumb: its metacarpal and two)
    kinds = ("proximal", "middle", "distal")
    for k in (2, 3, 4, 5):
        for seg, kind in zip((1, 2, 3), kinds):
            a, b, x, z = frame_of(f"finger{k}-{seg}")
            tip = None
            if seg == 3:                                            # the tuft stops short of the fingertip
                y = (b - a).normalized()
                tip = a + y * max(0.008, (hs["ends"][k] - a).dot(y) - 0.0035)
            out.append(_long_bone(f"Bone_finger{k}-{seg}", skin, a, b, x, z, kind, HALF[kind][k],
                                  0.3 if seg == 3 else 0.22, JOINT_GAP / 2, JOINT_GAP / 2, mat, col, end=tip,
                                  seed=k * 3 + seg))
    for seg, kind, half in ((1, "thumb_metacarpal", 0.0076), (2, "proximal", 0.0072), (3, "distal", 0.0062)):
        a, b, x, z = frame_of(f"finger1-{seg}")
        tip = None
        if seg == 1:                                                # the rig starts the thumb too far out: reach the trapezium
            a = a - (b - a).normalized() * 0.007
        if seg == 3:
            y = (b - a).normalized()
            tip = a + y * max(0.008, (hs["ends"][1] - a).dot(y) - 0.0035)
        out.append(_long_bone(f"Bone_thumb-{seg}", skin, a, b, x, z, kind, half, 0.25, JOINT_GAP / 2, JOINT_GAP / 2,
                              mat, col, end=tip, seed=20 + seg))
    # the palm: four metacarpals from the wrist to the knuckles, side by side (not centred)
    for k in (1, 2, 3, 4):
        _, knuckle, x, z = frame_of(f"metacarpal{k}")
        base = hand(*METACARPAL_BASE[k])
        axis = (knuckle - base).normalized()
        x = (across - axis * across.dot(axis)).normalized()
        zz = axis.cross(x)
        if zz.dot(up) < 0:
            zz = -zz
        out.append(_long_bone(f"Bone_metacarpal{k}", skin, base, knuckle, x, zz, "metacarpal", HALF["metacarpal"][k],
                              0.3, JOINT_GAP, JOINT_GAP / 2, mat, col, centre_sides=False, seed=30 + k))
    # the wrist: eight carpals in two rows (and the hook of the hamate), at the right depth
    for i, (name, (al, ac, deep), half, turn, waist) in enumerate(CARPALS):
        p = hand(al, ac)
        dx1, dx2, dz1, dz2 = _section(skin, p, across, up)
        ht = (dz1 + dz2) / 2
        c = p + up * ((dz1 - dz2) / 2 - 0.15 * ht + deep / 1000.0)
        room = min(dx1, dx2, ht)
        h = tuple(min(v / 1000.0, 0.85 * room) for v in half)
        out.append(_carpal(f"Bone_{name}", c, (along, across, up), h, turn, waist, mat, col, seed=40 + i))
    # the forearm bones: the radius on the thumb side (its end flared), the ulna's knob beside it
    e0 = W @ rig.pose.bones[f"lowerarm01.{side}"].head
    f = (w0 - e0).normalized()
    fx = (across - f * across.dot(f)).normalized()
    fz = f.cross(fx)
    if fz.dot(up) < 0:
        fz = -fz
    for name, kind, ac, back, half in (("Bone_radius", "radius", 0.5, 0.0008, 0.0125), ("Bone_ulna", "ulna", -13.0, 0.005, 0.0068)):
        end = w0 + fx * (ac / 1000.0) - f * back
        start = end - f * 0.2
        out.append(_long_bone(name, skin, start, end, fx, fz, kind, half, 0.12, 0.0, 0.0, mat, col, centre_sides=False,
                              stations=22, seed=50 + len(out)))
    for name, ac, back, size in (("Bone_radius_styloid", 10.5, 0.0005, (6.0, 4.5, 4.5)),   # the bony points of the wrist
                                 ("Bone_ulna_styloid", -16.5, 0.004, (4.0, 2.6, 2.6))):
        p = w0 + fx * (ac / 1000.0) - f * back
        dx1, dx2, dz1, dz2 = _section(skin, p, fx, fz)
        c = p + fz * ((dz1 - dz2) / 2 - 0.12 * (dz1 + dz2) / 2)
        room = min(dx1, dx2, (dz1 + dz2) / 2)
        h = tuple(min(v / 1000.0, 0.8 * room) for v in size)
        out.append(_carpal(name, c - f * h[0] * 0.5, (f, fx, fz), h, 0, 0.0, mat, col, seed=60 + len(out)))
    return out, mat


def nerve_paths(hs, side="R"):
    """Polylines (world) for the nerves, just under the skin of his palm side: the trunk from
    the forearm into the palm, then one branch along each finger to the middle of its pad."""
    hero, skin = hs["hero"], hs["skin"]
    rig = hero["rig"]
    W = rig.matrix_world
    pb = lambda n: rig.pose.bones[f"{n}.{side}"]
    across, up = hs["across"], hs["up"]

    def under(p, x, z, depth):
        dx1, dx2, dz1, dz2 = _section(skin, p, x, z)
        return p + x * ((dx1 - dx2) / 2) + z * (dz1 - depth)

    trunk = [W @ pb("lowerarm01").head.lerp(pb("lowerarm01").tail, 0.3), W @ pb("lowerarm02").head,
             W @ pb("wrist").head, hs["wrist"].lerp(hs["palm"], 0.6)]
    trunk = [under(p, across, up, 0.006) for p in trunk]
    branches = {}
    for k in FINGERS:
        pts = [trunk[-1]]
        for seg in (1, 2, 3):
            bone = pb(f"finger{k}-{seg}")
            M = (W @ bone.matrix).to_3x3()
            x, z = M.col[0].normalized(), M.col[2].normalized()
            for t in ((0.0, 0.5) if seg < 3 else (0.0, 0.45, 0.7)):
                pts.append(under((W @ bone.head).lerp(W @ bone.tail, t), x, z, 0.0032))
        branches[k] = K.path_spline(pts, 40)
    return K.path_spline(trunk, 30), branches


def nerves(hs, grow, pulse_at, side="R", col=None):
    """The yellow nerves light up from the wrist into every fingertip (grow=(start, end)),
    then pulses race along them from the forearm to the fingertips (starting at pulse_at)."""
    col = col or V.collection("XRAY")
    trunk, branches = nerve_paths(hs, side)
    mat = V.emission("Nerve_Yellow", NERVE, 2.6)
    g0, g1 = grow
    split = g0 + (g1 - g0) * 0.35
    out = [V.glow_curve("Nerve_Trunk", trunk, 0.0024, mat, col=col, grow=(g0, round(split)), taper=0.8)]
    for k, pts in branches.items():
        out.append(V.glow_curve(f"Nerve_Finger{k}", pts, 0.0016, mat, col=col, grow=(round(split), g1), taper=0.45))
    for i, (k, pts) in enumerate(branches.items()):
        path = np.vstack([trunk, pts[1:]])
        s = pulse_at + i * 2
        out.append(V.pulse(f"Nerve_Pulse{k}", path, s, s + 12, color=H("#FFE7A0"), size=0.0042, strength=14.0,
                           col=col, trail=0.09))                       # a short bright spark, a little thicker than the nerve
    return out
