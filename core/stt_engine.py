from abc import ABC, abstractmethod
import numpy as np


class STTInterface(ABC):
    @abstractmethod
    def recognize(self, audio_data: np.ndarray) -> str:
        """
        Распознает речь из аудиоданных

        Args:
            audio_data: аудиоданные в формате numpy array (float32 или int16)

        Returns:
            распознанный текст или пустая строка
        """
        pass

    @abstractmethod
    def reset(self):
        """Сбрасывает состояние распознавателя (между командами)"""
        pass

    @abstractmethod
    def get_sample_rate(self) -> int:
        """Возвращает требуемую частоту дискретизации"""
        pass