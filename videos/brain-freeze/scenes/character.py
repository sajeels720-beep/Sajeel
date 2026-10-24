"""The protagonist ("you"): a young man built with MPFB 2 from CC0 MakeHuman assets
(skin, eyes, hair, white T-shirt and jeans, shoes), the default rig for posing and the
ARKit face units (faceunits01 pack) as shape keys for expressions.

Needs the MPFB extension and these CC0 asset packs installed in MPFB:
makehuman_system_assets, shirts01, pants01, shoes01, poses01, faceunits01."""
import os

import bpy  # noqa: I001  (bpy first: it puts addon_utils on the path)
import addon_utils

MPFB = "bl_ext.user_default.mpfb"
CHANNEL_NAME = os.environ.get("CHANNEL_NAME", "Jay3Dfilms")      # printed on the T-shirt, exactly as written

HERO = {
    "phenotype": {"gender": 1.0, "age": 0.5, "muscle": 0.56, "weight": 0.47, "proportions": 0.65, "height": 0.55,
                  "cupsize": 0.5, "firmness": 0.5, "race": {"caucasian": 0.8, "asian": 0.1, "african": 0.1}},
    "rig": "default",
    "eyes": "high-poly/high-poly.mhclo",
    "eyebrows": "eyebrow001/eyebrow001.mhclo",
    "eyelashes": "eyelashes01/eyelashes01.mhclo",
    "teeth": "teeth_base/teeth_base.mhclo",
    "tongue": "tongue01/tongue01.mhclo",
    "hair": "short02/short02.mhclo",
    "clothes": ["male_casualsuit06/male_casualsuit06.mhclo", "shoes01/shoes01.mhclo"],
    "skin_mhmat": "young_caucasian_male/young_caucasian_male.mhmat",
    "skin_material_type": "ENHANCED_SSS",
    "eyes_material_type": "PROCEDURAL_EYES",
}


def services():
    addon_utils.enable(MPFB, default_set=True)
    from bl_ext.user_default.mpfb.services.animationservice import AnimationService
    from bl_ext.user_default.mpfb.services.assetservice import AssetService
    from bl_ext.user_default.mpfb.services.faceservice import FaceService
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.locationservice import LocationService
    return HumanService, AssetService, FaceService, AnimationService, LocationService


def build_hero(name="Hero", pose=None, faceunits=True, subdiv=1, spec=None):
    """Create the character. pose: a poses01 pose name (e.g. 'anrico_sitting02').
    spec: another character's settings in the same form as HERO (default: this video's hero).
    Returns {"body", "rig", "parts"} where parts are the child meshes (eyes, hair, clothes...)."""
    HS, AS, FS, ANIM, LS = services()
    info = HS._create_default_human_info_dict()          # pylint: disable=protected-access
    info.update({k: v for k, v in (spec or HERO).items()})
    info["name"] = name
    settings = HS.get_default_deserialization_settings()
    settings["subdiv_levels"] = subdiv
    body = HS.deserialize_from_dict(info, settings)
    if faceunits:
        FS.load_targets(body, load_microsoft_visemes=False, load_arkit_faceunits=True)
        FS.interpolate_targets(body)
    rig = body.parent if body.parent and body.parent.type == "ARMATURE" else None
    parts = [o for o in bpy.data.objects if o.parent in (body, rig) and o is not body and o.type == "MESH"]
    for o in parts:                                                # the smooth hair shell mirrored the sky and
        if "short02" in o.name:                                    # grass at grazing angles: grey/green crown
            for m in o.data.materials:
                b = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None) if m else None
                if b is not None:
                    b.inputs["Specular IOR Level"].default_value = 0.05
                    b.inputs["Roughness"].default_value = 0.85
    clear_corneas(parts)
    hero = {"body": body, "rig": rig, "parts": parts}
    if pose:
        apply_pose(hero, pose)
    return hero


