import datetime
import os
import webbrowser
import pymorphy3


class CommandExecutor:
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.morph = pymorphy3.MorphAnalyzer()

        self.apps = {
            "калькулятор": ("калькулятор", "calc"),
            "блокнот": ("блокнот", "notepad"),
            "проводник": ("проводник", "explorer"),
            "браузер": ("браузер", None),
        }

    def _debug(self, message):
        if self.debug_mode:
            print(f"[Executor] {message}")

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        try:
            parsed = self.morph.parse(text.split()[0])[0]
            return parsed.normal_form
        except Exception as e:
            self._debug(f"Ошибка нормализации: {e}")
            return text.lower()

    def execute(self, intent: str, entities: dict) -> str:
        if intent == "greeting":
            return "Привет! Чем могу помочь?"

        elif intent == "how_are_you":
            return "Всё отлично! Готова выполнять команды."

        elif intent == "thanks":
            return "Пожалуйста! Обращайтесь ещё."

        elif intent == "time":
            return f"Сейчас {datetime.datetime.now().strftime('%H:%M:%S')}"

        elif intent == "date":
            return f"Сегодня {datetime.datetime.now().strftime('%d.%m.%Y')}"

        elif intent == "open_app":
            app_name = entities.get('app_name', '')
            normalized = self._normalize(app_name)

            if normalized in self.apps:
                name, cmd = self.apps[normalized]
                if cmd:
                    os.system(cmd)
                else:
                    webbrowser.open_new("about:blank")
                return f"Открываю {name}"
            else:
                return f"Не знаю, как открыть {app_name}"

        elif intent == "capabilities":
            return "Я умею: показывать время и дату, открывать калькулятор, блокнот, проводник и браузер."

        elif intent == "goodbye":
            return "До свидания!"

        else:
            return "Извините, я не понял команду."