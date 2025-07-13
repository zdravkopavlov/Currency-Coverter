# converter_widget.py

VERSION = "2.3.0"

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from calculator import bgn_to_eur, eur_to_bgn

class ConverterWidget(QWidget):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings or {}
        self.bgn_to_eur_mode = self.settings.get("last_direction_bgn_to_eur", True)
        self.input_value = ""
        self.minimal_mode = False
        self._open_updates_callback = None

        # Fonts
        self.font_big = QFont("Arial", 24, QFont.Bold)
        self.font_medium = QFont("Arial", 18)
        self.font_small = QFont("Arial", 12)

        # Input label (amount)
        self.input_label = QLabel("0.00 лв.")
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setFont(self.font_big)

        # Switch button
        self.switch_button = QPushButton("⇄")
        self.switch_button.setStyleSheet("""
            QPushButton {
                font-size:24px;
                color:#dddddd;
                border:none;
                background:#aaaaaa;
                border-radius:16px;
            }
            QPushButton:hover {
                background:#cccccc;
            }
        """)
        self.switch_button.clicked.connect(self.toggle_direction)

        # Output label (converted)
        self.output_label = QLabel("€0.00")
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setFont(self.font_big)

        # Version label (clickable, settings shortcut)
        self.version_label = QLabel(f"версия {VERSION}")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setFont(self.font_small)
        self.version_label.setCursor(Qt.PointingHandCursor)
        self.version_label.mousePressEvent = self._open_updates

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self._build_layout(self.minimal_mode)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
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

    @property
    def remember_direction_enabled(self):
        return self.settings.get("remember_last_direction", True)

    def set_mode(self, minimal):
        self.minimal_mode = minimal
        self._build_layout(minimal)
        self.update_labels()

    def _build_layout(self, minimal):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            elif item.layout():
                self._clear_sub_layout(item.layout())
        if minimal:
            self.setFixedSize(325, 50)
            self.input_label.setFont(self.font_medium)
            self.output_label.setFont(self.font_medium)
            self.input_label.setAlignment(Qt.AlignCenter)
            self.output_label.setAlignment(Qt.AlignCenter)
            self.switch_button.setFixedSize(32, 32)
            self.switch_button.setStyleSheet("""
                QPushButton {
                    font-size:18px;
                    color:#dddddd;
                    border:none;
                    background:#aaaaaa;
                    border-radius:16px;
                }
                QPushButton:hover {
                    background:#cccccc;
                }
            """)
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(10, 5, 10, 5)
            h_layout.setSpacing(8)
            h_layout.addStretch()
            h_layout.addWidget(self.input_label)
            h_layout.addWidget(self.switch_button)
            h_layout.addWidget(self.output_label)
            h_layout.addStretch()
            self.layout.addLayout(h_layout)
            self.switch_button.show()
            self.version_label.hide()
        else:
            self.setFixedSize(250, 220)
            self.input_label.setFont(self.font_big)
            self.output_label.setFont(self.font_big)
            self.input_label.setAlignment(Qt.AlignCenter)
            self.output_label.setAlignment(Qt.AlignCenter)
            self.switch_button.setFixedSize(48, 48)
            self.switch_button.setStyleSheet("""
                QPushButton {
                    font-size:32px;
                    color:#dddddd;
                    border:none;
                    background:#aaaaaa;
                    border-radius:24px;
                }
                QPushButton:hover {
                    background:#cccccc;
                }
            """)
            self.layout.addWidget(self.input_label)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(self.switch_button)
            btn_layout.addStretch()
            self.layout.addLayout(btn_layout)
            self.layout.addWidget(self.output_label)
            self.layout.addWidget(self.version_label)
            self.switch_button.show()
            self.version_label.show()

    def _clear_sub_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def toggle_direction(self):
        self.bgn_to_eur_mode = not self.bgn_to_eur_mode
        if self.remember_direction_enabled:
            self.settings["last_direction_bgn_to_eur"] = self.bgn_to_eur_mode
            from settings import save_settings
            save_settings(self.settings)
        self.input_value = ""
        self.update_labels()

    def update_labels(self):
        try:
            val = float(self.input_value) if self.input_value else 0.0
        except ValueError:
            val = 0.0
        if self.bgn_to_eur_mode:
            self.input_label.setText(f"{val:.2f} лв.")
            eur = bgn_to_eur(val)
            self.output_label.setText(f"€{eur:.2f}")
            result_text = f"{eur:.2f}"
        else:
            self.input_label.setText(f"€{val:.2f}")
            bgn = eur_to_bgn(val)
            self.output_label.setText(f"{bgn:.2f} лв.")
            result_text = f"{bgn:.2f}"
        if self.auto_copy_enabled:
            QApplication.clipboard().setText(result_text)

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
        elif key == Qt.Key_Space:
            self.toggle_direction()
        elif key == Qt.Key_Tab:
            self.clearFocus()
            self.parentWidget().setFocus()
        elif key == Qt.Key_A and not event.modifiers():
            self.clearFocus()
            self.parentWidget().setFocus()
        else:
            super().keyPressEvent(event)
