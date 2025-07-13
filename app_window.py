# app_window.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPainterPath, QBrush, QColor

class AppWindow(QWidget):
    def __init__(self, icon, window_title, always_on_top=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setWindowIcon(icon)
        self.setWindowFlags(Qt.FramelessWindowHint | (Qt.WindowStaysOnTopHint if always_on_top else Qt.Widget))
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.dragging = False
        self.drag_position = QPoint()
        self.stacked = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        painter.fillPath(path, QBrush(QColor("#fafafa")))  # You can adjust for dark mode if needed.

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def setCurrentIndex(self, idx):
        self.stacked.setCurrentIndex(idx)

    def currentIndex(self):
        return self.stacked.currentIndex()

    def addWidget(self, widget):
        self.stacked.addWidget(widget)

    def widget(self, idx):
        return self.stacked.widget(idx)
