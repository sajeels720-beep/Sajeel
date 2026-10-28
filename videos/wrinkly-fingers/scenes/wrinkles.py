"""Water wrinkles on his fingertips, growing on cue.

Real pruney fingers: the pads of the last finger bones (and a little of the middle ones)
crumple into soft, pillowy ridges split by narrow furrows that mostly run along the finger,
and the pads go paler. The skin over the nails and on the backs of the fingers stays smooth.

setup(hero) does three things:
1. rest-pose data on his body mesh: wr_w (how much each vertex wrinkles: the finger pads,
   fading towards the joints, not the nails or the backs of the fingers) and wr_co (the
   vertex in its own finger's frame, in millimetres: x across, y along the finger, z out of
   the palm, 0 in the middle of the pad);
2. a geometry-nodes modifier after the pose and the subdivision that pushes the furrows into
   the skin along its normal (Amount x Depth; animate Amount with key()) and stores wr_amt
   for the shader;
3. the same pattern in his skin shader: a bump (so it reads when the mesh is coarse), darker
   furrows, paler pads, and fine fingerprint ridges.
The furrows are real geometry only where the mesh is dense enough: dense(hero) keeps just
his arms and hands and subdivides them more, for the extreme close-ups.
"""
import bpy
import numpy as np

import vfx_kit as V

H = V.hex_lin
CELL = 2.1            # mm from one ridge to the next (smaller reads as grit at arm's length)
STRETCH = 3.0         # the breaks between ridges come about this many times further apart along the finger
MEANDER = 1.5         # mm the ridges wander sideways along the finger
DEPTH = 0.6           # mm deep furrows at Amount 1 (real ones are shallower; his look is bigger than life)
PALE = H("#F4D5C8")   # the pads go pale (a warm pinkish white) as they soak
RIDGE_MM = 0.46       # fingerprint ridge spacing


def _smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _group_weights(body, names):
    """{group name: weight array over the base mesh's vertices} for the named vertex groups."""
    idx = {body.vertex_groups[n].index: n for n in names if n in body.vertex_groups}
    out = {n: np.zeros(len(body.data.vertices), np.float32) for n in idx.values()}
    for v in body.data.vertices:
        for g in v.groups:
            n = idx.get(g.group)
            if n is not None:
                out[n][v.index] = g.weight
    return out


def rest_shape(body):
    """World positions and normals of the base-mesh vertices in his rest pose, with his body
    shape applied: MPFB keeps the phenotype (height, build, face) in shape keys, and the rig is
    fitted to that shape, not to the raw base mesh. Every modifier is switched off while
    sampling, so the indices match body.data.vertices."""
    on = [m for m in body.modifiers if m.show_viewport]
    for m in on:
        m.show_viewport = False
    bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    M, R = ev.matrix_world, ev.matrix_world.to_3x3()
    P = np.array([tuple(M @ v.co) for v in me.vertices])
    N = np.array([tuple((R @ v.normal).normalized()) for v in me.vertices])
    ev.to_mesh_clear()
    for m in on:
        m.show_viewport = True
    bpy.context.view_layer.update()
    return P, N


def attributes(hero):
    """Write wr_w and wr_co onto the body mesh (rest pose). Returns wr_w."""
    body, rig = hero["body"], hero["rig"]
    me = body.data
    n = len(me.vertices)
    P, N = rest_shape(body)
    names = [f"finger{k}-{j}.{s}" for k in range(1, 6) for j in (2, 3) for s in "LR"] + ["fingernails"]
    W = _group_weights(body, names)
    nails = W.get("fingernails", np.zeros(n, np.float32))
    best = np.zeros(n, np.float32)
    wr_w = np.zeros(n, np.float32)
    wr_co = np.zeros((n, 3), np.float32)
    for s in "LR":
        for k in range(1, 6):
            w3 = W.get(f"finger{k}-3.{s}", np.zeros(n, np.float32))
            w2 = W.get(f"finger{k}-2.{s}", np.zeros(n, np.float32))
            tot = w3 + w2
            mine = tot > best
            if not mine.any():
                continue
            bone = rig.data.bones[f"finger{k}-3.{s}"]
            M = rig.matrix_world @ bone.matrix_local                # the distal bone's rest frame
            R = np.array(M.to_3x3().normalized())
            head = np.array(M.translation)
            centre = head + R[:, 1] * bone.length * 0.55             # the middle of the pad, along the finger
            local = (P[mine] - centre) @ R                           # columns: x across, y along, z to the palm
            palm_side = _smooth(N[mine] @ R[:, 2], -0.15, 0.55)
            amount = np.clip(w3[mine] + 0.5 * w2[mine], 0, 1)
            amount = _smooth(amount, 0.0, 0.9) * palm_side * (1 - _smooth(nails[mine], 0.1, 0.5))
            wr_w[mine] = amount
            wr_co[mine] = local * 1000.0
            best[mine] = tot[mine]
    for name, typ, data in (("wr_w", "FLOAT", wr_w), ("wr_co", "FLOAT_VECTOR", wr_co)):
        if name in me.attributes:
            me.attributes.remove(me.attributes[name])
        a = me.attributes.new(name, typ, "POINT")
        a.data.foreach_set("value" if typ == "FLOAT" else "vector", data.ravel())
    return wr_w


