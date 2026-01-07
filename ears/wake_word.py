"""
Wake Word Detection Module
Uses openWakeWord for lightweight, always-on wake word detection
"""

import threading
import queue
import numpy as np
from openwakeword.model import Model
import sounddevice as sd


class WakeWordDetector:
    def __init__(self, wake_word="hey_jarvis", threshold=0.5, sample_rate=16000):
        """
        Initialize wake word detector

        Args:
            wake_word: Name of the wake word model
            threshold: Detection confidence threshold (0.0-1.0)
            sample_rate: Audio sample rate in Hz
        """
        self.wake_word = wake_word
        self.threshold = threshold                  
        
        self.sample_rate = sample_rate
        self.is_running = False
        self.detection_queue = queue.Queue()

        # Initialize the wake word model
        self.model = Model(
            wakeword_models=[wake_word],
            inference_framework="onnx"
        )

        # Audio buffer settings
        self.chunk_size = 1280  # 80ms at 16kHz
        self.audio_buffer = np.array([], dtype=np.int16)

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")

        # Convert to the format expected by openWakeWord
        audio_data = indata.copy().flatten()
        self.audio_buffer = np.concatenate([self.audio_buffer, audio_data])

        # Process in chunks
        while len(self.audio_buffer) >= self.chunk_size:
            chunk = self.audio_buffer[:self.chunk_size]
            self.audio_buffer = self.audio_buffer[self.chunk_size:]

            # Get predictions
            prediction = self.model.predict(chunk)

            # Check if wake word detected
            for key, score in prediction.items():
                if score >= self.threshold:
                    print(f"Wake word detected! Confidence: {score:.2f}")
                    self.detection_queue.put({"wake_word": key, "confidence": score})

    def start(self):
        """Start listening for wake word"""
        if self.is_running:
            print("Wake word detector already running")
            return

        self.is_running = True
        print(f"Listening for wake word: {self.wake_word}")

        # Start audio stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.int16,
            blocksize=self.chunk_size,
            callback=self.audio_callback
        )
        self.stream.start()

    def stop(self):
        """Stop listening for wake word"""
        if not self.is_running:
            return

        self.is_running = False
        self.stream.stop()
        self.stream.close()
        print("Wake word detector stopped")

    def wait_for_wake_word(self, timeout=None):
        """
        Block until wake word is detected

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            Detection result dict or None if timeout
        """
        try:
            return self.detection_queue.get(timeout=timeout)
        except queue.Empty:
            return None


if __name__ == "__main__":
    # Test the wake word detector
    detector = WakeWordDetector()
    detector.start()

    try:
        print("Waiting for wake word... (Press Ctrl+C to stop)")
        while True:
            detection = detector.wait_for_wake_word(timeout=1.0)
            if detection:
                print(f"Detected: {detection}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        detector.stop()
