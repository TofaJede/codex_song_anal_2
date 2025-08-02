"""Text export utilities.

This module provides functions to export note events to plain text, optionally
including guitar tablature positions.
"""

from typing import Iterable, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hinting only
    from .analysis import SegmentAnalysis

# MIDI numbers for standard guitar tuning E2 A2 D3 G3 B3 E4
STANDARD_TUNING = {
    6: 40,  # String 6 - E2
    5: 45,  # String 5 - A2
    4: 50,  # String 4 - D3
    3: 55,  # String 3 - G3
    2: 59,  # String 2 - B3
    1: 64,  # String 1 - E4
}


def midi_to_tab(midi: int) -> Optional[Tuple[int, int]]:
    """Convert a MIDI note number to a guitar string and fret.

    Returns ``None`` if the note cannot be played within the first 24 frets.
    """
    best: Optional[Tuple[int, int]] = None
    for string, open_note in STANDARD_TUNING.items():
        fret = midi - open_note
        if 0 <= fret <= 24:
            if best is None or fret < best[1]:
                best = (string, fret)
    return best


def _format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"[{minutes:02d}:{secs:04.1f}]"


def export_text(
    segments: Iterable["SegmentAnalysis"], path: str, include_tab: bool = False
) -> None:
    """Export note events to a plain text file.

    Each line is formatted as ``"[mm:ss.s] NOTE (durations)"``. When
    ``include_tab`` is ``True`` and a note is playable on a standard tuned
    guitar, the string and fret numbers are appended.
    """
    lines = []
    for seg in segments:
        for note in seg.notes:
            line = f"{_format_time(note.start)} {note.name} ({note.duration:.1f}s)"
            if include_tab:
                if note.string is not None and note.fret is not None:
                    line += f" - string {note.string} fret {note.fret}"
                else:
                    pos = midi_to_tab(note.midi)
                    if pos is not None:
                        string, fret = pos
                        line += f" - string {string} fret {fret}"
            lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
