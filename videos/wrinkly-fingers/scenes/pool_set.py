"""The sunny backyard pool (shots 01-03, 12-13, 15-16).

He stands chest-deep in the water with his back to the pool wall. The set is laid out around
him: the water surface at z = 0, the wall behind him at y = WALL_Y (he faces -Y, like every
MPFB character), the floor DEPTH below, a warm sandstone edge (coping) and deck behind the
wall, and the pool running on in front of him and to the sides, far enough that the camera
never sees its other walls.

- Background and light: Poly Haven "Pool" HDRI (CC0), palms and a garden around a pool. Its
  sky is a soft, pale overcast: the camera sees it pushed towards a clear sunny blue, while
  the light keeps the real HDRI.
- Tiles: Poly Haven "Rounded Square Tiled Wall" (CC0) mosaic, recoloured pale aqua, with a
  deeper blue band at the waterline. Light patterns (caustics) dance over them; they brighten
  the tiles' colour, so they fade in shadows like real ones.
- Edge and deck: Poly Haven "Patio Tiles" (CC0), warm sandstone.
- Water: clear and turquoise, gently rippling. It casts no shadow, so the sun reaches the floor
  in both engines (the caustics are drawn into the tiles instead).
- Props: Poly Haven "Rubber Duck Toy" (CC0) and a modelled glass marble.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "..", "..", "sneeze", "scenes"), os.path.join(HERE, "..", "..", "production")):
    _p = os.path.abspath(_p)
    if _p not in sys.path:
        sys.path.append(_p)

import sky_set as SKY  # noqa: E402
import vfx_kit as V  # noqa: E402

H = V.hex_lin
WATER_Z = 0.0
DEPTH = 1.2                    # water depth: up to his lower chest, so the shirt print stays dry
WALL_Y = 0.30                  # the wall behind him
COPING_TOP = 0.11              # top of the stone edge above the water
COPING_DEPTH = 0.36            # front to back
EXTENT_X = (-14.0, 14.0)
EXTENT_Y = -28.0               # the pool runs this far in front of him
DECK_Y = 16.0                  # and the deck this far behind
HDRI = "pool"
TILE = "rounded_square_tiled_wall"   # 2 m per texture repeat
STONE = "patio_tiles"                # 2.15 m per repeat
TILE_COLOR = H("#CBEBF0")           # pale aqua mosaic
BAND_COLOR = H("#2D7FB8")           # deeper blue band at the waterline
SUN_COLOR = H("#FFE7C4")
CAUSTIC_SPEED = 0.45


def _col(name):
    return V.collection(name)


# --------------------------------------------------------------------------
# World: the garden HDRI, with a sunny blue sky for the camera
# --------------------------------------------------------------------------
def world(rot_deg=-8.0, strength=0.9, camera_strength=1.0, sky=True, light_sky=0.6):
    """Poly Haven "Pool" HDRI. rot_deg turns the garden behind him. sky: the camera sees the
    pale overcast sky pushed to blue (bright, low-saturation pixels above the trees);
    light_sky: how much of that blue the light and reflections get (with the plain HDRI the
    water reflected a white sky, a milky veil over everything under it)."""
    path = V.polyhaven(HDRI, "hdris", "4k")
    w, nt = V._world()
    L = nt.links
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rot_deg)
    L.new(tc.outputs["Generated"], mp.inputs["Vector"])
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path, check_existing=True)
    L.new(mp.outputs["Vector"], env.inputs["Vector"])
    light = nt.nodes.new("ShaderNodeBackground")
    light.inputs["Strength"].default_value = strength
    L.new(env.outputs["Color"], light.inputs["Color"])
    cam_col = env.outputs["Color"]
    light_col = env.outputs["Color"]
    if sky:
        nrm = nt.nodes.new("ShaderNodeVectorMath")
        nrm.operation = "NORMALIZE"
        L.new(tc.outputs["Generated"], nrm.inputs[0])
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        L.new(nrm.outputs[0], sep.inputs[0])
        hsv = nt.nodes.new("ShaderNodeSeparateColor")
        hsv.mode = "HSV"
        L.new(env.outputs["Color"], hsv.inputs[0])
        up = SKY._map(nt, sep.outputs["Z"], math.sin(math.radians(9)), math.sin(math.radians(24)))
        bright = SKY._map(nt, hsv.outputs["Blue"], 0.55, 1.4)            # value channel: the bright sky
        grey = SKY._map(nt, hsv.outputs["Green"], 0.32, 0.12)            # low saturation: not leaves
        mask = SKY._math(nt, "MULTIPLY", SKY._math(nt, "MULTIPLY", up, bright), grey)
        tint = SKY._mix(nt, SKY._map(nt, sep.outputs["Z"], 0.15, 0.85), SKY.SKY_LOW, SKY.SKY_TOP)
        cloud = SKY._math(nt, "MULTIPLY", SKY._map(nt, hsv.outputs["Blue"], 1.4, 3.0, 0.0, 0.35), 1.0)
        tinted = SKY._mix(nt, cloud, tint, (2.6, 2.75, 2.9))           # a few soft white clouds stay
        cam_col = SKY._mix(nt, SKY._math(nt, "MULTIPLY", mask, 0.92), cam_col, tinted)
        light_col = SKY._mix(nt, SKY._math(nt, "MULTIPLY", mask, light_sky), light_col, tinted)
        # light from below the horizon is the HDRI's own turquoise pool: in EEVEE it lit his chin
        # and neck grey-green, so it comes in dimmer and less green
        below = SKY._map(nt, sep.outputs["Z"], 0.0, -0.35, 1.0, 0.55)
        warm = SKY._mix(nt, SKY._map(nt, sep.outputs["Z"], 0.0, -0.35, 0.0, 0.5), light_col, (0.75, 0.68, 0.6))
        dim = nt.nodes.new("ShaderNodeMix")
        dim.data_type, dim.blend_type = "RGBA", "MULTIPLY"
        dim.inputs[0].default_value = 1.0
        L.new(warm, dim.inputs[6])
        gray = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3):
            L.new(below, gray.inputs[i])
        L.new(gray.outputs[0], dim.inputs[7])
        L.new(dim.outputs[2], light.inputs["Color"])
    cam = nt.nodes.new("ShaderNodeBackground")
    cam.inputs["Strength"].default_value = camera_strength
    L.new(cam_col, cam.inputs["Color"])
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    L.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    L.new(light.outputs[0], mix.inputs[1])
    L.new(cam.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs[0])
    return w


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def _quad(name, corners, uvs, col, cuts=(1, 1)):
    """A flat quad (optionally a grid of cuts) with UVs in metres."""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    nx, ny = cuts
    c = [Vector(p) for p in corners]
    verts = [[bm.verts.new(c[0].lerp(c[1], i / nx).lerp(c[3].lerp(c[2], i / nx), j / ny)) for i in range(nx + 1)]
             for j in range(ny + 1)]
    uv_layer = bm.loops.layers.uv.new("UVMap")
    u = [Vector(p) for p in uvs]
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                s, t = a / nx, b / ny
                loop[uv_layer].uv = u[0].lerp(u[1], s).lerp(u[3].lerp(u[2], s), t)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    V.link(ob, col)
    return ob


def _time_value(nt, name="Caustic_Time"):
    """A Value node that counts seconds (keyed linearly) for moving patterns."""
    v = nt.nodes.new("ShaderNodeValue")
    v.name = v.label = name
    fps = bpy.context.scene.render.fps
    s = v.outputs[0]
    for f in (0, 3000):
        s.default_value = f / fps * CAUSTIC_SPEED
        s.keyframe_insert("default_value", frame=f)
    for fc in V.fcurves(nt):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return s


def _caustics(nt, L, vec, time, scale=1.7):
    """Bright, thin, wobbling light lines (two warped Voronoi edge layers). vec: metres."""
    def node(kind, **kw):
        n = nt.nodes.new(kind)
        for k, v in kw.items():
            setattr(n, k, v)
        return n
    warp = node("ShaderNodeTexNoise", noise_dimensions="4D")
    warp.inputs["Scale"].default_value = 0.9
    warp.inputs["Detail"].default_value = 1.0
    L.new(vec, warp.inputs["Vector"])
    L.new(time, warp.inputs["W"])
    wv = node("ShaderNodeVectorMath", operation="MULTIPLY_ADD")
    wv.inputs[1].default_value = (0.22, 0.22, 0.22)
    L.new(warp.outputs["Color"], wv.inputs[0])
    L.new(vec, wv.inputs[2])
    total = None
    for sc, width, gain, off in ((scale, 0.075, 0.75, 0.0), (scale * 1.7, 0.06, 0.45, 3.1)):
        v = node("ShaderNodeTexVoronoi", voronoi_dimensions="4D", feature="DISTANCE_TO_EDGE")
        v.inputs["Scale"].default_value = sc
        L.new(wv.outputs[0], v.inputs["Vector"])
        t = node("ShaderNodeMath", operation="ADD")
        t.inputs[1].default_value = off
        L.new(time, t.inputs[0])
        L.new(t.outputs[0], v.inputs["W"])
        line = SKY._map(nt, v.outputs["Distance"], 0.0, width, 1.0, 0.0)
        g = SKY._math(nt, "MULTIPLY", line, gain)
        total = g if total is None else SKY._math(nt, "ADD", total, g)
    return total


def tile_material(name, color, band=None, texture_m=2.0, caustic_axes="XY", caustics=True):
    """Pool mosaic: the CC0 tiles' light and shade under a new colour, their roughness and
    normal maps, an optional deeper band at the waterline (band = (z_low, z_high) in
    metres, using the UV v as height), and dancing caustics."""
    maps = V.polyhaven(TILE, "textures", "2k")
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt, L = mat.node_tree, mat.node_tree.links
    b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / texture_m,) * 3
    L.new(tc.outputs["UV"], mp.inputs["Vector"])

    def tex(path, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    d = tex(maps["diffuse"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    L.new(d.outputs["Color"], bw.inputs["Color"])
    shade = SKY._map(nt, bw.outputs["Val"], 0.08, 0.45, 0.55, 1.05, smooth=False)   # grout darker, tiles light
    col = SKY._mix(nt, 1.0, (1, 1, 1), color)
    if band is not None:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        L.new(tc.outputs["UV"], sep.inputs[0])
        lo = SKY._map(nt, sep.outputs["Y"], band[0] - 0.004, band[0] + 0.004)
        hi = SKY._map(nt, sep.outputs["Y"], band[1] + 0.004, band[1] - 0.004)
        col = SKY._mix(nt, SKY._math(nt, "MULTIPLY", lo, hi), col, BAND_COLOR)
    base = nt.nodes.new("ShaderNodeMix")
    base.data_type, base.blend_type = "RGBA", "MULTIPLY"
    base.inputs[0].default_value = 1.0
    L.new(col, base.inputs[6])
    sh = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        L.new(shade, sh.inputs[i])
    L.new(sh.outputs[0], base.inputs[7])
    out = base.outputs[2]
    if caustics:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        L.new(geo.outputs["Position"], sep.inputs[0])
        cmb = nt.nodes.new("ShaderNodeCombineXYZ")
        a, bb = caustic_axes
        L.new(sep.outputs[a], cmb.inputs["X"])
        L.new(sep.outputs[bb], cmb.inputs["Y"])
        c = _caustics(nt, L, cmb.outputs[0], _time_value(nt))
        # brighter only under the water (the light patterns come from the rippling surface)
        under = SKY._map(nt, sep.outputs["Z"], WATER_Z + 0.02, WATER_Z - 0.06)
        k = SKY._math(nt, "MULTIPLY", SKY._math(nt, "MULTIPLY", c, under), 1.2)
        gain = SKY._math(nt, "ADD", k, 1.0)
        g3 = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3):
            L.new(gain, g3.inputs[i])
        warm = nt.nodes.new("ShaderNodeMix")
        warm.data_type, warm.blend_type = "RGBA", "MULTIPLY"
        warm.inputs[0].default_value = 1.0
        L.new(out, warm.inputs[6])
        L.new(g3.outputs[0], warm.inputs[7])
        out = warm.outputs[2]
    L.new(out, b.inputs["Base Color"])
    underwater(nt, b)
    r = tex(maps["rough"], True)
    rm = SKY._math(nt, "MULTIPLY", r.outputs["Color"], 0.55)                       # glazed tiles
    L.new(rm, b.inputs["Roughness"])
    n = tex(maps["normal"], True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.8
    L.new(n.outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], b.inputs["Normal"])
    return mat


def stone_material(name="Pool_Stone"):
    """Warm sandstone for the edge and the deck (Poly Haven "Patio Tiles", CC0)."""
    maps = V.polyhaven(STONE, "textures", "2k")
    return V.textured(name, maps, scale=1 / 2.15, rough_mult=1.0, normal_strength=1.0, tint=H("#FFE9D2"))


# --------------------------------------------------------------------------
# The pool
# --------------------------------------------------------------------------
def pool(col=None):
    """Floor, the wall behind him (with the waterline band), the stone edge and the deck."""
    col = col or _col("POOL")
    x0, x1 = EXTENT_X
    z_floor = WATER_Z - DEPTH
    lip = COPING_TOP - 0.055                                        # underside of the edge
    floor = _quad("Pool_Floor", [(x0, EXTENT_Y, z_floor), (x1, EXTENT_Y, z_floor), (x1, WALL_Y, z_floor),
                                 (x0, WALL_Y, z_floor)],
                  [(x0, EXTENT_Y), (x1, EXTENT_Y), (x1, WALL_Y), (x0, WALL_Y)], col)
    floor.data.materials.append(tile_material("Pool_Floor_Tiles", TILE_COLOR))
    wall = _quad("Pool_Wall", [(x0, WALL_Y, z_floor), (x1, WALL_Y, z_floor), (x1, WALL_Y, lip), (x0, WALL_Y, lip)],
                 [(x0, z_floor), (x1, z_floor), (x1, lip), (x0, lip)], col)
    wall.data.materials.append(tile_material("Pool_Wall_Tiles", TILE_COLOR, band=(WATER_Z - 0.13, lip), caustic_axes="XZ"))
    # the edge: a rounded (bullnose) stone slab that overhangs the wall a little
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    edge = bpy.context.active_object
    edge.name = "Pool_Edge"
    for c in list(edge.users_collection):
        c.objects.unlink(edge)
    col.objects.link(edge)
    edge.scale = (x1 - x0, COPING_DEPTH, 0.055)
    edge.location = (0.0, WALL_Y - 0.035 + COPING_DEPTH / 2, COPING_TOP - 0.0275)
    bpy.ops.object.transform_apply(scale=True)
    bev = edge.modifiers.new("Round", "BEVEL")
    bev.width, bev.segments, bev.limit_method = 0.024, 6, "ANGLE"
    edge.data.materials.append(stone_material())
    _box_uvs(edge)
    for p in edge.data.polygons:
        p.use_smooth = True
    deck_y0 = WALL_Y - 0.035 + COPING_DEPTH
    deck = _quad("Pool_Deck", [(x0, deck_y0, COPING_TOP - 0.004), (x1, deck_y0, COPING_TOP - 0.004),
                               (x1, DECK_Y, COPING_TOP - 0.004), (x0, DECK_Y, COPING_TOP - 0.004)],
                 [(x0, deck_y0), (x1, deck_y0), (x1, DECK_Y), (x0, DECK_Y)], col)
    deck.data.materials.append(bpy.data.materials["Pool_Stone"])
    return {"floor": floor, "wall": wall, "edge": edge, "deck": deck}


def _box_uvs(ob, size=1.0):
    """Box-projected UVs in metres (for the edge slab)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [i for i in range(3) if i != ax]
        for loop in f.loops:
            co = ob.matrix_world @ loop.vert.co
            loop[uv].uv = (co[a] / size, co[b] / size)
    bm.to_mesh(ob.data)
    bm.free()


