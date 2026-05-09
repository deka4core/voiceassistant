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

    def callback(self, indata, frames, time, status):
        if status:
            print(f"Статус аудио: {status}")
        self.audio_queue.append(indata.copy())

    def start(self):
        self.is_running = True

        with sd.InputStream(callback=self.callback,
                            channels=1,
                            samplerate=self.detector.get_sample_rate(),
                            blocksize=self.detector.get_frame_size()):

            while self.is_running:
                if self.audio_queue:
                    chunk = self.audio_queue.pop(0)
                    if self.detector.detect(chunk):
                        yield chunk
                time.sleep(0.01)

    def record_until_silence(self):
        recorded = []
        silence_start = None
        start_time = time.time()

        while True:
            if self.audio_queue:
                chunk = self.audio_queue.pop(0)
                recorded.append(chunk)

                volume = np.sqrt(np.mean(chunk ** 2))

                if volume < self.silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= self.silence_duration:
                        break
                else:
                    silence_start = None

                if time.time() - start_time > 10:
                    break

            time.sleep(0.01)

        return np.concatenate(recorded) if recorded else np.array([])

    def stop(self):
        self.is_running = False