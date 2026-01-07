"""
GLOW Orb - Cinematic floating orb with integrated controls
General Local Offline Windows-agent interface
Beautiful glowing orb with plasma effects
"""

import math
from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QRadialGradient, QColor, QBrush, QPainterPath, QCursor, QFont
)


class GlowOrb(QWidget):
    """Cinematic glowing plasma orb with integrated input and controls"""

    # Signals
    settings_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    text_entered = pyqtSignal(str)
    voice_toggled = pyqtSignal()

    # State color schemes (base colors for plasma glow)
    COLOR_IDLE = (10, 0, 90)         # Deep Blue - Ready state
    COLOR_LISTENING = (0, 90, 10)     # Deep Green - Voice input
    COLOR_THINKING = (90, 60, 0)      # Orange/Amber - Processing
    COLOR_SPEAKING = (60, 0, 90)      # Purple - Responding
    COLOR_ERROR = (90, 0, 0)          # Red - Error state

    def __init__(self, size=400, position=None):
        super().__init__()

        self.orb_size = size
        self.current_state = "idle"
        self._time = 0.0

        # Setup window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self.setFixedSize(size, size + 60)

        # Position window
        if position:
            self.move(position[0], position[1])
        else:
            self._position_bottom_right()

        # Setup UI controls
        self._setup_controls()

        # Animation timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(16)

        # Enable dragging
        self.dragging = False
        self.drag_start = None

    def _position_bottom_right(self):
        """Position orb in bottom-right corner"""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        margin = 50
        x = screen.width() - self.width() - margin
        y = screen.height() - self.height() - margin
        self.move(x, y)

    def _setup_controls(self):
        """Setup input box and control buttons with aesthetic styling"""
        # Settings button (top-left) with modern aesthetic
        self.settings_btn = QPushButton("⚙", self)
        self.settings_btn.setGeometry(10, 10, 35, 35)
        self.settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_btn.setFont(QFont("Segoe UI", 16))
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                border: 2px solid rgba(74, 144, 226, 100);
                border-radius: 17px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 226, 180);
                border: 2px solid rgba(104, 174, 255, 180);
            }
        """)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)

        # Close button (top-right) with modern aesthetic
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setGeometry(self.orb_size - 45, 10, 35, 35)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setFont(QFont("Segoe UI", 18))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                border: 2px solid rgba(231, 76, 60, 120);
                border-radius: 17px;
                font-size: 18px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: rgba(231, 76, 60, 180);
                border: 2px solid rgba(255, 106, 90, 200);
            }
        """)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        
        # Microphone button (bottom-right of orb)
        self.mic_btn = QPushButton("🎤", self)
        self.mic_btn.setGeometry(self.orb_size - 45, self.orb_size - 45, 35, 35)
        self.mic_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mic_btn.setFont(QFont("Segoe UI", 16))
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                border: 2px solid rgba(46, 204, 113, 100);
                border-radius: 17px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(46, 204, 113, 180);
                border: 2px solid rgba(88, 230, 150, 180);
            }
        """)
        self.mic_btn.clicked.connect(self.voice_toggled.emit)

        # Input box at bottom with aesthetic font and styling
        self.input_box = QLineEdit(self)
        self.input_box.setGeometry(20, self.orb_size + 10, self.orb_size - 40, 40)
        self.input_box.setPlaceholderText("✨ Type your command...")
        self.input_box.setFont(QFont("Segoe UI", 11))
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: rgba(248, 249, 250, 240);
                color: #2C3E50;
                border: 2px solid rgba(74, 144, 226, 150);
                border-radius: 20px;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                letter-spacing: 0.5px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(74, 144, 226, 255);
                background-color: rgba(255, 255, 255, 255);
            }
            QLineEdit::placeholder {
                color: rgba(123, 138, 155, 180);
                font-style: italic;
            }
        """)
        self.input_box.returnPressed.connect(self._on_text_entered)
        
        # Status Label (above input box)
        self.status_label = QLabel(self)
        self.status_label.setGeometry(20, self.orb_size - 40, self.orb_size - 40, 30)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("""
            color: rgba(255, 255, 255, 200);
            background-color: transparent;
            text-shadow: 1px 1px 2px rgba(0,0,0,150);
        """)
        self.status_label.setText("")

    def _on_text_entered(self):
        """Handle text input"""
        text = self.input_box.text().strip()
        if text:
            self.text_entered.emit(text)
            self.input_box.clear()

    def set_status_text(self, text):
        """Set status text in the orb UI"""
        self.status_label.setText(text)
        # Force redraw
        self.update()

    def advance(self):
        """Advance animation"""
        self._time += 0.02
        self.update()

    def _get_base_color(self):
        """Get base color based on current state"""
        if self.current_state == "idle":
            return self.COLOR_IDLE
        elif self.current_state == "listening":
            return self.COLOR_LISTENING
        elif self.current_state == "thinking":
            return self.COLOR_THINKING
        elif self.current_state == "speaking":
            return self.COLOR_SPEAKING
        elif self.current_state == "error":
            return self.COLOR_ERROR
        return self.COLOR_IDLE

    def _make_color(self, t: float) -> QColor:
        """
        Create color based on intensity and current state
        Black -> Deep Color -> Light Color -> White
        """
        base_r, base_g, base_b = self._get_base_color()

        t = max(0.0, min(1.0, t))
        if t < 0.35:
            # Black to deep base color
            k = t / 0.35
            r = 0 + base_r * k
            g = 0 + base_g * k
            b = 0 + base_b * k
        elif t < 0.75:
            # Deep color to light purple/color
            k = (t - 0.35) / 0.4
            r = base_r + (180 - base_r) * k
            g = base_g + (120 - base_g) * k
            b = base_b + (255 - base_b) * k
        else:
            # Light color to white
            k = (t - 0.75) / 0.25
            r = 180 + (255 - 180) * k
            g = 120 + (255 - 120) * k
            b = 255 + (255 - 255) * k
        return QColor(int(r), int(g), int(b))

    def paintEvent(self, event):
        """Paint the beautiful glowing cinematic orb"""
        _ = event
        w = self.orb_size
        h = self.orb_size
        size = min(w, h)
        radius = size * 0.45
        center = QPointF(w / 2.0, h / 2.0)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Clear canvas to transparent
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Orb base with breathing scale
        scale = 1.0 + 0.02 * math.sin(self._time * 0.7)
        orb_radius = radius * scale

        orb_path = QPainterPath()
        orb_path.addEllipse(center, orb_radius, orb_radius)

        # Outer glow (state-based color)
        base_r, base_g, base_b = self._get_base_color()
        glow_gradient = QRadialGradient(center, orb_radius * 1.4)
        glow_gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        glow_gradient.setColorAt(0.7, QColor(base_r + 30, base_g + 30, base_b + 50, 120))
        glow_gradient.setColorAt(1.0, QColor(base_r + 10, base_g + 10, base_b + 20, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, orb_radius * 1.4, orb_radius * 1.4)

        # Inner dark rim (glass thickness)
        rim_gradient = QRadialGradient(center, orb_radius)
        rim_gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        rim_gradient.setColorAt(0.8, QColor(0, 0, 0, 180))
        rim_gradient.setColorAt(1.0, QColor(0, 0, 0, 255))
        painter.setBrush(QBrush(rim_gradient))
        painter.setClipPath(orb_path)
        painter.drawEllipse(center, orb_radius, orb_radius)

        # Internal plasma with moving focal point
        fx = center.x() + orb_radius * 0.25 * math.sin(self._time * 0.9)
        fy = center.y() + orb_radius * 0.35 * math.cos(self._time * 0.7)
        plasma = QRadialGradient(QPointF(fx, fy), orb_radius * 1.2)
        plasma.setColorAt(0.0, self._make_color(1.0))    # white-ish core
        plasma.setColorAt(0.25, self._make_color(0.8))   # light color
        plasma.setColorAt(0.55, self._make_color(0.55))  # mid color
        plasma.setColorAt(0.85, self._make_color(0.25))  # deep color
        plasma.setColorAt(1.0, QColor(0, 0, 0, 255))     # edge fade

        painter.setBrush(QBrush(plasma))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(orb_path)

        # Floating blob highlights
        for phase, r_scale, alpha in [
            (0.0, 0.30, 120),
            (2.1, 0.20, 90),
            (4.3, 0.18, 80),
        ]:
            angle = self._time * 0.5 + phase
            bx = center.x() + orb_radius * 0.4 * math.cos(angle)
            by = center.y() + orb_radius * 0.3 * math.sin(angle * 1.3)
            blob_center = QPointF(bx, by)
            blob_grad = QRadialGradient(blob_center, orb_radius * r_scale)
            col = self._make_color(0.8)
            col.setAlpha(alpha)
            blob_grad.setColorAt(0.0, col)
            blob_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(blob_grad))
            painter.drawEllipse(blob_center, orb_radius * r_scale, orb_radius * r_scale)

        # Surface reflections (glass sheen)
        # Main static highlight
        highlight_path = QPainterPath()
        rx = orb_radius * 0.5
        ry = orb_radius * 0.3
        highlight_center = QPointF(center.x() - orb_radius * 0.25,
                                   center.y() - orb_radius * 0.25)
        highlight_path.addEllipse(highlight_center, rx, ry)
        highlight_grad = QRadialGradient(highlight_center, rx)
        highlight_grad.setColorAt(0.0, QColor(255, 255, 255, 180))
        highlight_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight_grad))
        painter.drawPath(highlight_path)

        # Sliding reflection band
        band_path = QPainterPath()
        band_radius = orb_radius * 1.1
        band_center = QPointF(center.x() + orb_radius * 0.1 * math.sin(self._time * 0.3),
                              center.y() - orb_radius * 0.1)
        band_path.addEllipse(band_center, band_radius * 0.8, band_radius * 0.25)
        band_grad = QRadialGradient(band_center, band_radius)
        band_grad.setColorAt(0.0, QColor(255, 255, 255, 90))
        band_grad.setColorAt(0.4, QColor(255, 255, 255, 40))
        band_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(band_grad))
        painter.drawPath(band_path)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on orb area (not buttons/input)
            if event.position().y() < self.orb_size:
                self.dragging = True
                self.drag_start = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start)

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def set_state_idle(self):
        """Set orb to idle state"""
        self.current_state = "idle"

    def set_state_listening(self):
        """Set orb to listening state"""
        self.current_state = "listening"

    def set_state_thinking(self):
        """Set orb to thinking state"""
        self.current_state = "thinking"

    def set_state_speaking(self):
        """Set orb to speaking state"""
        self.current_state = "speaking"

    def set_state_error(self):
        """Set orb to error state"""
        self.current_state = "error"
        # Flash error briefly then return to idle
        QTimer.singleShot(2000, self.set_state_idle)

    def closeEvent(self, event):
        """Clean up on close"""
        self.timer.stop()
        event.accept()
