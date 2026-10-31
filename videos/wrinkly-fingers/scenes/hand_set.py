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


def _capsule(name, a, b, ra, rb, mat, col, mid=None):
    """A bone: a waisted tube from a to b with round ends (through `mid` if given)."""
    a, b = Vector(a), Vector(b)
    c = a.lerp(b, 0.5) if mid is None else 2 * Vector(mid) - a.lerp(b, 0.5)      # the curve passes through mid
    pts = [(1 - t) ** 2 * a + 2 * t * (1 - t) * c + t * t * b for t in np.linspace(0, 1, 6)]
    radii = [ra + (rb - ra) * t for t in np.linspace(0, 1, 6)]
    radii = [r * (1.0 - 0.18 * math.sin(math.pi * t)) for r, t in zip(radii, np.linspace(0, 1, 6))]   # waisted shaft
    parts = [K.tube(name, pts, radii, segments=16, col=col),
             K.ellipsoid(name + "_A", a, (ra * 1.12,) * 3, segments=16, col=col),
             K.ellipsoid(name + "_B", b, (rb * 1.12,) * 3, segments=16, col=col)]
    for o in parts:
        V.assign(o, mat)
    return parts


def bone_material(name="XRay_Bone", sweep=None):
    """Bright bone with a glowing rim, nearly solid, so it shows through his glass skin.
    sweep=(origin, axis, length): it only shows where the scan line has passed (key it with
    key_xray, like the skin)."""
    mat = V.xray(name, BONE, strength=2.2, edge=0.6, core=0.8)
    if sweep:
        nt = mat.node_tree
        out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
        current = out.inputs["Surface"].links[0].from_socket
        amount = XB._value(nt, "XRayAmount", 0.0)
        shown = _behind(nt, _progress(nt, *sweep), XB._value(nt, "XRaySweep", -1.0), amount)
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(shown, mix.inputs[0])
        nt.links.new(nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
        nt.links.new(current, mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def bones(hs, side="R", col=None, sweep=None):
    """The bones of his hand and wrist and the two forearm bones, as glowing capsules fitted
    inside his skin (hs: from build()). Returns (objects, material)."""
    col = col or V.collection("XRAY")
    hero, skin = hs["hero"], hs["skin"]
    rig = hero["rig"]
    W = rig.matrix_world
    mat = bone_material(sweep=sweep)
    out = []

    def fit(name, a, b, x, z, r0, r1, dorsal=0.2):
        (ca, ra), (cm, rm), (cb, rb) = (_inside(skin, p, x, z, dorsal) for p in (a, a.lerp(b, 0.5), b))
        out.extend(_capsule(name, ca, cb, min(r0, 0.45 * ra, 0.45 * rm), min(r1, 0.45 * rb, 0.45 * rm), mat, col,
                            mid=cm))

    for k in FINGERS:
        for seg, (r0, r1) in zip((1, 2, 3), ((0.0052, 0.0044), (0.0043, 0.0038), (0.0036, 0.0028))):
            pb = rig.pose.bones[f"finger{k}-{seg}.{side}"]
            M = (W @ pb.matrix).to_3x3()
            x, y, z = (M.col[i].normalized() for i in range(3))
            a, b = W @ pb.head, W @ pb.tail
            if seg == 3:                                         # the tip bone stops short of the fingertip
                reach = (hs["ends"][k] - a).dot(y)
                b = a + y * max(0.006, reach - 0.0045)
            gap = (b - a) * 0.07
            fit(f"Bone_finger{k}-{seg}", a + gap, b - gap, x, z, r0, r1, dorsal=0.3 if seg == 3 else 0.2)
    for k in (1, 2, 3, 4):
        name = f"metacarpal{k}"
        if f"{name}.{side}" in rig.pose.bones:
            pb = rig.pose.bones[f"{name}.{side}"]
            M = (W @ pb.matrix).to_3x3()
            a, b = W @ pb.head, W @ pb.tail
            gap = (b - a) * 0.08
            fit(f"Bone_{name}", a + gap, b - gap, M.col[0].normalized(), M.col[2].normalized(), 0.0048, 0.0052)
    across, up, along = hs["across"], hs["up"], hs["along"]
    w0 = hs["wrist"]
    rnd = np.random.default_rng(4)
    for i in range(8):                                          # the carpals: two rows of pebbles, packed
        row, colm = divmod(i, 4)
        p = w0 + along * (0.007 + 0.0095 * row) + across * (-0.0125 + 0.0083 * (colm + 0.5 * row - 0.25)) \
            + Vector(rnd.normal(0, 0.0008, 3))
        c, room = _inside(skin, p, across, up, 0.15)
        o = K.ellipsoid(f"Bone_carpal_{i}", c, tuple(min(r, 0.42 * room) for r in rnd.uniform(0.0042, 0.0072, 3)),
                        rot=tuple(rnd.uniform(-40, 40, 3)), segments=12, col=col)      # knobbly, not marbles
        V.assign(o, mat)
        out.append(o)
    e0 = W @ rig.pose.bones[f"lowerarm01.{side}"].head           # radius and ulna, side by side
    for name, sx in (("Bone_radius", 0.3), ("Bone_ulna", -0.3)):
        ends = []
        for p in (e0.lerp(w0, 0.15), w0 - along * 0.012):
            dx1, dx2, dz1, dz2 = _section(skin, p, across, up)
            c = p + across * ((dx1 - dx2) / 2 + sx * (dx1 + dx2) / 2) + up * ((dz1 - dz2) / 2)
            ends.append((c, min((dx1 + dx2) / 2 * 0.3, (dz1 + dz2) / 2 * 0.45)))
        out.extend(_capsule(name, ends[0][0], ends[1][0], min(0.0075, ends[0][1]), min(0.0072, ends[1][1]), mat, col))
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
