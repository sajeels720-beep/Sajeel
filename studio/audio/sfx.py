"""Synthesised sound effects. Every function returns float32 audio at dsp.SR (mono unless noted)."""
from __future__ import annotations

import numpy as np

from .dsp import (SR, bp, brown, env_ad, env_exp, glide, hp, lp, norm, pink, pluck, reverb, rng, secs, sine,
                  stereo, sweep_bp, t_axis, white)


def snap(seed=1):
    """A guitar string snapping: bright pluck, a click, a falling twang."""
    s = pluck(659, 0.6, 0.985, 0.9, seed) * env_exp(0.6, 0.12)
    tw = sine(glide(660, 420, 0.35), 0.35) * env_exp(0.35, 0.08) * 0.4
    click = hp(white(0.02, seed), 2500) * env_exp(0.02, 0.003)
    out = np.zeros(secs(0.6), np.float32)
    out += s
    out[: len(tw)] += tw
    out[: len(click)] += click * 0.8
    return norm(out, 0.9)


def thoom(seed=0):
    """Low 'eye opens' pulse with a breathy edge."""
    dur = 1.1
    body = sine(glide(62, 40, dur), dur) * env_exp(dur, 0.35, 0.01)
    breath = bp(pink(dur, seed), 350, 1400) * env_ad(dur, 0.05, 0.9) * 0.25
    return norm(body + breath, 0.8)


def heartbeat(bpm=72, dur=6.0, seed=0):
    out = np.zeros(secs(dur), np.float32)
    beat = 60.0 / bpm
    t = 0.0
    while t < dur - 0.4:
        for off, f, g in ((0.0, 58, 1.0), (0.26, 52, 0.7)):
            th = sine(glide(f * 1.4, f, 0.18), 0.18) * env_exp(0.18, 0.06, 0.004) * g
            i = secs(t + off)
            out[i:i + len(th)] += th[: len(out) - i]
        t += beat
    return lp(norm(out, 0.9), 180)


def tick(tock=False, seed=0):
    dur = 0.06
    ping = sine(1900 if tock else 2400, dur) * env_exp(dur, 0.012)
    click = bp(white(dur, seed), 2000, 7000) * env_exp(dur, 0.002)
    return norm(ping * 0.5 + click, 0.6)


def whoosh(dur=0.7, f0=300, f1=3000, seed=0):
    x = sweep_bp(pink(dur, seed), f0, f1, q=1.5)
    t = t_axis(dur) / dur
    e = np.sin(np.pi * t) ** 2
    return norm(x * e, 0.8)


def shatter(dur=0.5, seed=0, bright=1.0):
    r = rng(seed)
    out = np.zeros(secs(dur), np.float32)
    for k in range(26):
        f = r.uniform(2500, 7500) * bright
        d = r.uniform(0.02, 0.09)
        ping = sine(f, d) * env_exp(d, d / 4)
        i = secs(r.uniform(0, dur * 0.6))
        out[i:i + len(ping)] += ping[: len(out) - i] * r.uniform(0.2, 0.6)
    burst = hp(white(dur, seed), 3000) * env_exp(dur, 0.05)
    return norm(out + burst * 0.5, 0.8)


def glass_crack(seed=2):
    dur = 1.4
    out = np.zeros(secs(dur), np.float32)
    crack = hp(white(0.05, seed), 1500) * env_exp(0.05, 0.006)
    out[: len(crack)] += crack * 1.0
    thump = sine(glide(120, 60, 0.3), 0.3) * env_exp(0.3, 0.08)
    out[: len(thump)] += thump * 0.6
    out += shatter(dur, seed + 1, 0.8) * 0.5
    r = rng(seed)
    for k in range(10):
        i = secs(0.1 + r.uniform(0, 0.9))
        c = bp(white(0.012, seed + k), 1000, 5000) * env_exp(0.012, 0.003)
        out[i:i + len(c)] += c * r.uniform(0.2, 0.5)
    return norm(out, 0.95)


def dust_blow(seed=3):
    dur = 0.9
    x = bp(pink(dur, seed), 400, 2400) * env_ad(dur, 0.08, 0.7)
    return norm(x, 0.7)


def twang(seed=4):
    """A string being tuned up: pluck with a rising pitch."""
    dur = 1.6
    base = pluck(196, dur, 0.997, 0.7, seed)
    # resample with a slowly rising rate
    rate = np.linspace(1.0, 1.035, len(base))
    pos = np.cumsum(rate)
    pos = pos[pos < len(base) - 1]
    y = np.interp(pos, np.arange(len(base)), base).astype(np.float32)
    return norm(y * env_exp(len(y) / SR, 0.7), 0.85)


