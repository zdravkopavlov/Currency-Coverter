import sys
import os
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PyQt5.QtGui import QIcon, QPainter, QPainterPath, QColor, QBrush
from PyQt5.QtCore import Qt, QPoint, QRectF

EXCHANGE_RATE = 1.95583

# --- One Instance Lock (Windows only) ---
try:
    import msvcrt
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

LOCKFILE_NAME = 'bgn_eur_converter_qt.mutex'
lock_file = None

def acquire_lock():
    if not IS_WINDOWS:
        return True
    global lock_file
    lock_path = os.path.join(tempfile.gettempdir(), LOCKFILE_NAME)
    try:
        lock_file = open(lock_path, 'w')
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        return True
    except (OSError, IOError):
        return False

def release_lock():
    if not IS_WINDOWS:
        return
    global lock_file
    if lock_file:
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            lock_file.close()
            os.remove(lock_file.name)
        except Exception:
            pass

class ConverterWindow(QWidget):
    def __init__(self, tray):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("BGN/EUR Конвертор")
        self.resize(250, 220)
        self.tray_icon = tray

        # --- Converter State ---
        self.input_value = ""
        self.bgn_to_eur = True
        self.dragging = False
        self.drag_position = QPoint()

        # --- UI ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.input_label = QLabel("0.00 лв.")
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setStyleSheet("font-size:24px; color:#888; font-weight:bold;")
        layout.addWidget(self.input_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.switch_button = QPushButton("⇄")
        self.switch_button.setFixedSize(48, 48)
        self.switch_button.setStyleSheet(
            "QPushButton {font-size:32px; color:#888; border:none; background:#eeeeee; border-radius:24px;}"
            "QPushButton:hover {background:#cccccc;}"
        )
        self.switch_button.setCursor(Qt.PointingHandCursor)
        self.switch_button.clicked.connect(self.toggle_direction)
        btn_layout.addWidget(self.switch_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.output_label = QLabel("€0.00")
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setStyleSheet("font-size:36px; color:#444;")
        layout.addWidget(self.output_label)

        self.setLayout(layout)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    # --- Drawing the rounded panel ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        painter.fillPath(path, QBrush(QColor("#fafafa")))

    # --- Draggable window ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.switch_button.underMouse():
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    def mouseReleaseEvent(self, event):
        self.dragging = False

    # --- Keyboard logic ---
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
            # If not already cleared, clear value
            if self.input_value and float(self.input_value or 0) != 0:
                self.input_value = ""
                self.update_labels()
            else:
                self.hide()
                if self.tray_icon:
                    self.tray_icon.showMessage(
                        "Конвертор е скрит",
                        "Щракнете върху иконата в системния трей, за да възстановите.",
                        QSystemTrayIcon.Information,
                        2000
                    )
        elif key == Qt.Key_A and not event.modifiers():
            self.toggle_always_on_top()
        else:
            super().keyPressEvent(event)

    # --- Conversion logic ---
    def toggle_direction(self):
        self.bgn_to_eur = not self.bgn_to_eur
        self.input_value = ""
        self.update_labels()

    def update_labels(self):
        try:
            val = float(self.input_value) if self.input_value else 0.0
        except ValueError:
            val = 0.0
        if self.bgn_to_eur:
            self.input_label.setText(f"{val:.2f} лв.")
            eur = round(val / EXCHANGE_RATE + 1e-8, 2)
            self.output_label.setText(f"€{eur:.2f}")
        else:
            self.input_label.setText(f"€{val:.2f}")
            bgn = round(val * EXCHANGE_RATE + 1e-8, 2)
            self.output_label.setText(f"{bgn:.2f} лв.")

    # --- Always-on-top toggle ---
    def toggle_always_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        self.show()

    # --- Minimize to tray (Escape) ---
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

def main():
    if not acquire_lock():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("BGN/EUR Конвертор")
        msg.setText("Конверторът вече работи.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)

    app = QApplication(sys.argv)
    icon = QIcon("icon.ico") if os.path.exists("icon.ico") else QIcon()

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("BGN/EUR Конвертор")

    menu = QMenu()
    restore_action = QAction("Покажи", tray)
    quit_action = QAction("Изход", tray)
    menu.addAction(restore_action)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    window = ConverterWindow(tray)

    def show_and_raise():
        window.show()
        window.activateWindow()
        window.raise_()
        window.setFocus()

    restore_action.triggered.connect(show_and_raise)
    quit_action.triggered.connect(app.quit)
    tray.activated.connect(
        lambda reason: show_and_raise() if reason == QSystemTrayIcon.Trigger else None
    )
    tray.show()

    # Ensure lock release on exit
    def cleanup():
        release_lock()
        app.quit()
    app.aboutToQuit.connect(cleanup)

    window.show()
    window.setFocus()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
