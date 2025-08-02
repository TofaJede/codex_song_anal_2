import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from typing import List

from .analysis import SegmentAnalysis, PercussionEvent

pg.setConfigOption("background", "#121212")
pg.setConfigOption("foreground", "w")


class PianoRollWidget(QtWidgets.QWidget):
    """Widget displaying note events in piano-roll or guitar-tab style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.graph = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph)

        self.melody_plot = self.graph.addPlot(row=0, col=0)
        self.melody_plot.setLabel("bottom", "Time", units="s")
        self.melody_plot.setLabel("left", "Pitch")
        self.melody_plot.setLimits(xMin=0, yMin=0, yMax=127)
        self.melody_plot.showGrid(x=True, y=True, alpha=0.3)
        self.melody_plot.setMouseEnabled(x=True, y=False)

        self.perc_plot = self.graph.addPlot(row=1, col=0)
        self.perc_plot.setXLink(self.melody_plot)
        self.perc_plot.setLabel("bottom", "Time", units="s")
        self.perc_plot.setLimits(xMin=0, yMin=0, yMax=1)
        self.perc_plot.hideAxis("left")
        self.perc_plot.showGrid(x=True, alpha=0.3)

        self.scroll = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        layout.addWidget(self.scroll)
        self.scroll.valueChanged.connect(self._on_scroll)

        self.melody_plot.sigXRangeChanged.connect(self._update_scroll_range)

        self.mode = "piano"
        self.segments: List[SegmentAnalysis] = []
        self.percussion: List[PercussionEvent] = []
        self.total_length = 0.0

    # ------------------------------------------------------------------
    def clear(self):
        self.melody_plot.clear()
        self.perc_plot.clear()
        self.segments = []
        self.percussion = []
        self.total_length = 0.0
        self._update_scroll_range()

    # ------------------------------------------------------------------
    def set_mode(self, mode: str):
        if mode not in {"piano", "guitar"}:
            return
        if self.mode != mode:
            self.mode = mode
            self._draw()

    # ------------------------------------------------------------------
    def display(self, segments: List[SegmentAnalysis], percussion: List[PercussionEvent]):
        self.segments = segments
        self.percussion = percussion
        self._draw()

    # ------------------------------------------------------------------
    def _draw(self):
        self.melody_plot.clear()
        self.perc_plot.clear()
        colors = {
            "Intro": (100, 51, 162),
            "Mid": (51, 162, 100),
            "Outro": (162, 51, 100),
        }

        if self.mode == "piano":
            self.melody_plot.setLabel("left", "Pitch")
            self.melody_plot.setLimits(yMin=0, yMax=127)
            self.melody_plot.getAxis("left").setTicks([])
            for seg in self.segments:
                color = colors.get(seg.name, (200, 200, 200))
                brush = pg.mkBrush(*color)
                for note in seg.notes:
                    rect = QtWidgets.QGraphicsRectItem(
                        note.start, note.midi, note.duration, 1
                    )
                    rect.setBrush(brush)
                    rect.setPen(pg.mkPen(None))
                    self.melody_plot.addItem(rect)
        else:  # guitar mode
            self.melody_plot.setLabel("left", "String")
            self.melody_plot.setLimits(yMin=0, yMax=6)
            ticks = [(i, str(i)) for i in range(1, 7)]
            self.melody_plot.getAxis("left").setTicks([ticks])
            for seg in self.segments:
                color = colors.get(seg.name, (200, 200, 200))
                brush = pg.mkBrush(*color)
                for note in seg.notes:
                    if note.string is None:
                        continue
                    rect = QtWidgets.QGraphicsRectItem(
                        note.start, note.string - 1, note.duration, 1
                    )
                    rect.setBrush(brush)
                    rect.setPen(pg.mkPen(None))
                    self.melody_plot.addItem(rect)
                    if note.fret is not None:
                        text = pg.TextItem(str(note.fret), color="w", anchor=(0, 0.5))
                        text.setPos(note.start, note.string - 0.5)
                        self.melody_plot.addItem(text)

        perc_colors = {
            "Kick": "b",
            "Snare/Clap": "r",
            "Hi-hat": "y",
        }
        for event in self.percussion:
            pen = pg.mkPen(perc_colors.get(event.hit_type, "w"), width=2)
            line = pg.InfiniteLine(event.time, angle=90, pen=pen)
            line.setToolTip(f"{event.time:.2f}s - {event.hit_type}")
            self.perc_plot.addItem(line)

        max_note = max(
            (n.start + n.duration for seg in self.segments for n in seg.notes),
            default=0,
        )
        max_perc = max((p.time for p in self.percussion), default=0)
        self.total_length = max(max_note, max_perc)
        self.melody_plot.setLimits(xMin=0, xMax=self.total_length)
        self.perc_plot.setLimits(xMin=0, xMax=self.total_length)
        if self.total_length > 0:
            self.melody_plot.setXRange(0, min(self.total_length, 10), padding=0)
        self._update_scroll_range()

    # ------------------------------------------------------------------
    def _on_scroll(self, value: int):
        width = self.melody_plot.viewRange()[0][1] - self.melody_plot.viewRange()[0][0]
        self.melody_plot.setXRange(value / 100.0, value / 100.0 + width, padding=0)

    # ------------------------------------------------------------------
    def _update_scroll_range(self, *_):
        if self.total_length <= 0:
            self.scroll.setRange(0, 0)
            self.scroll.setValue(0)
            return
        view_start, view_end = self.melody_plot.viewRange()[0]
        width = view_end - view_start
        max_start = max(self.total_length - width, 0)
        self.scroll.blockSignals(True)
        self.scroll.setRange(0, int(max_start * 100))
        self.scroll.setPageStep(int(width * 100))
        self.scroll.setValue(int(view_start * 100))
        self.scroll.blockSignals(False)
