import sys
import os
import subprocess
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class InstallThread(QThread):
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)

    def run(self):
        self.update_status.emit("Checking for Python installation...")
        self.update_progress.emit(10)

        if not self.is_python_installed():
            self.update_status.emit("Python not found. Downloading and installing...")
            self.download_and_install_python()
        else:
            self.update_status.emit("Python is already installed.")

        self.update_progress.emit(30)
        self.update_status.emit("Checking for Ollama installation...")

        if not self.is_ollama_installed():
            self.update_status.emit("Ollama not found. Downloading and installing...")
            self.download_and_install_ollama()
        else:
            self.update_status.emit("Ollama is already installed.")

        self.update_progress.emit(50)
        self.update_status.emit("Ensuring Ollama is running...")
        self.run_ollama()

        self.update_progress.emit(70)
        self.update_status.emit("Downloading deepseek-r1:1.5b model...")
        self.download_deepseek_model()

        self.update_progress.emit(90)
        self.update_status.emit("Installing Python dependencies...")
        self.install_requirements()

        self.update_progress.emit(100)
        self.update_status.emit("Setup complete!")

    def is_python_installed(self):
        try:
            subprocess.run(["python", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def download_and_install_python(self):
        url = "https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
        file_name = "python-installer.exe"
        self.download_file(url, file_name)
        subprocess.run([file_name, "/quiet", "InstallAllUsers=1", "PrependPath=1"], check=True)
        os.remove(file_name)

    def is_ollama_installed(self):
        result = subprocess.run(["where", "ollama"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0

    def download_and_install_ollama(self):
        url = "https://ollama.com/download/OllamaSetup.exe"
        file_name = "OllamaSetup.exe"
        self.download_file(url, file_name)
        subprocess.run([file_name, "/silent"], check=True)
        os.remove(file_name)

    def run_ollama(self):
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def download_deepseek_model(self):
        subprocess.run(["ollama", "pull", "deepseek-r1:1.5b"], check=True)

    def install_requirements(self):
        if os.path.exists("requirements.txt"):
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)

    def download_file(self, url, file_name):
        response = requests.get(url, stream=True)
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)


class InstallerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setup Installer")
        self.setGeometry(300, 200, 500, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.status_label = QLabel("Click 'Start Installation' to begin")
        self.layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)

        self.install_button = QPushButton("Start Installation")
        self.install_button.clicked.connect(self.start_installation)
        self.layout.addWidget(self.install_button)

        self.central_widget.setLayout(self.layout)

    def start_installation(self):
        self.install_button.setEnabled(False)
        self.install_thread = InstallThread()
        self.install_thread.update_status.connect(self.update_status)
        self.install_thread.update_progress.connect(self.progress_bar.setValue)
        self.install_thread.start()

    def update_status(self, text):
        self.status_label.setText(text)
        self.log_output.append(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstallerUI()
    window.show()
    sys.exit(app.exec_())
