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


# --- home and school (film 2) ------------------------------------------------------------------------

def buzz(dur=0.75, seed=21):
    """A phone vibrating on a wooden desk: two motor pulses with a woody rattle."""
    out = np.zeros(secs(dur), np.float32)
    t = t_axis(dur)
    for k, (t0, d) in enumerate(((0.0, 0.28), (0.4, 0.28))):
        if t0 >= dur:
            break
        n = secs(min(d, dur - t0))
        tt = t[:n]
        motor = np.sign(np.sin(2 * np.pi * 168 * tt)) * 0.35 + np.sin(2 * np.pi * 336 * tt) * 0.2
        rattle = bp(white(n / SR, seed + k), 300, 1800) * (np.sin(2 * np.pi * 42 * tt) * 0.5 + 0.5)
        e = env_ad(n / SR, 0.01, 0.03, 1.0)
        i = secs(t0)
        out[i:i + n] += ((motor + rattle * 0.6) * e)[: len(out) - i]
    return norm(lp(out, 2500), 0.7)


def slap(seed=22):
    """A sticky note slapped onto a wall."""
    dur = 0.18
    x = bp(white(dur, seed), 700, 4200) * env_exp(dur, 0.012, 0.001)
    body = sine(glide(260, 140, 0.08), 0.08) * env_exp(0.08, 0.02) * 0.5
    out = x.copy()
    out[: len(body)] += body
    return norm(out, 0.7)


def thud(seed=23, heavy=1.0):
    """A book dropped onto a pile."""
    dur = 0.5
    low = sine(glide(110, 62, 0.25), 0.25) * env_exp(0.25, 0.06) * heavy
    knock = bp(white(0.12, seed), 180, 1400) * env_exp(0.12, 0.025)
    flap = bp(white(dur, seed + 1), 1200, 5000) * env_exp(dur, 0.04) * 0.2
    out = flap.copy()
    out[: len(low)] += low
    out[: len(knock)] += knock * 0.8
    return norm(out, 0.8)


def alarm_ring(dur=3.0, seed=24):
    """A twin-bell alarm clock: a hammer trilling between two bells."""
    out = np.zeros(secs(dur), np.float32)
    rate = 17.0
    k = 0
    t = 0.0
    while t < dur - 0.1:
        bell = (2950, 4120) if k % 2 == 0 else (3330, 4710)
        d = 0.16
        s = (sine(bell[0], d) + 0.6 * sine(bell[1], d) + 0.3 * sine(bell[0] * 2.7, d)) * env_exp(d, 0.05, 0.001)
        s += bp(white(d, seed + k), 3000, 8000) * env_exp(d, 0.004) * 0.6
        i = secs(t)
        out[i:i + len(s)] += s[: len(out) - i]
        t += 1.0 / rate
        k += 1
    return norm(hp(out, 900), 0.6)


def sludge(dur=4.0, seed=25):
    """Quicksand: a slow churning drag with bubbles popping."""
    t = t_axis(dur)
    churn = lp(brown(dur, seed), 260) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t))
    out = churn * 1.2
    r = rng(seed)
    for k in range(int(dur * 6)):
        d = r.uniform(0.04, 0.09)
        f0 = r.uniform(140, 300)
        b = sine(glide(f0, f0 * r.uniform(1.6, 2.4), d), d) * env_ad(d, 0.005, d * 0.8)
        i = secs(r.uniform(0, dur - d))
        out[i:i + len(b)] += b * r.uniform(0.2, 0.5)
    return norm(out.astype(np.float32), 0.7)


def page_flip(seed=26):
    dur = 0.32
    x = bp(pink(dur, seed), 1200, 6500) * env_ad(dur, 0.06, 0.22, 1.5)
    crinkle = bp(white(dur, seed + 1), 3000, 9000) * env_exp(dur, 0.05) * 0.25
    return norm(x + crinkle, 0.5)


