import re
from typing import Dict, Any, Optional, Callable
from core.nlu_engine import NLUInterface


class RuleBasedNLU(NLUInterface):
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.intents = {}  # intent_name -> {'patterns': [], 'handler': callable}
        self._init_default_intents()

    def _debug(self, message: str):
        if self.debug_mode:
            print(f"[NLU] {message}")

    def _init_default_intents(self):
        """Инициализация стандартных интентов"""

        # Простые приветствия
        self.add_intent("greeting", [
            r"привет",
            r"здравствуй",
            r"добрый день",
            r"доброе утро",
            r"добрый вечер"
        ])

        # Вопросы о состоянии
        self.add_intent("how_are_you", [
            r"как дела",
            r"как ты",
            r"как настроение",
            r"как жизнь"
        ])

        # Благодарности
        self.add_intent("thanks", [
            r"спасибо",
            r"благодарю"
        ])

        # Время и дата
        self.add_intent("time", [
            r"который час",
            r"сколько время",
            r"какое время",
            r"текущее время"
        ])

        self.add_intent("date", [
            r"какая дата",
            r"какое сегодня число",
            r"текущая дата"
        ])

        # Открытие приложений (с сущностями)
        self.add_intent("open_app", [
            r"открой\s+(.+)",
            r"запусти\s+(.+)",
            r"открыть\s+(.+)"
        ])

        # Системные команды
        self.add_intent("restart", [
            r"перезагрузи",
            r"перезагрузка"
        ])

        self.add_intent("shutdown", [
            r"выключи",
            r"выключение"
        ])

        # Поиск в интернете
        self.add_intent("search", [
            r"найди\s+(.+)",
            r"поищи\s+(.+)",
            r"поискать\s+(.+)",
            r"что такое\s+(.+)",
            r"кто такой\s+(.+)"
        ])

        # Открытие сайтов
        self.add_intent("open_website", [
            r"открой\s+сайт\s+(.+)",
            r"перейди\s+на\s+(.+)",
            r"зайди\s+на\s+(.+)"
        ])

        # Вопросы о возможностях
        self.add_intent("capabilities", [
            r"что ты умеешь",
            r"какие команды",
            r"что ты можешь"
        ])

        # Прощания
        self.add_intent("goodbye", [
            r"пока",
            r"до свидания",
            r"всего хорошего",
            r"выход"
        ])

    def add_intent(self, intent_name: str, patterns: list, handler: Optional[Callable] = None):
        self.intents[intent_name] = {
            'patterns': [re.compile(p, re.IGNORECASE) for p in patterns],
            'handler': handler
        }
        self._debug(f"Добавлен интент: {intent_name} с {len(patterns)} шаблонами")

    def parse(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower().strip()

        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data['patterns']:
                match = pattern.search(text_lower)
                if match:
                    # Извлекаем сущности
                    entities = self._extract_entities(intent_name, match, text_lower)

                    result = {
                        'intent': intent_name,
                        'entities': entities,
                        'confidence': 1.0,
                        'raw_text': text
                    }

                    self._debug(f"Распознан интент: {intent_name}, сущности: {entities}")
                    return result

        # Интент не найден
        return {
            'intent': 'unknown',
            'entities': {},
            'confidence': 0.0,
            'raw_text': text
        }

    def _extract_entities(self, intent_name: str, match, text: str) -> Dict[str, Any]:
        """Извлекает сущности из совпадения"""
        entities = {}

        if intent_name == "open_app":
            # Извлекаем название приложения
            app_name = match.group(1) if match.groups() else None
            if app_name:
                entities['app_name'] = app_name

                # Нормализация названий
                app_mapping = {
                    'блокнот': 'notepad',
                    'калькулятор': 'calculator',
                    'проводник': 'explorer',
                    'браузер': 'browser'
                }

                for ru_name, en_name in app_mapping.items():
                    if ru_name in app_name:
                        entities['app_key'] = en_name
                        break

        elif intent_name == "search":
            query = match.group(1) if match.groups() else None
            if query:
                entities['query'] = query

        elif intent_name == "open_website":
            site = match.group(1) if match.groups() else None
            if site:
                entities['site'] = site

        return entities

    def get_handler(self, intent_name: str) -> Optional[Callable]:
        """Возвращает обработчик для интента"""
        if intent_name in self.intents:
            return self.intents[intent_name]['handler']
        return None