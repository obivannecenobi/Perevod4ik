import sys
from PyQt6 import QtWidgets
from ui_main import Ui_MainWindow


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
