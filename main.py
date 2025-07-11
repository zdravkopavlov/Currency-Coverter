import sys
import os
import json
import subprocess
import tempfile
import markdown  # pip install markdown
import requests  # <-- for update checking
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QDialog, QTabWidget, QTextBrowser,
    QCheckBox, QComboBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QIcon, QPainter, QPainterPath, QColor, QBrush, QMouseEvent, QCursor
from PyQt5.QtCore import Qt, QPoint, QRectF, QTimer

window_title = "BGN/EUR Converter SingleInstance MainWindow"

try:
    import win32event
    import win32api
    import winerror
    import win32gui
    import win32con
except ImportError:
    win32event = None



mutexname = "BGN_EUR_CONVERTER_MUTEX"
if win32event is not None:
    mutex = win32event.CreateMutex(None, False, mutexname)
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        # App already running: find and show the main window
        import time
        time.sleep(0.2)  # Give main window time to start, just in case
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        sys.exit(0)

VERSION = "2.2.4" # Update this version number with each release
EXCHANGE_RATE = 1.95583

# ---- UPDATE CHECKER CONFIG ----
UPDATE_URL = "https://raw.githubusercontent.com/zdravkopavlov/Currency-Coverter/main/latest_version.json"
# --------------------------------

def get_user_settings_path():
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    settings_folder = os.path.join(appdata, "BGN_EUR_Converter")
    if not os.path.exists(settings_folder):
        os.makedirs(settings_folder)
    return os.path.join(settings_folder, "settings.json")

def launch_downloader_and_exit(downloader_path="downloader.py"):
    # If you have downloader.exe, use that instead!
    try:
        if downloader_path.endswith(".py"):
            subprocess.Popen([sys.executable, downloader_path])
        else:
            subprocess.Popen([downloader_path])
    except Exception as e:
        print(f"Failed to launch updater: {e}")
        return
    # Quit the main app
    QApplication.quit()  # or sys.exit(0)

def load_settings():
    path = get_user_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "start_with_windows": False,
        "start_minimized": True,
        "always_on_top": True,
        "theme": 2,
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

def get_theme(settings):
    idx = settings.get("theme", 2)
    if idx == 2:
        if sys.platform == "win32":
            try:
                import winreg
                key = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as regkey:
                    val, _ = winreg.QueryValueEx(regkey, "AppsUseLightTheme")
                return "light" if val == 1 else "dark"
            except Exception:
                return "light"
        return "light"
    return "light" if idx == 0 else "dark"

def doc_path(filename):
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base, "Documentation", filename)

def load_markdown_html(filepath, theme="light"):
    try:
        with open(filepath, encoding="utf-8") as f:
            md_text = f.read()
        html = markdown.markdown(md_text, extensions=["extra", "tables", "sane_lists"])
    except Exception:
        html = "<i>Документът не е наличен.</i>"
    if theme == "dark":
        css = """
        <style>
        body { background: #333333; color: #e0e0e0; font-family: Arial, sans-serif; }
        h1, h2, h3, h4, h5 { color: #fafafa; }
        code, pre { background: #181a20; color: #fff; border-radius: 4px; padding: 1px 4px; }
        a { color: #8ab4f8; }
        ul, ol { margin-left: 20px; }
        </style>
        """
    else:
        css = """
        <style>
        body { background: #fafafa; color: #2b2b2b; font-family: Arial, sans-serif; }
        h1, h2, h3, h4, h5 { color: #222; }
        code, pre { background: #f1f1f1; color: #222; border-radius: 4px; padding: 1px 4px; }
        a { color: #1a0dab; }
        ul, ol { margin-left: 20px; }
        </style>
        """
    html = css + html
    return html

# --- UPDATE CHECKER LOGIC ---
def check_for_update(current_version, url=UPDATE_URL):
    try:
        r = requests.get(url, timeout=4)
        data = r.json()
        latest = data.get("version")
        if latest and latest != current_version:
            return data  # Dict with version, download_url, changelog, date
        return None
    except Exception as e:
        print("Update check failed:", e)
        return None