def drawer(open_=True, seed=27):
    """A wooden drawer sliding open, or slammed shut."""
    if open_:
        dur = 0.4
        slide = bp(white(dur, seed), 300, 2200) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 23 * t_axis(dur))))
        return norm(slide * env_ad(dur, 0.04, 0.2), 0.5)
    dur = 0.6
    slam = sine(glide(150, 80, 0.2), 0.2) * env_exp(0.2, 0.04)
    knock = bp(white(0.1, seed), 200, 2500) * env_exp(0.1, 0.02)
    rattle = bp(white(dur, seed + 1), 1500, 6000) * env_exp(dur, 0.08) * 0.3
    out = rattle.copy()
    out[: len(slam)] += slam
    out[: len(knock)] += knock
    return norm(out, 0.85)


def key_turn(seed=28):
    """A small key turning in a lock: two metallic clicks."""
    dur = 0.35
    out = np.zeros(secs(dur), np.float32)
    for k, t0 in enumerate((0.0, 0.14)):
        c = hp(white(0.015, seed + k), 2500) * env_exp(0.015, 0.002)
        ring = sine(3800 + 600 * k, 0.08) * env_exp(0.08, 0.015) * 0.3
        i = secs(t0)
        out[i:i + len(c)] += c
        out[i:i + len(ring)] += ring
    return norm(out, 0.6)


def bang(seed=29):
    """Something banging on the inside of a closed drawer."""
    dur = 0.7
    thump = sine(glide(120, 55, 0.3), 0.3) * env_exp(0.3, 0.07)
    wood = bp(white(0.12, seed), 150, 1200) * env_exp(0.12, 0.03)
    rattle = bp(white(dur, seed + 1), 900, 4000) * env_exp(dur, 0.1) * 0.35
    out = rattle.copy()
    out[: len(thump)] += thump
    out[: len(wood)] += wood
    return norm(lp(out, 3000), 0.9)


def click(seed=30):
    """A light switch or lamp switch."""
    dur = 0.06
    x = hp(white(dur, seed), 1800) * env_exp(dur, 0.003) + sine(2200, dur) * env_exp(dur, 0.006) * 0.3
    return norm(x, 0.55)


def door(open_=True, seed=31):
    """A front door: a short creak and the latch, or the thump of it closing."""
    if open_:
        dur = 0.9
        f = glide(420, 300, dur)
        creak = sine(f, dur) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * t_axis(dur)))) * env_ad(dur, 0.1, 0.5)
        latch = hp(white(0.02, seed), 2000) * env_exp(0.02, 0.003)
        out = lp(creak, 2500) * 0.4
        out[: len(latch)] += latch
        return norm(out, 0.6)
    dur = 0.6
    thump = sine(glide(90, 55, 0.3), 0.3) * env_exp(0.3, 0.06)
    latch = hp(white(0.02, seed + 1), 2000) * env_exp(0.02, 0.003)
    out = np.zeros(secs(dur), np.float32)
    out[: len(thump)] += thump
    i = secs(0.05)
    out[i:i + len(latch)] += latch * 0.8
    return norm(out, 0.8)


def tape_rip(dur=1.2, seed=32):
    """Duct tape pulled off the roll: dense crackle with a stretched tone."""
    r = rng(seed)
    out = np.zeros(secs(dur), np.float32)
    t = 0.0
    while t < dur - 0.01:
        c = bp(white(0.004, int(t * 1e4)), 1200, 6000) * r.uniform(0.3, 1.0)
        i = secs(t)
        out[i:i + len(c)] += c[: len(out) - i]
        t += r.uniform(0.002, 0.007)
    tone = sine(glide(900, 1300, dur), dur) * 0.05
    return norm((out + tone) * env_ad(dur, 0.05, 0.15), 0.5)


