"""Ice cream set for shots 1-2 (and the callback in shot 19): a striped paper cup with
three scoops on a worn wooden park table, a steel spoon, and a carved-scoop swap for the
big bite. Real-world scale (meters), cup centred at the origin, table top at Z=0."""
import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
CUP_H, CUP_R_TOP, CUP_R_BOT = 0.075, 0.042, 0.031
SCOOPS = {  # name: (centre, radius, colour, speck colour, speck threshold, speck scale)
    "Strawberry": ((-0.018, 0.0, 0.088), 0.027, "#F49AB0", "#C4234F", 0.64, 160),
    "Mint": ((0.018, 0.004, 0.087), 0.027, "#AEE9D2", "#3B2418", 0.70, 110),
    "Vanilla": ((0.0, 0.002, 0.118), 0.026, "#FFF1D2", "#6B4A33", 0.80, 420),
}
DIG = Vector((0.008, -0.012, 0.137))          # where the spoon bites the vanilla scoop (faces the camera)
DIG_N = Vector((0.36, -0.62, 0.70)).normalized()   # surface normal there


def ice_cream_material(name, hexcol, speck_hex, thr, speck_scale):
    m = V.principled(f"IceCream_{name}", H(hexcol), rough=0.42, sss=0.6, sss_radius=(1.0, 0.45, 0.35),
                     sss_scale=0.004, spec=0.45, coat=0.12)
    V.color_variation(m, H(speck_hex), scale=speck_scale, amount=1.0, threshold=thr)
    V.bump(m, scale=300, strength=0.22, distance=0.0005)
    return m


