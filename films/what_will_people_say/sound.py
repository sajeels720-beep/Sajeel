"""Soundtrack for 'What Will People Say?': score, effects, whispers and the mix."""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'studio'))

import numpy as np  # noqa: E402

from audio import sfx, voices  # noqa: E402
from audio.dsp import SR, lp, norm, read_wav, reverb, secs, stereo, write_wav  # noqa: E402
from audio.mix import Mix  # noqa: E402
from audio.score import Score, _jitter, chord, n  # noqa: E402
from cues import DURATION, EV, ROAR, WHISPERS  # noqa: E402

# Instrument channels (General MIDI programs)
NYLON, PIANO, STRINGS, BASS, STEEL, LEAD, CHOIR, BRASS, PAD, DRUMS, TIMP, TREM, LOWSTR, HIT, VIOLIN = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)

# His song: (beat, length in beats, pitch) over Am F C G Am F C G->C
THEME = [(0, 1.5, 'E5'), (1.5, 0.5, 'D5'), (2, 1, 'C5'), (3, 1, 'D5'),
         (4, 2, 'C5'), (6, 2, 'A4'),
         (8, 1, 'G4'), (9, 1, 'C5'), (10, 1, 'E5'), (11, 1, 'G5'),
         (12, 1.5, 'F5'), (13.5, 0.5, 'E5'), (14, 2, 'D5'),
         (16, 1.5, 'E5'), (17.5, 0.5, 'D5'), (18, 1, 'C5'), (19, 1, 'D5'),
         (20, 1, 'C5'), (21, 1, 'A4'), (22, 2, 'F5'),
         (24, 1, 'E5'), (25, 1, 'D5'), (26, 1, 'C5'), (27, 1, 'E5'),
         (28, 2, 'D5'), (30, 2, 'C5')]
PROG = ['Am', 'F', 'C', 'G', 'Am', 'F', 'C', 'G']
GUITAR_VOICING = {'Am': ['A2', 'E3', 'A3', 'C4', 'E4'], 'F': ['F2', 'C3', 'F3', 'A3', 'C4'],
                  'C': ['C3', 'G3', 'C4', 'E4', 'G4'], 'G': ['G2', 'D3', 'G3', 'B3', 'D4']}
ROOTS = {'Am': 'A', 'F': 'F', 'C': 'C', 'G': 'G', 'E': 'E', 'Dm': 'D'}
QUAL = {'Am': 'm', 'F': '', 'C': '', 'G': '', 'E': '', 'Dm': 'm'}


def fingerpick(s, stem, ch, t0, bpm, chord_name, beats=4, vel=58, cut=None):
    v = GUITAR_VOICING[chord_name]
    order = [0, 2, 3, 4, 1, 3, 2, 3]
    e = 60 / bpm / 2
    for k in range(beats * 2):
        t = t0 + k * e
        if cut is not None and t >= cut:
            return
        dur = e * (6 if k == 0 else 3)
        if cut is not None:
            dur = min(dur, cut - t)
        s.note(stem, ch, t, dur, v[order[k % 8]], vel + (10 if k == 0 else 0) - (k % 2) * 6)


def melody(s, stem, ch, t0, bpm, notes_, vel=80, cut=None, transpose=0, start_beat=0, end_beat=None):
    b = 60 / bpm
    for beat, length, p in notes_:
        if beat < start_beat or (end_beat is not None and beat >= end_beat):
            continue
        t = t0 + (beat - start_beat) * b
        if cut is not None and t >= cut:
            continue
        dur = length * b * 0.98
        if cut is not None:
            dur = min(dur, cut - t)
        s.note(stem, ch, t, dur, n(p) + transpose, vel)


def strum(s, stem, ch, t, chord_notes, vel, down=True, dur=0.45):
    seq = chord_notes if down else list(reversed(chord_notes))
    j = _jitter(t, len(chord_notes), 7)
    spread = 0.009 + 0.006 * abs(j)
    skip = 1 if (not down and j > 0.3) else 0  # light up-strums often miss the low string
    s.notes(stem, ch, t, dur, seq[skip:], vel * (1 + 0.12 * j), strum=spread)


def steel_voicing(name):
    root, q = ROOTS[name], QUAL[name]
    base = chord(root, q, 3)
    return [base[0] - 12] + base + [base[1] + 12]


