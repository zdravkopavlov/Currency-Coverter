import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QRadioButton, QButtonGroup, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve

class Page(QWidget):
    def __init__(self, title, body):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addStretch()
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title_label)
        body_label = QLabel(body)
        body_label.setAlignment(Qt.AlignCenter)
        body_label.setStyleSheet("font-size: 20px; color: #555;")
        layout.addWidget(body_label)
        layout.addStretch()

class CarouselWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carousel Demo")
        self.resize(400, 300)
        self.setStyleSheet("background: #fafafa; border-radius: 24px;")
        self.setFocusPolicy(Qt.StrongFocus)

        # Pages
        self.pages = QStackedWidget()
        self.page_titles = ["Converter", "Settings", "About"]
        self.page_bodies = [
            "This is your converter page!",
            "Theme and preferences here",
            "About / Help information here"
        ]
        for title, body in zip(self.page_titles, self.page_bodies):
            self.pages.addWidget(Page(title, body))

        # Dots using QRadioButton
        self.button_group = QButtonGroup(self)
        self.indicator_layout = QHBoxLayout()
        self.indicator_layout.setSpacing(2)
        self.indicator_layout.setContentsMargins(0, 0, 0, 0)
        self.indicator_layout.addStretch()
        self.indicators = []
        for i in range(len(self.page_titles)):
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

        # Layout
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

    def keyPressEvent(self, event):
        if self.anim.state() == QPropertyAnimation.Running:
            return
        idx = self.pages.currentIndex()
        if event.key() == Qt.Key_Right:
            new_idx = (idx + 1) % self.pages.count()
            self.indicators[new_idx].setChecked(True)
            self.go_to_page(new_idx)
        elif event.key() == Qt.Key_Left:
            new_idx = (idx - 1) % self.pages.count()
            self.indicators[new_idx].setChecked(True)
            self.go_to_page(new_idx)
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CarouselWidget()
    w.show()
    sys.exit(app.exec_())
