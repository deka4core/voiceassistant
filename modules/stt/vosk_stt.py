import json
import os
import numpy as np
from vosk import Model, KaldiRecognizer
from core.stt_engine import STTInterface


class VoskSTT(STTInterface):
    def __init__(self, model_path: str, sample_rate=16000, debug_mode=True):
        self.debug_mode = debug_mode
        self.sample_rate = sample_rate
        self.model = None
        self.recognizer = None

        self._load_model(model_path)

    def _load_model(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель Vosk не найдена: {model_path}")

        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.recognizer.SetWords(True)
        self._debug(f"Модель загружена: {model_path}")

    def _debug(self, message: str):
        if self.debug_mode:
            print(f"[Vosk-STT] {message}")

    def recognize(self, audio_data: np.ndarray) -> str:
        if self.recognizer is None:
            return ""

        # Конвертируем в int16 если нужно
        if audio_data.dtype in (np.float32, np.float64):
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            audio_int16 = (audio_data * 32767).astype(np.int16)
        else:
            audio_int16 = audio_data.astype(np.int16)

        self.recognizer.AcceptWaveform(audio_int16.tobytes())
        result = json.loads(self.recognizer.FinalResult())
        text = result.get("text", "").strip()

        if text:
            self._debug(f"Распознано: '{text}'")

        return text

    def reset(self):
        if self.recognizer:
            self.recognizer.Reset()
            self._debug("Сброшен")

    def get_sample_rate(self) -> int:
        return self.sample_rate