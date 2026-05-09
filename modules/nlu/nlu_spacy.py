import spacy
from core.nlu_engine import NLUInterface


class SpacyNLU(NLUInterface):
    def __init__(self, debug_mode=True):
        self.nlp = spacy.load("ru_core_news_sm")
        self.debug_mode = debug_mode

        # Словари ключевых слов для каждого интента
        self.intent_keywords = {
            "open_app": ["открыть", "открой", "запустить", "запусти", "открытие", "открывать"],
            "time": ["время", "часы", "сколько время", "который час"],
            "date": ["дата", "число", "сегодня число", "какое сегодня"],
            "greeting": ["привет", "здравствуй", "добрый день", "доброе утро"],
            "goodbye": ["пока", "до свидания", "выход", "завершить"],
            "capabilities": ["умеешь", "можешь", "команды", "функции"]
        }

    def _debug(self, message):
        if self.debug_mode:
            print(f"[spaCy-NLU] {message}")

    def add_intent(self, intent_name: str, patterns: list, handler=None):
        pass

    def parse(self, text: str):
        text_lower = text.lower()
        doc = self.nlp(text_lower)

        intent = "unknown"
        entities = {}

        # 1. Сначала проверяем по ключевым словам (быстро и надежно)
        for intent_name, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    intent = intent_name
                    break
            if intent != "unknown":
                break

        # 2. Если не нашли по ключевым словам, пробуем грамматический анализ
        if intent == "unknown":
            for token in doc:
                if token.dep_ == "ROOT":
                    lemma = token.lemma_
                    if lemma in ["открыть", "запустить", "открывать"]:
                        intent = "open_app"
                        break

        # 3. Извлекаем сущности для open_app
        if intent == "open_app":
            # Ищем объект действия (кого? что?)
            for token in doc:
                if token.dep_ in ["dobj", "nsubj"]:
                    entities['app_name'] = token.text
                    break

            # Если не нашли, берем последнее значимое слово
            if not entities:
                for token in doc:
                    if token.pos_ in ["NOUN"]:
                        entities['app_name'] = token.text

        self._debug(f"Интент: {intent}, Сущности: {entities}")

        return {
            'intent': intent,
            'entities': entities,
            'confidence': 1.0,
            'raw_text': text
        }

    def get_handler(self, intent_name: str):
        return None