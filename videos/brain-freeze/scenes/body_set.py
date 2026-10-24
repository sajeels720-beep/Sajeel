"""Inside-the-head look for the anatomy close-ups (shots 9-11, 14, 15). What the camera sees
behind the anatomy is warm, dark, out-of-focus tissue instead of the park; the park HDRI
still lights the scene and shows in reflections, so the materials keep their look and the
cut from the mouth (shot 8) stays seamless."""
import math

import bpy
import numpy as np

import claude_sculpt_kit as K
import vfx_kit as V

H = V.hex_lin
TISSUE = ("#1E0508", "#4E0F17", "#8E2F3A")      # deep shadow, flesh, soft lit fold


def backdrop(turn=0.0, scale=2.4, colors=TISSUE):
    """Swap the background the camera sees for soft tissue (call after park_set.world()).
    Returns its strength socket (same one park_set.camera_sky() returns, so shots can
    still dim and brighten it). turn (degrees) picks which part of the pattern sits behind
    the subject."""
    nt = bpy.context.scene.world.node_tree
    mix = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeMixShader")
    bg = mix.inputs[2].links[0].from_node                        # the camera-ray background
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (math.radians(20), 0.0, math.radians(turn))
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    # large soft forms: out-of-focus folds of tissue
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.5
    noise.inputs["Distortion"].default_value = 0.6
    nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.36, (*H(colors[0]), 1)
    els[1].position, els[1].color = 0.70, (*H(colors[2]), 1)
    mid = els.new(0.52)
    mid.color = (*H(colors[1]), 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    # a little lighter from above, darker below, as if lit from the top of the head
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    grad = nt.nodes.new("ShaderNodeMapRange")
    grad.inputs["From Min"].default_value, grad.inputs["From Max"].default_value = -0.9, 0.9
    grad.inputs["To Min"].default_value, grad.inputs["To Max"].default_value = 0.6, 1.25
    nt.links.new(sep.outputs["Z"], grad.inputs["Value"])
    shade = nt.nodes.new("ShaderNodeMix")
    shade.data_type, shade.blend_type = "RGBA", "MULTIPLY"
    shade.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], shade.inputs[6])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        nt.links.new(grad.outputs["Result"], comb.inputs[k])
    nt.links.new(comb.outputs[0], shade.inputs[7])
    nt.links.new(shade.outputs[2], bg.inputs["Color"])
    return bg.inputs["Strength"]


def background_vessels(col, centre, count=6, spread=(6.0, 3.0, 6.0), radius=(0.14, 0.32), seed=11,
                       away=(0.0, 1.0, 0.0), distance=(6.0, 11.0), mat=None):
    """Out-of-focus vessels in the distance (large-scale shots 14, 15): a few thick, curving
    red vessels well beyond the subject (so the depth of field melts them), so it sits inside
    a network of vessels instead of in empty space. Their ends thin out into twigs, like
    real vessels, instead of stopping in a blunt cap. away: direction from the subject
    toward the background."""
    rng = np.random.default_rng(seed)
    centre, away = np.asarray(centre, float), np.asarray(away, float) / np.linalg.norm(away)
    mat = mat or V.principled("Vessel_Far", H("#74101B"), rough=0.35, sss=0.4, sss_radius=(1.0, 0.2, 0.15),
                              sss_scale=0.05, coat=0.4)
    obs = []
    for i in range(count):
        mid = centre + away * rng.uniform(*distance) + rng.uniform(-1, 1, 3) * np.asarray(spread) * 0.5
        dirn = rng.normal(0, 1, 3)
        dirn -= away * dirn.dot(away) * 0.7                       # mostly across the view, not toward it
        dirn /= np.linalg.norm(dirn)
        side = np.cross(dirn, away)
        side /= max(np.linalg.norm(side), 1e-6)
        length, bend, waves = rng.uniform(10.0, 14.0), rng.uniform(0.6, 1.4), rng.uniform(1.2, 2.2)
        pts = [mid + dirn * length * (s - 0.5) + side * math.sin(s * math.pi * waves) * bend for s in np.linspace(0, 1, 13)]
        path = K.path_spline(np.array(pts), 128)
        s = np.linspace(0, 1, len(path))
        ends = np.minimum(1.0, np.minimum(s, 1 - s) / 0.15) ** 0.7  # thins out to a twig at each end
        tube = K.tube(f"Vessel_Far_{i:02d}", path, rng.uniform(*radius) * (1 - 0.4 * s) * (0.12 + 0.88 * ends),
                      segments=32, col=col)
        V.assign(tube, mat)
        obs.append(tube)
    return obs
