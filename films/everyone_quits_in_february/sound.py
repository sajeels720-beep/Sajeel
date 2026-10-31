"""Soundtrack for 'Everyone Quits in February.': score, effects, voices and the mix.

The score is built on two tunes. The resolution theme is the January crowd's bright little tune: it never gets
to finish (the first quitter cuts it off a note before home) until the very last chord of the film. The regular's
theme belongs to the old man: a music box in the old photos, a cello when he nods, the anthem of the year.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import numpy as np  # noqa: E402

from audio import sfx, voices  # noqa: E402
from audio.dsp import SR, bp, ffmpeg_filter, hp, lp, norm, read_wav, reverb, secs, stereo, write_wav  # noqa: E402
from audio.mix import Mix  # noqa: E402
from audio.score import Score, chord, n  # noqa: E402
from cues import COUNTDOWN, DURATION, EV, WHISPERS  # noqa: E402

BANNER_TEAR = 42.5   # the last day: the NEW YEAR. NEW ME. banner's right hook gives

# stems and their channels
PIANO, GLOCK, CELESTA, MBOX, HARP = 0, 1, 2, 3, 4          # 'keys'
PIZZ, CELLO, STR, TREM, VIOLIN = 0, 1, 2, 3, 4              # 'strings'
CHOIR, HORN, TIMP, PAD, BRASS, PAD2 = 0, 1, 2, 3, 4, 5      # 'orch'
TAIKO, BASS, DRUMS = 0, 1, 9                                # 'rhythm'

ROOT = {'G': 'G', 'D': 'D', 'Em': 'E', 'C': 'C', 'Am': 'A', 'B': 'B', 'Cmaj7': 'C', 'Am7': 'A', 'Fmaj7': 'F'}
QUAL = {'G': '', 'D': '', 'Em': 'm', 'C': '', 'Am': 'm', 'B': '', 'Cmaj7': 'maj7', 'Am7': 'm7', 'Fmaj7': 'maj7'}

# (beat, length in beats, pitch)
RESOLUTION = [(0, 1, 'D5'), (1, 1, 'G5'), (2, 1, 'A5'), (3, 1, 'B5'),          # G
              (4, 1.5, 'D6'), (5.5, 0.5, 'C6'), (6, 2, 'A5'),                  # D
              (8, 1, 'E5'), (9, 1, 'G5'), (10, 1, 'B5'), (11, 1, 'A5'),        # Em
              (12, 1.5, 'G5'), (13.5, 0.5, 'A5'), (14, 2, 'G5')]               # C ... and home
REGULAR = [(0, 2, 'B4'), (2, 1, 'A4'), (3, 1, 'G4'), (4, 3, 'E4'), (7, 1, 'D4'),          # Em  C
           (8, 2, 'G4'), (10, 1, 'A4'), (11, 1, 'B4'), (12, 4, 'A4'),                     # G   D
           (16, 2, 'B4'), (18, 1, 'C5'), (19, 1, 'D5'), (20, 3, 'E5'), (23, 1, 'D5'),     # C   D
           (24, 2, 'C5'), (26, 1, 'B4'), (27, 1, 'A4'), (28, 4, 'G4')]                    # Em  G
FEB = [(0, 1, 'B4'), (1, 1, 'E5'), (2, 1, 'F#5'), (3, 1, 'G5'), (4, 1.5, 'B5'), (5.5, 0.5, 'A5'), (6, 2, 'G5')]
LULLABY = [(0, 1, 'G5'), (1, 1, 'C6'), (2, 1, 'D6'), (3, 1, 'E6'), (4, 1.5, 'G6'), (5.5, 0.5, 'F6'), (6, 2, 'E6'),
           (8, 1, 'A5'), (9, 1, 'C6'), (10, 1, 'E6'), (11, 1, 'D6'), (12, 2, 'C6')]


def tri(name, octave=3):
    return chord(ROOT[name], QUAL[name], octave)


def low(name):
    """Bass root: octave 2, except B which sits on B1."""
    r = ROOT[name]
    return n(f'{r}1') if r == 'B' else n(f'{r}2')


def melody(s, stem, ch, t0, bpm, notes_, vel=80, cut=None, transpose=0, start_beat=0, end_beat=None, legato=0.98):
    b = 60 / bpm
    for beat, length, p in notes_:
        if beat < start_beat or (end_beat is not None and beat >= end_beat):
            continue
        t = t0 + (beat - start_beat) * b
        if cut is not None and t >= cut - 0.02:
            continue
        dur = length * b * legato
        if cut is not None:
            dur = min(dur, cut - t)
        s.note(stem, ch, t, dur, n(p) + transpose, vel)


def arpeggio(s, stem, ch, t0, dur, notes_, step, vel, pattern=(0, 1, 2, 3, 2, 1), length=None, cut=None):
    k = 0
    t = t0
    while t < t0 + dur - 1e-6:
        if cut is not None and t >= cut:
            return
        p = notes_[pattern[k % len(pattern)] % len(notes_)]
        s.note(stem, ch, t, length or step * 1.6, p, vel + (8 if k % len(pattern) == 0 else 0))
        t += step
        k += 1


ALL = {'kick', 'clap', 'hats', 'bass', 'piano', 'brass', 'strings', 'pizz'}


def groove_bar(s, tb, name, layers, cut=None, vel=1.0, taiko=False):
    """One bar (2 s at 120 BPM) of the January groove. cut: {layer: time it drops out}."""
    cut = cut or {}

    def ok(layer, t):
        return layer in layers and t < cut.get(layer, 1e9) - 0.01

    root = low(name)
    hi = tri(name, 4)
    mid = tri(name, 3)
    for k in range(4):
        t = tb + k * 0.5
        if ok('kick', t):
            s.note('rhythm', DRUMS, t, 0.1, 36, 104 * vel)
        if k in (1, 3) and ok('clap', t):
            s.note('rhythm', DRUMS, t, 0.1, 39, 86 * vel)
            s.note('rhythm', DRUMS, t, 0.1, 38, 52 * vel)
        if taiko and k in (0, 2):
            s.note('rhythm', TAIKO, t, 0.4, 'D2', (112 if k == 0 else 92) * vel)
    for k in range(8):
        t = tb + k * 0.25
        if ok('hats', t):
            s.note('rhythm', DRUMS, t, 0.06, 46 if k == 7 else 42, (62 if k % 2 == 0 else 44) * vel)
        if ok('bass', t):
            p = root + (7 if k == 7 else 0) + (12 if k in (3, 6) else 0)
            s.note('rhythm', BASS, t, 0.2, p, (94 if k % 2 == 0 else 80) * vel)
        if k % 2 == 1 and ok('piano', t):
            s.notes('keys', PIANO, t, 0.16, hi, 56 * vel)
        if ok('pizz', t):
            thin = t >= cut.get('pizz_thin', 1e9)
            if not (thin and k % 2):
                arp = [root + 12, root + 19, root + 24, mid[1] + 12]
                s.note('strings', PIZZ, t, 0.2, arp[k % 4], (40 if thin else 60) * vel)
    if ok('brass', tb):
        s.notes('orch', BRASS, tb, 0.24, mid + [mid[0] + 12], 92 * vel)
    if ok('brass', tb + 1.75):
        s.notes('orch', BRASS, tb + 1.75, 0.2, mid, 78 * vel)
    if ok('strings', tb):
        dur = min(1.98, cut.get('strings', 1e9) - tb)
        s.notes('strings', STR, tb, dur, [root + 12] + mid, 50 * vel)


def restore(s, stem, ch, t, value=127):
    s.cc(stem, ch, t, 11, value)


def compose():
    s = Score(humanize={'keys': (0.008, 5), 'strings': (0.008, 5)})
    s.program('keys', PIANO, 0, 100, 64, 60)
    s.program('keys', GLOCK, 9, 90, 72, 70)
    s.program('keys', CELESTA, 8, 92, 60, 80)
    s.program('keys', MBOX, 10, 92, 70, 80)
    s.program('keys', HARP, 46, 96, 58, 70)
    s.program('strings', PIZZ, 45, 96, 56, 60)
    s.program('strings', CELLO, 42, 104, 58, 70)
    s.program('strings', STR, 48, 100, 64, 80)
    s.program('strings', TREM, 44, 96, 64, 80)
    s.program('strings', VIOLIN, 40, 92, 72, 80)
    s.program('orch', CHOIR, 52, 96, 64, 90)
    s.program('orch', HORN, 60, 100, 60, 70)
    s.program('orch', TIMP, 47, 108, 64, 60)
    s.program('orch', PAD, 89, 90, 64, 90)
    s.program('orch', BRASS, 61, 96, 68, 50)
    s.program('orch', PAD2, 94, 70, 60, 90)
    s.program('rhythm', TAIKO, 116, 110, 64, 50)
    s.program('rhythm', BASS, 33, 104, 64, 30)
    s.program('rhythm', DRUMS, 0, 100, 64, 40)

    # --- 0-6: three, two, one ... midnight -----------------------------------------------------------------
    for k, t in enumerate(EV['count']):
        s.note('orch', TIMP, t, 0.6, 'G2', 80 + 12 * k)
        s.notes('keys', PIANO, t, 0.9, ['G1', 'G2'], 60 + 8 * k)
        s.note('rhythm', DRUMS, t, 0.3, [45, 47, 50][k], 74 + 10 * k)
    s.ramp('strings', STR, 1.0, 3.95, 20, 120)
    s.notes('strings', STR, 1.0, 2.95, ['D3', 'G3', 'B3', 'D4'], 70)
    for k in range(16):
        s.note('rhythm', DRUMS, 3.0 + k * 0.0625, 0.05, 38, 40 + 4 * k)
    mid = EV['midnight']
    s.cc('strings', STR, mid - 0.02, 11, 112)
    s.note('rhythm', DRUMS, mid, 2.0, 49, 112)
    s.note('orch', TIMP, mid, 1.0, 'G2', 118)
    s.notes('orch', BRASS, mid, 1.6, ['G3', 'B3', 'D4', 'G4'], 108)
    s.notes('strings', STR, mid, 2.1, ['G2', 'D3', 'G3', 'B3', 'D4'], 96)
    s.notes('orch', CHOIR, mid, 2.0, ['G4', 'B4', 'D5'], 84)
    for k, p in enumerate(['G5', 'B5', 'D6', 'G6', 'B6', 'D7']):
        s.note('keys', GLOCK, mid + k * 0.08, 0.8, p, 86 - 4 * k)
    s.ramp('strings', STR, 4.3, 5.9, 112, 40)
    restore(s, 'strings', STR, 5.98)
    for k in range(4):
        s.note('rhythm', DRUMS, 5.5 + k * 0.125, 0.1, 38, 70 + 8 * k)

    # --- 6-44: the January groove; one instrument leaves with every quitter --------------------------------------
    prog = ['G', 'D', 'Em', 'C', 'G', 'D', 'Em', 'C', 'G', 'D', 'Em', 'C', 'Em', 'C', 'G', 'D', 'Em', 'C', 'B']
    taps = [d + EV['tap'] for d in EV['days']]
    # the tune goes first, then the beat itself, then the brass and piano, the bass, the strings
    drops = {'glock': taps[0], 'kick': taps[1], 'hats': taps[1], 'clap': taps[1], 'brass': taps[2],
             'piano': taps[2], 'bass': taps[3], 'strings': taps[4], 'pizz_thin': taps[5]}
    for b, name in enumerate(prog):
        tb = 6.0 + 2.0 * b
        groove_bar(s, tb, name, ALL, drops)
    for t in (6.0, 14.0):
        s.note('rhythm', DRUMS, t, 1.5, 49, 100)
    # the resolution theme on glockenspiel (and a soft violin under it), twice: cut off a note before home
    for t0 in (6.0, 14.0):
        melody(s, 'keys', GLOCK, t0, 120, RESOLUTION, vel=88, cut=drops['glock'], end_beat=14)
        melody(s, 'strings', VIOLIN, t0, 120, RESOLUTION, vel=54, transpose=-12, cut=drops['glock'], end_beat=14)
    # the fill and flash for the photo
    for k in range(4):
        s.note('rhythm', DRUMS, 17.5 + k * 0.125, 0.1, 38, 72 + 8 * k)
    s.note('rhythm', DRUMS, EV['photo_flash'], 1.5, 49, 96)
    # each tap: a low, dark knock in the orchestra under the shoulder tap
    for t in taps:
        s.note('orch', TIMP, t, 0.8, 'E2', 70)
    # the last bars before February: only the pizzicato is left, slowing, in E minor
    s.notes('orch', PAD, 41.0, 2.8, ['B2', 'F#3'], 30)

    # --- 44-58: February: a lonely piano; the tap; a drone that won't let go ---------------------------------------
    tap = EV['tap_hero']
    melody(s, 'keys', PIANO, 44.2, 60, FEB, vel=70, cut=tap)
    s.notes('keys', PIANO, 44.2, 4.0, ['E2', 'B2'], 56)
    s.notes('keys', PIANO, 48.2, tap - 48.2, ['C2', 'G2'], 54)
    s.notes('orch', PAD, 44.2, tap - 44.2, ['E3', 'B3'], 34)
    s.note('orch', TIMP, tap, 1.2, 'E2', 92)
    s.ramp('strings', TREM, tap, tap + 3.0, 30, 100)
    s.notes('strings', TREM, tap, 57.55 - tap, ['E2', 'B2'], 70)
    s.notes('strings', TREM, tap + 0.6, 57.55 - tap - 0.6, ['F5', 'G5'], 40)
    s.ramp('orch', PAD, tap - 0.1, tap + 0.6, 30, 84)
    s.notes('orch', PAD, tap, 57.55 - tap, ['E2', 'B2', 'E3'], 50)
    s.ramp('strings', TREM, 57.2, 57.55, 100, 0)
    s.ramp('orch', PAD, 57.2, 57.55, 84, 0)
    restore(s, 'strings', TREM, 57.9)

    # --- 58-72: the photos (music box), the nod (cello, G major), the fist ---------------------------------------
    restore(s, 'orch', PAD, 57.95, 0)
    s.ramp('orch', PAD, 58.0, 58.8, 0, 64)
    melody(s, 'keys', MBOX, 58.3, 80, REGULAR, vel=72, end_beat=7)
    s.notes('orch', PAD, 58.3, 3.0, tri('Em', 3), 44)
    s.notes('orch', PAD, 61.3, 2.6, tri('C', 3), 44)
    s.notes('orch', PAD, 63.6, 1.3, ['D3', 'A3', 'D4'], 46)
    s.ramp('orch', PAD, 63.6, 64.6, 64, 30)
    s.ramp('strings', STR, 62.6, 64.75, 20, 70)
    s.notes('strings', STR, 62.6, 2.15, ['D3', 'A3'], 56)
    melody(s, 'strings', CELLO, 64.8, 80, REGULAR, vel=84, transpose=-12, start_beat=8, end_beat=18, cut=72.0)
    for name, t0, d in (('G', 64.8, 3.0), ('D', 67.8, 3.0), ('C', 70.8, 1.15)):
        s.notes('strings', STR, t0, d, [low(name) + 12] + tri(name, 3), 52)
    s.ramp('strings', STR, 64.8, 66.0, 60, 96)
    for k, p in enumerate(['G3', 'B3', 'D4', 'G4', 'B4', 'D5', 'G5']):
        s.note('keys', HARP, EV['nod'] + k * 0.06, 1.6, p, 70 - 2 * k)
    s.note('orch', TIMP, EV['fist'], 0.9, 'G2', 92)
    s.note('rhythm', TAIKO, EV['fist'], 0.6, 'D2', 96)

    # --- 70-74: back to the bench: the pulse, the riser, one beat of silence --------------------------------------
    for k in range(7):
        s.notes('strings', STR, 70.4 + k * 0.25, 0.2, ['G2', 'G3'], 50 + 6 * k)
    s.ramp('strings', TREM, 72.0, 73.8, 30, 127)
    for t0, notes_ in ((72.0, ['G3', 'B3', 'D4']), (72.6, ['A3', 'C4', 'E4']), (73.2, ['B3', 'D4', 'F#4'])):
        s.notes('strings', TREM, t0, 0.6 if t0 < 73 else 0.62, notes_, 84)
    for k in range(28):
        s.note('rhythm', DRUMS, 72.1 + k * (1.7 / 28), 0.05, 38, 40 + 2.5 * k)
    for k in range(16):
        s.note('orch', TIMP, 72.6 + k * 0.075, 0.08, 'G2', 50 + 3 * k)

    # --- 74-102: the drop and the year: the groove again, heavier, and the old man's theme on top -----------------
    year = {74: 'G', 76: 'D', 78: 'Em', 80: 'C', 82: 'Em', 84: 'C', 86: 'G', 88: 'D', 90: 'C', 92: 'D', 94: 'Em',
            96: 'G', 98: 'C', 100: 'D'}
    for tb, name in year.items():
        tb = float(tb)
        if tb < 78:
            layers, tk = ALL, True
        elif tb < 82:
            layers, tk = {'kick', 'hats', 'bass', 'pizz', 'piano'}, False
        elif tb < 94:
            layers, tk = ALL - {'brass'}, True
        else:
            layers, tk = ALL, True
        groove_bar(s, tb, name, layers, taiko=tk, cut={'brass': 101.9, 'kick': 101.9})
        if tb >= 94 or tb == 74:
            s.notes('orch', CHOIR, tb, 1.98, tri(name, 4), 64)
    s.note('rhythm', DRUMS, EV['drop'], 2.0, 49, 118)
    s.note('orch', TIMP, EV['drop'], 1.0, 'G2', 120)
    s.notes('orch', BRASS, EV['drop'], 1.2, ['G2', 'G3', 'B3', 'D4', 'G4'], 112)
    for t in (78.0, 82.0, 94.0, 98.0):
        s.note('rhythm', DRUMS, t, 1.5, 49, 100)
    for k, drum in enumerate((50, 48, 47, 45)):
        s.note('rhythm', DRUMS, 77.5 + k * 0.125, 0.1, drum, 84 + 6 * k)
    s.ramp('orch', HORN, 81.9, 82.0, 100, 110)
    melody(s, 'orch', HORN, 82.0, 120, REGULAR, vel=100)
    melody(s, 'strings', VIOLIN, 90.0, 120, REGULAR, vel=78, transpose=12, start_beat=16)
    melody(s, 'strings', CELLO, 82.0, 120, REGULAR, vel=70, transpose=-12, end_beat=16)
    # a big finish into the goodbye: D held, a timpani roll, then let go
    s.notes('strings', STR, 100.0, 1.9, ['D3', 'A3', 'D4', 'F#4'], 92)
    s.notes('orch', CHOIR, 100.0, 1.9, ['D4', 'F#4', 'A4'], 80)
    for k in range(20):
        s.note('orch', TIMP, 100.4 + k * 0.07, 0.08, 'D2', 60 + 2 * k)

    # --- 102-106: the goodbye: the theme's last phrase, warm and quiet ---------------------------------------------
    melody(s, 'strings', CELLO, 102.0, 120, REGULAR, vel=80, transpose=-12, start_beat=24)
    s.notes('keys', PIANO, 102.0, 2.0, ['C2'] + tri('C', 3), 54)
    s.notes('keys', PIANO, 104.0, 2.0, ['G1'] + tri('G', 3), 52)
    s.notes('strings', STR, 102.0, 2.0, ['C3', 'G3', 'E4'], 46)
    s.notes('strings', STR, 104.0, 2.0, ['G2', 'D3', 'B3'], 44)
    for k, p in enumerate(['G3', 'B3', 'D4', 'G4', 'B4', 'D5']):
        s.note('keys', HARP, EV['pat'] + k * 0.07, 1.4, p, 64 - 2 * k)

    # --- 106-122: New Year's Eve: quiet; the lullaby; the towel; the refusal; the lift ----------------------------------
    restore(s, 'orch', PAD, 105.9, 50)
    s.notes('orch', PAD, 106.0, 4.0, ['C3', 'G3', 'E4'], 54)
    for k, p in enumerate(['E5', 'G4', 'D5', 'C5']):
        s.note('keys', PIANO, 106.4 + k * 0.9, 1.6, p, 56)
    # "you've done enough": sweet and slow on celesta, a warm pad, and a second pad a little out of tune
    s.ramp('orch', PAD, 109.8, 110.4, 50, 70)
    melody(s, 'keys', CELESTA, 110.2, 75, LULLABY, vel=72, cut=116.0)
    for name, t0, d in (('Cmaj7', 110.2, 2.4), ('Am7', 112.6, 2.4), ('Fmaj7', 115.0, 0.98)):
        s.notes('orch', PAD, t0, d, tri(name, 3), 52)
        s.notes('orch', PAD2, t0, d, tri(name, 4), 40)
    s.bend('orch', PAD2, 110.0, 380)
    s.bend('orch', PAD2, 116.2, 0)
    # the towel: the cello remembers the theme
    melody(s, 'strings', CELLO, 116.1, 80, REGULAR, vel=74, transpose=-12, start_beat=8, end_beat=12, cut=118.2)
    s.notes('strings', STR, 116.1, 2.05, ['G2', 'D3', 'B3'], 44)
    s.note('keys', MBOX, 117.2, 0.8, 'D6', 62)
    s.note('keys', MBOX, 117.5, 0.8, 'B5', 56)
    # no: the strings climb
    s.ramp('strings', TREM, 118.2, 120.7, 30, 127)
    for t0, notes_ in ((118.2, ['G3', 'B3', 'D4']), (119.0, ['A3', 'C4', 'E4']), (119.8, ['B3', 'D4', 'F#4'])):
        s.notes('strings', TREM, t0, 0.8 if t0 < 119.5 else 0.96, notes_, 84)
    for k in range(13):
        s.note('orch', TIMP, 119.85 + k * 0.07, 0.08, 'D2', 56 + 4 * k)
    # lockout: everything, G major; the shadow goes to smoke under it
    hit = 120.8
    restore(s, 'strings', STR, hit - 0.05)
    s.note('rhythm', DRUMS, hit, 2.0, 49, 120)
    s.note('rhythm', TAIKO, hit, 0.8, 'D2', 122)
    s.note('orch', TIMP, hit, 1.0, 'G2', 122)
    s.notes('orch', BRASS, hit, 1.1, ['G2', 'G3', 'B3', 'D4', 'G4'], 112)
    s.ramp('orch', CHOIR, hit, hit + 0.2, 60, 116)
    s.notes('orch', CHOIR, hit, 1.15, ['G3', 'D4', 'G4', 'B4'], 92)
    s.notes('strings', STR, hit, 1.15, ['G2', 'D3', 'G3', 'B3', 'D4', 'G4'], 100)
    s.ramp('strings', STR, 121.3, 121.95, 127, 50)
    restore(s, 'strings', STR, 121.98)
    restore(s, 'strings', TREM, 121.0)

    # --- 122-148: midnight; January 1st again; the nod; the photo; the finale ---------------------------------------------
    s.ramp('orch', CHOIR, 122.0, 123.0, 40, 100)
    s.notes('orch', CHOIR, 122.0, 1.95, ['G4', 'B4', 'D5'], 70)
    s.notes('strings', STR, 122.0, 1.95, ['G2', 'D3', 'B3', 'G4'], 66)
    for k, p in enumerate(['G5', 'D6', 'B5', 'G6', 'D6', 'B6']):
        s.note('keys', GLOCK, 122.1 + k * 0.3, 0.9, p, 66)
    for k in range(4):
        s.note('rhythm', DRUMS, 123.5 + k * 0.125, 0.1, 38, 70 + 8 * k)
    prog2 = {124: 'G', 126: 'D', 128: 'Em', 130: 'C', 132: 'G', 134: 'D', 136: 'Em', 138: 'C', 140: 'G'}
    stop = {layer: EV['photo_flash2'] for layer in ALL}
    for tb, name in prog2.items():
        tb = float(tb)
        if 132 <= tb < 138:
            groove_bar(s, tb, name, {'bass', 'pizz', 'strings'}, vel=0.75)
        else:
            groove_bar(s, tb, name, ALL, cut=stop)
    s.note('rhythm', DRUMS, 124.0, 1.5, 49, 104)
    for t0 in (124.0,):
        melody(s, 'keys', GLOCK, t0, 120, RESOLUTION, vel=86, cut=131.9, end_beat=14)
        melody(s, 'orch', HORN, t0, 120, RESOLUTION, vel=70, transpose=-12, cut=131.9, end_beat=14)
    # the newcomer at the door: a low drone when the shadow's eyes show
    s.ramp('orch', PAD, 133.2, 134.0, 20, 80)
    s.notes('orch', PAD, 133.4, 2.4, ['E2', 'B2'], 50)
    s.ramp('orch', PAD, 135.4, 135.9, 80, 30)
    # the nod: the old man's theme passes to the hero
    melody(s, 'orch', HORN, 135.0, 80, REGULAR, vel=86, start_beat=8, end_beat=12, cut=138.0)
    for k, p in enumerate(['G3', 'B3', 'D4', 'G4', 'B4', 'D5', 'G5']):
        s.note('keys', HARP, EV['nod2'] + k * 0.06, 1.6, p, 72 - 2 * k)
    for k, p in enumerate(['D6', 'G6']):
        s.note('keys', GLOCK, EV['step_in'] + k * 0.25, 0.8, p, 64)
    melody(s, 'keys', GLOCK, 138.0 - 6.0, 120, RESOLUTION, vel=84, start_beat=12, end_beat=14)
    s.note('rhythm', DRUMS, 138.0, 1.5, 49, 104)
    s.note('rhythm', DRUMS, EV['photo_flash2'], 1.5, 49, 106)
    # the finale: the old man's last phrase, slow and full; home on G as the new photo goes up
    t0 = 141.2
    for stem, ch, tr, v in (('orch', HORN, 0, 104), ('strings', VIOLIN, 12, 84), ('strings', CELLO, -12, 84)):
        melody(s, stem, ch, t0, 80, REGULAR, vel=v, transpose=tr, start_beat=24)
    s.notes('strings', STR, t0, 1.5, ['C3', 'G3', 'E4'], 80)
    s.notes('strings', STR, t0 + 1.5, 1.5, ['E3', 'B3', 'G4'], 80)
    s.notes('orch', CHOIR, t0, 3.0, ['E4', 'G4', 'C5'], 70)
    for k in range(14):
        s.note('orch', TIMP, 143.2 + k * 0.07, 0.08, 'D2', 54 + 3 * k)
    home = 144.2
    s.note('rhythm', DRUMS, home, 2.5, 49, 110)
    s.note('orch', TIMP, home, 1.2, 'G2', 116)
    s.notes('strings', STR, home, 3.7, ['G2', 'D3', 'G3', 'B3', 'D4', 'G4'], 96)
    s.notes('orch', CHOIR, home, 3.7, ['G3', 'D4', 'G4', 'B4'], 84)
    s.notes('orch', BRASS, home, 1.6, ['G2', 'G3', 'B3', 'D4'], 100)
    s.notes('keys', PIANO, home, 3.7, ['G1', 'G2', 'D3', 'B3'], 70)
    for stem, ch in (('strings', STR), ('orch', CHOIR), ('strings', VIOLIN), ('orch', HORN)):
        s.ramp(stem, ch, 146.2, 147.85, 127, 20)

    # --- 148-160: the title: and this time the resolution gets home -----------------------------------------------------
    for stem, ch in (('strings', STR), ('orch', CHOIR), ('strings', VIOLIN), ('orch', HORN)):
        restore(s, stem, ch, 148.1)
    restore(s, 'orch', PAD, 148.2, 70)
    for name, t, d in (('G', 149.0, 4.0), ('D', 153.0, 4.0), ('G', 157.0, 3.0)):
        s.notes('keys', PIANO, t, d, [low(name)] + tri(name, 3), 46)
        s.notes('orch', PAD, t, d, tri(name, 3), 42)
    melody(s, 'keys', GLOCK, 149.0, 60, RESOLUTION, vel=80, end_beat=8)
    s.note('keys', GLOCK, 157.0, 3.0, 'G5', 84)
    s.note('keys', GLOCK, 157.0, 3.0, 'G6', 50)
    s.ramp('orch', PAD, 157.6, 160.0, 70, 10)
    s.ramp('keys', PIANO, 158.4, 160.0, 127, 60)
    return s


def step_times(t0, t1, speed):
    """Heel strikes of rig.walk(T, speed) or rig.run: a leg reaches full stride at T = (0.25 + 0.5 k) / speed."""
    k = math.ceil(t0 * speed * 2 - 0.5)
    out = []
    while True:
        t = (0.25 + 0.5 * k) / speed
        if t > t1:
            return out
        if t >= t0:
            out.append(t)
        k += 1


def steps(mx, t0, t1, speed, gain=-14, seed=0, pan=0.0, kind=None):
    for k, t in enumerate(step_times(t0, t1, speed)):
        x = kind(seed + k) if kind else sfx.footstep(False, seed + k)
        mx.add('sfx', x, t, gain, pan=pan + 0.12 * (1 if k % 2 else -1))


def pan_x(x):
    return max(-0.85, min(0.85, (x - 960) / 960))


# --- effects, ambience and voices on the timeline --------------------------------------------------------------

def gym_bed(mx, t0, t1, voices=14, level=0.45, clanks=16, seed=0, treads=1.0):
    """A busy gym: chatter, treadmills, iron."""
    d = t1 - t0
    if voices:
        mx.add('amb', sfx.murmur(d, voices, seed, level), t0, -4, fade_in=0.2, fade_out=0.3)
    if treads > 0:
        mx.add('amb', sfx.treadmill(d, seed, 0.2 * treads), t0, -6, fade_in=0.2, fade_out=0.3)
    r = np.random.default_rng(seed)
    for k in range(clanks):
        t = t0 + r.uniform(0.2, d - 0.3)
        mx.add('sfx', sfx.clank(seed + k, r.uniform(0.8, 1.3)), t, r.uniform(-24, -17), pan=r.uniform(-0.8, 0.8))


def place_sfx(mx):
    add = mx.add
    # midnight: the city, a crowd on the rooftops, the countdown, fireworks
    add('amb', sfx.city(6.4, 13, 0.12), 0.0, -2, fade_in=0.8, fade_out=0.3)
    add('amb', sfx.murmur(4.2, 24, 3, 0.5), 0.0, -2, fade_in=1.5, fade_out=0.3)
    for k, t in enumerate(EV['count']):
        add('sfx', sfx.whoosh(0.35, 400, 2600, 40 + k), t - 0.25, -16)
    add('sfx', sfx.reverse_swell(1.0, 4), EV['midnight'] - 1.0, -12)
    add('sfx', sfx.crowd_cheer(2.6, 5, 0.7), EV['midnight'], 0, fade_out=0.5)
    add('amb', sfx.crowd_cheer(2.4, 6, 0.6), EV['midnight'] + 0.1, -2, pan=0.5, fade_out=0.5)
    for k, (t, p) in enumerate(((4.35, -0.7), (4.8, 0.6), (5.4, -0.3))):
        add('sfx', sfx.car_horn(7 + k), t, -14, pan=p)
    for t0, x, y, k in EV['volley']:
        add('sfx', sfx.firework_boom(40 + k), t0 + 0.05, -4 - 0.8 * (k - 6), pan=pan_x(x), max_len=6.2 - t0 + 0.3,
            fade_out=0.2)
    for t0, x, y, k in EV['bursts']:
        add('sfx', sfx.firework_launch(10 + k), t0 - 0.68, -18, pan=pan_x(x))
        add('sfx', sfx.firework_boom(20 + k), t0, -2 - 1.0 * k, pan=pan_x(x), max_len=6.2 - t0 + 0.3,
            fade_out=0.2)

    # January 1st: the doors, the rush, the busy gym, the photo
    add('sfx', sfx.door(True, 31), EV['doors'], -2, pan=-0.6)
    add('sfx', sfx.whoosh(0.5, 300, 2000, 32), EV['doors'] - 0.1, -12, pan=-0.5)
    for k in range(9):
        t0 = 6.4 + (0.35 if k else 0) + 0.3 * max(0, k - 1)
        steps(mx, t0, min(t0 + 2.6, 9.0), 1.25, -22, seed=100 + 7 * k, pan=-0.4)
    gym_bed(mx, EV['doors'], 20.0, voices=16, level=0.5, clanks=22, seed=1)
    for k, t in enumerate(np.arange(9.0, 20.0, 1 / 2.3)):
        add('sfx', sfx.rope_turn(200 + k), float(t), -24, pan=-0.75)
    add('sfx', sfx.shutter(33), EV['photo_flash'], -2)
    add('sfx', sfx.whoosh(0.6, 2000, 400, 34), EV['photo_flash'] + 0.4, -16)

    # the vanishing: each day a little emptier; a tap; a voice; smoke; something hits the floor
    pans = [0.2, -0.58, -0.17, -0.5, 0.3, 0.72]
    drops = [None, ('dumbbell', -0.58), ('phone', -0.15), ('bar', -0.5), ('bottle', 0.35), ('towel', 0.72)]
    for k, d in enumerate(EV['days']):
        if k:
            add('sfx', sfx.whoosh(0.35, 400, 3000, 50 + k), d - 0.18, -18)
        gym_bed(mx, d, d + 4.0, voices=max(0, 12 - 2 * k), level=0.45 - 0.06 * k, clanks=max(1, 7 - k),
                seed=60 + k, treads=[1.0, 0.7, 0.5, 0.35, 0.2, 0.0][k])
        tap = d + EV['tap']
        add('sfx', sfx.shoulder_tap(70 + k), tap, -3, pan=pans[k])
        add('sfx', sfx.poof(80 + k), tap + 0.5, -3, pan=pans[k])
        if k == 4:
            add('sfx', sfx.poof(90), tap + 0.55, -6, pan=0.4)
            add('sfx', sfx.bar_rack(91), tap + 0.9, -8, pan=0.2)
        if drops[k]:
            kind, p = drops[k]
            t = tap + 0.9
            if kind == 'dumbbell':
                add('sfx', sfx.dumbbell_drop(92), t, -4, pan=p)
            elif kind == 'phone':
                add('sfx', sfx.thud(93, 0.35), t, -8, pan=p)
            elif kind == 'bar':
                add('sfx', sfx.clank(94, 1.4), t, -4, pan=p)
            elif kind == 'bottle':
                add('sfx', sfx.thud(95, 0.3), t, -10, pan=p)
                add('sfx', sfx.tap(96), t + 0.25, -14, pan=p)
            elif kind == 'towel':
                add('sfx', sfx.thud(97, 0.2), t, -14, pan=p)
    add('sfx', sfx.whoosh(1.0, 1200, 200, 98), 23.2, -20, pan=0.2)   # the empty treadmill winding down
    add('sfx', sfx.tape_rip(0.35, 99), BANNER_TEAR, -6, pan=0.5)     # the NEW YEAR banner tears loose
    add('sfx', sfx.whoosh(0.8, 300, 900, 99), BANNER_TEAR + 0.1, -12, pan=0.5)

    # February 12th
    feb = EV['feb']
    add('amb', sfx.wind(14.0, 101, 0.3), feb, -4, fade_in=0.5, fade_out=0.5)
    add('amb', sfx.light_buzz(14.0, 102, 0.06, flicker=[1.3, 1.5, 4.2, 6.8, 7.0, 9.9]), feb, -10, fade_out=0.4)
    for t in (45.6, 47.6):
        add('sfx', sfx.clank(103 + int(t), 1.2), t, -16, pan=0.2)
    add('sfx', sfx.breath_in(104), 46.2, -18)
    add('sfx', sfx.bar_rack(105), 48.6, -10, pan=0.2)
    tap = EV['tap_hero']
    add('sfx', sfx.shoulder_tap(106), tap, 0)
    add('sfx', sfx.thoom(107), tap + 0.05, -6)
    add('sfx', sfx.heartbeat(78, 7.8, 108), 50.0, -6, fade_in=0.6, fade_out=0.5)
    add('sfx', sfx.poof(109, 2.4), EV['smoke'], -5, pan=0.3)
    add('sfx', sfx.sizzle(2.0, 9), EV['smoke'] + 0.1, -6, pan=0.3)
    add('sfx', sfx.tinnitus(2.0, 110), EV['smoke'], -16)
    add('sfx', sfx.thud(111, 0.5), EV['stand_up'] + 0.5, -14)
    steps(mx, EV['walk_out'] + 0.1, EV['stop'] - 0.05, 0.85, -14, seed=112, pan=-0.2)

    # the photos, the turn, the nod, the fist
    add('amb', sfx.room_tone(14.0, 113, 0.05), 58.0, -6, fade_in=0.5, fade_out=0.5)
    add('amb', sfx.wind(14.0, 114, 0.12), 58.0, -14, fade_in=0.5, fade_out=0.5)
    add('sfx', sfx.whoosh(0.5, 300, 1500, 115), EV['turn'] + 0.1, -18)
    add('sfx', sfx.clank(116, 0.9), EV['nod'] - 0.5, -12, pan=0.6)
    add('sfx', sfx.reverse_swell(0.8, 117), EV['hand_back'] - 0.6, -10)
    add('sfx', sfx.thoom(117), EV['hand_back'] + 0.6, -6)
    add('sfx', sfx.breath_in(117), EV['hand_back'] - 0.2, -10)
    add('sfx', sfx.impact(118), EV['fist'], -8)
    add('sfx', sfx.impact(119), EV['shrug'], -8)
    add('sfx', sfx.whoosh(0.4, 500, 2200, 119), EV['shrug'], -6)
    add('sfx', sfx.poof(120, 1.2, dark=True), EV['shrug'] + 0.1, -4, pan=-0.3)
    add('sfx', sfx.reverse_swell(0.5, 120)[::-1].copy(), EV['shrug'] + 0.1, -10, pan=-0.3)
    add('sfx', sfx.thud(121, 1.1), EV['drop_bag'] + 0.2, -6)
    steps(mx, 70.5, 71.95, 1.1, -14, seed=122)

    # the bench: the old man comes over; the push; the drop
    steps(mx, 72.1, 72.9, 1.0, -18, seed=123, pan=0.3)
    add('sfx', sfx.clank(124, 1.2), 72.4, -12)
    add('sfx', sfx.clank(125, 1.3), EV['push'], -10)
    add('sfx', sfx.heartbeat(110, 1.1, 125), 72.9, -8)
    add('sfx', sfx.grunt(125), EV['drop'] - 0.45, -6)
    add('sfx', sfx.impact(126), EV['drop'], -4)
    add('sfx', sfx.drop_boom(127), EV['drop'], -6)
    add('sfx', sfx.clank(127, 1.3), EV['drop'], -8)
    for t in (75.0, 76.0, 77.0):
        add('sfx', sfx.clank(128 + int(t), 1.1), t, -16)
    # the struggle: the pull-up bar, a gasp; the rope, the trip
    add('sfx', sfx.breath_in(130), 78.1, -16)
    add('sfx', sfx.clank(131, 0.7), 78.3, -20)
    add('sfx', sfx.whoosh(0.3, 300, 1200, 132), 78.9, -18)
    for k, t in enumerate(np.arange(80.0, 81.0, 1 / 1.4)):
        add('sfx', sfx.rope_turn(133 + k), float(t), -16)
    add('sfx', sfx.whoosh(0.4, 600, 2400, 136), 81.0, -12)
    add('sfx', sfx.thud(137, 0.8), 81.3, -8)

    # the run: snow, rain, spring, summer, autumn; his feet in each
    for t in step_times(82.0, 94.0, 1.65):
        if t < 84.0:
            add('sfx', sfx.snow_step(int(t * 10)), t, -14, pan=-0.1)
        elif t < 85.3:
            add('sfx', sfx.splash_step(int(t * 10)), t, -14, pan=-0.1)
        else:
            add('sfx', sfx.footstep(False, int(t * 10)), t, -16, pan=-0.1)
    add('amb', sfx.wind(2.4, 140, 0.3), 82.0, -6, fade_in=0.2, fade_out=0.5)
    add('amb', sfx.rain(2.0, 141, 0.3), 83.8, -6, fade_in=0.3, fade_out=0.5)
    add('amb', sfx.birds(3.4, 142, 0.2), 85.2, -6, fade_in=0.4, fade_out=0.6)
    add('amb', sfx.cicadas(3.4, 143, 0.12), 87.3, -8, fade_in=0.4, fade_out=0.6)
    add('amb', sfx.rustle(3.6, 144, 0.2), 90.2, -6, fade_in=0.4, fade_out=0.5)
    add('amb', sfx.wind(2.2, 145, 0.25), 92.2, -8, fade_in=0.4, fade_out=0.4)
    for t in (83.3, 88.4):
        add('sfx', sfx.poof(146 + int(t), 1.0, dark=True), t, -12, pan=0.4)

    # strong: pull-ups, rope, deadlift, spotting him
    for k, t in enumerate(np.arange(94.2, 96.0, 1 / 1.4)):
        add('sfx', sfx.clank(150 + k, 0.7), float(t), -22)
    for k, t in enumerate(np.arange(96.0, 98.0, 1 / 3.2)):
        add('sfx', sfx.rope_turn(160 + k), float(t), -16)
    add('sfx', sfx.clank(170, 1.4), 98.45, -8)
    add('sfx', sfx.thud(171, 1.2), 99.95, -6)
    add('sfx', sfx.clank(172, 1.3), 99.97, -10)
    add('sfx', sfx.clank(173, 1.1), 100.9, -16)

    # the goodbye: footsteps, a pat, the door and the snow
    steps(mx, 102.6, 103.3, 0.9, -18, seed=174, pan=0.3)
    steps(mx, 103.9, 104.7, 0.9, -18, seed=175, pan=-0.3)
    add('sfx', sfx.tap(176), EV['pat'], -10)
    add('sfx', sfx.door(True, 177), 104.4, -12, pan=-0.7)
    add('amb', sfx.wind(1.6, 178, 0.35), 104.5, -8, fade_in=0.2, fade_out=0.4)
    add('sfx', sfx.door(False, 179), 105.6, -10, pan=-0.7)

    # New Year's Eve: the clock, the hum, the wind; the shadow; the chalk; the lift; midnight
    add('amb', sfx.room_tone(16.0, 180, 0.05), 106.0, -4, fade_in=0.3)
    add('amb', sfx.light_buzz(16.0, 181, 0.05), 106.0, -12)
    add('amb', sfx.wind(16.0, 182, 0.12), 106.0, -14)
    for k in range(16):
        add('sfx', sfx.tick(k % 2 == 1, 183 + k), 106.0 + k, -16, pan=-0.4)
    add('sfx', sfx.clank(184, 1.4), 106.35, -10)
    add('sfx', sfx.thud(185, 1.2), 108.3, -8)
    add('sfx', sfx.clank(186, 1.3), 108.32, -12)
    steps(mx, 108.4, 109.6, 0.9, -16, seed=187)
    add('sfx', sfx.thud(188, 0.4), 110.2, -18)
    add('sfx', sfx.poof(189, 1.6), EV['hand_smoke2'], -6, pan=0.3)
    add('sfx', sfx.sizzle(1.6, 10), EV['hand_smoke2'] + 0.1, -8, pan=0.3)
    add('sfx', sfx.tinnitus(2.0, 190), EV['hand_smoke2'], -14)
    add('sfx', sfx.whoosh(0.3, 3000, 600, 191), 117.05, -12)
    add('sfx', sfx.shimmer(0.8, 192, 20), 117.15, -14)
    add('sfx', sfx.whoosh(0.3, 500, 1800, 193), 118.2, -14)
    steps(mx, 118.6, 118.95, 1.0, -16, seed=194)
    add('sfx', sfx.chalk_clap(195), EV['chalk'], -4)
    add('sfx', sfx.tap(196), EV['lift2'], -14)
    add('sfx', sfx.breath_in(197), 119.5, -16)
    add('sfx', sfx.impact(200), 120.8, -4)
    add('sfx', sfx.clank(201, 1.5), 120.8, -8)
    add('sfx', sfx.whoosh(0.7, 300, 3000, 198), 120.8, -6)
    add('sfx', sfx.chalk_clap(198), 120.82, -8)
    shriek = sfx.whoosh(1.4, 3200, 500, 203) + 0.4 * sfx.tinnitus(1.4, 204)[: sfx.secs(1.4)]
    add('sfx', shriek, EV['shade_gone'], -6)
    add('sfx', sfx.poof(199, 2.4, dark=True), EV['shade_gone'], 0)
    add('sfx', sfx.sizzle(1.8, 205), EV['shade_gone'] + 0.1, -6)
    add('sfx', sfx.bell(202), 122.0, -4)
    add('sfx', sfx.shimmer(1.8, 206, 40), 120.85, -6)
    add('sfx', sfx.bell(207, f0=1320.0, dur=2.5), 120.9, -10)

    # midnight through the glass, and January 1st again
    for k in range(5):
        boom = lp(sfx.firework_boom(210 + k, 2.0), 900)
        add('sfx', boom, 122.0 + k * 0.45, -8 - k, pan=0.3 * (1 if k % 2 else -1))
    add('amb', lp(sfx.crowd_cheer(2.2, 215, 0.6), 1800), 122.1, -12, fade_out=0.4)
    add('sfx', sfx.door(True, 216), EV['doors2'], -2, pan=-0.6)
    for k in range(7):
        t0 = 124.45 + 0.28 * k
        steps(mx, t0, min(t0 + 2.4, 127.0), 1.25, -22, seed=220 + 7 * k, pan=-0.4)
    gym_bed(mx, EV['doors2'], 132.0, voices=16, level=0.5, clanks=12, seed=230)
    gym_bed(mx, 132.0, EV['photo_call2'], voices=10, level=0.32, clanks=4, seed=231, treads=0.6)
    add('sfx', sfx.thoom(232), 133.4, -10, pan=-0.6)
    steps(mx, EV['step_in'], EV['step_in'] + 1.4, 0.8, -16, seed=233, pan=-0.5)
    add('sfx', sfx.poof(233, 1.2, dark=True), EV['step_in'] + 0.3, -14, pan=-0.8)
    gym_bed(mx, EV['photo_call2'], EV['photo_wall'], voices=14, level=0.45, clanks=3, seed=234)
    add('sfx', sfx.shutter(235), EV['photo_flash2'], -2)
    add('sfx', sfx.whoosh(0.6, 2000, 400, 236), EV['photo_flash2'] + 0.4, -16)
    add('sfx', sfx.whoosh(0.8, 300, 2000, 237), EV['photo_wall'], -14)
    add('sfx', sfx.tap(238), EV['photo_wall'] + 1.1, -8)
    add('amb', sfx.room_tone(5.0, 239, 0.05), EV['photo_wall'], -6, fade_in=0.4, fade_out=1.0)


# --- voices ----------------------------------------------------------------------------------------------------

VOICE_FOR = {'hiss': ['Enceladus', 'Algenib'], 'deep': ['Charon', 'Fenrir'], 'soft': ['Enceladus', 'Enceladus']}
CROWD_VOICES = [('Puck', 1.0, -0.6), ('Zephyr', 1.04, 0.5), ('Fenrir', 0.96, -0.2), ('Leda', 1.06, 0.3),
                ('Sadachbia', 0.98, 0.7)]


def split_words(x, n_words=4):
    """Split a shouted line at its n-1 longest silences."""
    env = lp(np.abs(x), 30)
    on = env > 0.06 * env.max()
    gaps = []
    i = 0
    while i < len(on):
        if not on[i]:
            j = i
            while j < len(on) and not on[j]:
                j += 1
            if i > 0 and j < len(on):
                gaps.append((j - i, i, j))
            i = j
        else:
            i += 1
    cuts = sorted(sorted(gaps, reverse=True)[: n_words - 1], key=lambda g: g[1])
    if len(cuts) < n_words - 1:
        return None
    parts, a = [], 0
    for _, i, j in cuts:
        parts.append(voices.trim_silence(x[a:(i + j) // 2]))
        a = (i + j) // 2
    parts.append(voices.trim_silence(x[a:]))
    return parts


def place_countdown(mx, work):
    """'Three! Two! One! Happy New Year!' shouted by a small crowd on the rooftops."""
    cache, tmp = work / 'tts_cache', work / 'tmp'
    line = ' '.join(w.capitalize() if w != 'HAPPY NEW YEAR!' else 'Happy New Year!' for w, _ in COUNTDOWN)
    placed = 0
    for k, (voice, pitch, pan) in enumerate(CROWD_VOICES):
        path = voices.tts(line, voice, 'shout', cache)
        if path is None:
            continue
        x = read_wav(path)
        x = x.mean(axis=1) if x.ndim == 2 else x
        parts = split_words(voices.trim_silence(x))
        if not parts:
            continue
        for (word, t), p in zip(COUNTDOWN, parts):
            for layer, (pmul, dt, pn, g) in enumerate(((1.0, 0.0, pan, 0.0), (0.92, 0.05, -pan * 0.8, -5.0))):
                pp = pitch * pmul
                y = ffmpeg_filter(p, f'rubberband=pitch={pp:.3f}', tmp) if abs(pp - 1.0) > 1e-3 else p
                y = reverb(stereo(hp(y, 120), pn, 0.4), wet=0.3 + 0.1 * layer, length=1.8, decay=0.6)
                mx.add('voice', y, t + 0.03 * k - 0.05 + dt, (-4 if k else -1) + g, fade_out=0.15)
        placed += 1
    return placed


def place_voices(mx, work):
    """Every line is whispered close and dry so it can be understood; the 'deep' ones keep the demon underneath."""
    cache = work / 'tts_cache'
    tmp = work / 'tmp'
    windows = []
    pans = [0.2, -0.5, -0.15, -0.45, 0.35, 0.6, -0.2, 0.25, 0.4, 0.4, -0.25, -0.2]
    for k, (text, t0, t1, style) in enumerate(WHISPERS):
        voice = VOICE_FOR[style][k % 2]
        fit = max(1.1, t1 - t0 + 0.3)
        if style == 'soft':
            x = voices.line(text, 'soft', voice, cache, tmp, pan=pans[k], seed=k, max_dur=fit)
            gain = 1
        else:
            x = voices.line(text, 'close', voice, cache, tmp, pan=pans[k], seed=k, max_dur=fit)
            if style == 'deep':
                d = voices.line(text, 'deep', voice, cache, tmp, pan=pans[k], seed=k, max_dur=fit)
                n_ = max(len(x), len(d))
                x = np.pad(x, ((0, n_ - len(x)), (0, 0))) + 0.32 * np.pad(d, ((0, n_ - len(d)), (0, 0)))
            gain = 0
        mx.add('voice', x, t0 + 0.02, gain, max_len=t1 - t0 + 2.0, fade_out=0.4)
        windows.append((t0, min(t1, t0 + len(x) / SR)))
    place_countdown(mx, work)
    return windows


def build(out_dir):
    out_dir = Path(out_dir)
    work = out_dir / 'audio'
    work.mkdir(parents=True, exist_ok=True)
    stems = compose().render(work / 'stems')
    mx = Mix(DURATION)
    stem_gain = {'keys': 4.0, 'strings': 2.0, 'orch': 0.5, 'rhythm': -1.5}
    for name, path in stems.items():
        mx.add('music', read_wav(path), 0.0, stem_gain.get(name, 0.0))
    place_sfx(mx)
    windows = place_voices(mx, work)
    # lift the quiet music (February's piano, the photos, the goodbye, the title) for small speakers
    steps_down = []
    for k, d in enumerate(EV['days']):
        t = d + EV['tap']
        steps_down += [(t - 0.03, -2.0 * k), (t, -30.0), (t + 0.3, -30.0), (t + 0.36, -2.0 * (k + 1))]
    mx.automate('music', [(0.0, 0.0)] + steps_down + [(43.8, -12.0), (44.3, 5.0), (49.4, 5.0), (49.7, 0.0), (57.8, 0.0),
                          (58.2, 3.0), (71.8, 3.0), (72.2, 0.0), (101.8, 0.0), (102.2, 2.5), (109.6, 2.5),
                          (110.2, 0.0), (147.8, 0.0), (148.4, 3.0), (160.0, 3.0)])
    mx.duck('music', windows, -9.0, 0.25)
    mx.duck('sfx', windows, -4.0, 0.2)
    mx.duck('amb', windows, -6.0, 0.25)
    master = mx.render({'music': 0.0, 'sfx': -6.0, 'amb': -8.0, 'voice': 3.0}, level={'music': -22.0},
                       ceiling=0.6)
    return write_wav(work / 'mix.wav', master)


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
