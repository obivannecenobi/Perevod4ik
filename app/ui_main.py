"""Main application window UI setup."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon

from . import styles
from . import __version__
from .services.versioning import VersionManager
from .services.morphology import MorphologyService, MorphologyHighlighter
from .services.glossary import (
    Glossary,
    create_glossary,
    delete_glossary,
    list_glossaries,
    rename_glossary,
    import_csv,
    export_csv,
)
from .settings import AppSettings, SettingsDialog
from .services.synonyms import fetch_synonyms as fetch_synonyms_datamuse
from .models import fetch_synonyms_llm, _MODELS
from .diff_utils import DiffHighlighter

def resource_path(name: str) -> str:
    """Return absolute path to resource, compatible with PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    path = Path(base_path) / name
    if not path.exists():
        path = Path(base_path).parent / name
    return str(path)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, settings: AppSettings | None = None):
        print(f"Application version: {__version__}")
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        self.settings = settings or AppSettings.load()
        styles.init(self.settings)
        self.current_glossary: Glossary | None = None
        self._current_word: str = ""
        self._current_context: str = ""

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)

        # Menu bar
        self.menu_bar = MainWindow.menuBar()
        self.settings_menu = self.menu_bar.addMenu("")
        self.settings_action = QtGui.QAction(parent=MainWindow)
        self.settings_action.setIcon(QIcon(resource_path("настройки.png")))
        self.settings_menu.addAction(self.settings_action)
        self.settings_action.triggered.connect(self._open_settings)

        # Navigation bar
        self.nav_layout = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.chapter_combo = QtWidgets.QComboBox(parent=self.centralwidget)
        self.next_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.model_combo = QtWidgets.QComboBox(parent=self.centralwidget)
        models = [
            name
            for name in sorted(_MODELS.keys())
            if getattr(self.settings, f"{name}_key", "")
        ]
        self.model_combo.addItems(models)
        if self.settings.model:
            idx = self.model_combo.findText(self.settings.model)
            if idx != -1:
                self.model_combo.setCurrentIndex(idx)
        self.save_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.save_btn.setIcon(QIcon(resource_path("сохранить.png")))
        self.nav_layout.addWidget(self.prev_btn)
        self.nav_layout.addWidget(self.chapter_combo)
        self.nav_layout.addWidget(self.next_btn)
        self.nav_layout.addWidget(self.model_combo)
        self.nav_layout.addWidget(self.save_btn)
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
        self.translation_edit.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.translation_edit.customContextMenuRequested.connect(
            self._show_synonym_menu
        )
        self.translation_counter = QtWidgets.QLabel("0", parent=self.translation_widget)
        self.translation_counter.setObjectName("counter")
        self.translation_counter.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.version_layout = QtWidgets.QHBoxLayout()
        self.undo_btn = QtWidgets.QPushButton(parent=self.translation_widget)
        self.redo_btn = QtWidgets.QPushButton(parent=self.translation_widget)
        self.version_layout.addWidget(self.undo_btn)
        self.version_layout.addWidget(self.redo_btn)
        self.mini_prompt_label = QtWidgets.QLabel(parent=self.translation_widget)
        self.mini_prompt_edit = QtWidgets.QTextEdit(parent=self.translation_widget)
        self.translation_layout.addWidget(self.translation_label)
        self.translation_layout.addWidget(self.translation_edit)
        self.translation_layout.addWidget(self.translation_counter)
        self.translation_layout.addLayout(self.version_layout)
        self.translation_layout.addWidget(self.mini_prompt_label)
        self.translation_layout.addWidget(self.mini_prompt_edit)
        self.right_splitter.addWidget(self.translation_widget)

        # Setup diff highlighting for translation edits
        self.diff_highlighter = DiffHighlighter(
            self.translation_edit.document(),
            color=self.settings.highlight_color,
        )
        self.morphology_service = MorphologyService()
        self.morphology_highlighter: MorphologyHighlighter | None = None
        if self.settings.machine_check:
            self._enable_machine_check()
        self.original_translation = ""

        base = Path(
            self.settings.translation_path
            or self.settings.original_path
            or "."
        )
        base.mkdir(parents=True, exist_ok=True)
        history_path = base / "versions.json"
        self.version_manager = VersionManager(history_path)
        if self.version_manager.versions:
            last = self.version_manager.versions[self.version_manager.index]["text"]
            self.translation_edit.setPlainText(last)
            self.original_translation = self.version_manager.versions[0]["text"]
            self.diff_highlighter.set_base(self.original_translation)
            self.diff_highlighter.update_diff()

        # Glossary panel
        self.glossary_widget = QtWidgets.QWidget(parent=self.centralwidget)
        self.glossary_layout = QtWidgets.QVBoxLayout(self.glossary_widget)
        self.glossary_top = QtWidgets.QHBoxLayout()
        self.glossary_combo = QtWidgets.QComboBox(parent=self.glossary_widget)
        self.add_glossary_btn = QtWidgets.QPushButton("+", parent=self.glossary_widget)
        self.rename_glossary_btn = QtWidgets.QPushButton("Rename", parent=self.glossary_widget)
        self.delete_glossary_btn = QtWidgets.QPushButton("-", parent=self.glossary_widget)
        self.import_glossary_btn = QtWidgets.QPushButton("Import", parent=self.glossary_widget)
        self.export_glossary_btn = QtWidgets.QPushButton("Export", parent=self.glossary_widget)
        self.glossary_top.addWidget(self.glossary_combo)
        self.glossary_top.addWidget(self.add_glossary_btn)
        self.glossary_top.addWidget(self.rename_glossary_btn)
        self.glossary_top.addWidget(self.delete_glossary_btn)
        self.glossary_top.addWidget(self.import_glossary_btn)
        self.glossary_top.addWidget(self.export_glossary_btn)
        self.auto_prompt_checkbox = QtWidgets.QCheckBox(parent=self.glossary_widget)
        self.glossary_table = QtWidgets.QTableWidget(parent=self.glossary_widget)
        self.glossary_table.setColumnCount(2)
        self.glossary_table.setHorizontalHeaderLabels(["Source", "Target"])
        self.glossary_table.horizontalHeader().setStretchLastSection(True)
        self.glossary_table.setObjectName("glossary")
        self.pair_btn_layout = QtWidgets.QHBoxLayout()
        self.add_pair_btn = QtWidgets.QPushButton("Add", parent=self.glossary_widget)
        self.remove_pair_btn = QtWidgets.QPushButton("Remove", parent=self.glossary_widget)
        self.pair_btn_layout.addWidget(self.add_pair_btn)
        self.pair_btn_layout.addWidget(self.remove_pair_btn)
        self.glossary_layout.addLayout(self.glossary_top)
        self.glossary_layout.addWidget(self.auto_prompt_checkbox)
        self.glossary_layout.addWidget(self.glossary_table)
        self.glossary_layout.addLayout(self.pair_btn_layout)
        self.right_splitter.addWidget(self.glossary_widget)

        self.glossary_combo.currentIndexChanged.connect(self._on_glossary_selected)
        self.add_glossary_btn.clicked.connect(self._create_glossary)
        self.rename_glossary_btn.clicked.connect(self._rename_glossary)
        self.delete_glossary_btn.clicked.connect(self._delete_glossary)
        self.import_glossary_btn.clicked.connect(self._import_glossary)
        self.export_glossary_btn.clicked.connect(self._export_glossary)
        self.add_pair_btn.clicked.connect(self._add_pair)
        self.remove_pair_btn.clicked.connect(self._remove_pair)
        self.glossary_table.itemChanged.connect(self._on_pair_edited)
        self.auto_prompt_checkbox.toggled.connect(self._on_auto_prompt_toggled)

        # Status/timer area
        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_layout.addStretch()
        self.version_label = QtWidgets.QLabel(__version__, parent=self.centralwidget)
        self.status_layout.addWidget(self.version_label)
        self.timer_label = QtWidgets.QLabel("00:00:00", parent=self.centralwidget)
        self.status_layout.addWidget(self.timer_label)
        self.main_layout.addLayout(self.status_layout)

        # Fonts
        base_font = QtGui.QFont(styles.INTER_FONT, 10)
        self.original_edit.setFont(base_font)
        self.translation_edit.setFont(base_font)
        self.mini_prompt_edit.setFont(base_font)
        self.glossary_table.setFont(base_font)
        self.timer_label.setFont(base_font)
        self.version_label.setFont(base_font)
        self._apply_style()

        # Timer and character counters
        self.elapsed = 0
        self.timer = QtCore.QTimer(MainWindow)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_timer)

        self.original_edit.textChanged.connect(self._update_original_counter)
        self.translation_edit.textChanged.connect(self._update_translation_counter)
        self.translation_edit.cursorPositionChanged.connect(
            self._on_cursor_position_changed
        )
        self.undo_btn.clicked.connect(self._restore_prev)
        self.redo_btn.clicked.connect(self._restore_next)

        self._load_glossaries()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def _apply_style(self) -> None:
        glow_rule = styles.neon_glow_rule(
            self.settings.neon_color, self.settings.neon_intensity
        )
        focus_rule = styles.focus_hover_rule(self.settings.accent_color)
        style_sheet = f"""
        QWidget {{
            background-color: {self.settings.app_background};
            color: {self.settings.text_color};
            font-family: {styles.INTER_FONT};
        }}
        QTextEdit,
        QLineEdit {{
            background-color: {styles.FIELD_BACKGROUND};
            color: {self.settings.text_color};
            border: 1px solid transparent;
        }}
        QTableWidget#glossary {{
            background-color: {styles.GLOSSARY_BACKGROUND};
            border: 1px solid transparent;
        }}
        QLabel#counter {{
            color: rgba(255, 255, 255, 128);
            font-size: 10px;
        }}
        {focus_rule}
        {glow_rule}
        """
        self.centralwidget.setStyleSheet(style_sheet)

    # --- internal helpers -------------------------------------------------
    def _update_timer(self) -> None:
        self.elapsed += 1
        hours, remainder = divmod(self.elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _start_timer(self) -> None:
        if not self.timer.isActive():
            self.timer.start()

    def reset_timer(self) -> None:
        """Reset the editing timer."""

        self.timer.stop()
        self.elapsed = 0
        self.timer_label.setText("00:00:00")

    def _update_original_counter(self) -> None:
        self._start_timer()
        self.original_counter.setText(str(len(self.original_edit.toPlainText())))

    def _update_translation_counter(self) -> None:
        self._start_timer()
        text = self.translation_edit.toPlainText()
        self.translation_counter.setText(str(len(text)))
        if not self.original_translation:
            self.original_translation = text
            self.diff_highlighter.set_base(text)
        self.version_manager.add_version(text)
        self.diff_highlighter.update_diff()

    def _on_cursor_position_changed(self) -> None:
        cursor = self.translation_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip()
        if not word:
            return
        text = self.translation_edit.toPlainText()
        start = max(cursor.selectionStart() - 30, 0)
        end = min(cursor.selectionEnd() + 30, len(text))
        self._current_word = word
        self._current_context = text[start:end]
        rect = self.translation_edit.cursorRect(cursor)
        self._show_synonym_menu(rect.bottomRight())

    def _enable_machine_check(self) -> None:
        if self.morphology_highlighter is None:
            self.morphology_highlighter = MorphologyHighlighter(
                self.translation_edit.document(), self.morphology_service
            )
            self.translation_edit.textChanged.connect(
                self.morphology_highlighter.update_errors
            )
            self.morphology_highlighter.update_errors()

    def _disable_machine_check(self) -> None:
        if self.morphology_highlighter is not None:
            try:
                self.translation_edit.textChanged.disconnect(
                    self.morphology_highlighter.update_errors
                )
            except TypeError:
                pass
            self.morphology_highlighter.errors = []
            self.morphology_highlighter.rehighlight()
            self.morphology_highlighter.setDocument(None)
            self.morphology_highlighter.deleteLater()
            self.morphology_highlighter = None

    def _show_synonym_menu(self, pos: QtCore.QPoint) -> None:
        cursor = self.translation_edit.cursorForPosition(pos)
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip()
        if not word:
            return
        if self.settings.synonym_provider == "model":
            synonyms = fetch_synonyms_llm(word, self.settings.model)
        else:
            synonyms = fetch_synonyms_datamuse(word)
        if not synonyms:
            return
        menu = QtWidgets.QMenu(self.translation_edit)
        for syn in synonyms:
            action = menu.addAction(syn)
            action.triggered.connect(
                lambda checked=False, s=syn, c=QtGui.QTextCursor(cursor):
                    self._replace_with_synonym(c, s)
            )
        menu.exec(self.translation_edit.mapToGlobal(pos))

    def _replace_with_synonym(
        self, cursor: QtGui.QTextCursor, synonym: str
    ) -> None:
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(synonym)
        cursor.endEditBlock()

    def _open_settings(self) -> None:
        previous = self.settings.machine_check
        dialog = SettingsDialog(self.settings, self.centralwidget)
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            if self.settings.machine_check and not previous:
                self._enable_machine_check()
            elif not self.settings.machine_check and previous:
                self._disable_machine_check()
            self.diff_highlighter.set_color(self.settings.highlight_color)
            self._apply_style()

    def _restore_prev(self) -> None:
        text = self.version_manager.undo()
        if text is not None:
            self.translation_edit.blockSignals(True)
            self.translation_edit.setPlainText(text)
            self.translation_edit.blockSignals(False)
            self.translation_counter.setText(str(len(text)))
            self.diff_highlighter.update_diff()

    def _restore_next(self) -> None:
        text = self.version_manager.redo()
        if text is not None:
            self.translation_edit.blockSignals(True)
            self.translation_edit.setPlainText(text)
            self.translation_edit.blockSignals(False)
            self.translation_counter.setText(str(len(text)))
            self.diff_highlighter.update_diff()

    # --- glossary management ---------------------------------------------
    def _load_glossaries(self) -> None:
        base = Path(
            self.settings.translation_path
            or self.settings.original_path
            or "."
        )
        folder = base / "glossaries"
        folder.mkdir(parents=True, exist_ok=True)
        self._glossary_folder = folder
        self.glossary_combo.blockSignals(True)
        self.glossary_combo.clear()
        for path in list_glossaries(folder):
            self.glossary_combo.addItem(path.stem, path)
        self.glossary_combo.blockSignals(False)
        if self.glossary_combo.count():
            self.glossary_combo.setCurrentIndex(0)
            current = self.glossary_combo.currentData()
            if current:
                self._load_glossary(Path(current))
        else:
            self.current_glossary = None
            self.glossary_table.setRowCount(0)
            self.auto_prompt_checkbox.blockSignals(True)
            self.auto_prompt_checkbox.setChecked(False)
            self.auto_prompt_checkbox.blockSignals(False)

    def _load_glossary(self, path: Path) -> None:
        self.current_glossary = Glossary.load(path)
        self.auto_prompt_checkbox.blockSignals(True)
        self.auto_prompt_checkbox.setChecked(self.current_glossary.auto_to_prompt)
        self.auto_prompt_checkbox.blockSignals(False)
        self._populate_table()

    def _populate_table(self) -> None:
        self.glossary_table.blockSignals(True)
        self.glossary_table.setRowCount(0)
        if self.current_glossary:
            for src, dst in self.current_glossary.entries.items():
                row = self.glossary_table.rowCount()
                self.glossary_table.insertRow(row)
                self.glossary_table.setItem(row, 0, QtWidgets.QTableWidgetItem(src))
                self.glossary_table.setItem(row, 1, QtWidgets.QTableWidgetItem(dst))
        self.glossary_table.blockSignals(False)

    def _on_glossary_selected(self, index: int) -> None:
        path = self.glossary_combo.itemData(index)
        if path:
            self._load_glossary(Path(path))

    def _create_glossary(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(
            self.centralwidget, "Новый глоссарий", "Название:"
        )
        if not ok or not name:
            return
        glossary = create_glossary(name, self._glossary_folder)
        self.glossary_combo.addItem(name, glossary.file)
        self.glossary_combo.setCurrentIndex(self.glossary_combo.count() - 1)

    def _rename_glossary(self) -> None:
        if not self.current_glossary:
            return
        new_name, ok = QtWidgets.QInputDialog.getText(
            self.centralwidget,
            "Переименовать глоссарий",
            "Название:",
            text=self.current_glossary.name,
        )
        if not ok or not new_name:
            return
        new_path = rename_glossary(self.current_glossary.file, new_name)
        self.current_glossary.name = new_name
        self.current_glossary.file = new_path
        self.current_glossary.save()
        idx = self.glossary_combo.currentIndex()
        self.glossary_combo.setItemText(idx, new_name)
        self.glossary_combo.setItemData(idx, new_path)

    def _delete_glossary(self) -> None:
        idx = self.glossary_combo.currentIndex()
        if idx < 0:
            return
        path = self.glossary_combo.itemData(idx)
        delete_glossary(path)
        self.glossary_combo.removeItem(idx)
        if self.glossary_combo.count():
            self.glossary_combo.setCurrentIndex(0)
        else:
            self.current_glossary = None
            self.glossary_table.setRowCount(0)
            self.auto_prompt_checkbox.blockSignals(True)
            self.auto_prompt_checkbox.setChecked(False)
            self.auto_prompt_checkbox.blockSignals(False)

    def _import_glossary(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.centralwidget, "Импорт глоссария", "", "CSV/TSV Files (*.csv *.tsv)"
        )
        if not path:
            return
        glossary = import_csv(path)
        glossary.save(self._glossary_folder / f"{glossary.name}.json")
        self.glossary_combo.addItem(glossary.name, glossary.file)
        self.glossary_combo.setCurrentIndex(self.glossary_combo.count() - 1)

    def _export_glossary(self) -> None:
        if not self.current_glossary:
            return
        default = f"{self.current_glossary.name}.csv"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.centralwidget,
            "Экспорт глоссария",
            default,
            "CSV (*.csv);;TSV (*.tsv)",
        )
        if not path:
            return
        export_csv(self.current_glossary, path)

    def _add_pair(self) -> None:
        row = self.glossary_table.rowCount()
        self.glossary_table.insertRow(row)
        self.glossary_table.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        self.glossary_table.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

    def _remove_pair(self) -> None:
        row = self.glossary_table.currentRow()
        if row < 0:
            return
        src_item = self.glossary_table.item(row, 0)
        if src_item and self.current_glossary:
            self.current_glossary.remove(src_item.text())
            self.current_glossary.save()
        self.glossary_table.removeRow(row)

    def _on_pair_edited(self, row: int, column: int) -> None:
        if not self.current_glossary:
            return
        src_item = self.glossary_table.item(row, 0)
        dst_item = self.glossary_table.item(row, 1)
        if src_item and dst_item:
            src = src_item.text().strip()
            dst = dst_item.text().strip()
            if src:
                self.current_glossary.add(src, dst)
                self.current_glossary.save()

    def _on_auto_prompt_toggled(self, checked: bool) -> None:
        if self.current_glossary:
            self.current_glossary.auto_to_prompt = checked
            self.current_glossary.save()

    def glossary_entries(self) -> dict[str, str]:
        if self.current_glossary:
            return dict(self.current_glossary.entries)
        return {}

    # --- translations -----------------------------------------------------
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Main Window"))
        self.prev_btn.setText(_translate("MainWindow", "⦉"))
        self.next_btn.setText(_translate("MainWindow", "⦊"))
        self.save_btn.setText(_translate("MainWindow", "Сохранить"))
        self.original_label.setText(_translate("MainWindow", "Оригинал"))
        self.translation_label.setText(_translate("MainWindow", "Перевод"))
        self.undo_btn.setText(_translate("MainWindow", "Назад"))
        self.redo_btn.setText(_translate("MainWindow", "Вперёд"))
        self.mini_prompt_label.setText(_translate("MainWindow", "Мини-промпт"))
        self.settings_menu.setTitle(_translate("MainWindow", "Настройки"))
        self.settings_action.setText(_translate("MainWindow", "Параметры…"))
        self.add_glossary_btn.setText(_translate("MainWindow", "+"))
        self.rename_glossary_btn.setText(_translate("MainWindow", "Переименовать"))
        self.delete_glossary_btn.setText(_translate("MainWindow", "-"))
        self.import_glossary_btn.setText(_translate("MainWindow", "Импорт"))
        self.export_glossary_btn.setText(_translate("MainWindow", "Экспорт"))
        self.auto_prompt_checkbox.setText(_translate("MainWindow", "Авто в промпт"))
        self.add_pair_btn.setText(_translate("MainWindow", "Добавить"))
        self.remove_pair_btn.setText(_translate("MainWindow", "Удалить"))

