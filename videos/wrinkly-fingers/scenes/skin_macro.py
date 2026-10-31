"""The skin of his fingertip up close (shot 06): fingerprint ridges like rolling hills, with
sweat pores along their tops, and drops of water that seep into the pores.

Stylised large scale in metres: the ridges are 0.1 m apart (0.45 mm on a real finger), so depth
of field behaves like a normal macro shot. The ridges are arcs of a whorl centred far off to
one side, with a slow wobble (real ridges are never perfect). The camera looks along +Y.
"""
import math

import bpy
import numpy as np
from mathutils import Vector

import sky_set as SKY
import vfx_kit as V

H = V.hex_lin
LAMBDA = 0.1                 # ridge spacing
AMP = 0.024                  # ridge height
CENTRE = (-4.0, -3.0)        # the whorl's centre, far off: here the ridges cross the view at about 45 degrees
PORE_R, PORE_D = 0.018, 0.045
SKIN = H("#E4A08A")
HAZE = "#E9B49E"             # the warm glow far away (the world's horizon colour)
NEAR = (-0.45, 0.45, 0.3, 2.4)       # x0, x1, y0, y1 of the detailed patch (pores, 2.5 mm grid)
FAR = (-1.0, 1.0, 2.3, 7.5)          # beyond it, out of focus, fading into haze (1.25 cm grid; the frame
                                     # never sees further than about 6 m)


def ridge_phase(X, Y):
    """Which ridge a point is on (integers on the crests)."""
    r = np.hypot(X - CENTRE[0], (Y - CENTRE[1]) * 0.94)
    wob = 0.03 * np.sin(Y * 1.7 + 0.6) + 0.018 * np.sin(Y * 4.1 + X * 2.3) + 0.01 * np.sin(X * 6.0 - Y * 3.1)
    return (r + wob) / LAMBDA


def ridges(X, Y):
    c = 0.5 + 0.5 * np.cos(2 * np.pi * ridge_phase(X, Y))
    return AMP * c ** 1.6 * (0.85 + 0.15 * np.sin(Y * 3.3 + X * 1.1))          # crests rise and fall a little


def pores(rng, spacing=0.07):
    """Pore centres along the crests in the detailed patch: [(x, y, z)]."""
    x0, x1, y0, y1 = NEAR
    corners = [(x, y) for x in (x0, x1) for y in (y0, y1)]
    ph = [ridge_phase(np.array(x), np.array(y)) for x, y in corners]
    out = []
    for n in range(int(math.floor(min(ph))) - 1, int(math.ceil(max(ph))) + 2):
        R = n * LAMBDA
        th = np.arange(0.0, math.pi / 2, spacing / R)
        th = th + rng.uniform(0, spacing / R)
        for t in th:
            x, y = CENTRE[0] + R * math.cos(t), CENTRE[1] + R * math.sin(t) / 0.94
            if not (x0 + 0.03 < x < x1 - 0.03 and y0 + 0.03 < y < y1 - 0.03):
                continue
            # slide across the ridge onto its crest (the wobble moves it a little)
            d = np.array([x - CENTRE[0], (y - CENTRE[1]) / 0.94])
            d /= np.linalg.norm(d)
            s = np.linspace(-0.5 * LAMBDA, 0.5 * LAMBDA, 41)
            px, py = x + d[0] * s, y + d[1] * s
            k = int(np.argmax(ridges(px, py)))
            j = rng.normal(0, 0.006, 2)
            out.append((px[k] + j[0] * 0.3, py[k] + j[1], float(ridges(np.array(px[k]), np.array(py[k])))))
    return out


def _grid(name, box, step, height, col, pore_list=()):
    x0, x1, y0, y1 = box
    nx, ny = int(round((x1 - x0) / step)) + 1, int(round((y1 - y0) / step)) + 1
    xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(xs, ys)
    Z = height(X, Y)
    P = np.zeros_like(Z)
    for (px, py, _) in pore_list:                                       # dig the pores
        i0, i1 = np.searchsorted(ys, [py - 2 * PORE_R, py + 2 * PORE_R])
        j0, j1 = np.searchsorted(xs, [px - 2 * PORE_R, px + 2 * PORE_R])
        d = np.hypot(X[i0:i1, j0:j1] - px, Y[i0:i1, j0:j1] - py) / PORE_R
        funnel = np.where(d < 1, (1 - d * d) ** 2, 0.0)
        rim = 0.12 * np.exp(-((d - 1.05) / 0.35) ** 2)
        Z[i0:i1, j0:j1] += PORE_D * (rim - funnel)
        P[i0:i1, j0:j1] = np.maximum(P[i0:i1, j0:j1], np.clip(1.25 - d, 0, 1))
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1).astype(np.float32)
    idx = np.arange(nx * ny).reshape(ny, nx)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(faces.size)
    me.loops.foreach_set("vertex_index", faces.ravel().astype(np.int32))
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
    me.update(calc_edges=True)
    me.polygons.foreach_set("use_smooth", np.ones(len(faces), bool))
    at = me.attributes.new("pore", "FLOAT", "POINT")
    at.data.foreach_set("value", P.ravel().astype(np.float32))
    return V.link(bpy.data.objects.new(name, me), col)


