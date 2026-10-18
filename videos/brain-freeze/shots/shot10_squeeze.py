"""SHOT 10 (16.8-18.8 s, 60 frames @30fps) - "squeeze tight to hold in heat,"
X-ray close-up of the vessels along the side of the palate: they constrict to under half
their width and fade from red to a dim cold blue, while warm orange sparks stay trapped
inside them. Nearly static camera with a slight push.
"""
import os
import sys

ROOT = os.environ.get("BRAIN_FREEZE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "shots"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy
from mathutils import Vector

import mouth_set as MS
import park_set as PS
import shot09_xray_vessels as S09
import vessels as VS
import vfx_kit as V

FPS, SECONDS = 30, 2.0
SQUEEZE = (8, 34)


def build():
    parts, ves, brain = S09.build_xray_set(SECONDS, xray=1.0)
    mat = ves["mat"]
    MS.control(mat, "Glow").default_value = 0.45
    VS.thickness(ves["levels"], [(SQUEEZE[0], 1.0), (SQUEEZE[1], 0.45)])
    V.animate_socket(MS.control(mat, "Cold"), [(SQUEEZE[0], 0.0), (SQUEEZE[1], 1.0)])
    V.animate_socket(MS.control(mat, "Glow"), [(SQUEEZE[0], 0.45), (SQUEEZE[1], 0.25)])
    V.animate_socket(MS.control(mat, "Clear"), [(SQUEEZE[0], 0.0), (SQUEEZE[1], 1.0)])
    # trapped heat: sparks on the lower half of the artery in frame, small enough to sit inside
    # the squeezed tube, bright enough to glow through its cleared wall
    arteries = [p[:22] for p, r, lv in ves["paths"] if lv == 0][:1]
    VS.sparks(arteries, count=16, radius=0.00016, start=1, end=60, drift=0.04)
    bpy.data.materials["Spark_Warm"].node_tree.nodes["Emission"].inputs["Strength"].default_value = 20
    # the sky dims as the vessels go cold, so the dim blue vessels stay readable against it
    V.animate_socket(PS.camera_sky(), [(SQUEEZE[0], 1.1), (SQUEEZE[1], 0.4)])

    brain.hide_render = brain.hide_viewport = True                 # close-up: vessels against the sky
    parts["lump"].hide_render = True                               # a blurred grey arc this close; clutter
    r = V.camera_rig("Cam_Shot10", lens=24, fstop=40)
    r["cam"].data.clip_start = 0.0005
    V.cam_keys(r, [(1, Vector((0.0075, -0.0125, 0.0025)), Vector((0.0115, 0.0005, 0.0135)), 24),
                   (60, Vector((0.00864, -0.00939, 0.0050)), Vector((0.0118, 0.001, 0.0138)), 24)])
    V.handheld(r, amount=0.0001, aim_amount=0.00012)
    V.compositor(glow=0.6, threshold=0.9, dispersion=0.006)
    S09.preview_settings()
    return {"mouth": parts, "vessels": ves, "brain": brain}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
