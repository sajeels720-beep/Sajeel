"""Subtitles for YouTube from a film's cue sheet: every line the audience reads or hears, in order.

Writes two files to output/<film>/:
  subtitles.srt   timed captions (YouTube Studio > Subtitles > Add > Upload file > With timing)
  transcript.txt  the same lines without times (YouTube Studio > Subtitles > Add > Auto-sync)

Lines come from the film's cues.py: NARRATOR, WHISPERS, ROAR, COUNTDOWN and TITLE_CARD, whichever it has.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'january', 'february',
         'march', 'april', 'june', 'july', 'august', 'september', 'october', 'november', 'december']


def _sentence(s):
    """The shadow's lowercase whispers read better in subtitles as normal sentences."""
    words = [w[:1].upper() + w[1:] if w.rstrip('.,!?…').lower() in NAMES else w for w in s.split(' ')]
    s = ' '.join(words)
    return s[:1].upper() + s[1:] if s and s[0].islower() else s


def lines(cues):
    """[(start, end, text)] for every caption in the film, sorted by time, trimmed so they never overlap."""
    out = []
    for text, t0, t1 in getattr(cues, 'NARRATOR', []):
        out.append((t0, t1, text))
    for text, t0, t1, *_ in getattr(cues, 'WHISPERS', []):
        out.append((t0, t1, _sentence(text)))
    roar = getattr(cues, 'ROAR', None)
    if roar:
        out.append((roar[1], roar[2], roar[0]))
    countdown = getattr(cues, 'COUNTDOWN', [])
    for k, (word, t) in enumerate(countdown):
        end = countdown[k + 1][1] - 0.05 if k + 1 < len(countdown) else t + 1.8
        out.append((t, end, word.capitalize() if word.isupper() and len(word) < 8 else word.title()))
    for text, t0, t1 in getattr(cues, 'TITLE_CARD', []):
        out.append((t0, t1, text))
    out.sort()
    trimmed = []
    for k, (t0, t1, text) in enumerate(out):
        if k + 1 < len(out):
            t1 = min(t1, out[k + 1][0] - 0.02)
        if t1 - t0 >= 0.3:
            trimmed.append((t0, t1, text))
    return trimmed


def _stamp(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def build(film_dir, out_dir):
    film_dir, out_dir = Path(film_dir), Path(out_dir)
    sys.path.insert(0, str(film_dir))
    sys.modules.pop('cues', None)
    cues = importlib.import_module('cues')
    caps = lines(cues)
    srt = []
    for k, (t0, t1, text) in enumerate(caps, 1):
        srt.append(f'{k}\n{_stamp(t0)} --> {_stamp(t1)}\n{text}\n')
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'subtitles.srt').write_text('\n'.join(srt), encoding='utf-8')
    (out_dir / 'transcript.txt').write_text('\n'.join(text for _, _, text in caps) + '\n', encoding='utf-8')
    return out_dir / 'subtitles.srt'
