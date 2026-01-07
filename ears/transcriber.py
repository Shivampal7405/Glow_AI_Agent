"""
Speech-to-Text Transcription Module
Uses Faster-Whisper for high-speed, offline transcription
"""

import sounddevice as sd
import numpy as np
import queue
import threading
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(
        self,
        model_size="base",
        device="auto",
        compute_type="int8",
        sample_rate=16000,
        silence_threshold=0.01,
        silence_duration=1.5
    ):
        """
        Initialize the transcriber

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda, auto)
            compute_type: Computation type (int8, float16, float32)
            sample_rate: Audio sample rate in Hz
            silence_threshold: RMS threshold to detect silence
            silence_duration: Seconds of silence before stopping recording
        """
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

        print(f"Loading Whisper model: {model_size}")
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        print("Whisper model loaded successfully")

        self.audio_queue = queue.Queue()
        self.is_recording = False

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream during recording"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())

    def record_audio(self, max_duration=30):
        """
        Record audio until silence is detected or max duration reached

        Args:
            max_duration: Maximum recording duration in seconds

        Returns:
            Recorded audio as numpy array
        """
        print("Recording... (speak now)")
        self.is_recording = True
        self.audio_queue = queue.Queue()

        audio_data = []
        silence_chunks = 0
        silence_chunks_needed = int(self.silence_duration * self.sample_rate / 1024)

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            blocksize=1024,
            callback=self.audio_callback
        ):
            total_chunks = 0
            max_chunks = int(max_duration * self.sample_rate / 1024)

            while self.is_recording and total_chunks < max_chunks:
                try:
                    chunk = self.audio_queue.get(timeout=0.1)
                    audio_data.append(chunk)
                    total_chunks += 1

                    # Check for silence
                    rms = np.sqrt(np.mean(chunk**2))
                    if rms < self.silence_threshold:
                        silence_chunks += 1
                        if silence_chunks >= silence_chunks_needed:
                            print("Silence detected, stopping recording")
                            break
                    else:
                        silence_chunks = 0

                except queue.Empty:
                    continue

        self.is_recording = False

        if not audio_data:
            return None

        # Concatenate all chunks
        audio_array = np.concatenate(audio_data, axis=0).flatten()
        print(f"Recording complete ({len(audio_array) / self.sample_rate:.2f}s)")

        return audio_array

    def transcribe(self, audio_data):
        """
        Transcribe audio data to text

        Args:
            audio_data: Numpy array of audio samples

        Returns:
            Transcribed text string
        """
        if audio_data is None or len(audio_data) == 0:
            return ""

        print("Transcribing...")

        # Run transcription
        segments, info = self.model.transcribe(
            audio_data,
            beam_size=5,
            language="en",
            task="transcribe"
        )

        # Combine all segments
        text = " ".join([segment.text for segment in segments])
        text = text.strip()

        print(f"Transcription: {text}")
        return text

    def listen_and_transcribe(self, max_duration=30):
        """
        Record audio and transcribe in one call

        Args:
            max_duration: Maximum recording duration in seconds

        Returns:
            Transcribed text string
        """
        audio_data = self.record_audio(max_duration)
        return self.transcribe(audio_data)

    def stop_recording(self):
        """Manually stop the current recording"""
        self.is_recording = False


if __name__ == "__main__":
    # Test the transcriber
    transcriber = Transcriber(model_size="base", compute_type="int8")

    print("\n=== Testing Transcriber ===")
    text = transcriber.listen_and_transcribe()
    print(f"\nFinal transcription: {text}")
