# core/tts_engine.py - исправленная версия (работает многократно)
import threading
import pyttsx3
from abc import ABC, abstractmethod


class TTSInterface(ABC):
    @abstractmethod
    def say(self, text: str):
        pass


class Pyttsx3TTS(TTSInterface):
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self._lock = threading.Lock()

    def _create_engine(self):
        """Создает новый TTS движок для каждого воспроизведения"""
        try:
            engine = pyttsx3.init(driverName=None, debug=False)

            # Настройка голоса (русский)
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'russian' in voice.name.lower() or 'русский' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break

            engine.setProperty('rate', 180)  # Скорость речи
            engine.setProperty('volume', 0.9)  # Громкость

            return engine
        except Exception as e:
            if self.debug_mode:
                print(f"[TTS] Ошибка создания движка: {e}")
            return None

    def say(self, text: str):
        """Произносит текст в отдельном потоке"""
        if not text:
            return

        def speak():
            with self._lock:
                try:
                    # Создаем новый движок для каждого воспроизведения
                    engine = self._create_engine()
                    if engine:
                        engine.say(text)
                        engine.runAndWait()
                        engine.stop()  # Останавливаем движок после использования

                        if self.debug_mode:
                            print(f"[TTS] Произнесено: {text[:50]}...")
                    else:
                        if self.debug_mode:
                            print(f"[TTS] Не удалось создать движок")
                except Exception as e:
                    if self.debug_mode:
                        print(f"[TTS] Ошибка: {e}")

        thread = threading.Thread(target=speak, daemon=True)
        thread.start()