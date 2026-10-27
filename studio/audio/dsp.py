"""Small numpy/scipy DSP toolkit for sound effects and mixing (48 kHz float32)."""
from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000


def secs(n):
    return int(round(n * SR))


def t_axis(dur):
    return np.arange(secs(dur)) / SR


def rng(seed):
    return np.random.default_rng(seed)


def white(dur, seed=0):
    return rng(seed).standard_normal(secs(dur)).astype(np.float32)


def pink(dur, seed=0):
    n = secs(dur)
    x = rng(seed).standard_normal(n)
    f = np.fft.rfft(x)
    k = np.arange(len(f))
    k[0] = 1
    f /= np.sqrt(k)
    y = np.fft.irfft(f, n)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def brown(dur, seed=0):
    y = np.cumsum(white(dur, seed))
    y = signal.sosfilt(signal.butter(1, 20, 'highpass', fs=SR, output='sos'), y)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def lp(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, min(hz, SR / 2 - 100), 'lowpass', fs=SR, output='sos'), x, axis=0).astype(np.float32)


def hp(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, 'highpass', fs=SR, output='sos'), x, axis=0).astype(np.float32)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, min(hi, SR / 2 - 100)], 'bandpass', fs=SR, output='sos'), x, axis=0).astype(np.float32)


def sweep_bp(x, f0, f1, q=2.0, block=512):
    """Band-pass whose centre glides from f0 to f1 (log), processed in blocks."""
    out = np.zeros_like(x)
    n = len(x)
    zi = None
    for i in range(0, n, block):
        u = i / max(1, n - 1)
        fc = f0 * (f1 / f0) ** u
        lo, hi = fc / (1 + 1 / q), min(fc * (1 + 1 / q), SR / 2 - 200)
        sos = signal.butter(2, [lo, hi], 'bandpass', fs=SR, output='sos')
        if zi is None or zi.shape[0] != sos.shape[0]:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + block], zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
    return out.astype(np.float32)


def env_exp(dur, decay, attack=0.002):
    t = t_axis(dur)
    e = np.exp(-t / max(decay, 1e-4))
    if attack > 0:
        e *= np.clip(t / attack, 0, 1)
    return e.astype(np.float32)


def env_ad(dur, attack, release, curve=2.0):
    t = t_axis(dur)
    a = np.clip(t / max(attack, 1e-4), 0, 1) ** curve
    r = np.clip((dur - t) / max(release, 1e-4), 0, 1) ** curve
    return (a * r).astype(np.float32)


def sine(freq, dur, phase=0.0):
    """freq may be a float or an array (glide)."""
    if np.ndim(freq) == 0:
        return np.sin(2 * np.pi * freq * t_axis(dur) + phase).astype(np.float32)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    return np.sin(ph + phase).astype(np.float32)


def glide(f0, f1, dur, curve='exp'):
    n = secs(dur)
    u = np.linspace(0, 1, n)
    if curve == 'exp':
        return f0 * (f1 / f0) ** u
    return f0 + (f1 - f0) * u


def pluck(freq, dur, damping=0.996, bright=0.6, seed=0):
    """Karplus-Strong plucked string."""
    n = secs(dur)
    period = max(2, int(SR / freq))
    buf = rng(seed).uniform(-1, 1, period)
    buf = lp(buf, 2000 + 8000 * bright, 1) if period > 16 else buf
    out = np.zeros(n, dtype=np.float32)
    b = buf.astype(np.float64)
    for i in range(n):
        j = i % period
        out[i] = b[j]
        nxt = b[(j + 1) % period]
        b[j] = damping * 0.5 * (b[j] + nxt)
    return out


def stereo(x, pan=0.0, width=0.0):
    """Mono -> stereo with constant-power pan (-1 left .. 1 right)."""
    if x.ndim == 2:
        return x
    a = (pan + 1) * np.pi / 4
    left, right = np.cos(a) * x, np.sin(a) * x
    if width > 0:
        d = secs(0.012 * width)
        right = np.concatenate([np.zeros(d, np.float32), right[:-d]]) if d else right
    return np.stack([left, right], axis=1).astype(np.float32)


