"""SHOT 05 (6.5-8.0 s, 45 frames @30fps) - "It's your nerves."
X-ray reveal on the same hand, starting on shot 04's last framing: a scan line runs from his
wrist to his fingertips and the skin turns to glass, showing his glowing bones inside, and bright
yellow nerves light up from the wrist into every fingertip; pulses race along them. Crash zoom
onto his fingers on "nerves".

Run in a NEW Blender file:  blender -b -P shot05_nerves.py -a
Env: SHOT_PREVIEW=1 for half-res Cycles previews; default is the final EEVEE setup.
"""
import os
import sys

ROOT = os.environ.get("WRINKLES_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "production"),
          os.path.join(ROOT, "..", "..", "blender-expert"), os.path.join(ROOT, "..", "brain-freeze", "scenes"),
          os.path.join(ROOT, "..", "sneeze", "scenes"), os.path.join(ROOT, "shots")):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy

import hand_set as HS
import shot04_soak as S04
import sky_set as SKY
import vfx_kit as V
import xray_body as XB

PREVIEW = os.environ.get("SHOT_PREVIEW") == "1"
FPS = 30
N = 45
LENS = 50
SCAN = (1, 13)                   # the scan line runs from the wrist to the fingertips
GROW = (8, 22)                   # the nerves light up
ZOOM = (19, 24)                  # crash zoom on "nerves"
PULSES = 22


def build():
    V.start_fresh()
    V.setup_shot(N / FPS, fps=FPS, engine="CYCLES" if PREVIEW else "EEVEE", samples=24 if PREVIEW else 64,
                 scale=50 if PREVIEW else 100)
    hs = HS.build(wrinkled=1.0)
    hero = hs["hero"]
    length = max((hs["ends"][k] - hs["wrist"]).dot(hs["along"]) for k in HS.FINGERS)
    mats = HS.xray(hero, hs["wrist"], hs["along"], length)
    _, bone_mat = HS.bones(hs, sweep=(hs["wrist"], hs["along"], length))      # they show where the line has passed
    HS.key_xray(mats + [bone_mat], [(SCAN[0], -0.45, 1.0), (SCAN[1], 1.15, 1.0)])
    HS.nerves(hs, GROW, PULSES)
    XB.preview_bounces()
    # camera: shot 04's last framing, then a crash zoom onto the fingers and a slow push
    aim, _, c_end = S04.camera_path(hs)
    tips = sum((hs["tips"][k][0] for k in (2, 3, 4)), aim * 0) / 3
    a1 = aim.lerp(tips, 0.55)
    c1 = a1 + (c_end - aim).normalized() * 0.24
    c2 = a1 + (c_end - aim).normalized() * 0.22
    r = V.camera_rig("Cam_Shot05", lens=LENS, fstop=5.6)
    V.cam_keys(r, [(1, c_end, aim, LENS), (ZOOM[0], c_end.lerp(c1, 0.08), aim.lerp(a1, 0.1), LENS),
                   (ZOOM[1], c1, a1, LENS), (N, c2, a1, LENS)])
    V.handheld(r, amount=0.0005, aim_amount=0.0004)
    V.shake(r, ZOOM[1] - 1, ZOOM[1] + 7, strength=0.0016, scale=1.3)
    SKY.studio(c_end, aim, LENS)
    SKY.lights(aim, c_end, SKY.view_dir(c_end, aim, LENS), scale=0.4)
    V.compositor(glow=0.45, threshold=0.9, dispersion=0.006)
    if PREVIEW:
        V.fast_preview(samples=24)
    return hs


if __name__ in ("__main__", "<run_path>", "shot"):
    build()
    V.output_to(os.path.join(ROOT, "renders", os.path.basename(__file__).split("_")[0]))
    out = os.environ.get("SHOT_BLEND")
    if out:
        bpy.ops.wm.save_as_mainfile(filepath=out)
