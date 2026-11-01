"""Soundtrack for 'He's Waiting.': score, effects, whispers and the mix.

Dark and cinematic, and its own sound (none of films 1-3's piano, orchestral strings, horns, timpani or taiko):
- the old man's pocket watch ticks once a second all film long; from Day 1 it is the score's pulse;
- low drones under everything (the "soundtrack" and sweep pads, contrabass, a synth choir), heavy synth-brass
  braams with sub booms on the big moments, deep melodic toms and reverse cymbals for the builds;
- the shadow's music is a hypnotic echoing arpeggio over a sub pulse that wears out night after night and
  speeds up like tape in the time-lapse;
- the old man's theme, in D minor on an English horn, carries the weight: alone under his words at rock bottom,
  over the climb on synth strings and voices, and in D major, full, only when the sun breaks.
The characters never speak aloud; their lines are captions. Only the shadow whispers.
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
SOUNDTRACK, SWEEP, CBASS, SVOICE = 0, 1, 2, 3            # 'drone'
SSTR2, SSTR1 = 0, 1                                      # 'strings'
EHORN, OOH, BELLS = 0, 1, 2                              # 'lead'
SBRASS, SBRASS2 = 0, 1                                   # 'brass'
TOMS, REVCYM, KIT = 0, 1, 9                              # 'perc' (orchestra kit on 10)
PULSE = 0                                                # 'pulse'
ECHO, SHBASS, SHPAD = 0, 1, 2                            # 'shadow': its hypnotic loop
PH_LEAD, PH_BASS, PH_KEYS, PH_KIT = 0, 1, 2, 9           # 'phone': the clips on his screen

# The old man's theme in eighth notes (six to a bar): (start, length, pitch). D minor; the major form at sunrise.
THEME_MINOR = [(0, 2, 'A4'), (2, 1, 'D5'), (3, 3, 'F5'),
               (6, 2, 'E5'), (8, 1, 'D5'), (9, 3, 'A4'),
               (12, 2, 'Bb4'), (14, 1, 'D5'), (15, 3, 'G5'),
               (18, 2, 'F5'), (20, 1, 'E5'), (21, 3, 'C#5'),
               (24, 2, 'A4'), (26, 1, 'D5'), (27, 3, 'F5'),
               (30, 2, 'A5'), (32, 1, 'G5'), (33, 3, 'F5'),
               (36, 2, 'D5'), (38, 1, 'F5'), (39, 2, 'E5'), (41, 1, 'C#5'),
               (42, 6, 'D5')]
THEME_MAJOR = [(st, ln, p.replace('F5', 'F#5').replace('Bb4', 'B4')) for st, ln, p in THEME_MINOR]
MINOR_CHORDS = [('D', 'm'), ('Bb', ''), ('G', 'm'), ('A', ''), ('D', 'm'), ('Bb', ''), ('G', 'm'), ('D', 'm')]
MAJOR_CHORDS = [('D', ''), ('G', ''), ('E', 'm'), ('A', ''), ('D', ''), ('G', ''), ('E', 'm'), ('D', '')]
SHADOW_CHORDS = [('D', 'm'), ('Bb', ''), ('G', 'm'), ('A', '')]


def theme(s, stem, ch, t0, eighth, vel=80, transpose=0, bars=None, legato=0.95, swell=0.0, major=False):
    b0, b1 = bars or (0, 8)
    for st, ln, p in (THEME_MAJOR if major else THEME_MINOR):
        if not (b0 * 6 <= st < b1 * 6):
            continue
        t = t0 + (st - b0 * 6) * eighth
        v = vel + swell * (st - b0 * 6) / max(1, (b1 - b0) * 6)
        s.note(stem, ch, t, ln * eighth * legato, n(p) + transpose, v)


def low(name, octave=1):
    return n(f'{name}{octave}')


def pad(s, stem, ch, t, dur, notes_, vel, swell_in=0.0, fade_out=0.0):
    s.notes(stem, ch, t, dur, notes_, vel)
    if swell_in:
        s.ramp(stem, ch, t, t + swell_in, 0, 127, steps=24)
    if fade_out:
        s.ramp(stem, ch, t + dur - fade_out, t + dur, 127, 0, steps=24)
        s.cc(stem, ch, t + dur + 0.02, 11, 127)


# --- the score -----------------------------------------------------------------------------------------------------

def shadow_bar(s, tb, k, vel=1.0):
    """One 3-second bar of the shadow's loop: an echoing arpeggio over a sub pulse (80 BPM)."""
    name, q = SHADOW_CHORDS[k % 4]
    tones = chord(name, q, 4)
    pattern = [tones[0] + 12, tones[2], tones[1], tones[2]]
    e = 0.375                                   # eighth notes at 80 BPM
    for j in range(8):
        s.note('shadow', ECHO, tb + j * e, 0.3, pattern[j % 4] - (12 if j >= 4 else 0) + 12, 62 * vel)
    for j in range(4):
        s.note('shadow', SHBASS, tb + j * 0.75, 0.5, low(name, 1) + (12 if name in ('A', 'G') else 0), 84 * vel)
    s.notes('shadow', SHPAD, tb, 3.0, [low(name, 2), low(name, 2) + 7], 50 * vel)


