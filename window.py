import webview


class Api:
    def __init__(self, window):
        self.window = window
        self.assistant_running = True  # начальное состояние

    def toggle_assistant(self, current_state):
        """Переключает состояние ассистента"""
        print(f"[Python] Получен запрос на изменение состояния: {current_state}")

        # Меняем состояние
        self.assistant_running = not self.assistant_running

        # Здесь можно добавить реальную логику:
        if self.assistant_running:
            print("[Python] ▶️ Ассистент запущен")
            # Запустить прослушивание микрофона и т.д.
        else:
            print("[Python] ⏸️ Ассистент остановлен")
            # Остановить распознавание речи и т.д.

        # Возвращаем новое состояние в JavaScript
        return self.assistant_running

    def get_assistant_state(self):
        """Возвращает текущее состояние"""
        return self.assistant_running


def main():
    # Создаем окно с API
    window = webview.create_window(
        "EmilyOS - Голосовой Ассистент",
        "ui/index.html",
        width=1400,
        height=900,
        resizable=True
    )

    # Создаем экземпляр API и передаем в него window
    api = Api(window)
    window.evaluate_js = window.load_url  # для совместимости

    # Запускаем приложение
    webview.start(debug=True)  # debug=True для консоли разработчика


if __name__ == "__main__":
    main()