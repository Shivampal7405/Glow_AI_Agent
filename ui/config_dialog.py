"""
Configuration Dialog for GLOW
"""
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ConfigDialog(QDialog):
    """Configuration dialog for GLOW settings"""

    def __init__(self, config_path="config.json", parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.config = self._load_config()
        self._init_ui()

    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self):
        """Default configuration"""
        return {
            "conversational_model": "Groq (Fast API)",
            "gemini_api_key": "",
            "gemini_model": "gemini-3-flash-preview",
            "enable_vision": True,
            "groq_api_key": "",
            "groq_model": "meta-llama/llama-4-maverick-17b-128e-instruct",
            "anthropic_api_key": "",
            "anthropic_model": "claude-sonnet-4-5-20250929",
            "openai_api_key": "",
            "openai_model": "gpt-4o",
            "ollama_url": "http://localhost:11434",
            "ollama_model": "llama3.2",
            "whisper_model": "base",
            "auto_listen": False,
            "tts_engine": "windows",
            "wake_word_enabled": False
        }

    def _init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("GLOW Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

        # Modern font
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        section_font = QFont("Segoe UI", 10, QFont.Weight.Bold)

        layout = QVBoxLayout()

        # Title
        title = QLabel("GLOW Configuration")
        title.setFont(title_font)
        title.setStyleSheet("color: #4A90E2; padding: 10px;")
        layout.addWidget(title)

        # AI Model Selection
        model_group = QGroupBox("AI Model")
        model_group.setFont(section_font)
        model_layout = QFormLayout()

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Groq (Fast API)",
            "Gemini Vision (Live Vision)",
            "Claude (Anthropic)",
            "OpenAI (GPT-4)",
            "Ollama (Local)"
        ])
        self.model_combo.setCurrentText(self.config.get("conversational_model", "Groq (Fast API)"))
        model_layout.addRow("Model:", self.model_combo)

        self.vision_check = QCheckBox("Enable Vision")
        self.vision_check.setChecked(self.config.get("enable_vision", True))
        model_layout.addRow("Vision:", self.vision_check)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # API Keys
        api_group = QGroupBox("API Keys")
        api_group.setFont(section_font)
        api_layout = QFormLayout()

        self.gemini_key = QLineEdit(self.config.get("gemini_api_key", ""))
        self.gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Gemini:", self.gemini_key)

        self.groq_key = QLineEdit(self.config.get("groq_api_key", ""))
        self.groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Groq:", self.groq_key)

        self.anthropic_key = QLineEdit(self.config.get("anthropic_api_key", ""))
        self.anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Anthropic:", self.anthropic_key)

        self.openai_key = QLineEdit(self.config.get("openai_api_key", ""))
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("OpenAI:", self.openai_key)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Voice Settings
        voice_group = QGroupBox("Voice Settings")
        voice_group.setFont(section_font)
        voice_layout = QFormLayout()

        self.tts_combo = QComboBox()
        self.tts_combo.addItems(["windows", "pyttsx3"])
        self.tts_combo.setCurrentText(self.config.get("tts_engine", "windows"))
        voice_layout.addRow("TTS Engine:", self.tts_combo)

        self.auto_listen_check = QCheckBox("Auto Listen")
        self.auto_listen_check.setChecked(self.config.get("auto_listen", False))
        voice_layout.addRow("", self.auto_listen_check)

        self.wake_word_check = QCheckBox("Wake Word Enabled")
        self.wake_word_check.setChecked(self.config.get("wake_word_enabled", False))
        voice_layout.addRow("", self.wake_word_check)

        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        save_btn.clicked.connect(self._save_config)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _save_config(self):
        """Save configuration to file"""
        self.config["conversational_model"] = self.model_combo.currentText()
        self.config["enable_vision"] = self.vision_check.isChecked()
        self.config["gemini_api_key"] = self.gemini_key.text()
        self.config["groq_api_key"] = self.groq_key.text()
        self.config["anthropic_api_key"] = self.anthropic_key.text()
        self.config["openai_api_key"] = self.openai_key.text()
        self.config["tts_engine"] = self.tts_combo.currentText()
        self.config["auto_listen"] = self.auto_listen_check.isChecked()
        self.config["wake_word_enabled"] = self.wake_word_check.isChecked()

        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

        self.accept()
