from PyQt5 import QtWidgets
from song_analyzer.gui import MainWindow


def main():
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.resize(900, 700)
    win.show()
    app.exec_()


if __name__ == '__main__':
    main()
