"""Application settings management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets


@dataclass
class AppSettings:
    """Persistent application settings.

    Parameters
    ----------
    original_path:
        Folder containing original chapters.
    translation_path:
        Folder where translated chapters and metadata are stored.
    api_key:
        Key for accessing external translation services.
    model:
        Identifier of the LLM or translation model in use.
    machine_check:
        Whether machine translation verification is enabled.
    auto_next:
        Move to the next chapter automatically after saving.
    format:
        Output format for saved translations ("docx" or "txt").
    gdoc_token:
        OAuth token for accessing Google Docs.
    gdoc_folder_id:
        Identifier of the Google Drive folder containing chapters.
    highlight_color:
        Background colour for diff highlighting in ARGB hex format.
    """

    original_path: str = ""
    translation_path: str = ""
    api_key: str = ""
    model: str = ""
    machine_check: bool = False
    auto_next: bool = False
    format: str = "docx"
    gdoc_token: str = ""
    gdoc_folder_id: str = ""
    highlight_color: str = "#80ffff00"  # semi-transparent yellow
    _file: Path = field(default=Path("settings.ini"), repr=False)

    # --- persistence -------------------------------------------------
    def save(self, file: Path | str | None = None) -> None:
        """Persist settings using :class:`QtCore.QSettings`."""

        file_path = Path(file) if file else self._file
        qs = QtCore.QSettings(str(file_path), QtCore.QSettings.Format.IniFormat)
        qs.setValue("original_path", self.original_path)
        qs.setValue("translation_path", self.translation_path)
        qs.setValue("api_key", self.api_key)
        qs.setValue("model", self.model)
        qs.setValue("machine_check", self.machine_check)
        qs.setValue("auto_next", self.auto_next)
        qs.setValue("format", self.format)
        qs.setValue("gdoc_token", self.gdoc_token)
        qs.setValue("gdoc_folder_id", self.gdoc_folder_id)
        qs.setValue("highlight_color", self.highlight_color)
        qs.sync()
        self._file = file_path

    @classmethod
    def load(cls, file: Path | str | None = None) -> "AppSettings":
        """Load settings from a :class:`QtCore.QSettings` store."""

        file_path = Path(file) if file else Path("settings.ini")
        qs = QtCore.QSettings(str(file_path), QtCore.QSettings.Format.IniFormat)
        obj = cls(
            original_path=qs.value("original_path", "", str),
            translation_path=qs.value("translation_path", "", str),
            api_key=qs.value("api_key", "", str),
            model=qs.value("model", "", str),
            machine_check=qs.value("machine_check", False, bool),
            auto_next=qs.value("auto_next", False, bool),
            format=qs.value("format", "docx", str),
            gdoc_token=qs.value("gdoc_token", "", str),
            gdoc_folder_id=qs.value("gdoc_folder_id", "", str),
            highlight_color=qs.value("highlight_color", "#80ffff00", str),
        )
        obj._file = file_path
        return obj


class SettingsDialog(QtWidgets.QDialog):
    """Dialog allowing the user to edit application settings."""

    def __init__(self, settings: AppSettings, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.settings = settings
        self._color = QtGui.QColor(settings.highlight_color)

        layout = QtWidgets.QFormLayout(self)

        # Original folder selector
        orig_layout = QtWidgets.QHBoxLayout()
        self.original_edit = QtWidgets.QLineEdit(settings.original_path)
        orig_btn = QtWidgets.QPushButton("...")
        orig_btn.clicked.connect(lambda: self._choose_folder(self.original_edit))
        orig_layout.addWidget(self.original_edit)
        orig_layout.addWidget(orig_btn)

        # Translation folder selector
        trans_layout = QtWidgets.QHBoxLayout()
        self.translation_edit = QtWidgets.QLineEdit(settings.translation_path)
        trans_btn = QtWidgets.QPushButton("...")
        trans_btn.clicked.connect(lambda: self._choose_folder(self.translation_edit))
        trans_layout.addWidget(self.translation_edit)
        trans_layout.addWidget(trans_btn)

        self.api_key_edit = QtWidgets.QLineEdit(settings.api_key)
        self.gdoc_token_edit = QtWidgets.QLineEdit(settings.gdoc_token)
        self.gdoc_folder_edit = QtWidgets.QLineEdit(settings.gdoc_folder_id)

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItems(["gemini", "deepl", "grok", "qwen"])
        if settings.model:
            index = self.model_combo.findText(settings.model)
            if index != -1:
                self.model_combo.setCurrentIndex(index)

        self.machine_check_box = QtWidgets.QCheckBox()
        self.machine_check_box.setChecked(settings.machine_check)

        self.auto_next_box = QtWidgets.QCheckBox()
        self.auto_next_box.setChecked(settings.auto_next)

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["docx", "txt"])
        index = self.format_combo.findText(settings.format)
        if index != -1:
            self.format_combo.setCurrentIndex(index)

        self.color_btn = QtWidgets.QPushButton()
        self._update_color_btn()
        self.color_btn.clicked.connect(self._choose_color)

        layout.addRow("Папка оригинала", orig_layout)
        layout.addRow("Папка перевода", trans_layout)
        layout.addRow("API ключ", self.api_key_edit)
        layout.addRow("Токен Google Docs", self.gdoc_token_edit)
        layout.addRow("ID папки Google Docs", self.gdoc_folder_edit)
        layout.addRow("Модель", self.model_combo)
        layout.addRow("Формат", self.format_combo)
        layout.addRow("Машинная проверка", self.machine_check_box)
        layout.addRow("Следующая глава", self.auto_next_box)
        layout.addRow("Цвет подсветки", self.color_btn)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    # --- internal helpers --------------------------------------------
    def _choose_folder(self, line_edit: QtWidgets.QLineEdit) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Выбор папки", line_edit.text()
        )
        if path:
            line_edit.setText(path)

    def _choose_color(self) -> None:
        color = QtWidgets.QColorDialog.getColor(self._color, self)
        if color.isValid():
            self._color = color
            self._update_color_btn()

    def _update_color_btn(self) -> None:
        self.color_btn.setStyleSheet(
            f"background-color: {self._color.name(QtGui.QColor.NameFormat.HexArgb)}"
        )

    # --- Qt overrides ------------------------------------------------
    def accept(self) -> None:  # type: ignore[override]
        self.settings.original_path = self.original_edit.text()
        self.settings.translation_path = self.translation_edit.text()
        self.settings.api_key = self.api_key_edit.text()
        self.settings.gdoc_token = self.gdoc_token_edit.text()
        self.settings.gdoc_folder_id = self.gdoc_folder_edit.text()
        self.settings.model = self.model_combo.currentText()
        self.settings.machine_check = self.machine_check_box.isChecked()
        self.settings.auto_next = self.auto_next_box.isChecked()
        self.settings.format = self.format_combo.currentText()
        self.settings.highlight_color = self._color.name(
            QtGui.QColor.NameFormat.HexArgb
        )
        self.settings.save()
        super().accept()

