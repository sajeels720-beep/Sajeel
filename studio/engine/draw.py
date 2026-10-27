"""Thin helpers over skia-python: colours, paints, shapes, glow, light and text."""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import skia

FONT_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'fonts'

# Palette shared by every film in this style.
PAL = {
    'bg': '#0A0A0D',
    'floor': '#141418',
    'floor_line': '#2B2B33',
    'outline': '#1B1B20',
    'skin': '#EDE6D9',
    'skin_shade': '#D6CDBD',
    'hoodie': '#36586C',
    'pants': '#2B2E36',
    'shoes': '#1C1D22',
    'beanie': '#F2A33A',
    'red': '#FF3B36',
    'red_core': '#FF7466',
    'warm': '#FFC35E',
    'warm_deep': '#FF9A3C',
    'moon': '#9DB7FF',
    'white': '#F4F1EA',
    'wood': '#C98A4B',
    'wood_dark': '#8C5A2B',
    'grey': '#8D929B',
}


def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def col(c, a=1.0):
    """Colour from '#rrggbb' or (r, g, b) with alpha 0..1 -> skia int colour."""
    r, g, b = hex2rgb(PAL.get(c, c)) if isinstance(c, str) else c
    return skia.Color(int(r), int(g), int(b), int(max(0, min(1, a)) * 255))


def mixc(c1, c2, u):
    a = hex2rgb(PAL.get(c1, c1)) if isinstance(c1, str) else c1
    b = hex2rgb(PAL.get(c2, c2)) if isinstance(c2, str) else c2
    return tuple(int(x + (y - x) * u) for x, y in zip(a, b))


def paint(c='white', a=1.0, stroke=None, blur=0.0, blend=None, cap='round', join='round', shader=None):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap({'round': skia.Paint.kRound_Cap, 'butt': skia.Paint.kButt_Cap,
                        'square': skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin({'round': skia.Paint.kRound_Join, 'miter': skia.Paint.kMiter_Join,
                         'bevel': skia.Paint.kBevel_Join}[join])
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend == 'add':
        p.setBlendMode(skia.BlendMode.kPlus)
    elif blend == 'screen':
        p.setBlendMode(skia.BlendMode.kScreen)
    elif blend == 'multiply':
        p.setBlendMode(skia.BlendMode.kMultiply)
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(a)
    return p


# --- paths -------------------------------------------------------------------

def poly(points, closed=False):
    p = skia.Path()
    if not points:
        return p
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    if closed:
        p.close()
    return p


def smooth_path(points, closed=False, tension=0.5):
    """Catmull-Rom spline through points as cubic Beziers."""
    p = skia.Path()
    n = len(points)
    if n < 2:
        return p
    pts = list(points)
    if closed:
        pts = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        pts = [pts[0]] + pts + [pts[-1]]
    p.moveTo(*pts[1])
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def oval(cx, cy, rx, ry):
    return skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)


# --- outlined shapes in the house style -------------------------------------

OUTLINE_W = 5.0


def fill_outline(c, path, fill, outline='outline', ow=OUTLINE_W, a=1.0):
    c.drawPath(path, paint(fill, a))
    if ow:
        c.drawPath(path, paint(outline, a, stroke=ow))


def limb(c, pts, fill, width, outline='outline', ow=OUTLINE_W, a=1.0):
    """A thick rounded limb with a dark outline (outline stroke under a fill stroke)."""
    path = poly(pts)
    if ow:
        c.drawPath(path, paint(outline, a, stroke=width + 2 * ow))
    c.drawPath(path, paint(fill, a, stroke=width))


def circle(c, x, y, r, fill, outline='outline', ow=OUTLINE_W, a=1.0):
    c.drawCircle(x, y, r, paint(fill, a))
    if ow:
        c.drawCircle(x, y, r, paint(outline, a, stroke=ow))


# --- light and glow ----------------------------------------------------------

def glow_path(c, path, color, radius=14, a=1.0, stroke=None):
    c.drawPath(path, paint(color, a, stroke=stroke, blur=radius, blend='add'))


def radial(cx, cy, r, color, a=1.0, falloff=(0.0, 1.0)):
    rgb = hex2rgb(PAL.get(color, color)) if isinstance(color, str) else color
    return skia.GradientShader.MakeRadial(
        center=(cx, cy), radius=max(r, 1e-3),
        colors=[skia.Color(*rgb, int(255 * a)), skia.Color(*rgb, 0)],
        positions=list(falloff))


def light_pool(c, cx, cy, rx, ry, color='warm', a=0.5):
    """Soft elliptical pool of additive light (floor pools, lamp glows)."""
    c.save()
    c.translate(cx, cy)
    c.scale(1.0, ry / max(rx, 1e-3))
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial(0, 0, rx, color, a))
    p.setBlendMode(skia.BlendMode.kPlus)
    c.drawCircle(0, 0, rx, p)
    c.restore()


