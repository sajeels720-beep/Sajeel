"""His fingertip cut in half lengthwise (shots 09-10), on the studio blue: a detailed anatomy
cutaway, like a medical illustration.

On the cut face, from the outside in:
- the outer skin in two layers: the tough horny layer on top, with the fingerprint ridges in
  section along the pad, and the living layer under it, whose wavy border into the dermis has a
  capillary loop in each papilla (and a touch sensor in some);
- the pink, fibrous dermis, with sweat glands coiled at its bottom and their ducts corkscrewing up
  to the pores on the ridges (where the water gets in);
- the yellow fatty pad in bulging lobules with pale walls between them, the artery (cut open:
  the blood cells flow inside), its vein and the nerve running along the pad, small vessels cut
  across, and onion-like pressure sensors (Pacinian corpuscles) deep in the fat;
- the bones: a smooth outer shell around a spongy inside with red marrow; the joint with its
  glossy cartilage; the tendons on both sides;
- the nail in layers on its pink, ridged bed, its root under the cuticle fold.
Behind it, the rounded outside of the far half: skin with fingerprint ridges, and the nail.

The cut face is made of regions, each a fine triangle mesh (Blender's constrained Delaunay
triangulation, so it can take relief: the fat lobules bulge, the bony struts stand out), drawn
back to front a hair apart (LAYER); a region's relief is kept flat where a region in front covers
it. Shot 09: the vessels drain (they narrow, their red fades, the blood slows). Shot 10: the pad
shrinks inwards and the skin on top of it, now too big, buckles into folds (shape key "Shrink" on
every layer, on everything in the pad and on the outside).

Stylised large scale in metres (the fingertip is 0.6 m long, about 20 times life size). Built in
the finger's own frame (x along the finger to the tip, z towards the nail, the far half at +y),
then stood up on a parent empty: the finger points up, the cut face looks at -Y, the nail is on
the left.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector, geometry as G, noise

import claude_sculpt_kit as K
import finger_inside as FI
import vessel_tunnel as VT
import vfx_kit as V

H = V.hex_lin
L = 0.6                              # base of the nail joint to the tip
BASE = -0.35                         # the cut runs on down the finger, out of shot
TOP = [(BASE, 0.165), (0.0, 0.16), (0.2, 0.158), (0.38, 0.15), (0.48, 0.134), (0.545, 0.1), (0.578, 0.058), (0.596, 0.022),
       (L, 0.0)]
BOTTOM = [(BASE, -0.17), (0.0, -0.188), (0.18, -0.214), (0.33, -0.222), (0.43, -0.205), (0.51, -0.16), (0.56, -0.095),
          (0.588, -0.045), (0.598, -0.016), (L, 0.0)]           # a round tip (the two curves meet head on)
EPI, DERMIS = 0.02, 0.055            # skin thicknesses: the outer skin, then the living skin under it
SHRINK, BUCKLE, FOLD = 0.032, 0.0095, 0.052       # how far the pad shrinks, the folds' height and spacing
LAYER = 0.0007                       # each region this much closer to the camera than the one behind
FOLD_X = 0.152                       # the cuticle fold over the nail's root
RIDGE = (0.0022, 0.0115)             # fingerprint ridges along the pad, in section: height, spacing
PAPILLA = 0.0065                     # how far the dermis's papillae reach into the outer skin
CELL = 0.0055                        # triangle size inside the regions (finer: more relief detail)
COLORS = {"corneum": ("#F2DFC9", "#E6C7AA"), "epidermis": ("#C98E78", "#E3AE94"), "dermis": ("#D06A68", "#F2A098"),
          "fat": ("#F3E6C6", "#F6C552", "#E7A23A"), "bed": ("#C2415A", "#EE8C8E"), "tendon": ("#DCD5C8", "#FBF8F1"),
          "capsule": ("#E2C9BE", "#F3E3D8"), "cortex": ("#E3D5B9", "#FBF4E4"), "marrow": ("#9C3F36", "#D08A6E", "#F4EAD3"),
          "cartilage": ("#BFDCEB", "#EEF8FD"), "nail": ("#F6E7E1", "#E8C5BE", "#F1D9D2"),
          "vessel": "#C3122A", "vein": "#6A1E3E", "nerve": "#F2CF6E", "gland": "#E9A79C", "pacini": "#F4E7DA",
          "meissner": "#F6D6CC"}


# --------------------------------------------------------------------------
# The outline and the layers' borders (side view, x along the finger, z towards the nail)
# --------------------------------------------------------------------------
def _curve(ctrl, n):
    return K.path_spline(np.array([(x, 0.0, z) for x, z in ctrl], float), n)[:, [0, 2]]


def outline(n=1600):
    """The side view of the fingertip as a closed polygon (x, z), counter-clockwise."""
    top = _curve(TOP, n // 2)
    bot = _curve(BOTTOM, n // 2)
    P = np.vstack([bot, top[::-1][1:]])                   # along the pad to the tip, back over the nail
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return P if area > 0 else P[::-1]


def _normals(P):
    """Unit normals pointing into the outline (left of the direction of travel)."""
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    return np.stack([-T[:, 1], T[:, 0]], 1)


def _arclen(P):
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def inset(P, d, base_shift=0.0):
    """Offset an outline inwards by d (a number, or one per point). The outline runs counter-
    clockwise and is open across its base (from its last point back to its first, a straight
    edge): normals come from the open curve, so its corners there don't cross; base_shift also
    moves those two ends in from the base edge. Any little loops are cut out."""
    Q = P + _normals(P) * np.asarray(d, float).reshape(-1, 1)
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


def _pad(P):
    """0 on the back of the finger, 1 on the pad (and round the tip)."""
    return np.clip((-P[:, 1] - 0.02) / 0.05, 0.0, 1.0) * np.clip((L + 0.004 - P[:, 0]) / 0.02, 0.0, 1.0)


def ridged(P, s):
    """The skin's surface: the outline with the fingerprint ridges along the pad (rounded bumps)."""
    bump = RIDGE[0] * (0.5 + 0.5 * np.cos(2 * math.pi * s / RIDGE[1])) ** 1.5
    return P - _normals(P) * (bump * _pad(P))[:, None]


def papillae(P, s):
    """How deep the dermis lies under the surface: shallow at each papilla (between the ridges),
    deep under each ridge's crest, where the sweat duct goes down."""
    w = 0.35 + 0.65 * _pad(P)
    return 0.75 * EPI + PAPILLA * w * (0.5 + 0.5 * np.cos(2 * math.pi * s / RIDGE[1]))


