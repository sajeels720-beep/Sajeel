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


def wet_skin(hero, coat=0.3, coat_rough=0.2, rough=None):
    """A wet sheen: the enhanced skin's clear coat (its pores still show through)."""
    for m in hero["body"].data.materials:
        for g in (n for n in (m.node_tree.nodes if m and m.node_tree else []) if n.bl_idname == "ShaderNodeGroup"):
            for name, val in (("Clearcoat", coat), ("Clearcoat Roughness", coat_rough), ("Roughness", rough)):
                if val is not None and name in g.inputs:
                    g.inputs[name].default_value = val


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
