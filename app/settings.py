"""Application settings management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from . import styles
from .services.files import load_stats, save_stats
from .services.glossary import Glossary, list_glossaries


@dataclass
class AppSettings:
    """Persistent application settings.

    Parameters
    ----------
    original_path:
        Folder containing original chapters.
    translation_path:
        Folder where translated chapters and metadata are stored.
    gemini_key:
        API key for the Gemini model.
    deepl_key:
        API key for the DeepL service.
    grok_key:
        API key for xAI's Grok model.
    qwen_key:
        API key for the Qwen model.
    gemini_key_valid:
        Result of the last Gemini key verification.
    deepl_key_valid:
        Result of the last DeepL key verification.
    grok_key_valid:
        Result of the last Grok key verification.
    qwen_key_valid:
        Result of the last Qwen key verification.
    model:
        Identifier of the LLM or translation model in use.
    synonym_provider:
        Source for synonym suggestions ("datamuse" or "model").
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
    app_background:
        Background colour of the main interface.
    accent_color:
        Accent colour for focused elements.
    text_color:
        Default text colour for widgets.
    font_size:
        Base font size for text areas and tables.
    neon_color:
        Colour of the neon glow for focused elements.
    neon_intensity:
        Stored brightness value for the glow colour.
    neon_width:
        Border width of the glow effect.
    chapter_template:
        Template for naming saved chapters. Use "{n}" as a placeholder for the
        chapter number.
    use_proxy:
        Whether to route network traffic through a proxy.
    proxy_url:
        URL of the proxy server.
    """

    original_path: str = ""
    translation_path: str = ""
    gemini_key: str = ""
    deepl_key: str = ""
    grok_key: str = ""
    qwen_key: str = ""
    gemini_key_valid: bool = False
    deepl_key_valid: bool = False
    grok_key_valid: bool = False
    qwen_key_valid: bool = False
    model: str = ""
    synonym_provider: str = "datamuse"
    machine_check: bool = False
    auto_next: bool = False
    format: str = "docx"
    gdoc_token: str = ""
    gdoc_folder_id: str = ""
    highlight_color: str = "#80ffff00"  # semi-transparent yellow
    app_background: str = styles.APP_BACKGROUND
    accent_color: str = styles.ACCENT_COLOR
    text_color: str = styles.TEXT_COLOR
    neon_color: str = styles.ACCENT_COLOR
    neon_intensity: int = 20
    neon_width: int = 10
    font_size: int = 10
    chapter_template: str = "глава {n}"
    use_proxy: bool = False
    proxy_url: str = ""
    _file: Path = field(default=Path("settings.ini"), repr=False)

    # --- persistence -------------------------------------------------
    def save(self, file: Path | str | None = None) -> None:
        """Persist settings using :class:`QtCore.QSettings`."""

        file_path = Path(file) if file else self._file
        qs = QtCore.QSettings(str(file_path), QtCore.QSettings.Format.IniFormat)
        qs.setValue("original_path", self.original_path)
        qs.setValue("translation_path", self.translation_path)
        qs.setValue("gemini_key", self.gemini_key)
        qs.setValue("deepl_key", self.deepl_key)
        qs.setValue("grok_key", self.grok_key)
        qs.setValue("qwen_key", self.qwen_key)
        qs.setValue("gemini_key_valid", self.gemini_key_valid)
        qs.setValue("deepl_key_valid", self.deepl_key_valid)
        qs.setValue("grok_key_valid", self.grok_key_valid)
        qs.setValue("qwen_key_valid", self.qwen_key_valid)
        qs.setValue("model", self.model)
        qs.setValue("synonym_provider", self.synonym_provider)
        qs.setValue("machine_check", self.machine_check)
        qs.setValue("auto_next", self.auto_next)
        qs.setValue("format", self.format)
        qs.setValue("gdoc_token", self.gdoc_token)
        qs.setValue("gdoc_folder_id", self.gdoc_folder_id)
        qs.setValue("use_proxy", self.use_proxy)
        qs.setValue("proxy_url", self.proxy_url)
        qs.setValue("highlight_color", self.highlight_color)
        qs.setValue("app_background", self.app_background)
        qs.setValue("accent_color", self.accent_color)
        qs.setValue("text_color", self.text_color)
        qs.setValue("font_size", self.font_size)
        qs.setValue("neon_color", self.neon_color)
        qs.setValue("neon_intensity", self.neon_intensity)
        qs.setValue("neon_width", self.neon_width)
        qs.setValue("chapter_template", self.chapter_template)
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
            gemini_key=qs.value("gemini_key", "", str),
            deepl_key=qs.value("deepl_key", "", str),
            grok_key=qs.value("grok_key", "", str),
            qwen_key=qs.value("qwen_key", "", str),
            gemini_key_valid=qs.value("gemini_key_valid", False, bool),
            deepl_key_valid=qs.value("deepl_key_valid", False, bool),
            grok_key_valid=qs.value("grok_key_valid", False, bool),
            qwen_key_valid=qs.value("qwen_key_valid", False, bool),
            model=qs.value("model", "", str),
            synonym_provider=qs.value("synonym_provider", "datamuse", str),
            machine_check=qs.value("machine_check", False, bool),
            auto_next=qs.value("auto_next", False, bool),
            format=qs.value("format", "docx", str),
            gdoc_token=qs.value("gdoc_token", "", str),
            gdoc_folder_id=qs.value("gdoc_folder_id", "", str),
            use_proxy=qs.value("use_proxy", False, bool),
            proxy_url=qs.value("proxy_url", "", str),
            highlight_color=qs.value("highlight_color", "#80ffff00", str),
            app_background=qs.value("app_background", styles.APP_BACKGROUND, str),
            accent_color=qs.value("accent_color", styles.ACCENT_COLOR, str),
            text_color=qs.value("text_color", styles.TEXT_COLOR, str),
            font_size=qs.value("font_size", 10, int),
            neon_color=qs.value("neon_color", styles.ACCENT_COLOR, str),
            neon_intensity=qs.value("neon_intensity", 20, int),
            neon_width=qs.value("neon_width", 10, int),
            chapter_template=qs.value("chapter_template", "глава {n}", str),
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
        self._neon_color = QtGui.QColor(settings.neon_color)
        base = Path(
            self.settings.translation_path
            or self.settings.original_path
            or "."
        )
        self._stats_path = base / "stats.json"
        self._glossary_folder = base / "glossaries"

        main_layout = QtWidgets.QVBoxLayout(self)
        tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(tabs)

        settings_widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(settings_widget)

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

        self.use_proxy_box = QtWidgets.QCheckBox(
            "Использовать прокси", objectName="use_proxy"
        )
        self.use_proxy_box.setChecked(settings.use_proxy)
        self.use_proxy_box.toggled.connect(self._on_proxy_toggle)

        self.proxy_url_edit = QtWidgets.QLineEdit(
            settings.proxy_url, objectName="proxy_url"
        )
        self.proxy_check_btn = QtWidgets.QPushButton("Проверить")
        self.proxy_check_btn.clicked.connect(self._test_proxy)
        self._on_proxy_toggle(self.use_proxy_box.isChecked())

        self.gemini_key_edit = QtWidgets.QLineEdit(settings.gemini_key)
        self.deepl_key_edit = QtWidgets.QLineEdit(settings.deepl_key)
        self.grok_key_edit = QtWidgets.QLineEdit(settings.grok_key)
        self.qwen_key_edit = QtWidgets.QLineEdit(settings.qwen_key)
        self.gdoc_token_edit = QtWidgets.QLineEdit(settings.gdoc_token)
        self.gdoc_folder_edit = QtWidgets.QLineEdit(settings.gdoc_folder_id)

        icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
        )
        self._key_edits = {
            "gemini": self.gemini_key_edit,
            "deepl": self.deepl_key_edit,
            "grok": self.grok_key_edit,
            "qwen": self.qwen_key_edit,
        }
        self._key_labels: dict[str, QtWidgets.QLabel] = {}
        self._verified_key = {
            "gemini": settings.gemini_key if settings.gemini_key_valid else "",
            "deepl": settings.deepl_key if settings.deepl_key_valid else "",
            "grok": settings.grok_key if settings.grok_key_valid else "",
            "qwen": settings.qwen_key if settings.qwen_key_valid else "",
        }
        self._key_valid = {
            "gemini": settings.gemini_key_valid,
            "deepl": settings.deepl_key_valid,
            "grok": settings.grok_key_valid,
            "qwen": settings.qwen_key_valid,
        }

        for name, edit in self._key_edits.items():
            label = QtWidgets.QLabel()
            label.setPixmap(icon.pixmap(16, 16))
            if self._key_valid[name]:
                label.show()
            else:
                label.hide()
            edit.textChanged.connect(
                lambda text, n=name: self._on_key_changed(n)
            )
            edit.editingFinished.connect(lambda n=name: self._verify_key(n))
            layout_row = QtWidgets.QHBoxLayout()
            layout_row.addWidget(edit)
            layout_row.addWidget(label)
            label_text = {
                "gemini": "Ключ Gemini",
                "deepl": "Ключ DeepL",
                "grok": "Ключ Grok",
                "qwen": "Ключ Qwen",
            }[name]
            layout.addRow(label_text, layout_row)
            self._key_labels[name] = label

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItems(["gemini", "deepl", "grok", "qwen"])
        if settings.model:
            index = self.model_combo.findText(settings.model)
            if index != -1:
                self.model_combo.setCurrentIndex(index)

        self.synonym_combo = QtWidgets.QComboBox()
        self.synonym_combo.addItems(["datamuse", "model"])
        index = self.synonym_combo.findText(settings.synonym_provider)
        if index != -1:
            self.synonym_combo.setCurrentIndex(index)

        self.machine_check_box = QtWidgets.QCheckBox()
        self.machine_check_box.setChecked(settings.machine_check)

        self.auto_next_box = QtWidgets.QCheckBox()
        self.auto_next_box.setChecked(settings.auto_next)

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["docx", "txt"])
        index = self.format_combo.findText(settings.format)
        if index != -1:
            self.format_combo.setCurrentIndex(index)

        self.chapter_template_edit = QtWidgets.QLineEdit(settings.chapter_template)

        self.app_bg_edit = QtWidgets.QLineEdit(settings.app_background)
        self.app_bg_btn = QtWidgets.QPushButton()
        self.app_bg_btn.setStyleSheet(
            f"background-color: {settings.app_background}"
        )
        self.app_bg_btn.clicked.connect(
            lambda: self._choose_named_color(self.app_bg_edit, self.app_bg_btn)
        )
        self.app_bg_edit.textChanged.connect(
            lambda text: self.app_bg_btn.setStyleSheet(f"background-color: {text}")
        )

        self.accent_color_edit = QtWidgets.QLineEdit(settings.accent_color)
        self.accent_color_btn = QtWidgets.QPushButton()
        self.accent_color_btn.setStyleSheet(
            f"background-color: {settings.accent_color}"
        )
        self.accent_color_btn.clicked.connect(
            lambda: self._choose_named_color(
                self.accent_color_edit, self.accent_color_btn
            )
        )
        self.accent_color_edit.textChanged.connect(
            lambda text: self.accent_color_btn.setStyleSheet(
                f"background-color: {text}"
            )
        )

        self.text_color_edit = QtWidgets.QLineEdit(settings.text_color)
        self.text_color_btn = QtWidgets.QPushButton()
        self.text_color_btn.setStyleSheet(
            f"background-color: {settings.text_color}"
        )
        self.text_color_btn.clicked.connect(
            lambda: self._choose_named_color(self.text_color_edit, self.text_color_btn)
        )
        self.text_color_edit.textChanged.connect(
            lambda text: self.text_color_btn.setStyleSheet(f"background-color: {text}")
        )

        self.color_btn = QtWidgets.QPushButton()
        self._update_color_btn()
        self.color_btn.clicked.connect(self._choose_color)
        self.neon_color_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.neon_color_slider.setRange(0, 359)
        hue = self._neon_color.hue()
        self.neon_color_slider.setValue(0 if hue == -1 else hue)

        self.neon_intensity_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.neon_intensity_slider.setRange(1, 50)
        self.neon_intensity_slider.setValue(settings.neon_intensity)

        self.neon_width_spin = QtWidgets.QSpinBox()
        self.neon_width_spin.setRange(1, 50)
        self.neon_width_spin.setValue(settings.neon_width)

        self.neon_preview = QtWidgets.QFrame()
        self.neon_preview.setFixedSize(40, 20)
        self.neon_preview.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.neon_color_slider.valueChanged.connect(self._update_neon_preview)
        self.neon_intensity_slider.valueChanged.connect(self._update_neon_preview)
        self.neon_width_spin.valueChanged.connect(self._update_neon_preview)
        self._update_neon_preview()

        layout.addRow("Папка оригинала", orig_layout)
        layout.addRow("Папка перевода", trans_layout)
        layout.addRow(self.use_proxy_box)
        proxy_layout = QtWidgets.QHBoxLayout()
        proxy_layout.addWidget(self.proxy_url_edit)
        proxy_layout.addWidget(self.proxy_check_btn)
        layout.addRow("URL прокси", proxy_layout)
        layout.addRow("Токен Google Docs", self.gdoc_token_edit)
        layout.addRow("ID папки Google Docs", self.gdoc_folder_edit)
        layout.addRow("Модель", self.model_combo)
        layout.addRow("Провайдер синонимов", self.synonym_combo)
        layout.addRow("Формат", self.format_combo)
        layout.addRow("Машинная проверка", self.machine_check_box)
        layout.addRow("Следующая глава", self.auto_next_box)
        bg_layout = QtWidgets.QHBoxLayout()
        bg_layout.addWidget(self.app_bg_edit)
        bg_layout.addWidget(self.app_bg_btn)
        layout.addRow("Фон приложения", bg_layout)
        accent_layout = QtWidgets.QHBoxLayout()
        accent_layout.addWidget(self.accent_color_edit)
        accent_layout.addWidget(self.accent_color_btn)
        layout.addRow("Акцентный цвет", accent_layout)
        text_layout = QtWidgets.QHBoxLayout()
        text_layout.addWidget(self.text_color_edit)
        text_layout.addWidget(self.text_color_btn)
        layout.addRow("Цвет текста", text_layout)

        self.font_size_spin = QtWidgets.QSpinBox()
        self.font_size_spin.setRange(6, 48)
        self.font_size_spin.setValue(settings.font_size)
        layout.addRow("Размер шрифта", self.font_size_spin)
        layout.addRow("Цвет подсветки", self.color_btn)
        layout.addRow("Цвет свечения", self.neon_color_slider)
        layout.addRow("Интенсивность свечения", self.neon_intensity_slider)
        layout.addRow("Ширина свечения", self.neon_width_spin)
        layout.addRow("Предпросмотр свечения", self.neon_preview)
        layout.addRow("Шаблон главы", self.chapter_template_edit)

        tabs.addTab(settings_widget, "Общие")

        stats_widget = QtWidgets.QWidget()
        stats_layout = QtWidgets.QFormLayout(stats_widget)
        self.stats_chars = QtWidgets.QLabel("0")
        self.stats_chapters = QtWidgets.QLabel("0")
        self.stats_time = QtWidgets.QLabel("00:00:00")
        self.stats_pairs = QtWidgets.QLabel("0")
        reset_btn = QtWidgets.QPushButton("Сбросить статистику")
        reset_btn.clicked.connect(self._reset_stats)
        stats_layout.addRow("Переведённых символов", self.stats_chars)
        stats_layout.addRow("Глав", self.stats_chapters)
        stats_layout.addRow("Общее время", self.stats_time)
        stats_layout.addRow("Пар слов", self.stats_pairs)
        stats_layout.addRow(reset_btn)
        tabs.addTab(stats_widget, "Статистика")

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self._refresh_stats()

    # --- internal helpers --------------------------------------------
    def _refresh_stats(self) -> None:
        stats = load_stats(self._stats_path)
        total_chars = sum(entry.get("characters", 0) for entry in stats)
        total_time = sum(entry.get("time", 0) for entry in stats)
        chapters = len(stats)
        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.stats_chars.setText(str(total_chars))
        self.stats_chapters.setText(str(chapters))
        self.stats_time.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        pair_count = 0
        if self._glossary_folder.exists():
            for path in list_glossaries(self._glossary_folder):
                try:
                    glossary = Glossary.load(path)
                except Exception:
                    continue
                pair_count += len(glossary.entries)
        self.stats_pairs.setText(str(pair_count))

    def _reset_stats(self) -> None:
        save_stats([], self._stats_path)
        self._refresh_stats()

    def _on_key_changed(self, name: str) -> None:
        """Reset cached verification when a key edit is modified."""
        label = self._key_labels[name]
        text = self._key_edits[name].text()
        if text == self._verified_key.get(name, ""):
            if self._key_valid[name]:
                label.show()
            else:
                label.hide()
            return
        label.hide()
        self._key_valid[name] = False
        self._verified_key[name] = ""

    def _verify_key(self, name: str) -> None:
        """Perform a test request to validate an API key."""
        edit = self._key_edits[name]
        label = self._key_labels[name]
        key = edit.text().strip()
        if key == self._verified_key.get(name, ""):
            if self._key_valid[name]:
                label.show()
            else:
                label.hide()
            return
        if not key:
            label.hide()
            self._key_valid[name] = False
            self._verified_key[name] = ""
            return
        try:
            if name == "gemini":
                from .models.gemini import GeminiTranslator

                GeminiTranslator(key, settings=self.settings).translate("ping")
            elif name == "deepl":
                from .models.deepl import DeepLTranslator

                DeepLTranslator(key).translate("ping")
            elif name == "grok":
                from .models.grok import GrokTranslator

                GrokTranslator(key).translate("ping")
            elif name == "qwen":
                from .models.qwen import QwenTranslator

                QwenTranslator(key).translate("ping")
            success = True
        except Exception:
            success = False
        if success:
            label.show()
        else:
            label.hide()
        self._key_valid[name] = success
        self._verified_key[name] = key

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

    def _choose_named_color(
        self, edit: QtWidgets.QLineEdit, btn: QtWidgets.QPushButton
    ) -> None:
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(edit.text()), self)
        if color.isValid():
            edit.setText(color.name())
            btn.setStyleSheet(f"background-color: {color.name()}")

    def _on_proxy_toggle(self, checked: bool) -> None:
        self.proxy_url_edit.setEnabled(checked)
        self.proxy_check_btn.setEnabled(checked)

    def _test_proxy(self) -> None:
        import requests

        url = self.proxy_url_edit.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(
                self, "Проверка прокси", "Укажите URL прокси"
            )
            return
        proxies = {"http": url, "https": url}
        try:
            requests.get("https://httpbin.org/get", proxies=proxies, timeout=5)
        except Exception as exc:  # pragma: no cover - network error message
            QtWidgets.QMessageBox.critical(
                self, "Проверка прокси", f"Не удалось подключиться: {exc}"
            )
        else:  # pragma: no cover - network success message
            QtWidgets.QMessageBox.information(
                self, "Проверка прокси", "Прокси работает"
            )

    def _update_neon_preview(self) -> None:
        color = QtGui.QColor.fromHsv(
            self.neon_color_slider.value(),
            255,
            min(255, self.neon_intensity_slider.value() * 5),
        )
        self.neon_preview.setStyleSheet(
            f"background-color: {color.name()}; border: {self.neon_width_spin.value()}px solid {color.name()}"
        )

    def _update_color_btn(self) -> None:
        self.color_btn.setStyleSheet(
            f"background-color: {self._color.name(QtGui.QColor.NameFormat.HexArgb)}"
        )

    # --- Qt overrides ------------------------------------------------
    def accept(self) -> None:  # type: ignore[override]
        self.settings.original_path = self.original_edit.text()
        self.settings.translation_path = self.translation_edit.text()
        self.settings.gemini_key = self.gemini_key_edit.text()
        self.settings.deepl_key = self.deepl_key_edit.text()
        self.settings.grok_key = self.grok_key_edit.text()
        self.settings.qwen_key = self.qwen_key_edit.text()
        self.settings.gemini_key_valid = (
            self._key_valid["gemini"]
            and self._verified_key["gemini"] == self.gemini_key_edit.text().strip()
        )
        self.settings.deepl_key_valid = (
            self._key_valid["deepl"]
            and self._verified_key["deepl"] == self.deepl_key_edit.text().strip()
        )
        self.settings.grok_key_valid = (
            self._key_valid["grok"]
            and self._verified_key["grok"] == self.grok_key_edit.text().strip()
        )
        self.settings.qwen_key_valid = (
            self._key_valid["qwen"]
            and self._verified_key["qwen"] == self.qwen_key_edit.text().strip()
        )
        self.settings.gdoc_token = self.gdoc_token_edit.text()
        self.settings.gdoc_folder_id = self.gdoc_folder_edit.text()
        self.settings.use_proxy = self.use_proxy_box.isChecked()
        self.settings.proxy_url = self.proxy_url_edit.text()
        self.settings.model = self.model_combo.currentText()
        self.settings.synonym_provider = self.synonym_combo.currentText()
        self.settings.machine_check = self.machine_check_box.isChecked()
        self.settings.auto_next = self.auto_next_box.isChecked()
        self.settings.format = self.format_combo.currentText()
        self.settings.app_background = self.app_bg_edit.text()
        self.settings.accent_color = self.accent_color_edit.text()
        self.settings.text_color = self.text_color_edit.text()
        self.settings.highlight_color = self._color.name(
            QtGui.QColor.NameFormat.HexArgb
        )
        neon = QtGui.QColor.fromHsv(
            self.neon_color_slider.value(),
            255,
            min(255, self.neon_intensity_slider.value() * 5),
        )
        self.settings.neon_color = neon.name()
        self.settings.neon_intensity = self.neon_intensity_slider.value()
        self.settings.neon_width = self.neon_width_spin.value()
        self.settings.font_size = self.font_size_spin.value()
        self.settings.chapter_template = self.chapter_template_edit.text()
        styles.init(self.settings)
        self.settings.save()
        super().accept()

