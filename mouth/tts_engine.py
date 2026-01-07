"""
Text-to-Speech Engine using Piper TTS
Provides natural-sounding offline voice synthesis
"""

import subprocess
import os
import tempfile
from pathlib import Path
from typing import Optional
import pygame


class TTSEngine:
    def __init__(self, piper_path: Optional[str] = None, model_path: Optional[str] = None):
        """
        Initialize TTS Engine

        Args:
            piper_path: Path to piper executable
            model_path: Path to piper voice model
        """
        # Auto-detect Piper in project directory
        if piper_path is None:
            project_root = Path(__file__).parent.parent
            piper_paths = [
                project_root / "piper.exe",  # Windows in root
                project_root / "piper",      # Linux/Mac in root
                project_root / "piper" / "piper.exe",  # Windows in piper folder
                project_root / "piper" / "piper",      # Linux/Mac in piper folder
            ]

            for path in piper_paths:
                if path.exists():
                    piper_path = str(path)
                    break

            if piper_path is None:
                piper_path = "piper"  # Fall back to PATH

        self.piper_path = piper_path

        # Auto-detect voice model in project directory
        if model_path is None:
            project_root = Path(__file__).parent.parent
            model_dirs = [
                project_root / "piper" / "models",
                project_root / "models",
                project_root / "piper",
            ]

            for model_dir in model_dirs:
                if model_dir.exists():
                    # Look for any .onnx model file
                    models = list(model_dir.glob("*.onnx"))
                    if models:
                        model_path = str(models[0])
                        break

        self.model_path = model_path

        # Initialize pygame mixer for audio playback
        pygame.mixer.init()

        # Check if piper is available
        self.is_available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Piper TTS is available"""
        try:
            result = subprocess.run(
                [self.piper_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Speak text using TTS

        Args:
            text: Text to speak
            wait: Whether to wait for speech to complete

        Returns:
            Success status
        """
        if not text.strip():
            return False

        # Fallback to basic TTS if Piper not available
        if not self.is_available:
            return self._fallback_speak(text)

        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                audio_file = tmp_file.name

            # Run Piper TTS
            cmd = [self.piper_path, "--output_file", audio_file]
            if self.model_path:
                cmd.extend(["--model", self.model_path])

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            process.communicate(input=text.encode())

            # Play the audio file
            if os.path.exists(audio_file):
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()

                if wait:
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)

                # Clean up
                try:
                    os.remove(audio_file)
                except:
                    pass

                return True
            else:
                return False

        except Exception as e:
            print(f"TTS Error: {e}")
            return self._fallback_speak(text)

    def _fallback_speak(self, text: str) -> bool:
        """
        Fallback TTS using Windows built-in SAPI

        Args:
            text: Text to speak

        Returns:
            Success status
        """
        try:
            # Use Windows PowerShell for TTS
            ps_script = f'Add-Type -AssemblyName System.speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'

            subprocess.Popen(
                ["powershell", "-Command", ps_script],
                shell=True
            )

            return True
        except Exception as e:
            print(f"Fallback TTS Error: {e}")
            return False

    def stop(self):
        """Stop current speech"""
        try:
            pygame.mixer.music.stop()
        except:
            pass


class AdvancedTTSEngine(TTSEngine):
    """
    Advanced TTS with voice selection and speed control
    """

    def __init__(self, voice: str = "default", speed: float = 1.0):
        """
        Initialize advanced TTS

        Args:
            voice: Voice identifier
            speed: Speech speed multiplier
        """
        super().__init__()
        self.voice = voice
        self.speed = speed

    def speak_with_emotion(self, text: str, emotion: str = "neutral") -> bool:
        """
        Speak with emotional inflection (future enhancement)

        Args:
            text: Text to speak
            emotion: Emotion type (neutral, happy, sad, etc.)

        Returns:
            Success status
        """
        # For now, just use regular speak
        # Future: Could adjust pitch/speed based on emotion
        return self.speak(text)


if __name__ == "__main__":
    # Test TTS
    tts = TTSEngine()

    print("Testing TTS...")
    tts.speak("Hello! I am GLOW, your local AI assistant.")

    print("Testing with longer text...")
    tts.speak("I can control your computer, browse the web, and help you code. How can I assist you today?")

    print("TTS test complete")
