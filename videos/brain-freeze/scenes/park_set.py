"""Park set for the character shots (3, 4, 19): the same sunny park HDRI as shot 1, a lawn,
and a classic park bench (wooden slats on black cast-iron frames). Bench seat runs along
X, the sitter faces -Y."""
import math

import bpy
import numpy as np
from mathutils import Vector

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
SUN_AZ = 165                    # same sun direction as shot 1 (behind the subject, slightly right)


def world():
    hdri = V.polyhaven("rooitou_park", "hdris", "2k")
    sun_az, _ = V.sun_azimuth(hdri)
    V.hdri_world(hdri, strength=1.0, rot_deg=270 - sun_az - SUN_AZ, camera_strength=1.1)
    return hdri


def _slat(name, length, width, thick, loc, rot_x, col, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (length, width, thick)
    ob.rotation_euler = (math.radians(rot_x), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width, bev.segments = min(width, thick) * 0.25, 3
    V.link(ob, col)
    V.assign(ob, mat)
    K.shade_smooth(ob)
    return ob


def bench(col, seat_top=0.45, length=1.7, center=(0.0, 0.0)):
    """Wooden slat bench on two cast-iron side frames. Returns the bench objects."""
    cx, cy = center
    wood = V.textured("Bench_Wood", V.polyhaven("wood_table_worn", "textures", "1k"), scale=1.0,
                      tint=(0.95, 0.72, 0.5))
    iron = V.principled("Cast_Iron", H("#1E1F22"), rough=0.45, metal=0.85)
    obs = []
    depth, slat_w, slat_t, gap = 0.42, 0.075, 0.03, 0.012
    for i in range(5):                                            # seat slats
        y = cy - depth / 2 + slat_w / 2 + i * (slat_w + gap)
        obs.append(_slat(f"Bench_Seat_{i}", length, slat_w, slat_t, (cx, y, seat_top - slat_t / 2), 0, col, wood))
    back_tilt = 14
    for i in range(3):                                            # backrest slats
        z = seat_top + 0.12 + i * (slat_w + gap + 0.01)
        y = cy + depth / 2 + 0.02 + (z - seat_top) * math.tan(math.radians(back_tilt))
        obs.append(_slat(f"Bench_Back_{i}", length, slat_t, slat_w, (cx, y, z), -back_tilt, col, wood))
    for side in (-1, 1):                                          # cast-iron side frames
        x = cx + side * (length / 2 - 0.12)
        front_leg = [(x, cy - depth / 2 + 0.03, 0.0), (x, cy - depth / 2 + 0.01, seat_top * 0.5),
                     (x, cy - depth / 2 + 0.04, seat_top - 0.035)]
        back_leg = [(x, cy + depth / 2 - 0.04, 0.0), (x, cy + depth / 2, seat_top * 0.6),
                    (x, cy + depth / 2 + 0.03, seat_top), (x, cy + depth / 2 + 0.03 + 0.38 * math.tan(math.radians(back_tilt)),
                                                         seat_top + 0.38)]
        rail = [(x, cy - depth / 2 + 0.03, seat_top - 0.035), (x, cy + depth / 2 + 0.03, seat_top - 0.035)]
        arm = [(x, cy + depth / 2 + 0.05, seat_top + 0.2), (x, cy, seat_top + 0.23), (x, cy - depth / 2 + 0.02, seat_top + 0.2),
               (x, cy - depth / 2 + 0.03, seat_top - 0.03)]
        for k, pts in enumerate((front_leg, back_leg, rail, arm)):
            path = K.path_spline(pts, 24) if len(pts) > 2 else np.array(pts)
            t = K.tube(f"Bench_Frame_{'L' if side < 0 else 'R'}{k}", path, 0.016 if k != 3 else 0.014, segments=16, col=col)
            V.assign(t, iron)
            obs.append(t)
    return obs


def lawn(col, size=40.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    g = bpy.context.active_object
    g.name = "Lawn_geo"
    V.link(g, col)
    V.assign(g, V.textured("Lawn", V.polyhaven("leafy_grass", "textures", "1k"), scale=size / 2.5,
                           tint=(0.85, 1.0, 0.75)))
    return g


def build(col_name="SET_PARK", seat_top=0.45):
    col = V.collection(col_name)
    world()
    return {"col": col, "bench": bench(col, seat_top=seat_top), "lawn": lawn(col)}
