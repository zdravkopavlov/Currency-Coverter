from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QRadioButton, QButtonGroup, QGraphicsOpacityEffect, QSystemTrayIcon
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, QTimer
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QBrush

class CarouselWidget(QWidget):
    def __init__(self, pages):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("BGN/EUR Converter")
        self.resize(400, 340)
        self.setStyleSheet("background:#fafafa; border-radius:24px;")
        self.setFocusPolicy(Qt.StrongFocus)

        self.pages = QStackedWidget()
        for page in pages:
            self.pages.addWidget(page)

        # Indicator dots
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
                QRadioButton::indicator        {width:12px; height:12px;
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

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 12)
        main_layout.setSpacing(4)
        main_layout.addWidget(self.pages)
        main_layout.addLayout(self.indicator_layout)

        # Fade effect on content only
        self.fade_effect = QGraphicsOpacityEffect()
        self.pages.setGraphicsEffect(self.fade_effect)
        self.anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._target_index = 0
        self.anim.finished.connect(self._do_switch_page)

        # Draggable support
        self.dragging = False

        # Tray icon reference (set in main.py)
        self.tray_icon = None

        # Ensure focus at startup (timer so it's after window shows)
        QTimer.singleShot(200, self.ensureFocus)

    # --- Focus helper ---
    def ensureFocus(self):
        self.setFocus(Qt.OtherFocusReason)

    def go_to_page(self, index):
        if index == self.pages.currentIndex() or self.anim.state() == QPropertyAnimation.Running:
            return
        self._target_index = index
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()
        QTimer.singleShot(50, self.ensureFocus)  # Ensure focus after click

    def _do_switch_page(self):
        if self.fade_effect.opacity() == 0.0:
            self.pages.setCurrentIndex(self._target_index)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()
        QTimer.singleShot(50, self.ensureFocus)  # Ensure focus after fade

    # Borderless, rounded panel
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        painter.fillPath(path, QBrush(QColor("#fafafa")))

    # Draggable window
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

    # Proper closeEvent override (minimize to tray)
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Конвертор е скрит",
                "Щракнете върху иконата в системния трей, за да възстановите.",
                QSystemTrayIcon.Information,
                2000
            )

    # ---- Keyboard navigation and special shortcuts ----
    def keyPressEvent(self, event):
        # --- Escape key logic ---
        if event.key() == Qt.Key_Escape:
            # If ConverterPage and value is not zero, clear only
            current = self.pages.currentWidget()
            if hasattr(current, "clear_if_not_zero") and current.clear_if_not_zero():
                self.ensureFocus()
                return
            # Otherwise, minimize to tray
            self.hide()
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "Конвертор е скрит",
                    "Щракнете върху иконата в системния трей, за да възстановите.",
                    QSystemTrayIcon.Information,
                    2000
                )
            return

        # --- Always on Top toggle (Ctrl+T) ---
        if event.key() == Qt.Key_T and event.modifiers() & Qt.ControlModifier:
            self.toggle_always_on_top()
            QTimer.singleShot(50, self.ensureFocus)
            return

        # --- Arrow key navigation ---
        if self.anim.state() == QPropertyAnimation.Running:
            return
        idx = self.pages.currentIndex()
        if event.key() == Qt.Key_Right:
            new_idx = (idx + 1) % self.pages.count()
            self.indicators[new_idx].setChecked(True)
            self.go_to_page(new_idx)
            return
        elif event.key() == Qt.Key_Left:
            new_idx = (idx - 1) % self.pages.count()
            self.indicators[new_idx].setChecked(True)
            self.go_to_page(new_idx)
            return

        super().keyPressEvent(event)

    # Always on top logic
    def toggle_always_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        self.show()  # Necessary to apply new flags
        QTimer.singleShot(50, self.ensureFocus)
