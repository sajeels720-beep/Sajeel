"""Soundtrack for 'He's Waiting.': score, effects, voices and the mix.

Its own sound, not the orchestral 120 BPM of the earlier films:
- the old man's pocket watch ticks once a second all film long; from Day 1 it is the music's pulse;
- the shadow's music is a cosy lo-fi loop (electric piano, jazz brushes, a soft synth bass) that wears out a
  little more every night and speeds up like tape in the time-lapse;
- the old man's theme is a clarinet waltz in E flat. On the climb it becomes a running 6/8 (marimba clockwork,
  hand-claps, voices), and at the sunrise a church organ with bells, a whole step higher.
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
from audio.dsp import (SR, bp, brown, env_ad, env_exp, glide, hp, lp, norm, pink, read_wav, reverb, rng,  # noqa: E402
                       secs, sine, soft_clip, stereo, t_axis, white, write_wav)
from audio.mix import Mix  # noqa: E402
from audio.score import Score, chord, n  # noqa: E402
from cues import CHORUS, DURATION, EV, SPEECH, WHISPERS  # noqa: E402

# stems and channels
EP, SUB, LDR = 0, 1, 9                            # 'lofi': Rhodes, synth bass, jazz kit
CLAR, VIB, OOH, BELLS, KAL, PADN = 0, 1, 2, 3, 4, 5   # 'theme'
ORGAN, DRONE = 0, 1                               # 'organ'
MAR, ABASS = 0, 1                                 # 'pulse'
KIT = 9                                           # 'perc'
PH_LEAD, PH_BASS, PH_KEYS, PH_KIT = 0, 1, 2, 9    # 'phone': the clips on his screen

# The old man's theme in eighth notes (six to a bar): (start, length, pitch)
THEME = [(0, 2, 'G4'), (2, 1, 'Bb4'), (3, 3, 'Eb5'),
         (6, 2, 'D5'), (8, 1, 'C5'), (9, 3, 'G4'),
         (12, 2, 'Ab4'), (14, 1, 'C5'), (15, 3, 'F5'),
         (18, 2, 'Eb5'), (20, 1, 'D5'), (21, 3, 'Bb4'),
         (24, 2, 'G4'), (26, 1, 'Bb4'), (27, 3, 'Eb5'),
         (30, 2, 'G5'), (32, 1, 'F5'), (33, 3, 'Eb5'),
         (36, 2, 'C5'), (38, 1, 'Eb5'), (39, 2, 'D5'), (41, 1, 'Bb4'),
         (42, 6, 'Eb5')]
THEME_CHORDS = [('Eb', ''), ('C', 'm'), ('Ab', ''), ('Bb', ''), ('Eb', ''), ('C', 'm'), ('Ab', ''), ('Eb', '')]
LOFI_CHORDS = [('Ab', 'maj7'), ('G', 'm7'), ('F', 'm7'), ('Bb', '7')]


def theme(s, stem, ch, t0, eighth, vel=80, transpose=0, bars=None, legato=0.95, swell=0.0):
    b0, b1 = bars or (0, 8)
    for st, ln, p in THEME:
        if not (b0 * 6 <= st < b1 * 6):
            continue
        t = t0 + (st - b0 * 6) * eighth
        v = vel + swell * (st - b0 * 6) / max(1, (b1 - b0) * 6)
        s.note(stem, ch, t, ln * eighth * legato, n(p) + transpose, v)


def triad(name, q, octave):
    return chord(name, q, octave)


# --- the score -----------------------------------------------------------------------------------------------------

def lofi_bar(s, tb, k, vel=1.0, drums=True, bass=True, keys=True):
    """One 3-second bar of the shadow's groove (80 BPM, swung)."""
    root, q = LOFI_CHORDS[k % 4]
    beat = 0.75
    sw = 0.09                                 # swing on the off-beats
    if keys:
        voic = chord(root, q, 3)
        s.notes('lofi', EP, tb + 0.02, 1.45, voic, 58 * vel, strum=0.03)
        s.notes('lofi', EP, tb + 2 * beat + sw, 0.7, voic[1:], 46 * vel, strum=0.02)
        top = voic[-1] + 12
        s.note('lofi', EP, tb + 3 * beat + 0.5 * beat + sw, 0.5, top - 2 if k % 2 else top, 40 * vel)
    if bass:
        r = n(f'{root}1') + (12 if root in ('F', 'G') else 0)
        s.note('lofi', SUB, tb, 1.2, r, 86 * vel)
        s.note('lofi', SUB, tb + 2.5 * beat, 0.5, r + 7, 70 * vel)
    if drums:
        for b in range(4):
            t = tb + b * beat
            if b in (0, 2):
                s.note('lofi', LDR, t, 0.1, 36, 78 * vel)
            if b == 2:
                s.note('lofi', LDR, t + 0.5 * beat + sw, 0.1, 36, 52 * vel)
            if b in (1, 3):
                s.note('lofi', LDR, t, 0.1, 38, 58 * vel)
            s.note('lofi', LDR, t, 0.05, 42, 40 * vel)
            s.note('lofi', LDR, t + 0.5 * beat + sw, 0.05, 42, 28 * vel)


