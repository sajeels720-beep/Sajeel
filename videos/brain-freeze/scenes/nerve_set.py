"""Pain-sensor close-up (shot 14): a swollen artery with nerve fibres spiralling around it
and nerve endings resting on its wall. Electric sparks crackle along the fibres, the
endings flash and send out red ripple rings. Stylised large scale in metres (artery
radius 0.2) so depth of field behaves like a normal macro shot."""
import math

import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
R_VESSEL = 0.2


def axis_point(t):
    """Centre line of the artery, t in [0, 1]: rises along +Z (fills a vertical frame)
    with a gentle bend."""
    return np.array([0.22 * math.sin(t * math.pi) - 0.1, 0.1 * (t - 0.5), -1.6 + 3.2 * t])


def frame_at(t):
    p = axis_point(t)
    q = axis_point(min(t + 1e-3, 1.0)) if t < 1 else p + (p - axis_point(t - 1e-3))
    tan = (q - p) / np.linalg.norm(q - p)
    a = np.cross(tan, [1.0, 0, 0])
    a /= np.linalg.norm(a)
    b = np.cross(tan, a)
    return p, tan, a, b


def surface_point(t, ang, lift=0.0):
    p, tan, a, b = frame_at(t)
    return p + (a * math.cos(ang) + b * math.sin(ang)) * (R_VESSEL + lift)


def artery_material():
    m = V.principled("Artery_Close", H("#A3121F"), rough=0.3, sss=0.5, sss_radius=(1.0, 0.2, 0.15), sss_scale=0.05,
                     spec=0.5, coat=0.5, emission=H("#FF1A12"), emission_strength=0.05)
    V.color_variation(m, H("#C9354A"), scale=6.0, amount=0.45)
    V.bump(m, scale=14.0, strength=0.25, distance=0.01)
    return m


def nerve_material():
    """Pale yellow nerve fibre with a 'Glow' control (fires red-orange)."""
    m = V.principled("Nerve", H("#EBCB7A"), rough=0.35, sss=0.6, sss_radius=(1.0, 0.8, 0.5), sss_scale=0.02,
                     spec=0.5, coat=0.4, emission=H("#FF3A1E"), emission_strength=0.0)
    nt = m.node_tree
    glow = nt.nodes.new("ShaderNodeValue")
    glow.name = glow.label = "Glow"
    nt.links.new(glow.outputs[0], V._inp(V.bsdf(m), "Emission Strength"))
    return m


def build(col_name="SET_NERVES", seed=6):
    rng = np.random.default_rng(seed)
    col = V.collection(col_name)
    ts = np.linspace(0, 1, 120)
    artery = K.tube("Artery_geo", [axis_point(t) for t in ts], R_VESSEL, segments=96, col=col)
    K.skin(artery, 0.12, 0.008, octaves=3, seed=3)
    V.assign(artery, artery_material())
    nmat = nerve_material()
    fibres, endings = [], []
    # three fibres spiral around the artery
    for k in range(3):
        pts = []
        for t in np.linspace(0.02, 0.98, 160):
            ang = k * 2.1 + t * 7.5 + 0.25 * math.sin(t * 23 + k)
            pts.append(surface_point(t, ang, 0.014 + 0.006 * math.sin(t * 17 + k * 2)))
        fibres.append(np.array(pts))
    # endings: short twigs off the fibres ending in small bulbs on the artery wall
    bulbs = []
    for i in range(14):
        k = i % 3
        j = int(rng.uniform(15, 145))
        start = fibres[k][j]
        t = 0.02 + 0.96 * j / 159
        ang0 = k * 2.1 + t * 7.5
        ang = ang0 + rng.uniform(0.35, 0.8) * rng.choice([-1, 1])
        t2 = float(np.clip(t + rng.uniform(-0.04, 0.04), 0.03, 0.97))
        end = surface_point(t2, ang, 0.006)
        mid = (start + end) / 2 + (start - axis_point(t)) / np.linalg.norm(start - axis_point(t)) * 0.03
        twig = K.path_spline([start, mid, end], 16)
        fibres.append(twig)
        b = K.ellipsoid(f"Ending_{i:02d}", tuple(end), (0.013, 0.013, 0.013), segments=16, col=col)
        bulbs.append(b)
        endings.append((end, (end - axis_point(t2)) / np.linalg.norm(end - axis_point(t2))))
    curves = []
    for i, pts in enumerate(fibres):
        ob = V.glow_curve(f"Nerve_{i:02d}", pts, 0.009 if i < 3 else 0.005, nmat, col=col)
        curves.append(ob)
    bulb_ob = K.join(bulbs, "Nerve_Endings_geo", col)
    V.assign(bulb_ob, nmat)
    return {"col": col, "artery": artery, "fibres": fibres, "endings": endings, "nerve_mat": nmat,
            "curves": curves, "bulbs": bulb_ob}


def lightning(name, a, b, rng, col, mat, segments=10, jitter=0.03, radius=0.0035):
    """Jagged bolt between two points (straight line + random sideways kinks)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    n1 = np.cross(d, [0.3, 0.2, 1.0])
    n1 /= np.linalg.norm(n1)
    n2 = np.cross(d / np.linalg.norm(d), n1)
    pts = []
    for i in range(segments + 1):
        t = i / segments
        off = 0 if i in (0, segments) else rng.normal(0, jitter)
        off2 = 0 if i in (0, segments) else rng.normal(0, jitter)
        pts.append(a + d * t + n1 * off + n2 * off2)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1.0)
    ob = V.link(bpy.data.objects.new(name, cu), col)
    V.assign(ob, mat)
    return ob


def sparks(parts, start, end, count=90, seed=2):
    """Electric sparks flickering along the fibres and jumping off the endings."""
    rng = np.random.default_rng(seed)
    col = V.collection("SPARKS")
    core = V.emission("Spark_Core", H("#FFD2C4"), 30.0)
    red = V.emission("Spark_Red", H("#FF2A16"), 22.0)
    fibres = parts["fibres"]
    obs = []
    for i in range(count):
        f = int(rng.uniform(start, end - 2))
        fib = fibres[int(rng.integers(0, len(fibres)))]
        j = int(rng.integers(0, len(fib) - 6))
        a = fib[j]
        b = fib[min(j + int(rng.integers(3, 12)), len(fib) - 1)]
        if rng.random() < 0.35:                                    # some bolts leap off into space
            b = a + rng.normal(0, 1, 3) * 0.1
        ob = lightning(f"Bolt_{i:02d}", a, b, rng, col, core if rng.random() < 0.4 else red,
                       jitter=0.02 + 0.03 * rng.random(), radius=0.005 + 0.004 * rng.random())
        life = int(rng.integers(2, 5))
        V.visible(ob, [(1, False), (f, True), (f + life, False)])
        obs.append(ob)
    return obs