def compose():
    s = Score(humanize={'lead': (0.012, 6), 'strings': (0.006, 4)})
    s.program('drone', SOUNDTRACK, 97, 92, 64, 110)
    s.program('drone', SWEEP, 95, 84, 64, 110)
    s.program('drone', CBASS, 43, 100, 64, 70)
    s.program('drone', SVOICE, 54, 84, 64, 110)
    s.program('strings', SSTR2, 51, 96, 58, 100)
    s.program('strings', SSTR1, 50, 86, 70, 100)
    s.program('lead', EHORN, 69, 104, 62, 80)
    s.program('lead', OOH, 53, 92, 64, 110)
    s.program('lead', BELLS, 14, 90, 70, 100)
    s.program('brass', SBRASS, 62, 100, 64, 90)
    s.program('brass', SBRASS2, 63, 92, 64, 90)
    s.program('perc', TOMS, 117, 104, 64, 70)
    s.program('perc', REVCYM, 119, 96, 64, 60)
    s.program('perc', KIT, 48, 100, 64, 70)
    s.program('pulse', PULSE, 39, 100, 64, 40)
    s.program('shadow', ECHO, 102, 92, 50, 90)
    s.program('shadow', SHBASS, 39, 100, 64, 30)
    s.program('shadow', SHPAD, 97, 76, 64, 100)
    s.program('phone', PH_LEAD, 80, 90, 64, 10)
    s.program('phone', PH_BASS, 38, 90, 64, 10)
    s.program('phone', PH_KEYS, 0, 90, 64, 10)
    s.program('phone', PH_KIT, 0, 90, 64, 10)

    # --- the hook: a low drone creeps in under the phone; the figure in the dark; his face; the drain; the shadow
    phone_clips(s, EV['swipes'], 0.3, 19.4)
    pad(s, 'drone', CBASS, 1.0, 18.3, [n('D1'), n('D2')], 62, swell_in=4.0, fade_out=0.6)
    pad(s, 'drone', SOUNDTRACK, 3.0, 16.3, [n('D2'), n('A2'), n('F3')], 58, swell_in=3.0, fade_out=0.4)
    pad(s, 'drone', SVOICE, 4.0, 4.6, [n('D4'), n('Eb4')], 52, swell_in=2.5, fade_out=1.2)    # dread, unresolved
    pad(s, 'strings', SSTR2, 8.8, 3.6, [n('D3'), n('A3'), n('E4'), n('F4')], 66, swell_in=0.4, fade_out=0.8)
    theme(s, 'lead', EHORN, 9.4, 0.5, 66, bars=(0, 1))                   # three notes as his face ages
    for k in range(int((16.2 - 12.0) / 0.5)):                            # the drain: a pulse like a pulled heart
        s.note('pulse', PULSE, 12.0 + 0.5 * k, 0.3, n('D1') if k % 2 == 0 else n('D2'), 70 + 3 * k)
    pad(s, 'strings', SSTR2, 12.0, 4.2, [n('D3'), n('F3'), n('Bb3')], 60, swell_in=3.5)
    for k in range(2):                                                    # the shadow's loop creeps in
        shadow_bar(s, 14.0 + 3 * k, k, vel=0.7 + 0.2 * k)
    s.note('perc', REVCYM, 17.4, 2.0, n('C4'), 90)                       # into the title
    # --- the title: a braam, a low bell
    title_hit(s, 19.42)
    s.note('lead', BELLS, 19.45, 3.0, n('D3'), 80)

    # --- the loop: the shadow's music, night after night (it wears out in the mix)
    for k in range(7):
        shadow_bar(s, 23.0 + 3 * k, k, vel=1.0 if k < 6 else 1.1)
    pad(s, 'drone', CBASS, 23.0, 19.0, [n('D1')], 54, swell_in=2.0, fade_out=0.2)
    phone_clips(s, [23.3, 24.4, 25.6, 26.9, 29.4, 30.5, 31.6, 33.8, 34.7, 35.6], 23.0, 36.5, quiet=True)
    s.note('perc', REVCYM, 40.0, 2.0, n('C4'), 96)                       # the time-lapse slams shut

    # --- the mirror: dread, a stinger when the old man appears, a held cluster while he looks
    pad(s, 'drone', SWEEP, 43.0, 13.4, [n('D2'), n('Ab2')], 52, swell_in=3.0, fade_out=0.3)
    pad(s, 'drone', CBASS, 43.0, 13.4, [n('D1')], 58, swell_in=2.0, fade_out=0.3)
    stinger(s, 46.0)
    pad(s, 'strings', SSTR2, 46.2, 5.6, [n('C#4'), n('D4'), n('G#4')], 56, swell_in=0.6, fade_out=0.6)
    pad(s, 'drone', SVOICE, 49.0, 3.0, [n('A4'), n('Bb4')], 58, swell_in=1.0, fade_out=0.6)
    s.note('perc', TOMS, 50.62, 1.5, n('D2'), 110)                       # the palm hits the glass
    pad(s, 'drone', SWEEP, 53.6, 2.8, [n('D2'), n('Eb2'), n('A2')], 66, swell_in=0.8, fade_out=0.2)
    # --- turning his back: the shadow's loop leaks from under the blanket; a slow heart in the drone
    for k in range(2):
        shadow_bar(s, 57.0 + 3 * k, k + 2, vel=0.9)
    pad(s, 'drone', CBASS, 57.0, 10.0, [n('D1')], 60, swell_in=1.0)
    # --- rock bottom
    phone_clips(s, [67.3, 68.9, 70.6, 71.9], 67.0, 74.8, quiet=True)
    pad(s, 'drone', SOUNDTRACK, 67.0, 5.2, [n('D2'), n('A2')], 56, fade_out=0.15)
    # after the silence, under his words (captions only): low strings, then the theme alone on the English horn
    pad(s, 'strings', SSTR2, 78.8, 3.2, [n('D2'), n('A2'), n('F3')], 54, swell_in=2.0)
    for k, (name, q) in enumerate((('B', 'b'), ('G', 'm'), ('A', ''))):
        root = {'B': 'Bb'}.get(name, name)
        pad(s, 'strings', SSTR2, 82.0 + 2.2 * k, 2.2, chord(root, '' if root == 'Bb' else q, 3), 56 + 3 * k)
    pad(s, 'drone', CBASS, 78.8, 10.8, [n('D1'), n('D2')], 56, swell_in=2.0, fade_out=0.4)
    theme(s, 'lead', EHORN, 81.4, 0.62, 68, bars=(0, 2))
    pad(s, 'strings', SSTR1, 88.6, 1.0, [n('D4'), n('F4'), n('A4')], 50, fade_out=0.8)

    # --- Day 1: the theme, slow, three beats a bar on the tick; from dark toward hope
    t0 = 93.0
    for b in range(6):
        name, q = MINOR_CHORDS[b % 8]
        tb = t0 + 3 * b
        pad(s, 'strings', SSTR2, tb, 3.0, chord(name, q, 3), 50 + 4 * b)
        s.note('drone', CBASS, tb, 2.9, low(name, 2 if name in ('D', 'A', 'G') else 1), 58)
    theme(s, 'lead', EHORN, 96.0, 0.5, 72, bars=(0, 4), swell=10)
    s.note('perc', REVCYM, EV['curtains'] - 1.9, 2.0, n('C4'), 80)
    s.notes('lead', BELLS, EV['curtains'] + 0.05, 3.0, [n('D4'), n('A4')], 74)
    pad(s, 'lead', OOH, EV['curtains'], 4.0, [n('D4'), n('F4'), n('A4')], 54, swell_in=1.2, fade_out=1.0)
    for k in range(12):                                                  # the pulse quickens as he sets off
        s.note('pulse', PULSE, 105.0 + 0.5 * k, 0.3, n('D1') if k % 2 == 0 else n('D2'), 60 + 3 * k)
    for k in range(6):
        s.note('pulse', PULSE, 109.0 + k / 3, 0.22, n('D2'), 80)

    # --- the climb: 6/8 on the tick (a bar = 2 s): a driving low ostinato, toms, the theme
    climb(s, 111.0, 135.0)
    # --- the last temptation: the music stops for the rain; the shadow's loop tries to come back, warped
    for k in range(2):
        shadow_bar(s, 137.0 + 3 * k, k, vel=0.85)
    alarm(s, 135.4, 143.0)
    alarm(s, 27.5, 28.1)
    s.note('perc', REVCYM, 143.0, 2.0, n('C4'), 110)                     # he sits up through it: into the drop
    # --- the rise
    climb(s, 145.0, 153.0, full=True)
    # the trailhead: only a dark pad and the tick, then the pulse as they set off
    pad(s, 'drone', SOUNDTRACK, 153.0, 4.2, [n('D2'), n('A2'), n('E3')], 54, swell_in=0.5, fade_out=0.5)
    pad(s, 'drone', CBASS, 153.0, 4.0, [n('D1')], 58)
    for k in range(6):
        s.note('pulse', PULSE, 156.0 + k / 3, 0.22, n('D2'), 66 + 3 * k)
    # --- the ascent: a relentless build
    ascent(s, 157.0, 171.0)
    # --- the sunrise: D major at last
    sunrise(s, 171.0)
    # --- the epilogue: night again, heavy and quiet; his words on a held chord, then hope
    pad(s, 'drone', SOUNDTRACK, 193.0, 10.0, [n('D2'), n('A2')], 50, swell_in=2.0, fade_out=0.3)
    pad(s, 'strings', SSTR2, 195.6, 3.8, [n('D3'), n('F3'), n('A3'), n('E4')], 54, swell_in=1.5)
    theme(s, 'lead', EHORN, 195.8, 0.55, 60, bars=(0, 1))
    pad(s, 'strings', SSTR2, 199.4, 3.6, [n('D3'), n('F#3'), n('A3'), n('D4')], 58, swell_in=0.8)   # ...proud.
    pad(s, 'lead', OOH, 199.6, 3.4, [n('D4'), n('F#4'), n('A4')], 50, swell_in=1.0, fade_out=1.0)
    # --- the title card
    title_hit(s, 203.2, major=True)
    s.note('lead', BELLS, 203.3, 4.0, n('D3'), 76)
    pad(s, 'strings', SSTR2, 203.3, 7.5, [n('D2'), n('A2'), n('D3'), n('F#3'), n('A3')], 60, fade_out=3.0)
    return s


