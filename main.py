import sys
import os
import json
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PyQt5.QtGui import QIcon, QPainter, QPainterPath, QColor, QBrush
from PyQt5.QtCore import Qt, QPoint, QRectF

EXCHANGE_RATE = 1.95583
SETTINGS_FILE = "settings.json"

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

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings(pos, minimal_mode):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "x": pos.x(),
                "y": pos.y(),
                "minimal_mode": minimal_mode
            }, f)
    except Exception:
        pass

class ConverterWindow(QWidget):
    def __init__(self, tray, settings):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("BGN/EUR Конвертор")
        self.tray_icon = tray

        # --- State ---
        self.input_value = ""
        self.bgn_to_eur = True
        self.dragging = False
        self.drag_position = QPoint()
        self.minimal_mode = settings.get("minimal_mode", False)
        self.last_clipboard = ""

        # --- UI elements (shared) ---
        self.input_label = QLabel("0.00 лв.")
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setStyleSheet("font-size:24px; color:#888; font-family:'Arial'; font-weight:bold;")

        self.switch_button = QPushButton("⇄")
        self.switch_button.setFixedSize(48, 48)
        self.switch_button.setStyleSheet(
            "QPushButton {font-size:32px; color:#888; border:none; background:#eeeeee; border-radius:24px;}"
            "QPushButton:hover {background:#cccccc;}"
        )
        self.switch_button.setCursor(Qt.PointingHandCursor)
        self.switch_button.clicked.connect(self.toggle_direction)

        self.output_label = QLabel("€0.00")
        self.output_label.setAlignment(Qt.AlignCenter)
        self.output_label.setStyleSheet("font-size:24px; color:#888; font-family:'Arial'; font-weight:bold;")

        # --- Single main layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(12)

        # Set initial mode/layout
        self.set_mode(self.minimal_mode)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        # --- Restore window position if available ---
        x, y = settings.get("x"), settings.get("y")
        if x is not None and y is not None:
            self.move(x, y)

    def set_mode(self, minimal):
        self.minimal_mode = minimal
        # Remove everything from the main_layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
            else:
                del item

        if minimal:
            self.setFixedSize(300, 50)  # Even shorter!
            h_layout = QHBoxLayout()
            h_layout.setSpacing(8)
            h_layout.setContentsMargins(0, 0, 0, 0)
            # --- Shrink fonts and button for compact mode ---
            self.input_label.setStyleSheet("font-size:22px; color:#888; font-weight:bold; font-family:'Arial';")
            self.input_label.setFixedHeight(26) 
            self.output_label.setStyleSheet("font-size:22px; color:#888; font-weight:bold; font-family:'Arial';")
            self.output_label.setFixedHeight(26)
            self.switch_button.setFixedSize(16, 16)
            self.switch_button.setStyleSheet(
                "QPushButton {font-size:15px; color:#888; border:none; background:#eeeeee; border-radius:8px;}"
                "QPushButton:hover {background:#cccccc;}"
            )
            h_layout.addWidget(self.input_label)
            h_layout.addWidget(self.switch_button)
            h_layout.addWidget(self.output_label)
            self.main_layout.addLayout(h_layout)
        else:
            self.setFixedSize(250, 220)
            self.input_label.setStyleSheet("font-size:24px; color:#888;  font-weight:bold; font-family:'Arial';")
            self.output_label.setStyleSheet("font-size:36px; color:#888; font-weight:bold; font-family:'Arial';")
            self.switch_button.setFixedSize(48, 48)
            self.switch_button.setStyleSheet(
                "QPushButton {font-size:32px; color:#888; border:none; background:#eeeeee; border-radius:24px;}"
                "QPushButton:hover {background:#cccccc;}"
            )
            self.main_layout.addWidget(self.input_label)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(self.switch_button)
            btn_layout.addStretch()
            self.main_layout.addLayout(btn_layout)
            self.main_layout.addWidget(self.output_label)
        self.update_labels()

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
        elif key == Qt.Key_M and not event.modifiers():
            self.set_mode(not self.minimal_mode)
        else:
            super().keyPressEvent(event)

    # --- Conversion logic + auto clipboard ---
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
            output = f"{eur:.2f}"
            self.output_label.setText(f"€{output}")
        else:
            self.input_label.setText(f"€{val:.2f}")
            bgn = round(val * EXCHANGE_RATE + 1e-8, 2)
            output = f"{bgn:.2f}"
            self.output_label.setText(f"{output} лв.")
        # Auto-copy output value (not currency symbol)
        clipboard = QApplication.clipboard()
        if output != self.last_clipboard:
            clipboard.setText(output)
            self.last_clipboard = output

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

    settings = load_settings()
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

    window = ConverterWindow(tray, settings)

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

    # Save window position & layout on exit
    def cleanup():
        pos = window.pos()
        save_settings(pos, window.minimal_mode)
        release_lock()
        app.quit()
    app.aboutToQuit.connect(cleanup)

    window.show()
    window.setFocus()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