def compose():
    s = Score(humanize={'theme': (0.012, 6), 'pulse': (0.006, 5), 'lofi': (0.01, 6)})
    s.program('lofi', EP, 4, 96, 58, 50)
    s.program('lofi', SUB, 39, 92, 64, 20)
    s.program('lofi', LDR, 32, 84, 64, 30)
    s.program('theme', CLAR, 71, 104, 62, 70)
    s.program('theme', VIB, 11, 96, 70, 80)
    s.program('theme', OOH, 53, 92, 64, 95)
    s.program('theme', BELLS, 14, 86, 72, 90)
    s.program('theme', KAL, 108, 90, 50, 70)
    s.program('theme', PADN, 88, 80, 64, 100)
    s.program('organ', ORGAN, 19, 92, 64, 110)
    s.program('organ', DRONE, 92, 84, 64, 100)
    s.program('pulse', MAR, 12, 98, 56, 60)
    s.program('pulse', ABASS, 32, 100, 64, 40)
    s.program('perc', KIT, 16, 100, 64, 60)
    s.program('phone', PH_LEAD, 80, 90, 64, 10)
    s.program('phone', PH_BASS, 38, 90, 64, 10)
    s.program('phone', PH_KEYS, 0, 90, 64, 10)
    s.program('phone', PH_KIT, 0, 90, 64, 10)

    # --- the hook: the phone's clips; a low organ under the reveal; the theme's first notes at his face
    phone_clips(s, EV['swipes'], 0.3, 19.4)
    s.notes('organ', DRONE, 3.0, 9.0, [n('Eb2'), n('Bb2')], 46)
    s.ramp('organ', DRONE, 3.0, 6.0, 0, 110)
    s.notes('organ', ORGAN, 8.8, 3.6, [n('Eb3'), n('G3'), n('Bb3')], 40)
    s.ramp('organ', ORGAN, 8.8, 10.0, 30, 100)
    s.ramp('organ', ORGAN, 11.0, 12.6, 100, 0)
    s.cc('organ', ORGAN, 12.7, 11, 127)
    theme(s, 'theme', CLAR, 9.4, 0.5, 62, bars=(0, 1))          # three notes, as his face appears
    s.notes('theme', PADN, 12.0, 4.4, triad('C', 'm', 3), 44)
    for k in range(2):                                             # the groove, first from the phone, then close
        lofi_bar(s, 14.0 + 3 * k, k, vel=0.8 + 0.2 * k)
    s.note('lofi', EP, 19.4 - 0.02, 0.05, n('C3'), 1)           # the groove stops dead at the title
    # --- the title: an organ chord
    s.notes('organ', ORGAN, 19.42, 3.4, [n('Eb2'), n('Bb2'), n('Eb3'), n('G3'), n('Bb3'), n('Eb4')], 76)
    s.ramp('organ', ORGAN, 21.6, 22.95, 127, 0)
    s.cc('organ', ORGAN, 23.0, 11, 127)

    # --- the loop: the groove, every night a little more worn (the wear is added in the mix)
    for k in range(6):
        lofi_bar(s, 23.0 + 3 * k, k)
    lofi_bar(s, 41.0, 6, vel=1.1)
    phone_clips(s, [23.3, 24.4, 25.6, 26.9, 29.4, 30.5, 31.6, 33.8, 34.7, 35.6], 23.0, 36.5, quiet=True)

    # --- the mirror: a sting when the old man appears, a cluster that holds while he looks
    s.notes('organ', ORGAN, 46.0, 6.0, [n('C2'), n('Db3'), n('G3'), n('Ab3')], 58)
    s.ramp('organ', ORGAN, 46.0, 46.4, 60, 115)
    s.ramp('organ', ORGAN, 50.0, 51.9, 115, 40)
    s.cc('organ', ORGAN, 52.0, 11, 0)
    s.cc('organ', ORGAN, 52.5, 11, 127)
    s.note('theme', CLAR, 46.05, 2.2, n('D6'), 70)
    s.note('theme', CLAR, 49.0, 2.6, n('Db6'), 58)
    s.notes('organ', DRONE, 53.6, 3.0, [n('C2'), n('Gb2')], 64)
    # --- turning his back: the groove leaks from his headphones
    for k in range(2):
        lofi_bar(s, 57.0 + 3 * k, k + 2, vel=0.9)
    # --- rock bottom: the groove from the phone, then nothing
    phone_clips(s, [67.3, 68.9, 70.6, 71.9], 67.0, 74.8, quiet=True)
    s.notes('organ', DRONE, 79.0, 8.5, [n('Eb2'), n('Bb2')], 40)
    s.ramp('organ', DRONE, 79.0, 81.0, 0, 90)
    s.ramp('organ', DRONE, 86.0, 89.0, 90, 0)
    s.cc('organ', DRONE, 89.2, 11, 127)
    theme(s, 'theme', CLAR, 87.0, 0.6, 52, bars=(0, 1))          # after his words: the first bar, alone

    # --- Day 1: the theme, slow, three beats a bar on the tick
    t0 = 93.0
    for b in range(6):
        name, q = THEME_CHORDS[b % 8]
        tb = t0 + 3 * b
        voic = chord(name, q, 3)
        for k in range(6):
            s.note('theme', VIB, tb + 0.5 * k, 0.9, voic[k % 3] + (12 if k >= 3 else 0), 50 + (10 if k == 0 else 0))
        s.notes('theme', PADN, tb, 3.0, chord(name, q, 3), 38)
        s.note('pulse', ABASS, tb, 1.4, n(f'{name}2'), 66)
    theme(s, 'theme', CLAR, 96.0, 0.5, 70, bars=(0, 4), swell=10)
    s.notes('theme', BELLS, EV['curtains'] + 0.1, 3.0, [n('Eb5'), n('Bb5')], 70)
    for k in range(10):                                            # a vibraphone shimmer as the light floods in
        s.note('theme', VIB, EV['curtains'] + 0.06 * k, 0.8, chord('Eb', '', 5)[k % 3] + 12 * (k // 3 % 2), 52)
    theme(s, 'theme', OOH, 108.0, 0.5, 60, bars=(4, 5))
    # the pulse quickens: from twos to threes on the same tick, as he starts to run
    for k in range(6):
        s.note('pulse', MAR, 109.0 + k / 3, 0.25, chord('Bb', '', 4)[k % 3], 54 + 4 * k)

    # --- the climb: 6/8 on the tick (a bar = 2 s), marimba clockwork, claps, bass, the theme
    climb(s, 111.0, 135.0)
    # --- the last temptation: the music stops; the groove tries to come back, warped
    for k in range(2):
        lofi_bar(s, 137.0 + 3 * k, k, vel=0.85)
    s.note('lofi', EP, 141.6, 0.05, n('C3'), 1)
    alarm(s, 135.4, 143.0)
    alarm(s, 27.5, 28.1)
    # --- the rise: the drop, everything in
    climb(s, 145.0, 153.0, full=True)
    # the trailhead: just the pad and the tick, then the pulse comes back as they set off
    s.notes('theme', PADN, 153.0, 4.0, chord('Ab', '', 3), 44)
    s.notes('organ', DRONE, 153.0, 4.2, [n('Ab1'), n('Eb2')], 52)
    for k in range(6):
        s.note('pulse', MAR, 156.0 + k / 3, 0.25, chord('Bb', '', 4)[k % 3], 50 + 3 * k)
    # --- the ascent: organ arpeggios climbing, toms building
    ascent(s, 157.0, 171.0)
    # --- the sunrise: up a whole step to F; full organ, voices, bells
    sunrise(s, 171.0)
    # --- the epilogue: the theme on vibraphone, slow, at night
    theme(s, 'theme', VIB, 195.0, 0.5, 58, bars=(0, 4), legato=1.3)
    for b in range(4):
        name, q = THEME_CHORDS[b]
        s.notes('theme', PADN, 195.0 + 3 * b, 3.0, chord(name, q, 3), 34)
    theme(s, 'theme', CLAR, 201.0, 0.55, 54, bars=(7, 8))
    # --- the title card
    s.notes('organ', ORGAN, 203.2, 7.6, [n('Eb2'), n('Bb2'), n('Eb3'), n('G3'), n('Bb3'), n('D4'), n('G4')], 70)
    s.ramp('organ', ORGAN, 203.2, 204.4, 20, 110)
    s.ramp('organ', ORGAN, 208.0, 211.0, 110, 0)
    s.notes('theme', BELLS, 203.6, 4.0, [n('Eb5')], 60)
    return s


def climb(s, t0, t1, full=False):
    """The theme in 6/8 on the tick: dotted quarter = 1 s, so a bar is 2 s and an eighth a third of a second."""
    e = 1 / 3
    nb = int(round((t1 - t0) / 2))
    for b in range(nb):
        tb = t0 + 2 * b
        name, q = THEME_CHORDS[b % 8]
        voic = chord(name, q, 4)
        arp = [voic[0], voic[1], voic[2], voic[1] + 12, voic[2], voic[1]]
        for k in range(6):
            s.note('pulse', MAR, tb + k * e, 0.28, arp[k], 62 + (10 if k in (0, 3) else 0))
        s.note('pulse', ABASS, tb, 0.9, n(f'{name}2'), 82)
        s.note('pulse', ABASS, tb + 1.0, 0.6, n(f'{name}2') + 7, 70)
        if b % 2 == 1:
            s.note('theme', KAL, tb + 5 * e, 0.4, voic[2] + 12, 50)
        # percussion: claps on the second dotted beat; drums from Day 77 and in the rise
        busy = full or tb >= EV['days'][4]
        if tb >= t0 + 4 or full:
            s.note('perc', KIT, tb + 1.0, 0.1, 39, 70 if not full else 84)
        if busy:
            s.note('perc', KIT, tb, 0.1, 36, 96 if full else 80)
            s.note('perc', KIT, tb + 4 * e, 0.1, 36, 60)
            for k in range(6):
                s.note('perc', KIT, tb + k * e, 0.05, 70, 40 + (14 if k % 3 == 0 else 0))
        if full:
            s.note('perc', KIT, tb + 1.0, 0.1, 38, 80)
            s.notes('organ', ORGAN, tb, 2.0, chord(name, q, 3), 58)
            if b % 4 == 0:
                s.note('perc', KIT, tb, 0.5, 49, 70)
            if b % 2 == 1:
                for k, tom in enumerate((50, 48, 45)):
                    s.note('perc', KIT, tb + 1.0 + k * e, 0.1, tom, 66 + 8 * k)
        s.notes('theme', PADN, tb, 2.0, chord(name, q, 3), 32 if not full else 40)
    # the melody: clarinet first, then voices, then the organ joins (each 8 bars = 16 s)
    if not full:
        theme(s, 'theme', CLAR, t0, e, 72, bars=(0, 8))
        if t1 - t0 > 16:
            theme(s, 'theme', OOH, t0 + 16, e, 66, bars=(0, 4))
            theme(s, 'theme', CLAR, t0 + 16, e, 60, bars=(0, 4), transpose=-12)
    else:
        theme(s, 'theme', OOH, t0, e, 80, bars=(0, 4))
        theme(s, 'organ', ORGAN, t0, e, 70, bars=(0, 4), transpose=12)
        theme(s, 'theme', CLAR, t0, e, 74, bars=(0, 4))


def ascent(s, t0, t1):
    e = 1 / 3
    nb = int(round((t1 - t0) / 2))
    prog = [('Ab', ''), ('Bb', ''), ('C', 'm'), ('Bb', ''), ('Ab', ''), ('Bb', ''), ('C', 'sus4'), ('C', '')]
    for b in range(nb):
        tb = t0 + 2 * b
        name, q = prog[b % len(prog)]
        voic = chord(name, q, 3)
        rise = b / max(1, nb - 1)
        for k in range(6):
            s.note('organ', ORGAN, tb + k * e, 0.3, (voic + [voic[0] + 12, voic[1] + 12, voic[2] + 12])[k], 54 + 20 * rise)
        s.notes('organ', DRONE, tb, 2.0, [n(f'{name}1'), n(f'{name}2')], 50 + 20 * rise)
        s.note('pulse', ABASS, tb, 1.0, n(f'{name}2'), 80)
        s.note('perc', KIT, tb, 0.2, 41, 70 + 30 * rise)
        s.note('perc', KIT, tb + 1.0, 0.2, 43, 60 + 30 * rise)
        if rise > 0.4:
            for k in range(6):
                s.note('perc', KIT, tb + k * e, 0.05, 70, 40 + 30 * rise)
        if b >= nb - 2:
            for k in range(6):
                s.note('perc', KIT, tb + k * e, 0.1, 45 if k < 3 else 47, 70 + 6 * k)
        s.notes('theme', OOH, tb, 2.0, chord(name, q, 4), 40 + 30 * rise)
    # a breath at the top: everything holds before the sun
    s.cc('organ', ORGAN, t1 - 0.02, 11, 30)


def sunrise(s, t0):
    """171-189: the hush, the sun at 173, the theme in F, the gift, the fading."""
    s.cc('organ', ORGAN, t0, 11, 127)
    s.notes('theme', PADN, t0, 2.0, chord('C', 'sus4', 3), 40)
    t = EV['sun_breaks']
    e = 1 / 3
    up = 2                                               # E flat -> F
    s.notes('organ', ORGAN, t, 8.0, [n('F2'), n('C3'), n('F3'), n('A3'), n('C4'), n('F4')], 92)
    s.notes('organ', DRONE, t, 10.0, [n('F1'), n('C2')], 80)
    s.notes('theme', BELLS, t, 4.0, [n('F5'), n('C6')], 92)
    s.note('perc', KIT, t, 1.5, 49, 104)
    s.note('perc', KIT, t, 0.3, 36, 112)
    s.note('perc', KIT, t, 0.3, 41, 100)
    theme(s, 'theme', OOH, t, e * 1.5, 88, transpose=up, bars=(0, 2))
    theme(s, 'organ', ORGAN, t, e * 1.5, 76, transpose=up + 12, bars=(0, 2))
    for b in range(4):
        tb = t + 3 * b
        name, q = THEME_CHORDS[(b if b < 2 else b + 4) % 8]
        root = n(f'{name}2') + up
        s.note('pulse', ABASS, tb, 2.8, root, 74)
        for k in range(9):
            s.note('pulse', MAR, tb + k * e, 0.3, chord(name, q, 4)[k % 3] + up, 46)
    # the gift and the shoulder: the clarinet takes the last phrase
    theme(s, 'theme', CLAR, 179.0, 0.5, 70, transpose=up, bars=(6, 8))
    s.notes('theme', PADN, 179.0, 6.0, [n('F3'), n('A3'), n('C4')], 40)
    # fading into the light: a high bell and the vibraphone, then the last chord holds
    s.notes('theme', BELLS, EV['fade'][0] + 0.8, 4.0, [n('C6')], 66)
    for k in range(12):
        s.note('theme', VIB, EV['fade'][0] + 0.8 + k * 0.33, 1.2, chord('F', 'add9', 5)[k % 4], 50 - 2 * k)
    s.notes('theme', PADN, 183.0, 10.0, [n('F3'), n('C4'), n('G4'), n('A4')], 46)
    s.notes('organ', DRONE, 189.0, 4.0, [n('F2'), n('C3')], 50)
    s.ramp('organ', DRONE, 191.0, 192.9, 127, 0)
    s.cc('organ', DRONE, 193.0, 11, 127)


def alarm(s, t0, t1):
    """The phone alarm: a little kalimba figure, over and over."""
    pat = ['Eb5', 'Bb5', 'G5', 'Bb5', 'Eb6', 'Bb5']
    t = t0
    k = 0
    while t < t1 - 0.05:
        s.note('phone', PH_KEYS, t, 0.16, n(pat[k % 6]), 84)
        t += 0.18
        k += 1


CLIP_KINDS = ['pop', 'trap', 'laugh', 'uke', 'cheer', 'synth', 'boing', 'piano']


def phone_clips(s, swipes, t0, t1, quiet=False):
    """Each swipe cuts to a different few seconds of somebody's video."""
    edges = [t0] + [w for w in swipes if t0 < w < t1] + [t1]
    for k in range(len(edges) - 1):
        a, b = edges[k], edges[k + 1]
        kind = CLIP_KINDS[(k + int(t0)) % len(CLIP_KINDS)]
        v = 0.8 if quiet else 1.0
        t = a
        if kind == 'pop':
            while t < b:
                for j, p in enumerate(('E5', 'G5', 'A5', 'G5')):
                    if t + j * 0.18 < b:
                        s.note('phone', PH_LEAD, t + j * 0.18, 0.15, n(p), 70 * v)
                s.note('phone', PH_KIT, t, 0.1, 36, 80 * v)
                t += 0.72
        elif kind == 'trap':
            while t < b:
                s.note('phone', PH_KIT, t, 0.1, 36, 90 * v)
                for j in range(4):
                    if t + j * 0.125 < b:
                        s.note('phone', PH_KIT, t + j * 0.125, 0.05, 42, 60 * v)
                s.note('phone', PH_BASS, t, 0.3, n('C2'), 80 * v)
                t += 0.5
        elif kind == 'uke' or kind == 'piano':
            while t < b:
                s.notes('phone', PH_KEYS, t, 0.25, chord('C', '', 4) if int(t * 2) % 2 else chord('F', '', 4), 64 * v)
                t += 0.3
        elif kind == 'synth':
            while t < b:
                s.note('phone', PH_LEAD, t, 0.2, n('A4') + [0, 3, 7, 10][int(t * 5) % 4], 66 * v)
                t += 0.2
        # 'laugh', 'cheer' and 'boing' are sound effects, placed in the mix


# --- new sound effects --------------------------------------------------------------------------------------------------

def watch_tick(k=0, seed=0):
    """A pocket-watch tick: the escapement's sharp click, a tiny metallic ring, a hint of body."""
    dur = 0.09
    click = bp(white(dur, seed + k % 4), 2500, 9000) * env_exp(dur, 0.0018)
    ring = (sine(4100 if k % 2 else 3600, dur) * 0.6 + sine(6300, dur) * 0.3) * env_exp(dur, 0.014)
    body = sine(1100, dur) * env_exp(dur, 0.006) * 0.4
    return norm(click * 0.9 + ring * 0.35 + body, 0.6)


def swipe(seed=0):
    dur = 0.16
    x = bp(white(dur, seed), 1500, 7000) * env_ad(dur, 0.04, 0.12)
    return norm(x, 0.35)


def cough(seed=0, n_=2, gap=0.42):
    """A weak old man's cough: voiced burst, noisy turbulence, a little rasp."""
    out = np.zeros(secs(n_ * gap + 0.5), np.float32)
    r = rng(seed)
    for k in range(n_):
        dur = 0.32 + r.uniform(-0.04, 0.05)
        tt = t_axis(dur)
        f0 = 130 * (1 - 0.25 * tt / dur)
        voiced = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR)) * 0.35
        noise = bp(white(dur, seed + k), 300, 3200)
        x = (voiced * env_exp(dur, 0.05, 0.003) + noise * env_exp(dur, 0.09, 0.004)) * (1 - 0.3 * k)
        x = bp(x, 180, 3600)
        i = secs(k * gap)
        out[i:i + len(x)] += x[: len(out) - i]
    return norm(reverb(out, wet=0.15, length=0.8, decay=0.3), 0.6)


