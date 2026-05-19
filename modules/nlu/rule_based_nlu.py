# modules/nlu/rule_based_nlu.py
import re
from typing import Dict, Any, Optional, Callable
from core.nlu_engine import NLUInterface


class RuleBasedNLU(NLUInterface):
    def __init__(self, debug_mode=True, logger=None):
        self.debug_mode = debug_mode
        self.logger = logger
        self.intents = {}
        self._init_default_intents()

    def _debug(self, message: str):
        if self.debug_mode:
            print(f"[NLU] {message}")
        if self.logger:
            self.logger.debug(message, tag="NLU")

    def _init_default_intents(self):
        """Инициализация 25+ интентов по ТЗ"""

        # ========== ПРИВЕТСТВИЯ И ПРОЩАНИЯ ==========
        self.add_intent("greeting", [
            r"привет",
            r"здравствуй",
            r"добрый день",
            r"доброе утро",
            r"добрый вечер",
            r"здравствуйте",
            r"приветствую"
        ])

        self.add_intent("goodbye", [
            r"пока",
            r"до свидания",
            r"всего хорошего",
            r"выход",
            r"завершить",
            r"остановись",
            r"выйти"
        ])

        # ========== ИНФОРМАЦИОННЫЕ ==========
        self.add_intent("time", [
            r"который час",
            r"сколько время",
            r"какое время",
            r"текущее время",
            r"покажи время"
        ])

        self.add_intent("date", [
            r"какая дата",
            r"какое сегодня число",
            r"текущая дата",
            r"какой сегодня день",
            r"сегодняшняя дата"
        ])

        # ========== УПРАВЛЕНИЕ ГРОМКОСТЬЮ ==========
        self.add_intent("set_volume", [
            r"установи громкость на (\d+)",
            r"сделай громкость (\d+)",
            r"поставь громкость (\d+)",
            r"громкость (\d+)",
            r"установи уровень громкости (\d+)"
        ])

        self.add_intent("volume_up", [
            r"увеличь громкость",
            r"сделай громче",
            r"прибавь звук",
            r"громче"
        ])

        self.add_intent("volume_down", [
            r"уменьши громкость",
            r"сделай тише",
            r"убавь звук",
            r"тише"
        ])

        self.add_intent("mute", [
            r"выключи звук",
            r"без звука",
            r"отключи звук",
            r"заглуши",
            r"mute"
        ])

        # ========== ЗАПУСК ПРИЛОЖЕНИЙ ==========
        self.add_intent("open_app", [
            r"открой\s+(.+)",
            r"запусти\s+(.+)",
            r"открыть\s+(.+)",
            r"запустить\s+(.+)",
            r"включи\s+(.+)"
        ])

        self.add_intent("close_app", [
            r"закрой\s+(.+)",
            r"заверши\s+(.+)",
            r"закрыть\s+(.+)",
            r"выйди из\s+(.+)"
        ])

        self.add_intent("switch_to_app", [
            r"переключись на\s+(.+)",
            r"перейди в\s+(.+)",
            r"открой окно\s+(.+)"
        ])

        self.add_intent("open_folder", [
            r"открой папку\s+(.+)",
            r"покажи папку\s+(.+)"
        ])

        # ========== ВЕБ-ФУНКЦИОНАЛЬНОСТЬ ==========
        self.add_intent("google_search", [
            r"найди в гугле\s+(.+)",
            r"поищи в интернете\s+(.+)",
            r"google найди\s+(.+)",
            r"что такое\s+(.+)",
            r"кто такой\s+(.+)"
        ])

        self.add_intent("wikipedia_search", [
            r"найди в википедии\s+(.+)",
            r"википедия\s+(.+)",
            r"что говорит википедия о\s+(.+)"
        ])

        self.add_intent("open_url", [
            r"открой сайт\s+(.+)",
            r"перейди на\s+(.+)",
            r"зайди на\s+(.+)",
            r"открой ссылку\s+(.+)"
        ])

        # ========== МЕДИА ==========
        self.add_intent("next_track", [
            r"следующий трек",
            r"следующая песня",
            r"дальше",
            r"следующий"
        ])

        self.add_intent("prev_track", [
            r"предыдущий трек",
            r"предыдущая песня",
            r"назад"
        ])

        self.add_intent("play_pause", [
            r"пауза",
            r"останови",
            r"продолжи",
            r"играть",
            r"плей",
            r"play"
        ])

        # ========== УТИЛИТЫ ==========
        self.add_intent("create_reminder", [
            r"напомни\s+(.+)",
            r"создай напоминание\s+(.+)",
            r"запомни\s+(.+)"
        ])

        self.add_intent("what_reminders", [
            r"какие напоминания",
            r"что я просил запомнить",
            r"покажи напоминания"
        ])

        self.add_intent("write_note", [
            r"запиши\s+(.+)",
            r"сохрани заметку\s+(.+)",
            r"сделай запись\s+(.+)"
        ])

        self.add_intent("read_notes", [
            r"прочитай заметки",
            r"покажи заметки",
            r"что я записывал"
        ])

        # ========== СИСТЕМНЫЕ КОМАНДЫ ==========
        self.add_intent("lock_pc", [
            r"заблокируй компьютер",
            r"заблокируй экран",
            r"залочи пк"
        ])

        self.add_intent("shutdown", [
            r"выключи компьютер",
            r"выключи пк",
            r"заверши работу",
            r"выключение"
        ])

        self.add_intent("screenshot", [
            r"сделай скриншот",
            r"скриншот",
            r"сфоткай экран"
        ])

        self.add_intent("restart", [
            r"перезагрузи компьютер",
            r"перезагрузка",
            r"рестарт"
        ])

        # ========== НАСТРОЙКИ АССИСТЕНТА ==========
        self.add_intent("toggle_voice_response", [
            r"выключи голос",
            r"включи голос",
            r"отключи голосовые ответы",
            r"голосовые ответы"
        ])

        self.add_intent("set_sensitivity", [
            r"установи чувствительность на (\d+)",
            r"измени чувствительность",
            r"настрой микрофон"
        ])

        # ========== ДОПОЛНИТЕЛЬНЫЕ ==========
        self.add_intent("weather", [
            r"погода\s+(?:в\s+)?(.+)",
            r"какая погода",
            r"сколько градусов"
        ])

        self.add_intent("holiday", [
            r"какой сегодня праздник",
            r"сегодня праздник",
            r"праздники сегодня"
        ])

        self.add_intent("capabilities", [
            r"что ты умеешь",
            r"какие команды",
            r"что ты можешь",
            r"список команд",
            r"твои возможности"
        ])

        self.add_intent("how_are_you", [
            r"как дела",
            r"как ты",
            r"как настроение",
            r"как жизнь",
            r"как самочувствие"
        ])

        self.add_intent("thanks", [
            r"спасибо",
            r"благодарю",
            r"спс"
        ])

        self.add_intent("help", [
            r"помощь",
            r"help",
            r"что делать",
            r"подскажи"
        ])

        self._debug(f"Инициализировано {len(self.intents)} интентов")

    def add_intent(self, intent_name: str, patterns: list, handler: Optional[Callable] = None):
        self.intents[intent_name] = {
            'patterns': [re.compile(p, re.IGNORECASE) for p in patterns],
            'handler': handler
        }

    def parse(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower().strip()

        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data['patterns']:
                match = pattern.search(text_lower)
                if match:
                    entities = self._extract_entities(intent_name, match, text_lower)
                    result = {
                        'intent': intent_name,
                        'entities': entities,
                        'confidence': 1.0,
                        'raw_text': text
                    }
                    self._debug(f"Распознан интент: {intent_name}, сущности: {entities}")
                    return result

        return {
            'intent': 'unknown',
            'entities': {},
            'confidence': 0.0,
            'raw_text': text
        }

    def _extract_entities(self, intent_name: str, match, text: str) -> Dict[str, Any]:
        entities = {}

        # Извлечение параметра из команд с числами
        if intent_name in ["set_volume", "set_sensitivity"]:
            if match.groups():
                try:
                    value = int(match.group(1))
                    if intent_name == "set_volume":
                        entities['level'] = min(100, max(0, value))
                except ValueError:
                    pass

        # Извлечение текстовых параметров
        elif intent_name in ["open_app", "close_app", "switch_to_app", "open_folder"]:
            if match.groups():
                entities['name'] = match.group(1).strip()

        elif intent_name in ["google_search", "wikipedia_search"]:
            if match.groups():
                entities['query'] = match.group(1).strip()

        elif intent_name in ["open_url"]:
            if match.groups():
                entities['url'] = match.group(1).strip()

        elif intent_name in ["create_reminder", "write_note"]:
            if match.groups():
                entities['text'] = match.group(1).strip()

        elif intent_name == "weather":
            if match.groups() and match.group(1):
                entities['city'] = match.group(1).strip()

        return entities

    def get_handler(self, intent_name: str) -> Optional[Callable]:
        if intent_name in self.intents:
            return self.intents[intent_name]['handler']
        return None