def water(col=None, swell=0.012):
    """The water surface: clear turquoise with ripples (shader) and gentle swells (geometry)."""
    col = col or _col("POOL")
    x0, x1 = EXTENT_X
    ob = _quad("Pool_Water", [(x0, EXTENT_Y, WATER_Z), (x1, EXTENT_Y, WATER_Z), (x1, WALL_Y, WATER_Z),
                              (x0, WALL_Y, WATER_Z)],
               [(x0, EXTENT_Y), (x1, EXTENT_Y), (x1, WALL_Y), (x0, WALL_Y)], col, cuts=(224, 228))
    for p in ob.data.polygons:
        p.use_smooth = True
    tex = bpy.data.textures.new("Pool_Swell", "CLOUDS")
    tex.noise_scale = 1.6
    drift = V.link(bpy.data.objects.new("Pool_Swell_Drift", None), col)
    fps = bpy.context.scene.render.fps
    for f, d in ((0, 0.0), (3000, 3000 / fps * 0.12)):
        drift.location = (d, d * 0.6, 0.0)
        drift.keyframe_insert("location", frame=f)
    for fc in V.fcurves(drift):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    disp = ob.modifiers.new("Swell", "DISPLACE")
    disp.texture, disp.texture_coords, disp.texture_coords_object = tex, "OBJECT", drift
    disp.strength, disp.mid_level = swell, 0.5
    ob.visible_shadow = False                                   # sunlight reaches the floor (both engines)
    ob.data.materials.append(water_material())
    return ob