def chuckle(seed=0):
    """A short laugh through the nose."""
    out = np.zeros(secs(0.7), np.float32)
    for k in range(3):
        dur = 0.11
        x = bp(white(dur, seed + k), 400, 2600) * env_ad(dur, 0.01, 0.09) * (1 - 0.25 * k)
        x += sine(glide(170, 150, dur), dur) * env_ad(dur, 0.01, 0.08) * 0.2
        i = secs(0.04 + k * 0.17)
        out[i:i + len(x)] += x
    return norm(out, 0.5)


def old_breath(dur, rate=0.32, seed=0, rasp=0.5):
    """Slow, laboured breathing with a rasp on the way in."""
    t = t_axis(dur)
    ph = (t * rate) % 1.0
    inhale = np.clip(np.sin(np.pi * np.clip(ph / 0.4, 0, 1)), 0, 1) ** 1.5
    exhale = np.clip(np.sin(np.pi * np.clip((ph - 0.45) / 0.5, 0, 1)), 0, 1) ** 1.2 * 0.7
    air = bp(pink(dur, seed), 400, 2600)
    rough = bp(white(dur, seed + 1), 900, 3000) * (np.sin(2 * np.pi * 34 * t) * 0.5 + 0.5) * rasp
    return norm((air + rough * 0.5) * inhale + air * exhale, 0.4)