def title_hit(s, t, major=False):
    """A braam: low synth brass and a deep tom, with a bass drum and cymbal from the orchestra kit."""
    third = n('F#2') if major else n('F2')
    s.notes('brass', SBRASS, t, 3.2, [n('D1'), n('A1'), n('D2'), third, n('A2')], 118)
    s.notes('brass', SBRASS2, t, 3.0, [n('D2'), n('A2')], 104)
    s.ramp('brass', SBRASS, t + 1.6, t + 3.1, 127, 0, steps=24)
    s.cc('brass', SBRASS, t + 3.3, 11, 127)
    s.note('perc', TOMS, t, 2.0, n('D1'), 120)
    s.note('perc', KIT, t, 1.5, 36, 120)
    s.note('perc', KIT, t, 2.5, 49, 90)


def stinger(s, t):
    """A sudden shock: a braam with a dissonant synth choir on top."""
    s.notes('brass', SBRASS, t, 2.4, [n('D1'), n('Ab1'), n('D2')], 116)
    s.ramp('brass', SBRASS, t + 1.0, t + 2.3, 127, 0, steps=20)
    s.cc('brass', SBRASS, t + 2.5, 11, 127)
    s.notes('drone', SVOICE, t, 2.2, [n('D5'), n('Eb5'), n('Ab5')], 76)
    s.note('perc', TOMS, t, 1.6, n('D1'), 118)
    s.note('perc', KIT, t, 2.0, 49, 84)


