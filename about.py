from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addStretch()
        title_label = QLabel("About")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title_label)
        body_label = QLabel("About / Help information here")
        body_label.setAlignment(Qt.AlignCenter)
        body_label.setStyleSheet("font-size: 20px; color: #555;")
        layout.addWidget(body_label)
        layout.addStretch()
