"""Inside-the-mouth set for shots 8-12: palate dome with rugae ridges and a gum ridge,
upper teeth along the dental arch, a raised tongue, the cold ice cream lump pressed
against the palate, a cheek cavity that closes the set, and a mucosa material with
animated controls (frost growth, glowing frost front, ripple rings, warm glow, x-ray).
Real scale: palate ~6 cm long. The mouth opening faces -Y; up is +Z."""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
ARCH_A, ARCH_B, ARCH_C = 0.0225, 0.026, -0.004   # dental arch: half-width, front depth, y where the sides go straight


def arch_r(x, y):
    """Normalised distance from the arch centre: 1 on the dental arch, <1 inside it."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    yy = np.where(y < ARCH_C, (y - ARCH_C) / ARCH_B, 0.0)
    return np.sqrt((x / ARCH_A) ** 2 + yy ** 2)


def palate_height(x, y):
    """Palate surface height (m): vault high in the middle, gum ridge bulging down along
    the arch, transverse rugae in the front third, midline raphe, incisive papilla, and the
    soft palate dropping away at the back."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    r = arch_r(x, y)
    inside = np.clip(1.0 - r ** 2, 0, None)
    dome = 0.017 * inside ** 0.6
    gum = -0.004 * np.exp(-((r - 1.0) / 0.11) ** 2)
    outside = 0.004 * np.clip((r - 1.12) / 0.25, 0, 1)                 # vestibule rises to the cheek
    phase = (y + 0.03) * 1150 + 3.0 * np.sin(x * 140) + np.abs(x) * 300
    wave = (0.5 + 0.5 * np.sin(phase)) ** 3
    mask = (np.clip((-0.008 - y) / 0.008, 0, 1) * np.clip((y + 0.028) / 0.004, 0, 1)
            * np.exp(-(x / 0.012) ** 2))
    rugae = 0.0007 * wave * mask
    raphe = -0.0003 * np.exp(-(x / 0.0012) ** 2) * np.clip(inside * 3, 0, 1)
    papilla = 0.0009 * np.exp(-((x / 0.0025) ** 2 + ((y + 0.0255) / 0.003) ** 2))
    back = -0.024 * np.clip((y - 0.016) / 0.024, 0, None) ** 2           # soft palate
    return dome + gum + outside + rugae + raphe + papilla + back


def contact(xy=(0.0, 0.003)):
    """Point on the palate surface where the ice cream presses."""
    return Vector((xy[0], xy[1], float(palate_height(xy[0], xy[1]))))


CONTACT = contact()


def arch_points(step=0.0005):
    """Polyline along the dental arch from the front midline back along the left side (+X)."""
    th = np.linspace(0, math.pi / 2, 200)
    front = np.stack([ARCH_A * np.sin(th), ARCH_C - ARCH_B * np.cos(th)], 1)
    side = np.stack([np.full(60, ARCH_A), np.linspace(ARCH_C, ARCH_C + 0.024, 60)], 1)
    P = np.concatenate([front, side[1:]])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    s = np.arange(0, L[-1], step)
    return np.stack([np.interp(s, L, P[:, 0]), np.interp(s, L, P[:, 1])], 1), s


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------
def build_palate(col, n=240):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=0.04)
    for v in bm.verts:
        x, y = v.co.x * 0.85, v.co.y
        v.co = Vector((x, y, float(palate_height(x, y))))
    bmesh.ops.reverse_faces(bm, faces=bm.faces)                   # face down, toward the mouth
    me = bpy.data.meshes.new("Palate_geo")
    bm.to_mesh(me)
    bm.free()
    ob = V.link(bpy.data.objects.new("Palate_geo", me), col)
    K.shade_smooth(ob)
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.003
    sol.offset = -1.0                                             # tissue thickness goes up, normals stay outward
    return ob


def build_cavity(col, mat):
    """Cheeks, floor and throat around the set (normals inward), open at the front. The
    part above the palate is removed so the x-ray shots can see up into the head."""
    ob = K.ellipsoid("Mouth_Cavity_geo", (0, 0.006, -0.012), (0.033, 0.052, 0.034), segments=96, col=col)
    bm = bmesh.new()
    bm.from_mesh(ob.data)

    def hidden_above(c):
        return abs(c.x) < 0.033 and abs(c.y) < 0.039 and c.z > float(palate_height(c.x, c.y)) + 0.001
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y < -0.034
                               or hidden_above(f.calc_center_median())], context="FACES")
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    K.skin(ob, 0.006, 0.0012, octaves=3, seed=12)
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")                # closed shell keeps SSS well-behaved
    sol.thickness = 0.002
    sol.offset = -1.0
    V.assign(ob, mat)
    return ob