def _band(outer, inner):
    """A closed polygon between two open curves that run the same way (a layer of skin)."""
    return np.vstack([outer, inner[::-1]])


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


def tip_bone():
    """The end bone of the finger in side view: a broad base (its lips hold the tendons), a
    narrow waist and the tuft at the tip, a little hooked towards the pad."""
    up = [(0.03, 0.118), (0.06, 0.112), (0.12, 0.092), (0.2, 0.078), (0.28, 0.074), (0.36, 0.072), (0.42, 0.068),
          (0.455, 0.055), (0.472, 0.03), (0.474, 0.0)]
    low = [(0.03, -0.052), (0.06, -0.044), (0.12, -0.022), (0.2, -0.004), (0.28, 0.0), (0.36, -0.006), (0.42, -0.02),
           (0.455, -0.025), (0.47, -0.018), (0.474, 0.0)]
    t, b = _curve(up, 140), _curve(low, 140)
    base = [(0.03 + 0.012 * math.sin(a) ** 2, 0.033 + 0.085 * math.cos(a)) for a in np.linspace(0, math.pi, 40)][1:-1]
    P = np.vstack([b[60:], t[::-1], np.array(base), b[:60]])   # from mid-shaft round the tip, the top, the base (one piece)
    return P if 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]) > 0 else P[::-1]


def pad_weight(x):
    """0 at the joint and the very tip, 1 under the middle of the pad."""
    return np.clip(np.sin(np.clip((x - 0.04) / 0.52, 0, 1) * math.pi), 0, 1) ** 1.3


def shrink_dz(x, ripple=1.0):
    """How far a point on the pad side moves up (+z) when the pad shrinks: inwards, plus folds."""
    w = pad_weight(x)
    folds = np.sin(2 * math.pi * (x - 0.05) / FOLD) + 0.35 * np.sin(2 * math.pi * (x - 0.02) / (FOLD * 0.63))
    return SHRINK * w - ripple * BUCKLE * w * folds / 1.35                  # uneven folds, like real skin


_BOT = None


def _surface_z(x):
    """The pad's surface (z) under x."""
    global _BOT
    if _BOT is None:
        _BOT = _curve(BOTTOM, 600)
    return np.interp(x, _BOT[:, 0], _BOT[:, 1])


def lift(P, kind="fat"):
    """How far points (N x 2: x, z) rise when the pad has shrunk all the way: nothing near the
    bone, the full amount at the fat's edge and in the skin (the skin also folds)."""
    P = np.asarray(P, float).reshape(-1, 2)
    x, z = P[:, 0], P[:, 1]
    edge = _surface_z(x) + DERMIS
    ramp = np.clip((-z - 0.02) / np.maximum(-edge - 0.02, 0.02), 0.0, 1.0)
    surf = {"fat": SHRINK * 1.25 * pad_weight(x), "dermis": shrink_dz(x, 0.8), "skin": shrink_dz(x, 1.0)}[kind]
    return surf * ramp * (z < -0.02)


# --------------------------------------------------------------------------
# Regions of the cut face
# --------------------------------------------------------------------------
def _pip(pts, poly, chunk=600):
    """Which points (N x 2) lie inside a polygon (even-odd rule)."""
    out = np.zeros(len(pts), bool)
    x1, z1 = poly[:, 0], poly[:, 1]
    x2, z2 = np.roll(x1, -1), np.roll(z1, -1)
    for i in range(0, len(pts), chunk):
        p = pts[i:i + chunk]
        x, z = p[:, :1], p[:, 1:2]
        cond = (z1 > z) != (z2 > z)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (z - z1) * (x2 - x1) / (z2 - z1)
        out[i:i + chunk] = (np.sum(cond & (x < xi), axis=1) % 2) == 1
    return out


def _edge_distance(pts, poly, chunk=400):
    """Distance from each point to a polygon's nearest vertex (its outline is dense)."""
    d = np.empty(len(pts))
    for i in range(0, len(pts), chunk):
        p = pts[i:i + chunk]
        d[i:i + chunk] = np.sqrt(((p[:, None, :] - poly[None, :, :]) ** 2).sum(-1)).min(1)
    return d


def region(name, poly, depth, mat, col, relief=None, cover=(), shrink="skin", cell=CELL, seed=0):
    """A filled region of the cut face (an x, z polygon) `depth` layers in front of the cut,
    triangulated with points inside so it can take relief. relief(points) -> (dy, {attribute:
    values}): dy < 0 bulges towards the camera; it fades out at the region's edge and inside the
    `cover` polygons (regions drawn in front of it). Shape key "Shrink" (lift(kind=shrink))."""
    rng = np.random.default_rng(seed)
    poly = np.asarray(poly, float)
    lo, hi = poly.min(0), poly.max(0)
    xs = np.arange(lo[0] + cell / 2, hi[0], cell)
    zs = np.arange(lo[1] + cell / 2, hi[1], cell * 0.866)
    gx, gz = np.meshgrid(xs, zs)
    gx = gx + (np.arange(len(zs)) % 2)[:, None] * cell / 2
    pts = np.stack([gx.ravel(), gz.ravel()], 1) + rng.uniform(-0.12, 0.12, (gx.size, 2)) * cell
    pts = pts[_pip(pts, poly)] if len(pts) else pts
    if len(pts):
        pts = pts[_edge_distance(pts, poly) > 0.5 * cell]
    allp = np.vstack([poly, pts]) if len(pts) else poly
    n = len(poly)
    res = G.delaunay_2d_cdt([Vector((x, z)) for x, z in allp], [(k, (k + 1) % n) for k in range(n)],
                            [list(range(n))], 1, 1e-9)
    P2 = np.array([(v.x, v.y) for v in res[0]])
    faces = [tuple(f) for f in res[2]]
    dy, attrs = np.zeros(len(P2)), {}
    if relief is not None:
        dy, attrs = relief(P2)
        keep = np.clip(_edge_distance(P2, poly) / (1.5 * cell), 0.0, 1.0)
        for c in cover:
            c = np.asarray(c, float)
            inside = _pip(P2, c)
            keep = np.where(inside, 0.0, np.minimum(keep, np.clip(_edge_distance(P2, c) / (2.0 * cell), 0.0, 1.0)))
        dy = dy * keep
    y0 = -depth * LAYER
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y0 + d, z) for (x, z), d in zip(P2, dy)], [], faces)
    me.update()
    if len(me.polygons) and np.mean([p.normal.y for p in me.polygons]) > 0:
        me.flip_normals()                                       # it faces the camera (-y)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    for k, vals in attrs.items():
        a = me.attributes.new(k, "FLOAT", "POINT")
        a.data.foreach_set("value", np.asarray(vals, np.float32))
    ob = V.link(bpy.data.objects.new(name, me), col)
    V.assign(ob, mat)
    if shrink:
        dz = lift(P2, shrink)
        if np.any(dz != 0):
            ob.shape_key_add(name="Basis", from_mix=False)
            kb = ob.shape_key_add(name="Shrink", from_mix=False)
            kb.value = 0.0                                      # Blender 5 adds new keys switched on
            co = np.array([(x, y0 + d, z + e) for (x, z), d, e in zip(P2, dy, dz)], np.float32)
            kb.data.foreach_set("co", co.ravel())
    return ob


