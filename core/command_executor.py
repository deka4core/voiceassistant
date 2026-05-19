# core/command_executor.py - исправленная версия
import datetime
import os
import webbrowser
import subprocess
import platform
from pathlib import Path


class CommandExecutor:
    def __init__(self, debug_mode=True, logger=None):
        self.debug_mode = debug_mode
        self.logger = logger
        self.reminders = []
        self.notes = []

        # Простой маппинг без pymorphy3 (убираем проблемную библиотеку)
        self.apps = {
            "калькулятор": "calc.exe" if platform.system() == "Windows" else "gnome-calculator",
            "блокнот": "notepad.exe",
            "проводник": "explorer.exe",
            "браузер": None,
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "vscode": "code",
            "discord": "Discord",
            "telegram": "Telegram",
            "spotify": "Spotify",
            "steam": "steam.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
        }

    def _debug(self, message):
        if self.debug_mode:
            print(f"[Executor] {message}")
        if self.logger:
            self.logger.debug(message, tag="EXEC")

    def _normalize(self, text: str) -> str:
        """Простая нормализация без pymorphy3"""
        if not text:
            return ""
        return text.lower().strip()

    def execute(self, intent: str, entities: dict) -> str:
        self._debug(f"Выполнение интента: {intent}")

        # ========== ПРИВЕТСТВИЯ ==========
        if intent == "greeting":
            return "Привет! Чем могу помочь?"

        elif intent == "goodbye":
            return "До свидания! Хорошего дня!"

        # ========== ИНФОРМАЦИОННЫЕ ==========
        elif intent == "time":
            return f"Сейчас {datetime.datetime.now().strftime('%H:%M:%S')}"

        elif intent == "date":
            return f"Сегодня {datetime.datetime.now().strftime('%d.%m.%Y')}"

        # ========== УПРАВЛЕНИЕ ГРОМКОСТЬЮ ==========
        elif intent == "set_volume":
            level = entities.get('level', 50)
            try:
                if platform.system() == "Windows":
                    from ctypes import cast, POINTER
                    from comtypes import CLSCTX_ALL
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                    return f"Громкость установлена на {level}%"
                else:
                    os.system(f"pactl set-sink-volume @DEFAULT_SINK@ {level}%")
                    return f"Громкость установлена на {level}%"
            except Exception as e:
                self._debug(f"Ошибка установки громкости: {e}")
                return f"Не удалось изменить громкость"

        elif intent == "volume_up":
            try:
                if platform.system() == "Windows":
                    import pyautogui
                    pyautogui.press('volumeup', presses=5)
                else:
                    os.system("pactl set-sink-volume @DEFAULT_SINK@ +5%")
                return "Громкость увеличена"
            except Exception:
                return "Не удалось увеличить громкость"

        elif intent == "volume_down":
            try:
                if platform.system() == "Windows":
                    import pyautogui
                    pyautogui.press('volumedown', presses=5)
                else:
                    os.system("pactl set-sink-volume @DEFAULT_SINK@ -5%")
                return "Громкость уменьшена"
            except Exception:
                return "Не удалось уменьшить громкость"

        elif intent == "mute":
            try:
                if platform.system() == "Windows":
                    from ctypes import cast, POINTER
                    from comtypes import CLSCTX_ALL
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    volume.SetMute(1, None)
                else:
                    os.system("pactl set-sink-mute @DEFAULT_SINK@ toggle")
                return "Звук выключен"
            except Exception:
                return "Не удалось выключить звук"

        # ========== ПРИЛОЖЕНИЯ ==========
        elif intent == "open_app":
            # Получаем название приложения
            app_name = entities.get('name', '')
            if not app_name:
                app_name = entities.get('app_name', '')

            if not app_name:
                return "Что именно открыть?"

            normalized = app_name.lower().strip()

            # Поиск в маппинге
            for key, cmd in self.apps.items():
                if key in normalized or normalized in key:
                    if cmd is None:
                        webbrowser.open_new("about:blank")
                    else:
                        try:
                            if platform.system() == "Windows":
                                subprocess.Popen(cmd, shell=True)
                            else:
                                subprocess.Popen([cmd])
                        except Exception:
                            pass
                    return f"Открываю {key}"

            # Попытка открыть как команду
            try:
                if platform.system() == "Windows":
                    subprocess.Popen(app_name, shell=True)
                else:
                    subprocess.Popen([app_name])
                return f"Запускаю {app_name}"
            except Exception:
                return f"Не знаю, как открыть {app_name}"

        elif intent == "close_app":
            app_name = entities.get('name', '')
            if app_name:
                if platform.system() == "Windows":
                    os.system(f"taskkill /f /im {app_name}.exe")
                else:
                    os.system(f"pkill {app_name}")
                return f"Закрываю {app_name}"
            return "Что именно закрыть?"

        elif intent == "open_folder":
            folder = entities.get('name', '')
            if folder:
                try:
                    if platform.system() == "Windows":
                        os.startfile(folder)
                    else:
                        os.system(f"xdg-open '{folder}'")
                    return f"Открываю папку {folder}"
                except Exception:
                    pass
            # Открываем домашнюю папку
            home = str(Path.home())
            if platform.system() == "Windows":
                os.startfile(home)
            else:
                os.system(f"xdg-open '{home}'")
            return "Открываю домашнюю папку"

        # ========== ВЕБ ==========
        elif intent == "google_search":
            query = entities.get('query', '')
            if not query:
                query = entities.get('name', '')
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Ищу в Google: {query[:50]}..."
            return "Что искать?"

        elif intent == "wikipedia_search":
            query = entities.get('query', '')
            if query:
                webbrowser.open(f"https://ru.wikipedia.org/wiki/{query.replace(' ', '_')}")
                return f"Ищу в Википедии: {query[:50]}..."
            return "Что найти в Википедии?"

        elif intent == "open_url":
            url = entities.get('url', '')
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                webbrowser.open(url)
                return f"Открываю {url}"
            return "Какой сайт открыть?"

        # ========== МЕДИА ==========
        elif intent == "next_track":
            try:
                import pyautogui
                pyautogui.press('nexttrack')
                return "Следующий трек"
            except Exception:
                return "Не удалось переключить трек"

        elif intent == "prev_track":
            try:
                import pyautogui
                pyautogui.press('prevtrack')
                return "Предыдущий трек"
            except Exception:
                return "Не удалось переключить трек"

        elif intent == "play_pause":
            try:
                import pyautogui
                pyautogui.press('playpause')
                return "Пауза/Воспроизведение"
            except Exception:
                return "Не удалось"

        # ========== НАПОМИНАНИЯ ==========
        elif intent == "create_reminder":
            text = entities.get('text', '')
            if text:
                self.reminders.append({"text": text, "created": datetime.datetime.now()})
                return f"Напоминание создано: {text[:50]}..."
            return "Что напомнить?"

        elif intent == "what_reminders":
            if not self.reminders:
                return "У вас нет активных напоминаний"
            reminders_text = "\n".join([f"- {r['text'][:50]}" for r in self.reminders[-5:]])
            return f"Ваши напоминания:\n{reminders_text}"

        # ========== ЗАМЕТКИ ==========
        elif intent == "write_note":
            text = entities.get('text', '')
            if text:
                self.notes.append({"text": text, "created": datetime.datetime.now()})
                return f"Заметка сохранена: {text[:50]}..."
            return "Что записать?"

        elif intent == "read_notes":
            if not self.notes:
                return "У вас нет сохранённых заметок"
            notes_text = "\n".join([f"- {n['text'][:50]}" for n in self.notes[-5:]])
            return f"Ваши заметки:\n{notes_text}"

        # ========== СИСТЕМНЫЕ ==========
        elif intent == "lock_pc":
            if platform.system() == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
                return "Компьютер заблокирован"
            else:
                os.system("gnome-screensaver-command -l")
                return "Компьютер заблокирован"

        elif intent == "screenshot":
            try:
                import pyautogui
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_dir = Path.home() / "Pictures" / "Screenshots"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                path = screenshot_dir / f"screenshot_{timestamp}.png"
                pyautogui.screenshot(str(path))
                return f"Скриншот сохранён"
            except Exception as e:
                self._debug(f"Ошибка скриншота: {e}")
                return "Не удалось сделать скриншот"

        # ========== ПРОЧЕЕ ==========
        elif intent == "weather":
            city = entities.get('city', 'Москва')
            webbrowser.open(f"https://yandex.ru/pogoda/{city}")
            return f"Открываю прогноз погоды"

        elif intent == "capabilities":
            apps_list = ", ".join(list(self.apps.keys())[:10])
            return f"Я умею:\n- Открывать: {apps_list}\n- Показывать время и дату\n- Управлять громкостью\n- Делать скриншоты\n- Искать в интернете\n- Создавать напоминания и заметки\n- Блокировать компьютер"

        elif intent == "how_are_you":
            return "Всё отлично! Работаю в штатном режиме."

        elif intent == "thanks":
            return "Пожалуйста! Обращайтесь ещё."

        elif intent == "help":
            return "Скажите 'что ты умеешь', чтобы увидеть список команд."

        elif intent == "unknown":
            return "Извините, я не понял команду. Скажите 'что ты умеешь' для списка команд."

        else:
            return f"Команда '{intent}' распознана, но не реализована"