# --- SETTINGS TAB (with update block at the bottom) ---
class SettingsTab(QWidget):
    def __init__(self, app_settings, on_settings_changed, parent_window=None, update_info=None, manual_update_callback=None):
        super().__init__()
        self.app_settings = app_settings
        self.on_settings_changed = on_settings_changed
        self.parent_window = parent_window
        self.update_info = update_info
        self.manual_update_callback = manual_update_callback

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.chk_start_windows = QCheckBox("Стартирай с Windows")
        self.chk_start_windows.setChecked(app_settings.get("start_with_windows", False))
        self.chk_start_windows.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_start_windows)

        self.chk_start_minimized = QCheckBox("Стартирай минимизиран")
        self.chk_start_minimized.setChecked(app_settings.get("start_minimized", True))
        self.chk_start_minimized.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_start_minimized)

        # -- removed from the settings dialog
        #self.chk_always_on_top = QCheckBox("Винаги най-отгоре")
        #self.chk_always_on_top.setChecked(app_settings.get("always_on_top", True))
        #self.chk_always_on_top.stateChanged.connect(self.save_settings)
        #layout.addWidget(self.chk_always_on_top)

        lbl_theme = QLabel("Тема:")
        layout.addWidget(lbl_theme)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светла", "Тъмна", "Следвай Windows"])
        self.theme_combo.setCurrentIndex(app_settings.get("theme", 2))
        self.theme_combo.currentIndexChanged.connect(self.save_settings)
        layout.addWidget(self.theme_combo)

        self.chk_auto_copy_result = QCheckBox("Автоматично копирай резултата")
        self.chk_auto_copy_result.setChecked(app_settings.get("auto_copy_result", True))
        self.chk_auto_copy_result.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_auto_copy_result)

        self.chk_remember_last_direction = QCheckBox("Запомни последната посока на конвертиране")
        self.chk_remember_last_direction.setChecked(app_settings.get("remember_last_direction", True))
        self.chk_remember_last_direction.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_remember_last_direction)

        layout.addSpacing(10)

        # UPDATES BLOCK (always at the bottom)
        self.updates_block = QWidget()
        self.updates_layout = QVBoxLayout(self.updates_block)
        self.updates_layout.setContentsMargins(14, 10, 14, 10)
        self.updates_layout.setSpacing(7)
        self.updates_block.setStyleSheet("""
            background: rgba(64,68,80,0.08);
            border-radius: 12px;
        """)
        layout.addWidget(self.updates_block)

        # Current & Latest version labels
        self.lbl_current = QLabel(f"Инсталирана версия: {VERSION}")
        self.lbl_latest = QLabel("")
        self.lbl_latest.setStyleSheet("font-weight: bold")
        self.lbl_latest.setVisible(False)
        self.updates_layout.addWidget(self.lbl_current)
        self.updates_layout.addWidget(self.lbl_latest)

        # Download link
        self.download_button = QPushButton("Изтегли и инсталирай")
        self.download_button.setVisible(False)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.launch_downloader)
        self.updates_layout.addWidget(self.download_button)

        # Changelog preview
        self.changelog_label = QLabel()
        self.changelog_label.setVisible(False)
        self.changelog_label.setWordWrap(True)
        self.updates_layout.addWidget(self.changelog_label)

        # Manual check button (visible only if auto-check is off)
        self.manual_check_btn = QPushButton("Провери за обновления")
        self.manual_check_btn.setVisible(False)
        self.manual_check_btn.setCursor(Qt.PointingHandCursor)
        self.manual_check_btn.clicked.connect(self.do_manual_update)
        self.updates_layout.addWidget(self.manual_check_btn)

        # Add a label for feedback if no update is found
        self.no_update_label = QLabel("")
        self.no_update_label.setVisible(False)
        self.no_update_label.setStyleSheet("font-size:12px;")
        self.updates_layout.addWidget(self.no_update_label)

        # Auto-check checkbox (in update block, last)
        self.chk_auto_check_updates = QCheckBox("Автоматична проверка за обновления")
        self.chk_auto_check_updates.setChecked(app_settings.get("auto_check_updates", True))
        self.chk_auto_check_updates.stateChanged.connect(self.save_settings)
        self.updates_layout.addWidget(self.chk_auto_check_updates)

        layout.addItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)
        self.update_updates_block()
        self.apply_theme(get_theme(self.app_settings))

    def launch_downloader(self):
        try:
            from PyQt5.QtWidgets import QApplication
            import os
            import subprocess
            # Use .exe if you have it, otherwise .py
            downloader_path = os.path.join(os.path.dirname(sys.argv[0]), "update.py")
            if not os.path.exists(downloader_path):
                downloader_path = os.path.join(os.path.dirname(sys.argv[0]), "update.exe")
            if os.path.exists(downloader_path):
                if downloader_path.endswith(".py"):
                    subprocess.Popen([sys.executable, downloader_path])
                else:
                    subprocess.Popen([downloader_path])
                QApplication.quit()  # Close the main app
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Грешка", "Файлът за обновление не е намерен.")
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Грешка", f"Неуспешно стартиране на обновлението:\n{e}")

    def update_updates_block(self, info=None):
        if info is None:
            info = self.update_info
        if info:
            self.lbl_latest.setText(f"Налична версия: {info['version']}")
            self.lbl_latest.setVisible(True)
            dl_url = info.get("download_url")
            if dl_url:
                #self.download_label.setText(f"<a href='{dl_url}' style='color:#206ad8; text-decoration:underline'>Изтегли</a>")
                #self.download_label.setVisible(True)
                self.download_button.setVisible(True)
            changelog = info.get("changelog")
            if changelog:
                first_lines = "\n".join(changelog.strip().splitlines()[:3])
                self.changelog_label.setText(f"<span style='color:#888;'>{first_lines}</span>")
                self.changelog_label.setVisible(True)
            else:
                self.changelog_label.setVisible(False)
        else:
            self.lbl_latest.setVisible(False)
            self.download_button.setVisible(False)
            self.changelog_label.setVisible(False)
        # Show manual check button if auto-check is off
        self.manual_check_btn.setVisible(not self.chk_auto_check_updates.isChecked())

    def apply_theme(self, theme):
        # Set button style to be readable and interactive
        if theme == "dark":
            self.no_update_label.setStyleSheet("font-size:12px; color:#eeeeee;")  # soft yellow
            btn_style = (
                "QPushButton { background: #313640; color: #eee; border-radius: 8px; }"
                "QPushButton:hover { background: #374151; }"
                "QPushButton:pressed { background: #2d3848; }"
            )
        else:
            self.no_update_label.setStyleSheet("font-size:12px; color:#000000;")
            btn_style = (
                "QPushButton { background: #e8e8e8; color: #223; border-radius: 8px; }"
                "QPushButton:hover { background: #d4d4d4; }"
                "QPushButton:pressed { background: #c3c3c3; }"
            )
        self.manual_check_btn.setStyleSheet(btn_style)

    def save_settings(self):
        self.app_settings["start_with_windows"] = self.chk_start_windows.isChecked()
        self.app_settings["start_minimized"] = self.chk_start_minimized.isChecked()
        #self.app_settings["always_on_top"] = self.chk_always_on_top.isChecked()
        self.app_settings["theme"] = self.theme_combo.currentIndex()
        self.app_settings["auto_check_updates"] = self.chk_auto_check_updates.isChecked()
        self.app_settings["auto_copy_result"] = self.chk_auto_copy_result.isChecked()
        self.app_settings["remember_last_direction"] = self.chk_remember_last_direction.isChecked()
        if self.on_settings_changed:
            self.on_settings_changed(self.app_settings)
        if self.parent_window:
            self.parent_window.apply_theme(get_theme(self.app_settings))
        self.update_updates_block()

    def do_manual_update(self):
        if self.manual_update_callback:
            found = self.manual_update_callback()
            if not found:
                self.no_update_label.setText("Няма налични нови обновления.")
                self.no_update_label.setVisible(True)
                QTimer.singleShot(3000, lambda: self.no_update_label.setVisible(False))
            else:
                self.no_update_label.setVisible(False)



