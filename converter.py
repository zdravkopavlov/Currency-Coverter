from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

EXCHANGE_RATE = 1.95583

class ConverterPage(QWidget):
    """BGN ⇄ EUR live converter page (keyboard-only input)."""

    def __init__(self):
        super().__init__()

        self.input_value = ""
        self.bgn_to_eur = True

        # Layout
        layout = QVBoxLayout(self)
        layout.addStretch()

        self.input_label = QLabel("0.00 лв.")
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setStyleSheet("font-size:24px; color:#888; font-weight:bold;")
        layout.addWidget(self.input_label)

        # Switch button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.switch_button = QPushButton("⇄")
        self.switch_button.setStyleSheet(
            "QPushButton {font-size:32px; color:#888; border:none; background:#eeeeee; "
            "border-radius:24px;} "
            "QPushButton:hover {background:#cccccc;}"
        )
        self.switch_button.setFixedSize(48, 48)
        self.switch_button.setCursor(Qt.PointingHandCursor)
        self.switch_button.clicked.connect(self.toggle_direction)
        btn_layout.addWidget(self.switch_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.output_label = QLabel("€0.00")
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setStyleSheet("font-size:36px; color:#444;")
        layout.addWidget(self.output_label)
        layout.addStretch()

        self.setFocusPolicy(Qt.StrongFocus)

    def toggle_direction(self):
        self.bgn_to_eur = not self.bgn_to_eur
        self.input_value = ""
        self.update_labels()

    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key_0 <= key <= Qt.Key_9:
            if len(self.input_value) < 10:
                self.input_value += event.text()
        elif key == Qt.Key_Backspace:
            self.input_value = self.input_value[:-1]
        elif key in (Qt.Key_Comma, Qt.Key_Period):
            if '.' not in self.input_value:
                self.input_value += '.'
        self.update_labels()

    def update_labels(self):
        try:
            val = float(self.input_value) if self.input_value else 0.0
        except ValueError:
            val = 0.0
        if self.bgn_to_eur:
            self.input_label.setText(f"{val:.2f} лв.")
            eur = round(val / EXCHANGE_RATE + 1e-8, 2)
            self.output_label.setText(f"€{eur:.2f}")
        else:
            self.input_label.setText(f"€{val:.2f}")
            bgn = round(val * EXCHANGE_RATE + 1e-8, 2)
            self.output_label.setText(f"{bgn:.2f} лв.")

    # For Escape handling from the carousel
    def clear_if_not_zero(self):
        """Returns True if cleared, False if already zeroed."""
        if self.input_value and float(self.input_value or 0) != 0:
            self.input_value = ""
            self.update_labels()
            return True
        return False
