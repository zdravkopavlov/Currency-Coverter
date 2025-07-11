import sys
import os
import requests
import tempfile
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

INSTALLER_URL = "https://github.com/zdravkopavlov/Currency-Coverter/releases/download/v2.2.3/BGN-EUR_Converter_Setup_2.2.3.exe"

class DownloadSignals(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

def run_installer_as_admin(installer_path):
    if sys.platform == "win32":
        try:
            import ctypes
            params = ''
            # Show=1 (SW_SHOWNORMAL)
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", installer_path, params, None, 1
            )
            return result > 32
        except Exception as e:
            print(f"Error running as admin: {e}")
            return False
    else:
        return False

class Downloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Изтегли и инсталирай обновлението")
        self.setFixedSize(400, 160)
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel("Изтегли новата версия и инсталирай")
        self.layout.addWidget(self.label)
        
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)
        
        self.button = QPushButton("Изтегли и инсталирай")
        self.button.clicked.connect(self.start_download)
        self.layout.addWidget(self.button)

        self.signals = DownloadSignals()
        self.signals.progress.connect(self.progress.setValue)
        self.signals.finished.connect(self.download_finished)
        self.signals.error.connect(self.download_error)

        self.downloading = False

    def start_download(self):
        if self.downloading:
            return
        self.downloading = True
        self.button.setEnabled(False)
        threading.Thread(target=self.download_file, daemon=True).start()

    def download_file(self):
        url = INSTALLER_URL
        local_filename = os.path.basename(url)
        temp_dir = tempfile.gettempdir()
        dest_path = os.path.join(temp_dir, local_filename)
        try:
            with requests.get(url, stream=True, timeout=10) as r:
                r.raise_for_status()
                total_length = r.headers.get('content-length')
                dl = 0
                if total_length is None:
                    with open(dest_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    self.signals.progress.emit(100)
                else:
                    total_length = int(total_length)
                    with open(dest_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                dl += len(chunk)
                                percent = int(dl * 100 / total_length)
                                self.signals.progress.emit(percent)
            self.signals.finished.emit(dest_path)
        except Exception as e:
            self.signals.error.emit(str(e))

    def download_finished(self, dest_path):
        self.label.setText("Изтеглянето приключи. Стартиране на инсталатора...")
        try:
            if run_installer_as_admin(dest_path):
                self.close()
            else:
                QMessageBox.warning(self, "Грешка", "Неуспешно стартиране като администратор.")
                self.button.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Грешка", f"Неуспешно стартиране на инсталатора:\n{e}")
            self.button.setEnabled(True)
        self.downloading = False

    def download_error(self, message):
        QMessageBox.critical(self, "Грешка", f"Неуспешно изтегляне:\n{message}")
        self.button.setEnabled(True)
        self.downloading = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Downloader()
    w.show()
    sys.exit(app.exec_())
