"""Soundtrack for '90 Days Left.': score, effects, whispers and the mix."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import numpy as np  # noqa: E402

from audio import sfx, voices  # noqa: E402
from audio.dsp import SR, bp, hp, lp, read_wav, write_wav  # noqa: E402
from audio.mix import Mix  # noqa: E402
from audio.score import Score, chord, n  # noqa: E402
from cues import DURATION, EV, ROAR, WHISPERS  # noqa: E402

# Instrument channels (General MIDI programs set in compose())
PIANO, MBOX, PIZZ, CELLO, STR, TREM, VIOLIN, CHOIR, HORN, DRUMS, TIMP, PAD, HIT, TAIKO, SBASS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)

# The father's theme: (beat, length in beats, pitch). Minor over Dm Bb Gm A; major over F C Dm Bb F.
FATHER_MINOR = [(0, 1.5, 'A3'), (1.5, 0.5, 'D4'), (2, 2, 'F4'),
                (4, 1, 'F4'), (5, 1, 'D4'), (6, 2, 'Bb3'),
                (8, 1.5, 'G3'), (9.5, 0.5, 'Bb3'), (10, 1, 'D4'), (11, 1, 'C4'),
                (12, 2, 'C#4'), (14, 1, 'E4'), (15, 1, 'A3')]
FATHER_MAJOR = [(0, 1.5, 'C5'), (1.5, 0.5, 'F5'), (2, 2, 'A5'),
                (4, 1, 'G5'), (5, 1, 'E5'), (6, 2, 'C5'),
                (8, 1.5, 'A4'), (9.5, 0.5, 'C5'), (10, 1, 'F5'), (11, 1, 'E5'),
                (12, 2, 'D5'), (14, 1, 'C5'), (15, 1, 'Bb4'), (16, 2, 'A4')]
# the same tune fitted over the grind's Dm Bb F C, an octave up, played at one theme beat per second
GRIND_THEME = [(0, 1.5, 'A4'), (1.5, 0.5, 'D5'), (2, 2, 'F5'),
               (4, 1, 'F5'), (5, 1, 'D5'), (6, 2, 'Bb4'),
               (8, 1.5, 'G4'), (9.5, 0.5, 'Bb4'), (10, 1, 'D5'), (11, 1, 'C5'),
               (12, 2, 'C5'), (14, 1, 'E5'), (15, 1, 'G4')]
CLOCK = ['A5', 'F5', 'E5', 'D5']
ROOT = {'Dm': 'D', 'Bb': 'Bb', 'Gm': 'G', 'A': 'A', 'F': 'F', 'C': 'C'}
QUAL = {'Dm': 'm', 'Bb': '', 'Gm': 'm', 'A': '', 'F': '', 'C': ''}


def tri(name, octave=3):
    return chord(ROOT[name], QUAL[name], octave)


def melody(s, stem, ch, t0, bpm, notes_, vel=80, cut=None, transpose=0, start_beat=0, end_beat=None, legato=0.98):
    b = 60 / bpm
    for beat, length, p in notes_:
        if beat < start_beat or (end_beat is not None and beat >= end_beat):
            continue
        t = t0 + (beat - start_beat) * b
        if cut is not None and t >= cut:
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


def taiko_bar(s, t0, vel=1.0, fill=False):
    for off, v in ((0.0, 112), (1.0, 90)):
        s.note('rhythm', TAIKO, t0 + off, 0.4, 'D2', v * vel)
    if fill:
        for k in range(4):
            s.note('rhythm', TAIKO, t0 + 1.5 + k * 0.125, 0.2, 'D2', (70 + 10 * k) * vel)


def claps(s, t0, vel=1.0, hats=False):
    for off in (0.5, 1.5):
        s.note('rhythm', DRUMS, t0 + off, 0.1, 39, 92 * vel)
    if hats:
        for k in range(8):
            s.note('rhythm', DRUMS, t0 + k * 0.25, 0.08, 42, (58 if k % 2 == 0 else 40) * vel)


def compose():
    s = Score(humanize={'piano': (0.01, 6), 'strings': (0.008, 5)})
    s.program('piano', PIANO, 0, 104, 64, 70)
    s.program('piano', MBOX, 10, 92, 70, 80)
    s.program('strings', PIZZ, 45, 100, 56, 60)
    s.program('strings', CELLO, 42, 104, 58, 70)
    s.program('strings', STR, 48, 100, 64, 80)
    s.program('strings', TREM, 44, 96, 64, 80)
    s.program('strings', VIOLIN, 40, 92, 72, 80)
    s.program('orch', CHOIR, 52, 96, 64, 90)
    s.program('orch', HORN, 60, 98, 60, 70)
    s.program('orch', TIMP, 47, 108, 64, 60)
    s.program('orch', PAD, 89, 90, 64, 90)
    s.program('orch', HIT, 55, 100, 64, 60)
    s.program('rhythm', TAIKO, 116, 110, 64, 50)
    s.program('rhythm', SBASS, 38, 100, 64, 30)
    s.program('rhythm', DRUMS, 0, 100, 64, 40)

    # 0-9: the clock motif on music box over soft piano, cut off when he turns the phone over
    cut = EV['flip']
    for k in range(6):
        t = 1.0 + k * 1.0
        if t < cut:
            s.note('piano', MBOX, t, 0.9, CLOCK[k % 4], 74)
    s.notes('piano', PIANO, 1.0, 4.0, tri('Dm', 3), 40)
    s.note('piano', PIANO, 1.0, 4.0, 'D2', 44)
    s.notes('piano', PIANO, 5.0, cut - 5.0, tri('Bb', 3), 40)
    s.note('piano', PIANO, 5.0, cut - 5.0, 'Bb1', 44)
    s.notes('piano', PIANO, cut, 2.4, ['D1', 'Eb1', 'A1'], 66)
    s.ramp('strings', STR, cut, 9.0, 20, 70)
    s.notes('strings', STR, cut, 2.9, ['D2', 'A2'], 60)

    # 9-22: the time-lapse loop: one bar per day at ~92 BPM (2.6 s), pizzicato and the clock motif
    bar = 2.6
    step = bar / 8
    lapse_prog = ['Dm', 'Bb', 'Gm', 'A', 'Dm']
    for b, name in enumerate(lapse_prog):
        tb = 9.0 + b * bar
        r = n(f'{ROOT[name]}2')
        third = tri(name, 3)[1]
        for k, p in enumerate([r, r + 7, r + 12, r + 7, third + 12, r + 7, r + 12, r + 7]):
            s.note('strings', PIZZ, tb + k * step, 0.2, p, 70 + (10 if k == 0 else 0))
        for k in range(4):
            s.note('piano', MBOX, tb + k * bar / 4, bar / 4 * 0.9, CLOCK[k], 62 + (8 if b == 4 else 0))
        s.notes('piano', PIANO, tb, bar * 0.95, tri(name, 3), 38 + 3 * b)
        s.notes('strings', STR, tb, bar, [r + 12, r + 19], 30 + 6 * b)

    # 22-30: the alarm, then the quicksand: a low detuned drone that drags him under
    s.ramp('strings', STR, 23.4, 27.6, 30, 110)
    s.notes('strings', STR, 23.5, 4.3, ['D2', 'Eb2', 'A2'], 70)
    s.ramp('strings', STR, 27.6, 29.6, 110, 40)
    s.ramp('orch', PAD, 22.5, 24.0, 20, 70)
    s.notes('orch', PAD, 22.6, 7.2, ['D2', 'A2'], 50)
    for k in range(10):
        s.note('orch', TIMP, 24.0 + k * 0.33, 0.3, 'D2', 40 + 4 * k)
    s.notes('piano', PIANO, EV['sunk'], 2.2, ['D1', 'D2'], 64)

    # 30-40: the mountain: a piano ostinato that keeps climbing, then the wobble and silence
    asc = [('Dm', 30.0), ('Bb', 32.0), ('Gm', 34.0), ('A', 36.0)]
    for name, t0 in asc:
        lo = tri(name, 4)
        notes8 = [lo[0], lo[1], lo[2], lo[1], lo[0] + 12, lo[2], lo[1], lo[2]]
        for k in range(16):
            t = t0 + k * 0.125 * 2 / 2
            if t >= 38.55:
                break
            s.note('piano', PIANO, t0 + k * 0.125, 0.16, notes8[k % 8] + (12 if t0 >= 34.0 and k >= 8 else 0),
                   52 + 6 * asc.index((name, t0)))
        s.notes('piano', PIANO, t0, 0.6, [n(f'{ROOT[name]}1'), n(f'{ROOT[name]}2')], 70)
        s.notes('strings', STR, t0, 2.0, tri(name, 3), 50 + 10 * asc.index((name, t0)))
    s.ramp('strings', STR, 34.0, 38.5, 70, 120)
    for k in range(14):
        s.note('orch', TIMP, EV['wobble'] + k * 0.065, 0.1, 'A2', 50 + 4 * k)
    s.ramp('strings', STR, 38.55, 38.6, 120, 0)

    # 40-50: the shadow climbs out of the phone: drone, a low horn swell, a cluster of voices
    s.ramp('strings', STR, 39.8, 40.0, 0, 50)
    s.notes('strings', STR, 40.0, 8.8, ['D2', 'A2'], 56)
    s.ramp('orch', HORN, EV['rise'], 43.5, 20, 110)
    s.note('orch', HORN, EV['rise'], 7.6, 'D2', 82)
    s.ramp('orch', CHOIR, 42.0, 45.0, 20, 96)
    s.notes('orch', CHOIR, 42.0, 6.6, ['D4', 'Eb4', 'F4'], 52)
    s.ramp('strings', TREM, 44.0, 47.5, 20, 100)
    s.notes('strings', TREM, 44.0, 5.0, ['A5', 'Bb5'], 52)
    for name, ch in (('orch', HORN), ('orch', CHOIR), ('strings', TREM), ('strings', STR)):
        s.ramp(name, ch, 47.0, 49.1, 110, 0)
    for name, ch in (('orch', HORN), ('orch', CHOIR), ('strings', TREM), ('strings', STR)):
        s.ramp(name, ch, 49.9, 50.0, 0, 100)
    s.ramp('orch', PAD, 48.6, 49.2, 0, 50)
    s.notes('orch', PAD, 48.6, 2.6, ['D3', 'A3'], 34)

    # 50-62: 5 AM: the father's theme on cello, plain piano underneath
    bpm = 84
    beat = 60 / bpm
    t0 = 50.4
    melody(s, 'strings', CELLO, t0, bpm, FATHER_MINOR, vel=86, legato=1.0)
    for k, name in enumerate(['Dm', 'Bb', 'Gm', 'A']):
        tb = t0 + k * 4 * beat
        arpeggio(s, 'piano', PIANO, tb, 4 * beat, tri(name, 3) + [n(f'{ROOT[name]}4')], beat / 2, 38,
                 pattern=(0, 1, 2, 3, 2, 1, 2, 1))
        s.note('piano', PIANO, tb, 4 * beat, f'{ROOT[name]}2', 46)
        if k >= 2:
            s.notes('strings', STR, tb, 4 * beat, tri(name, 3), 40)
    s.ramp('strings', STR, 55.0, 61.8, 50, 80)

    # 62-70: Day 1: near silence, the drawer, the bangs, then a warm chord as the lamp comes on, a riser, the drop
    s.ramp('orch', PAD, 62.0, 63.0, 30, 60)
    s.notes('orch', PAD, 62.0, EV['slam'] - 62.0, ['D3', 'A3'], 40)
    for t in EV['bangs']:
        s.note('orch', TIMP, t, 0.4, 'D2', 72)
    s.notes('piano', PIANO, EV['lamp_on'], 2.0, ['D2', 'A2', 'E3', 'F3', 'A3', 'D4'], 62, strum=0.03)
    s.ramp('strings', STR, EV['lamp_on'], 69.9, 30, 120)
    s.notes('strings', STR, EV['lamp_on'], 69.95 - EV['lamp_on'], ['A2', 'E3', 'A3', 'C#4', 'E4'], 80)
    for k in range(16):
        s.note('rhythm', TAIKO, 68.9 + k * 0.065, 0.06, 'D2', 30 + 5 * k)
    s.ramp('strings', STR, 69.95, 70.0, 120, 100)

    # 70-108: the grind: 120 BPM, Dm Bb F C. Taiko, synth bass, piano ostinato, staccato strings, the theme
    prog = ['Dm', 'Bb', 'F', 'C']
    for b in range(19):
        tb = 70.0 + 2.0 * b
        name = prog[b % 4]
        root = n(f'{ROOT[name]}2') if ROOT[name] in ('D', 'C') else n(f'{ROOT[name]}1')
        quiet = 82.0 <= tb < 86.0          # the failed test: the beat drops out
        warm = 88.0 <= tb < 96.0           # the father at the door: softer
        big = tb >= 96.0
        if not quiet:
            taiko_bar(s, tb, vel=0.7 if warm else 1.0, fill=b % 4 == 3)
            for k in range(8):
                s.note('rhythm', SBASS, tb + k * 0.25, 0.2, root, 84 if not warm else 64)
        if b >= 3 and not quiet:
            claps(s, tb, vel=0.6 if warm else 1.0, hats=b >= 7 and not warm)
        if tb in (70.0, 78.0, 86.0, 96.0, 102.0):
            s.note('rhythm', DRUMS, tb, 1.5, 49, 96)
        hi = tri(name, 4) + [n(f'{ROOT[name]}5')]
        arpeggio(s, 'piano', PIANO, tb, 2.0, hi, 0.25, 50 if not quiet else 40, pattern=(0, 1, 2, 3, 2, 1, 2, 1),
                 length=0.3)
        if b >= 3 and not quiet:
            for k in range(8):
                s.notes('strings', STR, tb + k * 0.25, 0.12, tri(name, 3), 58 if not warm else 40)
        if quiet:
            s.notes('strings', CELLO, tb, 2.0, [n(f'{ROOT[name]}2')], 60)
        if big:
            s.notes('orch', CHOIR, tb, 2.0, tri(name, 4), 62)
            s.notes('orch', HORN, tb, 0.4, tri(name, 3), 84)
    melody(s, 'strings', CELLO, 88.0, 60, GRIND_THEME, vel=84, transpose=-12, end_beat=8)
    melody(s, 'orch', HORN, 96.0, 60, GRIND_THEME, vel=96)
    melody(s, 'strings', VIOLIN, 96.0, 60, GRIND_THEME, vel=80, transpose=12)
    s.ramp('orch', HORN, 96.0, 97.0, 70, 112)
    for k in range(24):
        s.note('orch', TIMP, 106.5 + k * 0.0625, 0.08, 'D2', 50 + 3 * k)
    for name, ch in (('orch', HORN), ('orch', CHOIR), ('strings', VIOLIN), ('strings', STR)):
        s.ramp(name, ch, 107.9, 108.0, 112, 0)

    # 108-120: the exam hall: a thin high pad, the blank, the roar, silence, then the climb back
    for name, ch in (('orch', HORN), ('orch', CHOIR), ('strings', VIOLIN), ('strings', STR)):
        s.ramp(name, ch, 108.05, 108.1, 0, 100)
    s.ramp('strings', VIOLIN, 108.2, 111.0, 20, 60)
    s.notes('strings', VIOLIN, 108.2, 4.0, ['A5'], 50)
    s.notes('strings', STR, 108.2, 5.8, ['D2', 'A2'], 44)
    s.ramp('strings', TREM, EV['blank'], 113.9, 20, 120)
    s.notes('strings', TREM, EV['blank'], 113.95 - EV['blank'], ['A5', 'Bb5', 'C6'], 70)
    s.notes('orch', HIT, ROAR[1], 0.8, ['D3', 'F3', 'Ab3', 'D4'], 100)
    s.note('orch', TIMP, ROAR[1], 0.8, 'D2', 110)
    s.note('rhythm', TAIKO, ROAR[1], 0.8, 'D2', 120)
    s.note('rhythm', DRUMS, ROAR[1], 2.0, 49, 100)
    s.ramp('orch', CHOIR, ROAR[1], ROAR[1] + 0.3, 40, 124)
    s.notes('orch', CHOIR, ROAR[1], 2.5, ['D3', 'Eb3', 'A3', 'Bb3'], 92)
    s.ramp('orch', HORN, ROAR[1], ROAR[1] + 0.2, 60, 124)
    s.note('orch', HORN, ROAR[1], 2.5, 'D2', 104)
    s.ramp('strings', TREM, ROAR[1], 116.5, 120, 120)
    s.notes('strings', TREM, ROAR[1], 2.5, ['D3', 'Eb3', 'A3', 'Bb3'], 96)
    for name, ch in (('orch', CHOIR), ('orch', HORN), ('strings', TREM)):
        s.ramp(name, ch, 116.5, 116.6, 124, 0)
    for t in EV['memories']:
        s.note('piano', MBOX, t, 0.5, 'A5', 60)
    for name, ch in (('orch', CHOIR), ('orch', HORN), ('strings', TREM)):
        s.ramp(name, ch, 118.0, 118.1, 0, 110)
    for k, p in enumerate(['D4', 'F4', 'A4', 'D5']):
        s.note('piano', PIANO, EV['eyes_open'] + k * 0.18, 1.2, p, 56 + 4 * k)
    s.ramp('strings', STR, EV['write'], 119.95, 30, 122)
    s.notes('strings', STR, EV['write'], 119.98 - EV['write'], ['C3', 'G3', 'Bb3', 'E4'], 86)
    s.ramp('strings', STR, 119.98, 120.0, 122, 104)

    # 120-136: release in F major: the father's theme, full, then warm and quiet for the narrator
    rel = ['F', 'C', 'Dm', 'Bb', 'F', 'C', 'Dm', 'Bb']
    for b, name in enumerate(rel):
        tb = 120.0 + 2.0 * b
        root = n(f'{ROOT[name]}2') if ROOT[name] in ('D', 'C') else n(f'{ROOT[name]}1')
        if b < 4:
            taiko_bar(s, tb, fill=b == 3)
            claps(s, tb, hats=True)
            for k in range(8):
                s.note('rhythm', SBASS, tb + k * 0.25, 0.2, root, 90)
            s.notes('orch', CHOIR, tb, 2.0, tri(name, 4), 70)
            s.notes('orch', HORN, tb, 0.5, tri(name, 3), 90)
        else:
            s.note('rhythm', SBASS, tb, 1.9, root, 60)
            s.notes('orch', CHOIR, tb, 2.0, tri(name, 4), 50)
        s.notes('strings', STR, tb, 2.0, tri(name, 3) + [n(f'{ROOT[name]}4')], 84 if b < 4 else 60)
        arpeggio(s, 'piano', PIANO, tb, 2.0, tri(name, 4) + [n(f'{ROOT[name]}5')], 0.25, 54 if b < 4 else 44,
                 pattern=(0, 1, 2, 3, 2, 1, 2, 1), length=0.4)
    s.note('rhythm', DRUMS, 120.0, 2.0, 49, 110)
    s.note('orch', TIMP, 120.0, 1.0, 'F2', 120)
    melody(s, 'orch', HORN, 120.0, 120, FATHER_MAJOR, vel=104, end_beat=16)
    melody(s, 'strings', VIOLIN, 120.0, 120, FATHER_MAJOR, vel=88, end_beat=16)
    melody(s, 'strings', VIOLIN, 128.0, 120, FATHER_MAJOR, vel=66, transpose=-12)
    s.ramp('strings', STR, 128.0, 136.0, 100, 60)
    s.ramp('orch', CHOIR, 128.0, 136.0, 96, 50)

    # 136-148: 5 AM again: the theme in major on piano and cello, alone
    bpm = 90
    beat = 60 / bpm
    t0 = 136.2
    melody(s, 'piano', PIANO, t0, bpm, FATHER_MAJOR, vel=62, transpose=-12)
    melody(s, 'strings', CELLO, t0 + 4 * beat, bpm, FATHER_MAJOR, vel=60, transpose=-24, start_beat=4)
    for k, name in enumerate(['F', 'C', 'Dm', 'Bb', 'F']):
        tb = t0 + k * 4 * beat
        if tb >= 147.8:
            break
        s.notes('piano', PIANO, tb, min(4 * beat, 148.0 - tb), [n(f'{ROOT[name]}2')] + tri(name, 3), 36)
    s.ramp('orch', PAD, 136.0, 137.0, 30, 64)
    s.notes('orch', PAD, 136.2, 11.4, ['F3', 'C4'], 38)
    s.ramp('orch', PAD, 146.4, 147.9, 64, 20)

    # 148-160: title: last chords
    for t, notes_ in ((148.3, ['Bb1', 'F2', 'D3', 'F3']), (150.9, ['A1', 'F2', 'C3', 'F3']),
                      (153.4, ['G1', 'D2', 'Bb2', 'F3']), (155.8, ['F1', 'C2', 'A2', 'C3', 'F3', 'A3'])):
        s.notes('piano', PIANO, t, 2.6 if t < 155 else 4.0, notes_, 54)
        s.notes('orch', PAD, t, 2.6 if t < 155 else 3.9, notes_[1:], 44)
    s.ramp('orch', PAD, 148.2, 148.4, 20, 80)
    s.note('piano', PIANO, 155.8, 3.8, 'C5', 50)
    s.note('piano', PIANO, 156.5, 3.2, 'F5', 44)
    s.note('piano', PIANO, 157.2, 2.6, 'A5', 40)
    s.ramp('orch', PAD, 157.6, 160.0, 80, 12)
    s.ramp('piano', PIANO, 158.2, 160.0, 127, 70, control=11)
    return s


def step_times(t0, t1, speed):
    """Heel strikes of rig.walk(T, speed): a leg reaches full stride at T = (0.25 + 0.5 k) / speed."""
    import math
    k = math.ceil(t0 * speed * 2 - 0.5)
    out = []
    while True:
        t = (0.25 + 0.5 * k) / speed
        if t > t1:
            return out
        if t >= t0:
            out.append(t)
        k += 1


def steps(mx, t0, t1, speed, gain=-14, wood=False, seed=0, pan=0.0):
    for k, t in enumerate(step_times(t0, t1, speed)):
        mx.add('sfx', sfx.footstep(wood, seed + k), t, gain, pan=pan + 0.12 * (1 if k % 2 else -1))


# --- effects, ambience and voices on the timeline --------------------------------------------------------

def place_sfx(mx):
    add = mx.add
    # ambience: the room at night, the street at 5 AM, the exam hall, the kitchen in the morning
    add('amb', sfx.room_tone(22.0, 1, 0.05), 0.0, fade_in=1.0, fade_out=0.4)
    add('amb', sfx.room_tone(28.0, 2, 0.05), 22.0, fade_out=0.6)
    add('amb', sfx.room_tone(12.0, 3, 0.06), 50.0, fade_in=0.4, fade_out=0.6)
    add('amb', sfx.city(11.0, 13, 0.08), 51.0, fade_in=1.0, fade_out=1.0)
    add('amb', sfx.room_tone(46.0, 4, 0.04), 62.0, fade_out=0.5)
    add('amb', sfx.room_tone(14.0, 5, 0.07), 108.0, fade_in=0.2, fade_out=0.3)
    add('amb', sfx.birds(14.0, 33, 0.12), 122.0, fade_in=1.0, fade_out=1.0)
    add('amb', sfx.birds(12.0, 34, 0.16), 136.0, fade_in=1.0, fade_out=1.0)

    # the opening: a clock ticking, a page, the phone buzzing, the turn
    for k in range(9):
        add('sfx', sfx.tick(k % 2 == 1, k), 0.5 + k * 1.0, -18 if k < 6 else -22, pan=-0.3)
    add('sfx', sfx.page_flip(1), EV['book_open'] + 0.1, -12)
    for t in EV['buzz']:
        add('sfx', sfx.buzz(0.75, int(t * 10)), t, -6, pan=0.2)
    add('sfx', sfx.whoosh(0.4, 600, 3000, 3), EV['flip'] - 0.1, -12)
    add('sfx', sfx.thoom(1), EV['flip'] + 0.6, -8)

    # the time-lapse: a tick on every beat, a note slapped on and a book dropped every day
    for k in range(20):
        add('sfx', sfx.tick(k % 2 == 1, 40 + k), 9.0 + k * 0.65, -20, pan=0.3 * (1 if k % 2 else -1))
    for t0 in EV['lapse_cuts']:
        add('sfx', sfx.slap(int(t0 * 10)), t0 + EV['note_slap'], -6, pan=-0.4)
        add('sfx', sfx.thud(int(t0 * 10)), t0 + EV['book_thud'], -6, pan=-0.3)
        add('sfx', sfx.thud(int(t0 * 10) + 1, 0.7), t0 + EV['book_thud'] + 0.12, -9, pan=-0.3)
        if t0 > 9.0:
            add('sfx', sfx.whoosh(0.35, 400, 3000, int(t0)), t0 - 0.18, -16)

    # the quicksand bed
    add('sfx', sfx.alarm_ring(4.6, 1), EV['alarm'], -1, pan=0.5, fade_out=2.6)
    add('sfx', sfx.sludge(4.2, 2), EV['sink'], 3, fade_in=0.3, fade_out=1.0)
    add('sfx', sfx.thoom(4), EV['sink'] + 0.1, -4)
    add('sfx', sfx.breath_in(3), EV['sit_up'] - 0.2, -12)

    # the mountain
    for t0 in EV['mountain_cuts'][1:]:
        add('sfx', sfx.whoosh(0.35, 400, 3000, int(t0)), t0 - 0.18, -16)
    for k in range(6):
        add('sfx', sfx.thud(60 + k, 0.6), EV['wobble'] + k * 0.11, -12 - k, pan=-0.3)
    steps(mx, EV['wobble'] + 0.15, EV['wobble'] + 0.8, 1.2, -14, seed=5)
    add('sfx', sfx.thud(70, 1.2), EV['flop'] + 0.22, -6)

    # the shadow rises
    add('sfx', sfx.thoom(10), EV['rise'], -6)
    add('sfx', sfx.reverse_swell(1.8, 11), EV['rise'] - 1.6, -12)
    add('sfx', sfx.heartbeat(70, 6.8), 42.0, -7, fade_in=1.0, fade_out=0.8)

    # 5 AM
    add('sfx', sfx.reverse_swell(1.1, 12), EV['clock_5am'] - 1.1, -14)
    add('sfx', sfx.beep(2100, 2), EV['clock_5am'], -5)
    add('sfx', sfx.door(True, 4), EV['son_door'], -16, pan=-0.6)
    add('sfx', sfx.tape_rip(1.4, 5), EV['tape'] + 0.4, -10, pan=0.3)
    add('sfx', sfx.tape_rip(1.0, 6), EV['tape'] + 2.0, -12, pan=0.3)
    add('sfx', sfx.click(7), EV['light_off'], -8, pan=0.5)
    steps(mx, EV['light_off'] + 0.3, EV['door_close'] - 0.1, 0.9, -14, seed=7, pan=0.5)
    steps(mx, 60.2, 61.4, 0.8, -20, seed=70, pan=-0.5)
    add('sfx', sfx.door(True, 8), EV['door_close'] - 0.9, -12, pan=0.7)
    add('sfx', sfx.door(False, 9), EV['door_close'], -8, pan=0.7)

    # Day 1
    for a, b in ((62.0, 62.7), (66.0, 66.3), (67.6, 67.9)):
        steps(mx, a, b, 1.1, -14, seed=int(a))
    add('sfx', sfx.buzz(0.6, 10), 62.2, -8)
    add('sfx', sfx.drawer(True, 11), EV['drawer_open'], -8)
    add('sfx', sfx.thud(12, 0.4), EV['drop_phone'] + 0.2, -10)
    add('sfx', sfx.drawer(False, 13), EV['slam'], -3)
    add('sfx', sfx.key_turn(14), EV['lock'], -6)
    for k, t in enumerate(EV['bangs']):
        add('sfx', sfx.bang(15 + k), t, -4 + k)
    add('sfx', sfx.thud(18, 0.8), EV['book_pull'] + 0.2, -10)
    add('sfx', sfx.page_flip(19), EV['book_pull'] + 0.5, -12)
    add('sfx', sfx.click(20), EV['lamp_on'], -6)
    add('sfx', sfx.riser(1.0, 21), 69.0, -10)
    add('sfx', sfx.drop_boom(22), EV['drop'], -6)

    # the grind
    add('sfx', sfx.scribble(5.4, 23), 70.4, -16)
    add('sfx', sfx.bang(24), EV['bang_ignored'], -10)
    add('sfx', sfx.alarm_ring(1.8, 25), EV['alarm2'], -4, pan=0.5, fade_out=0.3)
    add('sfx', sfx.sludge(1.6, 26), EV['alarm2'] + 0.3, -8, fade_out=0.4)
    add('sfx', sfx.whoosh(0.6, 300, 4000, 27), EV['break_free'] - 0.2, -6)
    add('sfx', sfx.footstep(True, 28), EV['break_free'] + 0.5, -8)
    steps(mx, EV['break_free'] + 0.8, 82.0, 1.2, -16, seed=29)
    steps(mx, 89.0, 90.4, 0.8, -18, seed=31, pan=-0.3)
    steps(mx, 95.2, 96.0, 0.8, -18, seed=33, pan=-0.3)
    add('sfx', sfx.bang(30), 83.7, -12)
    add('sfx', sfx.bang(31), 84.5, -12)
    add('sfx', sfx.scribble(1.0, 32), EV['pencil_up'] + 0.2, -14)
    add('sfx', sfx.door(True, 33), EV['father_peek'] - 0.3, -18, pan=-0.4)
    add('sfx', sfx.door(False, 34), 95.2, -18, pan=-0.4)
    for k, t in enumerate(EV['scores']):
        add('sfx', sfx.scribble(0.18, 35 + k), t, -12)
        add('sfx', sfx.thud(35 + k, 0.5), t + 0.2, -2)
        add('sfx', sfx.slap(45 + k), t + 0.2, -6)
        add('sfx', sfx.bling(k), t + 0.25, -14 + 3 * k)
    add('sfx', sfx.thud(39, 0.5), EV['fail'], -2)
    add('sfx', sfx.slap(40), EV['fail'], -6)
    from audio.dsp import reverb
    add('sfx', reverb(sfx.tape_rip(0.8, 41), wet=0.6, length=2.4), EV['look_door'], -10)
    add('sfx', sfx.reverse_swell(0.6, 42), EV['look_door'] - 0.6, -16)
    add('sfx', sfx.scribble(1.8, 38), 104.2, -16)
    add('sfx', sfx.riser(1.6, 39), 106.4, -10)

    # the exam hall
    for k in range(12):
        add('sfx', sfx.tick(k % 2 == 1, 80 + k), 108.4 + k * 0.5, -16, pan=0.1)
    steps(mx, 108.0, EV['sit'], 1.0, -16, seed=41)
    add('sfx', sfx.page_flip(42), EV['paper_flip'], -10)
    add('sfx', sfx.heartbeat(96, 1.8), EV['blank'], -6, fade_in=0.3)
    add('sfx', sfx.tinnitus(1.7, 43), EV['blank'] - 0.1, -12)
    add('sfx', sfx.impact(44), EV['roar'], -6)
    for t in EV['memories']:
        add('sfx', sfx.shimmer(0.5, 45 + int(t), 20), t, -14)
        add('sfx', sfx.whoosh(0.3, 3000, 600, int(t * 10)), t - 0.12, -12)
    add('sfx', sfx.heartbeat(64, 2.2), ROAR[2], -10, fade_out=0.6)
    add('sfx', sfx.breath_in(46), EV['breath'], -4)
    add('sfx', sfx.scribble(2.0, 47), EV['write'], -10)
    add('sfx', sfx.puff_out(48), EV['shade_gone'] - 0.4, 0)
    add('sfx', sfx.whoosh(0.9, 2500, 300, 60), EV['shade_gone'] - 0.5, -4)
    add('sfx', sfx.shimmer(2.0, 49, 30), EV['release'] + 0.1, -14)

    # result day
    add('sfx', sfx.tap(50), EV['open_result'], -10)
    add('sfx', sfx.whoosh(0.5, 300, 1500, 51), EV['turn_screen'], -18)
    add('sfx', sfx.breath_in(52), EV['tears'] - 0.4, -14)

    # 5 AM again
    steps(mx, EV['shoulder'] - 0.85, EV['shoulder'] - 0.15, 0.9, -18, seed=50)
    steps(mx, 136.0, 138.6, 0.85, -16, seed=53)
    add('sfx', sfx.shimmer(1.6, 54, 16), EV['shoes_seen'], -18)
    add('sfx', sfx.door(True, 55), EV['door_sun'], -10, pan=0.6)
    steps(mx, EV['door_sun'] + 0.2, 146.6, 0.85, -16, seed=56, pan=0.5)


MUFFLED = {'let me out!', 'you’re not smart enough.'}


def place_voices(mx, work):
    cache = work / 'tts_cache'
    tmp = work / 'tmp'
    voice_for = {'hiss': ['Enceladus', 'Algenib'], 'deep': ['Charon', 'Fenrir']}
    windows = []
    for k, (text, t0, t1, style) in enumerate(WHISPERS):
        pan = [0.3, -0.4, 0.5, -0.3, 0.4, -0.5, 0.5, 0.4, 0.2, 0.1, -0.5][k % 11]
        x = voices.line(text, style, voice_for[style][k % 2], cache, tmp, pan=pan, seed=k,
                        max_dur=max(1.1, t1 - t0 + 0.3))
        if text in MUFFLED:
            # through the wood of the drawer
            x = lp(x, 1100, 4) * 1.6
        else:
            # less rumble, more consonant
            x = hp(x, 170, 2)
            x = x + 0.7 * bp(x, 2000, 4800)
        room = t1 - t0 + 0.6
        mx.add('voice', x, t0 + 0.02, -1, max_len=room + 1.5, fade_out=0.4)
        windows.append((t0, min(t1, t0 + len(x) / SR)))
    text, r0, r1 = ROAR
    rx = voices.roar(text, [('Algenib', 0.93), ('Charon', 0.72), ('Fenrir', 0.66), ('Enceladus', 0.8)],
                     cache, tmp, length=r1 - r0 - 0.3)
    rx = rx + 0.6 * bp(rx, 1800, 4500)
    mx.add('voice', rx, r0, -3, fade_out=0.6)
    # the same words, whispered right at his ear, so they can be understood
    wx = voices.line('you’ll go blank.', 'hiss', 'Enceladus', cache, tmp, pan=0.2, seed=99,
                     max_dur=r1 - r0 - 0.4)
    wx = hp(wx, 170, 2) + 0.7 * bp(hp(wx, 170, 2), 2000, 4800)
    mx.add('voice', wx, r0 + 0.15, 0, fade_out=0.4)
    windows.append((r0, r1))
    return windows


def build(out_dir):
    out_dir = Path(out_dir)
    work = out_dir / 'audio'
    work.mkdir(parents=True, exist_ok=True)
    stems = compose().render(work / 'stems')
    mx = Mix(DURATION)
    stem_gain = {'piano': 5.0, 'strings': 2.0, 'orch': 0.5, 'rhythm': -2.0}
    for name, path in stems.items():
        mx.add('music', read_wav(path), 0.0, stem_gain.get(name, 0.0))
    place_sfx(mx)
    windows = place_voices(mx, work)
    # lift the quiet cello at 5 AM and the callback for small speakers
    mx.automate('music', [(0.0, 0.0), (49.9, 0.0), (50.5, 3.0), (61.5, 3.0), (62.0, 0.0), (127.8, 0.0),
                          (128.6, 3.5), (136.4, 3.5), (148.0, 3.0), (148.5, 0.0)])
    mx.duck('music', windows, -10.0, 0.25)
    mx.duck('sfx', windows, -4.0, 0.2)
    mx.duck('amb', windows, -6.0, 0.25)
    master = mx.render({'music': 0.0, 'sfx': -6.0, 'amb': -8.0, 'voice': 3.0}, level={'music': -22.0},
                       ceiling=0.6)
    return write_wav(work / 'mix.wav', master)


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