def climb(s, t0, t1, full=False):
    """The theme in 6/8 on the tick: dotted quarter = 1 s, so a bar is 2 s and an eighth a third of a second."""
    e = 1 / 3
    nb = int(round((t1 - t0) / 2))
    for b in range(nb):
        tb = t0 + 2 * b
        name, q = MINOR_CHORDS[b % 8]
        root1 = low(name, 1) + (12 if name in ('G', 'A', 'Bb') else 0)
        # the driving low ostinato: synth bass in eighths, contrabass on the dotted beats
        for k in range(6):
            s.note('pulse', PULSE, tb + k * e, 0.25, root1 + (12 if k in (2, 5) else 0), 76 + (12 if k in (0, 3) else 0))
        s.note('drone', CBASS, tb, 1.9, root1, 74)
        pad(s, 'strings', SSTR2, tb, 2.0, chord(name, q, 3), 52 + (10 if full else 0) + 8 * (tb >= EV['days'][4]))
        busy = full or tb >= t0 + 4
        if busy:
            s.note('perc', TOMS, tb, 0.6, n('D2'), 92 if full else 76)
            s.note('perc', TOMS, tb + 1.0, 0.6, n('A1'), 84 if full else 66)
        if full or tb >= EV['days'][4]:
            s.note('perc', KIT, tb, 0.4, 36, 104 if full else 86)
            if b % 2 == 1:
                for k in range(3):
                    s.note('perc', TOMS, tb + 1.0 + k * e, 0.3, n('D2') + 5 - 2 * k, 70 + 8 * k)
        if full:
            s.notes('brass', SBRASS, tb, 1.9, chord(name, q, 2), 88)
            if b % 4 == 0:
                s.note('perc', KIT, tb, 2.0, 49, 84)
        if b % 4 == 3 and not full:
            s.note('perc', REVCYM, tb, 2.0, n('C4'), 70)
    if not full:
        theme(s, 'lead', EHORN, t0, e, 76, bars=(0, 8))
        if t1 - t0 > 16:
            theme(s, 'lead', OOH, t0 + 16, e, 72, bars=(0, 4))
            theme(s, 'strings', SSTR1, t0 + 16, e, 64, bars=(0, 4))
    else:
        title_hit(s, t0)
        theme(s, 'lead', OOH, t0, e, 86, bars=(0, 4))
        theme(s, 'brass', SBRASS2, t0, e, 92, bars=(0, 4))
        theme(s, 'strings', SSTR1, t0, e, 76, bars=(0, 4), transpose=12)


