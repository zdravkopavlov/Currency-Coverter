import sys
import os
import json
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QDialog, QTabWidget, QTextEdit,
    QCheckBox, QComboBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QIcon, QPainter, QPainterPath, QColor, QBrush
from PyQt5.QtCore import Qt, QPoint, QRectF

VERSION = "2.0.2 beta"
EXCHANGE_RATE = 1.95583

try:
    import msvcrt
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

LOCKFILE_NAME = 'bgn_eur_converter.lock'
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

def get_user_settings_path():
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    settings_folder = os.path.join(appdata, "BGN_EUR_Converter")
    if not os.path.exists(settings_folder):
        os.makedirs(settings_folder)
    return os.path.join(settings_folder, "settings.json")

def load_settings():
    path = get_user_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Defaults
    return {
        "start_with_windows": False,
        "start_minimized": True,
        "always_on_top": True,
        "theme": 2,  # 0 = Light, 1 = Dark, 2 = Follow Windows
        "auto_check_updates": True,
        "auto_copy_result": True,
        "remember_last_direction": True,
        "last_direction_bgn_to_eur": True,
        "x": None,
        "y": None,
        "minimal_mode": False
    }

def save_settings(settings):
    path = get_user_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except Exception:
        pass

class SettingsTab(QWidget):
    def __init__(self, app_settings, on_settings_changed):
        super().__init__()
        self.app_settings = app_settings
        self.on_settings_changed = on_settings_changed

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Start with Windows
        self.chk_start_windows = QCheckBox("Стартирай с Windows")
        self.chk_start_windows.setChecked(app_settings.get("start_with_windows", False))
        self.chk_start_windows.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_start_windows)

        # Start minimized
        self.chk_start_minimized = QCheckBox("Стартирай минимизиран")
        self.chk_start_minimized.setChecked(app_settings.get("start_minimized", True))
        self.chk_start_minimized.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_start_minimized)

        # Always on top
        self.chk_always_on_top = QCheckBox("Винаги най-отгоре")
        self.chk_always_on_top.setChecked(app_settings.get("always_on_top", True))
        self.chk_always_on_top.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_always_on_top)

        # Theme (dropdown)
        lbl_theme = QLabel("Тема:")
        layout.addWidget(lbl_theme)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светла", "Тъмна", "Следвай Windows"])
        self.theme_combo.setCurrentIndex(app_settings.get("theme", 2))  # 2 = Follow Windows
        self.theme_combo.currentIndexChanged.connect(self.save_settings)
        layout.addWidget(self.theme_combo)

        # Auto check for updates
        self.chk_auto_check_updates = QCheckBox("Автоматична проверка за обновления")
        self.chk_auto_check_updates.setChecked(app_settings.get("auto_check_updates", True))
        self.chk_auto_check_updates.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_auto_check_updates)

        # Auto copy result
        self.chk_auto_copy_result = QCheckBox("Автоматично копирай резултата")
        self.chk_auto_copy_result.setChecked(app_settings.get("auto_copy_result", True))
        self.chk_auto_copy_result.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_auto_copy_result)

        # Remember last direction
        self.chk_remember_last_direction = QCheckBox("Запомни последната посока на конвертиране")
        self.chk_remember_last_direction.setChecked(app_settings.get("remember_last_direction", True))
        self.chk_remember_last_direction.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_remember_last_direction)

        layout.addItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)

    def save_settings(self):
        self.app_settings["start_with_windows"] = self.chk_start_windows.isChecked()
        self.app_settings["start_minimized"] = self.chk_start_minimized.isChecked()
        self.app_settings["always_on_top"] = self.chk_always_on_top.isChecked()
        self.app_settings["theme"] = self.theme_combo.currentIndex()
        self.app_settings["auto_check_updates"] = self.chk_auto_check_updates.isChecked()
        self.app_settings["auto_copy_result"] = self.chk_auto_copy_result.isChecked()
        self.app_settings["remember_last_direction"] = self.chk_remember_last_direction.isChecked()
        if self.on_settings_changed:
            self.on_settings_changed(self.app_settings)

