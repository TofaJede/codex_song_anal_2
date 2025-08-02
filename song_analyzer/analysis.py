import numpy as np
import librosa
from dataclasses import dataclass, field
from typing import List

@dataclass
class NoteEvent:
    name: str
    start: float
    duration: float

@dataclass
class SegmentAnalysis:
    name: str
    key: str
    tempo: float
    notes: List[NoteEvent] = field(default_factory=list)


def _group_notes(times: np.ndarray, notes: np.ndarray, offset: float) -> List[NoteEvent]:
    events: List[NoteEvent] = []
    if len(notes) == 0:
        return events
    current = notes[0]
    start_time = times[0]
    for n, t in zip(notes[1:], times[1:]):
        if n != current:
            events.append(NoteEvent(current, start_time + offset, t - start_time))
            current = n
            start_time = t
    events.append(NoteEvent(current, start_time + offset, times[-1] - start_time))
    return events


def analyze_segment(segment: np.ndarray, sr: int, name: str, offset: float) -> SegmentAnalysis:
    tempo, _ = librosa.beat.beat_track(y=segment, sr=sr)
    key = librosa.key.estimate_key(segment, sr=sr)
    f0, _, _ = librosa.pyin(segment,
                           fmin=librosa.note_to_hz('C2'),
                           fmax=librosa.note_to_hz('C7'))
    times = librosa.times_like(f0, sr=sr)
    mask = ~np.isnan(f0)
    notes = librosa.hz_to_note(f0[mask])
    times = times[mask]
    events = _group_notes(times, notes, offset)
    return SegmentAnalysis(name=name, key=key, tempo=float(tempo), notes=events)


def analyze_audio(path: str) -> List[SegmentAnalysis]:
    y, sr = librosa.load(path)
    total = len(y)
    third = total // 3
    segments = [
        ('Intro', y[:third], 0.0),
        ('Mid', y[third: 2 * third], third / sr),
        ('Outro', y[2 * third:], 2 * third / sr),
    ]
    analyses: List[SegmentAnalysis] = []
    for name, seg, offset in segments:
        analyses.append(analyze_segment(seg, sr, name, offset))
    return analyses
