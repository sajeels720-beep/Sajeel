"""SHOT 09 (14.8-16.8 s, 60 frames @30fps) - "the blood vessels in your head"
X-ray mode: the frosted roof of the mouth turns into see-through blue glass and a glowing
red vessel network draws itself across the palate and climbs to the front of the brain.
Camera tilts up from the palate to the brain.
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
import shot08_palate_frost as S08
import vessels as VS
import vfx_kit as V

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS, SECONDS = 30, 2.0


def xray_mats():
    return [m for m in bpy.data.materials if m.node_tree and "XRay" in m.node_tree.nodes]


def xray_all(value=None, keys=None):
    """Set (or keyframe) the x-ray control on every material that has one."""
    for m in xray_mats():
        if keys:
            V.animate_socket(MS.control(m, "XRay"), keys)
        else:
            MS.control(m, "XRay").default_value = value


def clear_shell(mat):
    """Turn a material's x-ray shell fully clear (no rim, no tint): the x-rayed palate's
    folds would otherwise draw stray violet strokes across the vessels and brain."""
    nt = mat.node_tree
    for n in nt.nodes:
        if n.bl_idname == "ShaderNodeBsdfTransparent":
            n.inputs["Color"].default_value = (1, 1, 1, 1)
        elif n.bl_idname == "ShaderNodeValToRGB" and n.inputs[0].links \
                and n.inputs[0].links[0].from_node.bl_idname == "ShaderNodeLayerWeight":
            n.color_ramp.elements[1].color = (0, 0, 0, 1)


def build_xray_set(seconds, xray=1.0, turn=0.0):
    """Shared by shots 09-11: frosted mouth (end of shot 08), vessel network, brain,
    the park sky showing through the x-ray (turn spins it), mouth lights."""
    V.start_fresh()
    V.setup_shot(seconds, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=32 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    PS.world(turn)
    parts = MS.build()
    muc = parts["mucosa"]
    MS.control(muc, "FrostRadius").default_value = 0.024
    MS.control(muc, "FrontGlow").default_value = 0.45
    xray_all(xray)
    MS.control(parts["lump"].active_material, "XRay").default_value = 0.93 * xray   # milky ice, still there
    for m in (muc, parts["cheek_mat"]):
        clear_shell(m)
    parts["cavity"].modifiers["Solidify"].use_rim = False         # its cut edge glowed as a saw-tooth
    parts["lump"].scale = (1.012, 1.012, 0.975)
    ves = VS.build()
    brain = VS.brain_underside()
    S08.mouth_lights(MS.CONTACT + Vector((0, 0, -0.004)))
    return parts, ves, brain


def preview_settings():
    if PREVIEW:
        V.fast_preview(bounces=(6, 2, 2, 4, 16))


def build():
    parts, ves, brain = build_xray_set(SECONDS, xray=0.0)
    muc = parts["mucosa"]
    xray_all(keys=[(1, 0.0), (14, 1.0)])
    V.animate_socket(MS.control(parts["lump"].active_material, "XRay"), [(1, 0.0), (14, 0.93)])
    V.animate_socket(MS.control(muc, "FrontGlow"), [(1, 0.45), (8, 0.0)])
    VS.grow(ves["levels"], [(2, 14), (10, 24), (20, 36), (31, 48)])     # each level starts as its parent arrives
    V.animate_socket(MS.control(ves["mat"], "Glow"), [(1, 0.15), (20, 0.4), (60, 0.45)])

    r = V.camera_rig("Cam_Shot09", lens=16, fstop=40)
    r["cam"].data.clip_start = 0.0005
    V.cam_keys(r, [(1, Vector((0.0025, -0.0205, -0.0015)), Vector((0.0, -0.001, 0.0135)), 18),   # = shot 08's end
                   (60, Vector((0.004, -0.024, -0.005)), Vector((0.0, -0.004, 0.052)), 16)])
    V.handheld(r, amount=0.00015, aim_amount=0.0002)
    V.compositor(glow=0.6, threshold=0.9, dispersion=0.006)
    preview_settings()
    return {"mouth": parts, "vessels": ves, "brain": brain}


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