def birds(dur, seed=33, level=0.2):
    """Morning birdsong far off: little groups of chirps."""
    out = np.zeros((secs(dur), 2), np.float32)
    r = rng(seed)
    t = r.uniform(0.0, 0.6)
    while t < dur - 0.5:
        pan = r.uniform(-0.8, 0.8)
        f = r.uniform(3200, 5600)
        for k in range(r.integers(2, 5)):
            d = r.uniform(0.04, 0.09)
            ch = sine(glide(f, f * r.uniform(1.1, 1.4), d), d) * env_ad(d, 0.005, d * 0.7)
            i = secs(t + k * r.uniform(0.07, 0.12))
            out[i:i + len(ch)] += stereo(ch * r.uniform(0.3, 0.7), pan)[: len(out) - i]
        t += r.uniform(0.6, 1.8)
    return norm(out, level)


def tinnitus(dur=1.6, seed=34):
    """A thin high ring as his mind goes blank."""
    x = sine(6200, dur) * env_ad(dur, 0.6, 0.4) + sine(6230, dur) * env_ad(dur, 0.6, 0.4) * 0.5
    return norm(x, 0.35)


def puff_out(seed=35):
    """The shadow dissolving into smoke."""
    dur = 1.4
    x = bp(pink(dur, seed), 300, 3000) * env_ad(dur, 0.05, 1.2)
    down = sine(glide(220, 70, 1.0), 1.0) * env_exp(1.0, 0.3) * 0.4
    out = x.copy()
    out[: len(down)] += down
    return norm(out, 0.6)


# --- the gym, the street and the year (film 3) ------------------------------------------------------------------

def _modes(freqs, decays, dur, amps=None, seed=0):
    """Sum of decaying sine modes: the ring of struck metal."""
    t = t_axis(dur)
    out = np.zeros(len(t), np.float32)
    amps = amps or [1.0] * len(freqs)
    r = rng(seed)
    for f, d, a in zip(freqs, decays, amps):
        f *= r.uniform(0.97, 1.03)
        out += (np.sin(2 * np.pi * f * t + r.uniform(0, 6)) * np.exp(-t / d) * a).astype(np.float32)
    return out


def clank(seed=0, heavy=1.0):
    """Iron plates knocking together (heavy > 1 is lower and longer)."""
    dur = 1.0
    k = 1.0 / heavy
    ring = _modes([310 * k, 870 * k, 1650 * k, 2400 * k, 3900 * k], [0.28 * heavy, 0.16, 0.1, 0.07, 0.04], dur,
                  [1.0, 0.7, 0.5, 0.35, 0.2], seed)
    hit = bp(white(dur, seed), 900, 6500) * env_exp(dur, 0.012)
    thump = sine(glide(110 * k, 70 * k, dur), dur) * env_exp(dur, 0.05) * 0.8
    return norm(ring * 0.5 + hit * 0.8 + thump, 0.9)


def dumbbell_drop(seed=0):
    """A dumbbell dropped on a rubber floor: a dull thud, a clank, a short roll."""
    dur = 1.6
    out = np.zeros(secs(dur), np.float32)
    th = lp(white(0.3, seed), 500) * env_exp(0.3, 0.04) + sine(glide(70, 45, 0.3), 0.3) * env_exp(0.3, 0.07)
    out[: len(th)] += th * 1.2
    ck = clank(seed + 1, 0.8) * 0.45
    out[: len(ck)] += ck[: len(out)]
    t = t_axis(dur - 0.15)
    roll = lp(brown(dur - 0.15, seed + 2), 300) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t)) * np.exp(-t / 0.4)
    i = secs(0.15)
    out[i:i + len(roll)] += roll * 0.7
    return norm(out, 0.9)


def bar_rack(seed=0):
    """A barbell set back in its hooks: two clanks a moment apart."""
    a = clank(seed, 1.25)
    b = clank(seed + 7, 1.1) * 0.55
    out = np.zeros(len(a) + secs(0.09), np.float32)
    out[: len(a)] += a
    out[secs(0.09): secs(0.09) + len(b)] += b
    return norm(out, 0.9)