def beep(freq=1000, n=1, seed=0):
    out = np.zeros(secs(0.18 * n + 0.1), np.float32)
    for k in range(n):
        b = sine(freq, 0.11) * env_ad(0.11, 0.004, 0.02)
        i = secs(k * 0.18)
        out[i:i + len(b)] += b
    return norm(out, 0.5)


def tap(seed=0):
    dur = 0.08
    click = lp(white(dur, seed), 3500) * env_exp(dur, 0.004)
    thump = sine(140, dur) * env_exp(dur, 0.015)
    return norm(click * 0.6 + thump, 0.6)


def bling(seed=0):
    dur = 1.2
    x = (sine(1320, dur) + 0.6 * sine(1980, dur) + 0.3 * sine(2640, dur)) * env_exp(dur, 0.35, 0.003)
    return norm(x, 0.5)


def riser(dur=3.0, seed=5):
    noise = sweep_bp(white(dur, seed), 250, 7000, q=2.5)
    tone = sine(glide(180, 1400, dur), dur) * 0.25
    e = (t_axis(dur) / dur) ** 2.2
    return norm((noise + tone) * e, 0.9)


def drop_boom(seed=6):
    dur = 2.6
    sub = sine(glide(75, 30, dur), dur) * env_exp(dur, 0.7, 0.003)
    hit = lp(white(0.4, seed), 300) * env_exp(0.4, 0.08)
    out = sub.copy()
    out[: len(hit)] += hit * 0.8
    return norm(out, 0.95)


def ding(seed=0):
    dur = 0.9
    x = (sine(1568, dur) + 0.5 * sine(2349, dur)) * env_exp(dur, 0.22, 0.002)
    return norm(x, 0.5)


def coin(seed=7):
    dur = 0.9
    out = np.zeros(secs(dur), np.float32)
    for k, (t0, g) in enumerate(((0.0, 1.0), (0.13, 0.55), (0.22, 0.3), (0.28, 0.15))):
        d = 0.35
        x = sum(sine(f, d) * env_exp(d, d / (3 + j)) for j, f in enumerate((2100, 3420, 5230, 7900)))
        i = secs(t0)
        out[i:i + len(x)] += x[: len(out) - i] * g
    return norm(out, 0.6)


def footstep(wood=False, seed=0):
    dur = 0.12
    if wood:
        x = bp(white(dur, seed), 180, 900) * env_exp(dur, 0.02) + sine(110, dur) * env_exp(dur, 0.03) * 0.6
    else:
        x = lp(white(dur, seed), 900) * env_exp(dur, 0.025) + sine(80, dur) * env_exp(dur, 0.03) * 0.5
    return norm(x, 0.5)


def footsteps(times, wood=False, seed=0):
    dur = max(times) + 0.3
    out = np.zeros((secs(dur), 2), np.float32)
    for k, t0 in enumerate(times):
        s = stereo(footstep(wood, seed + k), pan=0.15 * (1 if k % 2 else -1))
        i = secs(t0)
        out[i:i + len(s)] += s
    return out


def curtain(dur=1.8, seed=8):
    x = lp(pink(dur, seed), 1600) * env_ad(dur, 0.4, 1.0)
    y = lp(pink(dur, seed + 1), 1400) * env_ad(dur, 0.5, 0.9)
    return np.stack([norm(x, 0.6), norm(y, 0.6)], axis=1)


def murmur(dur, voices=10, seed=9, level=0.5):
    """Indistinct crowd chatter: formant-band noise gated at syllable rate."""
    out = np.zeros((secs(dur), 2), np.float32)
    r = rng(seed)
    t = t_axis(dur)
    for v in range(voices):
        lo = r.uniform(250, 500)
        x = bp(pink(dur, seed + v), lo, lo * r.uniform(2.2, 3.5))
        rate = r.uniform(3.0, 5.5)
        gate = np.clip(np.sin(2 * np.pi * rate * t + r.uniform(0, 6)) * 0.5 + 0.5, 0, 1) ** 2
        phrase = np.clip(np.sin(2 * np.pi * r.uniform(0.15, 0.35) * t + r.uniform(0, 6)), 0, 1)
        out += stereo(x * gate * phrase, pan=r.uniform(-0.8, 0.8))
    return norm(out, level)