class InfoDialog(QDialog):
    def __init__(self, parent=None, app_settings=None, on_settings_changed=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(460, 420)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # --- Close "X" label ---
        self.close_label = QLabel("✕", self)
        self.close_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 18px;
                font-weight: bold;
                padding: 0 2px 0 2px;
                background: transparent;
            }
            QLabel:hover {
                color: #e43;
            }
        """)
        self.close_label.setFixedSize(24, 24)
        self.close_label.setAlignment(Qt.AlignCenter)
        self.close_label.setCursor(Qt.PointingHandCursor)
        self.close_label.mousePressEvent = self.close_label_mouse_press

        # --- TABBED CONTENT ---
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabBar::tab { height: 28px; width: 130px; font-size: 13px; }
            QTabWidget::pane { border: none; background: transparent; }
        """)
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setStyleSheet("background: transparent; border: none;")
        try:
            with open("about.txt", encoding="utf-8") as f:
                about_text.setPlainText(f.read())
        except Exception:
            about_text.setPlainText("About information goes here.")
        self.tabs.addTab(about_text, "За приложението")

        self.settings_tab = SettingsTab(app_settings, on_settings_changed)
        self.tabs.addTab(self.settings_tab, "Настройки")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        painter.fillPath(path, QBrush(QColor("#fafafa")))

    def resizeEvent(self, event):
        # Keep "X" in the top-right, inside margins
        self.close_label.move(self.width() - self.close_label.width() - 8, 8)
        super().resizeEvent(event)

    def showEvent(self, event):
        if self.parent():
            parent_rect = self.parent().frameGeometry()
            this_rect = self.frameGeometry()
            x = parent_rect.center().x() - this_rect.width() // 2
            y = parent_rect.center().y() - this_rect.height() // 2
            self.move(x, y)
        else:
            qr = self.frameGeometry()
            cp = QApplication.desktop().screen().rect().center()
            self.move(cp.x() - qr.width() // 2, cp.y() - qr.height() // 2)
        self.close_label.raise_()
        super().showEvent(event)

    def close_label_mouse_press(self, event):
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

class ConverterWindow(QWidget):
    def __init__(self, tray, settings, on_settings_changed):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("BGN/EUR Конвертор")
        self.tray_icon = tray
        self.settings = settings
        self.on_settings_changed = on_settings_changed

        # --- State ---
        self.input_value = ""
        self.bgn_to_eur = settings.get("last_direction_bgn_to_eur", True)
        self.dragging = False
        self.drag_position = QPoint()
        self.minimal_mode = settings.get("minimal_mode", False)
        self.last_clipboard = ""
        self.always_on_top = settings.get("always_on_top", True)

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

        # --- Version label ---
        self.version_label = QLabel(f"версия {VERSION}")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("color: #888; font-size: 13px; font-family:'Arial'; background: #fffafa;")
        self.version_label.setFixedHeight(22)

        # --- Main layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 5, 10, 5)
        self.main_layout.setSpacing(8)

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
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
            else:
                del item

        self.main_layout.setContentsMargins(10, 5, 10, 5)
        self.main_layout.setSpacing(8)

        if minimal:
            self.setFixedSize(300, 50)
            h_layout = QHBoxLayout()
            h_layout.setSpacing(8)
            h_layout.setContentsMargins(0, 0, 0, 0)
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
            self.version_label.hide()
        else:
            self.setFixedSize(250, 220)
            self.input_label.setStyleSheet("font-size:24px; color:#888; font-weight:bold; font-family:'Arial';")
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
            self.main_layout.addWidget(self.version_label)
            self.version_label.show()

        self.update_labels()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        painter.fillPath(path, QBrush(QColor("#fafafa")))

        if not getattr(self, "always_on_top", True):
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
        if event.button() == Qt.RightButton:
            dlg = InfoDialog(parent=self, app_settings=self.settings, on_settings_changed=self.on_settings_changed)
            dlg.exec_()
            return
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
            self.input_value = ""
            self.update_labels()
        elif key == Qt.Key_A and not event.modifiers():
            self.toggle_always_on_top()
        elif key == Qt.Key_M and not event.modifiers():
            self.set_mode(not self.minimal_mode)
        else:
            super().keyPressEvent(event)

    def toggle_direction(self):
        self.bgn_to_eur = not self.bgn_to_eur
        if self.settings.get("remember_last_direction", True):
            self.settings["last_direction_bgn_to_eur"] = self.bgn_to_eur
            save_settings(self.settings)
        self.input_value = ""
        self.update_labels()

    def update_labels(self):
        try:
            val = float(self.input_value) if self.input_value else 0.0
        except ValueError:
            val = 0.0
        output = "0.00"
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

        # Auto-copy output value (if enabled in settings)
        if self.settings.get("auto_copy_result", True):
            clipboard = QApplication.clipboard()
            if output != getattr(self, "last_clipboard", ""):
                clipboard.setText(output)
                self.last_clipboard = output

    def toggle_always_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            self.always_on_top = False
        else:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            self.always_on_top = True
        self.settings["always_on_top"] = self.always_on_top
        save_settings(self.settings)
        self.show()
        self.update()

    def closeEvent(self, event):
        event.ignore()
        # Save window position and minimal_mode
        pos = self.pos()
        self.settings["x"] = pos.x()
        self.settings["y"] = pos.y()
        self.settings["minimal_mode"] = self.minimal_mode
        save_settings(self.settings)
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

    # --------- ICON LOGIC ---------
    import ctypes
    app_id = "stoimarket.currency.converter"
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    def resource_path(filename):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, filename)
        return os.path.join(os.path.dirname(sys.argv[0]), filename)

    icon_path = resource_path("icon.ico")
    icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
    app.setWindowIcon(icon)

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("BGN/EUR Конвертор")

    menu = QMenu()
    restore_action = QAction("Покажи", tray)
    info_action = QAction("Инфо / Настройки", tray)
    quit_action = QAction("Изход", tray)
    menu.addAction(restore_action)
    menu.addAction(info_action)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    def on_settings_changed(updated_settings):
        save_settings(updated_settings)
        # Here you can re-apply always-on-top, theme, etc., live if needed

    window = ConverterWindow(tray, settings, on_settings_changed)
    window.setWindowIcon(icon)

    def toggle_show_hide():
        if window.isVisible():
            window.hide()
        else:
            window.show()
            window.activateWindow()
            window.raise_()
            window.setFocus()

    restore_action.triggered.connect(toggle_show_hide)

    def open_info_dialog():
        dlg = InfoDialog(parent=window, app_settings=settings, on_settings_changed=on_settings_changed)
        dlg.exec_()
    info_action.triggered.connect(open_info_dialog)

    tray.activated.connect(
        lambda reason: toggle_show_hide() if reason == QSystemTrayIcon.Trigger else None
    )
    quit_action.triggered.connect(app.quit)
    tray.show()

    def cleanup():
        # Save settings on quit
        pos = window.pos()
        settings["x"] = pos.x()
        settings["y"] = pos.y()
        settings["minimal_mode"] = window.minimal_mode
        save_settings(settings)
        release_lock()
        app.quit()
    app.aboutToQuit.connect(cleanup)

    # Startup behavior
    if settings.get("start_minimized", True):
        window.hide()
    else:
        window.show()
        window.setFocus()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