def treadmill(dur, seed=0, level=0.25):
    """A treadmill running: motor whine and the belt's hum."""
    t = t_axis(dur)
    wob = 1 + 0.004 * np.sin(2 * np.pi * 0.7 * t)
    whine = np.sin(2 * np.pi * 240 * wob * t) * 0.25 + np.sin(2 * np.pi * 480 * wob * t) * 0.12
    belt = lp(pink(dur, seed), 260) * 0.8
    return stereo(norm((whine + belt).astype(np.float32), level), width=0.4)


def shoulder_tap(seed=0):
    """A finger on a shoulder: a small, soft knock with something enormous under it."""
    dur = 1.4
    out = np.zeros(secs(dur), np.float32)
    knock = bp(white(0.08, seed), 300, 1600) * env_exp(0.08, 0.008) + sine(190, 0.08) * env_exp(0.08, 0.02) * 0.6
    out[: len(knock)] += knock
    sub = sine(glide(54, 34, 1.3), 1.3) * env_ad(1.3, 0.04, 1.2) * 0.9
    i = secs(0.03)
    out[i:i + len(sub)] += sub
    return norm(out, 0.9)


def poof(seed=0, dur=1.8, dark=False):
    """Someone going to smoke: an airy hiss that drifts up and thins out, a dark whoosh, a few crackles."""
    air = bp(pink(dur, seed), 700 if not dark else 300, 6500 if not dark else 2500) * env_ad(dur, 0.12, dur - 0.12, 2.2)
    low = lp(pink(dur, seed + 1), 240) * env_ad(dur, 0.05, 0.9) * 0.6
    out = air + low
    r = rng(seed)
    for k in range(14):
        t0 = r.uniform(0.0, dur * 0.7)
        cl = bp(white(0.012, seed + 10 + k), 2500, 8000) * env_exp(0.012, 0.002) * r.uniform(0.1, 0.35)
        i = secs(t0)
        out[i:i + len(cl)] += cl
    return norm(out, 0.8)


def shutter(seed=0):
    """An old camera: shutter clack and a bright flash pop."""
    dur = 0.5
    out = np.zeros(secs(dur), np.float32)
    for t0, g in ((0.0, 1.0), (0.045, 0.7)):
        c = hp(white(0.03, seed + int(t0 * 100)), 1500) * env_exp(0.03, 0.004) * g
        i = secs(t0)
        out[i:i + len(c)] += c
    pop = sine(glide(2600, 5200, 0.2), 0.2) * env_exp(0.2, 0.05) * 0.12
    out[: len(pop)] += pop
    return norm(out, 0.8)


def chalk_clap(seed=0):
    dur = 0.6
    clap = bp(white(dur, seed), 700, 4200) * env_exp(dur, 0.012)
    dust = lp(pink(dur, seed + 1), 1800) * env_ad(dur, 0.02, 0.5) * 0.35
    return norm(clap + dust, 0.8)


def rope_turn(seed=0):
    """One turn of a skipping rope: a fast swish and a tick on the floor."""
    dur = 0.3
    sw = whoosh(0.18, 900, 3500, seed) * 0.6
    out = np.zeros(secs(dur), np.float32)
    out[: len(sw)] += sw
    tk = bp(white(0.02, seed + 1), 1500, 6000) * env_exp(0.02, 0.003)
    i = secs(0.17)
    out[i:i + len(tk)] += tk
    return norm(out, 0.7)


def firework_launch(seed=0, dur=0.7):
    t = t_axis(dur)
    whistle = sine(glide(700, 2600, dur), dur) * np.sin(np.pi * t / dur) * 0.3
    hiss = bp(white(dur, seed), 1500, 7000) * env_ad(dur, 0.05, dur - 0.05) * 0.4
    return norm(whistle + hiss, 0.6)


