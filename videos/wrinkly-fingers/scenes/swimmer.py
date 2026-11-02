"""The protagonist ("you") of the wrinkly-fingers video: a young man built with MPFB 2 from CC0
MakeHuman assets (young Asian male skin, eyes, short04 hair, thick straight eyebrow009 brows,
the crude T-shirt worn as a swim shirt, shorts), the default rig for posing and the ARKit face
units for his acting. He is not the brain-freeze guy or the sneeze heroine: different face,
hair, skin and shirt colour.

He has been in the pool all day: dark, glossy wet hair, a wet sheen on the skin (the skin's
clear coat) and a fitted red swim shirt, with a new stretch-fabric material (Poly Haven
"Bi Stretch", CC0) and the channel name printed across the chest. The shared MPFB helpers
(face shapes, posing, the EEVEE eye fix, the chest print) come from brain-freeze/scenes/
character.py; the eye and teeth tuning from sneeze/scenes/heroine.py.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(HERE, "..", "..", "brain-freeze", "scenes"), os.path.join(HERE, "..", "..", "sneeze", "scenes"),
           os.path.join(HERE, "..", "..", "production")):
    _p = os.path.abspath(_p)
    if _p not in sys.path:
        sys.path.append(_p)

import character as C  # noqa: E402
import heroine as HR  # noqa: E402
import vfx_kit as V  # noqa: E402

H = V.hex_lin
CHANNEL_NAME = C.CHANNEL_NAME
SPEC = {
    "phenotype": {"gender": 1.0, "age": 0.42, "muscle": 0.6, "weight": 0.42, "proportions": 0.7, "height": 0.62,
                  "cupsize": 0.5, "firmness": 0.5, "race": {"caucasian": 0.15, "asian": 0.85, "african": 0.0}},
    "rig": "default",
    "eyes": "high-poly/high-poly.mhclo",
    "eyebrows": "eyebrow009/eyebrow009.mhclo",
    "eyelashes": "eyelashes01/eyelashes01.mhclo",
    "teeth": "teeth_base/teeth_base.mhclo",
    "tongue": "tongue01/tongue01.mhclo",
    "hair": "short04/short04.mhclo",
    "clothes": ["elvs_crude_t-shirt_male/elvs_crude_t-shirt_male.mhclo", "cortu_jeans_shorts/cortu_jeans_shorts.mhclo"],
    "skin_mhmat": "young_asian_male/young_asian_male.mhmat",
    "skin_material_type": "ENHANCED_SSS",
    "eyes_material_type": "PROCEDURAL_EYES",
}
SHIRT_COLOR = H("#C8201A")                  # lifeguard red, a little deeper because it's wet
SHORTS_COLOR = H("#1D2B57")                 # navy board shorts
SKIN_TINT = H("#F4D6C0")                    # warms the CC0 young Asian skin texture: a summer tan
HAIR_TINT = H("#3A2A22")                    # multiplies the CC0 hair texture: near-black with brown strands
IRIS = (H("#24160D"), H("#4B2E1B"))         # dark brown eyes (minor, major)
PRINT_INK = H("#F2EEE6")                    # off-white print (never pure white)
FABRIC = "bi_stretch"                       # Poly Haven stretch fabric (CC0), 26.5 cm per repeat


def part(hero, *keys):
    return next((o for o in hero["parts"] if any(k in o.name for k in keys)), None)


def rest_coordinates(hero):
    """rest_co: every vertex's rest-pose position in metres, so the skin's patterns (wet
    patches, droplets, blotches) stay stuck to him when he moves."""
    import numpy as np
    import wrinkles as WR
    me = hero["body"].data
    P, _ = WR.rest_shape(hero["body"])
    if "rest_co" in me.attributes:
        me.attributes.remove(me.attributes["rest_co"])
    me.attributes.new("rest_co", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", P.astype(np.float32).ravel())


def wet_skin(hero, wet=0.6, rough=(0.42, 0.62), drop_size=170.0, pores=0.32):
    """Wet, real-looking skin instead of an even plastic sheen: roughness that varies over
    the body, a film of water in patches (the clear coat) with small droplets beading on it,
    slightly blotchy colour and finer pores. The film and droplets stop at the waterline:
    set_waterline() puts it at the pool's surface (it starts far below, i.e. wet all over).
    drop_size: droplet cells per metre."""
    rest_coordinates(hero)
    for m in hero["body"].data.materials:
        g = next((n for n in (m.node_tree.nodes if m and m.node_tree else []) if n.bl_idname == "ShaderNodeGroup"), None)
        if g is None or g.node_tree.nodes.get("Wet_Line"):
            continue
        nt, L = g.node_tree, g.node_tree.links
        b = nt.nodes["Principled BSDF"]
        g.inputs["Pore strength"].default_value = pores
        co = nt.nodes.new("ShaderNodeAttribute")
        co.attribute_type, co.attribute_name = "GEOMETRY", "rest_co"

        def node(kind, **kw):
            nd = nt.nodes.new(kind)
            for k, v in kw.items():
                setattr(nd, k, v)
            return nd

        def math(op, a, bb=None):
            mm = node("ShaderNodeMath", operation=op)
            for i, x in enumerate((a, bb)):
                if x is None:
                    continue
                if isinstance(x, (int, float)):
                    mm.inputs[i].default_value = x
                else:
                    L.new(x, mm.inputs[i])
            return mm.outputs[0]

        def noise(scale, detail=2.0):
            nz = node("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = scale
            nz.inputs["Detail"].default_value = detail
            L.new(co.outputs["Vector"], nz.inputs["Vector"])
            return nz.outputs["Fac"]

        def remap(x, a, bb, c, d):
            mr = node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
            for k, v in (("From Min", a), ("From Max", bb), ("To Min", c), ("To Max", d)):
                mr.inputs[k].default_value = v
            L.new(x, mr.inputs["Value"])
            return mr.outputs["Result"]
        # roughness that varies: oilier and drier areas, plus fine grain
        r = math("ADD", remap(noise(22.0), 0.3, 0.7, rough[0], rough[1]), math("MULTIPLY", math("SUBTRACT", noise(300.0, 3.0), 0.5), 0.08))
        for lk in list(b.inputs["Roughness"].links):
            L.remove(lk)
        L.new(r, b.inputs["Roughness"])
        # above the waterline only (Wet_Line holds its height; far below = wet all over)
        line = node("ShaderNodeValue")
        line.name = line.label = "Wet_Line"
        line.outputs[0].default_value = -100.0
        geo = node("ShaderNodeNewGeometry")
        sep = node("ShaderNodeSeparateXYZ")
        L.new(geo.outputs["Position"], sep.inputs[0])
        above = remap(math("SUBTRACT", sep.outputs["Z"], line.outputs[0]), 0.0, 0.025, 0.0, 1.0)
        # droplets: a few cells of a Voronoi grid hold a dome of water, each its own size
        vor = node("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="F1")
        vor.inputs["Scale"].default_value = drop_size
        L.new(co.outputs["Vector"], vor.inputs["Vector"])
        rnd = node("ShaderNodeSeparateColor")
        L.new(vor.outputs["Color"], rnd.inputs[0])
        radius = remap(rnd.outputs["Red"], 0.0, 1.0, 0.1, 0.34)
        present = math("GREATER_THAN", rnd.outputs["Green"], 0.48)
        t = math("DIVIDE", vor.outputs["Distance"], radius)
        dome = math("SQRT", math("MAXIMUM", math("SUBTRACT", 1.0, math("MULTIPLY", t, t)), 0.0))
        drop = math("MULTIPLY", math("MULTIPLY", dome, present), above)
        # the film of water: patches, plus wherever a droplet sits
        film = remap(noise(7.0, 3.0), 0.45, 0.62, 0.0, 1.0)
        coat = math("MAXIMUM", math("MULTIPLY", film, wet), math("GREATER_THAN", drop, 0.02))
        coat = math("MULTIPLY", coat, above)
        for sock in ("Coat Weight", "Coat Roughness"):
            for lk in list(b.inputs[sock].links):
                L.remove(lk)
        L.new(coat, b.inputs["Coat Weight"])
        b.inputs["Coat Roughness"].default_value = 0.05
        bump = node("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 0.0012                # 1.2 mm high droplets
        L.new(drop, bump.inputs["Height"])
        L.new(bump.outputs["Normal"], b.inputs["Coat Normal"])
        # colour: faintly blotchy, a little redder in places, like real skin
        base = b.inputs["Base Color"].links[0].from_socket
        blot = node("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
        L.new(remap(noise(14.0, 3.0), 0.35, 0.7, 0.0, 0.7), blot.inputs[0])
        L.new(base, blot.inputs[6])
        blot.inputs[7].default_value = (1.0, 0.86, 0.82, 1.0)
        L.new(blot.outputs[2], b.inputs["Base Color"])


def set_waterline(hero, z):
    """Water film and droplets only above this height (the pool's surface)."""
    for m in hero["body"].data.materials:
        g = next((n for n in (m.node_tree.nodes if m and m.node_tree else []) if n.bl_idname == "ShaderNodeGroup"), None)
        line = g.node_tree.nodes.get("Wet_Line") if g else None
        if line is not None:
            line.outputs[0].default_value = z


def wet_hair(hero, tint=HAIR_TINT):
    """Dark and glossy, the strands clumped by the water."""
    hair = part(hero, "short04")
    for m in hair.data.materials if hair else []:
        HR._multiply_texture(m, tint, "")
        b = HR._principled(m)
        if b is not None:
            b.inputs["Roughness"].default_value = 0.32
            b.inputs["Specular IOR Level"].default_value = 0.55
            if "Coat Weight" in b.inputs:
                b.inputs["Coat Weight"].default_value = 0.3
                b.inputs["Coat Roughness"].default_value = 0.2


def _fabric_material(name, color, maps, repeat=6.0, rough_mult=0.75, coat=0.0, normal_strength=0.7):
    """Stretch fabric in a solid colour: the CC0 weave's light and shade (not its yellow)
    under the colour, its roughness and normal maps, tiled `repeat` times across the UVs."""
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (repeat, repeat, repeat)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def tex(path, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    d = tex(maps["diffuse"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(d.outputs["Color"], bw.inputs["Color"])
    shade = nt.nodes.new("ShaderNodeMapRange")                   # weave shading around 1.0
    shade.inputs["From Min"].default_value, shade.inputs["From Max"].default_value = 0.2, 0.7
    shade.inputs["To Min"].default_value, shade.inputs["To Max"].default_value = 0.78, 1.08
    nt.links.new(bw.outputs["Val"], shade.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    mix.inputs[6].default_value = (*color, 1)
    nt.links.new(shade.outputs["Result"], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    r = tex(maps["rough"], True)
    rm = nt.nodes.new("ShaderNodeMath")
    rm.operation = "MULTIPLY"
    rm.inputs[1].default_value = rough_mult
    nt.links.new(r.outputs["Color"], rm.inputs[0])
    nt.links.new(rm.outputs[0], b.inputs["Roughness"])
    n = tex(maps["normal"], True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = normal_strength
    nt.links.new(n.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.25
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 0.15
    return mat


def swimwear(hero):
    """The red swim shirt and navy shorts, both wet stretch fabric."""
    maps = V.polyhaven(FABRIC, "textures", "2k")
    shirt, shorts = part(hero, "t-shirt", "shirt"), part(hero, "shorts")
    if shirt is not None:
        shirt.data.materials[0] = _fabric_material("Swim_Shirt", SHIRT_COLOR, maps, repeat=5.0, rough_mult=0.7, coat=0.2)
    if shorts is not None:
        shorts.data.materials[0] = _fabric_material("Swim_Shorts", SHORTS_COLOR, maps, repeat=4.0, rough_mult=0.75)
    return shirt


def build(name="Swimmer", faceunits=True, subdiv=1, brand=True, print_height=0.745, print_size=0.044):
    """Create him in the rest pose. Returns {"body", "rig", "parts", "shirt", "print"}."""
    hero = C.build_hero(name, None, faceunits, subdiv, spec=SPEC)
    HR.tune_skin(hero, tint=SKIN_TINT)
    wet_skin(hero)
    wet_hair(hero)
    HR.tune_eyes(hero["parts"], iris=IRIS)
    HR.tune_teeth(hero["parts"])
    hero["shirt"] = swimwear(hero)
    if brand and hero["shirt"] is not None:
        hero["print"] = C.chest_print(hero, height=print_height, size=print_size, ink=PRINT_INK, shirt=hero["shirt"],
                                      lift=0.0025, project=True)
    return hero
