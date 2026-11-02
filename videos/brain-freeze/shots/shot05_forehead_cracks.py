"""SHOT 05 (7.0-8.4 s, 42 frames @30fps) - "shoots through your forehead,"
Close-up on the forehead: the shocked face squeezes into pain as glowing icy cracks shoot
out from between the eyebrows, frost spreads over the skin and ice sparkles burst off.
Push-in with a shake on the hit.
"""
import math
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "shots"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy  # noqa: I001  (bpy first: the pip bpy module only exposes bmesh after it)
import bmesh
import numpy as np
from mathutils import Vector

import character as C
import claude_sculpt_kit as K
import head_set as HS
import shot03_perfect as S03
import shot17_question as S17
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 1.4
N = 42
HIT = 5
ICE = V.hex_lin("#7FD8FF")


def crack_paths(rng, n_main=6):
    """2D crack pattern (u across, v up; metres) fanning up and out from the glabella."""
    paths = []
    for i in range(n_main):
        ang = math.radians(35 + 110 * i / (n_main - 1) + rng.uniform(-6, 6))
        d = np.array([math.cos(ang), math.sin(ang)])
        p = np.zeros(2)
        pts = [p.copy()]
        L = rng.uniform(0.045, 0.075)
        for _ in range(9):
            d = d + rng.normal(0, 0.35, 2)
            d /= np.linalg.norm(d)
            p = p + d * L / 9
            p[1] = max(p[1], 0.003 + 0.4 * abs(p[0]))               # stay above the brow line
            pts.append(p.copy())
        paths.append((np.array(pts), 0))
        for j in (3, 5, 7):                                       # side branches
            if rng.random() < 0.7:
                bd = d + np.array([-d[1], d[0]]) * rng.choice([-1, 1]) * rng.uniform(0.6, 1.2)
                q = pts[j].copy()
                bp = [q.copy()]
                for _ in range(4):
                    bd = bd + rng.normal(0, 0.4, 2)
                    bd /= np.linalg.norm(bd)
                    q = q + bd * rng.uniform(0.004, 0.008)
                    q[1] = max(q[1], 0.003 + 0.4 * abs(q[0]))
                    bp.append(q.copy())
                paths.append((np.array(bp), j))
    return paths


def project(body, origin_pts, lift=0.0009):
    """Snap points onto the face by casting rays from in front of it."""
    out = []
    for p in origin_pts:
        hit, n = S17.surface_hit(body, Vector(p) + Vector((0, -0.25, 0)), (0, 1, 0))
        if hit is not None:
            out.append(tuple(hit + n * lift))
    return out


