"""MIDI export utilities.

This module attempts to use the external ``pretty_midi`` package for writing
MIDI files.  If the dependency is unavailable we fall back to a very small
built-in implementation that supports the subset of features needed by the
application.  The fallback is intentionally lightweight so that users can run
the project without installing additional packages.
"""

from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hinting only
    from .analysis import SegmentAnalysis

try:  # pragma: no cover - optional dependency
    import pretty_midi  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - used when dependency missing
    from . import pretty_midi_stub as pretty_midi


def export_midi(segments: Iterable['SegmentAnalysis'], path: str) -> None:
    """Export a collection of :class:`SegmentAnalysis` objects to a MIDI file."""
    pm = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for seg in segments:
        for note in seg.notes:
            start = note.start
            end = note.start + note.duration
            instrument.notes.append(
                pretty_midi.Note(velocity=100, pitch=note.midi, start=start, end=end)
            )
    pm.instruments.append(instrument)
    pm.write(path)
