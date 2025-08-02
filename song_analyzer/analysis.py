import numpy as np
import librosa
from dataclasses import dataclass, field
from typing import List, Tuple

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


@dataclass
class PercussionEvent:
    time: float
    hit_type: str


def extract_percussion_events(y: np.ndarray, sr: int) -> List[PercussionEvent]:
    """Detect basic percussion hits in an audio signal."""
    _, y_perc = librosa.effects.hpss(y)
    onset_env = librosa.onset.onset_strength(y=y_perc, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    S = np.abs(librosa.stft(y_perc))
    freqs = librosa.fft_frequencies(sr=sr)
    events: List[PercussionEvent] = []
    for frame in onset_frames:
        if frame >= S.shape[1]:
            continue
        spectrum = S[:, frame]
        kick = spectrum[(freqs >= 50) & (freqs <= 150)].sum()
        snare = spectrum[(freqs >= 200) & (freqs <= 800)].sum()
        hihat = spectrum[freqs >= 5000].sum()
        energies = {
            "Kick": kick,
            "Snare/Clap": snare,
            "Hi-hat": hihat,
        }
        hit_type = max(energies, key=energies.get)
        time = float(librosa.frames_to_time(frame, sr=sr))
        events.append(PercussionEvent(time=time, hit_type=hit_type))
    return events


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


def _estimate_key_fallback(segment: np.ndarray, sr: int) -> str:
    """Fallback key estimator using chroma profile correlation.

    Returns a string like "C major" or "A minor". If the estimation fails, the
    string "Unknown" is returned.
    """
    try:
        chroma = librosa.feature.chroma_cqt(y=segment, sr=sr)
        profile = chroma.mean(axis=1)
        major_template = np.array(
            [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        )
        minor_template = np.array(
            [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        )
        keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        major_scores = [
            np.corrcoef(np.roll(major_template, i), profile)[0, 1] for i in range(12)
        ]
        minor_scores = [
            np.corrcoef(np.roll(minor_template, i), profile)[0, 1] for i in range(12)
        ]
        if np.nanmax(major_scores) >= np.nanmax(minor_scores):
            return f"{keys[int(np.nanargmax(major_scores))]} major"
        return f"{keys[int(np.nanargmax(minor_scores))]} minor"
    except Exception:
        return "Unknown"


def analyze_segment(segment: np.ndarray, sr: int, name: str, offset: float) -> SegmentAnalysis:
    tempo, _ = librosa.beat.beat_track(y=segment, sr=sr)
    try:
        key = librosa.key.estimate_key(segment, sr=sr)
    except AttributeError:
        key = _estimate_key_fallback(segment, sr)
    f0, _, _ = librosa.pyin(segment,
                           fmin=librosa.note_to_hz('C2'),
                           fmax=librosa.note_to_hz('C7'))
    times = librosa.times_like(f0, sr=sr)
    mask = ~np.isnan(f0)
    notes = librosa.hz_to_note(f0[mask])
    times = times[mask]
    events = _group_notes(times, notes, offset)
    return SegmentAnalysis(name=name, key=key, tempo=float(tempo), notes=events)


def analyze_audio(path: str) -> Tuple[List[SegmentAnalysis], List[PercussionEvent]]:
    y, sr = librosa.load(path)
    total = len(y)
    third = total // 3
    segments = [
        ("Intro", y[:third], 0.0),
        ("Mid", y[third: 2 * third], third / sr),
        ("Outro", y[2 * third:], 2 * third / sr),
    ]
    analyses: List[SegmentAnalysis] = []
    for name, seg, offset in segments:
        analyses.append(analyze_segment(seg, sr, name, offset))
    percussion = extract_percussion_events(y, sr)
    return analyses, percussion