def frost_decal(body, centre, radius_keys, col):
    """Frost film over the forehead: a copy of the face skin that follows it (Shrinkwrap),
    visible only inside an animated radius from the glabella."""
    bm = bmesh.new()
    bm.from_mesh(body.data)
    posed = C.evaluated_points(body)
    keep = set(i for i, p in enumerate(posed) if (Vector(p) - centre).length < 0.11 and p[1] < centre.y + 0.05
               and p[2] > centre.z + 0.004)                       # forehead only: above the brows
    for v in bm.verts:                                            # posed positions first (indices change on delete)
        v.co = Vector(posed[v.index])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context="VERTS")
    me = bpy.data.meshes.new("Forehead_Frost")
    bm.to_mesh(me)
    bm.free()
    ob = V.link(bpy.data.objects.new("Forehead_Frost", me), col)
    K.shade_smooth(ob)
    sub = ob.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 2
    sw = ob.modifiers.new("Hug", "SHRINKWRAP")
    sw.target, sw.wrap_method, sw.offset = body, "NEAREST_SURFACEPOINT", 0.0005
    m = bpy.data.materials.new("Frost_Film")
    if getattr(m, "node_tree", None) is None:
        m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    fr = nt.nodes.new("ShaderNodeBsdfPrincipled")
    fr.inputs["Base Color"].default_value = (*V.hex_lin("#BFE3FF"), 1)          # icy blue, not a white plaster
    fr.inputs["Roughness"].default_value = 0.22
    V._inp(fr, "Emission Color", "Emission").default_value = (*V.hex_lin("#7FC8FF"), 1)
    V._inp(fr, "Emission Strength").default_value = 0.35
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "DISTANCE"
    dist.inputs[1].default_value = tuple(centre)
    nt.links.new(geo.outputs["Position"], dist.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 160.0
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    add.inputs[1].default_value = 0.012
    nt.links.new(nz.outputs["Fac"], add.inputs[0])
    nt.links.new(dist.outputs["Value"], add.inputs[2])
    rad = nt.nodes.new("ShaderNodeValue")
    rad.name = rad.label = "FrostRadius"
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(add.outputs[0], mr.inputs["Value"])
    nt.links.new(rad.outputs[0], mr.inputs["From Min"])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = 0.012
    nt.links.new(rad.outputs[0], sub.inputs[0])
    nt.links.new(sub.outputs[0], mr.inputs["From Max"])
    amt = nt.nodes.new("ShaderNodeMath")
    amt.operation = "MULTIPLY"
    amt.inputs[1].default_value = 0.65                             # thin film: skin still shows through
    nt.links.new(mr.outputs["Result"], amt.inputs[0])
    # fade out before the decal's cut edges (brow line below, temples behind) so no straight edge shows
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    for axis, lo, hi in (("Z", centre.z + 0.004, centre.z + 0.012), ("Y", centre.y + 0.05, centre.y + 0.032)):
        fade = nt.nodes.new("ShaderNodeMapRange")
        fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = lo, hi
        nt.links.new(sep.outputs[axis], fade.inputs["Value"])
        prod = nt.nodes.new("ShaderNodeMath")
        prod.operation = "MULTIPLY"
        nt.links.new(amt.outputs[0], prod.inputs[0])
        nt.links.new(fade.outputs["Result"], prod.inputs[1])
        amt = prod
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(amt.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(fr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    V.assign(ob, m)
    V.animate_socket(rad.outputs[0], radius_keys)
    return ob


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hero, park, ice, cup = S03.hero_on_bench()
    rig, body = hero["rig"], hero["body"]
    shock = {"eyeWideLeft": 1.8, "eyeWideRight": 1.8, "browInnerUp": 1.8, "browOuterUpLeft": 1.5,   # = shot 04's end
             "browOuterUpRight": 1.5, "jawOpen": 0.22}
    off = {k: 0.0 for k in shock}
    C.face(body, {**{k: 0.0 for k in HS.PAIN}, **shock}, frame=1)
    C.face(body, {**{k: 0.0 for k in HS.PAIN}, **shock}, frame=HIT - 1)
    C.face(body, {**HS.PAIN, **off}, frame=HIT + 4)
    C.face(body, {**HS.PAIN, **off}, frame=N)
    sc = bpy.context.scene
    sc.frame_set(N)
    eyes = (S03.bone_world(rig, "eye.L") + S03.bone_world(rig, "eye.R")) / 2
    glab, gn = S17.surface_hit(body, eyes + Vector((0, -0.25, 0.012)), (0, 1, 0))
    col = V.collection("FX_FOREHEAD")
    rng = np.random.default_rng(12)
    core = V.emission("Crack_Ice", ICE, 6.0)
    for i, (pts2, j) in enumerate(crack_paths(rng)):
        pts3 = project(body, [glab + Vector((u, 0, v)) for u, v in pts2])
        if len(pts3) < 3:
            continue
        start = HIT + (0 if j == 0 else 3 + j)
        cr = V.glow_curve(f"Crack_{i:02d}", pts3, 0.0007 if j == 0 else 0.0004, core, col=col, grow=(start, start + 9),
                          taper=0.35)
        cr.visible_diffuse = cr.visible_glossy = False
    frost_decal(body, glab, [(1, 0.0), (HIT, 0.0), (HIT + 6, 0.02), (N, 0.05)], col)
    spark = V.emission("Ice_Sparkle", (0.85, 0.95, 1.0), 12.0)
    for k in range(34):                                            # ice sparkles burst off the forehead
        d = Vector((rng.normal(0, 1), -abs(rng.normal(0.8, 0.4)), rng.normal(0.3, 1))).normalized()
        b = K.ellipsoid(f"Sparkle_{k:02d}", (0, 0, 0), (0.0009,) * 3, segments=8, col=col)
        V.assign(b, spark)
        f0 = HIT + int(rng.integers(0, 6))
        V.key(b, "location", [(f0, tuple(glab + gn * 0.002)), (f0 + 14, tuple(glab + d * rng.uniform(0.04, 0.1)))],
              "QUAD", "EASE_OUT")
        V.key(b, "scale", [(1, (0.001,) * 3), (f0 - 1, (0.001,) * 3), (f0, (1, 1, 1)), (f0 + 14, (0.001,) * 3)])
    sc.frame_set(1)
    head = (S03.bone_world(rig, "head") + S03.bone_world(rig, "head", tail=True)) / 2
    S03.sun_rim_lights(head)
    r = V.camera_rig("Cam_Shot05", lens=85, fstop=4.0)
    aim = glab + Vector((0, 0, 0.012))
    V.cam_keys(r, [(1, aim + K.look_dir(-8, 3) * 0.5, aim, 85), (N, aim + K.look_dir(-5, 3) * 0.4, aim, 85)])
    V.handheld(r, amount=0.001, aim_amount=0.0008)
    V.shake(r, HIT, HIT + 8, strength=0.004, scale=1.2)
    V.compositor(glow=0.55, threshold=0.9, dispersion=0.01)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 4, 8))
    return {"hero": hero}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