def scrub(dur, rate=3.2, seed=0):
    """A toothbrush."""
    t = t_axis(dur)
    x = bp(white(dur, seed), 1800, 7500)
    g = (np.sin(2 * np.pi * rate * t) * 0.5 + 0.5) ** 0.7
    return norm(x * g, 0.3)


def glass_palm(seed=0):
    dur = 0.6
    thump = sine(glide(140, 90, dur), dur) * env_exp(dur, 0.06, 0.002)
    ring = (sine(1520, dur) * 0.5 + sine(2390, dur) * 0.3) * env_exp(dur, 0.18)
    return norm(thump + ring * 0.25, 0.6)


def creak(seed=0, dur=0.55):
    """An old bedspring giving a little under someone's weight."""
    t = t_axis(dur)
    f = 520 + 140 * np.sin(2 * np.pi * 3.0 * t) * np.exp(-t * 3) + 60 * rng(seed).standard_normal(len(t)).cumsum() / len(t)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (np.sin(2 * np.pi * 37 * t) * 0.5 + 0.5)
    x = bp(tone.astype(np.float32) + 0.3 * white(dur, seed), 380, 2400) * env_ad(dur, 0.06, 0.4)
    return norm(x, 0.35)


def power_down(seed=0):
    dur = 0.4
    x = sine(glide(1400, 300, dur), dur) * env_exp(dur, 0.12) * 0.4
    return norm(x, 0.3)


