import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import librosa
from typing import List
from .analysis import SegmentAnalysis, PercussionEvent

pg.setConfigOption('background', '#121212')
pg.setConfigOption('foreground', 'w')

class PianoRollWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.melody_plot = self.addPlot(row=0, col=0)
        self.melody_plot.setLabel('bottom', 'Time', units='s')
        self.melody_plot.setLabel('left', 'Pitch')
        self.melody_plot.setLimits(xMin=0, yMin=0, yMax=127)
        self.melody_plot.showGrid(x=True, y=True, alpha=0.3)
        self.perc_plot = self.addPlot(row=1, col=0)
        self.perc_plot.setXLink(self.melody_plot)
        self.perc_plot.setLabel('bottom', 'Time', units='s')
        self.perc_plot.setLimits(xMin=0, yMin=0, yMax=1)
        self.perc_plot.hideAxis('left')
        self.perc_plot.showGrid(x=True, alpha=0.3)
        self.plot = self.melody_plot

    def clear(self):
        self.melody_plot.clear()
        self.perc_plot.clear()

    def display(self, segments: List[SegmentAnalysis], percussion: List[PercussionEvent]):
        self.clear()
        colors = {
            'Intro': (100, 51, 162),
            'Mid': (51, 162, 100),
            'Outro': (162, 51, 100),
        }
        for seg in segments:
            color = colors.get(seg.name, (200, 200, 200))
            brush = pg.mkBrush(*color)
            for note in seg.notes:
                pitch = librosa.note_to_midi(note.name)
                rect = QtWidgets.QGraphicsRectItem(note.start, pitch, note.duration, 1)
                rect.setBrush(brush)
                rect.setPen(pg.mkPen(None))
                self.melody_plot.addItem(rect)
        perc_colors = {
            'Kick': 'b',
            'Snare/Clap': 'r',
            'Hi-hat': 'y',
        }
        for event in percussion:
            pen = pg.mkPen(perc_colors.get(event.hit_type, 'w'), width=2)
            line = pg.InfiniteLine(event.time, angle=90, pen=pen)
            line.setToolTip(f"{event.time:.2f}s - {event.hit_type}")
            self.perc_plot.addItem(line)
