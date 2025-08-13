import sys
from PyQt6 import QtWidgets
from ui_main import Ui_MainWindow
from settings import AppSettings


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    settings = AppSettings.load()
    ui = Ui_MainWindow()
    ui.setupUi(window, settings)
    app.aboutToQuit.connect(settings.save)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
