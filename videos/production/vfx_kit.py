"""vfx_kit - helpers for Zack D. Films-style 3D Shorts in Blender (tested on 4.5 LTS and 5.2 LTS).

Project setup (1080x1920, 30 fps, AgX Punchy), Poly Haven downloads, sky/HDRI worlds,
camera rigs with eased moves + handheld noise + crash zooms, explainer materials
(x-ray, glow, frost) and effects (growing glow curves, pulses, ripple rings),
compositor glow/lens fringe, image-sequence rendering and ffmpeg encoding.

Use with claude_sculpt_kit for modeling:  import vfx_kit as V, claude_sculpt_kit as K
Conventions: meters, Z up; one shot per .blend; frames start at 1.
"""
import json
import math
import os
import subprocess
import urllib.request

import bpy
import numpy as np
from mathutils import Matrix, Vector

VERSION = "1.1"
ASSET_DIR = os.environ.get("VFX_ASSETS") or os.path.join(os.path.expanduser("~"), "vfx_assets")


# --------------------------------------------------------------------------
# Project / scene
# --------------------------------------------------------------------------
def start_fresh():
    """Remove only Blender's default startup objects (Cube, Light, Camera) so a shot
    script can build into a new file. Refuses if the scene holds anything else."""
    sc = bpy.context.scene
    names = {o.name for o in sc.objects}
    if names - {"Cube", "Light", "Camera"}:
        raise RuntimeError("Open a new Blender file (File > New > General) before building a shot; "
                           "this scene already contains: " + ", ".join(sorted(names)[:8]))
    for n in names:
        bpy.data.objects.remove(bpy.data.objects[n])


def setup_shot(seconds, fps=30, res=(1080, 1920), engine="EEVEE", samples=48, scale=100,
               motion_blur=True, look="Punchy", exposure=0.0):
    """Frame range, resolution, colour management (AgX + look), engine and motion blur.
    engine: "EEVEE" (final renders on a laptop) or "CYCLES" (CPU fallback)."""
    sc = bpy.context.scene
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, int(round(seconds * fps))
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = scale
    sc.render.use_motion_blur = motion_blur
    vs = sc.view_settings
    for vt, lk in (("AgX", "AgX - " + look), ("AgX", look), ("AgX", "AgX - Medium High Contrast"),
                   ("AgX", "Medium High Contrast"), ("Filmic", "Medium High Contrast")):
        try:
            vs.view_transform = vt
            vs.look = lk
            break
        except Exception:
            continue
    vs.exposure = exposure
    if os.environ.get("SHOT_CYCLES") == "1" and engine.upper().startswith("EEVEE"):
        # a fallback for a shot a laptop GPU can't render in EEVEE (black frames): Cycles on the
        # CPU, denoised, with shorter light paths. Set SHOT_CYCLES=1 (and SHOT_CYCLES_SAMPLES).
        set_engine("CYCLES", int(os.environ.get("SHOT_CYCLES_SAMPLES", "24")))
        cy = sc.cycles
        cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = 6, 3, 3, 6
        cy.transparent_max_bounces = 8
        return sc
    set_engine(engine, samples)
    return sc


def set_engine(engine="EEVEE", samples=48):
    sc = bpy.context.scene
    items = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    if engine.upper().startswith("EEVEE"):
        sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in items else "BLENDER_EEVEE"
        ee = sc.eevee
        ee.taa_render_samples = samples
        for prop, val in (("use_raytracing", True), ("use_shadows", True), ("use_gtao", True)):
            if hasattr(ee, prop):
                setattr(ee, prop, val)
    else:
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = 0.02
        sc.cycles.use_denoising = True
    return sc.render.engine


def fast_preview(samples=16, threshold=0.05, bounces=(4, 2, 2, 4, 8), sss="BURLEY"):
    """Quicker Cycles CPU previews: fewer samples (denoised), shorter light paths and the
    cheaper Burley subsurface on every Principled material. Final EEVEE renders ignore it."""
    sc = bpy.context.scene
    if sc.render.engine != "CYCLES":
        return
    cy = sc.cycles
    cy.samples, cy.adaptive_threshold = samples, threshold
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces, cy.transparent_max_bounces = bounces
    for m in bpy.data.materials:
        for n in (m.node_tree.nodes if m.node_tree else []):
            if n.bl_idname == "ShaderNodeBsdfPrincipled" and hasattr(n, "subsurface_method"):
                n.subsurface_method = sss


def collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def link(obj, col=None):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj


def hex_lin(h):
    """'#7EC8E3' -> linear RGB tuple."""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# --------------------------------------------------------------------------
# Assets (Poly Haven, CC0)
# --------------------------------------------------------------------------
def _get(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not os.path.exists(dest) or os.path.getsize(dest) == 0:
        req = urllib.request.Request(url, headers={"User-Agent": "vfx_kit/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
            f.write(r.read())
        os.replace(dest + ".part", dest)
    return dest


def _cached(asset_id, kind, res):
    """The files an earlier download left in ASSET_DIR (None if there are none), so a build
    still works when Poly Haven can't be reached."""
    if kind == "hdris":
        p = os.path.join(ASSET_DIR, "hdri", f"{asset_id}_{res}.hdr")
        return p if os.path.exists(p) else None
    folder = os.path.join(ASSET_DIR, "textures", asset_id)
    if not os.path.isdir(folder):
        return None
    tags = {"diffuse": "_diff_", "rough": "_rough_", "normal": "_nor_gl_", "disp": "_disp_", "ao": "_ao_"}
    out = {k: os.path.join(folder, f) for f in os.listdir(folder) for k, t in tags.items() if t in f and f"_{res}." in f}
    return out or None


def polyhaven(asset_id, kind="hdris", res="2k"):
    """Download a Poly Haven asset (CC0). kind: 'hdris' -> path of the .hdr;
    'textures' -> dict of map paths (diffuse, rough, normal, disp, ao). Uses the copy already
    downloaded if Poly Haven can't be reached."""
    req = urllib.request.Request(f"https://api.polyhaven.com/files/{asset_id}", headers={"User-Agent": "vfx_kit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            files = json.loads(r.read())
    except OSError:
        cached = _cached(asset_id, kind, res)
        if cached:
            return cached
        raise
    if kind == "hdris":
        url = files["hdri"][res]["hdr"]["url"]
        return _get(url, os.path.join(ASSET_DIR, "hdri", os.path.basename(url)))
    maps = {"diffuse": "Diffuse", "rough": "Rough", "normal": "nor_gl", "disp": "Displacement", "ao": "AO"}
    out = {}
    for key, name in maps.items():
        if name in files and res in files[name]:
            fmt = "jpg" if "jpg" in files[name][res] else next(iter(files[name][res]))
            url = files[name][res][fmt]["url"]
            out[key] = _get(url, os.path.join(ASSET_DIR, "textures", asset_id, os.path.basename(url)))
    return out


def polyhaven_model(asset_id, res="1k", col=None):
    """Download a Poly Haven model (CC0) as glTF with its textures and import it.
    Returns the imported objects (moved into `col` if given)."""
    folder = os.path.join(ASSET_DIR, "models", asset_id)
    req = urllib.request.Request(f"https://api.polyhaven.com/files/{asset_id}", headers={"User-Agent": "vfx_kit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            files = json.loads(r.read())
        gl = files["gltf"].get(res) or next(iter(files["gltf"].values()))
        gl = gl["gltf"]
        path = _get(gl["url"], os.path.join(folder, os.path.basename(gl["url"])))
        for rel, info in gl.get("include", {}).items():
            _get(info["url"], os.path.join(folder, rel))
    except OSError:                                              # offline: the copy downloaded before
        path = next((os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith(".gltf")), None) \
            if os.path.isdir(folder) else None
        if path is None:
            raise
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    if col is not None:
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
    return new


def sun_azimuth(hdri_path):
    """(azimuth_deg, elevation_deg) of the brightest spot (the sun) in an equirect HDRI,
    in the same convention as hdri_world rotation 0. Use it to place the sun:
    rot = wanted_azimuth - sun_azimuth."""
    img = bpy.data.images.load(hdri_path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[..., :3].mean(2)
    y, x = np.unravel_index(int(np.argmax(lum)), lum.shape)
    az = (x / w) * 360.0 - 180.0          # 0 = -X direction in Blender's equirect mapping
    el = (y / h) * 180.0 - 90.0           # pixels are stored bottom-up
    return az, el


def textured(name, maps, scale=1.0, rough_mult=1.0, normal_strength=1.0, tint=None):
    """PBR material from Poly Haven texture maps (dict from polyhaven(..., 'textures'))."""
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def tex(path, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    if "diffuse" in maps:
        d = tex(maps["diffuse"])
        col = d.outputs["Color"]
        if tint is not None:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs[0].default_value = 1.0
            mix.inputs[7].default_value = (*tint, 1)
            nt.links.new(col, mix.inputs[6])
            col = mix.outputs[2]
        nt.links.new(col, b.inputs["Base Color"])
    if "rough" in maps:
        r = tex(maps["rough"], True)
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = "MULTIPLY"
        m.inputs[1].default_value = rough_mult
        nt.links.new(r.outputs["Color"], m.inputs[0])
        nt.links.new(m.outputs[0], b.inputs["Roughness"])
    if "normal" in maps:
        n = tex(maps["normal"], True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return mat


# --------------------------------------------------------------------------
# Worlds
# --------------------------------------------------------------------------
def _world():
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    if getattr(w, "node_tree", None) is None:
        w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    return w, nt


def hdri_world(path, strength=1.0, rot_deg=0.0, camera_strength=None):
    """Poly Haven HDRI for light and background. camera_strength: different
    brightness for what the camera sees (e.g. brighter, bluer sky)."""
    w, nt = _world()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rot_deg)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    if camera_strength is None:
        nt.links.new(bg.outputs[0], out.inputs[0])
    else:
        bg2 = nt.nodes.new("ShaderNodeBackground")
        bg2.inputs["Strength"].default_value = camera_strength
        nt.links.new(env.outputs["Color"], bg2.inputs["Color"])
        lp = nt.nodes.new("ShaderNodeLightPath")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
        nt.links.new(bg.outputs[0], mix.inputs[1])
        nt.links.new(bg2.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
    return w


def gradient_world(top="#7EC8E3", bottom="#E6F5FB", strength=1.0, light_strength=0.6):
    """His explainer look: soft sky-blue gradient seen by the camera, gentle blue-white
    ambient for lighting. Gradient runs along the camera's vertical screen axis
    approximately (world Z)."""
    w, nt = _world()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -0.6, 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*hex_lin(bottom), 1)
    ramp.color_ramp.elements[1].color = (*hex_lin(top), 1)
    cam_bg = nt.nodes.new("ShaderNodeBackground")
    cam_bg.inputs["Strength"].default_value = strength
    amb = nt.nodes.new("ShaderNodeBackground")
    amb.inputs["Color"].default_value = (*[0.5 * a + 0.5 * b for a, b in zip(hex_lin(top), (1, 1, 1))], 1)
    amb.inputs["Strength"].default_value = light_strength
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], cam_bg.inputs["Color"])
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(amb.outputs[0], mix.inputs[1])
    nt.links.new(cam_bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return w


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
def _inp(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    return None


def _blended(mat):
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    if hasattr(mat, "use_backface_culling"):
        mat.use_backface_culling = False


def principled(name, color, rough=0.5, metal=0.0, sss=0.0, sss_radius=(1.0, 0.45, 0.25), sss_scale=0.02,
               spec=0.5, coat=0.0, transmission=0.0, ior=1.45, emission=None, emission_strength=0.0,
               alpha=1.0):
    """Principled material with names that work in Blender 4.x and 5.x."""
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for names, val in ((("Subsurface Weight", "Subsurface"), sss), (("Specular IOR Level", "Specular"), spec),
                       (("Coat Weight", "Clearcoat"), coat), (("Transmission Weight", "Transmission"), transmission),
                       (("IOR",), ior), (("Alpha",), alpha)):
        s = _inp(b, *names)
        if s is not None:
            s.default_value = val
    s = _inp(b, "Subsurface Radius")
    if s is not None:
        s.default_value = sss_radius
    s = _inp(b, "Subsurface Scale")
    if s is not None:
        s.default_value = sss_scale
    if emission is not None:
        _inp(b, "Emission Color", "Emission").default_value = (*emission, 1)
        _inp(b, "Emission Strength").default_value = emission_strength
    if alpha < 1.0 or transmission > 0:
        _blended(mat)
    return mat


def bsdf(mat):
    return mat.node_tree.nodes.get("Principled BSDF")


def color_variation(mat, color2, scale=40.0, amount=0.5, detail=4.0, threshold=None):
    """Mix a second colour into Base Color through noise (specks with threshold, e.g. vanilla
    bean dots or choc chips; soft blotches without)."""
    nt = mat.node_tree
    b = bsdf(mat)
    base = tuple(b.inputs["Base Color"].default_value)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    fac = nz.outputs["Fac"]
    if threshold is not None:
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = threshold
        ramp.color_ramp.elements[1].position = min(threshold + 0.02, 1.0)
        nt.links.new(fac, ramp.inputs[0])
        fac = ramp.outputs[0]
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = base
    mix.inputs[7].default_value = (*color2, 1)
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = "MULTIPLY"
    m.inputs[1].default_value = amount
    nt.links.new(fac, m.inputs[0])
    nt.links.new(m.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return mat


def bump(mat, scale=60.0, strength=0.15, distance=0.002):
    """Fine surface bump from noise (paper fibre, skin pores, frost grain)."""
    nt = mat.node_tree
    b = bsdf(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 8.0
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = distance
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return mat


def emission(name, color, strength=5.0):
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat


def xray(name, color, strength=3.0, edge=0.35, core=0.04):
    """See-through 'x-ray' surface: glowing rim, nearly transparent centre (his skin/skull
    reveals). Works in EEVEE (blended) and Cycles."""
    mat = bpy.data.materials.new(name)
    if getattr(mat, "node_tree", None) is None:
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 1.0 - edge
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (core, core, core, 1)
    ramp.color_ramp.elements[1].position = 0.85
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    _blended(mat)
    return mat


def animate_socket(socket, keys, interp="BEZIER"):
    """Keyframe a shader input over time: keys = [(frame, value), ...]."""
    for f, v in keys:
        socket.default_value = v
        socket.keyframe_insert("default_value", frame=f)
    ease_id(socket.id_data, interp)


def assign(obj, mat, slot=None):
    if slot is None:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    else:
        while len(obj.data.materials) <= slot:
            obj.data.materials.append(None)
        obj.data.materials[slot] = mat
    return obj


# --------------------------------------------------------------------------
# Animation helpers (Blender 4.x legacy fcurves and 5.x channelbags)
# --------------------------------------------------------------------------
def fcurves(id_data):
    ad = getattr(id_data, "animation_data", None)
    act = ad.action if ad else None
    if act is None:
        return []
    out = []
    if hasattr(act, "layers") and len(act.layers):
        for lay in act.layers:
            for st in lay.strips:
                for cb in getattr(st, "channelbags", []):
                    out += list(cb.fcurves)
    if not out and hasattr(act, "fcurves"):
        out = list(act.fcurves)
    return out


def ease_id(id_data, interp="BEZIER", easing="EASE_IN_OUT", data_path=None):
    """Smooth every keyframe (no linear motion): BEZIER with auto-clamped handles, or
    SINE/QUAD/CUBIC/EXPO/BACK with an easing direction."""
    for fc in fcurves(id_data):
        if data_path and not fc.data_path.startswith(data_path):
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            if interp == "BEZIER":
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            else:
                kp.easing = easing
        fc.update()


def key(id_data, data_path, keys, interp="BEZIER", easing="EASE_IN_OUT"):
    """Keyframe a property of one ID (object, camera data, curve...):
    keys = [(frame, value), ...]; vectors as tuples. Eased by default."""
    for f, v in keys:
        if isinstance(v, (tuple, list)):
            id_data.path_resolve(data_path)[:] = v
        else:
            owner, attr = id_data, data_path
            if "." in data_path:
                head, attr = data_path.rsplit(".", 1)
                owner = id_data.path_resolve(head)
            setattr(owner, attr, v)
        id_data.keyframe_insert(data_path, frame=f)
    ease_id(id_data, interp, easing, data_path)


def noise_on(id_data, data_path, strength, scale=12.0, start=None, end=None, blend=4, seed=0):
    """F-curve noise (handheld feel, shakes). start/end restrict it to a frame range."""
    if not fcurves(id_data) or not any(fc.data_path == data_path for fc in fcurves(id_data)):
        id_data.keyframe_insert(data_path, frame=bpy.context.scene.frame_start)
    for fc in fcurves(id_data):
        if fc.data_path != data_path:
            continue
        m = fc.modifiers.new("NOISE")
        m.scale = scale
        m.strength = strength
        m.phase = 7.0 * (fc.array_index + 1) + 13.0 * seed
        if start is not None:
            m.use_restricted_range = True
            m.frame_start, m.frame_end = start, end
            m.blend_in = m.blend_out = blend


# --------------------------------------------------------------------------
# Camera rig: rig (moves) > camera (handheld noise), aim target (look-at + focus)
# --------------------------------------------------------------------------
def camera_rig(name="Cam", lens=50.0, fstop=2.8, sensor=36.0, col=None):
    col = col or collection("CAMERA")
    rig = link(bpy.data.objects.new(name + "_rig", None), col)
    aim = link(bpy.data.objects.new(name + "_aim", None), col)
    aim.empty_display_size = 0.02
    cd = bpy.data.cameras.new(name)
    cd.lens, cd.sensor_width = lens, sensor
    cd.clip_start, cd.clip_end = 0.005, 500.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.dof.focus_object = aim
    cam = link(bpy.data.objects.new(name, cd), col)
    cam.parent = rig
    tt = cam.constraints.new("TRACK_TO")
    tt.target, tt.track_axis, tt.up_axis = aim, "TRACK_NEGATIVE_Z", "UP_Y"
    bpy.context.scene.camera = cam
    return {"cam": cam, "rig": rig, "aim": aim}


def cam_keys(r, keys, interp="BEZIER"):
    """keys = [(frame, cam_location, aim_location, lens or None), ...] - eased moves."""
    for f, loc, aim, lens in keys:
        r["rig"].location = loc
        r["rig"].keyframe_insert("location", frame=f)
        r["aim"].location = aim
        r["aim"].keyframe_insert("location", frame=f)
        if lens:
            r["cam"].data.lens = lens
            r["cam"].data.keyframe_insert("lens", frame=f)
    for idd in (r["rig"], r["aim"], r["cam"].data):
        ease_id(idd, interp)


def handheld(r, amount=0.0015, aim_amount=0.0012, speed=1.0, seed=0):
    """Very subtle handheld drift (scale amounts with the shot size)."""
    noise_on(r["cam"], "location", amount, scale=40.0 / speed, seed=seed)
    noise_on(r["aim"], "location", aim_amount, scale=55.0 / speed, seed=seed + 3)


def shake(r, start, end, strength=0.01, scale=1.6):
    """Short impact / stab shake between two frames."""
    noise_on(r["cam"], "location", strength, scale=scale, start=start, end=end, blend=2, seed=5)
    noise_on(r["aim"], "location", strength * 0.6, scale=scale, start=start, end=end, blend=2, seed=9)


def _glide_slopes(t, y, ease_in, ease_out):
    """Slopes for a monotone cubic through (t, y) (Fritsch-Carlson, as scipy's PCHIP): it never
    overshoots a key, is flat where an axis turns back, and otherwise carries its speed through
    each key. At the ends it is still moving (no acceleration there: the natural end of a
    spline), so a camera carries on into the cut, unless eased."""
    h = np.diff(t)
    delta = np.diff(y) / h
    d = np.zeros_like(y)
    for k in range(1, len(t) - 1):
        a, b = delta[k - 1], delta[k]
        if a * b > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            d[k] = (w1 + w2) / (w1 / a + w2 / b)
    if len(t) == 2:
        d[:] = delta[0]
    else:
        for i, j, dl in ((0, 1, delta[0]), (-1, -2, delta[-1])):
            e = (3 * dl - d[j]) / 2
            d[i] = e if e * dl > 0 else 0.0
    if ease_in:
        d[0] = 0.0
    if ease_out:
        d[-1] = 0.0
    return d


def glide(keys, frames, ease_in=False, ease_out=False):
    """Values on `frames` through keys [(frame, number or vector), ...] along monotone cubics
    (per axis): smooth speed through every key and no overshoot. Outside the keys it carries
    on at its end speed (or holds, if eased). Returns an array (len(frames), axes)."""
    keys = sorted(keys, key=lambda k: k[0])
    t = np.array([float(k[0]) for k in keys])
    Y = np.array([np.atleast_1d(np.asarray(k[1], float)) for k in keys])
    F = np.asarray(frames, float)
    out = np.zeros((len(F), Y.shape[1]))
    if len(t) == 1:
        out[:] = Y[0]
        return out
    for ax in range(Y.shape[1]):
        y = Y[:, ax]
        d = _glide_slopes(t, y, ease_in, ease_out)
        i = np.clip(np.searchsorted(t, F, side="right") - 1, 0, len(t) - 2)
        h = t[i + 1] - t[i]
        s = (F - t[i]) / h
        h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
        h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        v = h00 * y[i] + h10 * h * d[i] + h01 * y[i + 1] + h11 * h * d[i + 1]
        before, after = F < t[0], F > t[-1]
        v[before] = y[0] + d[0] * (F[before] - t[0])
        v[after] = y[-1] + d[-1] * (F[after] - t[-1])
        out[:, ax] = v
    return out


def settle_bump(t, length=10.0, decay=5.0):
    """A soft impact for crash zooms, t frames after the hit: one push and a smaller swing back,
    smooth at both ends (no speed jump), gone after `length` frames. Peaks at about 0.7."""
    if t <= 0 or t >= length:
        return 0.0
    w = 2 * math.pi * t / length
    return math.sin(w) * math.sin(w / 2) * math.exp(-t / decay) * 1.6


def cam_glide(r, keys, ease_in=False, ease_out=False, bumps=(), frames=None):
    """Like cam_keys, but the moves flow: keyed on every frame along `glide` curves through the
    keys [(frame, cam_location, aim_location, lens or None), ...], so the camera carries its speed
    smoothly through each key and keeps moving into and out of the cuts (unless ease_in /
    ease_out). bumps = [(frame, strength), ...]: the soft impact of a crash zoom, instead of a
    shake: from that frame the camera pushes on along its view by up to about 0.7 x strength x
    its distance to the aim, and settles back (settle_bump). Keys one frame either side of the
    shot too, so motion blur is right at the cuts."""
    sc = bpy.context.scene
    frames = list(frames or range(sc.frame_start - 1, sc.frame_end + 2))
    C = glide([(f, tuple(c)) for f, c, _, _ in keys], frames, ease_in, ease_out)
    A = glide([(f, tuple(a)) for f, _, a, _ in keys], frames, ease_in, ease_out)
    lenses = [(f, ln) for f, _, _, ln in keys if ln]
    L = glide(lenses, frames, ease_in, ease_out)[:, 0] if lenses else None
    for i, f in enumerate(frames):
        c, a = Vector(C[i]), Vector(A[i])
        for hit, strength in bumps:
            b = settle_bump(f - hit)
            if b:
                c = c + (a - c) * (strength * b)
        r["rig"].location = c
        r["rig"].keyframe_insert("location", frame=f)
        r["aim"].location = a
        r["aim"].keyframe_insert("location", frame=f)
        if L is not None:
            r["cam"].data.lens = float(L[i])
            r["cam"].data.keyframe_insert("lens", frame=f)
    for idd in (r["rig"], r["aim"], r["cam"].data):
        ease_id(idd, "LINEAR")
        for fc in fcurves(idd):
            fc.extrapolation = "CONSTANT" if (ease_in or ease_out) else "LINEAR"


# --------------------------------------------------------------------------
# Effects
# --------------------------------------------------------------------------
def glow_curve(name, points, radius, mat, col=None, resolution=12, grow=None, taper=None):
    """Tube along a polyline (vessel, nerve, signal path). grow=(start, end) animates it
    drawing on from first to last point. taper: 'thin' end radius factor."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.resolution_u = resolution
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY" if len(points) < 3 else "NURBS")
    pts = np.asarray(points, float)
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        w = 1.0 if taper is None else 1.0 + (taper - 1.0) * i / max(len(pts) - 1, 1)
        sp.points[i].co = (*p, 1.0)
        sp.points[i].radius = w
    if sp.type == "NURBS":
        sp.order_u = min(4, len(pts))
        sp.use_endpoint_u = True
    ob = link(bpy.data.objects.new(name, cu), col)
    assign(ob, mat)
    if grow:
        cu.bevel_factor_mapping_end = "SPLINE"
        cu.bevel_factor_end = 0.0
        cu.keyframe_insert("bevel_factor_end", frame=grow[0])
        cu.bevel_factor_end = 1.0
        cu.keyframe_insert("bevel_factor_end", frame=grow[1])
        ease_id(cu, "SINE", "EASE_IN_OUT")
    return ob


def pulse(name, points, start, end, color=(1.0, 0.1, 0.06), size=0.01, strength=30.0, col=None, trail=0.15):
    """A bright glowing blob travelling along a path (nerve signal, blood rush).
    trail: length of the glowing streak as a fraction of the path."""
    pts = np.asarray(points, float)
    mat = emission(name + "_mat", color, strength)
    cu = bpy.data.curves.new(name + "_streak", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = size * 0.6
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1.0)
    sp.order_u = min(4, len(pts))
    sp.use_endpoint_u = True
    cu.bevel_factor_mapping_start = cu.bevel_factor_mapping_end = "SPLINE"
    ob = link(bpy.data.objects.new(name, cu), col)
    assign(ob, mat)
    # keyed on every frame: with only two keys the clamping at 1.0 made start and end equal all
    # the way, a streak of no length that never showed
    span = max(end - start, 1)
    for f in range(start - 1, end + 2):
        t = min(max((f - start) / span, 0.0), 1.0)
        head = (1.0 + trail) * (1.0 - math.cos(t * math.pi / 2))          # eased in: it speeds up
        cu.bevel_factor_end = min(head, 1.0)
        cu.bevel_factor_start = max(0.0, min(head - trail, 1.0))
        cu.keyframe_insert("bevel_factor_end", frame=f)
        cu.keyframe_insert("bevel_factor_start", frame=f)
    ease_id(cu, "LINEAR")
    return ob


def ripple_rings(name, center, normal, start, count=3, interval=5, life=18, radius=0.05,
                 thickness=0.04, color=(1.0, 0.12, 0.08), strength=12.0, col=None):
    """His red ripple rings: glowing rings expand from a point and fade out.
    thickness is relative to the final radius."""
    z = Vector(normal).normalized()
    rot = z.to_track_quat("Z", "Y").to_matrix().to_4x4()
    rings = []
    for i in range(count):
        cu = bpy.data.curves.new(f"{name}_{i}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = thickness
        cu.bevel_resolution = 3
        sp = cu.splines.new("POLY")
        sp.points.add(63)
        for k in range(64):
            a = 2 * math.pi * k / 64
            sp.points[k].co = (math.cos(a), math.sin(a), 0.0, 1.0)
        sp.use_cyclic_u = True
        ob = link(bpy.data.objects.new(f"{name}_{i}", cu), col)
        ob.matrix_world = Matrix.Translation(Vector(center)) @ rot
        mat = emission(f"{name}_{i}_mat", color, strength)
        nt = mat.node_tree                                       # fade to transparent (a dimmed emission reads black)
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(nt.nodes["Emission"].outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs[0])
        _blended(mat)
        assign(ob, mat)
        f0 = start + i * interval
        key(ob, "scale", [(f0, (0.001,) * 3), (f0 + life, (radius,) * 3)], "QUAD", "EASE_OUT")
        animate_socket(mix.inputs[0], [(f0, 1.0), (f0 + int(life * 0.55), 0.7), (f0 + life, 0.0)])
        visible(ob, [(1, False), (f0, True), (f0 + life + 1, False)])
        rings.append(ob)
    return rings


def visible(obj, keys):
    """Hard visibility switches: keys = [(frame, True/False), ...] (render + viewport)."""
    for f, v in keys:
        obj.hide_render = obj.hide_viewport = not v
        obj.keyframe_insert("hide_render", frame=f)
        obj.keyframe_insert("hide_viewport", frame=f)
    for fc in fcurves(obj):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


# --------------------------------------------------------------------------
# Compositor: soft glow on bright effects + slight lens fringe (both APIs)
# --------------------------------------------------------------------------
def compositor(glow=0.5, threshold=1.0, size=0.5, dispersion=0.008):
    sc = bpy.context.scene
    if hasattr(sc, "compositing_node_group"):
        ng = bpy.data.node_groups.new("Shot_Compositor", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        sc.compositing_node_group = ng
        out = ng.nodes.new("NodeGroupOutput")
    else:
        sc.use_nodes = True
        ng = sc.node_tree
        ng.nodes.clear()
        out = ng.nodes.new("CompositorNodeComposite")
    rl = ng.nodes.new("CompositorNodeRLayers")
    last = rl.outputs["Image"]
    if glow:
        g = ng.nodes.new("CompositorNodeGlare")
        if "Type" in g.inputs:
            g.inputs["Type"].default_value = "Fog Glow"
        else:
            g.glare_type = "FOG_GLOW"
        for nm, val in (("Threshold", threshold), ("Strength", glow), ("Size", size)):
            s = g.inputs.get(nm)
            if s is not None:
                try:
                    s.default_value = val
                except Exception:
                    pass
        if g.inputs.get("Size") is None and hasattr(g, "size"):
            g.size = int(round(6 + 3 * size))           # older API: 6..9 octaves
        if g.inputs.get("Threshold") is None and hasattr(g, "threshold"):
            g.threshold = threshold
        if g.inputs.get("Strength") is None and hasattr(g, "mix"):
            g.mix = glow - 1.0
        ng.links.new(last, g.inputs["Image"])
        last = g.outputs["Image"]
    if dispersion:
        ld = ng.nodes.new("CompositorNodeLensdist")
        ld.inputs["Dispersion"].default_value = dispersion
        if "Fit" in ld.inputs:
            ld.inputs["Fit"].default_value = True
        elif hasattr(ld, "use_fit"):
            ld.use_fit = True
        ng.links.new(last, ld.inputs["Image"])
        last = ld.outputs["Image"]
    ng.links.new(last, out.inputs[0])
    return ng


# --------------------------------------------------------------------------
# Render / encode
# --------------------------------------------------------------------------
def render_frames(out_dir, start=None, end=None, step=1):
    """PNG image sequence (a crash never loses finished frames). Skips frames that exist."""
    sc = bpy.context.scene
    sc.render.use_persistent_data = False                       # persistent data turned cells black mid-shot (Cycles)
    os.makedirs(out_dir, exist_ok=True)
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    s, e = start or sc.frame_start, end or sc.frame_end
    for f in range(s, e + 1, step):
        path = os.path.join(out_dir, f"f_{f:04d}.png")
        if os.path.exists(path):
            continue
        sc.frame_set(f)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
    return out_dir


def encode(frames_dir, mp4, fps=30, crf=17, start_number=1):
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-start_number", str(start_number),
           "-i", os.path.join(frames_dir, "f_%04d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",   # x264 needs even sizes
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True)
    return mp4


def output_to(folder):
    """Final renders: write the animation as a PNG sequence folder/f_0001.png ... so that
    `blender -b -P shot.py -a` (or Render > Render Animation) fills it. Frames already in
    the folder are skipped, so an interrupted render picks up where it stopped (delete the
    folder to render a shot again from scratch)."""
    sc = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    sc.render.filepath = os.path.join(folder, "f_")
    sc.render.use_overwrite = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.use_file_extension = True
    return folder
