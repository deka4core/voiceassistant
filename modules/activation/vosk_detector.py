import json
import numpy as np
from vosk import Model, KaldiRecognizer
from core.wake_word_detector import WakeWordDetector

class VoskDetector(WakeWordDetector):
    def __init__(self, model_path: str, keyword: str, sample_rate=16000):
        self.model = Model(model_path)
        self.keyword = keyword.lower()
        self._sample_rate = sample_rate
        self._frame_size = 1600
        self.audio_buffer = []
        self.buffer_target_size = int(sample_rate / self._frame_size)

    def detect(self, audio_chunk: np.ndarray) -> bool:
        self.audio_buffer.append(audio_chunk)

        if len(self.audio_buffer) > self.buffer_target_size:
            self.audio_buffer.pop(0)

        if len(self.audio_buffer) < self.buffer_target_size:
            return False

        audio = np.concatenate(self.audio_buffer)

        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        audio_int16 = (audio * 32767).astype(np.int16)

        rec = KaldiRecognizer(self.model, self._sample_rate)

        try:
            if rec.AcceptWaveform(audio_int16.tobytes()):
                result = json.loads(rec.Result())
                text = result.get('text', '').lower()
                if self.keyword in text:
                    return True

            partial = json.loads(rec.PartialResult())
            partial_text = partial.get('partial', '').lower()
            if self.keyword in partial_text:
                return True

        except Exception:
            pass

        return False

    def get_sample_rate(self) -> int:
        return self._sample_rate

    def get_frame_size(self) -> int:
        return self._frame_size