def cone(c, top, half_top, bottom_y, half_bottom, color='warm', a=0.25, soft=22):
    """Spotlight cone from a point/narrow top down to a wide bottom."""
    x, y = top
    path = poly([(x - half_top, y), (x + half_top, y), (x + half_bottom, bottom_y), (x - half_bottom, bottom_y)], True)
    rgb = hex2rgb(PAL.get(color, color)) if isinstance(color, str) else color
    shader = skia.GradientShader.MakeLinear(
        points=[(x, y), (x, bottom_y)],
        colors=[skia.Color(*rgb, int(255 * a)), skia.Color(*rgb, int(255 * a * 0.35))])
    p = skia.Paint(AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, soft))
    p.setShader(shader)
    p.setBlendMode(skia.BlendMode.kPlus)
    c.drawPath(path, p)


def vignette(c, w, h, strength=0.75, inner=0.45):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        center=(w / 2, h / 2), radius=math.hypot(w, h) / 2,
        colors=[skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, int(255 * strength))],
        positions=[0.0, inner, 1.0]))
    c.drawRect(skia.Rect.MakeWH(w, h), p)


def fade(c, w, h, amount, color=(0, 0, 0)):
    if amount > 0:
        c.drawRect(skia.Rect.MakeWH(w, h), paint(color, amount))


# --- text ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def typeface(name):
    """Bundled font by file stem, or a system family; a '-Bold' suffix picks the bold face."""
    path = FONT_DIR / f'{name}.ttf'
    if path.exists():
        return skia.Typeface.MakeFromFile(str(path))
    if name.endswith('-Bold'):
        return skia.Typeface(name[:-5], skia.FontStyle.Bold())
    return skia.Typeface(name)


@lru_cache(maxsize=256)
def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def text_width(s, name, size):
    return font(name, size).measureText(s)


def text(c, s, x, y, size, name='PatrickHand', color='white', a=1.0, align='center',
         glow=None, glow_a=0.6, glow_r=16, outline=None, outline_w=0, tracking=0.0, shadow=0.0):
    """Draw a single line. y is the baseline. glow: colour for an additive halo;
    shadow: opacity of a soft dark backing that keeps text readable on busy backgrounds."""
    if a <= 0 or not s:
        return
    f = font(name, size)
    if tracking:
        widths = [f.measureText(ch) + tracking for ch in s]
        total = sum(widths) - tracking
    else:
        total = f.measureText(s)
    x0 = x - total / 2 if align == 'center' else x - total if align == 'right' else x

    def draw_with(p):
        if tracking:
            cx = x0
            for ch, wch in zip(s, widths):
                c.drawString(ch, cx, y, f, p)
                cx += wch
        else:
            c.drawString(s, x0, y, f, p)

    if shadow:
        draw_with(paint('#000000', a * shadow, stroke=size * 0.22, blur=size * 0.18))
    if glow:
        draw_with(paint(glow, a * glow_a, blur=glow_r, blend='add'))
    if outline and outline_w:
        draw_with(paint(outline, a, stroke=outline_w))
    draw_with(paint(color, a))