class InfoDialog(QDialog):
    def __init__(self, parent=None, app_settings=None, on_settings_changed=None, update_info=None, manual_update_callback=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.setFixedSize(520, 540)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.theme = get_theme(app_settings)
        self.update_info = update_info

        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabBar::tab { height: 28px; width: 140px; font-size: 13px; }
            QTabWidget::pane { border: none; background: transparent; }
        """)

        self.settings_tab = SettingsTab(
            app_settings, on_settings_changed, parent_window=self,
            update_info=self.update_info, manual_update_callback=manual_update_callback
        )
        self.tabs.addTab(self.settings_tab, "Настройки")

        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(True)
        help_html = load_markdown_html(doc_path("help_bg.md"), self.theme)
        self.help_browser.setHtml(help_html)
        self.tabs.addTab(self.help_browser, "Помощ")

        self.about_browser = QTextBrowser()
        self.about_browser.setOpenExternalLinks(True)
        about_html = load_markdown_html(doc_path("about_bg.md"), self.theme)
        self.about_browser.setHtml(about_html)
        self.tabs.addTab(self.about_browser, "За приложението")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.apply_theme(self.theme)

    def showEvent(self, event):
        # Smart positioning, below main window if possible
        if self.parent() and self.parent().isVisible():
            parent_geom = self.parent().frameGeometry()
            screen_geom = QApplication.desktop().screenGeometry(parent_geom.center())
            popup_height = self.height()
            below_top = parent_geom.bottom()
            below_room = screen_geom.bottom() - below_top
            if below_room >= popup_height:
                x = parent_geom.center().x() - self.width() // 2
                y = below_top
            else:
                above_bottom = parent_geom.top()
                if (above_bottom - screen_geom.top()) >= popup_height:
                    x = parent_geom.center().x() - self.width() // 2
                    y = above_bottom - popup_height
                else:
                    x = screen_geom.center().x() - self.width() // 2
                    y = screen_geom.center().y() - self.height() // 2
            x = max(screen_geom.left(), min(x, screen_geom.right() - self.width()))
            y = max(screen_geom.top(), min(y, screen_geom.bottom() - self.height()))
            self.move(int(x), int(y))
        else:
            # Fallback: center on screen
            qr = self.frameGeometry()
            cp = QApplication.desktop().screen().rect().center()
            self.move(cp.x() - qr.width() // 2, cp.y() - qr.height() // 2)
        super().showEvent(event)
        QApplication.instance().installEventFilter(self)

    def closeEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress:
            if not self.geometry().contains(event.globalPos()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def apply_theme(self, theme):
        if theme == "dark":
            bg = "#333333"
            fg = "#e0e0e0"
            border = "#393939"
        else:
            bg = "#fafafa"
            fg = "#2b2b2b"
            border = "#cccccc"
        self.setStyleSheet(f"""
            QDialog {{
                background: {bg};
                color: {fg};
                border-radius: 24px;
            }}
            QLabel, QCheckBox, QComboBox {{
                color: {fg};
                background: transparent;
            }}
            QTabWidget::pane {{
                background: transparent;
            }}
            QTabBar::tab {{
                background: {bg};
                color: {fg};
                border-radius: 8px 8px 0 0;
                min-width: 120px;
                padding: 8px 2px;
            }}
            QTabBar::tab:selected {{
                background: {border};
                color: {fg};
            }}
            QPushButton {{
                background: #313640;
                color: #eee;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: #374151;
            }}
        """)
        help_html = load_markdown_html(doc_path("help_bg.md"), theme)
        self.help_browser.setHtml(help_html)
        about_html = load_markdown_html(doc_path("about_bg.md"), theme)
        self.about_browser.setHtml(about_html)
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        painter.fillPath(path, QBrush(QColor("#222222" if self.theme == "dark" else "#fafafa")))

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

def update_updates_block(self, info=None):
    if info is None:
        info = self.update_info
    if info:
        self.lbl_latest.setText(f"Налична версия: {info['version']}")
        self.lbl_latest.setVisible(True)
        dl_url = info.get("download_url")
        if dl_url:
            self.download_button.setVisible(True)
        else:
            self.download_button.setVisible(False)
        changelog = info.get("changelog")
        if changelog:
            first_lines = "\n".join(changelog.strip().splitlines()[:3])
            self.changelog_label.setText(f"<span style='color:#888;'>{first_lines}</span>")
            self.changelog_label.setVisible(True)
        else:
            self.changelog_label.setVisible(False)
    else:
        self.lbl_latest.setVisible(False)
        self.download_button.setVisible(False)
        self.changelog_label.setVisible(False)
    self.manual_check_btn.setVisible(not self.chk_auto_check_updates.isChecked())


# --- MAIN CONVERTER WINDOW ---
class ConverterWindow(QWidget):
    def __init__(self, tray, settings, on_settings_changed):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("BGN/EUR Конвертор")
        self.tray_icon = tray
        self.settings = settings
        self.on_settings_changed = on_settings_changed

        self.input_value = ""
        self.bgn_to_eur = settings.get("last_direction_bgn_to_eur", True)
        self.dragging = False
        self.drag_position = QPoint()
        self.minimal_mode = settings.get("minimal_mode", False)
        self.last_clipboard = ""
        self.always_on_top = settings.get("always_on_top", True)
        self.info_popup = None
        self.update_info = None

        self.input_label = QLabel("0.00 лв.")
        self.input_label.setAlignment(Qt.AlignCenter)

        self.switch_button = QPushButton("⇄")
        self.switch_button.setFixedSize(48, 48)
        self.switch_button.setStyleSheet("""
            QPushButton {
                font-size:32px;
                color:#888;
                border:none;
                background:#aaaaaa;
                border-radius:24px;
            }
            QPushButton:hover {
                background:#cccccc;
            }
        """)
        self.switch_button.clicked.connect(self.toggle_direction)

        self.output_label = QLabel("€0.00")
        self.output_label.setAlignment(Qt.AlignCenter)

        # Version/update label (bottom)
        self.version_label = QLabel(f"версия {VERSION}")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setFixedHeight(22)
        self.version_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.version_label.mousePressEvent = self.open_updates_on_click

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 5, 10, 5)
        self.main_layout.setSpacing(8)

        self.set_mode(self.minimal_mode)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        x, y = settings.get("x"), settings.get("y")
        if x is not None and y is not None:
            self.move(x, y)
        self.apply_theme(get_theme(self.settings))

        # Update check on launch, if enabled
        if self.settings.get("auto_check_updates", True):
            QTimer.singleShot(1200, self.check_for_updates)
        else:
            self.set_update_label(False)

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
            self.input_label.setFixedHeight(26)
            self.output_label.setFixedHeight(26)
            self.switch_button.setFixedSize(24, 24)
            self.switch_button.setStyleSheet("""
                QPushButton {
                    font-size:15px;
                    color:#888;
                    border:none;
                    background:#eeeeee;
                    border-radius:12px;
                }
                QPushButton:hover {
                    background:#cccccc;
                }
            """)
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
            self.switch_button.setStyleSheet("""
                QPushButton {
                    font-size:32px;
                    color:#888;
                    border:none;
                    background:#eeeeee;
                    border-radius:24px;
                }
                QPushButton:hover {
                    background:#cccccc;
                }
            """)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(self.switch_button)
            btn_layout.addStretch()
            self.main_layout.addWidget(self.input_label)
            self.main_layout.addLayout(btn_layout)
            self.main_layout.addWidget(self.output_label)
            self.main_layout.addWidget(self.version_label)
            self.version_label.show()
        self.update_labels()
        self.apply_theme(get_theme(self.settings))

    def apply_theme(self, theme):
        if theme == "dark":
            bg = "#222222"
            fg = "#e0e0e0"
            border = "#393939"
            accent = "#4978e9"
        else:
            bg = "#fafafa"
            fg = "#454545"
            border = "#cccccc"
            accent = "#1658ff"
        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                color: {fg};
            }}
            QLabel {{
                color: {fg};
                background: transparent;
            }}
            QPushButton {{
                background: #313640;
                color: #eee;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: #374151;
            }}
        """)
        self.input_label.setStyleSheet(f"font-size:24px; color:{fg}; font-family:'Arial'; font-weight:bold; background:transparent;")
        self.output_label.setStyleSheet(f"font-size:24px; color:{fg}; font-family:'Arial'; font-weight:bold; background:transparent;")
        if self.update_info:
            self.version_label.setStyleSheet("color: #206ad8; font-size: 13px; text-decoration:underline; font-family:'Arial'; background: transparent; cursor: pointer;")
        else:
            self.version_label.setStyleSheet(f"color: {fg}; font-size: 13px; font-family:'Arial'; background: {bg}; cursor: pointer;")
        if self.info_popup and self.info_popup.isVisible():
            self.info_popup.apply_theme(theme)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        theme = get_theme(self.settings)
        painter.fillPath(path, QBrush(QColor("#222222" if theme == "dark" else "#fafafa")))
        if not getattr(self, "always_on_top", True):
            border_color = QColor("#393939" if theme == "dark" else "#5a5a5a")
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
        if self.info_popup is not None and self.info_popup.isVisible():
            self.info_popup.close()
            self.info_popup = None
            QTimer.singleShot(0, lambda: QApplication.postEvent(self, QMouseEvent(
                event.type(), event.localPos(), event.screenPos(),
                event.button(), event.buttons(), event.modifiers())))
            return
        if event.button() == Qt.RightButton:
            self.show_info_popup()
            return
        if event.button() == Qt.LeftButton and not self.switch_button.underMouse():
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def show_info_popup(self):
        if self.info_popup is None or not self.info_popup.isVisible():
            self.info_popup = InfoDialog(
                parent=self, app_settings=self.settings, on_settings_changed=self.on_settings_changed,
                update_info=self.update_info, manual_update_callback=self.manual_update_check
            )
            self.info_popup.show()
            self.info_popup.activateWindow()
            self.info_popup.setFocus()

    def mouseMoveEvent(self, event):
        if self.info_popup is not None and self.info_popup.isVisible():
            self.info_popup.close()
            self.info_popup = None
            QTimer.singleShot(0, lambda: QApplication.postEvent(self, QMouseEvent(
                event.type(), event.localPos(), event.screenPos(),
                event.button(), event.buttons(), event.modifiers())))
            return
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def keyPressEvent(self, event):
        key = event.key()
        if self.info_popup is not None and self.info_popup.isVisible():
            QApplication.sendEvent(self.info_popup, event)
            return
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
        elif key == Qt.Key_C and not event.modifiers():
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

    def open_updates_on_click(self, event):
        self.show_info_popup()

    def check_for_updates(self):
        info = check_for_update(VERSION)
        self.update_info = info
        self.set_update_label(bool(info))
        # update info_popup, if open
        if self.info_popup and self.info_popup.isVisible():
            self.info_popup.settings_tab.update_updates_block(self.update_info)
        self.apply_theme(get_theme(self.settings))

    def set_update_label(self, has_update):
        if has_update:
            self.version_label.setText("Налична е нова версия!")
            self.version_label.setStyleSheet("color: #206ad8; font-size: 13px; text-decoration:underline; font-family:'Arial'; background: transparent; cursor: pointer;")
        else:
            theme = get_theme(self.settings)
            fg = "#e0e0e0" if theme == "dark" else "#2b2b2b"
            bg = "#222222" if theme == "dark" else "#fafafa"
            self.version_label.setText(f"версия {VERSION}")
            self.version_label.setStyleSheet(f"color: {fg}; font-size: 13px; font-family:'Arial'; background: {bg}; cursor: pointer;")

    def manual_update_check(self):
        self.check_for_updates()
        if self.info_popup and self.info_popup.isVisible():
            self.info_popup.settings_tab.update_updates_block(self.update_info)
        # Return True if update info exists (update available), else False
        return bool(self.update_info)

