"""SHOT 17 (26.0-28.0 s, 60 frames @30fps) - "But in rare cases, it can even"
X-ray of her neck: her windpipe swells in pulses, its wall stretching thin, the trapped air
churning inside it; one weak spot on its front glows red, brighter and brighter, and fine red
cracks creep out from it. Slow orbit, 50 mm.

Run in a NEW Blender file:  blender -b -P shot17_weak_spot.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import math
import os
import sys

ROOT = os.environ.get("SNEEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
import numpy as np
from mathutils import Matrix, Vector

import air_fx as AF
import claude_sculpt_kit as K
import hold_in as HOLD
import sky_set as SKY
import vfx_kit as V
import xray_set as XS

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
LENS = 50
TUBE_R = 0.0085                                   # airways.windpipe radius
SWELL = [(1, 0.15), (10, 0.45), (14, 0.3), (24, 0.65), (28, 0.5), (38, 0.85), (42, 0.72), (52, 1.0), (60, 0.95)]
GLOW = [(1, 0.6), (12, 1.8), (16, 1.2), (26, 3.0), (30, 2.2), (40, 4.8), (44, 3.8), (54, 7.5), (60, 7.0)]
SPOT_AT = (0.62, -2.0)                            # (fraction up the windpipe, angle round it): facing the camera's orbit


def weak_spot(ch, s_c, th_c, col, rng, swell_max):
    """A red glowing patch on the windpipe's front and fine red cracks creeping from it. All
    hang from an empty on the windpipe's axis that scales out with the swelling wall."""
    i = int(np.argmin(np.abs(ch.s - s_c)))
    centre, T = Vector(ch.P[i]), Vector(ch.T[i])
    pivot = V.link(bpy.data.objects.new("Weak_Spot_Pivot", None), col)
    pivot.location = centre
    pivot.rotation_mode = "QUATERNION"
    pivot.rotation_quaternion = T.to_track_quat("Z", "Y")          # local Z along the windpipe
    bpy.context.view_layer.update()
    Mi = pivot.matrix_world.inverted()
    lift = 1.04

    def on_wall(s, th, k=lift):
        return Mi @ ch.at(s, th, k)

    red = V.emission("Weak_Spot_Glow", V.hex_lin("#FF2416"), 1.0)
    nt = red.node_tree                                             # soft round glow: fades to its edge
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 0.0062,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(grad.outputs["Fac"], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(nt.nodes["Emission"].outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs[0])
    V._blended(red)
    # the patch: a small grid on the wall round the spot
    pts, faces, n = [], [], 13
    for a in range(n):
        for b in range(n):
            ds = (a / (n - 1) - 0.5) * 0.0125
            dth = (b / (n - 1) - 0.5) * 0.0125 / TUBE_R
            pts.append(on_wall(s_c + ds, th_c + dth))
    for a in range(n - 1):
        for b in range(n - 1):
            faces.append((a * n + b, a * n + b + 1, (a + 1) * n + b + 1, (a + 1) * n + b))
    me = bpy.data.meshes.new("Weak_Spot")
    me.from_pydata([tuple(p) for p in pts], [], faces)
    patch = V.link(bpy.data.objects.new("Weak_Spot", me), col)
    patch.parent = pivot
    c_local = on_wall(s_c, th_c)
    me.transform(Matrix.Translation(-c_local))                    # origin at the spot: the glow is round about it
    patch.location = c_local
    V.assign(patch, red)
    # cracks: jagged red lines creeping out over the wall
    crack_mat = V.emission("Weak_Spot_Crack", V.hex_lin("#FF3A20"), 3.0)
    cracks = []
    for k in range(11):
        a = rng.uniform(0, 2 * math.pi)
        s, th, path = s_c, th_c, []
        for _ in range(int(rng.integers(6, 11))):
            path.append(on_wall(s, th, lift + 0.004))
            a += rng.normal(0, 0.5)
            step = rng.uniform(0.0014, 0.0026)
            s, th = s + math.cos(a) * step, th + math.sin(a) * step / TUBE_R
        cu = bpy.data.curves.new(f"Weak_Spot_Crack_{k}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.00012
        cu.bevel_resolution = 1
        sp = cu.splines.new("POLY")
        sp.points.add(len(path) - 1)
        for j, p in enumerate(path):
            sp.points[j].co = (*p, 1.0)
        f0 = int(rng.uniform(14, 44))
        cu.bevel_factor_mapping_end = "SPLINE"
        cu.bevel_factor_end = 0.0
        cu.keyframe_insert("bevel_factor_end", frame=f0)
        cu.bevel_factor_end = 1.0
        cu.keyframe_insert("bevel_factor_end", frame=f0 + int(rng.uniform(8, 16)))
        V.ease_id(cu)
        ob = V.link(bpy.data.objects.new(cu.name, cu), col)
        ob.parent = pivot
        V.assign(ob, crack_mat)
        cracks.append(ob)
    return pivot, patch, red, crack_mat


def build():
    V.start_fresh()
    lo, hi = HOLD.SHOTS["17"]
    n = hi - lo + 1
    V.setup_shot(n / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    if PREVIEW:
        V.fast_preview(samples=24)
    st = XS.stage("17")
    aw = st["aw"]
    P = aw["paths"]
    col = V.collection("FX")

    # the windpipe's wall swells in pulses (the rings hold), the air churning inside it
    tube = aw["windpipe"]
    disp = tube.modifiers.new("Swell", "DISPLACE")
    disp.direction, disp.mid_level = "NORMAL", 0.0
    swell_max = 0.0016
    for f, a in SWELL:
        disp.strength = swell_max * a
        tube.keyframe_insert('modifiers["Swell"].strength', frame=f)
    V.ease_id(tube)
    AF.swirl(aw, n, col, aw["roots"]["chest"], np.random.default_rng(1717), count=40, core=4,
             routes=[P["windpipe"] + P["larynx"]], name="Air_Neck")

    # the weak spot, glowing redder; its cracks creeping out
    ch = AF.Channel(P["windpipe"] + P["larynx"], None, fallback=TUBE_R)
    s_c = SPOT_AT[0] * ch.length
    pivot, patch, red, crack_mat = weak_spot(ch, s_c, SPOT_AT[1], col, np.random.default_rng(171), swell_max)
    k_of = lambda a: 1.0 + swell_max * a / TUBE_R
    for f, a in SWELL:                                           # it rides out with the swelling wall
        pivot.scale = (k_of(a), k_of(a), 1.0)
        pivot.keyframe_insert("scale", frame=f)
    V.ease_id(pivot)
    V.animate_socket(red.node_tree.nodes["Emission"].inputs["Strength"], GLOW)
    V.animate_socket(crack_mat.node_tree.nodes["Emission"].inputs["Strength"], [(1, 2.0), (40, 3.5), (n, 5.0)])
    pivot.parent = aw["roots"]["chest"]
    spot = ch.at(s_c, SPOT_AT[1], 1.0)

    # camera: a slow orbit round her neck, on the weak spot
    r = V.camera_rig("Cam_Shot17", lens=LENS, fstop=8)
    keys = []
    for f in (1, n // 2, n):
        u = (f - 1) / (n - 1)
        keys.append((f, spot + K.look_dir(-42 + 30 * u, 4 + 2 * u) * (0.23 - 0.04 * u), spot, None))
    V.cam_keys(r, keys)
    V.handheld(r, amount=0.0004, aim_amount=0.0003)
    c0 = keys[0][1]
    SKY.studio(c0, spot, LENS)
    SKY.lights(spot, c0, SKY.view_dir(c0, spot, LENS), scale=0.35)
    V.compositor(glow=0.45, threshold=1.0, dispersion=0.006)
    XS.finish()
    return st


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
