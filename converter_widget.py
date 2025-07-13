# converter_widget.py

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from calculator import bgn_to_eur, eur_to_bgn

class ConverterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bgn_to_eur_mode = True
        self.input_value = ""
        self.minimal_mode = False

        # Fonts
        self.font_big = QFont("Arial", 24, QFont.Bold)
        self.font_medium = QFont("Arial", 18)
        self.font_small = QFont("Arial", 12)

        # Layouts
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(10, 5, 10, 5)

        # Input label
        self.input_label = QLabel("0.00 лв.")
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setFont(self.font_big)
        self.layout.addWidget(self.input_label)

        # Switch button
        self.switch_button = QPushButton("⇄")
        self.switch_button.setFixedSize(48, 48)
        self.switch_button.setStyleSheet("""
            QPushButton {
                font-size:32px;
                color:#888;
                border:none;
                background:#aaaaaa;
                border-radius:24px;
            }
            QPushButton:hover {
                background:#cccccc;
            }
        """)
        self.switch_button.clicked.connect(self.toggle_direction)
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(self.switch_button)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)

        # Output label
        self.output_label = QLabel("€0.00")
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setFont(self.font_big)
        self.layout.addWidget(self.output_label)

        # Version label (shown only in normal mode)
        self.version_label = QLabel("версия 2.2.7")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setFont(self.font_small)
        self.layout.addWidget(self.version_label)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        self.set_mode(self.minimal_mode)
        self.update_labels()

    def set_mode(self, minimal):
        self.minimal_mode = minimal
        if minimal:
            self.setFixedSize(300, 50)
            self.input_label.setFont(self.font_medium)
            self.output_label.setFont(self.font_medium)
            self.switch_button.setFixedSize(24, 24)
            self.version_label.setVisible(False)
        else:
            self.setFixedSize(250, 220)
            self.input_label.setFont(self.font_big)
            self.output_label.setFont(self.font_big)
            self.switch_button.setFixedSize(48, 48)
            self.version_label.setVisible(True)
        self.update_labels()

    def toggle_direction(self):
        self.bgn_to_eur_mode = not self.bgn_to_eur_mode
        self.input_value = ""
        self.update_labels()

    def update_labels(self):
        try:
            val = float(self.input_value) if self.input_value else 0.0
        except ValueError:
            val = 0.0
        output = "0.00"
        if self.bgn_to_eur_mode:
            self.input_label.setText(f"{val:.2f} лв.")
            eur = bgn_to_eur(val)
            output = f"{eur:.2f}"
            self.output_label.setText(f"€{output}")
        else:
            self.input_label.setText(f"€{val:.2f}")
            bgn = eur_to_bgn(val)
            output = f"{bgn:.2f}"
            self.output_label.setText(f"{output} лв.")

    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key_0 <= key <= Qt.Key_9:
            if len(self.input_value) < 10:
                self.input_value += event.text()
                self.update_labels()
        elif key == Qt.Key_Backspace:
            self.input_value = self.input_value[:-1]
            self.update_labels()
        elif key in (Qt.Key_Comma, Qt.Key_Period):
            if '.' not in self.input_value:
                self.input_value += '.'
                self.update_labels()
        elif key == Qt.Key_Escape:
            self.input_value = ""
            self.update_labels()
        elif key in (Qt.Key_Space, Qt.Key_Tab):
            # Let the controller (main window) handle page switching
            self.clearFocus()
            self.parentWidget().setFocus()
        else:
            super().keyPressEvent(event)
