# change_widget.py

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from calculator import calculate_change

class ChangeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.price_bgn = 0.0   # Set this from outside when showing this widget!
        self.paid_bgn = ""
        self.minimal_mode = False

        # Fonts
        self.font_big = QFont("Arial", 24, QFont.Bold)
        self.font_medium = QFont("Arial", 18)
        self.font_small = QFont("Arial", 12)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(10, 5, 10, 5)

        self.given_label = QLabel("Дадена сума:")
        self.given_label.setFont(self.font_small)
        self.layout.addWidget(self.given_label)

        self.paid_label = QLabel("0.00 лв.")
        self.paid_label.setAlignment(Qt.AlignCenter)
        self.paid_label.setFont(self.font_big)
        self.layout.addWidget(self.paid_label)

        self.rest_label = QLabel("Ресто:")
        self.rest_label.setFont(self.font_small)
        self.layout.addWidget(self.rest_label)

        self.change_label = QLabel("€0.00")
        self.change_label.setAlignment(Qt.AlignCenter)
        self.change_label.setFont(self.font_big)
        self.layout.addWidget(self.change_label)

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
            self.paid_label.setFont(self.font_medium)
            self.change_label.setFont(self.font_medium)
            self.given_label.setVisible(False)
            self.rest_label.setVisible(False)
            self.version_label.setVisible(False)
        else:
            self.setFixedSize(250, 220)
            self.paid_label.setFont(self.font_big)
            self.change_label.setFont(self.font_big)
            self.given_label.setVisible(True)
            self.rest_label.setVisible(True)
            self.version_label.setVisible(True)
        self.update_labels()

    def set_price_bgn(self, price_bgn):
        """Call this to set the price before showing this widget!"""
        self.price_bgn = price_bgn
        self.paid_bgn = ""
        self.update_labels()

    def update_labels(self):
        try:
            paid_val = float(self.paid_bgn) if self.paid_bgn else 0.0
        except ValueError:
            paid_val = 0.0
        self.paid_label.setText(f"{paid_val:.2f} лв.")
        if paid_val > 0 and self.price_bgn > 0:
            change_eur = calculate_change(self.price_bgn, paid_val)
            self.change_label.setText(f"€{change_eur:.2f}")
        else:
            self.change_label.setText("€0.00")

    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key_0 <= key <= Qt.Key_9:
            if len(self.paid_bgn) < 10:
                self.paid_bgn += event.text()
                self.update_labels()
        elif key == Qt.Key_Backspace:
            self.paid_bgn = self.paid_bgn[:-1]
            self.update_labels()
        elif key in (Qt.Key_Comma, Qt.Key_Period):
            if '.' not in self.paid_bgn:
                self.paid_bgn += '.'
                self.update_labels()
        elif key == Qt.Key_Escape:
            self.paid_bgn = ""
            self.update_labels()
        elif key in (Qt.Key_Space, Qt.Key_Tab):
            self.clearFocus()
            self.parentWidget().setFocus()
        else:
            super().keyPressEvent(event)