def cup_material():
    """Pink/cream paper stripes around the cup, with a faint paper grain."""
    m = V.principled("Cup_Paper", H("#FF8FB1"), rough=0.55, spec=0.3)
    nt = m.node_tree
    b = V.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    at = nt.nodes.new("ShaderNodeMath"); at.operation = "ARCTAN2"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 12 / (2 * math.pi)
    fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*H("#FF8FB1"), 1)
    mix.inputs[7].default_value = (*H("#FFF6EC"), 1)
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], at.inputs[0])
    nt.links.new(sep.outputs["X"], at.inputs[1])
    nt.links.new(at.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], fr.inputs[0])
    nt.links.new(fr.outputs[0], gt.inputs[0])
    nt.links.new(gt.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    V.bump(m, scale=900, strength=0.08, distance=0.0003)
    return m


def build_cup(col, mat):
    rows = [(z, r) for z, r in ((0.0, CUP_R_BOT), (CUP_H, CUP_R_TOP))]
    ts = np.linspace(0, 1, 40)
    path = np.stack([np.zeros_like(ts), np.zeros_like(ts), ts * CUP_H], 1)
    radii = CUP_R_BOT + (CUP_R_TOP - CUP_R_BOT) * ts
    cup = K.tube("Cup_geo", path, radii, segments=96, col=col)
    rim = K.tube("Cup_rim", K.path_ring((0, 0, CUP_H - 0.001), (0, 0, 1), CUP_R_TOP + 0.0005, 96), 0.0022,
                 segments=16, col=col)
    cup = K.join([cup, rim], "Cup_geo", col)
    V.assign(cup, mat)
    return cup


def build_scoop(name, center, r, mat, col, seed, skirt=True):
    c = np.array(center)
    ob = K.ellipsoid(name, tuple(c), (r, r, r * 0.9), segments=64, col=col)
    K.voxel_remesh(ob, r / 45)
    K.skin(ob, r * 0.45, r * 0.07, octaves=4, seed=seed)                 # soft lumps
    K.skin(ob, r * 0.16, r * 0.035, octaves=3, ridged=True, seed=seed + 1)  # scooper ridges / crumbles
    if skirt:                                                           # melted lip where it sits
        P = K.co(ob)
        z = (P[:, 2] - c[2]) / r
        band = np.exp(-((z + 0.45) / 0.16) ** 2)
        K.displace(ob, band * r * 0.07)
    K.smooth(ob, iterations=1, factor=0.25)
    V.assign(ob, mat)
    return ob


def build_spoon(col, mat):
    """Steel spoon in its own frame: bowl centred at the origin, tip toward -Y, handle +Y,
    concave side +Z."""
    outer = K.ellipsoid("spoon_outer", (0, 0, 0), (0.017, 0.026, 0.0075), segments=64, col=col)
    inner = K.ellipsoid("spoon_inner", (0, -0.0005, 0.004), (0.0155, 0.0245, 0.0068), segments=64, col=col)
    K.boolean(outer, inner)
    cutter = K.ellipsoid("spoon_cap", (0, 0, 0.03), (0.05, 0.05, 0.028), segments=24, col=col)
    K.boolean(outer, cutter)
    handle_path = K.path_spline([(0, 0.022, 0.0015), (0, 0.06, 0.006), (0, 0.11, 0.018), (0, 0.15, 0.026)], 40)
    t = np.linspace(0, 1, len(handle_path))
    handle = K.tube("spoon_handle", handle_path, 0.0035 + 0.0035 * t ** 1.5, segments=24,
                    squash=np.stack([np.ones_like(t), np.full_like(t, 0.32)], 1), side=(1, 0, 0), col=col)
    spoon = K.join([outer, handle], "Spoon_geo", col)
    K.voxel_remesh(spoon, 0.0005)
    K.smooth(spoon, iterations=3, factor=0.5)
    V.assign(spoon, mat)
    return spoon


def build(col_name="SET_ICECREAM"):
    col = V.collection(col_name)
    mats = {k: ice_cream_material(k, *v[2:]) for k, v in SCOOPS.items()}
    cup = build_cup(col, cup_material())
    scoops = {k: build_scoop(f"Scoop_{k}_geo", v[0], v[1], mats[k], col, seed=i * 7)
              for i, (k, v) in enumerate(SCOOPS.items())}
    # choc chips on the mint scoop
    chip_mat = V.principled("ChocChip", H("#3B2418"), rough=0.5, spec=0.35)
    mint = scoops["Mint"]
    pts, nrm = K.scatter(mint, 22, mask=K.mask_normal(mint, (0, -0.4, 1), -0.6, 0.4), seed=3, min_dist=0.006)
    chips = []
    rng = np.random.default_rng(4)
    for i, (p, n) in enumerate(zip(pts, nrm)):
        s = rng.uniform(0.0016, 0.0028)
        ch = K.ellipsoid(f"chip_{i}", tuple(p - n * s * 0.4), (s, s * 0.8, s * 0.6),
                         rot=tuple(rng.uniform(0, 180, 3)), segments=12, col=col)
        chips.append(ch)
    chips_ob = K.join(chips, "Mint_Chips_geo", col)
    V.assign(chips_ob, chip_mat)
    # drips running down the cup
    drip_mats = (mats["Strawberry"], mats["Vanilla"])
    for i, (ang, length, mat) in enumerate(((200, 0.022, drip_mats[0]), (300, 0.014, drip_mats[1]))):
        a = math.radians(ang)
        pts = []
        for k in np.linspace(0, 1, 12):
            z = CUP_H + 0.003 - length * k
            r = CUP_R_BOT + (CUP_R_TOP - CUP_R_BOT) * (z / CUP_H) + 0.0012
            pts.append((r * math.cos(a), r * math.sin(a), z))
        tk = np.linspace(0, 1, len(pts))
        d = K.tube(f"Drip_{i}_geo", pts, 0.0028 + 0.0022 * tk ** 3, segments=16, col=col)
        V.assign(d, mat)
    # carved vanilla (swapped in while the spoon hides the bite) + the chunk on the spoon
    carved = build_scoop("Scoop_Vanilla_carved_geo", SCOOPS["Vanilla"][0], SCOOPS["Vanilla"][1], mats["Vanilla"],
                         col, seed=14)
    bite_rot = [math.degrees(a) for a in DIG_N.to_track_quat("Z", "Y").to_euler()]
    bite = K.ellipsoid("bite_cut", tuple(DIG + DIG_N * 0.003), (0.019, 0.016, 0.0125),
                       rot=tuple(bite_rot), segments=48, col=col)
    K.boolean(carved, bite)
    K.voxel_remesh(carved, SCOOPS["Vanilla"][1] / 45)
    near = K.mask_near(carved, [tuple(DIG)], 0.03)
    K.skin(carved, 0.004, 0.0012, octaves=3, ridged=True, mask=near, seed=21)
    K.smooth(carved, iterations=1, factor=0.25)
    V.assign(carved, mats["Vanilla"])
    spoon = build_spoon(col, V.principled("Spoon_Steel", (0.86, 0.87, 0.89), rough=0.14, metal=1.0))
    chunk = K.ellipsoid("Chunk_Vanilla_geo", (0, -0.002, 0.011), (0.017, 0.021, 0.0125), segments=48, col=col)
    K.voxel_remesh(chunk, 0.0006)
    K.skin(chunk, 0.006, 0.0016, octaves=4, seed=31)
    K.skin(chunk, 0.0025, 0.0007, octaves=3, ridged=True, seed=32)
    V.assign(chunk, mats["Vanilla"])
    # table
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0.1, 0))
    table = bpy.context.active_object
    table.name = "Table_geo"
    table.scale = (1.6, 1.0, 1.0)
    V.link(table, col)
    wood = V.polyhaven("wood_table_worn", "textures", "1k")
    V.assign(table, V.textured("Table_Wood", wood, scale=2.2, tint=(1.0, 0.92, 0.85)))
    return {"col": col, "cup": cup, "scoops": scoops, "carved": carved, "spoon": spoon, "chunk": chunk,
            "table": table, "mats": mats}


def spoon_rig(parts, name="SpoonCtrl"):
    """Empty that drives the spoon (and the chunk riding in it); quaternion rotation so
    keyframed turns never flip."""
    ctrl = V.link(bpy.data.objects.new(name, None), parts["col"])
    ctrl.rotation_mode = "QUATERNION"
    parts["spoon"].parent = ctrl
    parts["chunk"].parent = ctrl
    return ctrl


def spoon_quat(tip_dir, face_dir):
    """Orientation pointing the spoon tip (-Y local) along tip_dir with the concave side
    (+Z local) turned toward face_dir."""
    y = -Vector(tip_dir).normalized()
    z = Vector(face_dir) - y * Vector(face_dir).dot(y)
    z.normalize()
    x = y.cross(z).normalized()
    return Matrix((x, y, z)).transposed().to_quaternion()


def key_spoon(ctrl, keys):
    """keys = [(frame, location, tip_dir, face_dir), ...] with eased motion."""
    prev = None
    for f, loc, tip, face in keys:
        q = spoon_quat(tip, face)
        if prev is not None and prev.dot(q) < 0:
            q.negate()
        prev = q
        ctrl.location = loc
        ctrl.rotation_quaternion = q
        ctrl.keyframe_insert("location", frame=f)
        ctrl.keyframe_insert("rotation_quaternion", frame=f)
    V.ease_id(ctrl)
