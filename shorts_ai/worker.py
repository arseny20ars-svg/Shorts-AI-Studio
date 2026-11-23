import os, re, shutil, subprocess
from pathlib import Path
from PySide6.QtCore import QThread, Signal

class ClipWorker(QThread):
    progress = Signal(int, str)
    message = Signal(str)
    clip_created = Signal(str)
    completed = Signal(bool, str, str)

    def __init__(self, video, outdir, count, duration, categories, subtitle_style):
        super().__init__()
        self.video = Path(video)
        self.outdir = Path(outdir)
        self.count = count
        self.duration = duration
        self.categories = categories
        self.subtitle_style = subtitle_style

    def run(self):
        try:
            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                raise RuntimeError("FFmpeg не найден. Установи FFmpeg и добавь его в PATH (инструкция в README).")
            self.outdir.mkdir(parents=True, exist_ok=True)
            self.progress.emit(5, "Проверяю видео…")
            total = self._duration(ffmpeg)
            if total <= 0:
                raise RuntimeError("Не удалось определить длительность видео.")
            self.message.emit(f"Видео: {self.video.name} · {total:.1f} сек.")
            self.progress.emit(15, "Анализирую речь и сцены…")
            segments = self._transcribe()
            candidates = self._choose_segments(segments, total)
            if not candidates:
                raise RuntimeError("Не удалось подобрать фрагменты.")
            self.progress.emit(35, "Подготавливаю вертикальные клипы…")
            for i, (start, end, caption) in enumerate(candidates, 1):
                target = self.outdir / f"short_{i:02d}.mp4"
                self._render(ffmpeg, start, end, target, caption)
                self.clip_created.emit(f"{target.name}  ({start:.1f}–{end:.1f} сек.)")
                self.message.emit(f"Создано: {target.name}")
                self.progress.emit(35 + int(60 * i / len(candidates)), f"Создаю клип {i}/{len(candidates)}…")
            self.progress.emit(100, "Готово!")
            self.completed.emit(True, f"Готово! Создано клипов: {len(candidates)}", str(self.outdir))
        except Exception as e:
            self.completed.emit(False, str(e), str(self.outdir))

    def _duration(self, ffmpeg):
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            raise RuntimeError("Не найден ffprobe. Установи полный пакет FFmpeg.")
        p = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(self.video)],
                           capture_output=True, text=True)
        return float(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip() else 0

    def _transcribe(self):
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(str(self.video), vad_filter=True)
            result = []
            for s in segments:
                result.append((float(s.start), float(s.end), s.text.strip()))
            self.message.emit(f"Распознана речь. Язык: {info.language}")
            return result
        except ImportError:
            self.message.emit("faster-whisper не установлен: использую равномерный подбор сцен без анализа диалогов.")
            return []
        except Exception as e:
            self.message.emit(f"Распознавание речи недоступно ({e}); использую резервный подбор сцен.")
            return []

    def _choose_segments(self, transcript, total):
        d = min(self.duration, max(8, total))
        max_start = max(0, total - d)
        # Score transcript windows with lightweight keyword heuristics. This is a first MVP,
        # not a semantic video-understanding model.
        windows = []
        if transcript:
            keywords = {
                "эмоцион": ["люблю", "ненавиж", "прости", "пожалуйста", "почему", "умер", "любовь"],
                "драм": ["умер", "убить", "прощай", "предал", "боль", "страшно"],
                "смеш": ["смешно", "ха-ха", "шутка", "дурак", "серьёзно"],
                "конфликт": ["нет", "заткнись", "ненавижу", "виноват", "предал"],
                "мотивац": ["можешь", "верь", "сила", "никогда не сдавайся", "мечта"],
            }
            for start, end, text in transcript:
                center = (start + end) / 2
                s = max(0, min(max_start, center - d / 2))
                lower = text.lower()
                score = min(len(text), 180) / 60
                for words in keywords.values():
                    score += sum(1.2 for w in words if w in lower)
                if self.categories:
                    # Keep broad dialogue candidates when user selected any category.
                    score += 0.3
                windows.append((score, s, min(total, s + d), text))
        if not windows:
            # Fallback: spread clips across the source rather than pretending to identify highlights.
            n = min(self.count, max(1, int(total // max(1, d))))
            if n == 1:
                starts = [max_start / 2]
            else:
                starts = [max_start * i / (n - 1) for i in range(n)]
            return [(s, min(total, s + d), "") for s in starts]
        windows.sort(reverse=True, key=lambda x: x[0])
        chosen = []
        for score, start, end, text in windows:
            if all(abs(start - old[0]) > d * 0.75 for old in chosen):
                chosen.append((start, end, text))
            if len(chosen) >= self.count:
                break
        if len(chosen) < self.count:
            for _, start, end, text in windows:
                if (start, end, text) not in chosen:
                    chosen.append((start, end, text))
                if len(chosen) >= self.count:
                    break
        chosen.sort(key=lambda x: x[0])
        return chosen[:self.count]

    def _render(self, ffmpeg, start, end, target, caption):
        vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        cmd = [ffmpeg, "-y", "-ss", f"{start:.3f}", "-i", str(self.video),
               "-t", f"{end-start:.3f}", "-vf", vf, "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "160k",
               "-movflags", "+faststart", str(target)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError("Ошибка FFmpeg: " + (p.stderr[-900:] if p.stderr else "неизвестная ошибка"))
