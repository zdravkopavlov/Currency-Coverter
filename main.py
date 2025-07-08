import sys
import os
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PyQt5.QtGui import QIcon
from carousel import CarouselWidget
print("Carousel loaded from:", CarouselWidget.__module__)
from converter import ConverterPage
from settings import SettingsPage
from about import AboutPage
from PyQt5.QtCore import Qt

# ---- One Instance Lock ----
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

    # Create carousel window with 3 pages
    window = CarouselWidget([
        ConverterPage(),
        SettingsPage(),
        AboutPage()
    ])

    # Minimize to tray logic
    def show_and_raise():
        window.show()
        window.activateWindow()
        window.raise_()

    restore_action.triggered.connect(show_and_raise)
    quit_action.triggered.connect(app.quit)
    tray.activated.connect(
        lambda reason: show_and_raise() if reason == QSystemTrayIcon.Trigger else None
    )
    tray.show()

    # Minimize-to-tray on close
    def close_event(event):
        event.ignore()
        window.hide()
        tray.showMessage(
            "Конвертор е скрит",
            "Щракнете върху иконата в системния трей, за да възстановите.",
            QSystemTrayIcon.Information,
            2000
        )
    window.closeEvent = close_event

    # Make sure release_lock is called on exit
    def cleanup():
        release_lock()
        app.quit()
    app.aboutToQuit.connect(cleanup)

    window.setWindowTitle("BGN/EUR Конвертор")
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
