"""SHOT 06 (8.4-10.6 s, 66 frames @30fps) - "like your brain is freezing solid."
His brain-reveal device: the top of the head is cut away (glowing cut edge) on the wincing
protagonist; frost races over the brain from the front and ice crystals sprout across it.
Slow orbit from above.
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

import character as C
import claude_sculpt_kit as K
import head_set as HS
import shot03_perfect as S03
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 2.2
N = 66


def build_frozen_head(freeze=(6, 52), crystals=True, frozen=False, face=None):
    """Shared by shots 06, 17, 18, 19: hero on the bench, head cut open, brain freezing.
    frozen=True starts fully frozen (no growth); crystals=False keeps a healthy brain."""
    hero, park, ice, cup = S03.hero_on_bench()
    C.face(hero["body"], HS.PAIN if face is None else face)
    cut = HS.cutaway_scene(hero)
    mat = cut["brain_mat"]
    frost = mat.node_tree.nodes["Frost"].outputs[0]
    clusters = []
    if frozen:
        frost.default_value = 0.2
        clusters = HS.crystal_clusters(cut["brain"], -20, -10, cut["frost_origin"]) if crystals else []
    elif crystals:
        V.animate_socket(frost, [(1, 0.0), (freeze[0], 0.0), (freeze[1], 0.2)])
        clusters = HS.crystal_clusters(cut["brain"], freeze[0] + 4, freeze[1] + 6, cut["frost_origin"])
    HS.bake_static(hero)                                          # he holds still: no per-frame cut/pose work
    cut["rim"] = HS.rim_ring(hero["body"], cut["cutter"])
    return hero, cut, clusters


def build():
    V.start_fresh()
    V.setup_shot(SECONDS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hero, cut, clusters = build_frozen_head()
    top = cut["top"]
    S03.sun_rim_lights(top)
    cold = bpy.data.lights.new("Cold_Top_lgt", "AREA")
    cold.energy, cold.size, cold.color = 40, 0.5, (0.6, 0.8, 1.0)
    ob = V.link(bpy.data.objects.new("Cold_Top_lgt", cold), V.collection("LIGHTS"))
    ob.location = top + Vector((0.1, -0.2, 0.6))
    K._aim(ob, top)
    r = V.camera_rig("Cam_Shot06", lens=45, fstop=4.0)
    aim = top + Vector((0, -0.01, -0.035))
    V.cam_keys(r, [(1, aim + K.look_dir(-36, 20) * 0.66, aim, 45), (N, aim + K.look_dir(-12, 26) * 0.58, aim, 45)])
    V.handheld(r, amount=0.0015, aim_amount=0.001)
    V.compositor(glow=0.4, threshold=1.0, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(bounces=(4, 2, 2, 6, 8))
    return {"hero": hero}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