def firework_boom(seed=0, dur=2.6):
    """The burst: a deep boom and a crackling tail (stereo)."""
    boom = sine(glide(64, 30, dur), dur) * env_exp(dur, 0.35, 0.004)
    rumble = lp(brown(dur, seed), 180) * env_exp(dur, 0.6)
    out = stereo(norm(boom + rumble, 0.9), width=0.6)
    r = rng(seed)
    for k in range(60):
        t0 = r.uniform(0.25, dur - 0.1) * (0.6 + 0.4 * r.uniform())
        cl = bp(white(0.01, seed + 30 + k), 2000, 9000) * env_exp(0.01, 0.0015) * r.uniform(0.05, 0.3)
        i = secs(t0)
        out[i:i + len(cl)] += stereo(cl, r.uniform(-0.9, 0.9))[: len(out) - i]
    return norm(out, 0.9)


def crowd_cheer(dur, seed=0, level=0.6):
    """A happy crowd at midnight: clapping, chatter and whoops."""
    out = applause(dur, 55, seed, 0.7, swell=(0.05, dur * 0.8)) + murmur(dur, 16, seed + 1, 0.5)
    r = rng(seed)
    for k in range(int(dur * 2.5)):
        t0 = r.uniform(0.0, dur - 0.6)
        d = r.uniform(0.25, 0.5)
        f0 = r.uniform(380, 700)
        x = sine(glide(f0, f0 * r.uniform(1.3, 1.8), d), d)
        x = bp(x + 0.3 * bp(pink(d, seed + 50 + k), f0, f0 * 3), 300, 3000) * env_ad(d, 0.03, d - 0.03) * 0.5
        i = secs(t0)
        out[i:i + len(x)] += stereo(x, r.uniform(-0.8, 0.8))[: len(out) - i]
    return norm(out, level)


def wind(dur, seed=0, level=0.2, gusty=1.0):
    t = t_axis(dur)
    x = bp(pink(dur, seed), 180, 1400)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.13 * t + 1.0) * np.sin(2 * np.pi * 0.31 * t) * gusty
    y = bp(pink(dur, seed + 1), 200, 1600)
    return np.stack([norm(x * gust, level), norm(y * gust[::-1], level)], axis=1)


def rain(dur, seed=0, level=0.25):
    hiss = bp(white(dur, seed), 1200, 9000) * 0.5
    body = lp(pink(dur, seed + 1), 900) * 0.4
    out = hiss + body
    r = rng(seed)
    for k in range(int(dur * 70)):
        t0 = r.uniform(0, dur - 0.02)
        d = bp(white(0.012, seed + 100 + (k % 50)), 1800, 7000) * env_exp(0.012, 0.002) * r.uniform(0.2, 0.6)
        i = secs(t0)
        out[i:i + len(d)] += d
    y = np.roll(out, secs(0.013))
    return np.stack([norm(out, level), norm(y, level)], axis=1)


def cicadas(dur, seed=0, level=0.12):
    t = t_axis(dur)
    out = np.zeros((len(t), 2), np.float32)
    r = rng(seed)
    for v in range(3):
        f = r.uniform(4200, 5600)
        am = (np.sin(2 * np.pi * r.uniform(48, 62) * t) * 0.5 + 0.5) ** 3
        phrase = np.clip(np.sin(2 * np.pi * r.uniform(0.08, 0.2) * t + r.uniform(0, 6)) * 1.5, 0, 1)
        x = np.sin(2 * np.pi * f * t) * am * phrase
        out += stereo(x.astype(np.float32), r.uniform(-0.7, 0.7))
    return norm(out, level)


def rustle(dur, seed=0, level=0.15):
    t = t_axis(dur)
    x = bp(white(dur, seed), 1600, 8000)
    env = np.clip(np.sin(2 * np.pi * 0.4 * t) * np.sin(2 * np.pi * 0.17 * t + 2), 0, 1) ** 1.5 + 0.15
    return stereo(norm(x * env, level), width=0.8)


