"""
Perception Layer - The Ears of GLOW
Handles wake word detection and speech-to-text transcription
"""

from .wake_word import WakeWordDetector
from .transcriber import Transcriber

__all__ = ["WakeWordDetector", "Transcriber"]