def build_teeth(col):
    """Upper teeth placed by width along the dental arch, embedded in the gum ridge."""
    enamel = V.principled("Enamel", H("#FFF6E6"), rough=0.2, sss=0.3, sss_radius=(1.0, 0.85, 0.6),
                          sss_scale=0.002, spec=0.55, coat=0.45)
    V.color_variation(enamel, H("#EFE0C4"), scale=60, amount=0.5)
    pts, s = arch_points()
    # (mesiodistal width, buccolingual depth, crown height): incisors -> molars
    dims = [(0.0085, 0.0068, 0.0105), (0.0066, 0.006, 0.0092), (0.0076, 0.0078, 0.0102),
            (0.007, 0.0088, 0.0086), (0.0066, 0.0088, 0.0082), (0.0098, 0.0104, 0.0076),
            (0.009, 0.0098, 0.0072)]
    teeth = []
    for side in (1, -1):
        at = 0.0003
        for i, (w, d, h) in enumerate(dims):
            c = at + w / 2
            at += w + 0.0003
            k = min(int(c / 0.0005), len(pts) - 2)
            x, y = pts[k]
            tx, ty = pts[k + 1] - pts[k]
            ang = math.degrees(math.atan2(ty, tx))
            x *= side
            if side < 0:
                ang = 180 - ang
            top = float(palate_height(x, y)) + 0.0014
            z = top - h / 2
            t = K.ellipsoid(f"Tooth_{'L' if side > 0 else 'R'}{i}", (x, y, z), (w * 0.5, d * 0.5, h * 0.5),
                            rot=(0, 0, ang), segments=32, col=col)
            P = K.co(t)
            u = np.clip((z - P[:, 2]) / (h * 0.5), 0, 1)              # 0 at middle, 1 at the biting edge
            P[:, 2] = np.where(u > 0.55, z - h * 0.5 * (0.55 + (u - 0.55) * 0.35), P[:, 2])
            K.set_co(t, P)
            K.smooth(t, iterations=2, factor=0.4)
            teeth.append(t)
    ob = K.join(teeth, "Teeth_Upper_geo", col)
    add_xray(enamel, rim="#F4F8FF", strength=2.2, tint="#F4F6FF", rim_start=0.45)   # glowing dental x-ray
    V.assign(ob, enamel)
    return ob


def build_tongue(col, top_z=-0.0026):
    t = K.ellipsoid("Tongue_geo", (0, 0.008, top_z - 0.011), (0.0172, 0.036, 0.011), segments=96, col=col)
    K.voxel_remesh(t, 0.0006)
    P = K.co(t)                                                       # the tongue pushes up under the lump
    w = np.exp(-((((P[:, 0] - CONTACT.x) / 0.015) ** 2 + ((P[:, 1] - CONTACT.y) / 0.019) ** 2) ** 2))   # broad, flat-topped
    P[:, 2] += 0.0062 * w * np.clip((P[:, 2] - (top_z - 0.006)) / 0.006, 0, 1)
    K.set_co(t, P)
    K.crease(t, K.path_line((0, -0.026, top_z), (0, 0.04, top_z), 40), 0.004, 0.0009, symmetry_x=False)
    K.skin(t, 0.0012, 0.00022, octaves=3, seed=4)                       # papillae
    V.assign(t, V.principled("Tongue", H("#E07080"), rough=0.36, sss=0.4, sss_radius=(1.0, 0.35, 0.3),
                             sss_scale=0.003, coat=0.3))
    V.bump(t.data.materials[0], scale=2200, strength=0.25, distance=0.00015)
    add_xray(t.data.materials[0])
    return t


def build_lump(col, mat, center=None, radii=(0.0102, 0.0112, 0.0068)):
    """Cold ice cream lump squashed against the palate. The object origin sits at the
    contact point so scale keys squash it against the roof of the mouth."""
    c = CONTACT if center is None else Vector(center)
    lump = K.ellipsoid("IceCream_Lump_geo", (c.x, c.y, c.z - radii[2]), radii, segments=64, col=col)
    K.voxel_remesh(lump, 0.0003)
    K.skin(lump, 0.007, 0.0012, octaves=3, seed=8)                   # soft, creamy mass
    K.skin(lump, 0.0026, 0.0004, octaves=3, ridged=True, seed=9)     # spoon-carved ridges
    K.smooth(lump, iterations=2, factor=0.35)
    P = K.co(lump)
    roof = palate_height(P[:, 0], P[:, 1]) - 0.0002
    k = 0.0015                                                        # smooth-min against the palate
    hh = np.clip(k - np.abs(P[:, 2] - roof), 0, None) / k
    P[:, 2] = np.minimum(P[:, 2], roof) - hh * hh * k * 0.25
    P -= np.array(c)
    K.set_co(lump, P)
    lump.location = c
    K.smooth(lump, iterations=1, factor=0.3)
    V.assign(lump, mat)
    return lump


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
def _sock(nt, v):
    if isinstance(v, (int, float)):
        n = nt.nodes.new("ShaderNodeValue")
        n.outputs[0].default_value = float(v)
        return n.outputs[0]
    return v


