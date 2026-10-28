"""On-screen text in the house style: narrator lines, whispers, counters and title cards."""
from __future__ import annotations

from .core import H, W, noise1, out_back, smooth
from .draw import text, text_width


def envelope(T, t0, t1, fade_in=0.45, fade_out=0.45):
    if T < t0 or T > t1:
        return 0.0
    return smooth(t0, t0 + fade_in, T) * (1 - smooth(t1 - fade_out, t1, T))


def narrator(c, T, s, t0, t1, y=None, size=66, x=None, color='white', name='PatrickHand', rise=14):
    """Calm narrator caption that fades in with a small rise."""
    a = envelope(T, t0, t1)
    if a <= 0:
        return
    y = H * 0.84 if y is None else y
    x = W / 2 if x is None else x
    dy = (1 - smooth(t0, t0 + 0.8, T)) * rise
    text(c, s, x, y + dy, size, name, color, a, glow='#FFFFFF', glow_a=0.12, glow_r=18, shadow=0.75)


def whisper(c, T, s, t0, t1, x, y, size=54, color='#FF8A7E', seed=0, align='center', pop=True):
    """The shadow's lowercase whisper: pops in, trembles, glows red."""
    a = envelope(T, t0, t1, 0.12, 0.35)
    if a <= 0:
        return
    jx = noise1(T * 14, seed) * 2.2
    jy = noise1(T * 14, seed + 9) * 2.2
    scale = out_back(min(1.0, (T - t0) / 0.25)) if pop else 1.0
    c.save()
    c.translate(x + jx, y + jy)
    c.scale(scale, scale)
    text(c, s, 0, 0, size, 'PatrickHand', color, a, align=align, glow='red', glow_a=0.75, glow_r=16,
         outline='#160404', outline_w=7)
    c.restore()


def counter(c, T, label, t0, t1, x=72, y=112, size=54):
    """Top-left day/age counter, like the reference film."""
    a = envelope(T, t0, t1, 0.12, 0.2)
    if a <= 0:
        return
    text(c, label, x, y, size, 'Inter-Bold', 'white', a, align='left', tracking=2.0, shadow=0.7)


def title(c, T, s, t0, t1, y, size=120, name='PatrickHand', color='white', underline=None, ul_color='red'):
    a = envelope(T, t0, t1, 0.8, 0.6)
    if a <= 0:
        return
    text(c, s, W / 2, y, size, name, color, a)
    if underline is not None:
        from .draw import paint
        u = smooth(underline, underline + 0.9, T)
        w = text_width(s, name, size)
        x0 = W / 2 - w / 2
        c.drawLine(x0, y + 26, x0 + w * u, y + 26 + 4 * u, paint(ul_color, a, stroke=8))
        c.drawLine(x0, y + 26, x0 + w * u, y + 26 + 4 * u, paint(ul_color, a * 0.5, stroke=18, blur=10, blend='add'))
