VERSION = "2.3.0"

import sys
import os
import requests
import json
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QObject

from settings import load_settings, save_settings, get_theme
from calculator import eur_to_bgn  # For correct BGN computation
from converter_widget import ConverterWidget
from change_widget import ChangeWidget
from dialogs import InfoDialog
from app_window import AppWindow

window_title = "BGN/EUR Converter SingleInstance MainWindow"
UPDATE_URL = "https://raw.githubusercontent.com/zdravkopavlov/Currency-Coverter/main/latest_version.json"

def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(sys.argv[0]), filename)

def check_for_update(current_version, url=UPDATE_URL):
    try:
        r = requests.get(url, timeout=4)
        data = r.json()
        latest = data.get("version")
        if latest and latest != current_version:
            return data
        return None
    except Exception as e:
        print("Update check failed:", e)
        return None

def apply_theme_main(app_win, converter, changer, theme_name):
    if theme_name == "dark":
        fg = "#e0e0e0"
        bg = "#222222"
    else:
        fg = "#2b2b2b"
        bg = "#fafafa"
    app_win.set_bg_color(bg)
    converter.input_label.setStyleSheet(f"color:{fg}; background:transparent;")
    converter.output_label.setStyleSheet(f"color:{fg}; background:transparent;")
    converter.set_version_label_color(fg)
    changer.rest_label.setStyleSheet(f"color:{fg};")
    changer.change_label.setStyleSheet(f"color:{fg}; background:transparent;")
    changer.set_version_label_color(fg)
    app_win.update()

class MainEventFilter(QObject):
    def __init__(self, app_win, converter, changer, set_minimal_mode, show_info, toggle_always_on_top, set_update_available, settings, apply_theme):
        super().__init__()
        self.app_win = app_win
        self.converter = converter
        self.changer = changer
        self.set_minimal_mode = set_minimal_mode
        self.show_info = show_info
        self.toggle_always_on_top = toggle_always_on_top
        self.set_update_available = set_update_available
        self.settings = settings
        self.apply_theme = apply_theme

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            idx = self.app_win.currentIndex()
            if event.key() == Qt.Key_Tab:
                if idx == 0:
                    # Go to change page
                    try:
                        if self.converter.bgn_to_eur_mode:
                            price = float(self.converter.input_value) if self.converter.input_value else 0.0
                        else:
                            price = eur_to_bgn(float(self.converter.input_value)) if self.converter.input_value else 0.0
                    except ValueError:
                        price = 0.0
                    self.changer.set_price_bgn(price)
                    self.changer.paid_bgn = ""
                    self.changer.update_labels()
                    self.app_win.setCurrentIndex(1)
                    self.changer.setFocus()
                else:
                    # Go to converter page
                    self.app_win.setCurrentIndex(0)
                    self.converter.setFocus()
                return True
            elif event.key() == Qt.Key_C and not event.modifiers():
                self.set_minimal_mode(not self.converter.minimal_mode, save=True)
                return True
            elif event.key() == Qt.Key_A and not event.modifiers():
                self.toggle_always_on_top()
                self.settings["always_on_top"] = self.app_win._always_on_top
                save_settings(self.settings)
                return True
            elif event.key() == Qt.Key_F1:
                self.show_info()
                return True
        return False

def main():
    settings = load_settings()
    app = QApplication(sys.argv)

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

    # Main custom window
    app_win = AppWindow(icon, window_title, always_on_top=settings.get("always_on_top", True))
    converter = ConverterWidget(app_win, settings)
    changer = ChangeWidget(app_win, settings)

    # Set direction from settings as soon as widget is created (do not touch again)
    converter.bgn_to_eur_mode = settings.get("last_direction_bgn_to_eur", True)
    converter.update_labels()

    app_win.addWidget(converter)
    app_win.addWidget(changer)

    info_dialog = [None]
    update_info = [None]

    # Minimal mode
    def set_minimal_mode(minimal, save=False):
        converter.set_mode(minimal)
        changer.set_mode(minimal)
        if minimal:
            app_win.setFixedSize(325, 50)
        else:
            app_win.setFixedSize(250, 220)
        if save:
            settings["minimal_mode"] = minimal
            save_settings(settings)

    # Apply theme to all
    def apply_theme(theme_name):
        apply_theme_main(app_win, converter, changer, theme_name)
        app_win.update()

    # Settings/info dialog
    def show_info(tab=None):
        if info_dialog[0] is None or not info_dialog[0].isVisible():
            info_dialog[0] = InfoDialog(
                parent=app_win,
                app_settings=settings,
                on_settings_changed=lambda s: [save_settings(s), apply_theme(get_theme(s))],
                update_info=update_info[0],
                manual_update_callback=manual_update
            )
            info_dialog[0].show()
            info_dialog[0].activateWindow()
            info_dialog[0].setFocus()
        if tab == "updates":
            info_dialog[0].tabs.setCurrentIndex(0)

    converter.set_open_updates_callback(lambda: show_info("updates"))
    changer.set_open_updates_callback(lambda: show_info("updates"))

    # Update logic
    def set_update_available(info):
        is_update = bool(info)
        converter.set_update_available(is_update)
        changer.set_update_available(is_update)

    # Manual update logic
    def manual_update():
        info = check_for_update(VERSION)
        update_info[0] = info
        set_update_available(info)
        return info

    # Event filter
    event_filter = MainEventFilter(
        app_win, converter, changer,
        set_minimal_mode, show_info,
        app_win.toggle_always_on_top, set_update_available,
        settings, apply_theme
    )
    app.installEventFilter(event_filter)

    # Tray logic
    def toggle_show_hide():
        if app_win.isVisible():
            app_win.hide()
        else:
            app_win.show()
            app_win.raise_()
            app_win.activateWindow()
            app_win.setFocus()

    def tray_activated(reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            toggle_show_hide()

    tray.activated.connect(tray_activated)

    def update_tray_label():
        if app_win.isVisible():
            restore_action.setText("Затвори")
        else:
            restore_action.setText("Покажи")

    menu.aboutToShow.connect(update_tray_label)
    restore_action.triggered.connect(toggle_show_hide)
    quit_action.triggered.connect(app.quit)
    tray.show()

    # Save dialog position/state on close/hide
    def cleanup():
        pos = app_win.pos()
        settings["x"] = pos.x()
        settings["y"] = pos.y()
        settings["minimal_mode"] = converter.minimal_mode
        save_settings(settings)

    app.aboutToQuit.connect(cleanup)

    # Restore dialog position/state/theme/minimal
    x, y = settings.get("x"), settings.get("y")
    if x is not None and y is not None:
        app_win.move(x, y)
    minimal_mode = settings.get("minimal_mode", False)
    set_minimal_mode(minimal_mode)

    theme_name = get_theme(settings)
    apply_theme(theme_name)

    # Show/hide logic at start
    if settings.get("start_minimized", True):
        app_win.hide()
    else:
        app_win.show()
        app_win.setFocus()

    # Initial auto update check
    if settings.get("auto_check_updates", True):
        info = check_for_update(VERSION)
        update_info[0] = info
        set_update_available(info)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
