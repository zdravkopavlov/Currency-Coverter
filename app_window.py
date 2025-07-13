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
        self._always_on_top = always_on_top

        # Default to light theme
        self.bg_color = "#fafafa"

        self.stacked = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked)
        self.setLayout(layout)

    def set_bg_color(self, color):
        self.bg_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        painter.fillPath(path, QBrush(QColor(self.bg_color)))
        if not getattr(self, "_always_on_top", True):
            border_color = QColor("#5a5a5a")
            border_width = 3
            shrink = border_width / 2
            border_rect = rect.adjusted(shrink, shrink, -shrink, -shrink)
            border_path = QPainterPath()
            border_path.addRoundedRect(border_rect, 24 - shrink, 24 - shrink)
            pen = painter.pen()
            pen.setColor(border_color)
            pen.setWidth(border_width)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawPath(border_path)
        else:
            painter.setPen(Qt.NoPen)

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

    def toggle_always_on_top(self):
        current = self.windowFlags()
        if current & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(current & ~Qt.WindowStaysOnTopHint)
            self._always_on_top = False
        else:
            self.setWindowFlags(current | Qt.WindowStaysOnTopHint)
            self._always_on_top = True
        self.show()
        self.update()
