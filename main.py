from modules.activation.porcupine_detector import PorcupineDetector
from modules.stt.vosk_stt import VoskSTT
from modules.nlu.nlu_spacy import SpacyNLU
from core.command_executor import CommandExecutor
from core.microphone_stream import MicrophoneStream
from keys import PORCUPINE_ACCESS_TOKEN


def main():
    detector = PorcupineDetector(PORCUPINE_ACCESS_TOKEN, "computer")
    stt = VoskSTT("./models/vosk-model-small-ru-0.22", debug_mode=True)
    nlu = SpacyNLU(debug_mode=True)
    executor = CommandExecutor(debug_mode=True)
    stream = MicrophoneStream(detector)

    print("Скажите 'computer'...")

    try:
        for chunk in stream.start():
            print("\n🔊 Активация!")

            audio = stream.record_until_silence()

            if len(audio) > 0:
                text = stt.recognize(audio)
                stt.reset()

                if text:
                    print(f"📝 Распознано: {text}")

                    result = nlu.parse(text)
                    print(f"🎯 Интент: {result['intent']}")

                    if result['entities']:
                        print(f"📦 Сущности: {result['entities']}")

                    response = executor.execute(result['intent'], result['entities'])
                    print(f"💬 {response}")

                    if result['intent'] == 'goodbye':
                        break
                else:
                    print("❌ Речь не распознана")

            print("\nСлушаю...")

    except KeyboardInterrupt:
        print("\nОстановка...")
    finally:
        stream.stop()


if __name__ == "__main__":
    main()