"""Her x-ray look for the anatomy shots: as a glowing scan line sweeps down over her, her skin
and clothes turn to clear glass with a thin pale-cyan rim (hair, brows, lashes and the shirt
print fade out; her eyes stay as they are), so her airways show inside. Driven per material by two
values, XRaySweep (height of the scan line, m) and XRayAmount (0..1); key_sweep() keys them.
"""
import bpy

import vfx_kit as V

H = V.hex_lin
RIM, TINT, SCAN = "#CDF6FF", "#EEF9FF", "#8FEFFF"


def _value(nt, name, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.name = n.label = name
    n.outputs[0].default_value = value
    return n.outputs[0]


def _math(nt, op, a, b=None):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def _shell(nt, kind, rim, strength):
    if kind == "fade":
        return nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0]
    if kind == "glow":
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*H("#F4F8FF"), 1)
        em.inputs["Strength"].default_value = 1.6
        return em.outputs[0]
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1)               # a faint glassy fill: her shape reads
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (0.85, 0.85, 0.85, 1)               # a clear bright outline (face profile)
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*H(rim), 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*H(TINT), 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ramp.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    return mix.outputs[0]


def add_xray(mat, kind="glass", rim=RIM, strength=1.2, band=0.006, feather=0.004):
    """Mix the x-ray shell into a material above the scan line. kind: 'glass' (clear with a
    rim), 'fade' (disappears), 'glow' (teeth: soft white glow)."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial" and n.is_active_output)
    if not out.inputs["Surface"].is_linked:
        return None
    current = out.inputs["Surface"].links[0].from_socket
    shell = _shell(nt, kind, rim, strength)
    sweep = _value(nt, "XRaySweep", 50.0)
    amount = _value(nt, "XRayAmount", 0.0)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    z = sep.outputs["Z"]
    above = nt.nodes.new("ShaderNodeMapRange")                  # 0 below the line, 1 above (soft edge)
    above.interpolation_type = "SMOOTHSTEP"
    nt.links.new(z, above.inputs["Value"])
    nt.links.new(_math(nt, "SUBTRACT", sweep, feather), above.inputs["From Min"])
    nt.links.new(_math(nt, "ADD", sweep, feather), above.inputs["From Max"])
    fac = _math(nt, "MULTIPLY", above.outputs["Result"], amount)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fac, mix.inputs[0])
    nt.links.new(current, mix.inputs[1])
    nt.links.new(shell, mix.inputs[2])
    # the glowing scan line itself
    near = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", z, sweep))
    line = nt.nodes.new("ShaderNodeMapRange")
    line.interpolation_type = "SMOOTHSTEP"
    line.inputs["From Min"].default_value, line.inputs["From Max"].default_value = 0.0, band
    line.inputs["To Min"].default_value, line.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(near, line.inputs["Value"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*H(SCAN), 1)
    nt.links.new(_math(nt, "MULTIPLY", line.outputs["Result"], _math(nt, "MULTIPLY", amount, 6.0)), em.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mix.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "HASHED"
    return mat


def _kind(ob_name, mat_name):
    n = (ob_name + " " + mat_name).lower()
    if "high-poly" in n or "low-poly" in n:                     # her eyes stay as they are: bulging, readable
        return None
    if any(k in n for k in ("ponytail", "eyebrow", "eyelash", "print", "tongue", "teeth")):   # teeth: no floating grin
        return "fade"
    return "glass"


def apply(hero, extra=()):
    """Give every material on her (and on `extra` objects, e.g. the chest print) the x-ray
    sweep. Returns the materials."""
    objs = [hero["body"]] + list(hero["parts"]) + list(extra)
    if hero.get("print") is not None:
        objs.append(hero["print"])
    done = []
    for ob in objs:
        for slot in ob.material_slots:
            m = slot.material
            if m is None or m in done or m.node_tree is None:
                continue
            kind = _kind(ob.name, m.name)
            if kind is None:
                continue
            strength = 0.9 if any(k in m.name.lower() for k in ("suit", "shoe", "teeth")) else 1.2
            if add_xray(m, kind, strength=strength) is not None:
                done.append(m)
    return done


def key_sweep(mats, keys):
    """keys: [(frame, sweep height z, amount)], the same on every x-ray material."""
    for m in mats:
        nt = m.node_tree
        sw, am = nt.nodes["XRaySweep"].outputs[0], nt.nodes["XRayAmount"].outputs[0]
        for f, z, a in keys:
            sw.default_value, am.default_value = z, a
            sw.keyframe_insert("default_value", frame=f)
            am.keyframe_insert("default_value", frame=f)


def preview_bounces(scene=None):
    """Cycles stops a ray after a few transparent surfaces and paints it black: an x-ray stack
    (hair cards, glass skin, glass airways) needs many more."""
    sc = scene or bpy.context.scene
    if sc.render.engine == "CYCLES":
        sc.cycles.transparent_max_bounces = 64