def _math(nt, op, a, b=None):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = float(v)
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def _value(nt, name, v=0.0):
    n = nt.nodes.new("ShaderNodeValue")
    n.name = n.label = name
    n.outputs[0].default_value = v
    return n.outputs[0]


def _band(nt, d, r, width):
    """exp(-((d - r) / width)^2): a soft ring at distance r."""
    x = _math(nt, "DIVIDE", _math(nt, "SUBTRACT", d, r), width)
    return _math(nt, "EXPONENT", _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", x, x), -1.0))


def control(mat, name):
    """Output socket of a named animatable control in the material (keyframe its default_value)."""
    return mat.node_tree.nodes[name].outputs[0]


def add_xray(mat, rim="#4E5CFF", strength=1.4, tint="#E4E9FF", rim_start=0.55):
    """Append his x-ray look to a material, driven by its 'XRay' control (0..1): the
    surface turns to clear glass with a thin glowing blue-violet rim, so whatever is
    inside or behind shows through in full colour."""
    nt = mat.node_tree
    out = nt.nodes["Material Output"]
    current = out.inputs["Surface"].links[0].from_socket
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = rim_start
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.97
    ramp.color_ramp.elements[1].color = (0.85, 0.85, 0.85, 1)
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*H(rim), 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*H(tint), 1)
    xmix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ramp.outputs[0], xmix.inputs[0])
    nt.links.new(tr.outputs[0], xmix.inputs[1])
    nt.links.new(em.outputs[0], xmix.inputs[2])
    final = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(_value(nt, "XRay", 0.0), final.inputs[0])
    nt.links.new(current, final.inputs[1])
    nt.links.new(xmix.outputs[0], final.inputs[2])
    nt.links.new(final.outputs[0], out.inputs["Surface"])
    return mat


