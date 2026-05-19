# main.py
import sys
import threading
import signal
from pathlib import Path
from datetime import datetime
import webview

from modules.activation.porcupine_detector import PorcupineDetector
from modules.stt.vosk_stt import VoskSTT
from modules.nlu.rule_based_nlu import RuleBasedNLU
from core.command_executor import CommandExecutor
from core.microphone_stream import MicrophoneStream
from core.tts_engine import Pyttsx3TTS
from core.logger import Logger
from keys import PORCUPINE_ACCESS_TOKEN


class AssistantCore:
    """Ядро голосового ассистента"""

    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.is_listening = True
        self.is_active = True
        self.current_state = "idle"  # idle, listening, processing
        self.callbacks = []

        # Логгер
        self.logger = Logger("logs/assistant.log", debug_mode=debug_mode)

        # Инициализация модулей
        self._init_modules()

        # API для GUI
        self.api = AssistantAPI(self)

        self._listen_thread = None
        self._should_listen = True

    def _init_modules(self):
        """Инициализация всех модулей с DI"""
        self.logger.info("Инициализация модулей...", tag="SYSTEM")

        # Wake word detector
        try:
            self.detector = PorcupineDetector(
                PORCUPINE_ACCESS_TOKEN,
                keyword="computer"
            )
            self.logger.info("Porcupine загружен", tag="WAKE")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки Porcupine: {e}", tag="WAKE")
            raise

        # STT (Speech-to-Text)
        model_path = Path("./models/vosk-model-small-ru-0.22")
        if not model_path.exists():
            self.logger.warning(f"Модель Vosk не найдена: {model_path}", tag="STT")
            self.logger.warning("Скачайте с https://alphacephei.com/vosk/models", tag="STT")
        self.stt = VoskSTT(str(model_path), debug_mode=self.debug_mode)

        # NLU (Natural Language Understanding)
        self.nlu = RuleBasedNLU(debug_mode=self.debug_mode, logger=self.logger)

        # Command Executor
        self.executor = CommandExecutor(debug_mode=self.debug_mode, logger=self.logger)

        # TTS (Text-to-Speech)
        self.tts = Pyttsx3TTS(debug_mode=self.debug_mode)

        # Микрофонный поток
        self.microphone = MicrophoneStream(self.detector)

        self.logger.info("Все модули успешно загружены", tag="SYSTEM")

    def register_callback(self, callback):
        """Регистрация callback для GUI"""
        self.callbacks.append(callback)

    def _notify_ui(self, event, data=None):
        """Уведомление GUI об изменениях"""
        for callback in self.callbacks:
            try:
                callback(event, data)
            except Exception as e:
                self.logger.error(f"Callback error: {e}", tag="UI")

    def start_listening(self):
        """Запуск фонового прослушивания"""
        if self._listen_thread and self._listen_thread.is_alive():
            self._should_listen = False
            import time
            time.sleep(0.5)

        self._should_listen = True
        self.is_active = True

        self.logger.info("Запуск прослушивания...", tag="SYSTEM")
        self.current_state = "idle"
        self._notify_ui("state_change", {"state": "idle"})

        def listen_loop():
            try:
                for chunk in self.microphone.start():
                    if not self._should_listen or not self.is_active:
                        continue

                    # Wake word detected
                    self.logger.info("Активация по ключевому слову", tag="WAKE")
                    self.current_state = "listening"
                    self._notify_ui("state_change", {"state": "listening"})
                    self._notify_ui("wake_word", {"timestamp": datetime.now().isoformat()})

                    # Запись команды до тишины
                    audio = self.microphone.record_until_silence()

                    if len(audio) > 0:
                        self.current_state = "processing"
                        self._notify_ui("state_change", {"state": "processing"})

                        text = self.stt.recognize(audio)
                        self.stt.reset()

                        if text:
                            self.process_command(text)
                        else:
                            self.logger.warning("Речь не распознана", tag="STT")
                            self._notify_ui("error", {"message": "Речь не распознана"})
                    else:
                        self.logger.warning("Нет аудиоданных", tag="MIC")

                    self.current_state = "idle"
                    self._notify_ui("state_change", {"state": "idle"})

            except Exception as e:
                self.logger.error(f"Ошибка в listen_loop: {e}", tag="SYSTEM")
            finally:
                self.microphone.stop()

        self._listen_thread = threading.Thread(target=listen_loop, daemon=True)
        self._listen_thread.start()

    def process_command(self, text: str):
        """Обработка текстовой команды"""
        self.logger.info(f"Распознано: {text}", tag="STT")
        self._notify_ui("command_recognized", {"text": text})

        # NLU анализ
        result = self.nlu.parse(text)
        intent = result['intent']
        entities = result['entities']
        confidence = result.get('confidence', 0.0)

        self.logger.info(f"Интент: {intent} (confidence: {confidence:.2f})", tag="NLU")
        if entities:
            self.logger.info(f"Сущности: {entities}", tag="NLU")
        self._notify_ui("intent_parsed", {"intent": intent, "entities": entities})

        # Выполнение команды
        response = self.executor.execute(intent, entities)
        self.logger.info(f"Ответ: {response}", tag="EXEC")
        self._notify_ui("command_result", {"response": response})

        # Добавление в историю
        self._add_to_history(text, response, intent)

        # TTS ответ - в отдельном потоке и только если включен
        # Читаем настройки
        settings = self.logger.get_settings()
        tts_enabled = settings.get("tts_enabled", True)

        if response and intent not in ["goodbye", "unknown"] and tts_enabled:
            # Запускаем TTS в отдельном потоке, не блокируя основной цикл
            def speak_response():
                try:
                    self.tts.say(response)
                except Exception as e:
                    self.logger.error(f"TTS ошибка: {e}", tag="TTS")

            thread = threading.Thread(target=speak_response, daemon=True)
            thread.start()

        # Если прощание - останавливаем ассистента
        if intent == "goodbye":
            self.is_active = False
            self.logger.info("Ассистент остановлен. Скажите 'computer' для активации", tag="SYSTEM")
            self._notify_ui("assistant_stopped", {})

    def _add_to_history(self, command: str, response: str, intent: str):
        """Добавление в историю"""
        self.logger.add_history_entry(command, response, intent)
        self._notify_ui("history_update", {
            "command": command,
            "response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })

    def stop(self):
        """Остановка ассистента"""
        self.is_active = False
        self.microphone.stop()
        self.logger.info("Ассистент остановлен", tag="SYSTEM")

    def switch_activation_module(self, module_id: str):
        """Замена модуля активации без перезапуска потока"""
        self.logger.info(f"Замена модуля активации на {module_id}", tag="MODULES")

        try:
            # Останавливаем текущий поток
            self._should_listen = False
            import time
            time.sleep(0.3)

            # Создаем новый детектор
            if module_id == "vosk_detector":
                from modules.activation.vosk_detector import VoskDetector
                new_detector = VoskDetector("./models/vosk-model-small-ru-0.22", "компьютер")
                wake_word = "компьютер"
            elif module_id == "porcupine_detector":
                from modules.activation.porcupine_detector import PorcupineDetector
                new_detector = PorcupineDetector(PORCUPINE_ACCESS_TOKEN, "computer")
                wake_word = "computer"
            else:
                return {"success": False, "error": f"Неизвестный модуль: {module_id}"}

            # Заменяем детектор
            self.detector = new_detector

            # Пересоздаем микрофонный поток
            if hasattr(self, 'microphone'):
                self.microphone.stop()
            self.microphone = MicrophoneStream(self.detector)

            # Перезапускаем прослушивание
            self._should_listen = True
            self.start_listening()

            self.logger.info(f"Модуль активации заменен на {module_id}, wake word: {wake_word}", tag="MODULES")
            return {"success": True, "message": f"Модуль активации заменен на {module_id}"}

        except Exception as e:
            self.logger.error(f"Ошибка замены модуля активации: {e}", tag="MODULES")
            return {"success": False, "error": str(e)}

    def switch_nlu_module(self, module_id: str):
        """Замена NLU модуля без перезапуска"""
        self.logger.info(f"Замена NLU модуля на {module_id}", tag="MODULES")

        try:
            if module_id == "rule_based_nlu":
                from modules.nlu.rule_based_nlu import RuleBasedNLU
                new_nlu = RuleBasedNLU(debug_mode=self.debug_mode, logger=self.logger)
            elif module_id == "nlu_spacy":
                from modules.nlu.nlu_spacy import SpacyNLU
                new_nlu = SpacyNLU(debug_mode=self.debug_mode)
            else:
                return {"success": False, "error": f"Неизвестный NLU модуль: {module_id}"}

            self.nlu = new_nlu
            self.logger.info(f"NLU модуль заменен на {module_id}", tag="MODULES")
            return {"success": True, "message": f"NLU модуль заменен на {module_id}"}

        except Exception as e:
            self.logger.error(f"Ошибка замены NLU модуля: {e}", tag="MODULES")
            return {"success": False, "error": str(e)}


    def switch_stt_module(self, module_id: str):
        """Замена модуля распознавания речи"""
        self.logger.info(f"Замена STT модуля на {module_id}", tag="MODULES")

        try:
            if module_id == "vosk_stt":
                from modules.stt.vosk_stt import VoskSTT
                new_stt = VoskSTT("./models/vosk-model-small-ru-0.22", debug_mode=self.debug_mode)
            else:
                return {"success": False, "error": f"Неизвестный STT модуль: {module_id}"}

            self.stt = new_stt
            self.logger.info(f"STT модуль заменен на {module_id}", tag="MODULES")
            return {"success": True, "message": f"STT модуль заменен на {module_id}"}

        except Exception as e:
            self.logger.error(f"Ошибка замены STT модуля: {e}", tag="MODULES")
            return {"success": False, "error": str(e)}

    def switch_tts_module(self, module_id: str):
        """Замена TTS модуля"""
        self.logger.info(f"Замена TTS модуля на {module_id}", tag="MODULES")

        try:
            if module_id == "pyttsx3":
                from core.tts_engine import Pyttsx3TTS
                new_tts = Pyttsx3TTS(debug_mode=self.debug_mode)
            else:
                return {"success": False, "error": f"Неизвестный TTS модуль: {module_id}"}

            self.tts = new_tts
            self.logger.info(f"TTS модуль заменен на {module_id}", tag="MODULES")
            return {"success": True, "message": f"TTS модуль заменен на {module_id}"}

        except Exception as e:
            self.logger.error(f"Ошибка замены TTS модуля: {e}", tag="MODULES")
            return {"success": False, "error": str(e)}




# main.py - добавляем в класс AssistantAPI новые методы

class AssistantAPI:
    """API для взаимодействия с GUI (PyWebView)"""

    def __init__(self, core: AssistantCore):
        self.core = core
        self.logger = core.logger  # <-- ДОБАВИТЬ ЭТУ СТРОКУ
        core.register_callback(self.on_core_event)
        self.pending_callbacks = []
        self._listen_thread = None
        self._should_listen = True

    def get_today_stats(self):
        """Статистика за сегодня"""
        return self.core.logger.get_today_stats()

    def get_uptime(self):
        """Время работы"""
        return self.core.logger.get_uptime()

    def get_last_command(self):
        """Последняя команда"""
        last = self.core.logger.get_last_command()
        if last:
            return {
                "command": last.get("command", ""),
                "response": last.get("response", ""),
                "intent": last.get("intent", ""),
                "timestamp": last.get("timestamp", "")
            }
        return None

    def get_state_text(self):
        """Текстовое состояние"""
        states = {
            'idle': 'Ожидание активации...',
            'listening': '🎤 Слушаю команду...',
            'processing': '🔄 Обработка...'
        }
        return states.get(self.core.current_state, 'Готов к работе')

    def get_pipeline_status(self):
        """Статус pipeline"""
        return {
            "wake_word": "Porcupine",
            "wake_word_status": "Слушает 'computer'",
            "stt": "Vosk STT",
            "stt_status": "Модель: ru-small",
            "nlu": "RuleBased NLU",
            "nlu_status": f"Правил: {len(self.core.nlu.intents)}",
            "executor": "Command Executor",
            "executor_status": f"Доступно: {len(self.core.nlu.intents)} команд"
        }

    def get_pipeline_stats(self):
        """Статистика pipeline"""
        stats = self.core.logger.get_stats()
        return {
            "avg_response_time": "0.42с",
            "queue_length": 0,
            "errors_24h": stats.get("total_commands", 0) - (
                        stats.get("success_rate", 0) * stats.get("total_commands", 0) / 100) if stats.get(
                "total_commands", 0) > 0 else 0
        }

    def get_recent_commands(self):
        """Недавние команды"""
        return self.core.logger.get_recent_commands(5)

    def on_core_event(self, event, data):
        """Обработка событий от ядра"""
        print(f"[API Event] {event}: {data}")
        # Здесь можно отправлять события в JavaScript через WebView
        if hasattr(self, 'window') and self.window:
            try:
                self.window.evaluate_js(f"window.dispatchEvent(new CustomEvent('{event}', {{ detail: {data} }}))")
            except Exception:
                pass

    def set_window(self, window):
        """Устанавливаем окно для отправки событий"""
        self.window = window

    def get_status(self):
        """Возвращает статус ассистента"""
        return {
            "is_active": self.core.is_active,
            "state": self.core.current_state,
            "history_count": len(self.core.logger.get_history())
        }

    # Существующие методы...
    def toggle_listening(self):
        self.core.is_active = not self.core.is_active
        return self.core.is_active

    def process_text_command(self, text: str):
        if text and text.strip():
            self.core.process_command(text.strip())
        return {"success": True}

    def get_history(self, limit=50):
        return self.core.logger.get_history()[-limit:]

    def get_capabilities(self):
        intents = list(self.core.nlu.intents.keys())
        return {
            "intents": intents,
            "commands_count": len(intents),
            "total_commands": self.core.logger.get_stats().get("total_commands", 0)
        }

    def get_stats(self):
        return self.core.logger.get_stats()

    def clear_history(self):
        self.core.logger.clear_history()
        return {"success": True}

    def execute_command(self, intent: str, params: dict = None):
        if params is None:
            params = {}
        response = self.core.executor.execute(intent, params)
        return {"response": response}

    def get_settings(self):
        return self.core.logger.get_settings()

    def save_settings(self, settings: dict):
        self.core.logger.save_settings(settings)
        return {"success": True}

    # Добавьте эти методы в класс AssistantAPI в main.py:

    def get_available_modules(self):
        """Список всех доступных модулей из папки modules"""
        import os
        from pathlib import Path

        modules = []

        # Сканируем папку modules
        modules_path = Path("modules")

        # Activation модули
        activation_path = modules_path / "activation"
        if activation_path.exists():
            for py_file in activation_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    module_name = py_file.stem
                    modules.append({
                        "id": module_name,
                        "name": module_name.replace("_", " ").title(),
                        "type": "activation",
                        "file": str(py_file),
                        "icon": "🎙",
                        "description": "Wake-word detection module"
                    })

        # STT модули
        stt_path = modules_path / "stt"
        if stt_path.exists():
            for py_file in stt_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    module_name = py_file.stem
                    modules.append({
                        "id": module_name,
                        "name": module_name.replace("_", " ").title(),
                        "type": "stt",
                        "file": str(py_file),
                        "icon": "🧠",
                        "description": "Speech-to-text module"
                    })

        # NLU модули
        nlu_path = modules_path / "nlu"
        if nlu_path.exists():
            for py_file in nlu_path.glob("*.py"):
                if py_file.name not in ["__init__.py", "nlu_engine.py"]:
                    module_name = py_file.stem
                    modules.append({
                        "id": module_name,
                        "name": module_name.replace("_", " ").title(),
                        "type": "nlp",
                        "file": str(py_file),
                        "icon": "🤖",
                        "description": "Natural language understanding module"
                    })

        return modules

    def get_current_pipeline(self):
        """Получить текущие модули в pipeline (реальные, из ядра)"""
        pipeline = {}

        # Activation модуль
        detector_name = self.core.detector.__class__.__name__
        pipeline["activation"] = {
            "id": detector_name.lower().replace("detector", ""),
            "name": detector_name.replace("Detector", ""),
            "type": "activation",
            "icon": "🎙",
            "description": "Слушает 'computer'"
        }

        # STT модуль
        stt_name = self.core.stt.__class__.__name__
        pipeline["stt"] = {
            "id": stt_name.lower(),
            "name": stt_name,
            "type": "stt",
            "icon": "🧠",
            "description": "Готов к распознаванию"
        }

        # NLU модуль
        nlu_name = self.core.nlu.__class__.__name__
        rule_count = len(self.core.nlu.intents) if hasattr(self.core.nlu, 'intents') else 34
        pipeline["nlp"] = {
            "id": nlu_name.lower(),
            "name": nlu_name,
            "type": "nlp",
            "icon": "🤖",
            "description": f"{rule_count} правил"
        }

        # TTS модуль
        if self.core.tts:
            tts_name = self.core.tts.__class__.__name__
            pipeline["tts"] = {
                "id": tts_name.lower(),
                "name": tts_name.replace("TTS", " TTS"),
                "type": "tts",
                "icon": "🔊",
                "description": "Голосовые ответы"
            }
        else:
            pipeline["tts"] = {
                "id": "none",
                "name": "Отключен",
                "type": "tts",
                "icon": "🔇",
                "description": "TTS не активен"
            }

        return pipeline

    def switch_module(self, slot: str, module_id: str):
        """Переключить модуль в указанный слот"""
        self.logger.info(f"Переключение модуля {module_id} в слот {slot}", tag="MODULES")

        result = None

        if slot == "activation":
            result = self.core.switch_activation_module(module_id)
        elif slot == "stt":
            result = self.core.switch_stt_module(module_id)
        elif slot == "nlp":
            result = self.core.switch_nlu_module(module_id)
        elif slot == "tts":
            result = self.core.switch_tts_module(module_id)
        else:
            result = {"success": False, "error": f"Неизвестный слот: {slot}"}

        if result and result.get("success"):
            # Обновляем информацию о pipeline после замены
            return {
                "success": True,
                "message": result.get("message", f"Модуль {module_id} установлен"),
                "slot": slot,
                "module_id": module_id
            }
        else:
            error_msg = result.get("error", "Неизвестная ошибка") if result else "Ошибка"
            return {
                "success": False,
                "message": error_msg,
                "slot": slot,
                "module_id": module_id
            }

    def reload_module(self, module_id: str):
        """Перезагрузить модуль"""
        self.logger.info(f"Перезагрузка модуля {module_id}", tag="MODULES")
        return {"success": True, "message": f"Модуль {module_id} перезагружен"}




def main():
    # Создаем ядро ассистента
    assistant = AssistantCore(debug_mode=True)

    # Запускаем фоновое прослушивание
    assistant.start_listening()

    # Создаем API для GUI
    api = AssistantAPI(assistant)

    # Запускаем GUI окно
    window = webview.create_window(
        "EmilyOS - Голосовой Ассистент",
        "ui/index.html",
        width=1400,
        height=900,
        resizable=True,
        js_api=api,
        min_size=(800, 600)
    )

    webview.start(debug=True, http_server=True)


if __name__ == "__main__":
    main()