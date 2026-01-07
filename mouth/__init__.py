"""
Speech Output Layer - The Mouth of GLOW
Handles text-to-speech synthesis
"""

from .tts_engine import TTSEngine, AdvancedTTSEngine

__all__ = ["TTSEngine", "AdvancedTTSEngine"]
