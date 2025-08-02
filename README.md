# Song Analyzer

A desktop application that splits an audio file into three segments (Intro, Mid, Outro),
extracts the dominant melody and tempo, and visualizes the result on a piano-roll.
The melody can be exported as a MIDI file for further editing.

## Features
- Drag and drop audio file loading
- Melody extraction with `librosa`
- Key and tempo estimation for each segment
- Scrollable piano-roll visualization using `pyqtgraph`
- Export reconstructed melody to `.mid`

## Usage
```
pip install -r requirements.txt
python main.py
```

## Modules
- `song_analyzer/analysis.py` – audio analysis logic
- `song_analyzer/gui.py` – PyQt UI
- `song_analyzer/piano_roll.py` – piano roll widget
- `song_analyzer/midi_export.py` – MIDI export utility

## Notes
This project requires packages such as `librosa`, `PyQt5`, `pyqtgraph` and `pretty_midi` which
may need system dependencies to install. The application does not provide audio playback.
