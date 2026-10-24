"""His bright outdoor blur, like the user's screenshot (the slug on the razor blade): a
saturated sky blue that gets lighter towards a soft, warm sun glow, and a blurred green field
with a soft tree line along the bottom. It is built into the world, already soft as if out of
focus, so it works from every camera angle and both engines (EEVEE and Cycles) show the same
thing. The same colours light the scene softly (blue from above, green bounce from below),
and lights() adds the studio key, sky-blue fill and warm rim that go with it.

The glow sits where the shot asks for it on screen (glow_dir), top right by default.
"""
import math

import bpy
from mathutils import Vector

import vfx_kit as V

H = V.hex_lin
# Linear emission colours, solved so that AgX Punchy shows them as the sRGB in the comment
# (AgX dulls flat hex colours: the first try came out grey). The deepest blue AgX can show
# is a little darker than the target.
SKY_TOP = (0.0022, 0.153, 2.21)       # (55, 120, 219) deep, saturated blue at the top of the frame
SKY_MID = (0.0016, 0.451, 2.49)       # (90, 150, 220)
SKY_LOW = (0.0098, 2.09, 6.56)        # (169, 206, 241) pale near the horizon
GLOW = (21.8, 14.6, 2.5)              # (254, 246, 227) warm sun glow
HALO = (2.4, 6.6, 11.0)               # pale cyan-white around the sun (blue mixed with warm reads lilac)
FIELD_FAR = (0.271, 1.51, 0.036)      # (131, 192, 84) sunlit field near the horizon
FIELD_NEAR = (0.070, 0.508, 0.055)    # (62, 140, 42) greener towards the camera
TREES = (0.132, 0.559, 0.205)         # (86, 146, 97) soft tree line, hazed by distance


def view_dir(cam_loc, aim, lens, screen=(0.85, 0.95), aspect=9 / 16):
    """World direction that lands at a screen position (x right, y up, -1..1) for a camera at
    cam_loc looking at aim with this lens (vertical 9:16 frame, 36 mm sensor on the long side)."""
    f = (Vector(aim) - Vector(cam_loc)).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f)
    t = 18.0 / lens
    return (f + r * screen[0] * t * aspect + u * screen[1] * t).normalized()


def _node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def _map(nt, src, a, b, c=0.0, d=1.0, smooth=True):
    m = nt.nodes.new("ShaderNodeMapRange")
    if smooth:
        m.interpolation_type = "SMOOTHSTEP"
    m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = a, b
    m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = c, d
    nt.links.new(src, m.inputs["Value"])
    return m.outputs["Result"]


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