def mucosa_material(name="Mucosa", center=None, base="#E8828E", dark="#C2566A", rings=3):
    """Wet pink mouth tissue with animatable controls:
    FrostRadius (m) frost layer grows from `center`; FrontGlow glowing frost edge;
    Ring{i}_R / Ring{i}_S ripple rings ahead of the frost (radius m, strength);
    Warm warm orange glow outside the frost; XRay mixes in a see-through x-ray shell."""
    c = CONTACT if center is None else Vector(center)
    m = V.principled(name, H(base), rough=0.24, sss=0.45, sss_radius=(1.0, 0.35, 0.3), sss_scale=0.003,
                     spec=0.6, coat=0.35)
    V.color_variation(m, H(dark), scale=90, amount=0.45)
    V.bump(m, scale=900, strength=0.12, distance=0.0002)
    nt = m.node_tree
    b = V.bsdf(m)
    out = nt.nodes["Material Output"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "DISTANCE"
    dist.inputs[1].default_value = tuple(c)
    nt.links.new(geo.outputs["Position"], dist.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 260.0
    nz.inputs["Detail"].default_value = 6.0
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    d = _math(nt, "ADD", dist.outputs["Value"], _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", nz.outputs["Fac"], 0.5),
                                                      0.005))
    # frost layer
    fr = _value(nt, "FrostRadius", 0.0)
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(d, mr.inputs["Value"])
    nt.links.new(fr, mr.inputs["From Min"])
    nt.links.new(_math(nt, "SUBTRACT", fr, 0.0025), mr.inputs["From Max"])
    frost_mask = mr.outputs["Result"]
    frost = nt.nodes.new("ShaderNodeBsdfPrincipled")
    frost.inputs["Roughness"].default_value = 0.38
    V._inp(frost, "Emission Color", "Emission").default_value = (*H("#9ED6FF"), 1)
    V._inp(frost, "Emission Strength").default_value = 0.1
    for names, val in ((("Coat Weight", "Clearcoat"), 1.0), (("Coat Roughness", "Clearcoat Roughness"), 0.04)):
        sk = V._inp(frost, *names)
        if sk is not None:
            sk.default_value = val
    thick = nt.nodes.new("ShaderNodeMapRange")                     # 0 at the frost edge -> 1 deep inside
    nt.links.new(d, thick.inputs["Value"])
    nt.links.new(fr, thick.inputs["From Min"])
    nt.links.new(_math(nt, "SUBTRACT", fr, 0.009), thick.inputs["From Max"])
    fcol = nt.nodes.new("ShaderNodeMix")
    fcol.data_type = "RGBA"
    fcol.inputs[6].default_value = (*H("#BFE6FF"), 1)               # thin frost: icy blue
    fcol.inputs[7].default_value = (*H("#F7FBFF"), 1)               # thick frost: white
    nt.links.new(thick.outputs["Result"], fcol.inputs[0])
    nt.links.new(fcol.outputs[2], frost.inputs["Base Color"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")                      # crystal facets that glint
    vor.inputs["Scale"].default_value = 1100.0
    nt.links.new(geo.outputs["Position"], vor.inputs["Vector"])
    fnz = nt.nodes.new("ShaderNodeTexNoise")
    fnz.inputs["Scale"].default_value = 3000.0
    nt.links.new(geo.outputs["Position"], fnz.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.8
    bp.inputs["Distance"].default_value = 0.00025
    nt.links.new(_math(nt, "ADD", vor.outputs["Distance"], _math(nt, "MULTIPLY", fnz.outputs["Fac"], 0.5)),
                 bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], frost.inputs["Normal"])
    cn = V._inp(frost, "Coat Normal", "Clearcoat Normal")
    if cn is not None:
        nt.links.new(bp.outputs["Normal"], cn)
    surf = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(frost_mask, surf.inputs[0])
    nt.links.new(b.outputs[0], surf.inputs[1])
    nt.links.new(frost.outputs[0], surf.inputs[2])
    # glowing frost front + ripple rings (icy cyan), warm glow (orange)
    glow = _math(nt, "MULTIPLY", _band(nt, d, fr, 0.0009), _value(nt, "FrontGlow", 0.0))
    for i in range(rings):
        ring = _math(nt, "MULTIPLY", _band(nt, dist.outputs["Value"], _value(nt, f"Ring{i}_R", 0.0), 0.0006),
                     _value(nt, f"Ring{i}_S", 0.0))
        glow = _math(nt, "ADD", glow, ring)
    cyan = nt.nodes.new("ShaderNodeEmission")
    cyan.inputs["Color"].default_value = (*H("#2EC0FF"), 1)
    nt.links.new(_math(nt, "MULTIPLY", glow, 3.5), cyan.inputs["Strength"])
    # warm glow: bright band just outside the melting frost edge + a soft warmth that fades outward
    warm_mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(d, warm_mr.inputs["Value"])
    nt.links.new(fr, warm_mr.inputs["From Min"])
    nt.links.new(_math(nt, "ADD", fr, 0.0015), warm_mr.inputs["From Max"])
    warm_band = _math(nt, "MULTIPLY", _band(nt, d, _math(nt, "ADD", fr, 0.0025), 0.0022), 1.0)
    warm_fall = _math(nt, "MULTIPLY", _math(nt, "EXPONENT", _math(nt, "MULTIPLY", dist.outputs["Value"], -70.0)), 0.35)
    warm_amt = _math(nt, "MULTIPLY", warm_mr.outputs["Result"], _math(nt, "ADD", warm_band, warm_fall))
    warm = nt.nodes.new("ShaderNodeEmission")
    warm.inputs["Color"].default_value = (*H("#FF5208"), 1)
    nt.links.new(_math(nt, "MULTIPLY", warm_amt, _math(nt, "MULTIPLY", _value(nt, "Warm", 0.0), 1.6)),
                 warm.inputs["Strength"])
    add1 = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(surf.outputs[0], add1.inputs[0])
    nt.links.new(cyan.outputs[0], add1.inputs[1])
    add2 = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(add1.outputs[0], add2.inputs[0])
    nt.links.new(warm.outputs[0], add2.inputs[1])
    nt.links.new(add2.outputs[0], out.inputs["Surface"])
    add_xray(m)
    return m


def ice_cream_material(name="IceCream_Vanilla_Mouth"):
    m = V.principled(name, H("#FFF7EA"), rough=0.28, sss=0.5, sss_radius=(1.0, 0.8, 0.6),
                     sss_scale=0.003, spec=0.5, coat=0.35)
    V.color_variation(m, H("#F2DDB4"), scale=180, amount=0.6)                 # creamy tone variation
    V.color_variation(m, H("#5A3A26"), scale=380, amount=1.0, threshold=0.75)  # vanilla bean specks
    V.bump(m, scale=600, strength=0.25, distance=0.0002)
    add_xray(m, rim="#DDE8FF", strength=1.2, tint="#F2F6FF")
    return m


def build(col_name="SET_MOUTH", lump=True):
    col = V.collection(col_name)
    muc = mucosa_material()
    palate = build_palate(col)
    V.assign(palate, muc)
    cheek = mucosa_material("Mucosa_Cheek", base="#D86E7E", dark="#A9475A", rings=0)
    cavity = build_cavity(col, cheek)
    teeth = build_teeth(col)
    tongue = build_tongue(col)
    parts = {"col": col, "palate": palate, "mucosa": muc, "cheek_mat": cheek, "cavity": cavity, "teeth": teeth,
             "tongue": tongue}
    if lump:
        parts["lump"] = build_lump(col, ice_cream_material())
    return parts
