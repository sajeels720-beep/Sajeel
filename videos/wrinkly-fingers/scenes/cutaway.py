"""His fingertip cut in half lengthwise (shots 09-10), on the studio blue: the layers of skin,
the yellow fatty pad, the blood vessels, the bone and the nail, like a textbook cutaway.

The cut face is a stack of flat layers (each region drawn on top of the one before, a hair
closer to the camera), so the edges between them are clean curves; behind it, the rounded
outside of the far half with its nail. Shot 09: the vessels drain (they narrow and their red
fades). Shot 10: the pad shrinks inwards and the skin on top of it, now too big, buckles into
folds (shape key "Shrink" on every layer and on the outside).

Stylised large scale in metres (the fingertip is 0.6 m long). Built in the finger's own frame
(x along the finger to the tip, z towards the nail, the far half at +y), then stood up on a
parent empty: the finger points up, the cut face looks at -Y, the nail is on the left.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
L = 0.6                              # base of the nail joint to the tip
BASE = -0.35                         # the cut runs on down the finger, out of shot
TOP = [(BASE, 0.165), (0.0, 0.16), (0.2, 0.158), (0.38, 0.15), (0.48, 0.134), (0.545, 0.1), (0.578, 0.058), (0.596, 0.022),
       (L, 0.0)]
BOTTOM = [(BASE, -0.17), (0.0, -0.188), (0.18, -0.214), (0.33, -0.222), (0.43, -0.205), (0.51, -0.16), (0.56, -0.095),
          (0.588, -0.045), (0.598, -0.016), (L, 0.0)]           # a round tip (the two curves meet head on)
EPI, DERMIS = 0.02, 0.055            # skin thicknesses: the outer skin, then the living skin under it
COLORS = {"epidermis": "#E3B49B", "dermis": "#E9958E", "fat": "#F4CF6A", "bed": "#E7787A", "bone": "#F1E8D4",
          "marrow": "#E6C9A3", "cartilage": "#D9EEF5", "vessel": "#C3122A", "nail": "#F2D9D2"}
SHRINK, BUCKLE, FOLD = 0.032, 0.0095, 0.052       # how far the pad shrinks, the folds' height and spacing
LAYER = 0.0007                                   # each layer this much closer to the camera


def _curve(ctrl, n):
    return K.path_spline(np.array([(x, 0.0, z) for x, z in ctrl], float), n)[:, [0, 2]]


def outline(n=700):
    """The side view of the fingertip as a closed polygon (x, z), counter-clockwise."""
    top = _curve(TOP, n // 2)
    bot = _curve(BOTTOM, n // 2)
    P = np.vstack([bot, top[::-1][1:]])                   # along the pad to the tip, back over the nail
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return P if area > 0 else P[::-1]


def inset(P, d, base_shift=0.0):
    """Offset an outline inwards by d. The outline runs counter-clockwise and is open across its
    base (from its last point back to its first, a straight edge): normals come from the open
    curve, so its corners there don't cross; base_shift also moves those two ends in from the
    base edge. Any little loops (where d is more than a curve's radius) are cut out."""
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.stack([-T[:, 1], T[:, 0]], 1)                  # left of the direction of travel: inside
    Q = P + N * d
    Q[0, 0] += base_shift
    Q[-1, 0] += base_shift
    return _unloop(Q)


def _crossing(P):
    """The first pair of edges of a closed polygon that cross: (i, j, where) or None."""
    A, B = P, np.roll(P, -1, axis=0)
    n = len(P)
    S = B - A
    for i in range(n):
        r = S[i]
        den = r[0] * S[:, 1] - r[1] * S[:, 0]
        qp = A - A[i]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (qp[:, 0] * S[:, 1] - qp[:, 1] * S[:, 0]) / den
            u = (qp[:, 0] * r[1] - qp[:, 1] * r[0]) / den
        hit = (np.abs(den) > 1e-14) & (t > 0) & (t < 1) & (u > 0) & (u < 1)
        hit[[i, (i - 1) % n, (i + 1) % n]] = False
        js = np.nonzero(hit)[0]
        if len(js):
            return i, int(js[0]), A[i] + r * t[js[0]]
    return None


def _unloop(P):
    """Cut the little loops out of a polygon whose edges cross (keeps the bigger part)."""
    P = np.asarray(P, float)
    for _ in range(200):
        c = _crossing(P)
        if c is None:
            break
        i, j, X = c
        i, j = min(i, j), max(i, j)
        P = np.vstack([P[:i + 1], [X], P[j + 1:]]) if j - i <= len(P) // 2 else np.vstack([[X], P[i + 1:j + 1]])
    return P


def pad_weight(x):
    """0 at the joint and the very tip, 1 under the middle of the pad."""
    return np.clip(np.sin(np.clip((x - 0.04) / 0.52, 0, 1) * math.pi), 0, 1) ** 1.3


def shrink_dz(x, ripple=1.0):
    """How far a point on the pad side moves up (+z) when the pad shrinks: inwards, plus folds."""
    w = pad_weight(x)
    folds = np.sin(2 * math.pi * (x - 0.05) / FOLD) + 0.35 * np.sin(2 * math.pi * (x - 0.02) / (FOLD * 0.63))
    return SHRINK * w - ripple * BUCKLE * w * folds / 1.35                  # uneven folds, like real skin


def _ngon(name, P, y, mat, col, shrink=None):
    """A flat filled outline at depth y (finger frame). shrink(x, z) -> dz for the "Shrink" key."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x, z in P], [], [list(range(len(P)))])
    ob = V.link(bpy.data.objects.new(name, me), col)
    V.assign(ob, mat)
    if shrink is not None:
        ob.shape_key_add(name="Basis", from_mix=False)
        kb = ob.shape_key_add(name="Shrink", from_mix=False)
        kb.value = 0.0                                     # Blender 5 adds new keys switched on
        for i, (x, z) in enumerate(P):
            kb.data[i].co = Vector((x, y, z + shrink(x, z)))
    return ob


def _flat(name, color, rough=0.55, sss=0.0, texture=None, emission=0.0):
    """Cut-face material: soft and a little moist, like a sliced specimen in a textbook."""
    m = V.principled(name, H(color), rough=rough, sss=sss, sss_radius=(1.0, 0.4, 0.3), sss_scale=0.01, spec=0.35, coat=0.15,
                     emission=H(color), emission_strength=emission)
    if texture == "fat":                                          # rounded fat lobules
        nt = m.node_tree
        b = V.bsdf(m)
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.feature = "DISTANCE_TO_EDGE"
        vor.inputs["Scale"].default_value = 26.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, (*H("#D9A443"), 1)
        ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.09, (*H(color), 1)
        nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    elif texture == "bone":                                       # spongy inside
        nt = m.node_tree
        b = V.bsdf(m)
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 60.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.25, (*H("#C9A57E"), 1)
        ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.55, (*H(color), 1)
        nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def bone_outline(x0, x1, half0, half1, zc=0.035, n=160, flare=1.25):
    """A finger bone in side view: a waisted shaft with a wider base and a rounded end."""
    t = np.linspace(0, 1, n)
    x = x0 + (x1 - x0) * t
    half = (half0 + (half1 - half0) * t) * (1 - 0.22 * np.sin(math.pi * t)) * (1 + (flare - 1) * np.exp(-t / 0.08))
    top = np.stack([x, zc + half], 1)
    bot = np.stack([x, zc - half * 0.92], 1)
    cap = [(x1 + half1 * 0.9 * math.sin(a), zc + half1 * math.cos(a)) for a in np.linspace(math.pi - 0.1, 0.1, 16)]
    P = np.vstack([bot, np.array(cap), top[::-1]])
    return P if 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]) > 0 else P[::-1]


def outside(name, mat, col, nx=150, nphi=48, width=0.94):
    """The rounded outside of the far half (y >= 0): each slice across the finger is half an
    ellipse from the nail side (phi 0) to the pad side (phi pi); its edges are the cut's outline.
    Shape key "Shrink": the pad side sinks in and folds, matching the cut face."""
    u = np.sin(np.linspace(0, math.pi / 2, nx))                             # dense towards the tip
    xs = BASE + (L - BASE) * u
    top, bot = _curve(TOP, 400), _curve(BOTTOM, 400)
    zt = np.interp(xs, top[:, 0], top[:, 1])
    zb = np.interp(xs, bot[:, 0], bot[:, 1])
    phi = np.linspace(0, math.pi, nphi)
    verts, keyed = [], []
    for x, a, b in zip(xs, zt, zb):
        zc, ht, hb = (a + b) / 2, (a - b) / 2, (a - b) / 2
        w = width * (a - b) / 2
        for p in phi:
            k = (1 + math.cos(p)) / 2                                     # 1 on the nail side, 0 on the pad side
            z = zc + ht * math.cos(p)
            verts.append((x, w * math.sin(p), z))
            pad = max(0.0, -math.cos(p)) ** 1.5                          # the pad side moves, the nail side doesn't
            keyed.append((x, w * math.sin(p) * (1 - 0.15 * pad * pad_weight(x)), z + pad * float(shrink_dz(x))))
    faces = []
    for i in range(nx - 1):
        for j in range(nphi - 1):
            a = i * nphi + j
            faces.append((a, a + 1, a + nphi + 1, a + nphi))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    mid = (nx // 2) * nphi + nphi // 2                                   # a face on the far side: must face +y
    f = next(p for p in me.polygons if mid in p.vertices)
    if f.normal.y < 0:
        me.flip_normals()
    for p in me.polygons:
        p.use_smooth = True
    ob = V.link(bpy.data.objects.new(name, me), col)
    V.assign(ob, mat)
    ob.shape_key_add(name="Basis", from_mix=False)
    kb = ob.shape_key_add(name="Shrink", from_mix=False)
    kb.value = 0.0                                         # Blender 5 adds new keys switched on
    for i, c in enumerate(keyed):
        kb.data[i].co = Vector(c)
    return ob


def nail_plate(name, mat, col, x0=0.16, x1=0.585, phi1=0.8, t0=0.002, t1=0.026, nx=60, nphi=16, width=0.94):
    """The nail on the outside of the far half: a curved plate lying over the top of the finger,
    its cut edge matching the nail band on the cut face."""
    top, bot = _curve(TOP, 400), _curve(BOTTOM, 400)
    xs = np.linspace(x0, x1, nx)
    zt, zb = np.interp(xs, top[:, 0], top[:, 1]), np.interp(xs, bot[:, 0], bot[:, 1])
    phi = np.linspace(0, phi1, nphi)
    verts = []
    for t in (t1, t0):                                                   # outer skin of the plate, then inner
        for x, a, b in zip(xs, zt, zb):
            zc, h, w = (a + b) / 2, (a - b) / 2, width * (a - b) / 2
            for p in phi:
                verts.append((x, (w + t) * math.sin(p), zc + (h + t) * math.cos(p)))
    n = nx * nphi
    faces = []
    for i in range(nx - 1):
        for j in range(nphi - 1):
            a = i * nphi + j
            faces.append((a, a + nphi, a + nphi + 1, a + 1))                        # outer
            faces.append((n + a, n + a + 1, n + a + nphi + 1, n + a + nphi))        # inner
    for i in range(nx - 1):                                                         # the rims
        for j in (0, nphi - 1):
            a = i * nphi + j
            faces.append((a, n + a, n + a + nphi, a + nphi) if j else (a, a + nphi, n + a + nphi, n + a))
    for j in range(nphi - 1):
        for i in (0, nx - 1):
            a = i * nphi + j
            faces.append((a, a + 1, n + a + 1, n + a) if i else (a, n + a, n + a + 1, a + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)                     # a closed plate: all outwards
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = V.link(bpy.data.objects.new(name, me), col)
    V.assign(ob, mat)
    return ob


def skin_material(name="Cutaway_Skin"):
    m = V.principled(name, H("#E2A68E"), rough=0.42, sss=0.35, sss_radius=(1.0, 0.4, 0.25), sss_scale=0.02, spec=0.45, coat=0.2)
    V.bump(m, scale=90.0, strength=0.08, distance=0.002)
    return m


def build(col=None, at=(0.0, 0.0, 0.0)):
    """The cutaway, stood up at `at`. Returns dict(root, layers, vessels, vessel_mat, dermis_mat, shrinkers)."""
    col = col or V.collection("CUTAWAY")
    root = V.link(bpy.data.objects.new("Cutaway", None), col)
    R = Matrix(((0, 0, -1), (0, 1, 0), (1, 0, 0)))                      # finger x -> up, nail z -> world -X
    root.matrix_world = Matrix.Translation(Vector(at)) @ R.to_4x4()
    P = outline()
    mats = {k: _flat(f"Cut_{k}", c, sss=0.15 if k in ("dermis", "bed") else 0.0,
                     texture="fat" if k == "fat" else ("bone" if k == "marrow" else None))
            for k, c in COLORS.items() if k not in ("vessel", "nail")}
    vessel_mat = V.principled("Cut_vessel", H(COLORS["vessel"]), rough=0.3, sss=0.2, spec=0.5, coat=0.4,
                              emission=H("#E0102A"), emission_strength=0.25)
    nail_mat = V.principled("Cut_nail", H(COLORS["nail"]), rough=0.18, sss=0.3, sss_radius=(1.0, 0.5, 0.5), sss_scale=0.01,
                            spec=0.6, coat=0.6)
    layers, shrinkers = {}, []
    pad_only = lambda f: (lambda x, z: f(x) if z < 0 else 0.0)
    layers["epidermis"] = _ngon("Cut_Epidermis", P, -1 * LAYER, mats["epidermis"], col, pad_only(shrink_dz))
    D = inset(P, EPI)
    layers["dermis"] = _ngon("Cut_Dermis", D, -2 * LAYER, mats["dermis"], col, pad_only(lambda x: shrink_dz(x, 0.8)))
    F = inset(P, DERMIS)
    layers["fat"] = _ngon("Cut_Fat", F, -3 * LAYER, mats["fat"], col,
                          pad_only(lambda x: float(SHRINK * 1.25 * pad_weight(x))))
    # the nail bed: the band of living tissue between the bone and the nail
    bed = np.array([(x, z) for x, z in F if z > 0.07 and 0.12 < x < 0.56])
    bed = np.vstack([bed, [(0.12, 0.07), (0.56, 0.07)]]) if len(bed) > 3 else bed
    if len(bed) > 3:
        layers["bed"] = _ngon("Cut_NailBed", bed, -4 * LAYER, mats["bed"], col)
    # the bones: the end of the middle bone, the joint, and the tip bone with its rounded tuft
    mid = bone_outline(BASE, -0.03, 0.06, 0.068, flare=1.0)
    tip = bone_outline(0.025, 0.46, 0.075, 0.04, flare=1.15)
    layers["bone_mid"] = _ngon("Cut_Bone_Mid", mid, -5 * LAYER, mats["bone"], col)
    layers["bone_tip"] = _ngon("Cut_Bone_Tip", tip, -5 * LAYER, mats["bone"], col)
    layers["marrow_mid"] = _ngon("Cut_Marrow_Mid", inset(mid, 0.013), -6 * LAYER, mats["marrow"], col)
    layers["marrow_tip"] = _ngon("Cut_Marrow_Tip", inset(tip, 0.012, 0.012), -6 * LAYER, mats["marrow"], col)
    joint = np.array([(-0.032, 0.11), (-0.032, -0.04), (0.027, -0.04), (0.027, 0.11)])
    layers["cartilage"] = _ngon("Cut_Joint", joint, -4 * LAYER, mats["cartilage"], col)
    # the nail: a band lying on the skin over the top of the finger, past the tip
    top = _curve(TOP, 400)
    sel = top[(top[:, 0] > 0.16) & (top[:, 0] < 0.585)]
    nail = np.vstack([sel + [0, 0.002], (sel + [0, 0.026])[::-1]])
    layers["nail"] = _ngon("Cut_Nail", nail, -7 * LAYER, nail_mat, col)
    # blood vessels cut across in the pad and the living skin
    rng = np.random.default_rng(5)
    vessels = []
    spots = [(0.06, -0.12), (0.14, -0.155), (0.22, -0.13), (0.29, -0.175), (0.36, -0.14), (0.42, -0.165), (0.47, -0.11),
             (0.1, -0.07), (0.3, -0.09), (0.52, -0.06), (0.26, 0.105), (0.4, 0.1)]
    for i, (x, z) in enumerate(spots):
        r = rng.uniform(0.011, 0.018)
        c = np.array([(x + r * math.cos(a), z + r * 0.85 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)[:-1]])
        ob = _ngon(f"Cut_Vessel_{i}", c - (x, z), -8 * LAYER, vessel_mat, col)
        ob.location = (x, 0.0, z)
        ob["pad"] = float(z < 0)
        vessels.append(ob)
    skin = skin_material()
    layers["outside"] = outside("Cutaway_Outside", skin, col)
    layers["nail_plate"] = nail_plate("Cutaway_Nail", nail_mat, col)
    for ob in list(layers.values()) + vessels:
        if ob.parent is None:
            ob.parent = root
    shrinkers = [o for o in layers.values() if o.data.shape_keys]
    return {"root": root, "layers": layers, "vessels": vessels, "vessel_mat": vessel_mat, "dermis_mat": mats["dermis"],
            "bed_mat": mats["bed"], "shrinkers": shrinkers}


def drain(parts, start, end, narrow=0.5):
    """The vessels narrow and their red fades (and the living skin pales with them)."""
    for ob in parts["vessels"]:
        V.key(ob, "scale", [(start, (1.0, 1.0, 1.0)), (end, (narrow, 1.0, narrow))])
    b = V.bsdf(parts["vessel_mat"])
    V.animate_socket(b.inputs["Base Color"], [(start, (*H(COLORS["vessel"]), 1)), (end, (*H("#B26A6E"), 1))])
    V.animate_socket(V._inp(b, "Emission Strength"), [(start, 0.25), (end, 0.0)])
    for m, pale in ((parts["dermis_mat"], "#E9B4A6"), (parts["bed_mat"], "#E3A6A0")):
        bb = V.bsdf(m)
        sock = bb.inputs["Base Color"]
        if not sock.is_linked:
            V.animate_socket(sock, [(start, tuple(sock.default_value)), (end, (*H(pale), 1))])


def shrink(parts, keys):
    """keys = [(frame, 0..1)]: the pad shrinks and the skin buckles (and the vessels in the
    pad ride up with it)."""
    for ob in parts["shrinkers"]:
        kb = ob.data.shape_keys.key_blocks["Shrink"]
        for f, v in keys:
            kb.value = v
            kb.keyframe_insert("value", frame=f)
        V.ease_id(ob.data.shape_keys, "BEZIER")
    for ob in parts["vessels"]:
        if ob["pad"]:
            x, _, z = ob.location
            V.key(ob, "location", [(f, (x, 0.0, z + v * SHRINK * 1.1 * float(pad_weight(np.array(x))))) for f, v in keys])
