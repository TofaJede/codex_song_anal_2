from PyQt5 import QtWidgets, QtCore
from .analysis import analyze_audio
from .midi_export import export_midi
from .piano_roll import PianoRollWidget

class DropLabel(QtWidgets.QLabel):
    file_dropped = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__('Drop audio file here or click to browse')
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet('border:2px dashed rgb(100,51,162); padding:40px;')
        self.setAcceptDrops(True)
        self.setToolTip('Drop an audio file here or click to browse')
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        self.file_dropped.emit(url.toLocalFile())
    def mousePressEvent(self, event):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open audio', filter='Audio Files (*.wav *.mp3)')
        if path:
            self.file_dropped.emit(path)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Song Analyzer')
        self.setStyleSheet('background-color:#1e1e1e; color:white;')
        accent = 'rgb(100,51,162)'
        self.file_path = None
        self.segments = []

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        self.drop = DropLabel()
        self.drop.file_dropped.connect(self.set_file)
        layout.addWidget(self.drop)

        buttons = QtWidgets.QHBoxLayout()
        self.analyze_btn = QtWidgets.QPushButton('Analyze Song')
        self.export_btn = QtWidgets.QPushButton('Export as MIDI')
        self.reset_btn = QtWidgets.QPushButton('Reset')
        for btn in (self.analyze_btn, self.export_btn, self.reset_btn):
            btn.setStyleSheet(f'background-color:{accent}; color:white; padding:8px;')
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            buttons.addWidget(btn)
        layout.addLayout(buttons)

        self.analyze_btn.setToolTip('Analyze the selected audio file')
        self.export_btn.setToolTip('Export detected notes as a MIDI file')
        self.reset_btn.setToolTip('Clear the current song and analysis')

        self.info = QtWidgets.QTextEdit()
        self.info.setReadOnly(True)
        self.info.setToolTip('Displays details about the analyzed segments')
        layout.addWidget(self.info)

        self.piano = PianoRollWidget()
        self.piano.setToolTip('Visual piano roll of detected notes')
        layout.addWidget(self.piano)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setStyleSheet(f'QProgressBar::chunk{{background-color:{accent};}}')
        layout.addWidget(self.progress)

        self.setCentralWidget(central)
        self.analyze_btn.clicked.connect(self.analyze)
        self.export_btn.clicked.connect(self.export)
        self.reset_btn.clicked.connect(self.reset)

    def set_file(self, path: str):
        self.file_path = path
        self.info.setText(f'Selected file: {path}')

    def analyze(self):
        if not self.file_path:
            return
        dialog = QtWidgets.QProgressDialog('Analyzing song...', None, 0, 0, self)
        dialog.setWindowTitle('Please wait')
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.setCancelButton(None)
        dialog.show()
        QtWidgets.QApplication.processEvents()
        self.segments = analyze_audio(self.file_path)
        info_lines = []
        for seg in self.segments:
            notes = ', '.join(n.name for n in seg.notes[:10])
            line = f"{seg.name}: Key {seg.key}, Tempo {seg.tempo:.1f} BPM\nNotes: {notes}"
            info_lines.append(line)
        self.info.setText('\n\n'.join(info_lines))
        self.piano.display(self.segments)
        dialog.close()

    def export(self):
        if not self.segments:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save MIDI', filter='MIDI Files (*.mid)')
        if path:
            self.progress.setFormat('Exporting...')
            self.progress.setVisible(True)
            QtWidgets.QApplication.processEvents()
            export_midi(self.segments, path)
            self.progress.setVisible(False)

    def reset(self):
        self.file_path = None
        self.segments = []
        self.info.clear()
        self.piano.plot.clear()
        self.progress.setVisible(False)