def ascent(s, t0, t1):
    e = 1 / 3
    nb = int(round((t1 - t0) / 2))
    prog = [('D', 'm'), ('Bb', ''), ('G', 'm'), ('A', ''), ('D', 'm'), ('Bb', ''), ('C', ''), ('A', 'sus4')]
    for b in range(nb):
        tb = t0 + 2 * b
        name, q = prog[b % len(prog)]
        rise = b / max(1, nb - 1)
        root1 = low(name, 1) + (12 if name in ('G', 'A', 'Bb', 'C') else 0)
        for k in range(6):
            s.note('pulse', PULSE, tb + k * e, 0.25, root1 + (12 if k % 3 == 2 else 0), 78 + 30 * rise)
        pad(s, 'strings', SSTR2, tb, 2.0, chord(name, q, 3), 54 + 30 * rise)
        pad(s, 'drone', SVOICE, tb, 2.0, chord(name, q, 4), 44 + 30 * rise)
        s.note('drone', CBASS, tb, 1.9, root1, 74)
        s.note('perc', TOMS, tb, 0.6, n('D2'), 80 + 30 * rise)
        s.note('perc', TOMS, tb + 1.0, 0.6, n('A1'), 72 + 30 * rise)
        if rise > 0.35:
            s.note('perc', KIT, tb, 0.4, 36, 90 + 20 * rise)
            s.notes('brass', SBRASS, tb, 1.9, chord(name, q, 2), 70 + 30 * rise)
        if b >= nb - 2:
            for k in range(6):
                s.note('perc', TOMS, tb + k * e, 0.3, n('D2') + (k % 3) * 2, 86 + 5 * k)
    s.note('perc', REVCYM, t1 - 2.0, 2.0, n('C4'), 100)


