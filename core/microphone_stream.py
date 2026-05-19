# core/microphone_stream.py - исправленный
import sounddevice as sd
import numpy as np
import time
from core.wake_word_detector import WakeWordDetector


class MicrophoneStream:
    def __init__(self, detector: WakeWordDetector, silence_threshold=0.01, silence_duration=2.0):
        self.detector = detector
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.audio_queue = []
        self.is_running = False
        self.stream = None

    def callback(self, indata, frames, time_info, status):
        if status:
            # Не выводим каждую ошибку, только важные
            if "input overflow" not in str(status):
                print(f"Статус аудио: {status}")
        self.audio_queue.append(indata.copy())

    def start(self):
        self.is_running = True

        self.stream = sd.InputStream(
            callback=self.callback,
            channels=1,
            samplerate=self.detector.get_sample_rate(),
            blocksize=self.detector.get_frame_size()
        )
        self.stream.start()

        try:
            while self.is_running:
                if self.audio_queue:
                    chunk = self.audio_queue.pop(0)
                    try:
                        if self.detector.detect(chunk):
                            yield chunk
                    except Exception as e:
                        print(f"Ошибка детекции: {e}")
                else:
                    time.sleep(0.05)  # Уменьшаем нагрузку на CPU
        except GeneratorExit:
            pass
        finally:
            self.stop()

    def record_until_silence(self, max_duration=10.0):
        recorded = []
        silence_start = None
        start_time = time.time()

        # Сбрасываем очередь перед записью команды
        time.sleep(0.1)

        while time.time() - start_time < max_duration:
            if self.audio_queue:
                chunk = self.audio_queue.pop(0)
                recorded.append(chunk)

                # Вычисляем громкость
                volume = np.sqrt(np.mean(chunk ** 2))

                if volume < self.silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= self.silence_duration:
                        break
                else:
                    silence_start = None
            else:
                time.sleep(0.02)

        if not recorded:
            return np.array([])

        return np.concatenate(recorded)

    def stop(self):
        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None