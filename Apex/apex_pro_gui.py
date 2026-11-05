#!/usr/bin/env python3
"""
APEX PRO - Premium Audio Interface Control GUI
Built with PyQt6 - Professional metering with realistic ballistics
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush, QFont


class AudioMeter(QWidget):
    """Professional audio meter with realistic ballistics"""
    
    def __init__(self, orientation='vertical', parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.level = 0.0  # Current level (0.0 to 1.0)
        self.peak = 0.0   # Peak level
        self.peak_hold_time = 0
        
        # Ballistics parameters (professional audio standards)
        self.attack_time = 0.003  # 3ms attack
        self.release_time = 0.3   # 300ms release
        self.peak_hold_duration = 60  # Frames to hold peak
        
        if orientation == 'vertical':
            self.setMinimumSize(24, 120)
        else:
            self.setMinimumSize(120, 24)
            
    def set_level(self, target_level):
        """Set target level with realistic ballistics"""
        # Clamp target level
        target_level = max(0.0, min(1.0, target_level))
        
        # Apply attack/release ballistics
        if target_level > self.level:
            # Fast attack
            self.level += (target_level - self.level) * self.attack_time * 10
        else:
            # Slower release
            self.level += (target_level - self.level) * self.release_time * 0.05
            
        # Update peak with hold
        if self.level > self.peak:
            self.peak = self.level
            self.peak_hold_time = self.peak_hold_duration
        else:
            if self.peak_hold_time > 0:
                self.peak_hold_time -= 1
            else:
                # Decay peak slowly
                self.peak *= 0.95
                
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(20, 20, 20))
        
        # Create gradient for meter fill
        gradient = QLinearGradient()
        if self.orientation == 'vertical':
            gradient.setStart(0, self.height())
            gradient.setFinalStop(0, 0)
        else:
            gradient.setStart(0, 0)
            gradient.setFinalStop(self.width(), 0)
            
        # Green -> Yellow -> Orange -> Red gradient
        gradient.setColorAt(0.0, QColor(0, 230, 118))   # Green
        gradient.setColorAt(0.6, QColor(0, 230, 118))   # Green
        gradient.setColorAt(0.75, QColor(255, 171, 0))  # Yellow
        gradient.setColorAt(0.9, QColor(255, 109, 0))   # Orange
        gradient.setColorAt(1.0, QColor(255, 23, 68))   # Red
        
        # Draw meter fill
        if self.orientation == 'vertical':
            fill_height = int(self.height() * self.level)
            painter.fillRect(0, self.height() - fill_height, 
                           self.width(), fill_height, gradient)
            
            # Draw peak indicator
            if self.peak > 0.01:
                peak_y = int(self.height() * (1.0 - self.peak))
                painter.setPen(QPen(QColor(255, 23, 68), 2))
                painter.drawLine(0, peak_y, self.width(), peak_y)
        else:
            fill_width = int(self.width() * self.level)
            painter.fillRect(0, 0, fill_width, self.height(), gradient)
            
            # Draw peak indicator
            if self.peak > 0.01:
                peak_x = int(self.width() * self.peak)
                painter.setPen(QPen(QColor(255, 23, 68), 2))
                painter.drawLine(peak_x, 0, peak_x, self.height())
                
        # Border
        painter.setPen(QPen(QColor(64, 64, 64), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))


class IOChannel(QFrame):
    """Input/Output channel with metering"""
    
    clicked = pyqtSignal()
    
    def __init__(self, name, io_type, active=False, parent=None):
        super().__init__(parent)
        self.name = name
        self.io_type = io_type
        self.is_active = active
        self.signal_level = 0.0
        
        self.setup_ui()
        self.setStyleSheet(self.get_stylesheet())
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        name_label = QLabel(self.name)
        name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #ffffff;")
        
        type_label = QLabel(self.io_type)
        type_label.setStyleSheet("""
            font-size: 10px; 
            padding: 3px 8px; 
            background: #141414;
            border-radius: 4px;
            color: #707070;
        """)
        
        header.addWidget(name_label)
        header.addStretch()
        header.addWidget(type_label)
        layout.addLayout(header)
        
        # Meter and dB display
        meter_layout = QHBoxLayout()
        self.meter = AudioMeter('horizontal')
        self.db_label = QLabel("-∞ dB")
        self.db_label.setStyleSheet("""
            font-size: 11px;
            color: #b0b0b0;
            font-family: 'Monaco', monospace;
            min-width: 50px;
        """)
        self.db_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        meter_layout.addWidget(self.meter, 1)
        meter_layout.addWidget(self.db_label)
        layout.addLayout(meter_layout)
        
    def get_stylesheet(self):
        border_color = "rgba(0, 229, 255, 1.0)" if self.is_active else "rgba(255, 255, 255, 0.1)"
        bg_color = "rgba(0, 229, 255, 0.05)" if self.is_active else "rgba(20, 20, 20, 0.8)"
        
        return f"""
            IOChannel {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                margin-bottom: 8px;
            }}
            IOChannel:hover {{
                border: 1px solid rgba(0, 229, 255, 0.8);
                background: rgba(0, 229, 255, 0.08);
            }}
        """
        
    def update_level(self, level):
        """Update meter with new level"""
        self.signal_level = level
        self.meter.set_level(level)
        
        # Update dB display
        if level < 0.001:
            db_str = "-∞ dB"
        else:
            db = 20 * np.log10(level)
            db_str = f"{db:.1f} dB"
        self.db_label.setText(db_str)
        
    def mousePressEvent(self, event):
        self.is_active = not self.is_active
        self.setStyleSheet(self.get_stylesheet())
        self.clicked.emit()


class ChannelStrip(QFrame):
    """Premium channel strip with fader and metering"""
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.fader_level = 0.7  # Unity gain at 0.7 (0 dB)
        self.vu_level = 0.0
        self.muted = False
        self.soloed = False
        self.recording = False
        
        self.setup_ui()
        self.setStyleSheet("""
            ChannelStrip {
                background: rgba(20, 20, 20, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 16px 12px;
            }
            ChannelStrip:hover {
                background: rgba(20, 20, 20, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
        """)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Channel label
        label = QLabel(self.name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #b0b0b0;
            margin-bottom: 8px;
        """)
        layout.addWidget(label)
        
        # VU Meter
        self.vu_meter = AudioMeter('vertical')
        layout.addWidget(self.vu_meter)
        
        # Fader value display
        self.fader_label = QLabel("0.0 dB")
        self.fader_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fader_label.setStyleSheet("""
            font-size: 10px;
            color: #b0b0b0;
            font-family: 'Monaco', monospace;
        """)
        layout.addWidget(self.fader_label)
        
        # Control buttons
        self.rec_btn = QPushButton("REC")
        self.solo_btn = QPushButton("SOLO")
        self.mute_btn = QPushButton("MUTE")
        
        for btn in [self.rec_btn, self.solo_btn, self.mute_btn]:
            btn.setFixedHeight(24)
            layout.addWidget(btn)
            
        self.rec_btn.clicked.connect(self.toggle_record)
        self.solo_btn.clicked.connect(self.toggle_solo)
        self.mute_btn.clicked.connect(self.toggle_mute)
        
        self.update_button_styles()
        
    def update_button_styles(self):
        base_style = """
            QPushButton {
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: #141414;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                color: #707070;
            }
            QPushButton:hover {
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
        """
        
        rec_style = base_style
        if self.recording:
            rec_style = """
                QPushButton {
                    background: #ff1744;
                    border: 1px solid #ff1744;
                    color: white;
                    border-radius: 6px;
                    font-size: 10px;
                    font-weight: 600;
                }
            """
            
        solo_style = base_style
        if self.soloed:
            solo_style = """
                QPushButton {
                    background: #00e676;
                    border: 1px solid #00e676;
                    color: black;
                    border-radius: 6px;
                    font-size: 10px;
                    font-weight: 600;
                }
            """
            
        mute_style = base_style
        if self.muted:
            mute_style = """
                QPushButton {
                    background: #ffab00;
                    border: 1px solid #ffab00;
                    color: black;
                    border-radius: 6px;
                    font-size: 10px;
                    font-weight: 600;
                }
            """
            
        self.rec_btn.setStyleSheet(rec_style)
        self.solo_btn.setStyleSheet(solo_style)
        self.mute_btn.setStyleSheet(mute_style)
        
    def toggle_record(self):
        self.recording = not self.recording
        self.update_button_styles()
        
    def toggle_solo(self):
        self.soloed = not self.soloed
        self.update_button_styles()
        
    def toggle_mute(self):
        self.muted = not self.muted
        self.update_button_styles()
        
    def update_vu(self, level):
        """Update VU meter with realistic ballistics"""
        if not self.muted:
            self.vu_meter.set_level(level)


class ApexProGUI(QMainWindow):
    """Main Apex Pro application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("APEX PRO - Premium Audio Interface Control")
        self.setGeometry(100, 100, 1600, 900)
        
        # Audio simulation state
        self.input_signals = {}
        self.output_signals = {}
        self.channel_signals = {}
        
        # Create signal generators with different characteristics
        self.signal_phase = 0
        
        self.setup_ui()
        self.setup_timer()
        
        # Apply global stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background: #000000;
            }
            QScrollBar:vertical {
                border: none;
                background: #141414;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #2e2e2e;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Main content area
        content = QHBoxLayout()
        content.setSpacing(0)
        
        # Input panel
        input_panel = self.create_input_panel()
        content.addWidget(input_panel)
        
        # Mixer area
        mixer_area = self.create_mixer_area()
        content.addWidget(mixer_area, 1)
        
        # Output panel
        output_panel = self.create_output_panel()
        content.addWidget(output_panel)
        
        main_layout.addLayout(content)
        
    def create_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(64)
        bar.setStyleSheet("""
            QFrame {
                background: #0a0a0a;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 12)
        
        # Logo
        logo = QLabel("APEX PRO")
        logo.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00e5ff, stop:1 #7b2ff7);
        """)
        layout.addWidget(logo)
        
        # Status
        status = QLabel("● Antelope Audio Orion 32+ Connected")
        status.setStyleSheet("color: #b0b0b0; font-size: 13px;")
        layout.addWidget(status)
        
        layout.addStretch()
        
        # Sample rate info
        info_layout = QHBoxLayout()
        for text in ["48 kHz", "24-bit", "Buffer: 128"]:
            label = QLabel(text)
            label.setStyleSheet("""
                background: #141414;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 4px 12px;
                color: #b0b0b0;
                font-size: 13px;
            """)
            info_layout.addWidget(label)
            
        layout.addLayout(info_layout)
        
        return bar
        
    def create_input_panel(self):
        panel = QFrame()
        panel.setFixedWidth(420)
        panel.setStyleSheet("""
            QFrame {
                background: #0f0f0f;
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid rgba(255, 255, 255, 0.08);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        title = QLabel("INPUTS")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: white;")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Scroll area for inputs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        scroll_layout.setSpacing(0)
        
        # Create input channels
        inputs_data = [
            ("Mic 1", "XLR", True),
            ("Mic 2", "XLR", True),
            ("Line 1-2", "TRS", False),
            ("Line 3-4", "TRS", True),
            ("ADAT 1-2", "Digital", False),
            ("ADAT 3-4", "Digital", False),
            ("SPDIF L-R", "Digital", True),
            ("USB 1-2", "USB", True),
        ]
        
        for name, io_type, active in inputs_data:
            channel = IOChannel(name, io_type, active)
            scroll_layout.addWidget(channel)
            self.input_signals[name] = channel
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return panel
        
    def create_mixer_area(self):
        area = QFrame()
        area.setStyleSheet("background: #0a0a0a;")
        
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid rgba(255, 255, 255, 0.08);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        title = QLabel("CHANNEL STRIPS")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: white;")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Scroll area for channel strips
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(12)
        
        # Create channel strips
        channel_names = ["Vocal", "Guitar", "Keys", "Drums", "Bass", "FX 1", "FX 2", "Aux"]
        
        for name in channel_names:
            strip = ChannelStrip(name)
            strip.setFixedWidth(100)
            scroll_layout.addWidget(strip)
            self.channel_signals[name] = strip
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return area
        
    def create_output_panel(self):
        panel = QFrame()
        panel.setFixedWidth(380)
        panel.setStyleSheet("""
            QFrame {
                background: #0f0f0f;
                border-left: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid rgba(255, 255, 255, 0.08);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        title = QLabel("OUTPUTS")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: white;")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Scroll area for outputs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        scroll_layout.setSpacing(0)
        
        # Create output channels
        outputs_data = [
            ("Monitor L-R", "TRS", True),
            ("Headphone 1", "TRS", True),
            ("Headphone 2", "TRS", False),
            ("Line Out 1-2", "TRS", True),
            ("ADAT Out 1-2", "Digital", False),
            ("SPDIF Out", "Digital", True),
        ]
        
        for name, io_type, active in outputs_data:
            channel = IOChannel(name, io_type, active)
            scroll_layout.addWidget(channel)
            self.output_signals[name] = channel
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return panel
        
    def setup_timer(self):
        """Setup timer for realistic audio signal simulation"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_meters)
        self.timer.start(33)  # ~30 FPS for smooth animation
        
    def update_meters(self):
        """Update all meters with realistic audio signal simulation"""
        self.signal_phase += 0.02
        
        # Generate realistic signal levels for active inputs
        for name, channel in self.input_signals.items():
            if channel.is_active:
                # Create different signal characteristics for different channels
                base_freq = hash(name) % 10 * 0.1
                
                # Simulate audio material with envelope
                envelope = 0.5 + 0.3 * np.sin(self.signal_phase * 0.5 + base_freq)
                signal = 0.4 + 0.3 * np.sin(self.signal_phase * 3 + base_freq)
                
                # Add occasional peaks (like transients)
                if np.random.random() < 0.02:  # 2% chance of peak
                    signal += 0.3
                    
                level = envelope * signal
                level = max(0.0, min(1.0, level))
                
                channel.update_level(level)
            else:
                channel.update_level(0.0)
                
        # Update channel strips
        for name, strip in self.channel_signals.items():
            base_freq = hash(name) % 10 * 0.15
            
            # More musical envelope
            envelope = 0.6 + 0.25 * np.sin(self.signal_phase * 0.3 + base_freq)
            signal = 0.5 + 0.35 * np.sin(self.signal_phase * 2.5 + base_freq)
            
            # Occasional louder passages
            if np.random.random() < 0.05:
                signal += 0.2
                
            level = envelope * signal
            level = max(0.0, min(1.0, level))
            
            strip.update_vu(level)
            
        # Update outputs (similar to inputs but with different phase)
        for name, channel in self.output_signals.items():
            if channel.is_active:
                base_freq = hash(name) % 10 * 0.12
                envelope = 0.55 + 0.25 * np.sin(self.signal_phase * 0.4 + base_freq)
                signal = 0.45 + 0.3 * np.sin(self.signal_phase * 2.8 + base_freq)
                
                if np.random.random() < 0.03:
                    signal += 0.25
                    
                level = envelope * signal
                level = max(0.0, min(1.0, level))
                
                channel.update_level(level)
            else:
                channel.update_level(0.0)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern cross-platform style
    
    # Set application font
    font = QFont("Inter", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    window = ApexProGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