def backdrop(glow_dir=(0.45, 0.55, 0.7), horizon=-13.0, camera_strength=1.0, light_strength=0.22,
             glow=1.0, glow_size=None, lens=50.0, tree_seed=0.0):
    """The world. glow_dir: world direction of the sun glow (see view_dir); glow_size: radius
    of its bright core in degrees (the soft halo is three times wider; keep it well inside
    the lens's field of view). horizon: degrees below eye level where the field starts
    (lower = more sky behind a level close-up). Without glow_size, the glow is sized to the
    lens so it looks the same on screen in wide shots and close-ups.
    Returns the world; its "Backdrop_Camera" node's Strength is what the camera sees."""
    w, nt = V._world()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nrm = nt.nodes.new("ShaderNodeVectorMath")
    nrm.operation = "NORMALIZE"
    nt.links.new(tc.outputs["Generated"], nrm.inputs[0])
    d = nrm.outputs["Vector"]
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(d, sep.inputs[0])
    z = sep.outputs["Z"]
    h0 = math.sin(math.radians(horizon))
    if glow_size is None:
        glow_size = 0.22 * math.degrees(math.atan(18.0 / lens))

    # sky: pale at the horizon, deep blue overhead
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*SKY_LOW, 1)
    els[1].position, els[1].color = 1.0, (*SKY_TOP, 1)
    for pos, c in ((0.1, [(a + b) / 2 for a, b in zip(SKY_LOW, SKY_MID)]), (0.26, SKY_MID)):
        e = els.new(pos)                                          # pale only in a band over the horizon
        e.color = (*c, 1)
    nt.links.new(_map(nt, z, h0, 0.6, smooth=False), ramp.inputs["Fac"])
    sky = ramp.outputs["Color"]

    # sun glow: a bright warm core inside a wide soft halo
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = Vector(glow_dir).normalized()
    nt.links.new(d, dot.inputs[0])
    core = _math(nt, "POWER", _map(nt, dot.outputs["Value"], math.cos(math.radians(1.8 * glow_size)), 1.0), 3.0)
    halo = _math(nt, "POWER", _map(nt, dot.outputs["Value"], math.cos(math.radians(3.5 * glow_size)), 1.0), 2.0)
    sky = _mix(nt, _math(nt, "MULTIPLY", halo, 0.35 * glow), sky, HALO)
    sky = _mix(nt, _math(nt, "MULTIPLY", core, 0.4 * glow), sky, GLOW)

    # land: a soft, uneven tree line, then the field fading greener towards the camera
    flat = nt.nodes.new("ShaderNodeVectorMath")
    flat.operation = "MULTIPLY"
    flat.inputs[1].default_value = (1.0, 1.0, 0.0)
    nt.links.new(d, flat.inputs[0])
    az = nt.nodes.new("ShaderNodeVectorMath")
    az.operation = "NORMALIZE"
    nt.links.new(flat.outputs["Vector"], az.inputs[0])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.5
    noise.inputs["Detail"].default_value = 3.0
    if "W" in noise.inputs:
        noise.noise_dimensions = "4D"
        noise.inputs["W"].default_value = tree_seed
    nt.links.new(az.outputs["Vector"], noise.inputs["Vector"])
    tree_top = _math(nt, "ADD", _math(nt, "MULTIPLY", _map(nt, noise.outputs["Fac"], 0.35, 0.7), 0.05), h0 + 0.008)
    land = _map(nt, _math(nt, "SUBTRACT", z, tree_top), -0.05, 0.03, 1.0, 0.0)          # soft, as if out of focus
    field_ramp = nt.nodes.new("ShaderNodeValToRGB")
    fe = field_ramp.color_ramp.elements
    fe[0].color, fe[1].color = (*FIELD_NEAR, 1), (*FIELD_FAR, 1)
    nt.links.new(_map(nt, z, h0 - 0.45, h0), field_ramp.inputs["Fac"])
    trees = _mix(nt, 0.15, TREES, SKY_LOW)                        # haze
    land_col = _mix(nt, _map(nt, z, h0 - 0.02, h0 + 0.02), field_ramp.outputs["Color"], trees)
    col = _mix(nt, land, sky, land_col)

    cam_bg = _node(nt, "ShaderNodeBackground", Strength=camera_strength)
    cam_bg.name = "Backdrop_Camera"
    amb = _node(nt, "ShaderNodeBackground", Strength=light_strength)
    nt.links.new(col, cam_bg.inputs["Color"])
    nt.links.new(col, amb.inputs["Color"])
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(amb.outputs[0], mix.inputs[1])
    nt.links.new(cam_bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return w


def _area(name, loc, target, size, power, color, col):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape, ld.size, ld.size_y = "DISK", size, size
    ld.energy, ld.color = power, color
    ob = V.link(bpy.data.objects.new(name, ld), col)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def lights(subject, cam_loc, glow_dir, scale=1.0, key=1.0, fill=1.0, rim=1.0, col=None):
    """Soft studio light that matches the backdrop. subject: point the lights aim at;
    scale: roughly the subject size in meters (1 = head and shoulders at ~1-2 m).
    Key: warm-white, high on the camera's right (the sun-glow side). Fill: sky blue, low on
    the left. Rim: the warm sun itself, from the glow's direction, behind the subject."""
    col = col or V.collection("LIGHTS")
    s = Vector(subject)
    to_cam = Vector(cam_loc) - s
    to_cam.z = 0
    to_cam = to_cam.normalized() if to_cam.length > 1e-6 else Vector((0, -1, 0))
    right = to_cam.cross(Vector((0, 0, 1))).normalized() * -1.0  # camera's right as seen from the camera

    def around(yaw, up, dist):
        a = math.radians(yaw)
        h = (to_cam * math.cos(a) + right * math.sin(a)).normalized()
        e = math.radians(up)
        return s + (h * math.cos(e) + Vector((0, 0, math.sin(e)))) * dist

    d = 2.4 * scale
    out = {
        "key": _area("Key_Light", around(48, 38, d), s, 1.8 * scale, 260 * key * scale ** 2, H("#FFF1DE"), col),
        "fill": _area("Fill_Light", around(-60, 8, d), s, 2.6 * scale, 110 * fill * scale ** 2, H("#BFE3FA"), col),
    }
    sun = bpy.data.lights.new("Sun_Rim", "SUN")
    sun.energy, sun.color, sun.angle = 3.2 * rim, H("#FFE7C2"), math.radians(6)
    ob = V.link(bpy.data.objects.new("Sun_Rim", sun), col)
    g = Vector(glow_dir).normalized()
    g = Vector((g.x, g.y, max(g.z, 0.25))).normalized()           # keep the sun above the horizon
    ob.rotation_euler = (-g).to_track_quat("-Z", "Y").to_euler()
    out["rim"] = ob
    return out
