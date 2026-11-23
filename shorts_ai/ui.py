from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QScrollArea, QProgressBar, QListWidget, QMessageBox, QSplitter,
    QPlainTextEdit
)
from .worker import ClipWorker

CATEGORY_GROUPS = {
    "Эмоции и чувства": [
        "Самые эмоциональные моменты", "Драматичные сцены", "Грустные моменты",
        "Романтические сцены", "Трогательные моменты", "Радость и счастье"
    ],
    "Интересные события": [
        "Самые интересные моменты", "Неожиданные повороты сюжета",
        "Шокирующие моменты", "Напряжённые сцены", "Загадочные моменты",
        "Кульминационные сцены"
    ],
    "Диалоги": [
        "Интересные разговоры", "Сильные цитаты и фразы", "Глубокие разговоры",
        "Споры и конфликты", "Сарказм и остроумные ответы", "Мотивационные речи"
    ],
    "Развлекательные сцены": [
        "Смешные моменты", "Необычные ситуации", "Неловкие моменты",
        "Неожиданные реакции", "Яркие персонажи"
    ],
    "Экшен и динамика": [
        "Драки и сражения", "Погони", "Опасные ситуации",
        "Захватывающие сцены", "Эффектные появления персонажей"
    ],
}

STYLE = """
QWidget { background: #17191f; color: #eceef4; font-size: 13px; }
QMainWindow { background: #17191f; }
QLabel#title { font-size: 25px; font-weight: 700; color: #ffffff; }
QLabel#muted { color: #a6adbd; }
QGroupBox { border: 1px solid #353a47; border-radius: 10px; margin-top: 12px; padding: 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QPushButton { background: #303747; border: 0; border-radius: 8px; padding: 10px 14px; }
QPushButton:hover { background: #414d64; }
QPushButton#primary { background: #6d5dfc; font-weight: 700; }
QPushButton#primary:hover { background: #8275ff; }
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QListWidget {
 background: #222630; border: 1px solid #3a4050; border-radius: 7px; padding: 8px;
}
QCheckBox { spacing: 8px; padding: 3px; }
QProgressBar { background: #252a35; border: 0; border-radius: 5px; height: 12px; text-align: center; }
QProgressBar::chunk { background: #6d5dfc; border-radius: 5px; }
QScrollArea { border: 0; }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shorts AI Studio")
        self.resize(1120, 820)
        self.setStyleSheet(STYLE)
        self.video_path = None
        self.worker = None
        self.checks = {}
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        header = QHBoxLayout()
        title = QLabel("Shorts AI Studio")
        title.setObjectName("title")
        subtitle = QLabel("ИИ-помощник для создания вертикальных видео")
        subtitle.setObjectName("muted")
        lefthead = QVBoxLayout()
        lefthead.addWidget(title)
        lefthead.addWidget(subtitle)
        header.addLayout(lefthead)
        header.addStretch()
        header.addWidget(QLabel("Локальная версия · Windows"))
        outer.addLayout(header)

        split = QSplitter(Qt.Horizontal)
        outer.addWidget(split, 1)

        left = QWidget()
        lv = QVBoxLayout(left)
        filebox = QGroupBox("1. Исходное видео")
        fb = QVBoxLayout(filebox)
        self.file_label = QLabel("Видео ещё не выбрано")
        self.file_label.setWordWrap(True)
        row = QHBoxLayout()
        choose = QPushButton("Выбрать видео")
        choose.clicked.connect(self.choose_video)
        row.addWidget(choose)
        row.addStretch()
        fb.addWidget(self.file_label)
        fb.addLayout(row)
        lv.addWidget(filebox)

        settings = QGroupBox("2. Параметры Shorts")
        sv = QVBoxLayout(settings)
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Количество клипов"))
        self.count = QSpinBox()
        self.count.setRange(1, 50)
        self.count.setValue(5)
        r1.addWidget(self.count)
        r1.addStretch()
        sv.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Длительность"))
        self.duration = QComboBox()
        self.duration.addItems(["15 секунд", "30 секунд", "45 секунд", "60 секунд"])
        self.duration.setCurrentText("30 секунд")
        r2.addWidget(self.duration)
        r2.addStretch()
        sv.addLayout(r2)
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Субтитры"))
        self.subtitles = QComboBox()
        self.subtitles.addItems(["Без субтитров", "Белые с обводкой", "Жёлтые акцентные"])
        r3.addWidget(self.subtitles)
        r3.addStretch()
        sv.addLayout(r3)
        lv.addWidget(settings)

        catbox = QGroupBox("3. Какие моменты искать? (необязательно)")
        catlayout = QVBoxLayout(catbox)
        hint = QLabel("Если не поставить ни одной галочки, ИИ выберет моменты автоматически.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        catlayout.addWidget(hint)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cv = QVBoxLayout(content)
        for group, items in CATEGORY_GROUPS.items():
            group_label = QLabel(group)
            group_label.setStyleSheet("color:#b8b1ff; font-weight:700; margin-top:5px;")
            cv.addWidget(group_label)
            for item in items:
                cb = QCheckBox(item)
                self.checks[item] = cb
                cv.addWidget(cb)
        cv.addStretch()
        scroll.setWidget(content)
        catlayout.addWidget(scroll)
        lv.addWidget(catbox, 1)

        self.start_btn = QPushButton("Найти моменты и создать Shorts")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.start_processing)
        lv.addWidget(self.start_btn)
        split.addWidget(left)

        right = QWidget()
        rv = QVBoxLayout(right)
        outbox = QGroupBox("4. Процесс создания")
        ov = QVBoxLayout(outbox)
        self.status = QLabel("Ожидаю видео")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Здесь появится ход анализа и монтажа…")
        ov.addWidget(self.status)
        ov.addWidget(self.progress)
        ov.addWidget(self.log)
        rv.addWidget(outbox, 1)

        clipsbox = QGroupBox("5. Готовые клипы")
        cl = QVBoxLayout(clipsbox)
        self.clips = QListWidget()
        cl.addWidget(self.clips)
        self.open_folder_btn = QPushButton("Открыть папку с клипами")
        self.open_folder_btn.clicked.connect(self.open_output)
        cl.addWidget(self.open_folder_btn)
        rv.addWidget(clipsbox, 1)

        trendbox = QGroupBox("Тренды")
        tv = QVBoxLayout(trendbox)
        tv.addWidget(QLabel("Раздел подготовлен для подключения источников трендов YouTube и TikTok."))
        tv.addWidget(QLabel("Для актуальных данных потребуется интернет и подключение API/источника аналитики."))
        rv.addWidget(trendbox)
        split.addWidget(right)
        split.setSizes([520, 600])

    def choose_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать видео", "", "Видео (*.mp4 *.mkv *.avi *.mov *.webm);;Все файлы (*.*)"
        )
        if path:
            self.video_path = Path(path)
            self.file_label.setText(str(self.video_path))

    def selected_categories(self):
        return [name for name, cb in self.checks.items() if cb.isChecked()]

    def start_processing(self):
        if not self.video_path:
            QMessageBox.warning(self, "Нет видео", "Сначала выбери видеофайл.")
            return
        if self.worker and self.worker.isRunning():
            return
        outdir = self.video_path.parent / "Shorts_AI_Studio_Clips"
        duration = int(self.duration.currentText().split()[0])
        style = self.subtitles.currentText()
        self.clips.clear()
        self.log.clear()
        self.progress.setValue(0)
        self.start_btn.setEnabled(False)
        self.worker = ClipWorker(
            str(self.video_path), str(outdir), self.count.value(), duration,
            self.selected_categories(), style
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.message.connect(self.log.appendPlainText)
        self.worker.clip_created.connect(self.clips.addItem)
        self.worker.completed.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, value, text):
        self.progress.setValue(value)
        self.status.setText(text)

    def on_finished(self, success, message, folder):
        self.start_btn.setEnabled(True)
        self.status.setText(message)
        self.log.appendPlainText(message)
        if success:
            self.log.appendPlainText(f"Папка: {folder}")
            QMessageBox.information(self, "Готово", f"Обработка завершена.\nКлипы сохранены в:\n{folder}")
        else:
            QMessageBox.warning(self, "Не удалось завершить", message)

    def open_output(self):
        if self.video_path:
            folder = self.video_path.parent / "Shorts_AI_Studio_Clips"
            folder.mkdir(exist_ok=True)
            import os
            os.startfile(str(folder))
        else:
            QMessageBox.information(self, "Папка клипов", "Сначала выбери исходное видео.")
