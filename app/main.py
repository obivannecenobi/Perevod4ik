"""Application entry point and controller logic."""

from __future__ import annotations

import sys
from pathlib import Path
from queue import Queue
from typing import Dict

from PyQt6 import QtGui, QtWidgets

from models import get_translator
from services.files import (
    append_stat,
    enqueue_chapters,
    iter_docx_files,
    load_docx,
    load_stats,
    save_docx,
)
from services.reports import save_csv, save_html
from services.versioning import check_for_updates
from services.workers import DEFAULT_RATE_LIMITER, ModelWorker
from ui_main import Ui_MainWindow
from settings import AppSettings


class MainController:
    """Glue code connecting the UI with services and models."""

    def __init__(self, window: QtWidgets.QMainWindow, ui: Ui_MainWindow, settings: AppSettings) -> None:
        self.window = window
        self.ui = ui
        self.settings = settings
        self.chapters: list[Path] = []
        self.worker: ModelWorker | None = None
        self.batch_queue: Queue[Path] | None = None
        self.stats_path = Path(self.settings.project_path or ".") / "stats.json"
        self.stats = load_stats(self.stats_path)

        self._init_ui()
        self._load_chapter_list()

    # ------------------------------------------------------------------
    # UI setup and shortcuts
    def _init_ui(self) -> None:
        # translate buttons
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.translate_btn = QtWidgets.QPushButton("Перевести", parent=self.ui.translation_widget)
        self.batch_btn = QtWidgets.QPushButton("Перевести все", parent=self.ui.translation_widget)
        self.buttons_layout.addWidget(self.translate_btn)
        self.buttons_layout.addWidget(self.batch_btn)
        self.ui.translation_layout.insertLayout(0, self.buttons_layout)
        self.translate_btn.clicked.connect(self.translate)
        self.batch_btn.clicked.connect(self.batch_translate)

        # chapter navigation
        self.ui.prev_btn.clicked.connect(self.prev_chapter)
        self.ui.next_btn.clicked.connect(self.next_chapter)
        self.ui.chapter_combo.currentIndexChanged.connect(self.load_chapter)

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

    # ------------------------------------------------------------------
    # Chapter handling
    def _load_chapter_list(self) -> None:
        path = self.settings.project_path
        if not path:
            return
        folder = Path(path)
        self.chapters = sorted(iter_docx_files(folder))
        self.ui.chapter_combo.clear()
        for file in self.chapters:
            self.ui.chapter_combo.addItem(file.stem)
        if self.chapters:
            self.load_chapter(0)

    def load_chapter(self, index: int) -> None:
        if not (0 <= index < len(self.chapters)):
            return
        text = load_docx(self.chapters[index])
        self.ui.original_edit.setPlainText(text)
        self.ui.translation_edit.clear()
        self.ui.reset_timer()

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
            model = get_translator(self.settings.model or "gemini")
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
        path = self.settings.project_path
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
            model = get_translator(self.settings.model or "gemini")
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
        out_path = src.with_name(src.stem + "_translated.docx")
        save_docx(result, out_path)
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
        out_path = src.with_name(src.stem + "_translated.docx")
        save_docx(text, out_path)
        stat = {"chapter": src.stem, "characters": len(text), "time": self.ui.elapsed}
        self.stats = append_stat(stat, self.stats_path)
        self.ui.reset_timer()

    # ------------------------------------------------------------------
    def export_report(self) -> None:
        if not self.stats:
            QtWidgets.QMessageBox.information(self.window, "Отчёт", "Нет данных для отчёта.")
            return
        default_dir = Path(self.settings.project_path or ".")
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
        QtWidgets.QMessageBox.information(None, "Обновление", "Доступны обновления приложения.")
    window = QtWidgets.QMainWindow()
    settings = AppSettings.load()
    ui = Ui_MainWindow()
    ui.setupUi(window, settings)
    controller = MainController(window, ui, settings)
    app.aboutToQuit.connect(settings.save)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
