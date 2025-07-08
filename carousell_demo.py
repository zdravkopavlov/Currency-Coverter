import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer

class Page(QWidget):
    def __init__(self, title, body):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
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

        # Create pages
        self.page_list = [
            Page("Converter", "This is your converter page!"),
            Page("Settings", "Theme and preferences here"),
            Page("About", "About / Help information here")
        ]
        self.current_index = 0

        # Container for animation
        self.container = QWidget(self)
        self.container.setGeometry(self.contentsRect())
        self.container.setStyleSheet("background: transparent;")
        self.container.raise_()
        self.current_page = self.page_list[self.current_index]
        self.current_page.setParent(self.container)
        self.current_page.setGeometry(self.container.rect())
        self.current_page.show()

        # Page indicator dots (QPushButton)
        self.indicator_layout = QHBoxLayout()
        self.indicators = []
        for i in range(len(self.page_list)):
            dot = QPushButton("●")
            dot.setFocusPolicy(Qt.NoFocus)
            dot.setFixedSize(28, 28)
            dot.setStyleSheet("color: #bbb; font-size: 22px; background: transparent; border: none;")
            dot.clicked.connect(lambda checked, idx=i: self.slide_to(idx))
            self.indicators.append(dot)
            self.indicator_layout.addWidget(dot)
        self.update_indicators()

        # Main layout
        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.container)
        layout.addStretch()
        layout.addLayout(self.indicator_layout)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Animation
        self.animating = False

        QTimer.singleShot(200, self.set_focus_to_self)

    def resizeEvent(self, event):
        self.container.setGeometry(self.contentsRect())
        self.current_page.setGeometry(self.container.rect())

    def set_focus_to_self(self):
        self.setFocus()
        print("Focus forced to main widget.")

    def update_indicators(self):
        for i, dot in enumerate(self.indicators):
            if i == self.current_index:
                dot.setStyleSheet("color: #0099ff; font-size: 22px; background: transparent; border: none;")
            else:
                dot.setStyleSheet("color: #bbb; font-size: 22px; background: transparent; border: none;")

    def slide_to(self, target_index):
        if self.animating or target_index == self.current_index:
            return
        print(f"Sliding to page {target_index}")
        direction = 1 if target_index > self.current_index else -1
        old_page = self.current_page
        new_page = self.page_list[target_index]
        w, h = self.container.width(), self.container.height()
        new_page.setParent(self.container)
        new_page.setGeometry(QRect(direction * w, 0, w, h))
        new_page.show()

        # Animate both pages
        anim_old = QPropertyAnimation(old_page, b"geometry")
        anim_new = QPropertyAnimation(new_page, b"geometry")
        anim_old.setDuration(350)
        anim_new.setDuration(350)
        anim_old.setEasingCurve(QEasingCurve.InOutCubic)
        anim_new.setEasingCurve(QEasingCurve.InOutCubic)
        anim_old.setStartValue(QRect(0, 0, w, h))
        anim_old.setEndValue(QRect(-direction * w, 0, w, h))
        anim_new.setStartValue(QRect(direction * w, 0, w, h))
        anim_new.setEndValue(QRect(0, 0, w, h))
        self.animating = True

        def finish():
            old_page.hide()
            self.current_index = target_index
            self.current_page = new_page
            self.update_indicators()
            self.animating = False
            print("Slide finished.")

        anim_new.finished.connect(finish)
        anim_old.start()
        anim_new.start()

    def keyPressEvent(self, event):
        print(f"Key pressed: {event.key()}")
        if self.animating:
            return
        if event.key() == Qt.Key_Right:
            idx = (self.current_index + 1) % len(self.page_list)
            print(f"Right arrow: go to {idx}")
            self.slide_to(idx)
        elif event.key() == Qt.Key_Left:
            idx = (self.current_index - 1) % len(self.page_list)
            print(f"Left arrow: go to {idx}")
            self.slide_to(idx)
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CarouselWidget()
    w.show()
    sys.exit(app.exec_())
