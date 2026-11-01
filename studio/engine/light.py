"""Scene lighting for flat 2-D sets: draw the set in plain daylight colours, then multiply it by a light map
(an ambient colour plus soft coloured pools), so one set serves for 2 AM, dawn and noon. Emissive things (a phone
screen, the moon, red eyes) are drawn after the light pass, and rim lights are added on top.
"""
from __future__ import annotations

import skia

from .draw import col, paint

BIG = skia.Rect.MakeLTRB(-4000, -3000, 6000, 4000)


def _visible(c, margin=60.0):
    """What the canvas can currently draw to (local coordinates), a little larger: layer bounds that never
    allocate more than the screen, even when zoomed in."""
    b = c.getLocalClipBounds()
    return skia.Rect.MakeLTRB(b.left() - margin, b.top() - margin, b.right() + margin, b.bottom() + margin)


def begin_light(c, ambient, bounds=None):
    """Open a multiply layer filled with the ambient colour; add pools with pool(), then end_light()."""
    bounds = bounds or _visible(c)
    p = skia.Paint()
    p.setBlendMode(skia.BlendMode.kMultiply)
    c.saveLayer(bounds, p)
    c.drawRect(bounds, paint(ambient))


def pool(c, x, y, rx, ry, color, a=1.0, falloff=(0.0, 1.0), angle=0.0):
    """Additive soft light inside the light map (elliptical radial gradient)."""
    if a <= 0:
        return
    c.save()
    c.translate(x, y)
    if angle:
        c.rotate(angle)
    c.scale(1.0, ry / rx if rx else 1.0)
    sh = skia.GradientShader.MakeRadial(center=(0, 0), radius=rx, colors=[col(color, a), col(color, 0.0)],
                                        positions=list(falloff))
    p = skia.Paint(AntiAlias=True, Shader=sh)
    p.setBlendMode(skia.BlendMode.kPlus)
    c.drawCircle(0, 0, rx, p)
    c.restore()


def beam(c, path, color, a=1.0, blur=30.0):
    """Additive light in a shape (a window's light on the floor, a door crack)."""
    p = paint(color, a, blur=blur)
    p.setBlendMode(skia.BlendMode.kPlus)
    c.drawPath(path, p)


def end_light(c):
    c.restore()


def rim(c, draw_fn, dx, dy, color, a=0.8, blur=2.0, add=True):
    """A rim of light on one edge of whatever draw_fn draws: the shape shifted toward the light, minus the shape."""
    if a <= 0:
        return
    # keep the rim the same few pixels wide on screen however far the camera is zoomed in
    m = c.getTotalMatrix()
    zoom = max(1.0, (m.getScaleX() ** 2 + m.getSkewY() ** 2) ** 0.5)
    dx, dy = dx / zoom * 1.2, dy / zoom * 1.2
    vis = _visible(c)
    lp = skia.Paint()
    if add:
        lp.setBlendMode(skia.BlendMode.kPlus)
    lp.setAlphaf(min(1.0, a))
    if blur >= 4:
        # a soft rim costs a full-screen blur on the CPU (~0.3 s a frame); small values draw a crisp rim instead
        lp.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    c.saveLayer(vis, lp)
    c.save()
    c.translate(dx, dy)
    draw_fn(c)
    c.restore()
    fill = skia.Paint(Color=col(color))
    fill.setBlendMode(skia.BlendMode.kSrcIn)
    c.drawRect(vis, fill)
    cut = skia.Paint()
    cut.setBlendMode(skia.BlendMode.kDstOut)
    c.saveLayer(vis, cut)
    draw_fn(c)
    c.restore()
    c.restore()


def tint(c, draw_fn, color, a=1.0):
    """Draw something as a flat silhouette in one colour (shadows on a wall, a figure in the dark)."""
    vis = _visible(c)
    lp = skia.Paint()
    lp.setAlphaf(min(1.0, a))
    c.saveLayer(vis, lp)
    draw_fn(c)
    fill = skia.Paint(Color=col(color))
    fill.setBlendMode(skia.BlendMode.kSrcIn)
    c.drawRect(vis, fill)
    c.restore()