def gravel(seed=0):
    dur = 0.16
    out = np.zeros(secs(dur), np.float32)
    r = rng(seed)
    for k in range(9):
        d = bp(white(0.02, seed * 10 + k), 1200, 6000) * env_exp(0.02, 0.004) * r.uniform(0.3, 1.0)
        i = secs(r.uniform(0, dur - 0.02))
        out[i:i + len(d)] += d
    out += lp(white(dur, seed + 5), 600) * env_exp(dur, 0.04) * 0.4
    return norm(out, 0.4)


def crickets(dur, seed=0, level=0.08):
    t = t_axis(dur)
    out = np.zeros((len(t), 2), np.float32)
    r = rng(seed)
    for v in range(4):
        f = r.uniform(3800, 4600)
        chirp = (np.sin(2 * np.pi * r.uniform(2.2, 3.2) * t + r.uniform(0, 6)) > 0.55).astype(np.float32)
        chirp = lp(chirp, 60)
        am = (np.sin(2 * np.pi * 30 * t) * 0.5 + 0.5)
        x = np.sin(2 * np.pi * f * t) * am * chirp
        out += stereo(x.astype(np.float32), r.uniform(-0.8, 0.8))
    return norm(out, level)


def phone_eq(x, tmp=None):
    """A phone's tiny speaker: no lows, no highs, a little crunch."""
    y = bp(x, 520, 4800, order=3)
    return soft_clip(y * 1.6, 1.3) * 0.7


def tape(x, wobble=0.004, rate=0.55, seed=0):
    """Wow and flutter: read the audio back at a slightly wandering speed."""
    if x.ndim == 1:
        x = x[:, None]
    n_ = len(x)
    t = np.arange(n_) / SR
    drift = wobble * (np.sin(2 * np.pi * rate * t) + 0.4 * np.sin(2 * np.pi * rate * 2.7 * t + 1.3))
    pos = np.clip(np.arange(n_) + np.cumsum(drift), 0, n_ - 1)
    out = np.stack([np.interp(pos, np.arange(n_), x[:, c]) for c in range(x.shape[1])], axis=1)
    return out.astype(np.float32)


def speed_ramp(x, t0, t1, r0, r1, stop=None):
    """Play x from t0 at a speed that rises from r0 to r1 by t1 (pitch rises with it, like tape); returns the
    warped audio for [t0, t1], ending in a tape stop if stop (seconds) is given."""
    i0 = secs(t0)
    out_n = secs(t1 - t0)
    u = np.arange(out_n) / max(1, out_n - 1)
    rate = r0 + (r1 - r0) * u ** 1.6
    if stop:
        k = secs(stop)
        rate[-k:] *= np.linspace(1, 0, k) ** 1.5
    pos = i0 + np.cumsum(rate)
    pos = np.clip(pos, 0, len(x) - 1)
    return np.stack([np.interp(pos, np.arange(len(x)), x[:, c]) for c in range(x.shape[1])], axis=1).astype(np.float32)


def crackle(dur, seed=0, level=0.05):
    r = rng(seed)
    out = np.zeros(secs(dur), np.float32)
    for k in range(int(dur * 22)):
        i = secs(r.uniform(0, dur - 0.01))
        d = hp(white(0.004, seed + k % 40), 2000) * r.uniform(0.2, 1.0)
        out[i:i + len(d)] += d[: len(out) - i]
    hiss = hp(pink(dur, seed + 99), 3000) * 0.08
    return stereo(norm(out + hiss, level), width=0.6)


# --- placing effects ------------------------------------------------------------------------------------------------

def pan_of(x, cam_x=960, zoom=1.0):
    return max(-0.8, min(0.8, (x - cam_x) * zoom / 960))


def tick_times():
    """Every tick the watch makes, and how loud (dB)."""
    out = []
    for k in range(1, 20):            # the hook: fades in from nowhere
        t = float(k)
        out.append((t, -26 + min(12, 3 * (t - 1)) if t < 5 else -14, 0.45))
    for t in (20.0, 21.0, 22.0):
        out.append((t, -8, 0.0))
    for k in range(23, 37):
        out.append((float(k), -20, 0.4))
    # the time-lapse: faster and faster
    t, step = 36.5, 0.8
    while t < 42.0:
        out.append((t, -16, 0.0))
        t += step
        step = max(0.08, step * 0.86)
    out.append((42.05, -6, 0.0))
    for k in range(43, 46):
        out.append((float(k), -24, 0.0))
    for k in range(46, 52):            # in the mirror, every tick is loud
        out.append((float(k), -8, 0.0))
    for k in range(53, 57):
        out.append((float(k), -18, 0.0))
    t = 57.0
    while t < 63.0:
        out.append((t, -14, 0.35))
        t += 1.15
    for t in [62.0] + EV['watch_slow']:
        out.append((t, -4, 0.0))
    for t in EV['last_ticks']:
        out.append((t, -9, 0.35))
    out.append((EV['tick_back'], -2, 0.0))
    for k in range(93, 135):
        out.append((float(k), -17 if k < 111 else -21, 0.0))
    for k in range(145, 172):
        out.append((float(k), -24, 0.0))
    for k in range(183, 193):          # the watch in his hand
        out.append((float(k), -16, 0.1))
    for k in range(193, 212):          # on the nightstand
        out.append((float(k), -15 if k < 203 else -10, -0.4 if k < 203 else 0.0))
    return out


def run_steps(gait, t0, t1, dt=1 / 240):
    """Times a foot lands in a Gait run (each time the distance passes a whole step)."""
    times = []
    prev = None
    t = t0
    while t < t1:
        d = abs(gait.x(t) - gait.xa)
        k = int(d / gait.S)
        if prev is not None and k > prev:
            times.append(t)
        prev = k
        t += dt
    return times


