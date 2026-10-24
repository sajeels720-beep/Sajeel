"""The protagonist ("you") of the sneeze video: a young woman built with MPFB 2 from CC0
MakeHuman assets (skin, eyes, ponytail, arched brows, T-shirt and jeans, shoes), the default
rig for posing and the ARKit face units for her acting. She is not the brain-freeze hero:
different face, hair, skin and shirt colour.

The T-shirt is the CC0 female_casualsuit01 with its logo removed (assets/heroine_shirt_*),
recoloured coral in the shader, with the channel name printed across the chest. The shared
MPFB helpers (face shapes, posing, the EEVEE eye fix) come from brain-freeze/scenes/character.py.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
_shared = os.path.abspath(os.path.join(HERE, "..", "..", "brain-freeze", "scenes"))
if _shared not in sys.path:
    sys.path.append(_shared)

import character as C  # noqa: E402
import vfx_kit as V  # noqa: E402

H = V.hex_lin
CHANNEL_NAME = C.CHANNEL_NAME
SPEC = {
    "phenotype": {"gender": 0.0, "age": 0.44, "muscle": 0.5, "weight": 0.5, "proportions": 0.7, "height": 0.42,
                  "cupsize": 0.5, "firmness": 0.55, "race": {"caucasian": 0.45, "asian": 0.25, "african": 0.3}},
    "rig": "default",
    "eyes": "high-poly/high-poly.mhclo",
    "eyebrows": "eyebrow002/eyebrow002.mhclo",
    "eyelashes": "eyelashes02/eyelashes02.mhclo",
    "teeth": "teeth_base/teeth_base.mhclo",
    "tongue": "tongue01/tongue01.mhclo",
    "hair": "ponytail01/ponytail01.mhclo",
    "clothes": ["female_casualsuit01/female_casualsuit01.mhclo", "shoes02/shoes02.mhclo"],
    "skin_mhmat": "young_caucasian_female/young_caucasian_female.mhmat",
    "skin_material_type": "ENHANCED_SSS",
    "eyes_material_type": "PROCEDURAL_EYES",
}
SHIRT_COLOR = H("#FF6A3D")                  # coral orange: warm, pops against the blue, not video 1's yellow
SKIN_TINT = H("#B98466")                    # multiplies the CC0 skin texture: warm medium brown
HAIR_TINT = H("#6E4A36")                    # multiplies the CC0 hair texture: dark brown with visible strands
IRIS = (H("#3B2314"), H("#6B4325"))         # dark brown eyes (minor, major)
PRINT_INK = H("#F2EEE6")                    # off-white print (never pure white)


def _principled(mat):
    return next((n for n in mat.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None) \
        if mat and mat.node_tree else None


def _multiply_texture(mat, tint, match, tree=None):
    """Multiply the colour of the image texture whose name contains `match` by tint
    (in the material's node tree, or in `tree`, e.g. the skin's node group)."""
    nt = tree or (mat.node_tree if mat else None)
    if nt is None:
        return False
    for n in list(nt.nodes):
        if n.bl_idname != "ShaderNodeTexImage" or not n.image or match not in n.image.name.lower():
            continue
        targets = [l.to_socket for l in n.outputs["Color"].links]
        if not targets:
            continue
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(n.outputs["Color"], mix.inputs[6])
        for t in targets:
            nt.links.new(mix.outputs[2], t)
        return True
    return False


def tune_skin(hero, tint=SKIN_TINT, texture=None, brightness=None):
    """Warm the skin: MPFB's enhanced skin keeps its texture inside a node group, so the
    tint goes in there. texture: another CC0 skin texture file name from MPFB's skins folder."""
    for m in hero["body"].data.materials:
        for g in (n for n in (m.node_tree.nodes if m and m.node_tree else []) if n.bl_idname == "ShaderNodeGroup"):
            if texture:
                _, _, _, _, LS = C.services()
                tex = next((n for n in g.node_tree.nodes if n.name == "DiffuseTexture"), None)
                folder = os.path.join(LS.get_user_data(), "skins")
                path = next((os.path.join(r, texture) for r, _, fs in os.walk(folder) if texture in fs), None)
                if tex is not None and path:
                    tex.image = bpy.data.images.load(path, check_existing=True)
            if tint is not None:
                _multiply_texture(None, tint, "diffuse", tree=g.node_tree)
            if brightness is not None and "Brightness" in g.inputs:
                g.inputs["Brightness"].default_value = brightness


def tune_hair(parts, tint=HAIR_TINT):
    for o in parts:
        if "ponytail" not in o.name:
            continue
        for m in o.data.materials:
            _multiply_texture(m, tint, "")
            b = _principled(m)
            if b is not None:                                    # matte strands: no grey sky sheen on the crown
                b.inputs["Specular IOR Level"].default_value = 0.15
                b.inputs["Roughness"].default_value = 0.7


def tune_eyes(parts, iris=IRIS):
    for o in parts:
        for m in o.data.materials:
            for n in (m.node_tree.nodes if m and m.node_tree else []):
                if n.bl_idname != "ShaderNodeGroup":
                    continue
                for name, col in (("IrisMinorColor", iris[0]), ("IrisMajorColor", iris[1])):
                    if name in n.inputs:
                        n.inputs[name].default_value = (*col, 1)


