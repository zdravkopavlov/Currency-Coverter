import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon

def main():
    app = QApplication(sys.argv)

    # Try your icon, fallback to empty/default
    try:
        icon = QIcon("icon.ico")
        if icon.isNull():
            print("Warning: icon.ico not found or invalid, using default icon.")
            icon = QIcon()
    except Exception as e:
        print("Error loading icon:", e)
        icon = QIcon()

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("PyQt5 Tray Test")

    # Simple menu
    menu = QMenu()
    msg_action = QAction("Show Message", tray)
    quit_action = QAction("Quit", tray)
    menu.addAction(msg_action)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    msg_action.triggered.connect(
        lambda: tray.showMessage("Tray Test", "This is a test notification!", QSystemTrayIcon.Information, 2000)
    )
    quit_action.triggered.connect(app.quit)

    tray.show()

    print("Tray icon created! Right-click for menu. Ctrl+C here to quit if needed.")
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