def place_sfx(mx):
    # the room at night, the phone, the watch
    mx.add('amb', sfx.room_tone(DURATION, level=0.05), 0.0, -6)
    for t, g, pan in tick_times():
        mx.add('sfx', stereo(watch_tick(int(t * 3), 1), pan), t, g)
    for k, t in enumerate(EV['swipes'] + [23.3, 24.4, 25.6, 26.9, 29.4, 30.5, 31.6, 33.8, 34.7, 35.6, 67.3, 68.9,
                                         70.6, 71.9]):
        mx.add('sfx', stereo(swipe(k), -0.3), t - 0.03, -14)
    # the clips that are sound effects: a laugh track, a cheer, a cartoon boing
    for k, (a, b) in enumerate(zip([0.3] + EV['swipes'], EV['swipes'] + [19.4])):
        kind = CLIP_KINDS[(k + 0) % len(CLIP_KINDS)]
        if kind == 'laugh':
            mx.add('phone', sfx.murmur(b - a, voices=8, seed=40 + k, level=0.6), a, -2)
        elif kind == 'cheer':
            mx.add('phone', sfx.crowd_cheer(b - a, seed=50 + k, level=0.6), a, -2)
        elif kind == 'boing':
            mx.add('phone', stereo(sine(glide(200, 900, 0.3), 0.3) * env_exp(0.3, 0.2) * 0.6), a + 0.05, -4)
    # the hook
    mx.add('sfx', stereo(chuckle(1), -0.3), EV['chuckle'], -10)
    for k, t0 in enumerate(EV['drain']):
        mx.add('sfx', stereo(sfx.reverse_swell(0.9, seed=60 + k)[::-1] * 0.5, 0.2), t0, -18)
        mx.add('sfx', stereo(sfx.shimmer(1.2, seed=70 + k), 0.1)[::-1].copy(), t0, -20)
    mx.add('sfx', stereo(cough(3), 0.45), EV['cough'], -10)
    mx.add('sfx', stereo(sfx.thoom(1), -0.6), EV['eyes_open'] - 0.1, -6)
    mx.add('sfx', stereo(sfx.reverse_swell(1.1, seed=90), 0.3), 9.05, -12)
    mx.add('sfx', stereo(sfx.shimmer(1.4, seed=91), 0.3), 9.6, -18)
    mx.add('sfx', stereo(creak(1), 0.4), EV['head_up'] - 0.1, -16)
    mx.add('sfx', stereo(creak(2, 0.8), -0.2), EV['sit_up'], -14)
    mx.add('sfx', stereo(creak(3), 0.3), EV['old_lifts'], -18)
    # the loop
    for k, t in enumerate(EV['coughs']):
        mx.add('sfx', stereo(cough(10 + k, n_=2 + k % 2), 0.4), t, -12)
    mx.add('sfx', stereo(sfx.buzz(0.7, seed=3), -0.5), 27.5, -8)
    mx.add('sfx', stereo(sfx.thud(seed=4, heavy=0.4), -0.5), 28.05, -12)
    mx.add('amb', sfx.birds(1.5, seed=5, level=0.18), 27.5, -12, fade_in=0.1, fade_out=0.3)
    mx.add('amb', sfx.birds(1.5, seed=6, level=0.18), 32.0, -12, fade_in=0.1, fade_out=0.3)
    mx.add('sfx', stereo(sfx.slap(seed=7)[::-1] * 0.6, -0.6), EV['note_falls'], -16)
    for i, t0 in enumerate(CHORUS):
        mx.add('sfx', stereo(sfx.whoosh(0.4, 400, 2000, seed=80 + i), 0.3 * (-1) ** i), t0 - 0.05, -24)
    # the mirror
    mx.add('amb', sfx.light_buzz(14.0, seed=8, level=0.05), 43.0, -10, fade_out=0.05, max_len=13.4)
    mx.add('sfx', stereo(scrub(2.0, 3.2, 1)), 43.0, -18)
    mx.add('sfx', stereo(scrub(2.2, 2.1, 2)), EV['old_in_mirror'], -20, fade_out=0.4, max_len=EV['stop_brush'] - EV['old_in_mirror'])
    mx.add('sfx', stereo(sfx.reverse_swell(0.8, seed=9)), EV['old_in_mirror'] - 0.8, -12)
    mx.add('sfx', stereo(sfx.impact(seed=10)), EV['old_in_mirror'], -10)
    mx.add('sfx', stereo(glass_palm(1), 0.15), EV['palm'] + 0.62, -6)
    mx.add('sfx', stereo(sfx.breath_in(12)), EV['step_back'] - 0.1, -6)
    mx.add('sfx', stereo(old_breath(4.0, 0.9, seed=13, rasp=0.0) * 0.8), EV['normal'], -12)
    mx.add('sfx', stereo(sfx.thoom(2), 0.4), EV['shade_mirror'], -8)
    mx.add('sfx', stereo(sfx.click(seed=14)), EV['light_off'], -6)
    # turning his back, the watch slowing, rock bottom
    mx.add('sfx', stereo(old_breath(36.0, 0.3, seed=15), 0.35), 57.0, -20, fade_in=1.0, fade_out=2.0)
    mx.add('sfx', stereo(sfx.heartbeat(56, 6.0, seed=16)) * 0.6, 61.0, -16, fade_in=1.0)
    mx.add('sfx', stereo(sfx.heartbeat(44, 10.0, seed=17)), 70.0, -16, fade_out=3.0)
    mx.add('sfx', stereo(sfx.tinnitus(2.2, seed=18)), EV['watch_stops'] + 0.4, -30, fade_in=0.4, fade_out=1.4)
    mx.add('sfx', stereo(power_down(1), -0.1), EV['phone_dies'], -12)
    for t in EV['heartbeats']:
        mx.add('sfx', stereo(sfx.heartbeat(60, 0.9, seed=19)), t, -8)
    # Day 1
    mx.add('amb', sfx.birds(18.0, seed=20, level=0.16), EV['curtains'], -16, fade_in=0.6)
    mx.add('sfx', sfx.curtain(1.2, seed=21), EV['curtains'] - 0.05, -8)
    mx.add('sfx', sfx.footsteps([97.65 + 0.33 * k for k in range(6)], wood=True, seed=22), 0.0, -16)
    mx.add('sfx', stereo(sfx.door(True, seed=23), -0.3), EV['door_open'], -10)
    mx.add('amb', sfx.city(4.0, seed=24, level=0.2), 107.0, -12, fade_in=0.3, fade_out=0.3)
    mx.add('sfx', sfx.footsteps([108.0 + 0.45 * k for k in range(3)], seed=25), 0.0, -16)
    # the montage: running steps from the gaits themselves
    import act2
    for gait, t0, t1, g in ((act2.RUN_OUT, 109.1, 111.0, -18), (act2.D3_GAIT1, 111.0, 113.3, -18),
                            (act2.D3_GAIT2, 114.65, 115.0, -18), (act2.G77_H, 127.0, 135.0, -20),
                            (act2.G77_O, 129.6, 135.0, -22)):
        for k, t in enumerate(run_steps(gait, t0, t1)):
            mx.add('sfx', stereo(sfx.footstep(False, seed=100 + k), 0.1 * (-1) ** k), t, g)
    for t in (114.2, 114.5):
        mx.add('sfx', stereo(sfx.footstep(True, seed=7)), t, -14)
    mx.add('sfx', stereo(old_breath(1.4, 1.6, seed=26, rasp=0.0)), 113.3, -12)
    for k in range(5):
        mx.add('sfx', stereo(sfx.grunt(seed=27 + k, dur=0.4), 0.3), 115.6 + k / 0.8 * 0.95, -18)
    mx.add('sfx', stereo(sfx.drawer(True, seed=28), -0.6), EV['drawer'] - 0.7, -12)
    mx.add('sfx', stereo(sfx.drawer(False, seed=29), -0.6), EV['drawer'], -12)
    mx.add('sfx', stereo(sfx.click(seed=30), -0.6), 120.9, -10)
    mx.add('sfx', stereo(sfx.rustle(1.2, seed=31, level=0.2)[:, 0], 0.3), EV['tuck'], -14)
    mx.add('amb', crickets(4.0, seed=32), 119.0, -10, fade_in=0.3, fade_out=0.3)
    mx.add('amb', sfx.birds(4.0, seed=33, level=0.16), 115.0, -14, fade_in=0.2, fade_out=0.2)
    mx.add('amb', sfx.birds(4.0, seed=34, level=0.16), 123.0, -14, fade_in=0.2, fade_out=0.2)
    for t in (124.3, 125.6):
        mx.add('sfx', stereo(sfx.page_flip(seed=35)), t, -16)
    mx.add('amb', sfx.wind(8.0, seed=36, level=0.12), 127.0, -14, fade_in=0.4, fade_out=0.4)
    mx.add('amb', sfx.wind(4.0, seed=37, level=0.12), 111.0, -16, fade_in=0.3, fade_out=0.3)
    # the temptation
    mx.add('amb', sfx.rain(10.0, seed=38, level=0.3), 135.0, -10, fade_in=0.2, fade_out=0.6)
    for k in range(10):
        mx.add('sfx', stereo(sfx.buzz(0.7, seed=39 + k), -0.6), 135.4 + 0.76 * k, -12, max_len=max(0.0, 143.0 - 135.4 - 0.76 * k))
    mx.add('sfx', stereo(sfx.thoom(3), -0.5), EV['shade_rises'], -6)
    mx.add('sfx', stereo(sfx.reverse_swell(1.6, seed=40)), EV['drop'] - 1.6, -6)
    mx.add('sfx', stereo(sfx.poof(seed=41, dark=True), -0.4), EV['shade_gone'], -6)
    mx.add('sfx', stereo(sfx.rustle(0.8, seed=42, level=0.3)[:, 0]), EV['up_through'], -10)
    # quick days
    q = EV['quick_days']
    mx.add('amb', sfx.rain(2.0, seed=43, level=0.35), q[0], -8, fade_out=0.1)
    mx.add('amb', sfx.rustle(2.0, seed=44, level=0.25), q[1], -10, fade_out=0.1)
    mx.add('amb', sfx.wind(2.0, seed=45, level=0.25), q[2], -8, fade_out=0.1)
    mx.add('amb', sfx.birds(2.0, seed=46, level=0.15), q[3], -14, fade_out=0.1)
    for k in range(4):
        t = q[3] + 0.0 + k * 0.5
        mx.add('sfx', stereo(sfx.grunt(seed=60 + k, dur=0.3)), t + 0.45, -22)
    # the trailhead, the climb
    mx.add('amb', crickets(4.2, seed=47, level=0.09), EV['trailhead'], -8, fade_in=0.3, fade_out=0.6)
    mx.add('amb', sfx.wind(20.0, seed=48, level=0.18, gusty=1.2), EV['ascent'] - 1.0, -12, fade_in=2.0, fade_out=1.0)
    for k in range(60):
        t = EV['ascent'] + k * 0.42 + 0.05 * math.sin(k)
        if t > EV['last_step'] + 2:
            break
        mx.add('sfx', stereo(gravel(k), 0.15 * (-1) ** k), t, -20)
    mx.add('sfx', stereo(sfx.grunt(seed=71, dur=0.5)), EV['last_step'] + 0.9, -14)
    mx.add('sfx', stereo(sfx.grunt(seed=72, dur=0.6), 0.1), EV['pull_up'] + 0.2, -14)
    mx.add('sfx', stereo(sfx.slap(seed=73)), EV['hand_offer'] + 0.5, -16)
    # the sunrise
    mx.add('sfx', stereo(sfx.reverse_swell(2.0, seed=74)), EV['sun_breaks'] - 2.0, -6)
    mx.add('amb', sfx.wind(24.0, seed=75, level=0.15, gusty=0.6), 172.0, -14, fade_in=1.0, fade_out=3.0)
    mx.add('sfx', stereo(sfx.shimmer(4.5, seed=76), -0.2), EV['fade'][0] + 0.8, -10)
    mx.add('sfx', stereo(sfx.shimmer(3.0, seed=77), 0.5), EV['fade'][0] + 2.6, -14)
    # the epilogue: night, crickets far away
    mx.add('amb', crickets(10.0, seed=78, level=0.05), EV['epilogue'], -12, fade_in=1.0, fade_out=1.0)


