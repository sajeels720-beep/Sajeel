"""Compose with notes placed in seconds; render stems through a General MIDI soundfont."""
from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path

import mido

SOUNDFONT = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
TICKS_PER_SEC = 960  # 480 ticks/beat at 120 BPM

NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def n(name):
    """'A4' -> 69, 'C#5' -> 73, 'Bb3' -> 58."""
    if isinstance(name, int):
        return name
    letter = name[0].upper()
    rest = name[1:]
    acc = 0
    while rest and rest[0] in '#b':
        acc += 1 if rest[0] == '#' else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + NAMES[letter] + acc


# common chord shapes as semitone offsets
CHORDS = {
    '': (0, 4, 7), 'm': (0, 3, 7), 'sus2': (0, 2, 7), 'sus4': (0, 5, 7), '7': (0, 4, 7, 10),
    'maj7': (0, 4, 7, 11), 'm7': (0, 3, 7, 10), 'add9': (0, 4, 7, 14), 'madd9': (0, 3, 7, 14),
}


def chord(root, quality='', octave=3, inversion=0):
    base = n(f'{root}{octave}')
    notes = [base + i for i in CHORDS[quality]]
    for _ in range(inversion):
        notes = notes[1:] + [notes[0] + 12]
    return notes


def _jitter(*keys):
    h = 2166136261
    for k in keys:
        h = ((h ^ (int(k * 1000) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (h % 10007) / 10007.0 * 2 - 1


class Score:
    def __init__(self, humanize=None):
        self.events = defaultdict(list)    # stem -> [(sec, order, mido.Message)]
        self.programs = defaultdict(dict)  # stem -> {channel: program}
        self.humanize = humanize or {}     # stem -> (max timing offset s, max velocity offset)

    def program(self, stem, ch, program, volume=100, pan=64, reverb=60):
        self.programs[stem][ch] = (program, volume, pan, reverb)

    def note(self, stem, ch, t, dur, pitch, vel=80):
        p = n(pitch)
        if stem in self.humanize and ch != 9:
            dt, dv = self.humanize[stem]
            t = max(0.0, t + dt * _jitter(t, p, 1))
            vel += dv * _jitter(t, p, 2)
        vel = int(max(1, min(127, vel)))
        self.events[stem].append((t, 1, mido.Message('note_on', channel=ch, note=p, velocity=vel)))
        self.events[stem].append((t + max(0.02, dur), 0, mido.Message('note_off', channel=ch, note=p, velocity=0)))

    def notes(self, stem, ch, t, dur, pitches, vel=80, strum=0.0):
        for k, p in enumerate(pitches):
            self.note(stem, ch, t + k * strum, dur - k * strum, p, vel)

    def cc(self, stem, ch, t, control, value):
        self.events[stem].append((t, 0, mido.Message('control_change', channel=ch, control=control,
                                                     value=int(max(0, min(127, value))))))

    def ramp(self, stem, ch, t0, t1, v0, v1, control=11, steps=48):
        for k in range(steps + 1):
            u = k / steps
            self.cc(stem, ch, t0 + (t1 - t0) * u, control, v0 + (v1 - v0) * u)

    def bend(self, stem, ch, t, value):
        self.events[stem].append((t, 0, mido.Message('pitchwheel', channel=ch, pitch=int(value))))

    def write_midi(self, stem, path):
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
        for ch, (prog, vol, pan, rev) in sorted(self.programs[stem].items()):
            if ch != 9:
                track.append(mido.Message('program_change', channel=ch, program=prog, time=0))
            track.append(mido.Message('control_change', channel=ch, control=7, value=vol, time=0))
            track.append(mido.Message('control_change', channel=ch, control=10, value=pan, time=0))
            track.append(mido.Message('control_change', channel=ch, control=91, value=rev, time=0))
            track.append(mido.Message('control_change', channel=ch, control=11, value=127, time=0))
        last = 0
        for t, _, msg in sorted(self.events[stem], key=lambda e: (e[0], e[1])):
            tick = int(round(max(0.0, t) * TICKS_PER_SEC))
            track.append(msg.copy(time=tick - last))
            last = tick
        track.append(mido.MetaMessage('end_of_track', time=TICKS_PER_SEC * 2))
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        mid.save(str(path))
        return path

    def render(self, out_dir, gain=0.45, sr=48000):
        out_dir = Path(out_dir)
        stems = {}
        for stem in self.events:
            mid = self.write_midi(stem, out_dir / f'{stem}.mid')
            wav = out_dir / f'{stem}.wav'
            subprocess.run(['fluidsynth', '-ni', '-q', '-g', str(gain), '-r', str(sr), '-F', str(wav),
                            SOUNDFONT, str(mid)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            stems[stem] = wav
        return stems
