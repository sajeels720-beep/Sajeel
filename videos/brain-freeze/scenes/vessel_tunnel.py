"""Inside a blood vessel (shot 13): a gently winding tunnel with a wet, glowing red wall
and red blood cells (biconcave discs) streaming along it. Stylised scale in metres:
cell diameter 8 cm, tunnel radius 0.5 m, so the camera can fly through comfortably.
Cells ride the tunnel path with a Curve modifier; each speed group is one object that
slides along the curve."""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
RADIUS = 0.5
LENGTH = 16.0


def path_points(n=200):
    y = np.linspace(0, LENGTH, n)
    x = 0.55 * np.sin(y / 3.2)
    z = 0.35 * np.sin(y / 4.6 + 1.0)
    return np.stack([x, y, z], 1)


def path_curve(col):
    cu = bpy.data.curves.new("Tunnel_Path", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    P = path_points()
    sp.points.add(len(P) - 1)
    for i, p in enumerate(P):
        sp.points[i].co = (*p, 1.0)
    ob = V.link(bpy.data.objects.new("Tunnel_Path", cu), col)
    ob.hide_render = True
    return ob


def arc(P):
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def point_at(s):
    """World point and tangent at arc length s along the path."""
    P = path_points(800)
    L = arc(P)
    s = float(np.clip(s, 0, L[-1]))
    p = np.array([np.interp(s, L, P[:, k]) for k in range(3)])
    q = np.array([np.interp(min(s + 0.05, L[-1]), L, P[:, k]) for k in range(3)])
    t = q - p
    return Vector(p), Vector(t / max(np.linalg.norm(t), 1e-9))


def wall_material():
    m = V.principled("Vessel_Wall", H("#9A1626"), rough=0.38, sss=0.6, sss_radius=(1.0, 0.2, 0.15), sss_scale=0.06,
                     spec=0.3, coat=0.15, emission=H("#FF2A2A"), emission_strength=0.04)
    V.color_variation(m, H("#C2404F"), scale=5.0, amount=0.5)
    nt = m.node_tree
    b = V.bsdf(m)
    st = b.inputs.get("Specular Tint")                              # wet highlights stay blood-red, not grey
    if st is not None and len(st.default_value) >= 3:
        st.default_value = (1.0, 0.3, 0.3, 1.0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")                     # cell-like wall lining
    vor.inputs["Scale"].default_value = 9.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.25
    bp.inputs["Distance"].default_value = 0.015
    nt.links.new(vor.outputs["Distance"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def build_wall(col):
    P = path_points(240)
    ob = K.tube("Tunnel_Wall_geo", P, RADIUS, segments=64, col=col)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if len(f.verts) > 4], context="FACES")   # open ends
    bmesh.ops.reverse_faces(bm, faces=bm.faces)                                              # face inward
    bm.to_mesh(ob.data)
    bm.free()
    K.skin(ob, 0.35, 0.05, octaves=3, seed=2)                          # gentle bulges in the wall
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.06
    sol.offset = -1.0
    V.assign(ob, wall_material())
    return ob


def rbc_mesh(name, radius=0.04, segments=40):
    """Biconcave red blood cell (Evans-Fung thickness profile), lying in the XY plane."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=1.0)
    for v in bm.verts:
        rho = min(math.hypot(v.co.x, v.co.y), 1.0)
        t = math.sqrt(max(1 - rho * rho, 0.0)) * (0.207 + 2.003 * rho ** 2 - 1.123 * rho ** 4)
        v.co = Vector((v.co.x * radius, v.co.y * radius, math.copysign(t * 0.5 * radius, v.co.z)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def cell_material():
    m = V.principled("RBC", H("#B5121B"), rough=0.32, sss=0.55, sss_radius=(1.0, 0.2, 0.15), sss_scale=0.02,
                     spec=0.55, coat=0.35, emission=H("#FF2A20"), emission_strength=0.12)
    V.color_variation(m, H("#D8323A"), scale=30.0, amount=0.4)
    return m


def build_cells(col, curve_ob, groups=((0.0, 90, 1), (0.0, 90, 2), (0.0, 90, 3)), seed=4):
    """Speed groups of cells; each group is one joined object deformed along the path
    (local X = distance along the tunnel). Returns the group objects."""
    rng = np.random.default_rng(seed)
    proto = rbc_mesh("RBC_proto")
    mat = cell_material()
    obs = []
    for gi, (_, count, _) in enumerate(groups):
        bm = bmesh.new()
        for i in range(count):
            s = rng.uniform(-2.0, LENGTH)
            r = RADIUS * 0.78 * math.sqrt(rng.uniform(0.0, 1.0))
            a = rng.uniform(0, 2 * math.pi)
            # local frame: X along the tunnel, Y/Z across it
            off = Vector((s, r * math.cos(a), r * math.sin(a)))
            rot = Vector(rng.uniform(0, 2 * math.pi, 3))
            sc = rng.uniform(0.85, 1.12)
            tmp = bmesh.new()
            tmp.from_mesh(proto)
            M = Matrix.Translation(off) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Scale(sc, 4)
            bmesh.ops.transform(tmp, matrix=M, verts=tmp.verts)
            me_tmp = bpy.data.meshes.new("tmp")
            tmp.to_mesh(me_tmp)
            tmp.free()
            bm.from_mesh(me_tmp)
            bpy.data.meshes.remove(me_tmp)
        me = bpy.data.meshes.new(f"RBC_group_{gi}")
        bm.to_mesh(me)
        bm.free()
        ob = V.link(bpy.data.objects.new(f"RBC_group_{gi}", me), col)
        K.shade_smooth(ob)
        V.assign(ob, mat)
        cm = ob.modifiers.new("FollowTunnel", "CURVE")
        cm.object = curve_ob
        cm.deform_axis = "POS_X"
        obs.append(ob)
    bpy.data.meshes.remove(proto)
    return obs