def light_buzz(dur, seed=0, level=0.05, flicker=None):
    """Fluorescent tubes: a mains hum; flicker: list of times for a stutter."""
    t = t_axis(dur)
    hum = np.sin(2 * np.pi * 100 * t) * 0.6 + np.sin(2 * np.pi * 200 * t) * 0.25 + np.sin(2 * np.pi * 300 * t) * 0.1
    x = (hum + 0.15 * hp(white(dur, seed), 3000)).astype(np.float32)
    for f in flicker or []:
        i = secs(f)
        c = bp(white(0.03, seed + int(f * 10)), 1000, 6000) * env_exp(0.03, 0.004) * 4
        x[i:i + len(c)] += c[: len(x) - i]
    return stereo(norm(x, level), width=0.5)


def bell(seed=0, f0=660.0, dur=3.5):
    """A clear chime (midnight)."""
    ratios = [0.5, 1.0, 1.19, 1.56, 2.0, 2.66, 3.01]
    decays = [2.6, 2.2, 1.6, 1.2, 1.0, 0.7, 0.5]
    amps = [0.5, 1.0, 0.6, 0.45, 0.35, 0.25, 0.15]
    x = _modes([f0 * r for r in ratios], decays, dur, amps, seed)
    strike = bp(white(dur, seed), 2000, 8000) * env_exp(dur, 0.005) * 0.4
    return norm(x + strike, 0.8)


def snow_step(seed=0):
    """A footstep in snow: a short granular crunch."""
    dur = 0.2
    out = np.zeros(secs(dur), np.float32)
    r = rng(seed)
    for k in range(40):
        t0 = r.uniform(0, 0.12)
        g = bp(white(0.004, seed + k), 1200, 6000) * r.uniform(0.2, 1.0)
        i = secs(t0)
        out[i:i + len(g)] += g
    out += lp(white(dur, seed + 99), 500) * env_exp(dur, 0.03) * 0.6
    return norm(lp(out, 5000), 0.55)


def splash_step(seed=0):
    dur = 0.35
    x = bp(white(dur, seed), 500, 4500) * env_ad(dur, 0.005, 0.3, 3.0)
    slosh = lp(pink(dur, seed + 1), 900) * env_ad(dur, 0.03, 0.3) * 0.6
    return norm(x + slosh, 0.6)


def car_horn(seed=0, dur=0.45):
    """A distant two-tone car horn (New Year's Eve in the street)."""
    t = t_axis(dur)
    x = np.zeros(len(t), np.float32)
    for f in (392.0, 494.0):
        x += np.sign(np.sin(2 * np.pi * f * t)).astype(np.float32) * 0.3
    x = lp(bp(x, 300, 2500), 1800) * env_ad(dur, 0.02, 0.08)
    return norm(reverb(x, wet=0.5, length=1.6, decay=0.6), 0.5)


def sizzle(dur=1.6, seed=0):
    """Something crumbling to ash: a dry crackle over a soft hiss."""
    out = bp(white(dur, seed), 3000, 9000) * env_ad(dur, 0.05, dur * 0.7) * 0.25
    r = rng(seed)
    for k in range(int(dur * 90)):
        t0 = r.uniform(0, dur - 0.02)
        c = bp(white(0.006, seed + 7 + (k % 40)), 2500, 9000) * r.uniform(0.2, 1.0)
        i = secs(t0)
        out[i:i + len(c)] += c * (1 - t0 / dur)
    return norm(out, 0.7)


def grunt(seed=0, dur=0.55):
    """A wordless effort sound: a voiced push of breath through closed teeth."""
    t = t_axis(dur)
    f0 = 118 * (1 + 0.06 * np.sin(2 * np.pi * 7 * t))
    buzz = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR)).astype(np.float32)
    voiced = bp(buzz, 300, 1400) * 0.5 + bp(pink(dur, seed), 500, 3000) * 0.6
    return norm(voiced * env_ad(dur, 0.04, 0.3, 1.5), 0.6)
