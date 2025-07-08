from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QRadioButton, QButtonGroup, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QBrush, QIcon


class CarouselWidget(QWidget):
    """Borderless, draggable window containing a fade-animated multi-page stack."""

    def __init__(self, pages):
        super().__init__()

        # -------- window flags / appearance --------
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("BGN/EUR Converter")
        self.resize(350, 250)
        self.setStyleSheet("background:#fafafa; border-radius:24px;")

        # -------- stacked pages --------
        self.pages = QStackedWidget()
        for page in pages:
            self.pages.addWidget(page)

        # -------- indicator dots --------
        self.button_group = QButtonGroup(self)
        self.indicator_layout = QHBoxLayout()
        self.indicator_layout.setSpacing(2)
        self.indicator_layout.setContentsMargins(0, 6, 0, 0)
        self.indicator_layout.addStretch()

        self.indicators = []
        for i in range(len(pages)):
            dot = QRadioButton()
            dot.setCursor(Qt.PointingHandCursor)
            dot.setFocusPolicy(Qt.NoFocus)
            dot.setStyleSheet("""
                QRadioButton::indicator        {width:4px; height:4px;
                                                border-radius:6px;
                                                border:1px solid #aaa;
                                                background:#bbb;
                                                margin:0 3px;}
                QRadioButton::indicator:checked{background:#0099ff;
                                                border:1px solid #0077cc;}
                QRadioButton::indicator:focus,
                QRadioButton:focus             {outline:none; border:none;}
            """)
            self.button_group.addButton(dot, i)
            self.indicators.append(dot)
            self.indicator_layout.addWidget(dot)
        self.indicator_layout.addStretch()
        self.indicators[0].setChecked(True)
        self.button_group.buttonClicked[int].connect(self.go_to_page)

        # -------- main layout --------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 12)
        main_layout.setSpacing(4)
        main_layout.addWidget(self.pages)
        main_layout.addLayout(self.indicator_layout)

        # -------- fade effect on content only --------
        self.fade_effect = QGraphicsOpacityEffect()
        self.pages.setGraphicsEffect(self.fade_effect)
        self.anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._target_index = 0
        self.anim.finished.connect(self._do_switch_page)

        # -------- draggable support --------
        self.dragging = False

    # ---------- navigation ----------
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

    # ---------- custom painting (solid rounded panel) ----------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect())        # convert to QRectF
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24) # now OK
        painter.fillPath(path, QBrush(QColor("#fafafa")))

    # ---------- draggable window ----------
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