# --- voices -----------------------------------------------------------------------------------------------------------

SHADOW_VOICE = {'soft': 'Algieba', 'close': 'Umbriel'}


def place_voices(mx, work):
    cache = work / 'tts_cache'
    tmp = work / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    windows = []
    pans = [-0.45, -0.5, -0.5, -0.5, 0.2, -0.1, -0.45, -0.5]
    for k, (text, t0, t1, style) in enumerate(WHISPERS):
        x = voices.line(text, style, SHADOW_VOICE[style], cache, tmp, pan=pans[k], seed=k, max_dur=t1 - t0 + 0.4)
        mx.add('voice', x, t0 + 0.02, -1, max_len=t1 - t0 + 1.5, fade_out=0.4)
        windows.append((t0, t1))
    # the time-lapse chorus: the same line, faster and higher each time, all around him
    base = voices.tts('you have time.', SHADOW_VOICE['soft'], 'soft', cache)
    if base:
        raw = read_wav(base)
        raw = raw.mean(axis=1) if raw.ndim == 2 else raw
        for i, t0 in enumerate(CHORUS):
            rate = 1.0 + 0.12 * i
            from audio.dsp import ffmpeg_filter
            y = ffmpeg_filter(voices.trim_silence(raw), f'rubberband=tempo={rate:.2f}:pitch={0.92 + 0.03 * i:.2f}', tmp)
            y = voices.process(y, 'soft', tmp, pan=[-0.7, 0.6, -0.3, 0.8, -0.8, 0.4, 0.0][i])
            y = hp(y, 200, order=3)
            mx.add('voice', y, t0, -7 + 0.5 * i, fade_out=0.2)
        windows.append((CHORUS[0], CHORUS[-1] + 0.8))
    # the old man, once; and the boy's answer
    speak = {'old': ('Algenib', 'old', 0.25), 'hero': ('Orus', 'firm', -0.1)}
    for text, t0, t1, who in SPEECH:
        voice, style, pan = speak[who]
        x = voices.line(text.replace('…', '...'), style, voice, cache, tmp, pan=pan, seed=90, max_dur=t1 - t0 + 0.6)
        mx.add('voice', x, t0, 4.0 if who == 'old' else 1.0, fade_out=0.3)
        windows.append((t0, t1))
    return windows


