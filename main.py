"""
Project GLOW - General Local Offline Windows-agent
Main entry point - Complete end-to-end functionality

Features:
- Intelligent vision (Gemini can SEE the screen)
- Multi-agent system with planning, execution, verification
- Voice interaction with wake word detection
- Text-based interaction mode
- Complete Windows PC automation
- NO hardcoded coordinates or silent fallbacks
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


class GLOW:
    """
    Main GLOW assistant - Complete end-to-end functionality
    Handles configuration, initialization, and orchestration
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize GLOW with configuration

        Args:
            config_path: Path to configuration file
        """
        print("=" * 80)
        print("GLOW - General Local Offline Windows-agent")
        print("=" * 80)

        # Load configuration
        self.config = self._load_config(config_path)
        self.running = False

        # Initialize components
        self._init_planner()
        self._init_multi_agent_system()
        self._init_voice_components()

        print("\n" + "=" * 80)
        print("GLOW initialized successfully!")
        print("=" * 80)
        self._print_status()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        print(f"\n[CONFIG] Loading configuration from {config_path}...")

        if not os.path.exists(config_path):
            print(f"[WARNING] Config file not found. Creating default config...")
            self._create_default_config(config_path)

        with open(config_path, 'r') as f:
            config = json.load(f)

        print(f"[OK] Configuration loaded")
        print(f"  Model: {config.get('conversational_model', 'Unknown')}")
        print(f"  Vision enabled: {config.get('enable_vision', False)}")

        return config

    def _create_default_config(self, config_path: str):
        """Create default configuration file"""
        print("\n" + "=" * 80)
        print("FIRST TIME SETUP")
        print("=" * 80)
        print("\nAvailable AI Models:")
        print("  1. Gemini Vision (Recommended) - Can SEE your screen!")
        print("  2. Groq (Fast) - Very fast, no vision")
        print("  3. Claude (Anthropic) - High quality, no vision")

        while True:
            choice = input("\nSelect model (1-3): ").strip()
            if choice in ['1', '2', '3']:
                break
            print("Invalid choice. Please enter 1, 2, or 3.")

        # Get API key
        if choice == '1':
            model_name = "Gemini Vision (Live Vision)"
            api_key = input("\nEnter your Gemini API key (from ai.google.dev): ").strip()
            default_config = {
                "conversational_model": model_name,
                "gemini_api_key": api_key,
                "gemini_model": "gemini-3-flash-preview",
                "enable_vision": True,
                "groq_api_key": "",
                "groq_model": "meta-llama/llama-4-maverick-17b-128e-instruct",
                "anthropic_api_key": "",
                "anthropic_model": "claude-sonnet-4-5-20250929",
                "auto_listen": False,
                "tts_engine": "windows",
                "wake_word_enabled": False
            }
        elif choice == '2':
            model_name = "Groq (Fast API)"
            api_key = input("\nEnter your Groq API key (from console.groq.com): ").strip()
            default_config = {
                "conversational_model": model_name,
                "gemini_api_key": "",
                "gemini_model": "gemini-3-flash-preview",
                "enable_vision": False,
                "groq_api_key": api_key,
                "groq_model": "meta-llama/llama-4-maverick-17b-128e-instruct",
                "anthropic_api_key": "",
                "anthropic_model": "claude-sonnet-4-5-20250929",
                "auto_listen": False,
                "tts_engine": "windows",
                "wake_word_enabled": False
            }
        else:  # choice == '3'
            model_name = "Claude (Anthropic)"
            api_key = input("\nEnter your Anthropic API key (from console.anthropic.com): ").strip()
            default_config = {
                "conversational_model": model_name,
                "gemini_api_key": "",
                "gemini_model": "gemini-3-flash-preview",
                "enable_vision": False,
                "groq_api_key": "",
                "groq_model": "meta-llama/llama-4-maverick-17b-128e-instruct",
                "anthropic_api_key": api_key,
                "anthropic_model": "claude-sonnet-4-5-20250929",
                "auto_listen": False,
                "tts_engine": "windows",
                "wake_word_enabled": False
            }

        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        print(f"\n[OK] Configuration saved to {config_path}")
        print(f"[OK] Using: {model_name}")
        print("\nYou can change settings later by editing config.json")
        print("=" * 80)

    def _init_planner(self):
        """Initialize AI planner based on configuration"""
        print("\n[PLANNER] Initializing AI planner...")

        model_name = self.config.get('conversational_model', '')

        # Determine which planner to use
        if "Gemini" in model_name:
            from brain.gemini_vision_planner import GeminiVisionPlanner

            api_key = self.config.get('gemini_api_key')
            if not api_key:
                raise ValueError("Gemini API key required. Set 'gemini_api_key' in config.json")

            model = self.config.get('gemini_model', 'gemini-3-flash-preview')
            enable_vision = self.config.get('enable_vision', True)

            if enable_vision:
                print(f"  Using: Gemini Vision Planner (Model: {model})")
                self.planner = GeminiVisionPlanner(api_key=api_key, model=model)
                print(f"  [OK] Gemini Vision ready - AI can SEE the screen!")
            else:
                from brain.gemini_planner import GeminiPlanner
                print(f"  Using: Gemini Planner (Model: {model})")
                self.planner = GeminiPlanner(api_key=api_key, model=model)
                print(f"  [OK] Gemini Planner ready")

        elif "Groq" in model_name:
            from brain.groq_planner import GroqPlanner

            api_key = self.config.get('groq_api_key')
            if not api_key:
                raise ValueError("Groq API key required. Set 'groq_api_key' in config.json")

            model = self.config.get('groq_model', 'meta-llama/llama-4-maverick-17b-128e-instruct')
            print(f"  Using: Groq Planner (Model: {model})")
            self.planner = GroqPlanner(api_key=api_key, model=model)
            print(f"  [OK] Groq Planner ready")

        elif "Claude" in model_name or "Anthropic" in model_name:
            from brain.claude_planner import ClaudePlanner

            api_key = self.config.get('anthropic_api_key')
            if not api_key:
                raise ValueError("Anthropic API key required. Set 'anthropic_api_key' in config.json")

            model = self.config.get('anthropic_model', 'claude-sonnet-4-5-20250929')
            print(f"  Using: Claude Planner (Model: {model})")
            self.planner = ClaudePlanner(api_key=api_key, model=model)
            print(f"  [OK] Claude Planner ready")

        else:
            raise ValueError(f"Unknown model: {model_name}. Check config.json")

    def _init_multi_agent_system(self):
        """Initialize multi-agent orchestration system"""
        print("\n[AGENTS] Initializing multi-agent system...")

        from brain.multi_agent_system import MultiAgentSystem
        from hands import TOOL_REGISTRY

        self.agent_system = MultiAgentSystem(
            planner=self.planner,
            tool_registry=TOOL_REGISTRY
        )

        print(f"  [OK] Multi-agent system ready")
        print(f"  [OK] {len(TOOL_REGISTRY)} tools available")

    def _init_voice_components(self):
        """Initialize voice components (optional)"""
        print("\n[VOICE] Initializing voice components...")

        self.tts = None
        self.wake_detector = None
        self.transcriber = None
        self.ui = None

        # Visual UI Orb
        try:
            from body.glow_orb import GlowOrb
            print(f"  Loading visual orb...")
            # We don't have a standalone UI runner in main.py anymore, usually glow_app (glow_app) handles this
            # But for completeness if main_cli runs it:
            pass # CLI mode doesn't really support the PyQt Orb easily without QApp loop
            print(f"  [INFO] Visual orb managed by GUI app")
        except Exception as e:
            print(f"  [SKIP] Visual orb not available: {e}")

        # TTS Engine (optional)
        try:
            from mouth.tts_engine import TTSEngine
            tts_engine_type = self.config.get('tts_engine', 'windows')
            print(f"  Loading TTS engine ({tts_engine_type})...")
            self.tts = TTSEngine()
            print(f"  [OK] TTS engine ready")
        except Exception as e:
            print(f"  [SKIP] TTS not available: {e}")

        # Wake word detection (optional)
        if self.config.get('wake_word_enabled', False):
            try:
                from ears.wake_word import WakeWordDetector
                print(f"  Loading wake word detector...")
                self.wake_detector = WakeWordDetector(wake_word="hey_jarvis", threshold=0.5)
                print(f"  [OK] Wake word detector ready")
            except Exception as e:
                print(f"  [SKIP] Wake word not available: {e}")

        # Whisper transcriber (optional)
        if self.config.get('auto_listen', False):
            try:
                from ears.transcriber import Transcriber
                print(f"  Loading Whisper transcriber...")
                self.transcriber = Transcriber(model_size="base", compute_type="int8")
                print(f"  [OK] Transcriber ready")
            except Exception as e:
                print(f"  [SKIP] Transcriber not available: {e}")

    def _print_status(self):
        """Print current system status"""
        print("\n" + "-" * 80)
        print("System Status:")
        print("-" * 80)
        print(f"  AI Planner: {self.config.get('conversational_model')}")
        print(f"  Vision: {'Enabled' if self.config.get('enable_vision') else 'Disabled'}")
        print(f"  TTS: {'Available' if self.tts else 'Not available'}")
        print(f"  Wake Word: {'Available' if self.wake_detector else 'Not available'}")
        print(f"  Voice Input: {'Available' if self.transcriber else 'Not available'}")
        print(f"  Tools: {len(self.agent_system.executor.tool_registry)}")
        print("-" * 80)

    def process_command(self, user_input: str) -> str:
        """
        Process a user command end-to-end

        Args:
            user_input: User's request

        Returns:
            Response message
        """
        print(f"\n{'=' * 80}")
        print(f"USER: {user_input}")
        print(f"{'=' * 80}")

        try:
            # Process through multi-agent system
            response = self.agent_system.process_request(user_input)
            return response

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg

    def speak(self, text: str):
        """Speak text using TTS (if available)"""
        print(f"\nGLOW: {text}")

        if self.tts:
            self.tts.speak(text, wait=True)

    def run_text_mode(self):
        """Run in text-based interactive mode"""
        print("\n" + "=" * 80)
        print("TEXT MODE - Type your commands")
        print("=" * 80)
        print("Commands:")
        print("  - Type any command to execute")
        print("  - Type 'exit' or 'quit' to stop")
        print("  - Type 'status' to see system status")
        print("=" * 80)

        self.running = True

        # Welcome message
        welcome = "Hello! I am GLOW, your Windows assistant. How can I help you?"
        self.speak(welcome)

        try:
            while self.running:
                # Get user input
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ["exit", "quit", "stop", "bye"]:
                    break

                if user_input.lower() == "status":
                    self._print_status()
                    continue

                # Process command
                response = self.process_command(user_input)

                # Speak response
                self.speak(response)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")

        finally:
            self.speak("Goodbye!")
            self.running = False

    def run_voice_mode(self):
        """Run in voice interaction mode"""
        if not self.transcriber:
            print("\n[ERROR] Voice mode requires Whisper transcriber")
            print("Set 'auto_listen': true in config.json")
            return

        print("\n" + "=" * 80)
        print("VOICE MODE - Press Enter to speak")
        print("=" * 80)
        print("  - Press Enter to start listening")
        print("  - Speak your command (max 30 seconds)")
        print("  - Type 'exit' to quit")
        print("=" * 80)

        self.running = True
        self.speak("Hello! Press Enter when you want to talk to me.")

        try:
            while self.running:
                # Wait for user
                command = input("\n[Press Enter to speak, or type 'exit']: ").strip()

                if command.lower() in ["exit", "quit", "stop"]:
                    break

                # Listen for voice input
                print("\n[LISTENING] Speak now...")
                user_input = self.transcriber.listen_and_transcribe(max_duration=30)

                if user_input:
                    print(f"[HEARD] {user_input}")

                    # Process command
                    response = self.process_command(user_input)

                    # Speak response
                    self.speak(response)
                else:
                    print("[INFO] No input detected")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")

        finally:
            self.speak("Goodbye!")
            self.running = False

    def run_wake_word_mode(self):
        """Run with wake word activation"""
        if not self.wake_detector or not self.transcriber:
            print("\n[ERROR] Wake word mode requires wake word detector and transcriber")
            print("Set 'wake_word_enabled': true and 'auto_listen': true in config.json")
            return

        print("\n" + "=" * 80)
        print("WAKE WORD MODE - Say 'Hey Jarvis' to activate")
        print("=" * 80)
        print("  - Say wake word to activate GLOW")
        print("  - Then speak your command")
        print("  - Press Ctrl+C to exit")
        print("=" * 80)

        self.wake_detector.start()
        self.running = True

        print("\nListening for wake word...")

        try:
            while self.running:
                # Wait for wake word
                detection = self.wake_detector.wait_for_wake_word(timeout=0.5)

                if detection:
                    print(f"\n[WAKE WORD DETECTED] Confidence: {detection['confidence']:.2f}")
                    self.speak("Yes?")

                    # Listen for command
                    print("[LISTENING] Speak now...")
                    user_input = self.transcriber.listen_and_transcribe(max_duration=30)

                    if user_input:
                        print(f"[HEARD] {user_input}")

                        # Process command
                        response = self.process_command(user_input)

                        # Speak response
                        self.speak(response)
                    else:
                        print("[INFO] No input detected")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")

        finally:
            self.wake_detector.stop()
            self.running = False

    def run_demo(self):
        """Run demo mode with example commands"""
        print("\n" + "=" * 80)
        print("DEMO MODE - Example Commands")
        print("=" * 80)

        demo_commands = [
            "What can you do?",
            "open browser then youtube and play banda kaam ka by chaar diwari",
            "create a folder called GLOWTest on desktop",
        ]

        for i, command in enumerate(demo_commands, 1):
            print(f"\n{'=' * 80}")
            print(f"DEMO {i}/{len(demo_commands)}")
            print(f"{'=' * 80}")

            # Process command
            response = self.process_command(command)

            # Speak response
            self.speak(response)

            # Wait for user
            if i < len(demo_commands):
                input("\n[Press Enter to continue to next demo...]")

        print("\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80)

    def start(self, mode: str = "text"):
        """
        Start GLOW in specified mode

        Args:
            mode: Operation mode ('text', 'voice', 'wake', 'demo')
        """
        if mode == "text":
            self.run_text_mode()
        elif mode == "voice":
            self.run_voice_mode()
        elif mode == "wake":
            self.run_wake_word_mode()
        elif mode == "demo":
            self.run_demo()
        else:
            print(f"[ERROR] Unknown mode: {mode}")
            print("Available modes: text, voice, wake, demo")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="GLOW - General Local Offline Windows-agent",
        epilog="Configure API keys in config.json before running"
    )

    parser.add_argument(
        "--mode",
        choices=["text", "voice", "wake", "demo"],
        default="text",
        help="Operation mode (default: text)"
    )

    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )

    args = parser.parse_args()

    try:
        # Initialize and start GLOW
        assistant = GLOW(config_path=args.config)
        assistant.start(mode=args.mode)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