def clear_corneas(parts):
    """MPFB's eye material makes the outer layer (cornea) refractive. Cycles looks through
    it, but EEVEE shows the sky probe there instead, so the eyes read as mirror balls of the
    park. Make the cornea fully see-through instead (alpha 0 on the outer layer only); the
    inner layer's clear coat still gives the wet highlight."""
    for o in parts:
        for m in o.data.materials:
            nodes = m.node_tree.nodes if m and m.node_tree else []
            eye = next((n for n in nodes if n.bl_idname == "ShaderNodeGroup" and n.node_tree
                        and "OuterLayerAlpha" in n.inputs), None)
            if eye is None:
                continue
            eye.inputs["OuterLayerTransmission"].default_value = 0.0
            eye.inputs["OuterLayerAlpha"].default_value = 0.0
            nt = eye.node_tree
            bsdf = nt.nodes.get("Principled BSDF")
            tmix = nt.nodes.get("TransmissionMix")
            if bsdf is None or tmix is None or nt.nodes.get("OuterLayerAlphaMix") or not bsdf.inputs["Alpha"].is_linked:
                continue
            outer_alpha = bsdf.inputs["Alpha"].links[0].from_socket
            nt.links.remove(bsdf.inputs["Alpha"].links[0])
            amix = nt.nodes.new("ShaderNodeMix")                 # same layer split as the transmission
            amix.name, amix.data_type = "OuterLayerAlphaMix", "FLOAT"
            nt.links.new(tmix.inputs["Factor"].links[0].from_socket, amix.inputs["Factor"])
            outer_first = tmix.inputs["Color1"].is_linked        # Color1 holds the outer layer's value
            nt.links.new(outer_alpha, amix.inputs["A" if outer_first else "B"])
            amix.inputs["B" if outer_first else "A"].default_value = 1.0
            nt.links.new(amix.outputs["Result"], bsdf.inputs["Alpha"])


def apply_pose(hero, pose):
    """Load a poses01 BVH pose onto the rig (brand the shirt before posing)."""
    _, _, _, ANIM, LS = services()
    path = os.path.join(LS.get_user_data(), "poses", pose, pose + ".bvh")
    ANIM.import_bvh_file_as_pose(hero["rig"], path)


def face(body, values, frame=None):
    """Set ARKit face-unit shape keys, e.g. {"eyeBlinkLeft": 1, "eyeBlinkRight": 1,
    "mouthSmileLeft": 0.6}. With frame, keyframe them (on the body and every child mesh
    that carries the same shape keys, so brows and lashes follow). Values above 1
    exaggerate a unit (his faces read bigger than life; brows move only ~6 mm at 1)."""
    meshes = [body] + [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys
                       and o is not body and (o.parent is body or o.parent is body.parent)]
    for ob in meshes:
        kb = ob.data.shape_keys.key_blocks if ob.data.shape_keys else {}
        for k, v in values.items():
            for key in (k, "$md-" + k, "faceunits-" + k):
                if key in kb:
                    kb[key].slider_max = max(kb[key].slider_max, v)
                    kb[key].value = v
                    if frame is not None:
                        kb[key].keyframe_insert("value", frame=frame)


# --------------------------------------------------------------------------
# Branded T-shirt (like his ZACK D FILMS tee): logo-free copy of the CC0 casual suit
# texture, recoloured in the shader, with the channel name as a thin text decal that
# hugs the chest (Shrinkwrap) and moves with the spine bone.
# --------------------------------------------------------------------------
SHIRT_COLOR = (1.0, 0.78, 0.0)                                    # linear RGB: bright yellow, pops against blue sky
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def shirt_object(parts):
    return next((p for p in parts if "casualsuit" in p.name), None)


def recolor_shirt(parts, color=SHIRT_COLOR):
    """Swap in the logo-free texture and tint only the T-shirt half of the atlas (the
    jeans keep their colour)."""
    shirt = shirt_object(parts)
    if shirt is None:
        return None
    clean = bpy.data.images.load(os.path.join(ASSETS, "hero_shirt_clean_diffuse.png"), check_existing=True)
    for mat in shirt.data.materials:
        nt = mat.node_tree if mat else None
        if nt is None:
            continue
        for n in list(nt.nodes):
            if n.bl_idname != "ShaderNodeTexImage" or not n.image or "diffuse" not in n.image.name.lower():
                continue
            n.image = clean
            targets = [l.to_socket for l in n.outputs["Color"].links]
            uv = nt.nodes.new("ShaderNodeTexCoord")
            sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(uv.outputs["UV"], sep.inputs[0])
            top = nt.nodes.new("ShaderNodeMath")
            top.operation = "GREATER_THAN"
            top.inputs[1].default_value = 0.57                   # shirt panels: upper part of the UV atlas
            nt.links.new(sep.outputs["Y"], top.inputs[0])
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs[7].default_value = (*color, 1)
            nt.links.new(top.outputs[0], mix.inputs[0])
            nt.links.new(n.outputs["Color"], mix.inputs[6])
            for t in targets:
                nt.links.new(mix.outputs[2], t)
            return mat
    return None