def water_material(name="Pool_Water", tint=H("#CDF2EC"), ripple=0.45, ior=1.333):
    """See-through water with a mirror sheen that grows at grazing angles (Fresnel). There is
    no refraction: EEVEE's screen-space refraction missed the floor from low angles (it showed
    the HDRI's own pool instead) and Cycles washed everything under it out, so the colour of
    the water comes from underwater() on the things beneath it, the same in both engines."""
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt, L = mat.node_tree, mat.node_tree.links
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    time = _time_value(nt, "Ripple_Time")
    h = None
    for sc, gain in ((1.3, 1.0), (4.2, 0.35), (11.0, 0.12)):
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.noise_dimensions = "4D"
        nz.inputs["Scale"].default_value = sc
        nz.inputs["Detail"].default_value = 2.0
        L.new(geo.outputs["Position"], nz.inputs["Vector"])
        L.new(time, nz.inputs["W"])
        g = SKY._math(nt, "MULTIPLY", nz.outputs["Fac"], gain)
        h = g if h is None else SKY._math(nt, "ADD", h, g)
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = ripple
    bp.inputs["Distance"].default_value = 0.02
    L.new(h, bp.inputs["Height"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*tint, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.015
    L.new(bp.outputs["Normal"], gl.inputs["Normal"])
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = ior
    L.new(bp.outputs["Normal"], fr.inputs["Normal"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    L.new(fr.outputs[0], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(gl.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    for prop, val in (("surface_render_method", "DITHERED"), ("use_transparent_shadow", True),
                      ("use_backface_culling", False)):
        if hasattr(mat, prop):
            setattr(mat, prop, val)
    return mat


# --------------------------------------------------------------------------
# Under the water
# --------------------------------------------------------------------------
UNDER_TINT = (0.2, 0.64, 0.72)      # linear: clear pool water soaks up red first
UNDER_GLOW = (0.012, 0.075, 0.085)  # ...and scatters a little turquoise light back


def underwater(nt, bsdf, full_depth=0.7, tint=UNDER_TINT, glow=UNDER_GLOW):
    """Things under the water take on its colour, more the deeper they are: a stand-in for
    the water's volume that looks the same in EEVEE and Cycles (the water is only a surface).
    Inserts a world-height mix in front of the Principled BSDF's Base Color."""
    L = nt.links
    sock = bsdf.inputs["Base Color"]
    if not sock.is_linked:
        src = nt.nodes.new("ShaderNodeRGB")
        src.outputs[0].default_value = tuple(sock.default_value)
        base = src.outputs[0]
    else:
        base = sock.links[0].from_socket
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep.inputs[0])
    k = SKY._map(nt, sep.outputs["Z"], WATER_Z + 0.004, WATER_Z - full_depth)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.name = "Underwater"
    L.new(k, mix.inputs[0])
    L.new(base, mix.inputs[6])
    mix.inputs[7].default_value = (*tint, 1)
    haze = nt.nodes.new("ShaderNodeMix")
    haze.data_type, haze.blend_type = "RGBA", "ADD"
    L.new(k, haze.inputs[0])
    L.new(mix.outputs[2], haze.inputs[6])
    haze.inputs[7].default_value = (*glow, 1)
    L.new(haze.outputs[2], sock)
    return mix


def underwater_materials(mats, **kw):
    """underwater() on every Principled BSDF in these materials (and in node groups they use)."""
    done = set()
    for m in mats:
        if m is None or not m.node_tree:
            continue
        trees = [m.node_tree] + [n.node_tree for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeGroup" and n.node_tree]
        for nt in trees:
            if nt.name in done or nt.nodes.get("Underwater"):
                continue
            done.add(nt.name)
            for b in [n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"]:
                underwater(nt, b, **kw)


def underwater_hero(hero):
    """His skin, swimwear and print, tinted below the waterline."""
    obs = [hero["body"]] + [p for p in hero["parts"] if any(k in p.name for k in ("shirt", "shorts"))]
    if hero.get("print") is not None:
        obs.append(hero["print"])
    underwater_materials([m for o in obs for m in o.data.materials])


# --------------------------------------------------------------------------
# Props
# --------------------------------------------------------------------------
def duck(col=None, at=(0.55, -0.55), heading=200.0, drift=(0.0, 0.0), bob=0.004, scale_to=0.11):
    """The CC0 rubber duck floating at `at` (x, y), bobbing; drift: metres per second."""
    col = col or _col("POOL")
    objs = V.polyhaven_model("rubber_duck_toy", "1k", col)
    meshes = [o for o in objs if o.type == "MESH"]
    root = V.link(bpy.data.objects.new("Duck", None), col)
    for o in objs:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    size = max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3))
    s = scale_to / size
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    zmin = min(p.z for p in pts)
    root.location.z = WATER_Z - (zmin - root.location.z) - scale_to * 0.22   # sits a little low in the water
    root.rotation_euler.z = math.radians(heading)
    fps = bpy.context.scene.render.fps
    base = Vector((at[0], at[1], root.location.z))
    for f in range(0, 241, 6):
        t = f / fps
        root.location = base + Vector((drift[0] * t, drift[1] * t, bob * math.sin(t * 2.1)))
        root.rotation_euler = (math.radians(2.0 * math.sin(t * 1.7)), math.radians(2.5 * math.sin(t * 1.3 + 1)),
                               math.radians(heading + 6 * math.sin(t * 0.5)))
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
    return root


def marble(col=None, at=(0.12, -0.32, None), radius=0.008):
    """A glass marble with a twisted orange swirl inside (16 mm)."""
    col = col or _col("POOL")
    z = WATER_Z - DEPTH + radius if at[2] is None else at[2]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24, location=(at[0], at[1], z))
    glass = bpy.context.active_object
    glass.name = "Marble"
    for c in list(glass.users_collection):
        c.objects.unlink(glass)
    col.objects.link(glass)
    for p in glass.data.polygons:
        p.use_smooth = True
    gm = V.principled("Marble_Glass", H("#F4FBFF"), rough=0.0, transmission=1.0, ior=1.52, spec=0.6)
    for prop, val in (("surface_render_method", "DITHERED"), ("use_raytrace_refraction", True), ("thickness_mode", "SPHERE")):
        if hasattr(gm, prop):
            setattr(gm, prop, val)
    glass.data.materials.append(gm)
    swirl_mat = V.principled("Marble_Swirl", H("#FF6A1A"), rough=0.35, sss=0.3, spec=0.5)
    for i in range(3):
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=glass.location)
        vane = bpy.context.active_object
        vane.name = f"Marble_Swirl_{i}"
        for c in list(vane.users_collection):
            c.objects.unlink(vane)
        col.objects.link(vane)
        vane.scale = (radius * 0.55, radius * 1.5, 1.0)
        vane.rotation_euler = (math.radians(90), 0.0, math.radians(120 * i))
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        sub = vane.modifiers.new("Dense", "SUBSURF")
        sub.subdivision_type, sub.levels, sub.render_levels = "SIMPLE", 4, 4
        tw = vane.modifiers.new("Twist", "SIMPLE_DEFORM")
        tw.deform_method, tw.deform_axis, tw.angle = "TWIST", "Z", math.radians(170)
        sol = vane.modifiers.new("Thick", "SOLIDIFY")
        sol.thickness = radius * 0.04
        vane.data.materials.append(swirl_mat)
        vane.parent = glass
        vane.matrix_parent_inverse = glass.matrix_world.inverted()
    return glass


# --------------------------------------------------------------------------
# Light
# --------------------------------------------------------------------------
def sun(az=35.0, el=48.0, strength=4.2, angle=1.2, color=SUN_COLOR, col=None):
    """The key: a warm sun. az/el in the look_dir convention (0 = in front of him, -Y;
    90 = his left / screen right in a front view)."""
    col = col or _col("LIGHTS")
    lt = bpy.data.lights.new("Key_Sun", "SUN")
    lt.energy, lt.color, lt.angle = strength, color, math.radians(angle)
    ob = V.link(bpy.data.objects.new("Key_Sun", lt), col)
    a, e = math.radians(az), math.radians(el)
    to_sun = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    ob.rotation_euler = to_sun.to_track_quat("Z", "Y").to_euler()
    return ob


def rim(target, from_dir=(-0.5, 1.0, 0.55), dist=2.6, power=260.0, size=1.6, color=H("#FFD9A8"), col=None):
    """A warm area light behind him to separate him from the garden. It makes no reflections:
    on the water it showed up as a big bright rectangle."""
    col = col or _col("LIGHTS")
    lt = bpy.data.lights.new("Rim", "AREA")
    lt.energy, lt.color, lt.size = power, color, size
    if hasattr(lt, "specular_factor"):
        lt.specular_factor = 0.0                                   # EEVEE
    ob = V.link(bpy.data.objects.new("Rim", lt), col)
    ob.visible_glossy = False                                      # Cycles
    d = Vector(from_dir).normalized()
    ob.location = Vector(target) + d * dist
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return ob


def build(duck_at=(0.55, -0.55), marble_at=(0.12, -0.32, None), hdri_rot=-8.0, sun_az=35.0, sun_el=48.0):
    """The whole set. Returns its parts."""
    col = _col("POOL")
    world(rot_deg=hdri_rot)
    parts = pool(col)
    parts["water"] = water(col)
    parts["duck"] = duck(col, at=duck_at) if duck_at else None
    parts["marble"] = marble(col, at=marble_at) if marble_at else None
    parts["sun"] = sun(sun_az, sun_el)
    sc = bpy.context.scene
    if hasattr(sc, "eevee"):
        for prop, val in (("use_raytracing", True), ("use_shadows", True)):
            if hasattr(sc.eevee, prop):
                setattr(sc.eevee, prop, val)
    return parts
