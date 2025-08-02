from __future__ import annotations

"""A minimal stand-in for :mod:`pretty_midi`.

This module implements the tiny subset of the ``pretty_midi`` API that is
required by :func:`song_analyzer.midi_export.export_midi`.  It allows the
project to export very simple MIDI files without the third‑party dependency.
The implementation is intentionally lightweight and does not aim to be a full
MIDI solution.
"""

from dataclasses import dataclass
from typing import List
import struct

# Mapping from note names to semitone numbers within an octave
_NOTE_MAP = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9,
    'A#': 10, 'Bb': 10, 'B': 11,
}


def note_name_to_number(name: str) -> int:
    """Convert a note name (e.g. ``C4``) to a MIDI note number.

    ``librosa`` (used by the analysis module) returns note names containing
    Unicode accidentals such as ``"♯"`` and ``"♭"``.  The original implementation
    of this stub only recognised ASCII ``#`` and ``b`` characters which caused a
    ``KeyError`` for names like ``"C♯4"`` when exporting to MIDI.  To mirror the
    behaviour of :func:`pretty_midi.note_name_to_number` we normalise these
    characters before looking up the semitone value.
    """

    # Separate note and octave.  The simple slicing works because this project
    # only deals with octave numbers in the range 0-9.
    note = name[:-1]
    octave = int(name[-1])

    # Normalise Unicode accidentals to ASCII representations.
    note = note.replace("♯", "#").replace("♭", "b")

    if note not in _NOTE_MAP:
        raise ValueError(f"Unknown note name: {name}")

    return _NOTE_MAP[note] + 12 * (octave + 1)


def _var_len(value: int) -> bytes:
    """Encode an integer as a MIDI variable-length quantity."""
    buffer = value & 0x7F
    result = bytearray()
    while value >> 7:
        value >>= 7
        buffer <<= 8
        buffer |= ((value & 0x7F) | 0x80)
    while True:
        result.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes(result)


@dataclass
class Note:
    velocity: int
    pitch: int
    start: float
    end: float


class Instrument:
    """Collection of notes played by a single instrument."""

    def __init__(self, program: int = 0) -> None:
        self.program = program
        self.notes: List[Note] = []


class PrettyMIDI:
    """Very small MIDI file writer compatible with ``pretty_midi`` usage."""

    def __init__(self, tempo: float = 120.0, ticks_per_beat: int = 480) -> None:
        self.tempo = tempo
        self.ticks_per_beat = ticks_per_beat
        self.instruments: List[Instrument] = []

    def _seconds_to_ticks(self, seconds: float) -> int:
        return int(seconds * self.ticks_per_beat * self.tempo / 60.0)

    def write(self, path: str) -> None:
        events = []
        # Build events from all instruments
        for inst in self.instruments:
            events.append((0, 0, bytes([0xC0, inst.program])))  # program change
            for note in inst.notes:
                start = self._seconds_to_ticks(note.start)
                end = self._seconds_to_ticks(note.end)
                events.append((start, 1, bytes([0x90, note.pitch, note.velocity])))
                events.append((end, 2, bytes([0x80, note.pitch, 0])))

        events.sort(key=lambda x: (x[0], x[1]))
        track = bytearray()

        # tempo meta event
        tempo_us = int(60_000_000 / self.tempo)
        track += _var_len(0) + b"\xFF\x51\x03" + tempo_us.to_bytes(3, "big")

        last = 0
        for tick, _, data in events:
            delta = tick - last
            track += _var_len(delta) + data
            last = tick

        track += _var_len(0) + b"\xFF\x2F\x00"  # end of track

        header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, self.ticks_per_beat)
        track_chunk = b"MTrk" + struct.pack(">I", len(track)) + track

        with open(path, "wb") as fh:
            fh.write(header + track_chunk)