def chest_print(hero, text=None, size=0.05, height=0.815, ink=(0.012, 0.012, 0.014)):
    """Channel name across the chest (call in the rest pose, before apply_pose).
    height: fraction of body height for the text centre (upper chest, above the cup he
    holds in his lap in shots 3, 4 and 19b)."""
    from mathutils import Vector
    text = text or CHANNEL_NAME
    body, rig = hero["body"], hero["rig"]
    shirt = shirt_object(hero["parts"])
    top = max((body.matrix_world @ v.co).z for v in body.data.vertices)
    z = top * height
    pts = [shirt.matrix_world @ v.co for v in shirt.data.vertices]
    for dz, dx in ((0.02, 0.03), (0.035, 0.06), (0.05, 0.1)):         # widen the search on low-poly shirts
        near = [p for p in pts if abs(p.z - z) < dz and abs(p.x) < dx]
        if near:
            break
    front = min(near, key=lambda p: p.y)
    cu = bpy.data.curves.new("Chest_Print", "FONT")
    cu.body = text
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    words = text.split()
    if len(text) > 8 and len(words) > 1:                          # two lines for longer names
        half = (len(words) + 1) // 2
        cu.body = " ".join(words[:half]) + "\n" + " ".join(words[half:])
    ob = bpy.data.objects.new("Chest_Print", cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.size = 1.0                                                 # measure the set text at size 1
    xs = [c[0] for c in ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).bound_box]
    size = min(size, 0.21 / (max(xs) - min(xs)))                  # keep it within the front of the chest
    cu.size = size
    cu.offset = size * 0.035                                      # thicker strokes: reads as a bold print
    cu.extrude = 0.0003
    ob.rotation_euler = (1.5708, 0, 0)                            # stand the text up, facing -Y
    ob.location = (0.0, front.y - 0.004, z)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    mesh_ob = bpy.data.objects.new("Chest_Print", me)
    for c in ob.users_collection:
        c.objects.link(mesh_ob)
    mesh_ob.matrix_world = ob.matrix_world.copy()
    bpy.data.objects.remove(ob)
    sub = mesh_ob.modifiers.new("Dense", "SUBSURF")
    sub.subdivision_type, sub.levels, sub.render_levels = "SIMPLE", 3, 3
    sw = mesh_ob.modifiers.new("HugShirt", "SHRINKWRAP")
    sw.target, sw.wrap_method, sw.offset = shirt, "NEAREST_SURFACEPOINT", 0.0012
    ink_mat = bpy.data.materials.new("Print_Ink")
    if getattr(ink_mat, "node_tree", None) is None:
        ink_mat.use_nodes = True
    b = ink_mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*ink, 1)
    b.inputs["Roughness"].default_value = 0.75
    mesh_ob.data.materials.append(ink_mat)
    if rig is not None:                                          # ride the spine bone nearest the print
        spines = [b for b in rig.data.bones if b.name.startswith("spine")]
        at = mesh_ob.matrix_world.translation
        bone = min(spines, key=lambda b: ((rig.matrix_world @ b.head_local) - at).length)
        mw = mesh_ob.matrix_world.copy()
        mesh_ob.parent, mesh_ob.parent_type, mesh_ob.parent_bone = rig, "BONE", bone.name
        mesh_ob.matrix_world = mw
    return mesh_ob


def brand(hero, text=None, color=SHIRT_COLOR):
    recolor_shirt(hero["parts"], color)
    return chest_print(hero, text)


def evaluated_points(ob):
    """Posed world positions of every base-mesh vertex (every modifier except the
    Armature is switched off while sampling so indices match ob.data.vertices)."""
    import numpy as np
    masks = [m for m in ob.modifiers if m.type != "ARMATURE" and m.show_viewport]   # keep only the pose deform
    for m in masks:
        m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    P = np.array([tuple(ev.matrix_world @ v.co) for v in me.vertices])
    ev.to_mesh_clear()
    for m in masks:
        m.show_viewport = True
    return P


def seat_heights(hero):
    """(butt bottom z, feet bottom z) of the posed character, from the posed mesh."""
    import numpy as np
    body = hero["body"]
    rest = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    posed = evaluated_points(body)
    top = rest[:, 2].max()
    hips = (rest[:, 2] > top * 0.44) & (rest[:, 2] < top * 0.56) & (rest[:, 1] > 0.0)   # buttocks (back side)
    feet = rest[:, 2] < top * 0.06
    return float(posed[hips, 2].min()), float(posed[feet, 2].min())


def place_on_seat(hero, seat_top, seat_y, x=0.0):
    """Move the posed character so the buttocks rest on a seat top (height seat_top,
    centred at y=seat_y). Returns the resulting feet height (0 = on the ground)."""
    import numpy as np
    rig, body = hero["rig"], hero["body"]
    rest = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    posed = evaluated_points(body)
    top = rest[:, 2].max()
    hips = (rest[:, 2] > top * 0.44) & (rest[:, 2] < top * 0.56) & (rest[:, 1] > 0.0)
    feet = rest[:, 2] < top * 0.06
    dz = seat_top - posed[hips, 2].min()
    rig.location.x += x - posed[hips, 0].mean()
    rig.location.y += seat_y - posed[hips, 1].mean()
    rig.location.z += dz
    return float(posed[feet, 2].min() + dz)