def sunrise(s, t0):
    """171-193: the hush at the top, the sun at 173 in D major, the gift, the fading, alone."""
    pad(s, 'drone', SWEEP, t0, 2.0, [n('A3'), n('E4')], 44)               # a breath before the sun
    t = EV['sun_breaks']
    title_hit(s, t, major=True)
    s.notes('lead', BELLS, t, 4.0, [n('D4'), n('A4')], 96)
    e = 0.5
    theme(s, 'lead', OOH, t, e, 92, bars=(0, 2), major=True)
    theme(s, 'strings', SSTR1, t, e, 84, bars=(0, 2), major=True, transpose=12)
    theme(s, 'brass', SBRASS2, t, e, 80, bars=(0, 2), major=True, transpose=-12)
    for b in range(4):
        tb = t + 3 * b
        name, q = MAJOR_CHORDS[(b if b < 2 else b + 4) % 8]
        pad(s, 'strings', SSTR2, tb, 3.0, chord(name, q, 3), 72)
        s.note('drone', CBASS, tb, 2.9, low(name, 1) + (12 if name in ('G', 'A', 'E') else 0), 74)
        for k in range(9):
            s.note('pulse', PULSE, tb + k / 3, 0.25, low(name, 2), 56)
    # the gift and his hand on the shoulder: the English horn sings the last phrase, in major
    theme(s, 'lead', EHORN, 179.0, 0.5, 74, bars=(6, 8), major=True)
    pad(s, 'strings', SSTR2, 179.0, 6.0, [n('D3'), n('F#3'), n('A3'), n('D4')], 58, fade_out=1.5)
    # fading into the light: high voices and a bell, then the last chord holds while he stands alone
    pad(s, 'lead', OOH, EV['fade'][0] + 0.8, 5.2, [n('A4'), n('D5'), n('F#5')], 62, swell_in=1.5, fade_out=1.5)
    s.notes('lead', BELLS, EV['fade'][0] + 0.8, 4.0, [n('D5')], 70)
    pad(s, 'strings', SSTR2, 186.0, 7.0, [n('D2'), n('A2'), n('D3'), n('F#3'), n('A3')], 56, fade_out=2.5)


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
    # (the old man and the boy never speak aloud: their lines are captions, carried by the music)
    return windows


# --- the build ----------------------------------------------------------------------------------------------------------

def shadow_versions(x):
    """The shadow's loop four ways: close (it leans in), worn (night after night), from the phone, leaking out
    from under the blanket."""
    near = reverb(lp(x, 7000), wet=0.18, length=2.4, decay=0.6)
    worn = tape(lp(x, 2400), wobble=0.012, rate=0.45)
    phone = stereo(phone_eq(x.mean(axis=1)), 0.35)
    leak = stereo(phone_eq(lp(x.mean(axis=1), 2000)) * 0.7, 0.0)
    return near, worn, phone, leak


def braam(seed=0, dur=3.6, major=False):
    """The weight under a big hit: detuned low saws closing down through a filter, and a sub that drops."""
    t = t_axis(dur)
    out = np.zeros(len(t), np.float32)
    r = rng(seed)
    for f in (36.71, 55.0, 73.42, 110.0, 92.5 if major else 87.31):
        for det in (-0.6, 0.0, 0.7):
            ph = 2 * np.pi * (f + det + r.uniform(-0.1, 0.1)) * t
            out += ((ph / (2 * np.pi)) % 1.0 * 2 - 1).astype(np.float32) * 0.12
    cut = 2400 * np.exp(-t / 0.5) + 220
    y = np.zeros_like(out)
    block = 2048
    for i in range(0, len(out), block):
        y[i:i + block] = lp(out[i:i + block + 256], float(cut[min(i, len(cut) - 1)]))[: len(out[i:i + block])]
    y = soft_clip(y * 1.6, 1.4) * env_ad(dur, 0.04, dur - 0.1, 1.6)
    sub = sine(glide(62, 34, 1.8), 1.8) * env_exp(1.8, 0.9, 0.01)
    y[: len(sub)] += sub * 0.9
    return norm(y, 0.9)


