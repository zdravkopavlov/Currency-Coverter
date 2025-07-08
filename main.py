import sys, os
import os
import tempfile

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QPainterPath, QIcon

# ---- One Instance Lock (Windows-only, simple file lock) ----
try:
    import msvcrt
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

LOCKFILE_NAME = 'bgn_eur_converter_qt.mutex'
lock_file = None

def resource_path(filename):
    """ Get absolute path to resource for PyInstaller or dev """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

def acquire_lock():
    if not IS_WINDOWS:
        return True  # No lock on non-Windows for now
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

# ---- Main Window Class ----

EXCHANGE_RATE = 1.95583

class CurrencyConverter(QWidget):
    def __init__(self, tray):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.tray_icon = tray  # Set tray reference for showing messages

        # Window state
        self.input_value = ""
        self.bgn_to_eur = True
        self.dragging = False
        self.drag_position = QPoint()

        # Widgets
        self.input_label = QLabel("0.00 лв.", self)
        self.input_label.setFont(QFont("Tahoma", 32))
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setStyleSheet("color: #888888;")

        self.switch_button = QPushButton("⇄", self)
        self.switch_button.setFixedSize(48, 48)
        self.switch_button.setFont(QFont("Tahoma", 32))
        self.switch_button.setCursor(Qt.PointingHandCursor)
        self.switch_button.setStyleSheet(
            "QPushButton { border: none; background: #eeeeee; border-radius: 24px; }"
            "QPushButton:hover { background: #cccccc; }"
        )
        self.switch_button.clicked.connect(self.toggle_direction)

        self.output_label = QLabel("€0.00", self)
        self.output_label.setFont(QFont("Tahoma", 32))
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setStyleSheet("color: #888888;")

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
        # Allow numbers, comma, dot, backspace, escape, minimize to tray (Ctrl+M)
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
        elif key == Qt.Key_M and event.modifiers() & Qt.ControlModifier:
            self.hide_to_tray()
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

    def closeEvent(self, event):
        # Hide to tray instead of closing
        event.ignore()
        self.hide_to_tray()

    def hide_to_tray(self):
        self.hide()
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Конвертор е скрит",
                "Щракнете върху иконата в системния трей, за да възстановите.",
                QSystemTrayIcon.Information,
                2000
            )

    def show_and_raise(self):
        self.show()
        self.activateWindow()
        self.raise_()

# ---- Main App Entry ----

def main():
    if not acquire_lock():
        # Already running
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("BGN/EUR Конвертор")
        msg.setText("Конверторът вече работи.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        sys.exit(0)

    app = QApplication(sys.argv)

    # Always use your own icon.ico for tray reliability
    icon = QIcon(resource_path("icon.ico"))
    if icon.isNull():
        # fallback to default if missing
        icon = QIcon()

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("BGN/EUR Конвертор")

    # Set up menu
    menu = QMenu()
    restore_action = QAction("Покажи", tray)
    quit_action = QAction("Изход", tray)
    menu.addAction(restore_action)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    # Create main window and hook up tray signals
    window = CurrencyConverter(tray)
    restore_action.triggered.connect(window.show_and_raise)
    quit_action.triggered.connect(app.quit)
    tray.activated.connect(
        lambda reason: window.show_and_raise() if reason == QSystemTrayIcon.Trigger else None
    )
    tray.show()

    # Make sure release_lock is called on exit
    def cleanup():
        release_lock()
        app.quit()
    app.aboutToQuit.connect(cleanup)

    window.setWindowTitle("BGN/EUR Конвертор")
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
