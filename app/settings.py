
"""Application settings management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json

from PyQt6 import QtWidgets


@dataclass
class AppSettings:
    """Persistent application settings.

    Parameters
    ----------
    project_path:
        Path to the project or files being processed.
    api_key:
        Key for accessing external translation services.
    model:
        Identifier of the LLM or translation model in use.
    machine_check:
        Whether machine translation verification is enabled.
    """

    project_path: str = ""
    api_key: str = ""
    model: str = ""
    machine_check: bool = False
    _file: Path = field(default=Path("settings.json"), repr=False)

    # --- persistence -------------------------------------------------
    def save(self, file: Path | str | None = None) -> None:
        """Save settings to *file* in JSON format."""

        file_path = Path(file) if file else self._file
        data = {
            "project_path": self.project_path,
            "api_key": self.api_key,
            "model": self.model,
            "machine_check": self.machine_check,
        }
        file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._file = file_path

    @classmethod
    def load(cls, file: Path | str | None = None) -> "AppSettings":
        """Load settings from *file* if it exists."""

        file_path = Path(file) if file else Path("settings.json")
        if file_path.exists():
            data = json.loads(file_path.read_text(encoding="utf-8"))
            obj = cls(**data)
        else:
            obj = cls()
        obj._file = file_path
        return obj


class SettingsDialog(QtWidgets.QDialog):
    """Simple dialog allowing the user to edit settings."""

    def __init__(self, settings: AppSettings, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.settings = settings

        layout = QtWidgets.QFormLayout(self)

        self.path_edit = QtWidgets.QLineEdit(settings.project_path)
        self.api_key_edit = QtWidgets.QLineEdit(settings.api_key)

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItems(["gpt-4", "gpt-3.5", "custom"])
        if settings.model:
            index = self.model_combo.findText(settings.model)
            if index != -1:
                self.model_combo.setCurrentIndex(index)

        self.machine_check_box = QtWidgets.QCheckBox()
        self.machine_check_box.setChecked(settings.machine_check)

        layout.addRow("Путь", self.path_edit)
        layout.addRow("API ключ", self.api_key_edit)
        layout.addRow("Модель", self.model_combo)
        layout.addRow("Машинная проверка", self.machine_check_box)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    # --- Qt overrides ------------------------------------------------
    def accept(self) -> None:  # type: ignore[override]
        self.settings.project_path = self.path_edit.text()
        self.settings.api_key = self.api_key_edit.text()
        self.settings.model = self.model_combo.currentText()
        self.settings.machine_check = self.machine_check_box.isChecked()
        self.settings.save()
        super().accept()