def build(out_dir):
    out_dir = Path(out_dir)
    work = out_dir / 'audio'
    work.mkdir(parents=True, exist_ok=True)
    stems = compose().render(work / 'stems')
    mx = Mix(DURATION)
    stem_gain = {'drone': 0.0, 'strings': 1.0, 'lead': 2.0, 'brass': 2.0, 'perc': 0.0, 'pulse': -1.0}
    for name, path in stems.items():
        if name in ('shadow', 'phone'):
            continue
        mx.add('music', read_wav(path), 0.0, stem_gain.get(name, 0.0))
    # the shadow's loop, routed by scene
    sh = read_wav(stems['shadow'])
    if sh.ndim == 1:
        sh = stereo(sh)
    near, worn, phone, leak = shadow_versions(sh)
    n_ = len(sh)
    crack = crackle(DURATION + 2, seed=3, level=0.04)[:n_]

    def seg(src, t0, t1, g, fi=0.05, fo=0.05):
        a, b = secs(t0), min(n_, secs(t1))
        mx.add('shadow', src[a:b], t0, g, fade_in=fi, fade_out=fo)

    seg(phone, 14.0, 16.4, -8, fi=0.6)                   # it starts on his phone...
    seg(near, 16.0, 19.4, -3, fi=0.5, fo=0.02)           # ...then it is in the room, as the shadow leans in
    seg(near, 23.0, 29.0, -3)
    seg(worn, 29.0, 36.5, -4, fi=0.3)
    tl = speed_ramp(worn, 36.5, 42.0, 1.0, 2.6, stop=0.45)
    mx.add('shadow', tl, 36.5, -3, fade_out=0.02)
    seg(leak, 57.0, 63.0, -10, fi=0.4, fo=0.6)
    seg(near, 137.0, 141.6, -8, fi=1.2, fo=0.05)
    mx.add('shadow', tape(near[secs(137.0):secs(141.6)], wobble=0.05, rate=0.9), 137.0, -13, fade_in=1.0, fade_out=0.05)
    mx.add('shadow', crack[secs(23.0):secs(42.0)], 23.0, -8, fade_out=0.05)
    # the phone's clips
    ph = read_wav(stems['phone'])
    ph = stereo(phone_eq(ph.mean(axis=1) if ph.ndim == 2 else ph), 0.3)
    mx.add('phone', ph, 0.0, 0.0)
    place_sfx(mx)
    # the weight under the big hits
    for k, (t, g, major) in enumerate(((9.0, -10, False), (19.42, -4, False), (EV['old_in_mirror'], -6, False),
                                       (EV['drop'], -5, False), (EV['sun_breaks'], -4, True), (203.2, -6, True))):
        mx.add('sfx', stereo(braam(k, major=major)), t, g)
    windows = place_voices(mx, work)
    # levels by scene
    mx.automate('sfx', [(0.0, 5.0), (7.6, 5.0), (9.0, 0.0)])
    mx.automate('phone', [(0.0, 10.0), (3.4, 8.0), (7.6, 0.0), (12.0, -2.0), (16.2, -10.0), (19.3, -12.0), (19.4, -40.0),
                          (23.0, -14.0), (36.5, -14.0), (36.6, -40.0), (66.9, -40.0), (67.0, -12.0), (72.2, -14.0),
                          (74.8, -40.0), (135.3, -40.0), (135.4, -6.0), (143.0, -6.0), (143.1, -40.0)])
    mx.automate('music', [(0.0, 2.0), (3.0, 3.0), (19.4, 3.0), (23.0, 0.0), (78.8, 3.0), (89.6, 3.0), (92.6, 2.0),
                          (111.0, 0.0), (134.95, 0.0), (135.0, -40.0), (142.9, -40.0), (143.0, -2.0), (145.0, 2.0),
                          (153.0, 0.0), (172.0, 0.0), (173.0, 3.0), (183.0, 1.0), (193.0, 1.0), (203.0, 2.0)])
    mx.automate('shadow', [(0.0, 0.0), (42.0, 0.0), (42.4, -60.0), (56.9, -60.0), (57.0, 0.0)])
    mx.duck('music', windows, -6.0, 0.25)
    mx.duck('shadow', windows, -7.0, 0.25)
    mx.duck('phone', windows, -8.0, 0.2)
    mx.duck('sfx', windows, -3.0, 0.2)
    mx.duck('amb', windows, -6.0, 0.25)
    # silence where the watch stops: nothing but breath until he lifts his head
    mx.duck('music', [(EV['watch_stops'] + 0.02, 78.8)], -40.0, 0.05)
    mx.duck('music', [(EV['phone_dies'] - 0.05, EV['dawn'] + 0.4)], -40.0, 0.15)
    master = mx.render({'music': 0.0, 'shadow': -3.0, 'phone': -6.0, 'sfx': -6.0, 'amb': -8.0, 'voice': 3.0},
                       level={'music': -21.0}, ceiling=0.6)
    return write_wav(work / 'mix.wav', master)


if __name__ == '__main__':
    print(build(HERE.parents[1] / 'output' / HERE.name))
