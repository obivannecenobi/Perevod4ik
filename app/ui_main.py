"""Main application window UI setup."""

from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

import styles
from settings import AppSettings, SettingsDialog


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, settings: AppSettings | None = None):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        styles.init()

        self.settings = settings or AppSettings.load()

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)

        # Menu bar
        self.menu_bar = MainWindow.menuBar()
        self.settings_menu = self.menu_bar.addMenu("")
        self.settings_action = QtGui.QAction(parent=MainWindow)
        self.settings_menu.addAction(self.settings_action)
        self.settings_action.triggered.connect(self._open_settings)

        # Navigation bar
        self.nav_layout = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.chapter_combo = QtWidgets.QComboBox(parent=self.centralwidget)
        self.next_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.nav_layout.addWidget(self.prev_btn)
        self.nav_layout.addWidget(self.chapter_combo)
        self.nav_layout.addWidget(self.next_btn)
        self.main_layout.addLayout(self.nav_layout)

        # Splitter separating original and translation/glossary
        self.h_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal, parent=self.centralwidget
        )
        self.main_layout.addWidget(self.h_splitter)

        # Original text section
        self.original_widget = QtWidgets.QWidget()
        self.original_layout = QtWidgets.QVBoxLayout(self.original_widget)
        self.original_label = QtWidgets.QLabel(parent=self.original_widget)
        self.original_label.setFont(QtGui.QFont(styles.HEADER_FONT, 14))
        self.original_edit = QtWidgets.QTextEdit(parent=self.original_widget)
        self.original_counter = QtWidgets.QLabel("0", parent=self.original_widget)
        self.original_counter.setObjectName("counter")
        self.original_counter.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.original_layout.addWidget(self.original_label)
        self.original_layout.addWidget(self.original_edit)
        self.original_layout.addWidget(self.original_counter)
        self.h_splitter.addWidget(self.original_widget)

        # Right splitter dividing translation/prompt and glossary
        self.right_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical, parent=self.centralwidget
        )
        self.h_splitter.addWidget(self.right_splitter)

        # Translation block with mini-prompt
        self.translation_widget = QtWidgets.QWidget()
        self.translation_layout = QtWidgets.QVBoxLayout(self.translation_widget)
        self.translation_label = QtWidgets.QLabel(parent=self.translation_widget)
        self.translation_label.setFont(QtGui.QFont(styles.HEADER_FONT, 14))
        self.translation_edit = QtWidgets.QTextEdit(parent=self.translation_widget)
        self.translation_counter = QtWidgets.QLabel("0", parent=self.translation_widget)
        self.translation_counter.setObjectName("counter")
        self.translation_counter.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.mini_prompt_label = QtWidgets.QLabel(parent=self.translation_widget)
        self.mini_prompt_edit = QtWidgets.QTextEdit(parent=self.translation_widget)
        self.translation_layout.addWidget(self.translation_label)
        self.translation_layout.addWidget(self.translation_edit)
        self.translation_layout.addWidget(self.translation_counter)
        self.translation_layout.addWidget(self.mini_prompt_label)
        self.translation_layout.addWidget(self.mini_prompt_edit)
        self.right_splitter.addWidget(self.translation_widget)

        # Glossary panel
        self.glossary = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.glossary.setReadOnly(True)
        self.glossary.setObjectName("glossary")
        self.right_splitter.addWidget(self.glossary)

        # Status/timer area
        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_layout.addStretch()
        self.timer_label = QtWidgets.QLabel("00:00", parent=self.centralwidget)
        self.status_layout.addWidget(self.timer_label)
        self.main_layout.addLayout(self.status_layout)

        # Fonts
        base_font = QtGui.QFont(styles.INTER_FONT, 10)
        self.original_edit.setFont(base_font)
        self.translation_edit.setFont(base_font)
        self.mini_prompt_edit.setFont(base_font)
        self.glossary.setFont(base_font)

        # Style sheet applying colours
        style_sheet = f"""
        QWidget {{
            background-color: {styles.APP_BACKGROUND};
            color: {styles.TEXT_COLOR};
            font-family: {styles.INTER_FONT};
        }}
        QTextEdit {{
            background-color: {styles.FIELD_BACKGROUND};
            color: {styles.TEXT_COLOR};
        }}
        QTextEdit#glossary {{
            background-color: {styles.GLOSSARY_BACKGROUND};
        }}
        QLabel#counter {{
            color: rgba(255, 255, 255, 128);
            font-size: 10px;
        }}
        """
        self.centralwidget.setStyleSheet(style_sheet)

        # Timer and character counters
        self.elapsed = 0
        self.timer = QtCore.QTimer(MainWindow)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_timer)

        self.original_edit.textChanged.connect(self._update_original_counter)
        self.translation_edit.textChanged.connect(self._update_translation_counter)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    # --- internal helpers -------------------------------------------------
    def _update_timer(self) -> None:
        self.elapsed += 1
        minutes, seconds = divmod(self.elapsed, 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _start_timer(self) -> None:
        if not self.timer.isActive():
            self.timer.start()

    def _update_original_counter(self) -> None:
        self._start_timer()
        self.original_counter.setText(str(len(self.original_edit.toPlainText())))

    def _update_translation_counter(self) -> None:
        self._start_timer()
        self.translation_counter.setText(str(len(self.translation_edit.toPlainText())))

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self.centralwidget)
        dialog.exec()

    # --- translations -----------------------------------------------------
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Main Window"))
        self.prev_btn.setText(_translate("MainWindow", "⦉"))
        self.next_btn.setText(_translate("MainWindow", "⦊"))
        self.original_label.setText(_translate("MainWindow", "Оригинал"))
        self.translation_label.setText(_translate("MainWindow", "Перевод"))
        self.mini_prompt_label.setText(_translate("MainWindow", "Мини-промпт"))
        self.settings_menu.setTitle(_translate("MainWindow", "Настройки"))
        self.settings_action.setText(_translate("MainWindow", "Параметры…"))

