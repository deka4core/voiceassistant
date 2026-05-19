# window.py - альтернативная версия
import webview
from main import AssistantCore, AssistantAPI


class WebViewApi:
    """Обертка для API, чтобы гарантировать его доступность"""

    def __init__(self, core):
        self.core = core
        self.api = AssistantAPI(core)

    def get_status(self):
        return self.api.get_status()

    def get_today_stats(self):
        return self.api.get_today_stats()

    def get_uptime(self):
        return self.api.get_uptime()

    def get_last_command(self):
        return self.api.get_last_command()

    def get_state_text(self):
        return self.api.get_state_text()

    def get_pipeline_status(self):
        return self.api.get_pipeline_status()

    def get_pipeline_stats(self):
        return self.api.get_pipeline_stats()

    def get_recent_commands(self):
        return self.api.get_recent_commands()

    def toggle_listening(self):
        return self.api.toggle_listening()

    def process_text_command(self, text):
        return self.api.process_text_command(text)

    def get_history(self, limit=50):
        return self.api.get_history(limit)

    def get_capabilities(self):
        return self.api.get_capabilities()

    def get_stats(self):
        return self.api.get_stats()

    def clear_history(self):
        return self.api.clear_history()

    def execute_command(self, intent, params=None):
        return self.api.execute_command(intent, params)

    def get_settings(self):
        return self.api.get_settings()

    def save_settings(self, settings):
        return self.api.save_settings(settings)


def main():
    assistant = AssistantCore(debug_mode=True)
    assistant.start_listening()

    # Создаем обертку для API
    api_wrapper = AssistantAPI(assistant)

    window = webview.create_window(
        title="EmilyOS - Голосовой Ассистент",
        url="ui/index.html",
        width=1400,
        height=900,
        resizable=True,
        js_api=api_wrapper,
        min_size=(800, 600)
    )

    webview.start(debug=True, http_server=True)


if __name__ == "__main__":
    main()