def _voronoi(P, scale, w=0.0):
    """Voronoi distances (F1, F2) and a random value per cell for each point."""
    f1, f2, cid = np.empty(len(P)), np.empty(len(P)), np.empty(len(P))
    for i, (x, z) in enumerate(P):
        d, pts = noise.voronoi(Vector((x * scale, z * scale, w)), distance_metric="DISTANCE")
        f1[i], f2[i] = d[0], d[1]
        c = pts[0]
        cid[i] = (math.sin(c.x * 12.9898 + c.y * 78.233 + c.z * 37.719) * 43758.5453) % 1.0
    return f1, f2, cid


def _noise(P, sx, sz, w=0.0):
    return np.array([noise.noise(Vector((x * sx, z * sz, w))) for x, z in P])


def fat_relief(P):
    """Bulging fat lobules with pale walls (septa) between them."""
    f1, f2, cid = _voronoi(P, 21.0, 0.31)
    lobe = np.clip((f2 - f1) / 0.6, 0.0, 1.0)              # 0 at a wall, rising to the lobule's middle
    dy = -0.0072 * lobe ** 0.55 - 0.0009 * _noise(P, 70, 70, 2.1)      # rounded domes
    return dy, {"tint": np.clip(lobe * 1.6, 0.0, 1.0), "cell": cid}


def marrow_relief(P):
    """The spongy inside of a bone: thin bony struts standing up round little pits of marrow."""
    f1, f2, cid = _voronoi(P, 55.0, 0.77)
    wall = 1.0 - np.clip((f2 - f1) / 0.24, 0.0, 1.0)
    return -0.0038 * wall ** 0.8, {"tint": wall, "cell": cid}


def fibre_relief(amount, sx=30.0, sz=110.0):
    """Fine fibrous relief (fibres along the finger)."""
    def relief(P):
        n = _noise(P, sx, sz, 4.2)
        return -amount * n, {"tint": 0.5 + 0.5 * n}
    return relief


