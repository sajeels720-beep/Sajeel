"""Head cutaway set (shots 6, 17, 18, 19): the protagonist's skull top cut away with a
glowing cut edge (his brain-reveal look), a real brain inside, frost that spreads over the
brain and ice crystal clusters that grow, then shatter.

Brain model: "Detailed Human Brain Model" by Schmidt's, NIH 3D entry 3DPX-021161, CC BY
(credit it in the video description). Downloaded on first use."""
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

import character as C
import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
BRAIN_URL = ("https://3d.nih.gov/api/submissions/43648/runs/32ff69ef-ae74-4c0e-86d1-27cd28b3d371/"
             "output-files/2120336")
BRAIN_CREDIT = "Detailed Human Brain Model by Schmidt's, NIH 3D (3DPX-021161), CC BY"


def brain_file():
    return V._get(BRAIN_URL, os.path.join(V.ASSET_DIR, "nih", "brain_human-nih3d.glb"))


def import_brain(col):
    """The NIH brain as one mesh, real size in metres, facing -Y, origin at its centre."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=brain_file())
    new = [o for o in bpy.data.objects if o not in before]
    new_names = [o.name for o in new]
    meshes = [o for o in new if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    brain = bpy.context.active_object
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for n in new_names:                                           # leftover empties from the glTF
        o = bpy.data.objects.get(n)
        if o is not None and o is not brain:
            bpy.data.objects.remove(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    brain.name = "Brain_geo"
    me = brain.data
    me.transform(Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(0.001, 4))   # mm -> m, front to -Y
    P = np.array([v.co[:] for v in me.vertices])
    c = (P.min(0) + P.max(0)) / 2
    me.transform(Matrix.Translation(Vector(-c)))
    me.materials.clear()
    V.link(brain, col)
    K.shade_smooth(brain)
    return brain


def brain_material():
    """Pink-grey wet brain with darker sulci and controls: Frost (radius in m from the
    'FrostFrom' point), Glow (red emission strength)."""
    m = V.principled("Brain", H("#E7A3A8"), rough=0.38, sss=0.45, sss_radius=(1.0, 0.4, 0.35), sss_scale=0.006,
                     spec=0.5, coat=0.35)
    nt = m.node_tree
    b = V.bsdf(m)
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")                 # darker folds
    ao.inputs["Distance"].default_value = 0.006
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*H("#8A3C4C"), 1)
    ramp.color_ramp.elements[1].color = (*H("#EDB0B4"), 1)
    ramp.color_ramp.elements[0].position = 0.35
    nt.links.new(ao.outputs["AO"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    V.bump(m, scale=900, strength=0.12, distance=0.0002)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    frm = nt.nodes.new("ShaderNodeValue")
    frm.name = frm.label = "Frost"
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "DISTANCE"
    dist.name = "FrostFrom"
    nt.links.new(geo.outputs["Position"], dist.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 90.0
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    add.inputs[1].default_value = 0.012
    nt.links.new(nz.outputs["Fac"], add.inputs[0])
    nt.links.new(dist.outputs["Value"], add.inputs[2])
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(add.outputs[0], mr.inputs["Value"])
    nt.links.new(frm.outputs[0], mr.inputs["From Min"])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = 0.012
    nt.links.new(frm.outputs[0], sub.inputs[0])
    nt.links.new(sub.outputs[0], mr.inputs["From Max"])
    frost = nt.nodes.new("ShaderNodeBsdfPrincipled")
    frost.inputs["Base Color"].default_value = (*H("#EAF6FF"), 1)
    frost.inputs["Roughness"].default_value = 0.35
    V._inp(frost, "Emission Color", "Emission").default_value = (*H("#8FD3FF"), 1)
    V._inp(frost, "Emission Strength").default_value = 0.15
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 700.0
    nt.links.new(geo.outputs["Position"], vor.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.7
    bp.inputs["Distance"].default_value = 0.0003
    nt.links.new(vor.outputs["Distance"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], frost.inputs["Normal"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs["Result"], mix.inputs[0])
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(frost.outputs[0], mix.inputs[2])
    glow = nt.nodes.new("ShaderNodeValue")
    glow.name = glow.label = "Glow"
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*H("#FF2A2A"), 1)
    nt.links.new(glow.outputs[0], em.inputs["Strength"])
    addsh = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mix.outputs[0], addsh.inputs[0])
    nt.links.new(em.outputs[0], addsh.inputs[1])
    nt.links.new(addsh.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def set_frost_origin(mat, point):
    mat.node_tree.nodes["FrostFrom"].inputs[1].default_value = tuple(point)


def head_measure(hero):
    """Posed head landmarks: eye centre, crown top, cranium bbox above the eyes."""
    body, rig = hero["body"], hero["rig"]
    rest = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    posed = C.evaluated_points(body)
    eyes = (rig.matrix_world @ rig.pose.bones["eye.L"].head + rig.matrix_world @ rig.pose.bones["eye.R"].head) / 2
    top = rest[:, 2].max()
    head = rest[:, 2] > top - 0.24
    near = np.linalg.norm(posed[:, :2] - np.array(eyes[:2]) - np.array([0, 0.06]), axis=1) < 0.16
    cran = posed[head & near & (posed[:, 2] > eyes.z - 0.01)]
    return {"eyes": eyes, "min": Vector(cran.min(0)), "max": Vector(cran.max(0)), "points": posed[head & near]}


def cut_head(hero, cut_z, tilt_deg=12, glow_color="#FF7A1A", col=None):
    """Remove the skull top above a tilted plane (higher at the back); rim_ring() then
    covers the cut edge with a glowing band. Returns the cutter object."""
    col = col or V.collection("CUTAWAY")
    body = hero["body"]
    m = head_measure(hero)
    size = 0.6
    bpy.ops.mesh.primitive_cube_add(size=size, location=(m["eyes"].x, m["eyes"].y + 0.05, cut_z + size / 2))
    cutter = bpy.context.active_object
    cutter.name = "Skull_Cutter"
    V.link(cutter, col)
    cutter.rotation_euler = (math.radians(-tilt_deg), 0, 0)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    rim = V.principled("Cut_Rim", H("#FFB37A"), rough=0.5, emission=H(glow_color), emission_strength=4.0)
    V.assign(cutter, rim)
    boo = body.modifiers.new("Cutaway", "BOOLEAN")
    boo.operation, boo.object, boo.solver = "DIFFERENCE", cutter, "EXACT"
    boo.material_mode = "TRANSFER"
    if hasattr(boo, "use_hole_tolerant"):
        boo.use_hole_tolerant = True
    _before_subsurf(body, ["Cutaway"])
    hair_cut = cutter.copy()                                      # hair stops a little below the skull rim
    hair_cut.name = "Hair_Cutter"
    col.objects.link(hair_cut)
    hair_cut.location.z -= 0.012
    for p in hero["parts"]:
        if "short" in p.name or "hair" in p.name.lower():
            hb = p.modifiers.new("Cutaway", "BOOLEAN")
            hb.operation, hb.object, hb.solver = "DIFFERENCE", hair_cut, "EXACT"
            _before_subsurf(p, ["Cutaway"])
    cutter["hair_cutter"] = hair_cut.name
    return cutter


def _before_subsurf(ob, names):
    """Move the named modifiers just before the Subdivision modifier."""
    mods = [m.name for m in ob.modifiers]
    sub = next((n for n in mods if ob.modifiers[n].type == "SUBSURF"), None)
    if sub is None:
        return
    for n in names:
        while [m.name for m in ob.modifiers].index(n) > [m.name for m in ob.modifiers].index(sub):
            bpy.context.view_layer.objects.active = ob
            with bpy.context.temp_override(object=ob):
                bpy.ops.object.modifier_move_up(modifier=n)


def place_brain(brain, hero, cut_z, fill=0.95):
    """Scale and place the brain inside the cranium so its crown pokes above the cut."""
    m = head_measure(hero)
    P = np.array([v.co[:] for v in brain.data.vertices])
    size = P.max(0) - P.min(0)
    inner = (m["max"] - m["min"]) - Vector((0.024, 0.024, 0.0))
    s = fill * min(inner.x / size[0], inner.y / size[1])
    brain.scale = (s, s, s)
    top_target = m["max"].z - 0.013
    brain.location = (float((m["min"].x + m["max"].x) / 2), float((m["min"].y + m["max"].y) / 2) + 0.004,
                      float(top_target - size[2] * s / 2))
    bpy.ops.object.select_all(action="DESELECT")                  # bake it so local = world for crystals
    brain.select_set(True)
    bpy.context.view_layer.objects.active = brain
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return s


def crystal_clusters(brain, start, end, origin, count=40, seed=4, col=None, size=(0.009, 0.028)):
    """Ice crystal clusters that sprout over the top of the brain, spreading from origin:
    each cluster is its own object (origin at its base) so it can grow and later shatter.
    Returns [(object, base_point, grow_frame)]."""
    col = col or V.collection("ICE")
    rng = np.random.default_rng(seed)
    bpy.context.view_layer.update()
    ice = V.principled("Ice_Crystal", H("#DDF3FF"), rough=0.12, transmission=0.55, ior=1.31, spec=0.6,
                       emission=H("#9ED8FF"), emission_strength=0.45)
    up = K.mask_normal(brain, (0, 0, 1), 0.15, 0.6)               # brain transforms are applied: local = world
    pts, nrm = K.scatter(brain, count, mask=up, seed=seed, min_dist=0.012)
    out = []
    d = [np.linalg.norm(np.array(p) - np.array(origin)) for p in pts]
    dmax = max(d) if d else 1.0
    for i, (p, n) in enumerate(zip(pts, nrm)):
        wp = Vector(p)
        wn = Vector(n).normalized()
        k = int(rng.integers(3, 7))
        local = [tuple(wp + Vector(rng.normal(0, 0.004, 3))) for _ in range(k)]
        dirs = [tuple((wn + Vector(rng.normal(0, 0.45, 3))).normalized()) for _ in range(k)]
        lens = rng.uniform(*size, k)
        ob, _ = K.crystals(f"Ice_{i:02d}", brain, local, direction=dirs, lengths=lens, tilt=8, broken=0.3,
                           col=col, symmetry_x=False, thickness=0.18)
        ob.data.transform(Matrix.Translation(-wp))
        ob.location = wp
        V.assign(ob, ice)
        f = int(start + (end - start - 8) * d[i] / dmax)
        if end > 1:                                               # grow in turn; start < 1 = already grown
            V.key(ob, "scale", [(1, (0.001,) * 3), (max(f, 1), (0.001,) * 3), (max(f, 1) + 8, (1, 1, 1))],
                  "BACK", "EASE_OUT")
        out.append((ob, wp, f))
    return out


def attach_to_head(hero, objs):
    """Bone-parent objects to the head so cutter, brain and ice follow head motion."""
    rig = hero["rig"]
    bpy.context.view_layer.update()
    for ob in objs:
        mw = ob.matrix_world.copy()
        ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", "head"
        ob.matrix_world = mw


PAIN = {"eyeBlinkLeft": 1.0, "eyeBlinkRight": 1.0, "eyeSquintLeft": 1.2, "eyeSquintRight": 1.2,  # a wince you
        "browInnerUp": 1.6, "browDownLeft": 0.6, "browDownRight": 0.6, "noseSneerLeft": 1.0,          # read at phone
        "noseSneerRight": 1.0, "cheekSquintLeft": 1.0, "cheekSquintRight": 1.0, "mouthStretchLeft": 1.0,  # size: at 1.0
        "mouthStretchRight": 1.0, "mouthFrownLeft": 0.6, "mouthFrownRight": 0.6, "mouthUpperUpLeft": 0.5,  # it read as
        "mouthUpperUpRight": 0.5, "jawOpen": 0.12}                                                         # sleeping


def cutaway_scene(hero, cut_above_eyes=0.052, tilt=12):
    """Cut the head, add the brain. Returns {"brain", "brain_mat", "cutter", "cut_z", "eyes", "top"}."""
    m = head_measure(hero)
    cut_z = m["eyes"].z + cut_above_eyes
    cutter = cut_head(hero, cut_z, tilt_deg=tilt)
    col = V.collection("BRAIN")
    brain = import_brain(col)
    place_brain(brain, hero, cut_z)
    mat = brain_material()
    V.assign(brain, mat)
    P = np.array([v.co[:] for v in brain.data.vertices])
    front_top = Vector((float(P[:, 0].mean()), float(P[:, 1].min()) + 0.02, float(P[:, 2].max()) - 0.015))
    set_frost_origin(mat, front_top)
    return {"brain": brain, "brain_mat": mat, "cutter": cutter, "cut_z": cut_z, "eyes": m["eyes"],
            "top": Vector((float(P[:, 0].mean()), float(P[:, 1].mean()), float(P[:, 2].max()))),
            "frost_origin": front_top}


def bake_static(hero, extra=()):
    """For shots where the character holds still: bake pose, expression, skull cut and
    hair cut into plain meshes (no per-frame armature or boolean work), then re-add a
    render-time subdivision. Keeps object names and materials."""
    rig = hero["rig"]
    obs = [hero["body"]] + [p for p in hero["parts"]] + list(extra)
    obs += [o for o in bpy.data.objects if o.type == "MESH" and o.parent is rig and o not in obs]
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in obs:
        subs = [m for m in ob.modifiers if m.type == "SUBSURF"]
        lvl = max([m.render_levels for m in subs] or [0])
        for m in subs:
            m.show_viewport = False
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=False)
        mw = ob.matrix_world.copy()
        ob.modifiers.clear()
        if ob.data.shape_keys:
            ob.shape_key_clear()
        old = ob.data
        ob.data = me
        ob.parent = None
        ob.matrix_world = mw
        if lvl and not ob.modifiers and "short" not in ob.name:   # cut hair cards subdivide badly (very slow)
            s = ob.modifiers.new("Subdivision", "SUBSURF")
            s.levels, s.render_levels = 0, lvl
        if old.users == 0:
            bpy.data.meshes.remove(old)
    return obs


def rim_ring(body, cutter, radius=0.0065, col=None, glow="#FF7A1A", below=0.002):
    """Glowing ring along the cut edge of the (baked) head - his hot-cut look. Slices the
    head just under the cut plane and sweeps a tube along the outer skin loop."""
    import bmesh
    col = col or V.collection("CUTAWAY")
    plane_n = (cutter.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    plane_p = cutter.matrix_world @ Vector((0, 0, -0.3)) - plane_n * below
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.transform(body.matrix_world)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                                 plane_co=plane_p, plane_no=plane_n)
    cut_edges = [g for g in res["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]
    adj = {}
    for e in cut_edges:
        a, b = e.verts
        adj.setdefault(a.index, []).append(b.index)
        adj.setdefault(b.index, []).append(a.index)
    bm.verts.ensure_lookup_table()
    co = {i: bm.verts[i].co.copy() for i in adj}
    bm.free()
    seen, loops = set(), []
    for start_i in adj:
        if start_i in seen:
            continue
        loop, prev, cur = [start_i], None, start_i
        seen.add(start_i)
        while True:
            nxt = [n for n in adj[cur] if n != prev and n not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        loops.append(loop)
    if not loops:
        return None

    def spread(lp):
        P = np.array([tuple(co[i]) for i in lp])
        return float(np.ptp(P[:, 0]) + np.ptp(P[:, 1]))
    loop = max(loops, key=spread)                                 # the outer skin loop is the widest
    pts = np.array([tuple(co[i]) for i in loop] + [tuple(co[loop[0]])])
    pts = K.resample(pts, 0.003)
    ring = K.tube("Cut_Rim_Ring", pts, radius, segments=12, col=col)
    hot = V.principled("Cut_Hot", H("#FFC48A"), rough=0.4, emission=H(glow), emission_strength=6.0)
    V.assign(ring, hot)
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_shadow"):
        setattr(ring, attr, False)                                # glows on camera, doesn't light the face
    return ring
