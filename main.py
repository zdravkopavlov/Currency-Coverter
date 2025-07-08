import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QPainterPath

EXCHANGE_RATE = 1.95583

class CurrencyConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Window state
        self.input_value = ""
        self.bgn_to_eur = True
        self.dragging = False
        self.drag_position = QPoint()

        # Widgets
        self.input_label = QLabel("0.00 лв.", self)
        self.input_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.input_label.setAlignment(Qt.AlignCenter)

        self.switch_button = QPushButton("⇄", self)
        self.switch_button.setFixedSize(48, 48)
        self.switch_button.setFont(QFont("Arial", 24))
        self.switch_button.setCursor(Qt.PointingHandCursor)
        self.switch_button.setStyleSheet(
            "QPushButton { border: none; background: #eeeeee; border-radius: 24px; }"
            "QPushButton:hover { background: #cccccc; }"
        )
        self.switch_button.clicked.connect(self.toggle_direction)

        self.output_label = QLabel("€0.00", self)
        self.output_label.setFont(QFont("Arial", 32))
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setStyleSheet("color: #444444;")

        # Layouts
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(32, 32, 32, 32)
        v_layout.setSpacing(16)
        v_layout.addWidget(self.input_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.switch_button)
        btn_layout.addStretch()
        v_layout.addLayout(btn_layout)

        v_layout.addWidget(self.output_label)
        self.setLayout(v_layout)

        self.setMinimumWidth(340)
        self.setMinimumHeight(240)
        self.setMaximumWidth(360)
        self.setMaximumHeight(260)

        self.update_labels()

    def paintEvent(self, event):
        # Rounded, drop-shadowed background
        path = QPainterPath()
        rect = QRectF(self.rect().adjusted(4, 4, -4, -4))  # Convert to QRectF
        path.addRoundedRect(rect, 32, 32)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Shadow
        painter.fillPath(path, QBrush(QColor(50, 50, 50, 60)))
        # Main white panel
        rect = QRectF(self.rect())  # Convert to QRectF
        path = QPainterPath()
        path.addRoundedRect(rect, 32, 32)
        painter.fillPath(path, QBrush(QColor("#fafafa")))

    def toggle_direction(self):
        self.bgn_to_eur = not self.bgn_to_eur
        self.input_value = ""
        self.update_labels()

    def keyPressEvent(self, event):
        key = event.key()
        # Allow numbers, comma, dot, backspace, escape
        if Qt.Key_0 <= key <= Qt.Key_9:
            if len(self.input_value) < 10:  # Limit length
                self.input_value += event.text()
        elif key == Qt.Key_Backspace:
            self.input_value = self.input_value[:-1]
        elif key in (Qt.Key_Comma, Qt.Key_Period):
            if '.' not in self.input_value:
                self.input_value += '.'
        elif key == Qt.Key_Escape:
            self.close()
            return
        self.update_labels()

    def update_labels(self):
        # Show formatted input and output
        try:
            val = float(self.input_value) if self.input_value else 0.0
        except ValueError:
            val = 0.0

        if self.bgn_to_eur:
            input_str = f"{val:.2f} лв."
            eur = round(val / EXCHANGE_RATE + 1e-8, 2)
            output_str = f"€{eur:.2f}"
        else:
            input_str = f"€{val:.2f}"
            bgn = round(val * EXCHANGE_RATE + 1e-8, 2)
            output_str = f"{bgn:.2f} лв."
        self.input_label.setText(input_str)
        self.output_label.setText(output_str)

    # Custom dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Only allow dragging if not over the switch button
            if not self.switch_button.underMouse():
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CurrencyConverter()
    window.setWindowTitle("Currency Converter")
    window.show()
    sys.exit(app.exec_())
