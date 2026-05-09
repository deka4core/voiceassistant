from abc import ABC, abstractmethod
import numpy as np

class WakeWordDetector(ABC):
    @abstractmethod
    def detect(self, audio_chunk: np.ndarray) -> bool:
        pass

    @abstractmethod
    def get_sample_rate(self) -> int:
        pass

    @abstractmethod
    def get_frame_size(self) -> int:
        pass