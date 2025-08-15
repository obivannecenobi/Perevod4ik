"""Application entry point and controller logic."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from queue import Queue
from typing import Tuple

# Qt 6 no longer ships default fonts. Ensure the application has a font
# directory available so that the GUI doesn't hang on startup when
# QFontDatabase tries to locate fonts. We bundle fonts under ``app/fonts``
# and point ``QT_QPA_FONTDIR`` there before importing any Qt modules.
os.environ.setdefault("QT_QPA_FONTDIR", str(Path(__file__).resolve().parent / "fonts"))

from PyQt6 import QtCore, QtGui, QtWidgets

from .default_icon import ensure_empty_project_icon

ensure_empty_project_icon()

from .models import get_translator, _MODELS
from .services.files import (
    append_stat,
    enqueue_chapters,
    iter_docx_files,
    load_docx,
    load_stats,
    save_docx,
    save_txt,
)
from .services.project import ProjectManager
from .services.cloud import list_documents, load_document
from .services.reports import save_csv, save_html
from .services.versioning import check_for_updates, pull_updates
from .services.workers import DEFAULT_RATE_LIMITER, ModelWorker
from .ui_main import Ui_MainWindow
from .settings import AppSettings


class MainController:
    """Glue code connecting the UI with services and models."""

    def __init__(self, window: QtWidgets.QMainWindow, ui: Ui_MainWindow, settings: AppSettings) -> None:
        self.window = window
        self.ui = ui
        self.settings = settings
        self.chapters: list[Path | Tuple[str, str]] = []
        self.worker: ModelWorker | None = None
        self.batch_queue: Queue[Path] | None = None
        self.project_manager = ProjectManager()
        project_id = (
            Path(self.settings.translation_path or self.settings.original_path or "project").stem
        )
        self.project = self.project_manager.load(project_id, title=project_id)
        base = Path(
            self.settings.translation_path
            or self.settings.original_path
            or "."
        )
        base.mkdir(parents=True, exist_ok=True)
        self.stats_path = base / "stats.json"
        self.stats = load_stats(self.stats_path)

        self._init_ui()
        self._load_chapter_list()

    # ------------------------------------------------------------------
    # UI setup and shortcuts
    def _init_ui(self) -> None:
        # project icon setup
        self.ui.project_icon_btn.clicked.connect(self.choose_project_icon)
        self._refresh_project_item()

        # translate buttons
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.translate_btn = QtWidgets.QPushButton("Перевести", parent=self.ui.translation_widget)
        self.batch_btn = QtWidgets.QPushButton("Перевести все", parent=self.ui.translation_widget)
        self.buttons_layout.addWidget(self.translate_btn)
        self.buttons_layout.addWidget(self.batch_btn)
        self.ui.translation_layout.insertLayout(0, self.buttons_layout)
        self.ui.translation_layout.setStretch(0, 0)
        self.ui.translation_layout.setStretch(1, 1)
        self.ui.translation_layout.setStretch(2, 0)
        self.ui.translation_layout.setStretch(3, 0)
        self.translate_btn.clicked.connect(self.translate)
        self.batch_btn.clicked.connect(self.batch_translate)

        # chapter navigation
        self.ui.prev_btn.clicked.connect(self.prev_chapter)
        self.ui.next_btn.clicked.connect(self.next_chapter)
        self.ui.chapter_combo.currentIndexChanged.connect(self.load_chapter)

        # model selection and saving
        models = [
            name
            for name in sorted(_MODELS.keys())
            if getattr(self.settings, f"{name}_key", "")
        ]
        self.ui.model_combo.clear()
        self.ui.model_combo.addItems(models)
        if self.settings.model:
            idx = self.ui.model_combo.findText(self.settings.model)
            if idx != -1:
                self.ui.model_combo.setCurrentIndex(idx)
        self.ui.model_combo.currentTextChanged.connect(
            lambda name: setattr(self.settings, "model", name)
        )
        self.ui.save_btn.clicked.connect(self.save_translation)

        # shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Enter"), self.window, activated=self.translate)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self.window, activated=self.translate)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self.window, activated=self.save_translation)
        QtGui.QShortcut(QtGui.QKeySequence("Alt+Right"), self.window, activated=self.next_chapter)
        QtGui.QShortcut(QtGui.QKeySequence("Alt+Left"), self.window, activated=self.prev_chapter)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+G"), self.window, activated=lambda: self.ui.glossary_table.setFocus())
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+1"), self.window, activated=lambda: self.ui.original_edit.setFocus())
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+2"), self.window, activated=lambda: self.ui.translation_edit.setFocus())
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+3"), self.window, activated=lambda: self.ui.mini_prompt_edit.setFocus())

        # report export button
        self.export_btn = QtWidgets.QPushButton("Экспорт отчёта", parent=self.ui.centralwidget)
        self.ui.status_layout.insertWidget(0, self.export_btn)
        self.export_btn.clicked.connect(self.export_report)
    
    def choose_project_icon(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            "Выбор иконки",
            "",
            "Images (*.png *.jpg *.bmp)"
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
        self.project.icon_path = path
        self.project_manager.save(self.project)
        self._refresh_project_item(pixmap)

    def _refresh_project_item(self, pixmap: QtGui.QPixmap | None = None) -> None:
        self.ui.project_list.clear()
        if pixmap is None:
            pixmap = QtGui.QPixmap(self.project.icon_path)
            if pixmap.isNull():
                pixmap = QtGui.QPixmap("assets/empty_project.png")
            pixmap = pixmap.scaled(
                32,
                32,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        item = QtWidgets.QListWidgetItem(QtGui.QIcon(pixmap), self.project.title)
        self.ui.project_list.addItem(item)

    # ------------------------------------------------------------------
    # Chapter handling
    def _load_chapter_list(self) -> None:
        token = getattr(self.settings, "gdoc_token", "")
        folder_id = getattr(self.settings, "gdoc_folder_id", "")
        self.ui.chapter_combo.clear()
        if token and folder_id:
            try:
                self.chapters = list_documents(token, folder_id)
            except Exception as exc:  # pragma: no cover - network/auth issues
                QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(exc))
                self.chapters = []
                return
            for _, name in self.chapters:
                self.ui.chapter_combo.addItem(name)
            if self.chapters:
                self.load_chapter(0)
            return
        path = self.settings.original_path
        if not path:
            return
        folder = Path(path)
        self.chapters = sorted(iter_docx_files(folder))
        for file in self.chapters:
            self.ui.chapter_combo.addItem(file.stem)
        if self.chapters:
            self.load_chapter(0)

    def load_chapter(self, index: int) -> None:
        if not (0 <= index < len(self.chapters)):
            return
        chapter = self.chapters[index]
        if isinstance(chapter, tuple):
            doc_id, _ = chapter
            try:
                text = load_document(self.settings.gdoc_token, doc_id)
            except Exception as exc:  # pragma: no cover - network/auth issues
                QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(exc))
                return
        else:
            text = load_docx(chapter)
        self.ui.original_edit.setPlainText(text)
        self.ui.translation_edit.clear()
        self.ui.reset_timer()
        context = self.project_manager.overview(self.project, index)
        if context:
            self.ui.mini_prompt_edit.setPlaceholderText(context)

    def prev_chapter(self) -> None:
        idx = self.ui.chapter_combo.currentIndex()
        if idx > 0:
            self.ui.chapter_combo.setCurrentIndex(idx - 1)

    def next_chapter(self) -> None:
        idx = self.ui.chapter_combo.currentIndex()
        if idx < len(self.chapters) - 1:
            self.ui.chapter_combo.setCurrentIndex(idx + 1)

    # ------------------------------------------------------------------
    # Translation workflow
    def _parse_glossary(self) -> Dict[str, str]:
        return self.ui.glossary_entries()

    def translate(self) -> None:
        text = self.ui.original_edit.toPlainText().strip()
        if not text:
            return
        prompt = self.ui.mini_prompt_edit.toPlainText().strip()
        glossary = self._parse_glossary()
        try:
            model = get_translator(self.settings.model or "gemini", self.settings)
        except Exception as exc:  # pragma: no cover - settings misuse
            QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(exc))
            return

        self.translate_btn.setEnabled(False)
        worker = ModelWorker(
            model,
            text,
            prompt=prompt,
            glossary=glossary,
            rate_limiter=DEFAULT_RATE_LIMITER,
        )
        worker.finished.connect(self._on_translation_finished)
        worker.error.connect(self._on_translation_error)
        worker.start()
        self.worker = worker

    def _on_translation_finished(self, result: str) -> None:
        self.translate_btn.setEnabled(True)
        self.ui.translation_edit.setPlainText(result)

    def _on_translation_error(self, exc: Exception) -> None:
        self.translate_btn.setEnabled(True)
        QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(exc))

    # ------------------------------------------------------------------
    # Batch translation
    def batch_translate(self) -> None:
        path = self.settings.original_path
        if not path:
            return
        queue: Queue[Path] = Queue()
        self.chapters = enqueue_chapters(Path(path), queue)
        if not self.chapters:
            return
        self.batch_queue = queue
        self.batch_btn.setEnabled(False)
        self.translate_btn.setEnabled(False)
        self._process_queue()

    def _process_queue(self) -> None:
        if not self.batch_queue or self.batch_queue.empty():
            self.batch_btn.setEnabled(True)
            self.translate_btn.setEnabled(True)
            return
        src = self.batch_queue.get()
        text = load_docx(src)
        prompt = self.ui.mini_prompt_edit.toPlainText().strip()
        glossary = self._parse_glossary()
        try:
            model = get_translator(self.settings.model or "gemini", self.settings)
        except Exception as exc:  # pragma: no cover - settings misuse
            QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(exc))
            self._process_queue()
            return
        worker = ModelWorker(
            model,
            text,
            prompt=prompt,
            glossary=glossary,
            rate_limiter=DEFAULT_RATE_LIMITER,
        )
        worker.finished.connect(lambda result, p=src: self._on_batch_translation_finished(p, result))
        worker.error.connect(self._on_batch_translation_error)
        worker.start()
        self.worker = worker

    def _on_batch_translation_finished(self, src: Path, result: str) -> None:
        self.ui.translation_edit.setPlainText(result)
        idx = self.chapters.index(src) if src in self.chapters else 0
        name = self.settings.chapter_template.format(n=idx + 1)
        if self.settings.translation_path:
            out_dir = Path(self.settings.translation_path)
            out_dir.mkdir(parents=True, exist_ok=True)
            base = out_dir / name
        else:
            base = src.with_name(name)
        out_path = base.with_suffix(".docx")
        save_docx(result, out_path)
        self.project_manager.add_chapter(self.project, name, result)
        self._process_queue()

    def _on_batch_translation_error(self, exc: Exception) -> None:
        QtWidgets.QMessageBox.critical(self.window, "Ошибка", str(exc))
        self._process_queue()

    # ------------------------------------------------------------------
    def save_translation(self) -> None:
        if not self.chapters:
            return
        idx = self.ui.chapter_combo.currentIndex()
        if not (0 <= idx < len(self.chapters)):
            return
        text = self.ui.translation_edit.toPlainText()
        if not text:
            return
        src = self.chapters[idx]
        ext = ".txt" if self.settings.format == "txt" else ".docx"
        save_func = save_txt if self.settings.format == "txt" else save_docx
        name = self.settings.chapter_template.format(n=idx + 1)

        if isinstance(src, tuple):
            if self.settings.translation_path:
                out_dir = Path(self.settings.translation_path)
                out_dir.mkdir(parents=True, exist_ok=True)
                base = out_dir / name
            else:
                base = Path(name)
            out_path = base.with_suffix(ext)
            save_func(text, out_path)
        else:
            if self.settings.translation_path:
                out_dir = Path(self.settings.translation_path)
                out_dir.mkdir(parents=True, exist_ok=True)
                base = out_dir / name
            else:
                base = src.with_name(name)
            out_path = base.with_suffix(ext)
            save_func(text, out_path)
        stat = {"chapter": name, "characters": len(text), "time": self.ui.elapsed}
        self.stats = append_stat(stat, self.stats_path)
        self.project_manager.add_chapter(self.project, name, text)
        self.ui.reset_timer()
        self.ui.version_manager.flush()
        if self.settings.auto_next:
            self.next_chapter()

    # ------------------------------------------------------------------
    def export_report(self) -> None:
        if not self.stats:
            QtWidgets.QMessageBox.information(self.window, "Отчёт", "Нет данных для отчёта.")
            return
        default_dir = Path(
            self.settings.translation_path
            or self.settings.original_path
            or "."
        )
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            "Сохранить отчёт",
            str(default_dir / "report.csv"),
            "CSV (*.csv);;HTML (*.html)",
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() == ".csv":
            save_csv(self.stats, target)
        else:
            save_html(self.stats, target)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    repo_root = Path(__file__).resolve().parent.parent
    if check_for_updates(repo_root):
        success, message = pull_updates(repo_root)
        if success:
            QtWidgets.QMessageBox.information(None, "Обновление", "Приложение обновлено до последней версии.")
        else:
            QtWidgets.QMessageBox.warning(None, "Обновление", f"Не удалось обновить приложение: {message}")
    window = QtWidgets.QMainWindow()
    settings = AppSettings.load()
    ui = Ui_MainWindow()
    ui.setupUi(window, settings)
    controller = MainController(window, ui, settings)
    app.aboutToQuit.connect(settings.save)
    app.aboutToQuit.connect(ui.version_manager.flush)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