def applause(dur, density=40.0, seed=10, level=0.6, swell=(0.4, 1.5)):
    out = np.zeros((secs(dur), 2), np.float32)
    r = rng(seed)
    n = int(density * dur)
    clap_cache = [bp(white(0.03, seed + k), 900, 3200) * env_exp(0.03, 0.006) for k in range(12)]
    for k in range(n):
        t0 = r.uniform(0, dur - 0.05)
        c = stereo(clap_cache[k % 12] * r.uniform(0.3, 1.0), pan=r.uniform(-0.9, 0.9))
        i = secs(t0)
        out[i:i + len(c)] += c
    e = env_ad(dur, swell[0], swell[1], 1.0)[:, None]
    return norm(out * e, level)


def breath_in(seed=11):
    dur = 1.4
    x = bp(pink(dur, seed), 500, 3200) * env_ad(dur, 1.0, 0.3, 1.5)
    return norm(x, 0.45)


def room_tone(dur, seed=12, level=0.06):
    x = lp(pink(dur, seed), 380)
    return stereo(norm(x, level), width=1.0)


def city(dur, seed=13, level=0.25):
    rumble = lp(brown(dur, seed), 220)
    out = stereo(norm(rumble, 0.6), width=1.0)
    r = rng(seed)
    for k in range(3):
        t0 = r.uniform(0, max(0.1, dur - 3))
        car = lp(whoosh(2.5, 120, 900, seed + k), 1200)
        pan = np.linspace(-0.8, 0.8, len(car)) if k % 2 else np.linspace(0.8, -0.8, len(car))
        c = np.stack([car * np.cos((pan + 1) * np.pi / 4), car * np.sin((pan + 1) * np.pi / 4)], axis=1)
        i = secs(t0)
        out[i:i + len(c)] += c[: len(out) - i] * 0.5
    return norm(out, level)


def cafe(dur, seed=14, level=0.25):
    out = murmur(dur, 12, seed, 0.6)
    r = rng(seed)
    for k in range(int(dur * 0.8)):
        d = 0.25
        clink = (sine(r.uniform(2800, 4200), d) + 0.4 * sine(r.uniform(5000, 6500), d)) * env_exp(d, 0.05)
        i = secs(r.uniform(0, dur - 0.3))
        out[i:i + len(clink)] += stereo(clink * 0.15, pan=r.uniform(-0.7, 0.7))
    return norm(out, level)


def clunk(seed=15):
    dur = 1.5
    thump = sine(glide(95, 60, 0.4), 0.4) * env_exp(0.4, 0.09)
    click = bp(white(0.03, seed), 1500, 6000) * env_exp(0.03, 0.004)
    hum_t = t_axis(dur)
    hum = (np.sin(2 * np.pi * 60 * hum_t) + 0.5 * np.sin(2 * np.pi * 120 * hum_t)) * 0.08
    hum *= np.clip(hum_t / 0.4, 0, 1) * np.exp(-hum_t / 1.2)
    out = hum.astype(np.float32)
    out[: len(thump)] += thump
    out[: len(click)] += click * 0.7
    return norm(out, 0.7)


def shimmer(dur=2.5, seed=16, density=30):
    """Glittering bells (eyes closing, magic moments)."""
    out = np.zeros((secs(dur), 2), np.float32)
    r = rng(seed)
    for k in range(int(density * dur)):
        f = r.uniform(1800, 5200)
        d = r.uniform(0.15, 0.4)
        b = sine(f, d) * env_exp(d, d / 4) * r.uniform(0.2, 0.6)
        i = secs(r.uniform(0, dur - d))
        out[i:i + len(b)] += stereo(b, pan=r.uniform(-1, 1))
    return norm(out, 0.5)


def typing(dur, seed=17):
    out = np.zeros(secs(dur), np.float32)
    r = rng(seed)
    t = 0.0
    while t < dur - 0.05:
        k = bp(white(0.02, int(t * 1000)), 1500, 6000) * env_exp(0.02, 0.004) * r.uniform(0.3, 0.8)
        i = secs(t)
        out[i:i + len(k)] += k
        t += r.uniform(0.06, 0.16)
    return norm(out, 0.4)


def scribble(dur, seed=18):
    x = bp(white(dur, seed), 2000, 7000)
    t = t_axis(dur)
    gate = (np.sin(2 * np.pi * 9 * t) * 0.5 + 0.5) ** 3
    return norm(x * gate, 0.35)


def impact(seed=19):
    """Shockwave hit: boom + bright whoosh."""
    boom = drop_boom(seed)
    w = whoosh(1.0, 400, 6000, seed)
    out = boom.copy()
    out[: len(w)] += w * 0.5
    return norm(out, 0.95)


def reverse_swell(dur=1.2, seed=20):
    x = lp(white(dur, seed), 6000) * (t_axis(dur) / dur) ** 3
    return norm(x, 0.6)