def skin_material(name="Skin_Macro", haze=(2.5, 14.0)):
    """Soft, translucent, wet skin; the pores are dark openings (the "pore" attribute)."""
    m = V.principled(name, SKIN, rough=0.4, sss=0.5, sss_radius=(1.0, 0.35, 0.2), sss_scale=0.06, spec=0.5, coat=0.45)
    b = V.bsdf(m)
    nt = m.node_tree
    if V._inp(b, "Coat Roughness") is not None:
        V._inp(b, "Coat Roughness").default_value = 0.12               # a film of water on top
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "pore"
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 9.0
    tex.inputs["Detail"].default_value = 6.0
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs[0].default_value = 0.35
    tint.inputs[6].default_value = (*SKIN, 1)
    nt.links.new(tex.outputs["Color"], tint.inputs[7])                 # blotchy, like real skin
    dark = nt.nodes.new("ShaderNodeMix")
    dark.data_type, dark.blend_type = "RGBA", "MIX"
    nt.links.new(at.outputs["Fac"], dark.inputs[0])
    nt.links.new(tint.outputs[2], dark.inputs[6])
    dark.inputs[7].default_value = (*H("#2A0705"), 1)
    nt.links.new(dark.outputs[2], b.inputs["Base Color"])
    open_ = SKY._math(nt, "SUBTRACT", 1.0, at.outputs["Fac"])           # no wet sheen or glow inside the pores
    for names, val in ((("Coat Weight", "Clearcoat"), 0.45), (("Subsurface Weight", "Subsurface"), 0.5)):
        sock = V._inp(b, *names)
        if sock is not None:
            nt.links.new(SKY._math(nt, "MULTIPLY", open_, val), sock)
    V.bump(m, scale=60.0, strength=0.12, distance=0.002)
    # haze: far away the skin melts into the warm glow behind it (rolling hills into the distance)
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    surf = out.inputs["Surface"].links[0].from_socket
    cam = nt.nodes.new("ShaderNodeCameraData")
    fade = nt.nodes.new("ShaderNodeMapRange")
    fade.interpolation_type = "SMOOTHSTEP"
    fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = haze[0], haze[1]
    nt.links.new(cam.outputs["View Distance"], fade.inputs["Value"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*H(HAZE), 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fade.outputs["Result"], mix.inputs[0])
    nt.links.new(surf, mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def build(col=None, seed=3):
    """The skin: the detailed patch with its pores, and the out-of-focus skin beyond.
    Returns dict(near, far, pores, mat)."""
    col = col or V.collection("SKIN")
    rng = np.random.default_rng(seed)
    pl = pores(rng)
    mat = skin_material()
    near = _grid("Skin_Near", NEAR, 0.0025, ridges, col, pl)
    far = _grid("Skin_Far", FAR, 0.0125, lambda X, Y: ridges(X, Y) - 0.0015, col)
    for ob in (near, far):
        V.assign(ob, mat)
    return {"near": near, "far": far, "pores": pl, "mat": mat}


def world(horizon=HAZE, sky="#F6D2BE", camera_strength=1.0, light_strength=0.5):
    """Beyond the skin: a soft warm glow (more skin, far out of focus)."""
    w, nt = V._world()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mp = nt.nodes.new("ShaderNodeMapRange")
    mp.inputs["From Min"].default_value, mp.inputs["From Max"].default_value = -1.0, 1.0
    nt.links.new(sep.outputs["Z"], mp.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.5, (*H(horizon), 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.75, (*H(sky), 1)
    nt.links.new(mp.outputs["Result"], ramp.inputs["Fac"])
    SKY._finish(nt, ramp.outputs["Color"], camera_strength, light_strength)
    return w


def seep(name, pore, start, radius=0.024, col=None, mat=None):
    """A bead of water sitting on a pore seeps into it: the dome shrinks and drains down the
    hole from frame `start` (about 12 frames)."""
    import hand_set as HS
    col = col or V.collection("FX")
    mat = mat or HS.drop_material()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16, location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(mat)
    x, y, z = pore
    top = z + PORE_D * 0.12
    keys = [(1, (1.0, 1.0, 0.62), 0.45), (start, (1.0, 1.0, 0.62), 0.45), (start + 3, (0.88, 0.88, 0.56), 0.3),
            (start + 6, (0.66, 0.66, 0.46), 0.05), (start + 9, (0.4, 0.4, 0.34), -0.3), (start + 12, (0.14, 0.14, 0.18), -0.9),
            (start + 13, (0.0, 0.0, 0.0), -1.1)]                    # a dome that drains down the hole
    for f, s, dz in keys:
        ob.location = (x, y, top + radius * dz)
        ob.scale = s
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("scale", frame=f)
    V.ease_id(ob, "BEZIER")
    return ob