def tint_relief(amount=0.0008):
    def relief(P):
        n = _noise(P, 60, 60, 1.7)
        return -amount * n, {"tint": 0.5 + 0.5 * n}
    return relief


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
def tissue(name, stops, rough=0.38, sss=0.25, coat=0.25, spec=0.45, fibres=None, cells=0.0):
    """A wet cut tissue whose colour follows the mesh's "tint" attribute through `stops`
    [(position, hex)]; fibres=(scale along the finger, across, strength) adds fine streaks;
    cells shades each fat lobule (the "cell" attribute) a little differently."""
    m = V.principled(name, H(stops[-1][1]), rough=rough, sss=sss, sss_radius=(1.0, 0.5, 0.3), sss_scale=0.012, spec=spec,
                     coat=coat)
    nt, b = m.node_tree, V.bsdf(m)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "tint"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], (*H(stops[0][1]), 1)
    els[1].position, els[1].color = stops[-1][0], (*H(stops[-1][1]), 1)
    for pos, hx in stops[1:-1]:
        e = els.new(pos)
        e.color = (*H(hx), 1)
    nt.links.new(at.outputs["Fac"], ramp.inputs["Fac"])
    color = ramp.outputs["Color"]
    if cells:
        ca = nt.nodes.new("ShaderNodeAttribute")
        ca.attribute_name = "cell"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0 - cells, 1.0 + cells * 0.4
        nt.links.new(ca.outputs["Fac"], mr.inputs["Value"])
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(color, mix.inputs[6])
        nt.links.new(mr.outputs["Result"], mix.inputs[7])
        color = mix.outputs[2]
    if fibres:
        sx, sz, k = fibres
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (sx, 1.0, sz)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        tx = nt.nodes.new("ShaderNodeTexNoise")
        tx.inputs["Scale"].default_value = 1.0
        tx.inputs["Detail"].default_value = 6.0
        nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
        fm = nt.nodes.new("ShaderNodeMapRange")
        fm.inputs["To Min"].default_value, fm.inputs["To Max"].default_value = 1.0 - k, 1.0 + k * 0.5
        nt.links.new(tx.outputs["Fac"], fm.inputs["Value"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(color, mix.inputs[6])
        nt.links.new(fm.outputs["Result"], mix.inputs[7])
        color = mix.outputs[2]
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = 0.25
        bp.inputs["Distance"].default_value = 0.002
        nt.links.new(tx.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(color, b.inputs["Base Color"])
    return m


def onion_material(name="Cut_Pacini"):
    """A Pacinian corpuscle: layer on layer like an onion (rings round its centre)."""
    m = V.principled(name, H(COLORS["pacini"]), rough=0.3, sss=0.45, sss_radius=(1.0, 0.7, 0.5), sss_scale=0.01, spec=0.5,
                     coat=0.5)
    nt, b = m.node_tree, V.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "RINGS"
    wv.rings_direction = "SPHERICAL"
    wv.inputs["Scale"].default_value = 90.0
    wv.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*H("#D9BFA9"), 1)
    ramp.color_ramp.elements[1].color = (*H("#FBF3EA"), 1)
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def nerve_material(name="Cut_Nerve"):
    """A nerve: creamy yellow bundles of fibres, streaked along its length."""
    return tissue(name, [(0.0, "#E3B54E"), (1.0, COLORS["nerve"])], rough=0.32, sss=0.35, coat=0.35, fibres=(4.0, 160.0, 0.35))


def skin_material(name="Cutaway_Skin"):
    """His skin on the outside of the far half: soft and translucent, with the fingerprint ridges
    across the pad (and fine pores)."""
    m = V.principled(name, H("#E2A68E"), rough=0.5, sss=0.4, sss_radius=(1.0, 0.4, 0.25), sss_scale=0.02, spec=0.35, coat=0.04)
    nt, b = m.node_tree, V.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave")                        # ridges across the finger, a little wavy
    wv.wave_type = "BANDS"
    wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 2 * math.pi / (20.0 * RIDGE[1])     # (bands repeat every 2 pi / (20 scale))
    wv.inputs["Distortion"].default_value = 2.0
    wv.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    pad = nt.nodes.new("ShaderNodeMapRange")                       # only on the pad side (z < 0)
    pad.inputs["From Min"].default_value, pad.inputs["From Max"].default_value = -0.02, -0.07
    nt.links.new(sep.outputs["Z"], pad.inputs["Value"])
    pores = nt.nodes.new("ShaderNodeTexVoronoi")
    pores.inputs["Scale"].default_value = 160.0
    nt.links.new(tc.outputs["Object"], pores.inputs["Vector"])
    h = nt.nodes.new("ShaderNodeMath")
    h.operation = "MULTIPLY"
    nt.links.new(wv.outputs["Fac"], h.inputs[0])
    nt.links.new(pad.outputs["Result"], h.inputs[1])
    h2 = nt.nodes.new("ShaderNodeMath")
    h2.operation = "ADD"
    nt.links.new(h.outputs[0], h2.inputs[0])
    pm = nt.nodes.new("ShaderNodeMath")
    pm.operation = "MULTIPLY"
    pm.inputs[1].default_value = 0.25
    nt.links.new(pores.outputs["Distance"], pm.inputs[0])
    nt.links.new(pm.outputs[0], h2.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.35
    bp.inputs["Distance"].default_value = 0.0025
    nt.links.new(h2.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


# --------------------------------------------------------------------------
# Things lying in the cut: vessels, the nerve, glands, sensors
# --------------------------------------------------------------------------
def _tube(name, path, radius, mat, col, y, kind="fat", segments=14, taper=None):
    """A tube along an (x, z) path lying in the cut face at depth y (its centre a little in front
    of the face, so it shows), with shape key "Shrink" (it rides up with the pad)."""
    pts = [Vector((x, y, z)) for x, z in path]
    radii = [radius * (taper(i / max(len(pts) - 1, 1)) if taper else 1.0) for i in range(len(pts))]
    ob = K.tube(name, pts, radii, segments=segments, col=col)
    V.assign(ob, mat)
    _key_lift(ob, kind)
    return ob


def _key_lift(ob, kind):
    me = ob.data
    M = ob.matrix_basis
    co = np.array([tuple(M @ v.co) for v in me.vertices])
    dz = lift(co[:, [0, 2]], kind)
    if not np.any(dz != 0):
        return
    if me.shape_keys is None:
        ob.shape_key_add(name="Basis", from_mix=False)
    kb = ob.shape_key_add(name="Shrink", from_mix=False)
    kb.value = 0.0
    base = np.array([tuple(v.co) for v in me.vertices])
    base[:, 2] += dz
    kb.data.foreach_set("co", base.astype(np.float32).ravel())


def _smooth_path(ctrl, n):
    return _curve(ctrl, n)


def _coil(centre, rng, turns=5, radius=0.0062, length=0.022, n=90):
    """A sweat gland: a tube wound up into a little ball."""
    t = np.linspace(0, 2 * math.pi * turns, n)
    u = np.linspace(-0.5, 0.5, n)
    x = centre[0] + u * length + radius * 0.5 * np.sin(t * 0.37)
    z = centre[1] + radius * np.cos(t) * (1 - 0.25 * np.cos(t * 0.21))
    x = x + radius * 0.35 * np.sin(t) + rng.normal(0, 0.0006, n)
    return np.stack([x, z], 1)


VESSEL_ENDS = [(0.03, -0.15), (0.2, -0.178), (0.31, -0.19), (0.41, -0.175), (0.49, -0.13), (0.26, -0.06), (0.08, 0.118),
               (0.33, 0.112), (-0.2, -0.13), (-0.12, 0.13)]       # small vessels cut across (x, z)


def _circle(x, z, r, n=32):
    return np.array([(x + r * math.cos(a), z + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)])


def vessel_end(name, x, z, r, y_front, wall_mat, blood_mat, col, n=24):
    """The cut end of a small vessel running on into the far half: its wall, a short open tube
    standing a little out of the cut, and the blood in it, a little way down inside. Returns both."""
    verts = [(r * math.cos(a), y, r * math.sin(a)) for y in (0.012, y_front) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    wall = V.link(bpy.data.objects.new(name, me), col)
    V.assign(wall, wall_mat)
    blood = K.tube(name + "_Blood", [Vector((0.0, 0.012, 0.0)), Vector((0.0, y_front + 0.0018, 0.0))], [r * 0.84, r * 0.84],
                   segments=n, col=col)
    V.assign(blood, blood_mat)
    for ob in (wall, blood):
        ob.location = (x, 0.0, z)
        ob["pad"] = float(z < 0)
        _key_lift(ob, "fat")
    return wall, blood


def build(col=None, at=(0.0, 0.0, 0.0)):
    """The cutaway, stood up at `at`. Returns dict(root, layers, vessels, vessel_mat, dermis_mat,
    bed_mat, shrinkers, flow)."""
    col = col or V.collection("CUTAWAY")
    root = V.link(bpy.data.objects.new("Cutaway", None), col)
    R = Matrix(((0, 0, -1), (0, 1, 0), (1, 0, 0)))                      # finger x -> up, nail z -> world -X
    root.matrix_world = Matrix.Translation(Vector(at)) @ R.to_4x4()
    rng = np.random.default_rng(5)
    P0 = outline()
    s = _arclen(P0)
    skin = ridged(P0, s)                                             # the skin's surface, ridges on the pad
    corneum_in = inset(skin, 0.38 * EPI)
    D = inset(P0, papillae(P0, s))                                   # the dermis: wavy under the outer skin
    F = inset(P0, DERMIS + 0.0035 * np.sin(2 * math.pi * s / 0.07))  # the fat: a gently uneven edge
    mats = {
        "corneum": tissue("Cut_Corneum", [(0.0, COLORS["corneum"][1]), (1.0, COLORS["corneum"][0])], rough=0.3, sss=0.4, coat=0.45),
        "epidermis": tissue("Cut_Epidermis", [(0.0, COLORS["epidermis"][0]), (1.0, COLORS["epidermis"][1])], sss=0.3),
        "dermis": tissue("Cut_Dermis", [(0.0, COLORS["dermis"][0]), (1.0, COLORS["dermis"][1])], sss=0.3,
                         fibres=(30.0, 140.0, 0.25)),
        "fat": tissue("Cut_Fat", [(0.0, COLORS["fat"][0]), (0.35, COLORS["fat"][2]), (1.0, COLORS["fat"][1])], rough=0.26,
                      sss=0.35, coat=0.4, spec=0.55, cells=0.16),
        "bed": tissue("Cut_NailBed", [(0.0, COLORS["bed"][0]), (1.0, COLORS["bed"][1])], sss=0.3, fibres=(4.0, 220.0, 0.3)),
        "tendon": tissue("Cut_Tendon", [(0.0, COLORS["tendon"][0]), (1.0, COLORS["tendon"][1])], rough=0.25, sss=0.15,
                         coat=0.5, spec=0.6, fibres=(3.0, 260.0, 0.3)),
        "capsule": tissue("Cut_Capsule", [(0.0, COLORS["capsule"][0]), (1.0, COLORS["capsule"][1])], sss=0.2,
                          fibres=(60.0, 60.0, 0.2)),
        "cortex": tissue("Cut_Cortex", [(0.0, COLORS["cortex"][0]), (1.0, COLORS["cortex"][1])], rough=0.32, sss=0.12,
                         coat=0.3, fibres=(5.0, 300.0, 0.12)),
        "marrow": tissue("Cut_Marrow", [(0.0, COLORS["marrow"][0]), (0.45, COLORS["marrow"][1]), (0.8, COLORS["marrow"][2]),
                                        (1.0, COLORS["marrow"][2])], rough=0.3, sss=0.2, coat=0.35, cells=0.12),
        "cartilage": tissue("Cut_Cartilage", [(0.0, COLORS["cartilage"][0]), (1.0, COLORS["cartilage"][1])], rough=0.12,
                            sss=0.4, coat=0.8, spec=0.7),
    }
    nail_mat = V.principled("Cut_nail", H(COLORS["nail"][0]), rough=0.15, sss=0.35, sss_radius=(1.0, 0.5, 0.5),
                            sss_scale=0.01, spec=0.6, coat=0.7)
    nail_mats = [tissue(f"Cut_Nail_{i}", [(0.0, c), (1.0, c)], rough=0.14, sss=0.35, coat=0.7, spec=0.6,
                        fibres=(2.0, 400.0, 0.08)) for i, c in enumerate(COLORS["nail"])]
    # the bones, the joint and the tendons (needed first: they cover the fat)
    mid = bone_outline(BASE, -0.03, 0.06, 0.068, flare=1.0)
    tip = tip_bone()
    mid_in, tip_in = inset(mid, 0.011), inset(tip, 0.010, 0.006)
    capsule = np.array([(-0.075, 0.125), (-0.075, -0.06), (0.06, -0.068), (0.06, 0.13)])
    capsule = _curve([tuple(p) for p in capsule] + [tuple(capsule[0])], 121)[:-1]
    ext = np.vstack([_curve([(BASE, 0.104), (-0.12, 0.112), (-0.03, 0.118), (0.03, 0.126), (0.06, 0.121)], 80),
                     _curve([(0.06, 0.112), (0.02, 0.11), (-0.04, 0.1), (-0.13, 0.098), (BASE, 0.092)], 80)])
    flex = np.vstack([_curve([(BASE, -0.044), (-0.14, -0.05), (-0.04, -0.06), (0.03, -0.068), (0.085, -0.052)], 80),
                      _curve([(0.085, -0.04), (0.03, -0.052), (-0.04, -0.044), (-0.14, -0.036), (BASE, -0.03)], 80)])
    bed = np.array([(x, z) for x, z in F if z > 0.072 and 0.11 < x < 0.565])
    bed = np.vstack([bed, [(0.11, 0.072), (0.565, 0.072)]]) if len(bed) > 3 else bed
    covers_fat = [mid, tip, capsule, ext, flex, bed] + [_circle(x, z, 0.017) for x, z in VESSEL_ENDS]
    layers, shrinkers = {}, []
    layers["epidermis"] = region("Cut_Epidermis", skin, 1, mats["epidermis"], col, tint_relief(0.0006), cover=[D], seed=1)
    layers["corneum"] = region("Cut_Corneum", _band(skin, corneum_in), 2, mats["corneum"], col, tint_relief(0.0005), seed=2)
    layers["dermis"] = region("Cut_Dermis", D, 3, mats["dermis"], col, fibre_relief(0.0016), cover=[F], shrink="dermis", seed=3)
    layers["fat"] = region("Cut_Fat", F, 4, mats["fat"], col, fat_relief, cover=covers_fat, shrink="fat", seed=4)
    if len(bed) > 3:
        layers["bed"] = region("Cut_NailBed", bed, 5, mats["bed"], col, tint_relief(0.0008), cover=[tip], shrink=None, seed=5)
    layers["capsule"] = region("Cut_Capsule", capsule, 5, mats["capsule"], col, tint_relief(0.001), cover=[mid, tip], shrink=None,
                               seed=6)
    layers["extensor"] = region("Cut_Extensor", ext, 6, mats["tendon"], col, tint_relief(0.0012), shrink=None, seed=7)
    layers["flexor"] = region("Cut_Flexor", flex, 6, mats["tendon"], col, tint_relief(0.0012), shrink=None, seed=8)
    for nm, B, Bin in (("mid", mid, mid_in), ("tip", tip, tip_in)):
        layers[f"cortex_{nm}"] = region(f"Cut_Cortex_{nm}", B, 7, mats["cortex"], col, tint_relief(0.0005), cover=[Bin],
                                        shrink=None, seed=9)
        layers[f"marrow_{nm}"] = region(f"Cut_Marrow_{nm}", Bin, 8, mats["marrow"], col, marrow_relief, shrink=None, seed=10,
                                        cell=0.0042)
    # the joint: glossy cartilage on the two bone ends, and the thin gap between them
    head = mid[mid[:, 0] > -0.066]
    head_out = inset(head, -0.0045)
    layers["cart_mid"] = region("Cut_Cartilage_Mid", _band(head_out, head), 9, mats["cartilage"], col, shrink=None, seed=11)
    base = tip[tip[:, 0] < 0.05]
    base_out = inset(base, -0.0042)
    layers["cart_tip"] = region("Cut_Cartilage_Tip", _band(base_out, base), 9, mats["cartilage"], col, shrink=None, seed=12)
    # the nail: three layers of keratin over its pink bed, its root dipping under the cuticle fold
    top = _curve(TOP, 500)
    sel = top[(top[:, 0] > 0.15) & (top[:, 0] < 0.588)]
    inner_c, outer_c = sel + [0, 0.002], sel + [0, 0.026]
    for i, (a, b) in enumerate(((0.0, 0.3), (0.3, 0.7), (0.7, 1.0))):
        lo_c, hi_c = inner_c + (outer_c - inner_c) * a, inner_c + (outer_c - inner_c) * b
        layers[f"nail_{i}"] = region(f"Cut_Nail_{i}", _band(hi_c, lo_c), 10, nail_mats[i], col, shrink=None, seed=13 + i,
                                     cell=0.004)
    # the cuticle fold: a rounded lip of skin over the nail's root (the nail grows out from under it)
    zt = lambda x: float(np.interp(x, top[:, 0], top[:, 1]))
    lip = [(FOLD_X - 0.024 * math.cos(a), zt(FOLD_X - 0.024 * math.cos(a)) + 0.031 * math.sin(a)) for a in np.linspace(0, math.pi, 40)]
    fold = np.vstack([np.array(lip), [(FOLD_X + 0.024, zt(FOLD_X + 0.024) - 0.003), (FOLD_X - 0.024, zt(FOLD_X - 0.024) - 0.003)]])
    layers["cuticle"] = region("Cut_Cuticle", fold, 11, mats["corneum"], col, tint_relief(0.0006), shrink=None, seed=17, cell=0.004)
    # things lying in the cut: the artery (cut open, blood cells flowing), its vein, the nerve
    y_fat = -4 * LAYER
    vessel_mat = FI.vessel_material("Cut_Artery")
    vein_mat = V.principled("Cut_Vein", H(COLORS["vein"]), rough=0.3, sss=0.35, sss_radius=(1.0, 0.25, 0.3), sss_scale=0.05,
                            spec=0.5, coat=0.5)
    nerve_mat = nerve_material()
    gland_mat = V.principled("Cut_Gland", H(COLORS["gland"]), rough=0.28, sss=0.4, sss_radius=(1.0, 0.5, 0.4), sss_scale=0.01,
                             spec=0.5, coat=0.5)
    cap_mat = V.principled("Cut_Capillary", H("#D01A30"), rough=0.3, sss=0.3, spec=0.5, coat=0.4, emission=H("#E0102A"),
                           emission_strength=0.3)
    artery = _smooth_path([(BASE, -0.098), (-0.15, -0.1), (0.0, -0.104), (0.15, -0.116), (0.3, -0.13), (0.42, -0.118),
                           (0.5, -0.082), (0.55, -0.038)], 160)
    vein = _smooth_path([(BASE, -0.125), (-0.15, -0.128), (0.0, -0.132), (0.14, -0.145), (0.27, -0.158), (0.38, -0.148)], 140)
    nerve = _smooth_path([(BASE, -0.074), (-0.15, -0.078), (0.0, -0.084), (0.14, -0.09), (0.28, -0.098), (0.4, -0.09),
                          (0.48, -0.06)], 150)
    vessels, flow_paths = [], []
    ob = _tube("Cut_Artery", artery, 0.0125, vessel_mat, col, y_fat - 0.011, taper=lambda t: 1.0 - 0.35 * t)
    vessels.append(ob)
    flow_paths.append((artery, 0.0125, ob))
    ob = _tube("Cut_Vein", vein, 0.0095, vein_mat, col, y_fat - 0.008, taper=lambda t: 1.0 - 0.3 * t)
    vessels.append(ob)
    layers["nerve"] = _tube("Cut_Nerve", nerve, 0.0098, nerve_mat, col, y_fat - 0.009, taper=lambda t: 1.0 - 0.3 * t)
    # branches: the artery's up towards the skin of the pad, the nerve's to the sensors
    for k, x in enumerate((0.06, 0.17, 0.27, 0.36, 0.45)):
        z0 = float(np.interp(x, artery[:, 0], artery[:, 1]))
        zs = float(_surface_z(x)) + DERMIS - 0.004
        br = _smooth_path([(x, z0), (x + 0.012, (z0 + zs) / 2 + rng.uniform(-0.006, 0.006)), (x + 0.02, zs)], 30)
        vessels.append(_tube(f"Cut_Artery_Branch_{k}", br, 0.0052, vessel_mat, col, y_fat - 0.006, taper=lambda t: 1.0 - 0.5 * t))
    pacini = []
    for k, (x, z) in enumerate(((0.12, -0.064), (0.24, -0.072), (0.34, -0.07))):
        e = K.ellipsoid(f"Cut_Pacini_{k}", (0.0, 0.0, 0.0), (0.019, 0.008, 0.011), rot=(0, rng.uniform(-25, 25), 0),
                        segments=28, col=col)
        e.location = (x, y_fat - 0.007, z)
        V.assign(e, onion_material())
        _key_lift(e, "fat")
        pacini.append(e)
        zn = float(np.interp(x - 0.03, nerve[:, 0], nerve[:, 1]))
        twig = _smooth_path([(x - 0.03, zn), (x - 0.022, (zn + z) / 2), (x - 0.017, z)], 20)
        layers[f"nerve_twig_{k}"] = _tube(f"Cut_Nerve_Twig_{k}", twig, 0.0028, nerve_mat, col, y_fat - 0.006)
    # small vessels cut across: the cut ends of tubes running into the far half, blood inside
    blood_mat = V.principled("Cut_Blood", H("#7A0A16"), rough=0.18, sss=0.3, sss_radius=(1.0, 0.2, 0.15), sss_scale=0.02, spec=0.6,
                             coat=0.7, emission=H("#C0101E"), emission_strength=0.15)
    stubs = []
    for k, (x, z) in enumerate(VESSEL_ENDS):
        stubs.extend(vessel_end(f"Cut_VesselEnd_{k}", x, z, rng.uniform(0.0065, 0.0095), y_fat - 0.004, vessel_mat, blood_mat, col))
    vessels.extend(stubs)
    # in the skin: a capillary loop in each papilla of the pad, sweat glands and their ducts
    N0 = _normals(P0)
    d_pap = papillae(P0, s)
    w_pad = _pad(P0)
    y_derm = -3 * LAYER
    caps = []
    phase = s / RIDGE[1]
    tips = np.nonzero((np.abs((phase % 1.0) - 0.5) < 0.5 / (RIDGE[1] / np.mean(np.diff(s)))) & (w_pad > 0.6)
                      & (P0[:, 0] > -0.2) & (P0[:, 0] < 0.57))[0]
    for k, i in enumerate(tips[::2]):
        p, n = P0[i], N0[i]
        t = np.array([-n[1], n[0]])
        a = p + n * (d_pap[i] + 0.0035)
        loop = [a + t * 0.0022 + n * 0.012, a + t * 0.0022, a + n * -0.0008, a - t * 0.0022, a - t * 0.0022 + n * 0.012]
        caps.append(_tube(f"Cut_Capillary_{k}", _smooth_path([tuple(q) for q in loop], 16), 0.0013, cap_mat, col, y_derm - 0.003,
                          kind="dermis", segments=8))
        if k % 4 == 1:                                                    # a touch sensor in some papillae
            m = K.ellipsoid(f"Cut_Meissner_{k}", (0.0, 0.0, 0.0), (0.0028, 0.002, 0.0042), segments=12, col=col)
            m.location = (a[0] + n[0] * 0.006, y_derm - 0.003, a[1] + n[1] * 0.006)
            V.assign(m, V.principled("Cut_Meissner", H(COLORS["meissner"]), rough=0.3, sss=0.4, spec=0.5, coat=0.4))
            _key_lift(m, "dermis")
            caps.append(m)
    crests = np.nonzero((((phase + 0.5) % 1.0 - 0.5) ** 2 < 0.0016) & (w_pad > 0.8) & (P0[:, 0] > -0.05) & (P0[:, 0] < 0.5))[0]
    picked, last = [], -1.0
    for i in crests:
        if P0[i, 0] - last > 0.075:
            picked.append(i)
            last = P0[i, 0]
    glands = []
    for k, i in enumerate(picked):
        p, n = skin[i], N0[i]
        t = np.array([-n[1], n[0]])
        deep = P0[i] + n * (DERMIS - 0.0095)
        coil = _coil(deep, rng)
        glands.append(_tube(f"Cut_SweatGland_{k}", coil, 0.0021, gland_mat, col, y_derm - 0.004, kind="dermis", segments=8))
        top_d = P0[i] + n * (d_pap[i] + 0.002)
        duct = [tuple(deep + n * 0.004)] + [tuple(deep + (top_d - deep) * u + t * 0.0012 * math.sin(u * 7)) for u in
                                            np.linspace(0.15, 1.0, 10)]
        cork = [tuple(top_d + (p - top_d) * u + t * 0.0028 * math.sin(u * 2 * math.pi * 3)) for u in np.linspace(0.0, 1.0, 40)]
        glands.append(_tube(f"Cut_SweatDuct_{k}", _smooth_path(duct + cork[1:], 90), 0.0014, gland_mat, col, y_derm - 0.004,
                            kind="skin", segments=8))
    # the rounded outside of the far half, and its nail
    skin_mat = skin_material()
    layers["outside"] = outside("Cutaway_Outside", skin_mat, col)
    layers["nail_plate"] = nail_plate("Cutaway_Nail", nail_mat, col)
    layers["fold"] = nail_fold("Cutaway_Fold", skin_mat, col)
    everything = list(layers.values()) + vessels + pacini + caps + glands
    for ob in everything:
        if ob.parent is None:                                  # built in the finger's frame: keep it
            mb = ob.matrix_basis.copy()
            ob.parent = root
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_basis = mb
    shrinkers = [o for o in everything if o.data.shape_keys]
    return {"root": root, "layers": layers, "vessels": vessels, "stubs": stubs, "capillaries": caps, "vessel_mat": vessel_mat,
            "cap_mat": cap_mat, "blood_mat": blood_mat, "dermis_mat": mats["dermis"], "bed_mat": mats["bed"], "shrinkers": shrinkers,
            "flow": flow_paths, "col": col}


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
        zc, ht = (a + b) / 2, (a - b) / 2
        w = width * (a - b) / 2
        for p in phi:
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
    its cut edge matching the nail on the cut face."""
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


def nail_fold(name, mat, col, x=FOLD_X, phi1=0.95, offset=0.012, radius=0.02, width=0.94):
    """The cuticle fold round the outside: a roll of skin over the nail's root, from the cut face
    round the back of the finger (its end at the cut matches the lip on the cut face)."""
    top, bot = _curve(TOP, 400), _curve(BOTTOM, 400)
    a, b = float(np.interp(x, top[:, 0], top[:, 1])), float(np.interp(x, bot[:, 0], bot[:, 1]))
    zc, h, w = (a + b) / 2, (a - b) / 2, width * (a - b) / 2
    path = [Vector((x, -11 * LAYER, zc + h + offset))]
    path += [Vector((x, (w + offset) * math.sin(p), zc + (h + offset) * math.cos(p))) for p in np.linspace(0, phi1, 24)]
    ob = K.tube(name, path, [radius] * len(path), segments=20, col=col)
    V.assign(ob, mat)
    return ob


# --------------------------------------------------------------------------
# Animation
# --------------------------------------------------------------------------
def _eased(keys, f):
    """A 0..1 value at frame f from [(frame, value)], eased between the keys."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            u = (f - f0) / max(f1 - f0, 1e-9)
            return v0 + (v1 - v0) * u * u * (3 - 2 * u)
    return keys[-1][1]


def drain(parts, start, end, narrow=0.5, frames=(1, 39)):
    """The vessels narrow and their red fades, the blood slows to a trickle (and the living skin
    pales with them). frames: the shot's frames, for the blood cells."""
    for ob in parts["vessels"]:
        V.key(ob, "scale", [(start, (1.0, 1.0, 1.0)), (end, (narrow, 1.0, narrow) if ob in parts["stubs"] else
                                                          (1.0, 1.0, 1.0))])
    for ob in parts["vessels"]:
        if ob not in parts["stubs"]:
            _narrow_key(ob, start, end, narrow)
    b = V.bsdf(parts["vessel_mat"])
    V.animate_socket(b.inputs["Base Color"], [(start, (*H(COLORS["vessel"]), 1)), (end, (*H("#9A4E58"), 1))])
    V.animate_socket(V._inp(b, "Emission Strength"), [(start, 0.08), (end, 0.0)])
    bb = V.bsdf(parts["blood_mat"])
    V.animate_socket(bb.inputs["Base Color"], [(start, (*H("#7A0A16"), 1)), (end, (*H("#4E2A30"), 1))])
    V.animate_socket(V._inp(bb, "Emission Strength"), [(start, 0.15), (end, 0.0)])
    cb = V.bsdf(parts["cap_mat"])
    V.animate_socket(cb.inputs["Base Color"], [(start, (*H("#D01A30"), 1)), (end, (*H("#B87A80"), 1))])
    V.animate_socket(V._inp(cb, "Emission Strength"), [(start, 0.3), (end, 0.0)])
    for ob in parts["capillaries"]:
        if ob.name.startswith("Cut_Capillary"):
            V.key(ob, "scale", [(start, (1.0, 1.0, 1.0)), (end, (1.0, 0.6, 1.0))])
    for m, pale in ((parts["dermis_mat"], "#E9B4A6"), (parts["bed_mat"], "#E3A6A0")):
        nt = m.node_tree
        ramp = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeValToRGB")
        el = ramp.color_ramp.elements[-1]
        el.color = tuple(el.color)
        el.keyframe_insert("color", frame=start)
        el.color = (*H(pale), 1)
        el.keyframe_insert("color", frame=end)
    parts["drain"] = (start, end, narrow)
    _blood(parts, frames)


def _narrow_key(ob, start, end, narrow):
    """Shape key "Narrow" on a tube: every point moves towards the tube's centre line (found as
    the middle of each ring of its vertices)."""
    me = ob.data
    co = np.array([tuple(v.co) for v in me.vertices])
    seg = 14 if not ob.name.startswith("Cut_Artery_Branch") else 14
    n = len(co)
    rings = n // seg if n % seg == 0 else None
    if rings is None:
        return
    C = co.reshape(rings, seg, 3).mean(1, keepdims=True)
    narrowed = (C + (co.reshape(rings, seg, 3) - C) * narrow).reshape(-1, 3)
    if me.shape_keys is None:
        ob.shape_key_add(name="Basis", from_mix=False)
    kb = ob.shape_key_add(name="Narrow", from_mix=False)
    kb.value = 0.0
    kb.data.foreach_set("co", narrowed.astype(np.float32).ravel())
    for f, v in ((start, 0.0), (end, 1.0)):
        kb.value = v
        kb.keyframe_insert("value", frame=f)
    V.ease_id(me.shape_keys, "BEZIER")


def _blood(parts, frames):
    """Red blood cells flowing in the cut-open artery: they slow down and thin out as it drains,
    and ride up with the pad when it shrinks (see shrink)."""
    start, end, narrow = parts["drain"]
    col = parts["col"]
    mesh = VT.rbc_mesh("Cut_RBC", radius=1.0, segments=24)
    mat = VT.cell_material()
    V._inp(V.bsdf(mat), "Emission Strength").default_value = 0.5
    mesh.materials.append(mat)
    rng = np.random.default_rng(11)
    f0, f1 = frames
    speed = lambda f: 0.012 * (1.0 - 0.8 * _eased([(start, 0.0), (end, 1.0)], f))       # metres per frame
    travelled = {f0 - 1: 0.0}
    for f in range(f0, f1 + 2):
        travelled[f] = travelled[f - 1] + speed(f)
    cells = []
    for path, radius, tube in parts["flow"]:
        Ls = _arclen(path)
        ys = np.array([v.co.y for v in tube.data.vertices]).mean()
        count = int(Ls[-1] / 0.03)
        for i in range(count):
            ob = V.link(bpy.data.objects.new(f"Cut_RBC_{i:02d}", mesh), col)
            ob.parent = parts["root"]
            s0 = rng.uniform(0, Ls[-1])
            off = rng.uniform(-0.5, 0.5)
            rot0 = Euler(rng.uniform(0, 2 * math.pi, 3)).to_matrix()
            spin = rng.normal(0, 0.06, 3)
            gone = rng.uniform(0.25, 1.0)                                  # when it thins out (share of the drain)
            ob["base"] = [0.0, 0.0, 0.0]
            keyed = []
            for f in range(f0 - 1, f1 + 2):
                sx = (s0 + travelled[f]) % Ls[-1]
                x = float(np.interp(sx, Ls, path[:, 0]))
                z = float(np.interp(sx, Ls, path[:, 1]))
                t = sx / Ls[-1]
                room = radius * (1.0 - 0.35 * t) * (1.0 - (1.0 - narrow) * _eased([(start, 0.0), (end, 1.0)], f))
                z += off * room * 0.9
                sc = 0.0062 * (1.0 - 0.35 * t) * min(1.0, 4.0 * min(t, 1.0 - t) / 0.2)
                sc *= 1.0 - _eased([(start + (end - start) * gone * 0.5, 0.0), (start + (end - start) * gone, 1.0)], f) * 0.85
                keyed.append((f, x, ys - room * 0.25, z, sc))
                ob.matrix_basis = Matrix.Translation(Vector((x, ys - room * 0.25, z))) @ \
                    (Euler(spin * (f - f0)).to_matrix() @ rot0).to_4x4() @ Matrix.Scale(max(sc, 1e-4), 4)
                ob.keyframe_insert("location", frame=f)
                ob.keyframe_insert("rotation_euler", frame=f)
                ob.keyframe_insert("scale", frame=f)
            V.ease_id(ob, "LINEAR")
            ob["track"] = [list(k) for k in keyed]
            cells.append(ob)
    parts["cells"] = cells


def shrink(parts, keys):
    """keys = [(frame, 0..1)]: the pad shrinks and the skin buckles (and everything in the pad
    rides up with it, the blood cells too)."""
    for ob in parts["shrinkers"]:
        kb = ob.data.shape_keys.key_blocks.get("Shrink")
        if kb is None:
            continue
        for f, v in keys:
            kb.value = v
            kb.keyframe_insert("value", frame=f)
        V.ease_id(ob.data.shape_keys, "BEZIER")
    for ob in parts.get("cells", []):
        for f, x, y, z, sc in ob["track"]:
            dz = float(lift(np.array([[x, z]]), "fat")[0]) * _eased(keys, f)
            ob.location = (x, y, z + dz)
            ob.keyframe_insert("location", frame=f)
        V.ease_id(ob, "LINEAR")