# --------------------------------------------------------------------------
# The pattern, shared by the geometry nodes and the shader
# --------------------------------------------------------------------------
def _pattern(nt, links, co):
    """Node chain: wr_co (mm) -> furrow (1 in the furrows, 0 on the pillows). Works in both
    geometry-node and shader trees. Returns the furrow socket."""
    def node(kind, **kw):
        nd = nt.nodes.new(kind)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd
    # the ridges meander: shift each point sideways by slow noise along the finger
    wob = node("ShaderNodeTexNoise", noise_dimensions="3D")
    wob.inputs["Scale"].default_value = 1.0
    wob.inputs["Detail"].default_value = 3.0
    slow = node("ShaderNodeVectorMath", operation="MULTIPLY")
    slow.inputs[1].default_value = (0.09, 0.14, 0.09)
    links.new(co, slow.inputs[0])
    links.new(slow.outputs[0], wob.inputs["Vector"])
    centred = node("ShaderNodeVectorMath", operation="SUBTRACT")
    centred.inputs[1].default_value = (0.5, 0.5, 0.5)
    links.new(wob.outputs["Color"], centred.inputs[0])
    amp = node("ShaderNodeVectorMath", operation="MULTIPLY_ADD")
    amp.inputs[1].default_value = (MEANDER * 2.0, MEANDER * 0.6, MEANDER * 2.0)
    links.new(centred.outputs[0], amp.inputs[0])
    links.new(co, amp.inputs[2])
    # main ridges: wavy, sausage-shaped, running along the finger (bands across x)
    wave = node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", wave_profile="SIN")
    wave.inputs["Scale"].default_value = 0.314 / CELL               # Blender's bands: period 0.314 / scale
    wave.inputs["Distortion"].default_value = 0.0
    links.new(amp.outputs[0], wave.inputs["Vector"])
    # breaks: some ridges split or end (long Voronoi cells give the cross furrows)
    div = node("ShaderNodeVectorMath", operation="DIVIDE")
    div.inputs[1].default_value = (CELL * 1.8, CELL * STRETCH, CELL * 1.8)
    links.new(amp.outputs[0], div.inputs[0])
    vor = node("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="DISTANCE_TO_EDGE")
    vor.inputs["Scale"].default_value = 1.0
    vor.inputs["Randomness"].default_value = 0.9
    links.new(div.outputs[0], vor.inputs["Vector"])
    out = []
    for sock, width in ((wave.outputs["Fac"], 0.3), (vor.outputs["Distance"], 0.1)):
        mr = node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, width
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
        links.new(sock, mr.inputs["Value"])
        out.append(mr.outputs["Result"])
    part = node("ShaderNodeMath", operation="MULTIPLY")
    part.inputs[1].default_value = 0.7
    links.new(out[1], part.inputs[0])
    mx = node("ShaderNodeMath", operation="MAXIMUM")
    links.new(out[0], mx.inputs[0])
    links.new(part.outputs[0], mx.inputs[1])
    return mx.outputs[0]


def _gn_group():
    ng = bpy.data.node_groups.get("Fingertip_Wrinkles")
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new("Fingertip_Wrinkles", "GeometryNodeTree")
    io = ng.interface
    io.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    io.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nt, L = ng, ng.links
    gi, go = nt.nodes.new("NodeGroupInput"), nt.nodes.new("NodeGroupOutput")
    # the controls are Value nodes in the group, keyed on the group itself: modifier inputs are
    # set differently in Blender 4.5 and 5.x, node values the same way in both
    knobs = {}
    for name, val in (("WR_Amount", 0.0), ("WR_Depth", 0.0), ("WR_Shrink", 0.35)):
        v = nt.nodes.new("ShaderNodeValue")
        v.name = v.label = name
        v.outputs[0].default_value = val
        knobs[name] = v.outputs[0]
    co = nt.nodes.new("GeometryNodeInputNamedAttribute")
    co.data_type = "FLOAT_VECTOR"
    co.inputs["Name"].default_value = "wr_co"
    w = nt.nodes.new("GeometryNodeInputNamedAttribute")
    w.data_type = "FLOAT"
    w.inputs["Name"].default_value = "wr_w"
    furrow = _pattern(nt, L, co.outputs["Attribute"])

    def math(op, a, b):
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                L.new(x, m.inputs[i])
        return m.outputs[0]
    amt = math("MULTIPLY", knobs["WR_Amount"], w.outputs["Attribute"])
    # mm of inward push: the furrows (real geometry only when dense()), plus the whole pad
    # deflating a little as it loses blood
    push = math("ADD", math("MULTIPLY", furrow, knobs["WR_Depth"]), knobs["WR_Shrink"])
    off = math("MULTIPLY", math("MULTIPLY", push, amt), -0.001)
    nrm = nt.nodes.new("GeometryNodeInputNormal")
    scale = nt.nodes.new("ShaderNodeVectorMath")
    scale.operation = "SCALE"
    L.new(nrm.outputs["Normal"], scale.inputs[0])
    L.new(off, scale.inputs["Scale"])
    sp = nt.nodes.new("GeometryNodeSetPosition")
    L.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    L.new(scale.outputs[0], sp.inputs["Offset"])
    st = nt.nodes.new("GeometryNodeStoreNamedAttribute")
    st.data_type, st.domain = "FLOAT", "POINT"
    st.inputs["Name"].default_value = "wr_amt"
    L.new(sp.outputs["Geometry"], st.inputs["Geometry"])
    L.new(amt, st.inputs["Value"])
    L.new(st.outputs["Geometry"], go.inputs["Geometry"])
    return ng


def move_modifier(ob, name, index):
    """Move a modifier to a stack position (ObjectModifiers has no move() in Blender 4.5/5.x)."""
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_move_to_index(modifier=name, index=index)


def knob(name):
    """A control of the wrinkle node group: WR_Amount, WR_Depth (mm) or WR_Shrink (mm)."""
    return _gn_group().nodes[name].outputs[0]


def _modifier(hero):
    body = hero["body"]
    mod = body.modifiers.get("Wrinkles")
    if mod is not None:
        return mod
    mod = body.modifiers.new("Wrinkles", "NODES")
    mod.node_group = _gn_group()
    sub = next(i for i, m in enumerate(body.modifiers) if m.type == "SUBSURF")
    move_modifier(body, mod.name, sub + 1)                         # right after the pose and the subdivision
    return mod


def _skin_shader(hero):
    """Add the wrinkles to his skin shader (inside MPFB's skin node group)."""
    for m in hero["body"].data.materials:
        g = next((n for n in (m.node_tree.nodes if m and m.node_tree else []) if n.bl_idname == "ShaderNodeGroup"), None)
        if g is None or g.node_tree.nodes.get("WR_Bump"):
            continue
        nt, L = g.node_tree, g.node_tree.links
        bsdf = nt.nodes.get("Principled BSDF")

        def attr(name):
            a = nt.nodes.new("ShaderNodeAttribute")
            a.attribute_type, a.attribute_name = "GEOMETRY", name
            return a
        co, amt, w = attr("wr_co"), attr("wr_amt"), attr("wr_w")
        furrow = _pattern(nt, L, co.outputs["Vector"])

        def math(op, a, b, name=None):
            mm = nt.nodes.new("ShaderNodeMath")
            mm.operation = op
            if name:
                mm.name = mm.label = name
            for i, x in enumerate((a, b)):
                if isinstance(x, (int, float)):
                    mm.inputs[i].default_value = x
                else:
                    L.new(x, mm.inputs[i])
            return mm.outputs[0]
        # fingerprint ridges: rings around the middle of each pad, wobbled like real whorls
        ring = nt.nodes.new("ShaderNodeTexWave")
        ring.wave_type, ring.rings_direction = "RINGS", "SPHERICAL"
        ring.inputs["Scale"].default_value = 0.314 / RIDGE_MM        # Blender's rings: period 0.314 / scale
        ring.inputs["Distortion"].default_value = 3.0
        ring.inputs["Detail"].default_value = 2.0
        flat = nt.nodes.new("ShaderNodeVectorMath")
        flat.operation = "MULTIPLY"
        flat.inputs[1].default_value = (1.0, 0.8, 0.0)               # whorls in the plane of the pad
        L.new(co.outputs["Vector"], flat.inputs[0])
        L.new(flat.outputs[0], ring.inputs["Vector"])
        ridges = math("MULTIPLY", ring.outputs["Fac"], math("MULTIPLY", w.outputs["Fac"], 0.035))
        strength = nt.nodes.new("ShaderNodeValue")                    # 1 = bump carries the furrows (coarse mesh)
        strength.name = strength.label = "WR_BumpShare"
        strength.outputs[0].default_value = 1.0
        depth = math("MULTIPLY", math("MULTIPLY", furrow, amt.outputs["Fac"]), DEPTH)
        height = math("SUBTRACT", ridges, math("MULTIPLY", depth, strength.outputs[0]))
        bump = nt.nodes.new("ShaderNodeBump")
        bump.name = "WR_Bump"
        bump.inputs["Distance"].default_value = 0.001                # height 1 = 1 mm
        L.new(height, bump.inputs["Height"])
        old = bsdf.inputs["Normal"].links[0].from_socket if bsdf.inputs["Normal"].is_linked else None
        if old is not None:
            L.new(old, bump.inputs["Normal"])
        L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        # colour: paler pads, darker furrows
        base = bsdf.inputs["Base Color"].links[0].from_socket
        pale = nt.nodes.new("ShaderNodeMix")
        pale.data_type, pale.blend_type = "RGBA", "MIX"
        L.new(math("MULTIPLY", amt.outputs["Fac"], 0.32), pale.inputs[0])
        L.new(base, pale.inputs[6])
        pale.inputs[7].default_value = (*PALE, 1)
        shade = nt.nodes.new("ShaderNodeMix")
        shade.data_type, shade.blend_type = "RGBA", "MULTIPLY"
        L.new(math("MULTIPLY", math("MULTIPLY", furrow, amt.outputs["Fac"]), 0.28), shade.inputs[0])
        L.new(pale.outputs[2], shade.inputs[6])
        shade.inputs[7].default_value = (*H("#BC6F64"), 1)
        L.new(shade.outputs[2], bsdf.inputs["Base Color"])


def setup(hero):
    """Fingertip data, the modifier and the shader. Returns the modifier."""
    attributes(hero)
    mod = _modifier(hero)
    _skin_shader(hero)
    return mod


def key(hero, keys):
    """Animate the wrinkles: keys = [(frame, amount 0..1)], eased in and out."""
    _modifier(hero)
    sock = knob("WR_Amount")
    for f, a in keys:
        sock.default_value = a
        sock.keyframe_insert("default_value", frame=f)
    for fc in V.fcurves(_gn_group()):
        if "WR_Amount" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation, kp.easing = "BEZIER", "EASE_IN_OUT"
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def set_amount(hero, amount):
    _modifier(hero)
    knob("WR_Amount").default_value = amount


def dense(hero, levels=3, keep=("wrist", "finger", "metacarpal", "lowerarm"), hide_parts=True):
    """Extreme close-ups: keep only his forearms and hands, subdivide them `levels` times
    and push the furrows in as real geometry (the shader bump then only adds the fine
    detail). Hides his hair and clothes, which these shots never see."""
    body = hero["body"]
    vg = body.vertex_groups.get("WR_keep") or body.vertex_groups.new(name="WR_keep")
    W = _group_weights(body, [g.name for g in body.vertex_groups if any(g.name.startswith(k) for k in keep)])
    sel = np.zeros(len(body.data.vertices), bool)
    for arr in W.values():
        sel |= arr > 0.01
    vg.add([int(i) for i in np.where(sel)[0]], 1.0, "REPLACE")
    mask = body.modifiers.get("WR_KeepHands") or body.modifiers.new("WR_KeepHands", "MASK")
    mask.vertex_group = "WR_keep"
    sub = next(i for i, m in enumerate(body.modifiers) if m.type == "SUBSURF")
    if list(body.modifiers).index(mask) != sub - 1:
        move_modifier(body, mask.name, sub)
    s = next(m for m in body.modifiers if m.type == "SUBSURF")
    s.levels = s.render_levels = levels
    _modifier(hero)
    knob("WR_Depth").default_value = DEPTH
    for m in body.data.materials:
        g = next((n for n in (m.node_tree.nodes if m and m.node_tree else []) if n.bl_idname == "ShaderNodeGroup"), None)
        share = g.node_tree.nodes.get("WR_BumpShare") if g else None
        if share is not None:
            share.outputs[0].default_value = 0.25
    if hide_parts:
        for o in hero["parts"]:
            o.hide_render = o.hide_viewport = True
        for k in ("print",):
            if hero.get(k) is not None:
                hero[k].hide_render = hero[k].hide_viewport = True
    return mask
