"""X-ray head (shots 7 and 16): the protagonist's head as see-through blue glass with a
glowing rim (his x-ray skin look) on a clean sky-blue backdrop, with the brain, glowing
teeth, the roof of the mouth with the cold ice cream lump on it, and the trigeminal nerve's
three branches (forehead, cheek, jaw) on one side of the face."""
import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import character as C
import claude_sculpt_kit as K
import head_set as HS
import mouth_set as MS
import nerve_set as NS
import vfx_kit as V

H = V.hex_lin


def build(nerves=True, side=1):
    """side: +1 puts the nerve on the character's left (+X) side of the face."""
    hero = C.build_hero()
    body, rig = hero["body"], hero["rig"]
    for p in hero["parts"]:
        if any(k in p.name for k in ("short", "eyebrow", "eyelash", "casualsuit", "shoes")):
            p.hide_render = p.hide_viewport = True
    skin = body.data.materials[0]
    MS.add_xray(skin, rim="#5B6BFF", strength=1.6, tint="#E8ECFF", rim_start=0.5)
    MS.control(skin, "XRay").default_value = 1.0
    for p in hero["parts"]:
        if "teeth" in p.name:
            for m in p.data.materials:
                MS.add_xray(m, rim="#F4F8FF", strength=2.4, tint="#F4F6FF", rim_start=0.4)
                MS.control(m, "XRay").default_value = 1.0
    m = HS.head_measure(hero)
    eyes = m["eyes"]
    col = V.collection("XRAY_INSIDE")
    brain = HS.import_brain(col)
    HS.place_brain(brain, hero, eyes.z + 0.05, fill=0.85)
    bmat = HS.brain_material()
    V.assign(brain, bmat)
    bmat.node_tree.nodes["Glow"].outputs[0].default_value = 0.15
    palate, lump = mouth_roof(hero, col)
    out = {"hero": hero, "brain": brain, "brain_mat": bmat, "eyes": eyes, "palate": palate, "lump": lump,
           "measure": m}
    if nerves:
        out["nerves"] = trigeminal(hero, eyes, side, col)
    return out


def mouth_roof(hero, col):
    """Pink palate dome over the upper teeth and the cold white ice cream lump under it."""
    teeth = next(p for p in hero["parts"] if "teeth" in p.name)
    P = np.array([tuple(teeth.matrix_world @ v.co) for v in teeth.data.vertices])
    upper = P[P[:, 2] > np.median(P[:, 2])]
    c = upper.mean(0)
    top = upper[:, 2].max()
    w, d = np.ptp(upper[:, 0]), np.ptp(upper[:, 1])
    pal = K.ellipsoid("Palate_Xray", (c[0], c[1] + d * 0.08, top), (w * 0.42, d * 0.62, 0.014), segments=48, col=col)
    Q = K.co(pal)
    Q[:, 2] = np.maximum(Q[:, 2], top)                            # keep the dome, flatten the underside
    K.set_co(pal, Q)
    V.assign(pal, V.principled("Palate_Pink", H("#E77C8C"), rough=0.3, sss=0.4, sss_radius=(1, 0.35, 0.3),
                               sss_scale=0.003, coat=0.4, emission=H("#FF6F86"), emission_strength=0.6))
    lump = K.ellipsoid("IceCream_Xray", (c[0], c[1] + d * 0.1, top - 0.007), (w * 0.28, d * 0.3, 0.009),
                       segments=32, col=col)
    K.skin(lump, 0.006, 0.0012, octaves=3, seed=5)
    V.assign(lump, V.principled("IceCream_Cold", H("#DFF4FF"), rough=0.35, emission=H("#4FC3FF"),
                                emission_strength=3.0))                 # cold cyan glow: not lost among the teeth
    return pal, lump


def _face_point(body, p, depth=0.0035):
    """Snap a point onto the face (ray from the front) and sink it just under the skin."""
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(body, dg)
    inv = body.matrix_world.inverted()
    loc, nrm, _, _ = tree.ray_cast(inv @ (Vector(p) + Vector((0, -0.3, 0))), Vector((0, 1, 0)))
    if loc is None:
        return Vector(p)
    loc, nrm = body.matrix_world @ loc, (body.matrix_world.to_3x3() @ nrm).normalized()
    return loc - nrm * depth


def trigeminal(hero, eyes, side, col):
    """The three branches from the ganglion in front of the ear. Returns {"V1", "V2", "V3"}
    curve objects; V1 (forehead) has its own material so its signal can run alone."""
    body = hero["body"]
    s = side
    e = eyes + Vector((s * 0.033, 0, 0))                          # the eye on that side
    G = eyes + Vector((s * 0.05, 0.062, -0.032))                  # trigeminal ganglion, deep in front of the ear
    fp = lambda dx, dz: _face_point(body, eyes + Vector((s * dx, 0, dz)))
    paths = {
        "V1": [G, eyes + Vector((s * 0.045, 0.03, 0.0)), e + Vector((s * 0.002, 0.004, 0.017)), fp(0.03, 0.022),
               fp(0.032, 0.045), fp(0.028, 0.075)],
        "V2": [G, eyes + Vector((s * 0.047, 0.035, -0.022)), e + Vector((0, 0.008, -0.022)), fp(0.026, -0.026),
               fp(0.035, -0.045)],
        "V3": [G, eyes + Vector((s * 0.058, 0.045, -0.07)), eyes + Vector((s * 0.05, 0.02, -0.105)), fp(0.03, -0.112),
               fp(0.012, -0.118)],
    }
    twigs = {"V1": [(3, (0.012, 0.07)), (4, (0.05, 0.068)), (4, (0.016, 0.06))],
             "V2": [(3, (0.012, -0.035)), (3, (0.045, -0.03))],
             "V3": [(3, (0.042, -0.118)), (3, (0.022, -0.1))]}
    out = {}
    for name, ctrl in paths.items():
        mat = NS.signal_nerve_material(f"Trigeminal_{name}")
        pts = K.path_spline([tuple(p) for p in ctrl], 60)
        ob = V.glow_curve(f"Trigeminal_{name}", pts, 0.0016, mat, col=col, taper=0.45)
        for k, (dx, dz) in twigs[name]:
            a = Vector(ctrl[k])
            b = fp(dx, dz)
            tw = K.path_spline([tuple(a), tuple((a + b) / 2 + Vector((0, -0.004, 0.004))), tuple(b)], 20)
            t = V.glow_curve(f"Trigeminal_{name}_twig", tw, 0.0009, mat, col=col, taper=0.3)
            t.parent = ob
        out[name] = ob
    return out
