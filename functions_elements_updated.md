
## Элементы функций

### 1. Функция **load_fonts**
   - Загрузчик шрифтов для интерфейса. Загружает шрифты для основного текста и заголовков.
   - Пример кода:
     ```python
     def load_fonts():
         QFontDatabase.addApplicationFont('path/to/Inter.ttf')
         QFontDatabase.addApplicationFont('path/to/Cattedrale.ttf')
     ```

### 2. Функция **_build_ui**
   - Строит основной интерфейс приложения.
   - Создает элементы управления, такие как кнопки, поля ввода и меню.
   - Пример кода:
     ```python
     def _build_ui(self):
         header = QHBoxLayout()
         self.lblTitle = QLabel('Переводчик')
         self.cmbModel = QComboBox()
         header.addWidget(self.lblTitle)
         header.addWidget(self.cmbModel)
     ```

### 3. Функция **on_translate**
   - Отправляет запрос на перевод в выбранную модель.
   - Формирует промпт, включая глоссарий, и отправляет текст в модель.
   - Пример кода:
     ```python
     def on_translate(self):
         model = self.registry.client(self.cmbModel.currentText())
         prompt = self.prompt_builder.build(self.txtPrompt.toPlainText())
         response = model.translate(self.txtOriginal.toPlainText(), prompt)
         self.txtTranslate.setPlainText(response)
     ```

### 4. Функция **on_save**
   - Сохраняет переведенный текст в облако или на локальный диск.
   - Пример кода:
     ```python
     def on_save(self):
         text = self.txtTranslate.toPlainText()
         self.chapters.save_translation(idx, text)
     ```

### 5. Функция **_maybe_offer_synonyms**
   - По клику на слово в поле «Перевод» система анализирует контекст и предлагает синонимы.
   - Пример:
     ```python
     def _maybe_offer_synonyms(self):
         word = self.txtTranslate.selected_text()
         synonyms = model.get_synonyms(word, left_context, right_context)
         # Выводим синонимы пользователю для выбора
     ```

### 6. Обработчик **cursorPositionChanged**
   - При изменении позиции курсора в поле «Перевод» определяет текущие слово и контекст.
   - Автоматически вызывает существующую функцию `_show_synonym_menu`, что приводит к отображению списка синонимов без вызова контекстного меню.
   - Пример:
     ```python
     def _on_cursor_position_changed(self):
         cursor = self.translation_edit.textCursor()
         cursor.select(QTextCursor.WordUnderCursor)
         word = cursor.selectedText()
         self._show_synonym_menu(self.translation_edit.cursorRect(cursor).bottomRight())
     ```
