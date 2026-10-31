"""Whispered lines for the shadow crowd via Gemini text-to-speech (cached), then processed.

The API key is read from GEMINI_API_KEY or ~/.config/watch/.env and is never printed.
Without a key (or with quota exhausted) a wordless synthetic whisper is used instead.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
from scipy.io import wavfile

from .dsp import SR, bp, env_ad, ffmpeg_filter, hp, lp, norm, pink, read_wav, reverb, secs, soft_clip, stereo

TTS_MODELS = ['gemini-3.8-flash-tts', 'gemini-3.1-flash-tts-preview', 'gemini-2.5-flash-preview-tts']
# Only the line itself is sent: style instructions get read aloud by the TTS model.
# The whispered, menacing character comes from whisperize() and the processing below.
CACHE_VERSION = 'v2-plain'


def _key():
    k = os.environ.get('GEMINI_API_KEY', '').strip()
    if k:
        return k
    cfg = Path.home() / '.config' / 'watch' / '.env'
    if cfg.exists():
        for line in cfg.read_text().splitlines():
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return ''


def tts(text, voice, style, cache_dir, retries=6):
    """Return a cached WAV path for this line, generating it if needed (None if unavailable)."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    tag = hashlib.sha1(f'{CACHE_VERSION}|{text}|{voice}'.encode()).hexdigest()[:16]
    path = cache_dir / f'{tag}.wav'
    if path.exists() and path.stat().st_size > 1000:
        return path
    key = _key()
    if not key:
        return None
    body = {'contents': [{'parts': [{'text': text}]}],
            'generationConfig': {'responseModalities': ['AUDIO'],
                                 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice}}}}}
    for attempt in range(retries):
        for model in TTS_MODELS:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
            req = Request(url, data=json.dumps(body).encode(),
                          headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
            try:
                with urlopen(req, timeout=120) as r:
                    data = json.load(r)
                part = data['candidates'][0]['content']['parts'][0]['inlineData']
                raw = base64.b64decode(part['data'])
                if raw[:4] == b'RIFF':
                    path.write_bytes(raw)
                else:  # raw 24 kHz 16-bit PCM
                    pcm = np.frombuffer(raw, dtype=np.int16)
                    buf = io.BytesIO()
                    wavfile.write(buf, 24000, pcm)
                    path.write_bytes(buf.getvalue())
                return path
            except HTTPError as e:
                if e.code in (429, 500, 503):
                    continue
                return None
            except (URLError, TimeoutError, KeyError, IndexError, ValueError):
                continue
        time.sleep(min(60, 8 * (attempt + 1)))
    return None


def trim_silence(x, thresh=0.02, pad=0.05):
    mono = np.abs(x if x.ndim == 1 else x.mean(axis=1))
    idx = np.where(mono > thresh * mono.max())[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - secs(pad)), min(len(x), idx[-1] + secs(pad))
    return x[a:b]


def fake_whisper(dur=1.2, seed=0):
    """Wordless breathy whisper used when TTS is unavailable."""
    x = bp(pink(dur, seed), 900, 5000)
    t = np.arange(len(x)) / SR
    gate = (np.sin(2 * np.pi * 4.2 * t) * 0.5 + 0.5) ** 1.5
    return norm(x * gate * env_ad(dur, 0.05, 0.3), 0.6)


def whisperize(x, bands=28, lo=120.0, hi=7800.0, seed=0):
    """Noise vocoder: keep each band's loudness contour, replace the voice with breath."""
    from .dsp import white
    edges = np.geomspace(lo, hi, bands + 1)
    noise = white(len(x) / SR + 0.01, seed)[: len(x)]
    out = np.zeros(len(x), np.float32)
    for a, b in zip(edges[:-1], edges[1:]):
        env = lp(np.abs(bp(x, a, b)), 45)
        nb = bp(noise, a, b)
        nb /= np.sqrt((nb ** 2).mean()) + 1e-9
        out += nb * np.maximum(env, 0)
    return norm(out, 0.9)


def fit(x, max_dur, tmpdir):
    """Speed a line up (up to 1.6x) so it fits its on-screen window."""
    dur = len(x) / SR
    if dur <= max_dur:
        return x
    tempo = min(1.6, dur / max_dur)
    return ffmpeg_filter(x, f'rubberband=tempo={tempo:.3f}', tmpdir)


def process(x, style, tmpdir, pan=0.0, max_dur=None):
    x = trim_silence(x)
    if max_dur:
        x = fit(x, max_dur, tmpdir)
    if style == 'hiss':
        voice = ffmpeg_filter(x, 'rubberband=pitch=0.9:formant=preserved', tmpdir)
        breath = whisperize(x)
        n_ = min(len(voice), len(breath))
        y = 0.8 * breath[:n_] + 0.5 * voice[:n_]
        y = hp(y, 160)
        y = reverb(stereo(y, pan, 0.6), wet=0.33, length=2.4, decay=0.6)
    elif style == 'deep':
        low = ffmpeg_filter(x, 'rubberband=pitch=0.7', tmpdir)
        sub = ffmpeg_filter(x, 'rubberband=pitch=0.5', tmpdir)
        breath = whisperize(low)
        n_ = min(len(low), len(sub), len(breath))
        y = 0.6 * low[:n_] + 0.3 * sub[:n_] + 0.6 * breath[:n_]
        y = soft_clip(hp(lp(y, 6500), 70) * 1.3, 1.4)
        y = reverb(stereo(y, pan, 0.8), wet=0.4, length=3.0, decay=0.8)
    elif style == 'close':
        # right at your ear: dry and crisp, so every word is understood
        voice = ffmpeg_filter(x, 'rubberband=pitch=0.95:formant=preserved', tmpdir)
        breath = whisperize(x)
        n_ = min(len(voice), len(breath))
        y = 0.75 * voice[:n_] + 0.6 * breath[:n_]
        y = hp(y, 150)
        y = y + 0.6 * bp(y, 2200, 5200)
        y = reverb(stereo(y, pan, 0.25), wet=0.12, length=1.0, decay=0.35)
    elif style == 'soft':
        # close and intimate, almost kind: mostly breath, a little voice, a small room
        voice = ffmpeg_filter(x, 'rubberband=pitch=0.97:formant=preserved', tmpdir)
        breath = whisperize(x)
        n_ = min(len(voice), len(breath))
        y = 0.75 * breath[:n_] + 0.5 * voice[:n_]
        y = hp(y, 140)
        y = reverb(stereo(y, pan, 0.3), wet=0.16, length=1.2, decay=0.4)
    else:  # roar layer
        y = soft_clip(x * 1.8, 2.0)
        y = reverb(stereo(y, pan, 1.0), wet=0.45, length=3.2, decay=0.9)
    return norm(y, 0.9)


def line(text, style, voice, cache_dir, tmpdir, pan=0.0, seed=0, max_dur=None):
    path = tts(text, voice, style, cache_dir)
    if path is None:
        x = fake_whisper(0.35 + 0.08 * len(text.split()) * 2, seed)
    else:
        x = read_wav(path)
        if x.ndim == 2:
            x = x.mean(axis=1)
    return process(x, style, tmpdir, pan, max_dur)


def roar(text, voices, cache_dir, tmpdir, length=2.4):
    """Many voices shouting the same line, time-aligned and pitched into a crowd."""
    layers = []
    for k, (voice, pitch) in enumerate(voices):
        path = tts(text, voice, 'roar', cache_dir)
        x = read_wav(path) if path else fake_whisper(length, 40 + k)
        if x.ndim == 2:
            x = x.mean(axis=1)
        x = trim_silence(x)
        tempo = max(0.5, min(2.0, (len(x) / SR) / length))
        x = ffmpeg_filter(x, f'rubberband=pitch={pitch}:tempo={tempo:.3f}', tmpdir)
        gain = 1.0 if k == 0 else 0.4  # the first voice leads so the words stay intelligible
        layers.append(stereo(x * gain, pan=0.0 if k == 0 else -0.8 + 1.6 * k / max(1, len(voices) - 1), width=0.5))
    n_ = max(len(a) for a in layers)
    mix = np.zeros((n_, 2), np.float32)
    for a in layers:
        mix[: len(a)] += a
    mix = soft_clip(lp(mix, 6500) * 0.9, 1.3)
    return norm(reverb(mix, wet=0.32, length=3.2, decay=0.9), 0.9)
