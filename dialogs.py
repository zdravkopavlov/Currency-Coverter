from version import VERSION

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QComboBox, QPushButton, QSpacerItem, QSizePolicy,
    QTabWidget, QTextBrowser, QDialog, QApplication  # <-- Add QApplication here
)
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QCursor, QPainter, QPainterPath, QBrush, QColor

from settings import get_theme, save_settings
import sys
import os
import markdown

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

        self.chk_auto_copy_result = QCheckBox("Автоматично копирай резултата")
        self.chk_auto_copy_result.setChecked(app_settings.get("auto_copy_result", True))
        self.chk_auto_copy_result.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_auto_copy_result)

        self.chk_remember_last_direction = QCheckBox("Запомни последната посока на конвертиране")
        self.chk_remember_last_direction.setChecked(app_settings.get("remember_last_direction", True))
        self.chk_remember_last_direction.stateChanged.connect(self.save_settings)
        layout.addWidget(self.chk_remember_last_direction)

        theme_row = QHBoxLayout()
        lbl_theme = QLabel("Тема:")
        theme_row.addWidget(lbl_theme)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светла", "Тъмна", "Следвай Windows"])
        self.theme_combo.setCurrentIndex(app_settings.get("theme", 2))
        self.theme_combo.currentIndexChanged.connect(self.save_settings)
        self.theme_combo.setMaximumWidth(120)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        layout.addLayout(theme_row)

        layout.addSpacing(10)

        self.updates_block = QWidget()
        self.updates_layout = QVBoxLayout(self.updates_block)
        self.updates_layout.setContentsMargins(14, 10, 14, 10)
        self.updates_layout.setSpacing(8)
        self.updates_block.setStyleSheet("""
            background: rgba(64,68,80,0.08);
            border-radius: 12px;
        """)
        layout.addWidget(self.updates_block)

        self.chk_auto_check_updates = QCheckBox("Автоматична проверка за обновления")
        self.chk_auto_check_updates.setChecked(app_settings.get("auto_check_updates", True))
        self.chk_auto_check_updates.stateChanged.connect(self.save_settings)
        self.updates_layout.addWidget(self.chk_auto_check_updates)

        self.lbl_current = QLabel(f"Инсталирана версия: {VERSION}")
        self.updates_layout.addWidget(self.lbl_current)

        self.manual_check_btn = QPushButton("Провери за обновления")
        self.manual_check_btn.setCursor(Qt.PointingHandCursor)
        self.manual_check_btn.clicked.connect(self.do_manual_update)
        self.updates_layout.addWidget(self.manual_check_btn)

        self.no_update_label = QLabel("")
        self.no_update_label.setVisible(False)
        self.no_update_label.setStyleSheet("font-size:12px;")
        self.updates_layout.addWidget(self.no_update_label)

        self.lbl_latest = QLabel("")
        self.lbl_latest.setVisible(False)
        self.lbl_latest.setStyleSheet("font-weight: bold")
        self.updates_layout.addWidget(self.lbl_latest)

        self.changelog_label = QLabel()
        self.changelog_label.setVisible(False)
        self.changelog_label.setWordWrap(True)
        self.updates_layout.addWidget(self.changelog_label)

        self.download_button = QPushButton("Изтегли и инсталирай")
        self.download_button.setVisible(False)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.launch_downloader)
        self.updates_layout.addWidget(self.download_button)

        layout.addItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)
        self.update_updates_block()
        self.apply_theme(get_theme(self.app_settings))

    def save_settings(self):
        self.app_settings["start_with_windows"] = self.chk_start_windows.isChecked()
        self.app_settings["start_minimized"] = self.chk_start_minimized.isChecked()
        self.app_settings["theme"] = self.theme_combo.currentIndex()
        self.app_settings["auto_check_updates"] = self.chk_auto_check_updates.isChecked()
        self.app_settings["auto_copy_result"] = self.chk_auto_copy_result.isChecked()
        self.app_settings["remember_last_direction"] = self.chk_remember_last_direction.isChecked()
        if self.on_settings_changed:
            self.on_settings_changed(self.app_settings)
        if self.parent_window:
            self.parent_window.apply_theme(get_theme(self.app_settings))
        self.update_updates_block()

    def launch_downloader(self):
        try:
            from PyQt5.QtWidgets import QApplication
            import subprocess
            downloader_path = os.path.join(os.path.dirname(sys.argv[0]), "update.py")
            if not os.path.exists(downloader_path):
                downloader_path = os.path.join(os.path.dirname(sys.argv[0]), "update.exe")
            if os.path.exists(downloader_path):
                if downloader_path.endswith(".py"):
                    subprocess.Popen([sys.executable, downloader_path])
                else:
                    subprocess.Popen([downloader_path])
                QApplication.quit()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Грешка", "Файлът за обновление не е намерен.")
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Грешка", f"Неуспешно стартиране на обновлението:\n{e}")

    def update_updates_block(self, info=None):
        if info is None:
            info = self.update_info
        self.manual_check_btn.setVisible(not self.chk_auto_check_updates.isChecked())
        self.no_update_label.setVisible(False)
        self.lbl_latest.setVisible(False)
        self.changelog_label.setVisible(False)
        self.download_button.setVisible(False)

        if info:
            self.lbl_latest.setText(f"Налична версия: {info['version']}")
            self.lbl_latest.setVisible(True)
            changelog = info.get("changelog")
            if changelog:
                first_lines = "\n".join(changelog.strip().splitlines()[:3])
                self.changelog_label.setText(f"<span style='color:#888;'>{first_lines}</span>")
                self.changelog_label.setVisible(True)
            dl_url = info.get("download_url")
            if dl_url:
                self.download_button.setVisible(True)
        elif hasattr(self, 'last_manual_check') and self.last_manual_check:
            self.no_update_label.setText("Няма налични нови обновления.")
            self.no_update_label.setVisible(True)

    def apply_theme(self, theme):
        if theme == "dark":
            self.no_update_label.setStyleSheet("font-size:12px; color:#eeeeee;")
            btn_style = (
                "QPushButton { background: #313640; color: #eee; border-radius: 8px; font-size: 15px; padding: 10px 0; }"
                "QPushButton:hover { background: #374151; }"
                "QPushButton:pressed { background: #2d3848; }"
            )
            self.updates_block.setStyleSheet("background: rgba(64,68,80,0.13); border-radius: 12px;")
        else:
            self.no_update_label.setStyleSheet("font-size:12px; color:#000000;")
            btn_style = (
                "QPushButton { background: #e8e8e8; color: #223; border-radius: 8px; font-size: 15px; padding: 10px 0; }"
                "QPushButton:hover { background: #d4d4d4; }"
                "QPushButton:pressed { background: #c3c3c3; }"
            )
            self.updates_block.setStyleSheet("background: rgba(64,68,80,0.08); border-radius: 12px;")
        self.manual_check_btn.setStyleSheet(btn_style)
        self.download_button.setStyleSheet(btn_style)

    def do_manual_update(self):
        if self.manual_update_callback:
            info = self.manual_update_callback()
            self.update_info = info
            self.last_manual_check = True
            self.update_updates_block()

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
        if theme == "dark":
            self.help_browser.setStyleSheet("background:#333333; color:#e0e0e0;")
            self.about_browser.setStyleSheet("background:#333333; color:#e0e0e0;")
        else:
            self.help_browser.setStyleSheet("background:#fafafa; color:#2b2b2b;")
            self.about_browser.setStyleSheet("background:#fafafa; color:#2b2b2b;")
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
