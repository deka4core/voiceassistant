# core/logger.py - ПОЛНОСТЬЮ ПЕРЕПИСАННАЯ ВЕРСИЯ БЕЗ РЕКУРСИИ
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import os


class Logger:
    def __init__(self, log_file: str = "logs/assistant.log", debug_mode=True):
        self.debug_mode = debug_mode
        self.log_dir = "logs"
        self.log_file_path = os.path.join(self.log_dir, "assistant.log")
        self.history_file_path = os.path.join(self.log_dir, "history.json")
        self.start_time = datetime.now()
        self._history = []

        # Создаем папку logs
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
        except Exception:
            pass

        self._load_history()
        self.info("Логгер инициализирован", tag="LOGGER")

    def _load_history(self):
        try:
            if os.path.exists(self.history_file_path):
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
        except Exception:
            self._history = []

    def _save_history(self):
        try:
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                # Сохраняем только последние 500 записей
                to_save = self._history[-500:] if len(self._history) > 500 else self._history
                json.dump(to_save, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _log(self, level: str, message: str, tag: str = "APP"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{tag}] [{level}] {message}"

        if self.debug_mode:
            print(log_entry)

        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception:
            pass

    def debug(self, message: str, tag: str = "APP"):
        self._log("DEBUG", message, tag)

    def info(self, message: str, tag: str = "APP"):
        self._log("INFO", message, tag)

    def warning(self, message: str, tag: str = "APP"):
        self._log("WARNING", message, tag)

    def error(self, message: str, tag: str = "APP"):
        self._log("ERROR", message, tag)

    def add_history_entry(self, command: str, response: str, intent: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "response": response,
            "intent": intent
        }
        self._history.append(entry)
        self._save_history()

    def get_history(self) -> List[Dict]:
        return self._history

    def clear_history(self):
        self._history = []
        self._save_history()
        self.info("История очищена", tag="LOGGER")

    def get_stats(self) -> Dict:
        total_commands = len(self._history)
        if total_commands == 0:
            return {
                "total_commands": 0,
                "success_rate": 0,
                "unique_intents": 0,
                "most_used": "none",
                "start_time": self.start_time.isoformat(),
                "uptime_seconds": 0
            }

        successful = 0
        intents_count = {}
        for entry in self._history:
            response = entry.get("response", "")
            if "не понял" not in response.lower():
                successful += 1

            intent = entry.get("intent", "unknown")
            intents_count[intent] = intents_count.get(intent, 0) + 1

        most_used = max(intents_count.items(), key=lambda x: x[1])[0] if intents_count else "none"
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())

        return {
            "total_commands": total_commands,
            "success_rate": round((successful / total_commands * 100), 1),
            "unique_intents": len(intents_count),
            "most_used": most_used,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": uptime_seconds
        }

    def get_today_stats(self) -> Dict:
        """Статистика за сегодня"""
        today = datetime.now().date()
        total_today = 0
        successful_today = 0

        for entry in self._history:
            try:
                entry_date = datetime.fromisoformat(entry.get("timestamp", "")).date()
                if entry_date == today:
                    total_today += 1
                    response = entry.get("response", "")
                    if "не понял" not in response.lower() and "не удалось" not in response.lower():
                        successful_today += 1
            except Exception:
                pass

        return {
            "total": total_today,
            "successful": successful_today,
            "failed": total_today - successful_today,
            "success_rate": round((successful_today / total_today * 100) if total_today > 0 else 0, 1)
        }

    def get_uptime(self) -> str:
        """Время работы в формате ЧЧч ММмин"""
        elapsed = datetime.now() - self.start_time
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        return f"{hours:02d}ч {minutes:02d}мин"

    def get_settings(self) -> Dict:
        settings_file = "config/settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "microphone_device": "default",
            "sensitivity": 0.01,
            "tts_enabled": True,
            "wake_word": "computer",
            "auto_start": False,
            "theme": "dark"
        }

    def save_settings(self, settings: Dict):
        settings_file = "config/settings.json"
        try:
            settings_dir = os.path.dirname(settings_file)
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.info("Настройки сохранены", tag="CONFIG")
        except Exception as e:
            self.error(f"Ошибка сохранения настроек: {e}", tag="CONFIG")

    def get_recent_commands(self, limit=5) -> List[Dict]:
        """Недавние команды с частотой использования"""
        command_count = {}
        for entry in self._history[-50:]:
            cmd = entry.get("command", "")
            if cmd:
                command_count[cmd] = command_count.get(cmd, 0) + 1

        sorted_commands = sorted(command_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"name": cmd, "count": count} for cmd, count in sorted_commands]

    def get_last_command(self) -> Dict:
        """Последняя выполненная команда"""
        if self._history:
            return self._history[-1]
        return None