# --- the build ----------------------------------------------------------------------------------------------------------

def lofi_versions(x):
    """The groove four ways: warm (the shadow close by), worn (night after night), phone and headphone leaks."""
    warm = lp(x, 6500) * 1.0
    worn = tape(lp(x, 2600), wobble=0.012, rate=0.45)
    phone = stereo(phone_eq(x.mean(axis=1)), 0.35)
    leak = stereo(phone_eq(lp(x.mean(axis=1), 2400)) * 0.7, 0.0)
    return warm, worn, phone, leak


def build(out_dir):
    out_dir = Path(out_dir)
    work = out_dir / 'audio'
    work.mkdir(parents=True, exist_ok=True)
    stems = compose().render(work / 'stems')
    mx = Mix(DURATION)
    stem_gain = {'theme': 1.0, 'organ': -2.0, 'pulse': 0.0, 'perc': -3.0}
    for name, path in stems.items():
        if name in ('lofi', 'phone'):
            continue
        mx.add('music', read_wav(path), 0.0, stem_gain.get(name, 0.0))
    # the lo-fi groove, routed by scene
    lofi = read_wav(stems['lofi'])
    if lofi.ndim == 1:
        lofi = stereo(lofi)
    warm, worn, phone, leak = lofi_versions(lofi)
    n_ = len(lofi)
    crack = crackle(DURATION + 2, seed=3, level=0.05)[:n_]

    def seg(src, t0, t1, g, fi=0.05, fo=0.05):
        a, b = secs(t0), min(n_, secs(t1))
        mx.add('lofi', src[a:b], t0, g, fade_in=fi, fade_out=fo)

    seg(phone, 14.0, 16.4, -6, fi=0.6)                   # from his phone...
    seg(warm, 16.0, 19.4, -2, fi=0.5, fo=0.02)           # ...then close, as the shadow leans in
    seg(warm, 23.0, 29.0, -2)
    seg(worn, 29.0, 36.5, -3, fi=0.3)
    tl = speed_ramp(worn, 36.5, 42.0, 1.0, 2.6, stop=0.45)
    mx.add('lofi', tl, 36.5, -2, fade_out=0.02)
    seg(leak, 57.0, 63.0, -10, fi=0.4, fo=0.6)
    seg(warm, 137.0, 141.6, -7, fi=1.2, fo=0.05)
    mx.add('lofi', tape(warm[secs(137.0):secs(141.6)], wobble=0.05, rate=0.9), 137.0, -12, fade_in=1.0, fade_out=0.05)
    mx.add('lofi', crack[secs(23.0):secs(42.0)], 23.0, -6, fade_out=0.05)
    # the phone's clips
    ph = read_wav(stems['phone'])
    ph = stereo(phone_eq(ph.mean(axis=1) if ph.ndim == 2 else ph), 0.3)
    mx.add('phone', ph, 0.0, 0.0)
    place_sfx(mx)
    windows = place_voices(mx, work)
    # levels by scene
    mx.automate('sfx', [(0.0, 5.0), (7.6, 5.0), (9.0, 0.0)])
    mx.automate('phone', [(0.0, 10.0), (3.4, 8.0), (7.6, 0.0), (12.0, -2.0), (16.2, -10.0), (19.3, -12.0), (19.4, -40.0),
                          (23.0, -14.0), (36.5, -14.0), (36.6, -40.0), (66.9, -40.0), (67.0, -12.0), (72.2, -14.0),
                          (74.8, -40.0), (135.3, -40.0), (135.4, -6.0), (143.0, -6.0), (143.1, -40.0)])
    mx.automate('music', [(0.0, 2.0), (3.0, 4.0), (19.4, 3.0), (23.0, 0.0), (92.6, 2.0), (111.0, 0.0),
                          (134.95, 0.0), (135.0, -40.0), (135.1, -40.0), (144.9, -40.0), (145.0, 2.0), (153.0, 0.0), (172.0, 0.0),
                          (173.0, 3.0), (183.0, 1.0), (193.0, 0.0), (203.0, 2.0)])
    mx.automate('lofi', [(0.0, 0.0), (42.0, 0.0), (42.4, -60.0), (56.9, -60.0), (57.0, 0.0)])
    mx.duck('music', windows, -8.0, 0.25)
    mx.duck('lofi', windows, -7.0, 0.25)
    mx.duck('phone', windows, -8.0, 0.2)
    mx.duck('sfx', windows, -3.0, 0.2)
    mx.duck('amb', windows, -6.0, 0.25)
    # silence where the watch stops: nothing but breath until he speaks
    mx.duck('music', [(EV['watch_stops'] + 0.02, 78.8)], -40.0, 0.05)
    mx.duck('music', [(EV['black'] - 0.2, EV['dawn'] + 0.4)], -40.0, 0.2)
    master = mx.render({'music': 0.0, 'lofi': -3.0, 'phone': -6.0, 'sfx': -6.0, 'amb': -8.0, 'voice': 3.0},
                       level={'music': -22.0}, ceiling=0.6)
    return write_wav(work / 'mix.wav', master)


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
