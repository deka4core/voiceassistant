import pvporcupine
import numpy as np
from core.wake_word_detector import WakeWordDetector

class PorcupineDetector(WakeWordDetector):
    def __init__(self, access_key: str, keyword: str = "computer"):
        self.engine = pvporcupine.create(
            access_key=access_key,
            keywords=[keyword]
        )

    def detect(self, audio_chunk: np.ndarray) -> bool:
        if len(audio_chunk.shape) > 1:
            audio_chunk = audio_chunk.flatten()

        if np.max(np.abs(audio_chunk)) > 0:
            audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))

        pcm = (audio_chunk * 32767).astype(np.int16)

        if len(pcm) < self.engine.frame_length:
            pcm = np.pad(pcm, (0, self.engine.frame_length - len(pcm)))
        else:
            pcm = pcm[:self.engine.frame_length]

        return self.engine.process(pcm) >= 0

    def get_sample_rate(self) -> int:
        return self.engine.sample_rate

    def get_frame_size(self) -> int:
        return self.engine.frame_length

    def __del__(self):
        self.engine.delete()