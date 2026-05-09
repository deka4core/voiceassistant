from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable


class NLUInterface(ABC):
    @abstractmethod
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Анализирует текст и возвращает структурированный результат

        Args:
            text: входной текст от пользователя

        Returns:
            Словарь с полями:
            - intent: название интента
            - entities: словарь извлеченных сущностей
            - confidence: уверенность (0-1)
            - raw_text: исходный текст
        """
        pass

    def add_intent(self, intent_name: str, patterns: list, handler: Optional[Callable] = None):
        """Опциональный метод. Не все реализации NLU его поддерживают."""
        pass

