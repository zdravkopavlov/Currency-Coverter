from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QRadioButton, QButtonGroup, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

class CarouselWidget(QWidget):
    def __init__(self, pages):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("BGN/EUR Converter")
        self.resize(400, 300)
        self.setStyleSheet("background: #fafafa; border-radius: 24px;")

        self.pages = QStackedWidget()
        for page in pages:
            self.pages.addWidget(page)

        self.button_group = QButtonGroup(self)
        self.indicator_layout = QHBoxLayout()
        self.indicator_layout.setSpacing(2)
        self.indicator_layout.setContentsMargins(0, 0, 0, 0)
        self.indicator_layout.addStretch()
        self.indicators = []
        for i in range(len(pages)):
            dot = QRadioButton()
            dot.setCursor(Qt.PointingHandCursor)
            dot.setFocusPolicy(Qt.NoFocus)
            dot.setStyleSheet("""
                QRadioButton::indicator {
                    width: 12px; height: 12px;
                    border-radius: 6px;
                    border: 1px solid #aaa;
                    background: #bbb;
                    margin: 0px 3px 0px 3px;
                }
                QRadioButton::indicator:checked {
                    background: #0099ff;
                    border: 1px solid #0077cc;
                }
                QRadioButton::indicator:focus, QRadioButton:focus {
                    outline: none; border: none;
                }
            """)
            self.button_group.addButton(dot, i)
            self.indicators.append(dot)
            self.indicator_layout.addWidget(dot)
        self.indicator_layout.addStretch()
        self.indicators[0].setChecked(True)
        self.button_group.buttonClicked[int].connect(self.go_to_page)

        layout = QVBoxLayout(self)
        layout.addWidget(self.pages)
        layout.addLayout(self.indicator_layout)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Fade effect
        self.fade_effect = QGraphicsOpacityEffect()
        self.pages.setGraphicsEffect(self.fade_effect)
        self.anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._target_index = 0
        self.anim.finished.connect(self._do_switch_page)

        # Draggable logic
        self.dragging = False

    def go_to_page(self, index):
        if index == self.pages.currentIndex() or self.anim.state() == QPropertyAnimation.Running:
            return
        self._target_index = index
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()

    def _do_switch_page(self):
        if self.fade_effect.opacity() == 0.0:
            self.pages.setCurrentIndex(self._target_index)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()

    # ---- Draggable window ----
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
