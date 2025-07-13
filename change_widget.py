# change_widget.py

VERSION = "2.3.0"

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from calculator import calculate_change

class ChangeWidget(QWidget):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.price_bgn = 0.0
        self.paid_bgn = ""
        self.minimal_mode = False
        self._open_updates_callback = None
        self.settings = settings or {}

        # Fonts
        self.font_big = QFont("Arial", 24, QFont.Bold)
        self.font_medium = QFont("Arial", 18)
        self.font_small = QFont("Arial", 12)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(10, 5, 10, 5)

        self.given_label = QLabel("Дадена сума:")
        self.given_label.setFont(self.font_small)

        self.paid_label = QLabel("0.00 лв.")
        self.paid_label.setAlignment(Qt.AlignCenter)
        self.paid_label.setFont(self.font_big)

        self.rest_label = QLabel("Ресто:")
        self.rest_label.setFont(self.font_small)

        self.change_label = QLabel("€0.00")
        self.change_label.setAlignment(Qt.AlignCenter)
        self.change_label.setFont(self.font_big)

        self.version_label = QLabel(f"версия {VERSION}")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setFont(self.font_small)
        self.version_label.setCursor(Qt.PointingHandCursor)
        self.version_label.mousePressEvent = self._open_updates

        self.layout.addWidget(self.given_label)
        self.layout.addWidget(self.paid_label)
        self.layout.addWidget(self.rest_label)
        self.layout.addWidget(self.change_label)
        self.layout.addWidget(self.version_label)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        self.set_mode(self.minimal_mode)
        self.update_labels()

    def set_open_updates_callback(self, callback):
        self._open_updates_callback = callback

    def _open_updates(self, event):
        if self._open_updates_callback:
            self._open_updates_callback()

    def set_update_available(self, available):
        if available:
            self.version_label.setText("Налична е нова версия!")
        else:
            self.version_label.setText(f"версия {VERSION}")

    def set_version_label_color(self, color):
        self.version_label.setStyleSheet(f"color:{color};")

    @property
    def auto_copy_enabled(self):
        return self.settings.get("auto_copy_result", False)

    def set_mode(self, minimal):
        self.minimal_mode = minimal
        self._clear_layout()
        if minimal:
            self.setFixedSize(300, 50)
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(10, 5, 10, 5)
            h_layout.setSpacing(8)
            self.paid_label.setFont(self.font_medium)
            self.change_label.setFont(self.font_medium)
            h_layout.addWidget(self.paid_label)
            h_layout.addWidget(self.change_label)
            self.layout.addLayout(h_layout)
            self.given_label.hide()
            self.rest_label.hide()
            self.version_label.hide()
        else:
            self.setFixedSize(250, 220)
            self.paid_label.setFont(self.font_big)
            self.change_label.setFont(self.font_big)
            self.given_label.show()
            self.rest_label.show()
            self.version_label.show()
            self.layout.addWidget(self.given_label)
            self.layout.addWidget(self.paid_label)
            self.layout.addWidget(self.rest_label)
            self.layout.addWidget(self.change_label)
            self.layout.addWidget(self.version_label)
        self.update_labels()

    def _clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def set_price_bgn(self, price_bgn):
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
            result_text = f"{change_eur:.2f}"
        else:
            self.change_label.setText("€0.00")
            result_text = "0.00"
        if self.auto_copy_enabled:
            QApplication.clipboard().setText(result_text)

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
        elif key == Qt.Key_A and not event.modifiers():
            self.clearFocus()
            self.parentWidget().setFocus()
        else:
            super().keyPressEvent(event)
