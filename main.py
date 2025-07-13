# main.py

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QObject

from settings import load_settings, save_settings
from converter_widget import ConverterWidget
from change_widget import ChangeWidget
from dialogs import InfoDialog
from app_window import AppWindow

window_title = "BGN/EUR Converter SingleInstance MainWindow"
VERSION = "2.3.0"

def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(sys.argv[0]), filename)

class MainEventFilter(QObject):
    def __init__(self, app_win, converter, changer, set_minimal_mode, show_info):
        super().__init__()
        self.app_win = app_win
        self.converter = converter
        self.changer = changer
        self.set_minimal_mode = set_minimal_mode
        self.show_info = show_info

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Space, Qt.Key_Tab):
                idx = self.app_win.currentIndex()
                if idx == 0:
                    # Going from converter to changer: set price!
                    try:
                        price = float(self.converter.input_value) if self.converter.input_value else 0.0
                    except ValueError:
                        price = 0.0
                    self.changer.set_price_bgn(price)
                    self.changer.paid_bgn = ""
                    self.changer.update_labels()
                    self.app_win.setCurrentIndex(1)
                    self.changer.setFocus()
                else:
                    self.app_win.setCurrentIndex(0)
                    self.converter.setFocus()
                return True
            if event.key() == Qt.Key_Escape:
                self.app_win.hide()
                return True
            if event.key() == Qt.Key_C and not event.modifiers():
                self.set_minimal_mode(not self.converter.minimal_mode)
                return True
            if event.key() == Qt.Key_F1:
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

    # --- Main custom window ---
    app_win = AppWindow(icon, window_title, always_on_top=settings.get("always_on_top", True))
    converter = ConverterWidget(app_win)
    changer = ChangeWidget(app_win)
    app_win.addWidget(converter)
    app_win.addWidget(changer)

    info_dialog = [None]

    def set_minimal_mode(minimal):
        converter.set_mode(minimal)
        changer.set_mode(minimal)
        if minimal:
            app_win.setFixedSize(300, 50)
        else:
            app_win.setFixedSize(250, 220)

    def show_info():
        if info_dialog[0] is None or not info_dialog[0].isVisible():
            info_dialog[0] = InfoDialog(
                parent=app_win,
                app_settings=settings,
                on_settings_changed=lambda s: save_settings(s)
            )
            info_dialog[0].show()
            info_dialog[0].activateWindow()
            info_dialog[0].setFocus()

    event_filter = MainEventFilter(app_win, converter, changer, set_minimal_mode, show_info)
    app.installEventFilter(event_filter)

    def toggle_show_hide():
        if app_win.isVisible():
            app_win.hide()
        else:
            app_win.show()
            app_win.raise_()
            app_win.activateWindow()
            app_win.setFocus()

    def update_tray_label():
        if app_win.isVisible():
            restore_action.setText("Затвори")
        else:
            restore_action.setText("Покажи")

    menu.aboutToShow.connect(update_tray_label)
    restore_action.triggered.connect(toggle_show_hide)
    quit_action.triggered.connect(app.quit)
    tray.show()

    if settings.get("start_minimized", True):
        app_win.hide()
    else:
        app_win.show()
        app_win.setFocus()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
