import pretty_midi
from .analysis import SegmentAnalysis


def export_midi(segments, path: str) -> None:
    pm = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for seg in segments:
        for note in seg.notes:
            pitch = pretty_midi.note_name_to_number(note.name)
            start = note.start
            end = note.start + note.duration
            instrument.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end))
    pm.instruments.append(instrument)
    pm.write(path)