def main():
    settings = load_settings()
    app = QApplication(sys.argv)

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
    quit_action = QAction("Изход", tray)
    menu.addAction(restore_action)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)


    def tray_activated(reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            toggle_show_hide()

    tray.activated.connect(tray_activated)

    def on_settings_changed(updated_settings):
        save_settings(updated_settings)
        window.apply_theme(get_theme(updated_settings))
        if window.info_popup and window.info_popup.isVisible():
            window.info_popup.apply_theme(get_theme(updated_settings))

    window = ConverterWindow(tray, settings, on_settings_changed)
    window.setWindowIcon(icon)

    window.setWindowTitle(window_title)

    def toggle_show_hide():
        window.dragging = False
        if window.info_popup and window.info_popup.isVisible():
            window.info_popup.close()
            window.info_popup = None
        if window.isVisible():
            window.hide()
        else:
            window.show()
            window.raise_()
            window.activateWindow()
            window.setFocus()

    def update_tray_label():
        if window.isVisible():
            restore_action.setText("Затвори")
        else:
            restore_action.setText("Покажи")

    menu.aboutToShow.connect(update_tray_label)
    restore_action.triggered.connect(toggle_show_hide)

    def open_info_dialog():
        window.show_info_popup()

    quit_action.triggered.connect(app.quit)
    tray.show()

    def cleanup():
        pos = window.pos()
        settings["x"] = pos.x()
        settings["y"] = pos.y()
        settings["minimal_mode"] = window.minimal_mode
        save_settings(settings)
        app.quit()
    app.aboutToQuit.connect(cleanup)

    if settings.get("start_minimized", True):
        window.hide()
    else:
        window.show()
        window.setFocus()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
