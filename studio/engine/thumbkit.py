"""Helpers for thumbnails in the house style (see studio/THUMBNAILS.md): brush lettering, soft light, depth."""
from __future__ import annotations

from functools import lru_cache

import skia

from .core import H, W
from .draw import col, paint, text


@lru_cache(maxsize=4)
def _noise_image(freq=0.08, octaves=2, seed=3.0):
    surface = skia.Surface(W, H)
    p = skia.Paint()
    p.setShader(skia.PerlinNoiseShader.MakeTurbulence(freq, freq, octaves, seed))
    surface.getCanvas().drawPaint(p)
    return surface.makeImageSnapshot()


def rough(c, amount=5.0):
    """Begin a layer whose edges get a dry-brush roughness when restored (call c.restore() after drawing)."""
    disp = skia.ImageFilters.DisplacementMap(skia.ColorChannel.kR, skia.ColorChannel.kG, amount,
                                             skia.ImageFilters.Image(_noise_image()), skia.ImageFilters.Offset(0, 0))
    c.saveLayer(None, skia.Paint(ImageFilter=disp))


def brush_title(c, lines, x, y, size, gap=1.0, name='LuckiestGuy', color='white', roughness=5.0, align='left'):
    """House lettering: bold white capitals, thick black outline, a hard drop shadow, rough brush edges.
    y is the first line's baseline; returns the last baseline."""
    rough(c, roughness)
    yy = y
    for line in lines:
        text(c, line, x + size * 0.05, yy + size * 0.07, size, name, '#000000', 0.65, align=align)
        text(c, line, x, yy, size, name, color, align=align, outline='#000000', outline_w=size * 0.12)
        text(c, line, x, yy, size, name, color, align=align)
        yy += size * gap
    c.restore()
    return yy - size * gap


def blurred(c, sigma, fn):
    """Draw fn() out of focus."""
    c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
    fn()
    c.restore()


def shade_head(c, hx, hy, R, light=(0.45, -0.9), rim='#FFF1D6', bounce=None, rim_a=0.5, bounce_a=0.35):
    """Soft spherical shading on a round head: shadow away from the light, a rim toward it, an optional
    coloured bounce light from below."""
    lx, ly = light
    clip = skia.Path()
    clip.addCircle(hx, hy, R - 1)
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    shadow = skia.GradientShader.MakeRadial(
        center=(hx + lx * R * 0.35, hy + ly * R * 0.35), radius=R * 1.45,
        colors=[col('#000000', 0.0), col('#000000', 0.0), col('#14101A', 0.45)], positions=[0.0, 0.55, 1.0])
    c.drawCircle(hx, hy, R, paint('#000000', 1.0, shader=shadow))
    c.drawCircle(hx + lx * R * 0.12, hy + ly * R * 0.12, R * 0.98,
                 paint(rim, rim_a, stroke=R * 0.1, blur=R * 0.05, blend='add'))
    if bounce:
        c.drawCircle(hx - lx * R * 0.05, hy + R * 0.18, R,
                     paint(bounce, bounce_a, stroke=R * 0.16, blur=R * 0.09, blend='add'))
    c.restore()


def haze(c, x0, y0, x1, y1, color='#9DB7FF', a=0.08, blur=60):
    """A soft shaft of light (a quad from the top edge (x0..x1, y0) widening to the floor at y1)."""
    path = skia.Path()
    path.moveTo(x0, y0)
    path.lineTo(x1, y0)
    path.lineTo(x1 + (x1 - x0) * 0.8, y1)
    path.lineTo(x0 - (x1 - x0) * 0.3, y1)
    path.close()
    c.drawPath(path, paint(color, a, blur=blur, blend='add'))


def render(fn, path, size=(1280, 720)):
    """Draw fn(canvas) at 1920x1080 and save a resized PNG."""
    surface = skia.Surface(W, H)
    c = surface.getCanvas()
    c.clear(col('#000000'))
    fn(c)
    img = surface.makeImageSnapshot()
    img.resize(*size, skia.SamplingOptions(skia.CubicResampler.Mitchell())).save(str(path), skia.kPNG)
    return path
