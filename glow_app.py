"""
GLOW Desktop Application
General Local Offline Windows-agent
Complete GUI with visual orb and text interface
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QMenuBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase, QAction

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


class CommandWorker(QThread):
    """Worker thread for processing commands"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, agent_system, command):
        super().__init__()
        self.agent_system = agent_system
        self.command = command

    def run(self):
        try:
            response = self.agent_system.process_request(self.command)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class GlowApp(QMainWindow):
    """GLOW Desktop Application - General Local Offline Windows-agent"""

    def __init__(self):
        super().__init__()

        # Load configuration
        self.config = self._load_config()

        # Initialize GLOW components
        self._init_glow()

        # Setup UI (hidden - only orb is visible)
        self._init_ui()

        # Hide the main window - we only want the orb!
        self.hide()

        # Worker thread
        self.worker = None

    def _load_config(self):
        """Load configuration"""
        config_path = "config.json"

        if not Path(config_path).exists():
            print("Config not found. Please run: python main.py")
            sys.exit(1)

        with open(config_path, 'r') as f:
            return json.load(f)

    def _init_glow(self):
        """Initialize GLOW components"""
        print("Initializing GLOW v1.0.5 (Patched with Argument Aliasing)...")

        # Initialize planner
        model_name = self.config.get('conversational_model', '')

        if "Gemini" in model_name:
            enable_vision = self.config.get('enable_vision', False)

            if enable_vision:
                from brain.gemini_vision_planner import GeminiVisionPlanner
                key = self.config.get('gemini_api_key', '')
                self.planner = GeminiVisionPlanner(
                    api_key=key,
                    model=self.config.get('gemini_model', 'gemini-3-flash-preview')
                )
            else:
                from brain.gemini_planner import GeminiPlanner
                key = self.config.get('gemini_api_key', '')
                self.planner = GeminiPlanner(
                    api_key=key,
                    model=self.config.get('gemini_model', 'gemini-2.5-flash-native-audio-preview-12-2025')
                )

        elif "Groq" in model_name:
            from brain.groq_planner import GroqPlanner
            key = self.config.get('groq_api_key', '')
            self.planner = GroqPlanner(
                api_key=key,
                model=self.config.get('groq_model', 'meta-llama/llama-4-maverick-17b-128e-instruct')
            )

        elif "Claude" in model_name or "Anthropic" in model_name:
            from brain.claude_planner import ClaudePlanner
            key = self.config.get('anthropic_api_key', '')
            self.planner = ClaudePlanner(
                api_key=key,
                model=self.config.get('anthropic_model', 'claude-sonnet-4-5-20250929')
            )

        else:
            # Default fallback
            from brain.gemini_planner import GeminiPlanner
            key = self.config.get('gemini_api_key', '')
            self.planner = GeminiPlanner(
                api_key=key,
                model=self.config.get('gemini_model', 'gemini-2.5-flash-native-audio-preview-12-2025')
            )

        # Initialize multi-agent system
        from brain.multi_agent_system import MultiAgentSystem
        from hands import TOOL_REGISTRY

        self.agent_system = MultiAgentSystem(
            planner=self.planner,
            tool_registry=TOOL_REGISTRY
        )

        # Initialize GLOW orb interface
        try:
            from body.glow_orb import GlowOrb
            self.orb = GlowOrb(size=300)

            # Connect Orb Signals
            self.orb.settings_clicked.connect(self._show_settings)
            self.orb.close_clicked.connect(self.close)
            self.orb.text_entered.connect(self.process_command)
            self.orb.voice_toggled.connect(self.toggle_voice_input)

            self.orb.show()
            self.orb.set_state_idle()
            print("GLOW orb initialized")
        except Exception as e:
            print(f"Orb not available: {e}")
            self.orb = None

        print("GLOW ready!")

    def _create_menu_bar(self):
        """Create menu bar with settings option"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_settings(self):
        """Show settings dialog"""
        from ui.config_dialog import ConfigDialog

        new_config = ConfigDialog.edit_config("config.json", self)

        if new_config:
            # Update local config
            self.config = new_config
            # Re-initialize basic parts if needed (like status label)
            self.status_label.setText(f"Model: {self.config.get('conversational_model')}")

            QMessageBox.information(
                self,
                "Settings Saved",
                "Configuration saved successfully!\nPlease restart GLOW for all changes to take effect."
            )

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About GLOW",
            """<h2 style='font-family: "Segoe UI", "Inter", sans-serif; color: #4A90E2;'>GLOW</h2>
            <p style='font-family: "Segoe UI", "Inter", sans-serif; font-size: 11pt;'><b>General Local Offline Windows-agent</b></p>
            <p style='font-family: "Segoe UI", sans-serif;'>Version 1.0.5 (Patched)</p>
            <p style='font-family: "Segoe UI", sans-serif;'>Intelligent Windows PC automation with vision and multi-agent planning.</p>
            <p style='font-family: "Segoe UI", sans-serif;'><b>Features:</b></p>
            <ul style='font-family: "Segoe UI", sans-serif;'>
            <li>Intelligent Vision (AI can SEE your screen)</li>
            <li>Multi-Agent System (Planning, Execution, Verification)</li>
            <li>88+ Windows automation tools</li>
            <li>Beautiful glowing orb interface</li>
            </ul>
            """
        )

    def _init_ui(self):
        """Initialize user interface with aesthetic fonts"""
        self.setWindowTitle("GLOW - Windows Assistant")
        self.setGeometry(100, 100, 800, 600)

        # Create menu bar
        self._create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Title with modern aesthetic font
        title = QLabel("✨ GLOW")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4A90E2; padding: 10px;")
        layout.addWidget(title)

        # Subtitle with elegant font
        subtitle = QLabel("General Local Offline Windows-agent")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7B8A9B; font-style: italic; padding-bottom: 10px;")
        layout.addWidget(subtitle)

        # Status label with modern font
        self.status_label = QLabel(f"Model: {self.config.get('conversational_model')}")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #5A6C7D; padding: 5px;")
        layout.addWidget(self.status_label)

        # Chat display with beautiful monospace font
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #E1E4E8;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.chat_display)

        # Input field with modern styling
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your command here...")
        self.input_field.setFont(QFont("Segoe UI", 11))
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #D1D5DB;
                border-radius: 8px;
                background-color: white;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #4A90E2;
            }
        """)
        self.input_field.returnPressed.connect(self.send_command)
        layout.addWidget(self.input_field)

        # Send button with modern aesthetic
        self.send_button = QPushButton("✨ Send")
        self.send_button.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', sans-serif;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2E6BA9;
            }
            QPushButton:disabled {
                background-color: #B0BEC5;
            }
        """)
        self.send_button.clicked.connect(self.send_command)
        layout.addWidget(self.send_button)

        # Welcome message with styled HTML
        welcome_msg = """<div style='font-family: "Segoe UI", sans-serif; color: #4A90E2; font-size: 11pt;'>
        <b>✨ Hello! I am GLOW</b><br>
        <span style='color: #7B8A9B;'>Your General Local Offline Windows-agent. How can I help you today?</span>
        </div>"""
        self.chat_display.append(welcome_msg)

    def append_message(self, sender, message):
        """Append message to chat display with aesthetic styling"""
        if sender == "GLOW":
            styled_msg = f"""<div style='font-family: "Segoe UI", sans-serif; margin: 8px 0;'>
            <b style='color: #4A90E2;'>✨ {sender}:</b>
            <span style='color: #2C3E50;'>{message}</span>
            </div>"""
        elif sender == "You":
            styled_msg = f"""<div style='font-family: "Segoe UI", sans-serif; margin: 8px 0;'>
            <b style='color: #27AE60;'>👤 {sender}:</b>
            <span style='color: #34495E;'>{message}</span>
            </div>"""
        elif sender == "ERROR":
            styled_msg = f"""<div style='font-family: "Segoe UI", sans-serif; margin: 8px 0;'>
            <b style='color: #E74C3C;'>⚠️ {sender}:</b>
            <span style='color: #C0392B;'>{message}</span>
            </div>"""
        elif sender == "System":
            styled_msg = f"""<div style='font-family: "Segoe UI", sans-serif; margin: 8px 0;'>
            <b style='color: #9B59B6;'>⚙️ {sender}:</b>
            <span style='color: #8E44AD;'>{message}</span>
            </div>"""
        else:
            styled_msg = f"""<div style='font-family: "Segoe UI", sans-serif; margin: 8px 0;'>
            <b>{sender}:</b> {message}
            </div>"""

        self.chat_display.append(styled_msg)

    def send_command(self):
        """Handle button click from main window"""
        text = self.input_field.text().strip()
        if text:
            self.process_command(text)

    def process_command(self, command):
        """Process command from any source"""
        if not command:
            return

        # Clear main input if it matches
        if self.input_field.text() == command:
            self.input_field.clear()

        # Display user message
        self.append_message("You", command)

        # Update Orb status
        if self.orb:
            self.orb.set_status_text(f"You: {command}")

        # Handle special commands
        if command.lower() in ["exit", "quit", "bye"]:
            self.close()
            return

        if command.lower() == "status":
            self.show_status()
            return

        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.status_label.setText("Processing...")

        # Update orb state
        if self.orb:
            self.orb.set_state_thinking()
            self.orb.set_status_text("GLOW is thinking...")

        # Process command in background thread
        self.worker = CommandWorker(self.agent_system, command)
        self.worker.finished.connect(self.on_command_finished)
        self.worker.error.connect(self.on_command_error)
        self.worker.start()

    def toggle_voice_input(self):
        """Toggle voice input mode"""
        if self.orb:
            if self.orb.current_state == "listening":
                self.orb.set_state_idle()
                self.orb.set_status_text("")
                self.append_message("System", "Voice mode deactivated")
            else:
                self.orb.set_state_listening()
                self.orb.set_status_text("Listening...")
                self.append_message("System", "Voice mode activated (Simulation)")

    def on_command_finished(self, response):
        """Handle command completion"""
        # Display response
        self.append_message("GLOW", response)

        # Update Orb text
        if self.orb:
            snippet = response[:100] + "..." if len(response) > 100 else response
            self.orb.set_status_text(snippet)
            self.orb.set_state_idle()

        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()
        self.status_label.setText(f"Model: {self.config.get('conversational_model')}")

    def on_command_error(self, error):
        """Handle command error"""
        # Display error
        self.append_message("ERROR", error)

        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()
        self.status_label.setText("Error")

        # Update orb
        if self.orb:
            self.orb.set_state_error()
            self.orb.set_status_text(f"Error: {error}")

    def show_status(self):
        """Show system status"""
        status = f"""<div style='font-family: "Segoe UI", sans-serif;'>
        <b style='color: #4A90E2;'>✨ System Status:</b><br>
        <span style='color: #7B8A9B;'>
        AI Model: {self.config.get('conversational_model')}<br>
        Vision: {'Enabled' if self.config.get('enable_vision') else 'Disabled'}<br>
        Tools: {len(self.agent_system.executor.tool_registry)}<br>
        </span>
        </div>"""
        self.append_message("System", status)

    def closeEvent(self, event):
        """Handle window close"""
        if self.orb:
            self.orb.close()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern style

    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))

    # Initialize app but don't show the main window
    # The Orb will be shown by GlowApp._init_glow
    window = GlowApp()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
