import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
import librosa

pg.setConfigOption('background', '#121212')
pg.setConfigOption('foreground', 'w')

class PianoRollWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot = self.addPlot()
        self.plot.setLabel('bottom', 'Time', units='s')
        self.plot.setLabel('left', 'Pitch')
        self.plot.setLimits(xMin=0, yMin=0, yMax=127)
        self.plot.showGrid(x=True, y=True, alpha=0.3)

    def display(self, segments):
        self.plot.clear()
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
                rect = QtGui.QGraphicsRectItem(note.start, pitch, note.duration, 1)
                rect.setBrush(brush)
                rect.setPen(pg.mkPen(None))
                self.plot.addItem(rect)