def drums_bar(s, t0, bar_len=2.0, kick=True, snare=True, hats=True, open_hat=False, vel=1.0, crash=False):
    e = bar_len / 8
    if crash:
        s.note('rhythm', DRUMS, t0, 1.5, 49, 100 * vel)
    for k in range(8):
        t = t0 + k * e
        if hats:
            s.note('rhythm', DRUMS, t, 0.1, 42, (62 if k % 2 == 0 else 44) * vel)
        if kick and k in (0, 4, 5):
            s.note('rhythm', DRUMS, t, 0.2, 36, (110 if k != 5 else 80) * vel)
        if snare and k in (2, 6):
            s.note('rhythm', DRUMS, t, 0.2, 38, 100 * vel)
    if open_hat:
        s.note('rhythm', DRUMS, t0 + 7 * e, 0.3, 46, 60 * vel)


def fill(s, t0, length=0.5, vel=1.0):
    k = 0
    steps = int(length / 0.0625)
    for i in range(steps):
        tom = [50, 48, 47, 45][min(3, i * 4 // steps)]
        s.note('rhythm', DRUMS, t0 + i * 0.0625, 0.1, 38 if i % 2 else tom, (70 + 50 * i / steps) * vel)


def compose():
    s = Score(humanize={'piano': (0.012, 7), 'guitar': (0.012, 10), 'orch': (0.006, 4)})
    s.program('guitar', NYLON, 24, 110, 58, 70)
    s.program('guitar', STEEL, 25, 92, 70, 50)
    s.program('piano', PIANO, 0, 108, 64, 80)
    s.program('orch', STRINGS, 48, 100, 64, 80)
    s.program('orch', LEAD, 49, 104, 60, 80)
    s.program('orch', CHOIR, 52, 96, 64, 90)
    s.program('orch', BRASS, 61, 92, 66, 70)
    s.program('orch', PAD, 89, 90, 64, 90)
    s.program('orch', TIMP, 47, 110, 64, 60)
    s.program('orch', TREM, 44, 100, 64, 80)
    s.program('orch', LOWSTR, 43, 104, 64, 70)
    s.program('orch', HIT, 55, 100, 64, 60)
    s.program('orch', VIOLIN, 40, 92, 72, 80)
    s.program('rhythm', BASS, 33, 108, 64, 30)
    s.program('rhythm', DRUMS, 0, 104, 64, 40)

    # 0-14: his song on nylon guitar, cut off mid-phrase by the snap
    bpm = 80
    bar = 4 * 60 / bpm
    t0 = 0.6
    cut = EV['snap']
    for k in range(5):
        fingerpick(s, 'guitar', NYLON, t0 + k * bar, bpm, PROG[k], cut=cut)
    melody(s, 'guitar', NYLON, t0, bpm, THEME, vel=88, cut=cut)

    # 14-22: drone, a dissonant high cluster as the eyes open
    s.ramp('orch', TREM, 14.2, 20.0, 30, 105)
    s.ramp('orch', TREM, 20.0, 22.4, 105, 50)
    s.notes('orch', TREM, 14.3, 8.2, ['A2', 'E3'], 70)
    s.note('orch', LOWSTR, 14.3, 8.4, 'A1', 80)
    s.ramp('orch', VIOLIN, 15.4, 19.5, 20, 90)
    s.note('orch', VIOLIN, 15.5, 6.5, 'A5', 50)
    s.note('orch', VIOLIN, 17.0, 5.0, 'Bb5', 46)

    # 22-40: the years - piano ostinato over a falling bass, strings underneath
    bpm = 90
    bar = 4 * 60 / bpm
    e = bar / 8
    cells = [('A2', ['E4', 'A4', 'C5', 'A4']), ('G2', ['E4', 'A4', 'C5', 'A4']), ('F2', ['F4', 'A4', 'C5', 'A4']),
             ('E2', ['E4', 'G#4', 'B4', 'G#4'])]
    for b in range(7):
        tb = 22.0 + b * bar
        bass, cell = cells[b % 4]
        grow = b / 6
        s.note('piano', PIANO, tb, bar * 0.98, bass, 62 + 10 * grow)
        s.note('piano', PIANO, tb, bar * 0.98, n(bass) + 12, 50 + 8 * grow)
        for k in range(8):
            t = tb + k * e
            if t >= 39.9:
                break
            s.note('piano', PIANO, t, e * 1.6, cell[k % 4], 44 + 18 * grow + (8 if k == 0 else 0))
        if b >= 2:
            root = {'A2': 'A', 'G2': 'A', 'F2': 'F', 'E2': 'E'}[bass]
            q = {'A2': 'm', 'G2': 'm', 'F2': '', 'E2': ''}[bass]
            s.notes('orch', STRINGS, tb, bar, chord(root, q, 3), 46 + 14 * grow)
    s.ramp('orch', STRINGS, 27.0, 39.8, 40, 92)

    # 40-47: the mirror - a cluster swells, then everything stops at the crack
    s.ramp('orch', STRINGS, 40.0, 46.9, 25, 108)
    for t, p in ((40.0, 'A3'), (40.0, 'Bb3'), (42.0, 'B3'), (44.0, 'C4'), (45.5, 'C#4'), (44.0, 'A2')):
        s.note('orch', STRINGS, t, EV['crack'] - t, p, 80)
    s.ramp('orch', BRASS, 44.0, 46.9, 30, 98)
    s.note('orch', BRASS, 44.0, EV['crack'] - 44.0, 'A2', 70)
    s.note('orch', LOWSTR, 40.0, EV['crack'] - 40.0, 'A1', 62)
    for k in range(18):
        t = 45.8 + k * (1.2 / 18)
        s.note('orch', TIMP, t, 0.1, 'A2', 50 + 4 * k)
    s.ramp('orch', BRASS, 47.05, 47.1, 120, 127)  # restore expression for later sections
    s.ramp('orch', STRINGS, 47.05, 47.1, 124, 100)

    # 50-60: rock bottom - his theme, slow, on piano
    bpm = 60
    b = 1.0
    t0 = 50.6
    s.notes('piano', PIANO, t0, 4.0, ['A2', 'E3', 'A3'], 50)
    s.notes('piano', PIANO, t0 + 4, 4.0, ['F2', 'C3', 'A3'], 48)
    melody(s, 'piano', PIANO, t0, bpm, THEME, vel=62, end_beat=8)
    s.notes('piano', PIANO, 58.6, 2.0, ['C3', 'G3', 'D4'], 46)
    s.notes('piano', PIANO, 59.3, 1.4, ['E4'], 50)
    s.note('piano', PIANO, 58.6, 0.9, 'G4', 60)
    s.note('piano', PIANO, 59.3, 1.0, 'C5', 66)
    s.ramp('orch', PAD, 50.0, 52.0, 20, 60)
    s.notes('orch', PAD, 50.2, 8.4, ['A3', 'E4'], 40)
    s.notes('orch', PAD, 58.6, 3.4, ['C4', 'G4'], 44)

    # 60-70: Day 1 - a quiet chord, then the build, a held breath, the drop
    s.notes('piano', PIANO, 62.0, 3.0, ['C2', 'C4', 'E4', 'G4'], 58)
    s.ramp('orch', PAD, 62.0, 65.0, 50, 80)
    s.notes('orch', PAD, 62.0, 5.0, ['C3', 'G3', 'E4'], 50)
    s.ramp('rhythm', BASS, 65.0, 69.4, 40, 115)
    for k in range(int((69.5 - 65.0) / 0.25)):
        s.note('rhythm', BASS, 65.0 + k * 0.25, 0.2, 'C2', 90)
    s.ramp('orch', STRINGS, 65.0, 69.4, 40, 120)
    for t, p in ((65.0, 'C4'), (66.0, 'D4'), (67.0, 'E4'), (67.8, 'G4'), (68.5, 'A4'), (69.0, 'B4')):
        s.note('orch', STRINGS, t, 69.48 - t, p, 85)
    for k in range(24):
        t = 68.0 + k * (1.45 / 24)
        s.note('rhythm', DRUMS, t, 0.05, 38, 30 + 3.5 * k)
    s.ramp('orch', STRINGS, 69.5, 69.55, 120, 100)

    # 70-110: the grind - 120 BPM, Am F C G
    grind_prog = ['Am', 'F', 'C', 'G'] * 5
    for b, name in enumerate(grind_prog):
        tb = 70.0 + b * 2.0
        crash = b in (0, 4, 8, 12, 14, 16)
        if b < 2:
            drums_bar(s, tb, snare=False, crash=crash)
        else:
            drums_bar(s, tb, crash=crash, open_hat=b % 2 == 1)
        if b in (3, 7, 11, 13, 19):
            fill(s, tb + 1.5, 0.5)
        root = ROOTS[name]
        for k in range(8):
            s.note('rhythm', BASS, tb + k * 0.25, 0.22, n(f'{root}1') + (12 if root in 'C' else 0), 92)
        vs = steel_voicing(name)
        for k, (beat, down) in enumerate(((0, True), (1, True), (1.5, False), (2.5, False), (3, True), (3.5, False))):
            strum(s, 'guitar', STEEL, tb + beat * 0.5, vs, 82 if down else 64, down)
        if b >= 2:
            s.notes('orch', STRINGS, tb, 2.0, chord(root, QUAL[name], 3) + [n(f'{root}4')], 62 + (10 if b >= 14 else 0))
        if b >= 4:
            arp = chord(root, QUAL[name], 4) + [n(f'{root}5')]
            for k in range(8):
                s.note('piano', PIANO, tb + k * 0.25, 0.3, arp[[0, 1, 2, 3, 2, 1, 2, 3][k]], 52)
        if b >= 14:
            s.notes('orch', CHOIR, tb, 2.0, chord(root, QUAL[name], 4), 58)
            s.notes('orch', BRASS, tb, 0.35, chord(root, QUAL[name], 3), 84)
    melody(s, 'orch', LEAD, 86.0, 120, THEME, vel=92)
    melody(s, 'orch', LEAD, 102.0, 120, THEME, vel=100, transpose=12, end_beat=16)
    melody(s, 'orch', BRASS, 102.0, 120, THEME, vel=78, end_beat=16)
    s.ramp('orch', LEAD, 86.0, 87.0, 70, 112)

    # 110-120: the final stage - suspense, the eyes, the roar, a breath of silence
    s.ramp('orch', TREM, 110.0, 113.8, 40, 110)
    s.notes('orch', TREM, 110.2, 6.4, ['A2', 'E3'], 70)
    s.note('orch', LOWSTR, 110.2, 6.6, 'A1', 85)
    for k, t in enumerate((110.4, 112.0, 113.2)):
        s.note('orch', TIMP, t, 0.6, 'A2', 60 + 15 * k)
    s.ramp('orch', CHOIR, 112.6, 114.0, 30, 120)
    for k, p in enumerate(('A3', 'Bb3', 'C4', 'Db4', 'E4')):
        s.note('orch', CHOIR, 112.6 + k * 0.25, 114.0 - (112.6 + k * 0.25), p, 80)
    s.ramp('orch', BRASS, 112.6, 114.0, 30, 124)
    s.note('orch', BRASS, 112.6, 4.0, 'A1', 100)
    s.notes('orch', HIT, ROAR[1], 0.8, ['A3', 'C4', 'Eb4', 'A4'], 96)
    s.note('orch', TIMP, ROAR[1], 0.8, 'A2', 104)
    s.note('rhythm', DRUMS, ROAR[1], 2.0, 49, 98)
    s.ramp('orch', TREM, 114.0, 116.6, 120, 120)
    s.notes('orch', TREM, 114.0, 2.7, ['A2', 'Bb2', 'E3', 'F3'], 100)
    s.ramp('orch', VIOLIN, 116.4, 119.0, 70, 10)
    s.note('orch', VIOLIN, 116.6, 2.6, 'A6', 60)
    s.ramp('orch', BRASS, 117.0, 117.1, 124, 127)
    s.ramp('orch', CHOIR, 117.0, 117.1, 120, 127)
    s.ramp('orch', TREM, 116.7, 116.8, 120, 127)

    # 120-136: release - F G Am C, the triumphant theme, then warm and quiet as the lights come up
    rel_prog = ['F', 'G', 'Am', 'C', 'F', 'G', 'C', 'C']
    rel_melody = [(0, 2, 'A4'), (2, 1, 'C5'), (3, 1, 'F5'), (4, 2, 'G5'), (6, 1, 'F5'), (7, 1, 'D5'),
                  (8, 3, 'E5'), (11, 1, 'C5'), (12, 4, 'G5'), (16, 2, 'A5'), (18, 1, 'G5'), (19, 1, 'F5'),
                  (20, 2, 'G5'), (22, 2, 'D5'), (24, 2, 'E5'), (26, 1, 'D5'), (27, 1, 'C5'), (28, 4, 'C5')]
    for b, name in enumerate(rel_prog):
        tb = 120.0 + b * 2.0
        root, q = ROOTS[name], QUAL[name]
        if b < 2:
            drums_bar(s, tb, crash=(b == 0), open_hat=True)
        elif b < 4:
            drums_bar(s, tb, snare=False, vel=0.75, crash=(b == 2))
        elif b < 7:
            drums_bar(s, tb, snare=False, hats=True, kick=b < 6, vel=0.45)
        if b < 4:
            for k in range(8):
                s.note('rhythm', BASS, tb + k * 0.25, 0.22, n(f'{root}1') + (12 if root == 'C' else 0), 96)
        else:
            s.note('rhythm', BASS, tb, 1.9, n(f'{root}1') + (12 if root == 'C' else 0), 70)
        vs = steel_voicing(name)
        if b < 4:
            for beat, down in ((0, True), (1, True), (1.5, False), (2.5, False), (3, True), (3.5, False)):
                strum(s, 'guitar', STEEL, tb + beat * 0.5, vs, 92 if down else 70, down)
        else:
            strum(s, 'guitar', STEEL, tb, vs, 62, True, dur=1.8)
        s.notes('orch', STRINGS, tb, 2.0, chord(root, q, 3) + [n(f'{root}4')], 82 if b < 4 else 64)
        if b < 4:
            s.notes('orch', CHOIR, tb, 2.0, chord(root, q, 4), 70)
            s.notes('orch', BRASS, tb, 0.5, chord(root, q, 3), 90)
        if b >= 2:
            arp = chord(root, q, 4) + [n(f'{root}5')]
            for k in range(8):
                s.note('piano', PIANO, tb + k * 0.25, 0.4, arp[[0, 1, 2, 3, 2, 1, 2, 3][k]], 56 if b < 6 else 46)
    s.note('orch', TIMP, 120.0, 1.0, 'F2', 127)
    melody(s, 'orch', LEAD, 120.0, 120, rel_melody, vel=104)
    melody(s, 'orch', CHOIR, 120.0, 120, rel_melody, vel=70, end_beat=16)
    s.ramp('orch', STRINGS, 128.0, 136.2, 100, 60)
    s.ramp('orch', LEAD, 128.0, 136.2, 112, 70)

    # 136-148: the callback - his song again, the part that was cut off, and this time it ends
    bpm = 90
    bar = 4 * 60 / bpm
    t0 = 136.2
    for k, name in enumerate(['Am', 'F', 'C', 'G']):
        fingerpick(s, 'guitar', NYLON, t0 + k * bar, bpm, name, vel=56)
    melody(s, 'guitar', NYLON, t0, bpm, THEME, vel=84, start_beat=16)
    s.notes('guitar', NYLON, t0 + 4 * bar, 3.6, ['C3', 'G3', 'C4', 'E4', 'G4', 'C5'], 64, strum=0.07)
    s.ramp('orch', PAD, 136.0, 137.0, 40, 70)
    s.notes('orch', PAD, 136.2, 10.6, ['C3', 'G3'], 40)
    s.ramp('orch', PAD, 146.0, 147.9, 70, 30)

    # 148-160: title card - pad and piano, last chord
    for t, ch_notes in ((148.3, ['F2', 'C3', 'A3', 'C4']), (150.9, ['C2', 'G2', 'E3', 'G3']),
                        (153.4, ['A1', 'E2', 'C3', 'E3']), (155.8, ['C2', 'G2', 'C3', 'E3', 'G3', 'C4'])):
        s.notes('piano', PIANO, t, 2.6 if t < 155 else 4.0, ch_notes, 54)
        s.notes('orch', PAD, t, 2.6 if t < 155 else 3.9, [p for p in ch_notes[1:]], 46)
    s.ramp('orch', PAD, 148.2, 148.4, 30, 85)
    s.note('piano', PIANO, 155.8, 3.8, 'E5', 52)
    s.note('piano', PIANO, 156.5, 3.2, 'G5', 44)
    s.note('piano', PIANO, 157.2, 2.6, 'C6', 40)
    s.ramp('orch', PAD, 157.0, 159.6, 85, 0)
    s.ramp('piano', PIANO, 157.8, 159.8, 127, 30, control=11)
    return s


# --- effects, ambience and voices on the timeline --------------------------------------------------------

def place_sfx(mx):
    add = mx.add
    # ambience
    add('amb', sfx.room_tone(22.5, 1, 0.05), 0.0, fade_in=1.0, fade_out=0.6)
    add('amb', sfx.murmur(7.2, 10, 3, 0.10), 22.0, fade_in=0.3, fade_out=0.4)
    add('amb', sfx.room_tone(40.0, 2, 0.04), 60.0, fade_out=0.5)
    add('amb', sfx.city(8.2, 13, 0.16), 82.0, fade_in=0.2, fade_out=0.3)
    add('amb', sfx.cafe(8.2, 14, 0.14), 90.0, fade_in=0.2, fade_out=0.3)
    add('amb', sfx.murmur(12.0, 16, 5, 0.12), 124.2, fade_in=0.4, fade_out=2.0)
    add('amb', sfx.room_tone(12.0, 3, 0.05), 136.0, fade_in=0.3, fade_out=1.0)

    # bedroom: the snap, the shards, the eyes, the heartbeat
    add('sfx', sfx.snap(), EV['snap'], -5)
    add('sfx', sfx.shatter(0.8, 4), EV['notes_fall'] + 0.35, -8)
    eye_x = [150, 600, 640, 1180, 1640, 1730, 470, 1520, 90, 1050, 1560, 330]
    for k, t in enumerate(EV['eyes_open'] + [17.8, 18.2]):
        add('sfx', sfx.thoom(k), t, -11 - (k % 3), pan=(eye_x[k % len(eye_x)] / 960 - 1) * 0.8)
    add('sfx', sfx.heartbeat(76, 6.6), 15.4, -6, fade_in=1.5, fade_out=0.5)
    add('sfx', sfx.footstep(True, 2), EV['guitar_down'] + 1.1, -10)

    # hallway: he touches pen to paper, then stops
    add('sfx', sfx.scribble(0.45, 3), 22.5, -18)
    add('sfx', sfx.tap(3), 26.55, -14)
    add('sfx', sfx.footsteps([0.0, 0.55, 1.1, 1.65], seed=4), EV['walk_away'], -12)

    # montage: a clock that speeds up, whooshes on the cuts
    t, gap, k = 29.0, 0.5, 0
    while t < 39.9:
        add('sfx', sfx.tick(k % 2 == 1, k), t, -14 + 6 * (t - 29) / 11, pan=0.2 * (1 if k % 2 else -1))
        t += gap
        gap = max(0.2, gap * 0.94)
        k += 1
    for cut in EV['montage_cuts'][1:]:
        add('sfx', sfx.whoosh(0.5, 300, 2500, int(cut * 10)), cut - 0.25, -16)
    add('sfx', sfx.typing(1.8, 5), 30.8, -16)
    add('sfx', sfx.applause(1.8, 14, 6, 0.4), 32.6, -18)

    # mirror
    add('sfx', lp(sfx.glass_crack(), 7000), EV['crack'], -3)
    add('sfx', sfx.reverse_swell(1.0, 7), 49.0, -12)

    # day 1
    add('sfx', sfx.dust_blow(), EV['blow'], -4)
    add('sfx', sfx.twang(), EV['twang'], -6)
    add('sfx', sfx.beep(1200, 2), EV['rec'], -14)
    for k, t in enumerate(EV['eyes_return']):
        add('sfx', sfx.thoom(20 + k), t, -14, pan=0.4 * (1 if k % 2 else -1))
    add('sfx', sfx.heartbeat(112, 2.2), 67.3, -9, fade_in=0.3)
    add('sfx', sfx.riser(3.0), 66.5, -8)
    add('sfx', sfx.tap(9), EV['tap_post'], -6)
    add('sfx', sfx.bling(), 69.72, -10)
    add('sfx', sfx.drop_boom(), EV['drop'], -6)

    # the grind
    for k in range(12):
        add('sfx', sfx.shimmer(0.6, 30 + k, 18), 70.7 + k * 0.42, -18)
    add('sfx', sfx.whoosh(0.8, 500, 4000, 11), 72.5, -10)
    add('sfx', sfx.shatter(0.6, 12, 0.9), 73.3, -8)
    add('sfx', sfx.tap(14), 76.25, -14)
    add('sfx', sfx.ding(), EV['ding_lol'], -10)
    add('sfx', sfx.tap(15), 77.95, -14)
    add('sfx', sfx.tap(13), 79.25, -12)
    add('sfx', sfx.coin(), EV['coin'] + 0.42, -8)
    for k, t0 in enumerate((91.6, 93.2, 94.8)):
        add('sfx', sfx.whoosh(0.85, 500, 4000, 20 + k), t0, -10, pan=-0.4)
        add('sfx', sfx.shatter(0.6, 25 + k, 0.9), t0 + 0.85, -8)
    add('sfx', sfx.applause(1.5, 10, 8, 0.4), 96.6, -16)
    for cut in (100.0, 102.0, 104.0, 106.0, 108.0):
        add('sfx', sfx.whoosh(0.5, 300, 2500, int(cut)), cut - 0.25, -16)
    add('sfx', sfx.scribble(1.8, 6), 100.2, -11)
    add('sfx', sfx.bling(), 104.3, -14)
    add('sfx', sfx.scribble(1.3, 7), 108.3, -11)

    # the final stage
    add('sfx', sfx.curtain(), EV['curtain'], -8)
    add('sfx', sfx.footsteps([k * 0.55 for k in range(5)], wood=True, seed=8), 110.9, -10)
    for k in range(16):
        add('sfx', sfx.thoom(40 + k), EV['eye_wave'] + k * 0.08, -14, pan=(k % 5 - 2) * 0.35)
    add('sfx', sfx.heartbeat(104, 1.6), 116.5, -4, fade_out=0.4)
    add('sfx', sfx.breath_in(), EV['breath'], -6)
    add('sfx', sfx.impact(), EV['strum'], -4)
    add('sfx', sfx.shimmer(2.4, 60, 34), EV['strum'] + 0.1, -12)

    # lights up
    add('sfx', sfx.clunk(), EV['lights_up'], -6)
    add('sfx', sfx.applause(6.5, 60, 9, 0.6, swell=(0.4, 4.0)), EV['lights_up'] + 0.3, -10)


def place_voices(mx, work):
    cache = work / 'tts_cache'
    tmp = work / 'tmp'
    voice_for = {'hiss': ['Enceladus', 'Algenib'], 'deep': ['Charon', 'Fenrir']}
    windows = []
    for k, (text, t0, t1, style) in enumerate(WHISPERS):
        pan = [-0.5, 0.5, -0.3, 0.4, -0.4, -0.6, 0.6, -0.5, 0.0, 0.3, -0.3][k % 11]
        x = voices.line(text, style, voice_for[style][k % 2], cache, tmp, pan=pan, seed=k,
                        max_dur=max(1.1, t1 - t0 + 0.3))
        room = t1 - t0 + 0.6
        mx.add('voice', x, t0 + 0.02, -1, max_len=room + 1.5, fade_out=0.4)
        windows.append((t0, min(t1, t0 + len(x) / SR)))
    text, r0, r1 = ROAR
    rx = voices.roar(text, [('Charon', 0.8), ('Fenrir', 0.68), ('Algenib', 0.85), ('Enceladus', 0.75),
                            ('Kore', 0.95), ('Orus', 0.55)], cache, tmp, length=r1 - r0 - 0.3)
    mx.add('voice', rx, r0, -2, fade_out=0.6)
    windows.append((r0, r1))
    return windows


def build(out_dir):
    out_dir = Path(out_dir)
    work = out_dir / 'audio'
    work.mkdir(parents=True, exist_ok=True)
    stems = compose().render(work / 'stems')
    mx = Mix(DURATION)
    stem_gain = {'guitar': -1.0, 'piano': 7.0, 'orch': 1.5, 'rhythm': -2.0}
    for name, path in stems.items():
        mx.add('music', read_wav(path), 0.0, stem_gain.get(name, 0.0))
    place_sfx(mx)
    windows = place_voices(mx, work)
    # lift the quiet piano of rock bottom and the start of Day 1 for small speakers
    mx.automate('music', [(0.0, 0.0), (49.9, 0.0), (50.5, 4.0), (64.0, 4.0), (65.0, 0.0)])
    mx.duck('music', windows, -10.0, 0.25)
    mx.duck('sfx', windows, -4.0, 0.2)
    mx.duck('amb', windows, -6.0, 0.25)
    master = mx.render({'music': 0.0, 'sfx': -6.0, 'amb': -8.0, 'voice': 3.0}, level={'music': -22.0},
                       ceiling=0.6)
    return write_wav(work / 'mix.wav', master)


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
