"""The x-ray stage shared by shots 06-09 (and the later x-ray shots): her take for the shot,
her skin and clothes turned to x-ray glass, and her airways built inside her, riding on
her head and chest bones.
"""
import bpy

import airways as AW
import heroine as HR
import hold_in as HOLD
import xray_body as XB


def stage(shot, xray=True, ears=False, puffed=1.0):
    """Build her for `shot` with her airways inside. xray: see-through from frame 1 (shot
    06 keys its own scan instead). Returns dict(take, hero, nose, mats, aw, n)."""
    take = HOLD.perform(shot)
    hero = take["hero"]
    bpy.context.scene.frame_set(1)
    nose, _ = HR.surface_point(hero, hero["nose_tip"])
    mats = XB.apply(hero)
    if xray:
        XB.key_sweep(mats, [(1, -1.0, 1.0)])                     # scan line below her feet: all glass
    aw = AW.build(hero, nose, ears=ears, puffed=puffed)
    AW.attach(hero, aw)
    XB.preview_bounces()
    return {"take": take, "hero": hero, "nose": nose, "mats": mats, "aw": aw, "n": take["n"]}


def finish():
    """Last touches after everything is built (Cycles previews need the deep transparency)."""
    XB.preview_bounces()