@lru_cache(maxsize=8)
def _ir(length, decay, seed, bright):
    n = secs(length)
    t = np.arange(n) / SR
    r = rng(seed)
    ir = r.standard_normal((n, 2)) * np.exp(-t / decay)[:, None]
    ir = lp(ir, bright)
    ir[: secs(0.008)] *= np.linspace(0, 1, secs(0.008))[:, None]
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-9
    return ir.astype(np.float32)


def reverb(x, wet=0.3, length=2.2, decay=0.55, bright=6000, seed=3, predelay=0.02):
    x = stereo(x) if x.ndim == 1 else x
    ir = _ir(length, decay, seed, bright)
    pad = np.zeros((secs(length) + secs(predelay), 2), np.float32)
    xx = np.concatenate([x, pad])
    wet_sig = np.stack([signal.fftconvolve(xx[:, ch], ir[:, ch])[: len(xx)] for ch in range(2)], axis=1)
    d = secs(predelay)
    wet_sig = np.concatenate([np.zeros((d, 2), np.float32), wet_sig[:-d]]) if d else wet_sig
    return ((1 - wet) * xx + wet * wet_sig * 2.2).astype(np.float32)


def norm(x, peak=0.9):
    m = np.abs(x).max()
    return (x * (peak / m)).astype(np.float32) if m > 0 else x


def db(v):
    return 10 ** (v / 20)


def fade(x, fin=0.005, fout=0.02):
    x = x.copy()
    a, b = secs(fin), secs(fout)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def read_wav(path):
    sr, x = wavfile.read(str(path))
    if x.dtype == np.int16:
        x = x.astype(np.float32) / 32768.0
    elif x.dtype == np.int32:
        x = x.astype(np.float32) / 2147483648.0
    else:
        x = x.astype(np.float32)
    if sr != SR:
        from math import gcd
        g = gcd(SR, sr)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    return x


def write_wav(path, x):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(str(path), SR, np.clip(x, -1, 1).astype(np.float32))
    return path


def ffmpeg_filter(x, af, tmpdir):
    """Run an ffmpeg audio filter (e.g. rubberband) on an array."""
    tmpdir = Path(tmpdir)
    tmpdir.mkdir(parents=True, exist_ok=True)
    src, dst = tmpdir / '_in.wav', tmpdir / '_out.wav'
    write_wav(src, x)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src), '-af', af,
                    '-ar', str(SR), '-c:a', 'pcm_f32le', str(dst)], check=True)
    return read_wav(dst)


def soft_clip(x, drive=1.0):
    return (np.tanh(x * drive) / np.tanh(drive)).astype(np.float32)


def leveler(x, target_db=-20.0, ratio=0.5, max_boost=9.0, max_cut=6.0, floor_db=-55.0, window=0.4, smooth_s=0.8):
    """Slow section-to-section levelling; leaves near-silence alone."""
    from scipy.ndimage import uniform_filter1d
    mono = x.mean(axis=1) if x.ndim == 2 else x
    ms = uniform_filter1d(mono.astype(np.float64) ** 2, size=secs(window))
    rms_db = 10 * np.log10(ms + 1e-12)
    gain_db = np.clip((target_db - rms_db) * ratio, -max_cut, max_boost)
    gain_db[rms_db < floor_db] = 0.0
    gain_db = uniform_filter1d(gain_db, size=secs(smooth_s))
    g = (10 ** (gain_db / 20)).astype(np.float32)
    return x * (g[:, None] if x.ndim == 2 else g)


def limiter(x, ceiling=0.95, smooth_s=0.01):
    """Peak limiter: min-hold the needed gain, then average it (never overshoots the ceiling)."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    need = np.minimum(1.0, ceiling / (np.abs(x).max(axis=1) + 1e-9))
    L = max(3, secs(smooth_s))
    held = minimum_filter1d(need, size=2 * L + 1)
    g = uniform_filter1d(held, size=L)
    return (x * g[:, None]).astype(np.float32)