def tune_teeth(parts):
    """Warm, slightly translucent enamel: with the plain CC0 material, the teal studio light
    turned the teeth blue-grey inside the mouth."""
    for o in parts:
        if "teeth" not in o.name:
            continue
        for m in o.data.materials:
            _multiply_texture(m, H("#FFF0DC"), "teeth")
            b = _principled(m)
            if b is None:
                continue
            b.inputs["Roughness"].default_value = 0.35
            for name, val in (("Subsurface Weight", 0.35), ("Subsurface Scale", 0.003)):
                if name in b.inputs:
                    b.inputs[name].default_value = val
            if "Subsurface Radius" in b.inputs:
                b.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.35)


def recolor_shirt(parts, color=SHIRT_COLOR):
    """Logo-free texture, tinted only where the shirt mask is white (the jeans keep their colour)."""
    shirt = C.shirt_object(parts)
    clean = bpy.data.images.load(os.path.join(ASSETS, "heroine_shirt_clean_diffuse.png"), check_existing=True)
    mask = bpy.data.images.load(os.path.join(ASSETS, "heroine_shirt_mask.png"), check_existing=True)
    mask.colorspace_settings.name = "Non-Color"
    for mat in shirt.data.materials:
        nt = mat.node_tree if mat else None
        for n in list(nt.nodes if nt else []):
            if n.bl_idname != "ShaderNodeTexImage" or not n.image or "diffuse" not in n.image.name.lower():
                continue
            n.image = clean
            targets = [l.to_socket for l in n.outputs["Color"].links]
            mt = nt.nodes.new("ShaderNodeTexImage")
            mt.image = mask
            if n.inputs["Vector"].is_linked:
                nt.links.new(n.inputs["Vector"].links[0].from_socket, mt.inputs["Vector"])
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs[7].default_value = (*color, 1)
            nt.links.new(mt.outputs["Color"], mix.inputs[0])
            nt.links.new(n.outputs["Color"], mix.inputs[6])
            for t in targets:
                nt.links.new(mix.outputs[2], t)
            return mat
    return None


def build(name="Heroine", pose=None, faceunits=True, subdiv=1, brand=True, print_height=0.725, skin=None):
    """Create her. Returns {"body", "rig", "parts"} like character.build_hero.
    skin: tune_skin settings to try another skin tone."""
    hero = C.build_hero(name, None, faceunits, subdiv, spec=SPEC)
    tune_skin(hero, **(skin or {}))
    tune_hair(hero["parts"])
    tune_eyes(hero["parts"])
    tune_teeth(hero["parts"])
    if brand:
        recolor_shirt(hero["parts"])
        hero["print"] = C.chest_print(hero, height=print_height, size=0.042, ink=PRINT_INK)
    if pose:
        C.apply_pose(hero, pose)
    return hero


def arms_down(hero, angle=38.0):
    """From MPFB's A-pose rest, lower both upper arms to hang by her sides."""
    import math
    rig = hero["rig"]
    for side, sign in (("L", -1.0), ("R", 1.0)):
        pb = rig.pose.bones.get(f"upperarm01.{side}")
        if pb is None:
            continue
        pb.rotation_mode = "XYZ"
        pb.rotation_euler[2] = math.radians(sign * angle)
    bpy.context.view_layer.update()


def nose_shapes(hero):
    """Extra CC0 MakeHuman targets as animatable shape keys for the sneeze acting:
    "flare" (nostrils flare) and "nostrils_wide". Animate them with character.face()."""
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    body = hero["body"]
    for target, name in (("nose-flaring-incr", "flare"), ("nose-nostrils-width-incr", "nostrils_wide")):
        if body.data.shape_keys and name in body.data.shape_keys.key_blocks:
            continue
        path = TargetService.target_full_path(target)
        if path:
            key = TargetService.load_target(body, path, weight=0.0, name=name)
            key.slider_max = 2.0


def nose_tip(hero):
    """Base-mesh index of the nose tip: the most forward vertex on the face's centre line."""
    import numpy as np
    body = hero["body"]
    rig = hero["rig"]
    P = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    z0 = (rig.matrix_world @ rig.pose.bones["head"].head).z
    sel = np.where((np.abs(P[:, 0]) < 0.004) & (P[:, 2] > z0 + 0.04) & (P[:, 2] < z0 + 0.16))[0]
    return int(sel[np.argmin(P[sel, 1])])


def surface_point(hero, index):
    """Posed world position and normal of a base-mesh vertex on the rendered (smoothed)
    skin at the current frame: shape keys and pose applied, and moved to where the
    subdivision surface lies, so things can touch the skin."""
    import numpy as np
    from mathutils import Vector
    body = hero["body"]
    key = f"_subdiv_{index}"
    if key not in hero:                       # nearest smoothed vertex to the cage vertex (topology never changes)
        cage = C.evaluated_points(body)[index]
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        Q = np.array([tuple(ev.matrix_world @ v.co) for v in me.vertices])
        hero[key] = int(np.argmin(np.linalg.norm(Q - cage, axis=1)))
        ev.to_mesh_clear()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    v = me.vertices[hero[key]]
    p, n = ev.matrix_world @ v.co, (ev.matrix_world.to_3x3() @ v.normal).normalized()
    ev.to_mesh_clear()
    return Vector(p), Vector(n)
