"""Main application window UI setup."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel

from . import styles
from . import get_version
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
from .glossary import GlossaryTableModel
from .settings import AppSettings, SettingsDialog
from .services.synonyms import fetch_synonyms as fetch_synonyms_datamuse
from .models import fetch_synonyms_llm, _MODELS
from .diff_utils import DiffHighlighter
from .project_manager import Project, ProjectManager
from .services.project import ProjectManager as ProjectDataManager

def resource_path(name: str) -> str:
    """Return absolute path to resource, compatible with PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    path = Path(base_path) / name
    if not path.exists():
        path = Path(base_path).parent / name
    return str(path)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, settings: AppSettings | None = None):
        version = get_version()
        print(f"Application version: {version}")
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        self.settings = settings or AppSettings.load()
        styles.init(self.settings)
        self.current_glossary: Glossary | None = None
        self._current_word: str = ""
        self._current_context: str = ""
        self._updating_translation = False

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)

        # Project tree dock
        self.project_manager = ProjectManager()
        self.project_service = ProjectDataManager()
        self.project_dock = QtWidgets.QDockWidget(parent=MainWindow)
        self.project_widget = QtWidgets.QWidget()
        self.project_layout = QtWidgets.QVBoxLayout(self.project_widget)
        self.project_tree = QtWidgets.QTreeView(parent=self.project_widget)
        self.project_tree.setStyleSheet(
            """
            QTreeView::item:selected {
                background-color: #39ff14;
                border: 1px solid #39ff14;
                color: black;
            }
            QTreeView::item:selected:!active {
                background-color: #39ff14;
                border: 1px solid #39ff14;
                color: black;
            }
            """
        )
        self.project_tree.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.project_model = QStandardItemModel()
        self.project_model.setHorizontalHeaderLabels(["Projects"])
        self.active_root = QStandardItem()
        self.archived_root = QStandardItem()
        self.project_model.appendRow(self.active_root)
        self.project_model.appendRow(self.archived_root)
        self.project_tree.setModel(self.project_model)
        self.project_tree.setIconSize(QtCore.QSize(32, 32))
        self.project_tree.expandAll()
        self.project_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal, parent=self.project_widget
        )
        self.project_splitter.addWidget(self.project_tree)
        self.project_summary = QtWidgets.QTextEdit(parent=self.project_widget)
        self.project_summary.setReadOnly(True)
        self.project_splitter.addWidget(self.project_summary)
        self.project_splitter.setSizes([200, 0])
        self.project_layout.addWidget(self.project_splitter)
        self.project_btn_layout = QtWidgets.QHBoxLayout()
        self.create_project_btn = QtWidgets.QPushButton(parent=self.project_widget)
        self.rename_project_btn = QtWidgets.QPushButton(parent=self.project_widget)
        self.archive_project_btn = QtWidgets.QPushButton(parent=self.project_widget)
        self.delete_project_btn = QtWidgets.QPushButton(parent=self.project_widget)
        self.select_icon_btn = QtWidgets.QPushButton(parent=self.project_widget)
        self.project_btn_layout.addWidget(self.create_project_btn)
        self.project_btn_layout.addWidget(self.rename_project_btn)
        self.project_btn_layout.addWidget(self.archive_project_btn)
        self.project_btn_layout.addWidget(self.delete_project_btn)
        self.project_btn_layout.addWidget(self.select_icon_btn)
        self.project_layout.addLayout(self.project_btn_layout)
        self.project_dock.setWidget(self.project_widget)
        MainWindow.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.project_dock
        )

        self.create_project_btn.clicked.connect(self._create_project)
        self.rename_project_btn.clicked.connect(self._rename_project)
        self.archive_project_btn.clicked.connect(self._archive_project)
        self.delete_project_btn.clicked.connect(self._delete_project)
        self.select_icon_btn.clicked.connect(self._choose_project_icon)
        self._refresh_project_tree()
        self.project_tree.selectionModel().currentChanged.connect(
            self._display_project_summary
        )

        # Project list and icon selection
        self.project_list = QtWidgets.QListWidget(parent=self.centralwidget)
        self.project_list.setIconSize(QtCore.QSize(32, 32))
        self.main_layout.addWidget(self.project_list)

        self.project_icon_btn = QtWidgets.QPushButton("Выбрать иконку", parent=self.centralwidget)
        self.main_layout.addWidget(self.project_icon_btn)

        # Menu bar
        self.menu_bar = MainWindow.menuBar()
        self.menu_bar.setFont(QtGui.QFont(styles.HEADER_FONT, 10))
        self.settings_menu = self.menu_bar.addMenu("")
        self.settings_menu.setFont(QtGui.QFont(styles.HEADER_FONT, 10))
        self.settings_action = QtGui.QAction(parent=MainWindow)
        self.settings_action.setIcon(QIcon(resource_path("настройки.png")))
        self.settings_action.setFont(QtGui.QFont(styles.HEADER_FONT, 10))
        self.settings_menu.addAction(self.settings_action)
        self.settings_action.triggered.connect(self._open_settings)

        # Navigation bar
        self.nav_layout = QtWidgets.QHBoxLayout()
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(4)
        self.prev_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.prev_btn.setFixedSize(24, 24)
        self.chapter_combo = QtWidgets.QComboBox(parent=self.centralwidget)
        self.next_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.next_btn.setFixedSize(24, 24)
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
        self.save_btn.setMinimumHeight(24)
        self.nav_layout.addWidget(self.prev_btn)
        self.nav_layout.addWidget(self.chapter_combo)
        self.nav_layout.addWidget(self.next_btn)
        self.nav_layout.addWidget(self.model_combo)
        self.nav_layout.addWidget(self.save_btn)
        self.toggle_glossary_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.toggle_glossary_btn.setIcon(QIcon(resource_path("свернуть.png")))
        self.toggle_glossary_btn.setCheckable(True)
        self.nav_layout.addWidget(self.toggle_glossary_btn)
        self.main_layout.addLayout(self.nav_layout)

        # Splitter separating original and translation
        self.h_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal, parent=self.centralwidget
        )

        # Original text section
        self.original_widget = QtWidgets.QWidget()
        self.original_layout = QtWidgets.QVBoxLayout(self.original_widget)
        self.original_layout.setContentsMargins(0, 0, 0, 0)
        self.original_layout.setSpacing(4)
        self.original_edit = QtWidgets.QTextEdit(parent=self.original_widget)
        self.original_edit.setPlaceholderText("Оригинал")
        self.original_counter = QtWidgets.QLabel("0", parent=self.original_widget)
        self.original_counter.setObjectName("counter")
        self.original_counter.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.original_layout.addWidget(self.original_edit)
        self.original_layout.addWidget(self.original_counter)
        self.original_layout.setStretch(0, 1)
        self.h_splitter.addWidget(self.original_widget)

        # Translation block with mini-prompt
        self.translation_widget = QtWidgets.QWidget()
        self.translation_layout = QtWidgets.QVBoxLayout(self.translation_widget)
        self.translation_layout.setContentsMargins(0, 0, 0, 0)
        self.translation_layout.setSpacing(4)
        self.translation_edit = QtWidgets.QTextEdit(parent=self.translation_widget)
        self.translation_edit.setPlaceholderText("Перевод")
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
        self.version_layout.setContentsMargins(0, 0, 0, 0)
        self.version_layout.setSpacing(4)
        self.undo_btn = QtWidgets.QPushButton(parent=self.translation_widget)
        self.undo_btn.setMinimumHeight(24)
        self.redo_btn = QtWidgets.QPushButton(parent=self.translation_widget)
        self.redo_btn.setMinimumHeight(24)
        self.version_layout.addWidget(self.undo_btn)
        self.version_layout.addWidget(self.redo_btn)
        self.translation_layout.addWidget(self.translation_edit)
        self.translation_layout.addWidget(self.translation_counter)
        self.translation_layout.addLayout(self.version_layout)
        self.h_splitter.addWidget(self.translation_widget)
        self.h_splitter.setStretchFactor(0, 1)
        self.h_splitter.setStretchFactor(1, 1)

        # Mini-prompt section placed below the text editors
        self.mini_prompt_widget = QtWidgets.QWidget(parent=self.centralwidget)
        self.mini_prompt_layout = QtWidgets.QVBoxLayout(self.mini_prompt_widget)
        self.mini_prompt_layout.setContentsMargins(0, 0, 0, 0)
        self.mini_prompt_layout.setSpacing(4)
        self.mini_prompt_edit = QtWidgets.QTextEdit(parent=self.mini_prompt_widget)
        self.mini_prompt_edit.setPlaceholderText("Мини-промпт")
        self.mini_prompt_layout.addWidget(self.mini_prompt_edit)

        # Vertical splitter combining editor area and mini-prompt
        self.v_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical, parent=self.centralwidget
        )
        self.v_splitter.addWidget(self.h_splitter)
        self.v_splitter.addWidget(self.mini_prompt_widget)
        self.v_splitter.setStretchFactor(0, 1)
        self.v_splitter.setStretchFactor(1, 0)

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
        self.glossary_layout.setContentsMargins(0, 0, 0, 0)
        self.glossary_layout.setSpacing(4)
        self.glossary_top = QtWidgets.QHBoxLayout()
        self.glossary_top.setContentsMargins(0, 0, 0, 0)
        self.glossary_top.setSpacing(4)
        self.glossary_combo = QtWidgets.QComboBox(parent=self.glossary_widget)
        self.add_glossary_btn = QtWidgets.QPushButton("Создать", parent=self.glossary_widget)
        self.rename_glossary_btn = QtWidgets.QPushButton("Rename", parent=self.glossary_widget)
        self.delete_glossary_btn = QtWidgets.QPushButton("-", parent=self.glossary_widget)
        self.delete_glossary_btn.setFixedSize(24, 24)
        self.import_glossary_btn = QtWidgets.QPushButton("Import", parent=self.glossary_widget)
        self.export_glossary_btn = QtWidgets.QPushButton("Export", parent=self.glossary_widget)
        self.glossary_top.addWidget(self.glossary_combo)
        self.glossary_top.addWidget(self.add_glossary_btn)
        self.glossary_top.addWidget(self.rename_glossary_btn)
        self.glossary_top.addWidget(self.delete_glossary_btn)
        self.glossary_top.addWidget(self.import_glossary_btn)
        self.glossary_top.addWidget(self.export_glossary_btn)
        self.auto_prompt_checkbox = QtWidgets.QCheckBox(parent=self.glossary_widget)
        self.glossary_table = QtWidgets.QTableView(parent=self.glossary_widget)
        self.glossary_table.setObjectName("glossary")
        self.glossary_model = GlossaryTableModel()
        self.glossary_table.setModel(self.glossary_model)
        self.glossary_table.horizontalHeader().setStretchLastSection(True)
        self.pair_btn_layout = QtWidgets.QHBoxLayout()
        self.pair_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.pair_btn_layout.setSpacing(4)
        self.add_pair_btn = QtWidgets.QPushButton("Add", parent=self.glossary_widget)
        self.remove_pair_btn = QtWidgets.QPushButton("Remove", parent=self.glossary_widget)
        self.pair_btn_layout.addWidget(self.add_pair_btn)
        self.pair_btn_layout.addWidget(self.remove_pair_btn)
        self.glossary_layout.addLayout(self.glossary_top)
        self.glossary_layout.addWidget(self.auto_prompt_checkbox)
        self.glossary_layout.addWidget(self.glossary_table)
        self.glossary_layout.addLayout(self.pair_btn_layout)

        self.main_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal, parent=self.centralwidget
        )
        self.main_splitter.addWidget(self.v_splitter)
        self.main_splitter.addWidget(self.glossary_widget)
        self.main_layout.addWidget(self.main_splitter)
        self.main_layout.setStretch(1, 1)  # splitter fills space
        self.main_layout.setStretch(2, 0)  # mini-prompt keeps minimal height
        self._splitter_sizes = self.main_splitter.sizes()

        self.glossary_combo.currentIndexChanged.connect(self._on_glossary_selected)
        self.add_glossary_btn.clicked.connect(self._create_glossary)
        self.rename_glossary_btn.clicked.connect(self._rename_glossary)
        self.delete_glossary_btn.clicked.connect(self._delete_glossary)
        self.import_glossary_btn.clicked.connect(self._import_glossary)
        self.export_glossary_btn.clicked.connect(self._export_glossary)
        self.add_pair_btn.clicked.connect(self._add_pair)
        self.remove_pair_btn.clicked.connect(self._remove_pair)
        self.auto_prompt_checkbox.toggled.connect(self._on_auto_prompt_toggled)
        self.toggle_glossary_btn.toggled.connect(self._toggle_glossary)

        # Status/timer area
        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setSpacing(4)
        self.status_layout.addStretch()
        self.version_label = QtWidgets.QLabel(version, parent=self.centralwidget)
        self.version_label.setFont(QtGui.QFont(styles.HEADER_FONT, 10))
        self.status_layout.addWidget(self.version_label)
        self.timer_label = QtWidgets.QLabel("00:00:00", parent=self.centralwidget)
        self.timer_label.setFont(QtGui.QFont(styles.HEADER_FONT, 10))
        self.status_layout.addWidget(self.timer_label)
        self.main_layout.addLayout(self.status_layout)

        # Fonts
        base_font = QtGui.QFont(styles.INTER_FONT, self.settings.font_size)
        self.original_edit.setFont(base_font)
        self.translation_edit.setFont(base_font)
        self.mini_prompt_edit.setFont(base_font)
        self.glossary_table.setFont(base_font)
        self._apply_style()

        # Timer and character counters
        self.elapsed = 0
        self.timer = QtCore.QTimer(MainWindow)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_timer)
        self._start_timer()

        self.original_edit.textChanged.connect(self._update_original_counter)
        self.translation_timer = QtCore.QTimer()
        self.translation_timer.setInterval(500)
        self.translation_timer.setSingleShot(True)
        self.translation_timer.timeout.connect(self._commit_translation_change)
        self.translation_edit.textChanged.connect(self._on_translation_changed)
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
            self.settings.neon_color,
            self.settings.neon_intensity,
            self.settings.neon_width,
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
            border-radius: 6px;
        }}
        QTableView#glossary {{
            background-color: {styles.GLOSSARY_BACKGROUND};
            border: 1px solid transparent;
            border-radius: 6px;
        }}
        QLabel#counter {{
            color: rgba(255, 255, 255, 128);
            font-size: 10px;
        }}
        QPushButton {{
            padding: 2px 6px;
            min-height: 20px;
        }}
        {focus_rule}
        {glow_rule}
        """
        self.centralwidget.setStyleSheet(style_sheet)

    def _apply_font_size(self) -> None:
        base_font = QtGui.QFont(styles.INTER_FONT, self.settings.font_size)
        self.original_edit.setFont(base_font)
        self.translation_edit.setFont(base_font)
        self.mini_prompt_edit.setFont(base_font)
        self.glossary_table.setFont(base_font)

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
        self.original_counter.setText(str(len(self.original_edit.toPlainText())))

    def _on_translation_changed(self) -> None:
        if self._updating_translation:
            return
        self._updating_translation = True
        try:
            self.translation_timer.start()
            text = self.translation_edit.toPlainText()
            self.translation_counter.setText(str(len(text)))
        finally:
            self._updating_translation = False

    def _commit_translation_change(self) -> None:
        self.translation_timer.stop()
        text = self.translation_edit.toPlainText()
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
            self._apply_font_size()

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

    def _toggle_glossary(self, checked: bool) -> None:
        if checked:
            self._splitter_sizes = self.main_splitter.sizes()
            self.main_splitter.setSizes([1, 0])
        else:
            if hasattr(self, "_splitter_sizes"):
                self.main_splitter.setSizes(self._splitter_sizes)
            else:
                self.main_splitter.setSizes([1, 1])

    # --- glossary management ---------------------------------------------
    def _load_glossaries(self) -> None:
        folder = Path(__file__).resolve().parent.parent / "data"
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
            glossary = create_glossary("glossary", folder)
            self.glossary_combo.addItem(glossary.name, glossary.file)
            self.glossary_combo.setCurrentIndex(0)
            self._load_glossary(glossary.file)

    def _load_glossary(self, path: Path) -> None:
        self.current_glossary = Glossary.load(path)
        self.auto_prompt_checkbox.blockSignals(True)
        self.auto_prompt_checkbox.setChecked(self.current_glossary.auto_to_prompt)
        self.auto_prompt_checkbox.blockSignals(False)
        self._populate_table()

    def _populate_table(self) -> None:
        self.glossary_model.set_glossary(self.current_glossary)

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
            self.glossary_model.set_glossary(None)
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
        self.glossary_model.add_pair()

    def _remove_pair(self) -> None:
        row = self.glossary_table.currentIndex().row()
        if row < 0:
            return
        self.glossary_model.remove_pair(row)

    def _on_pair_edited(self, item: QtWidgets.QTableWidgetItem) -> None:
        if not self.current_glossary:
            return
        row = item.row()
        column = item.column()
        src_item = self.glossary_table.item(row, 0)
        dst_item = self.glossary_table.item(row, 1)
        if src_item and dst_item:
            src = src_item.text().strip()
            dst = dst_item.text().strip()
            if src:
                self.current_glossary.add(src, dst)
                self.current_glossary.save()

    # --- project management ---------------------------------------------
    def _selected_project(self) -> Project | None:
        index = self.project_tree.currentIndex()
        if not index.isValid():
            return None
        item = self.project_model.itemFromIndex(index)
        if item in (self.active_root, self.archived_root):
            return None
        project_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        return self.project_manager.get(project_id)

    def _refresh_project_tree(self) -> None:
        self.active_root.removeRows(0, self.active_root.rowCount())
        self.archived_root.removeRows(0, self.archived_root.rowCount())
        for proj in self.project_manager.projects:
            item = QStandardItem(proj.name)
            item.setData(proj.id, QtCore.Qt.ItemDataRole.UserRole)
            pixmap = QtGui.QPixmap(proj.icon_path)
            if pixmap.isNull():
                pixmap = QtGui.QPixmap("assets/empty_project.png")
            pixmap = pixmap.scaled(
                32,
                32,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            item.setIcon(QtGui.QIcon(pixmap))
            if proj.archived:
                self.archived_root.appendRow(item)
            else:
                self.active_root.appendRow(item)
        self.project_tree.expandAll()

    def _display_project_summary(
        self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex
    ) -> None:
        proj = self._selected_project()
        if not proj:
            self.project_summary.clear()
            return
        meta = self.project_service.load(proj.id, title=proj.name)
        lines = [f"{ch.name}: {ch.plot}" for ch in meta.chapters]
        self.project_summary.setPlainText("\n".join(lines))

    def _create_project(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(
            self.project_widget, "Новый проект", "Название проекта:"
        )
        if not ok or not name:
            return
        self.project_manager.create(name)
        self._refresh_project_tree()

    def _rename_project(self) -> None:
        proj = self._selected_project()
        if not proj:
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self.project_widget, "Переименовать", "Новое название:", text=proj.name
        )
        if not ok or not name:
            return
        self.project_manager.rename(proj.id, name)
        self._refresh_project_tree()

    def _archive_project(self) -> None:
        proj = self._selected_project()
        if not proj:
            return
        self.project_manager.archive(proj.id, not proj.archived)
        self._refresh_project_tree()

    def _delete_project(self) -> None:
        proj = self._selected_project()
        if not proj:
            return
        res = QtWidgets.QMessageBox.question(
            self.project_widget,
            "Удалить проект",
            f"Удалить '{proj.name}'?",
        )
        if res != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.project_manager.delete(proj.id)
        self._refresh_project_tree()

    def _choose_project_icon(self) -> None:
        proj = self._selected_project()
        if not proj:
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.project_widget,
            "Выбор иконки",
            "",
            "Images (*.png *.jpg *.bmp *.gif)",
        )
        if not path:
            return
        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            return
        pixmap = pixmap.scaled(
            32,
            32,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        proj.icon_path = path
        self.project_manager.save()
        self._refresh_project_tree()


    def _on_auto_prompt_toggled(self, checked: bool) -> None:
        if self.current_glossary:
            self.current_glossary.auto_to_prompt = checked
            self.current_glossary.save()

    def glossary_entries(self) -> dict[str, str]:
        return self.glossary_model.glossary_entries()

    # --- translations -----------------------------------------------------
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Main Window"))
        self.prev_btn.setText(_translate("MainWindow", "⦉"))
        self.next_btn.setText(_translate("MainWindow", "⦊"))
        self.save_btn.setText(_translate("MainWindow", "Сохранить"))
        self.undo_btn.setText(_translate("MainWindow", "Назад"))
        self.redo_btn.setText(_translate("MainWindow", "Вперёд"))
        self.settings_menu.setTitle(_translate("MainWindow", "Настройки"))
        self.settings_action.setText(_translate("MainWindow", "Параметры…"))
        self.add_glossary_btn.setText(_translate("MainWindow", "Создать"))
        self.rename_glossary_btn.setText(_translate("MainWindow", "Переименовать"))
        self.delete_glossary_btn.setText(_translate("MainWindow", "-"))
        self.import_glossary_btn.setText(_translate("MainWindow", "Импорт"))
        self.export_glossary_btn.setText(_translate("MainWindow", "Экспорт"))
        self.auto_prompt_checkbox.setText(_translate("MainWindow", "Авто в промпт"))
        self.add_pair_btn.setText(_translate("MainWindow", "Добавить"))
        self.remove_pair_btn.setText(_translate("MainWindow", "Удалить"))
        self.project_dock.setWindowTitle(_translate("MainWindow", "Проекты"))
        self.create_project_btn.setText(_translate("MainWindow", "Создать"))
        self.rename_project_btn.setText(_translate("MainWindow", "Переименовать"))
        self.archive_project_btn.setText(_translate("MainWindow", "Архивировать"))
        self.delete_project_btn.setText(_translate("MainWindow", "Удалить"))
        self.project_summary.setPlaceholderText(
            _translate("MainWindow", "Информация о проекте")
        )
        self.select_icon_btn.setText(_translate("MainWindow", "Иконка"))
        self.active_root.setText(_translate("MainWindow", "Активные"))
        self.archived_root.setText(_translate("MainWindow", "Архив"))

