import os
from PyQt5.QtCore import QUrl, QSize, QThread, pyqtSignal, Qt, QTimer, QPoint
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton,
    QHBoxLayout, QTabWidget, QToolButton, QTabBar, QShortcut, QSplitter,
    QTextEdit, QLabel, QProgressBar, QComboBox, QFrame
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtGui import QColor, QPalette, QIcon, QKeySequence, QFont

import requests
import json
import sys

def chat_with_ollama(prompt, model="deepseek-r1:8b"):
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json", "charset":"UTF-8"}
    data = {"model": model, "prompt": prompt, "stream": True}
    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
    if response.status_code != 200:
        sys.stdout.write(f"Error: {response.status_code}, {response.text}\n")
        sys.stdout.flush()
        return
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            dec=json.loads(chunk.decode('utf-8'))
            yield dec["response"]

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class AIWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, text, model):
        super().__init__()
        self.text = text
        self.model = model
        self._is_running = True

    def run(self):
        try:
            for chunk in chat_with_ollama(self.text, self.model):
                if not self._is_running:
                    break
                self.chunk_received.emit(chunk)
            self.finished.emit()
        except Exception as e:
            self.chunk_received.emit("\n<finish>")
            self.finished.emit()

    def stop(self):
        self._is_running = False

class WebTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        self.splitter = QSplitter(Qt.Horizontal)
        self.web_view = QWebEngineView()
        self.splitter.addWidget(self.web_view)
        self.ai_panel = AISidePanel()
        self.splitter.addWidget(self.ai_panel)
        self.splitter.setSizes([700, 300])

        layout.addWidget(self.splitter)
        layout.setContentsMargins(0, 0, 0, 0)

COLORS = {
    'bg_primary': '#1E1E1E',
    'bg_secondary': '#1E1E1E',
    'bg_tertiary': '#3A3A3F',
    'accent': '#198754',
    'accent_hover': '#209055',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B0B0',
    'danger': '#E53935',
    'success': '#43A047'
}
class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(8)
        self.button_container = QWidget()
        self.button_container.setFixedWidth(70)
        button_layout = QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        self.close_button = QPushButton()
        self.minimize_button = QPushButton()
        self.maximize_button = QPushButton()

        for button in [self.close_button, self.minimize_button, self.maximize_button]:
            button.setFixedSize(12, 12)

        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.minimize_button)
        button_layout.addWidget(self.maximize_button)
        button_layout.addStretch()

        self.title = QLabel("New Tab - Chronico")
        self.title.setAlignment(Qt.AlignCenter)

        self.close_button.clicked.connect(self.parent.close)
        self.minimize_button.clicked.connect(self.parent.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximize)

        self.layout.addWidget(self.button_container)
        self.layout.addWidget(self.title)
        self.layout.addSpacing(70)

        self.setFixedHeight(38)
        self.start = QPoint(0, 0)
        self.pressing = False

        self.setStyleSheet(f"""
            TitleBar {{
                background-color: {COLORS['bg_primary']};
                border-bottom: 1px solid {COLORS['bg_tertiary']};
            }}

            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                letter-spacing: -0.01em;

            }}

            QPushButton {{
                border: none;
                border-radius: 6px;
            }}

            QPushButton#close {{
                background-color: #ff5f57;
            }}
            QPushButton#close:hover {{
                background-color: #ff7369;
            }}

            QPushButton#minimize {{
                background-color: #febc2e;
            }}
            QPushButton#minimize:hover {{
                background-color: #fec84a;
            }}

            QPushButton#maximize {{
                background-color: #28c940;
            }}
            QPushButton#maximize:hover {{
                background-color: #3ed955;
            }}

            QPushButton:pressed {{
                opacity: 0.8;
            }}
        """)

        self.close_button.setObjectName("close")
        self.minimize_button.setObjectName("minimize")
        self.maximize_button.setObjectName("maximize")

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.button_container.geometry().contains(event.pos()):
            self.start = self.mapToGlobal(event.pos())
            self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            if self.parent.isMaximized():
                self.parent.showNormal()
                ratio = event.pos().x() / self.width()
                new_x = int(self.parent.width() * ratio)
                self.start = QPoint(new_x, event.pos().y())

            end = self.mapToGlobal(event.pos())
            movement = end - self.start

            pos = self.parent.pos()
            self.parent.move(pos.x() + movement.x(), pos.y() + movement.y())
            self.start = end

    def mouseReleaseEvent(self, event):
        self.pressing = False

    def mouseDoubleClickEvent(self, event):
        if not self.button_container.geometry().contains(event.pos()):
            self.toggle_maximize()
class AISidePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.models = [
            "deepseek-r1:1.5b",
            "deepseek-r1",
            "deepseek-r1:8b",
            "llama3.2"
        ]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        self.model_selector = QComboBox()
        self.model_selector.addItems(self.models)
        self.model_selector.setFixedHeight(43)

        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("Type your question or press Ctrl+Shift+A to analyze current page...")
        self.input_area.setMaximumHeight(100)

        self.progress = QProgressBar()
        self.progress.setMaximumHeight(2)
        self.progress.setTextVisible(False)
        self.progress.hide()

        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.send_button = QPushButton("Send")
        self.stop_button = QPushButton("Stop")
        self.stop_button.hide()

        controls_layout.addWidget(self.send_button)
        controls_layout.addWidget(self.stop_button)
        layout.addWidget(self.model_selector)
        layout.addWidget(self.input_area)
        layout.addWidget(self.progress)
        layout.addLayout(controls_layout)
        layout.addWidget(self.response_area)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
            }}
            QTextEdit {{
                background-color: {COLORS['bg_tertiary']};
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            QLabel {{
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 4px;
            }}
            QPushButton {{
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton#send {{
                background-color: {COLORS['accent']};
                color: {COLORS['text_primary']};
            }}
            QPushButton#send:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            QPushButton#stop {{
                background-color: {COLORS['danger']};
                color: {COLORS['text_primary']};
            }}
            QProgressBar {{
                background-color: {COLORS['bg_tertiary']};
                border: none;
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 1px;
            }}
            QComboBox {{
                background-color: {COLORS['bg_tertiary']};
                border: none;
                padding: 0 8px;
                border-radius: 8px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            QComboBox::drop-down:button {{
                border-radius: 8px;
            }}
        """)
        self.send_button.setObjectName("send")
        self.stop_button.setObjectName("stop")

    @property
    def model(self):
        return self.model_selector.currentText()

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.new_tab_path = QUrl().fromLocalFile(os.path.abspath("templates/new_tab.html"))
        self.init_ui()
        self.current_worker = None
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def init_ui(self):
        self.setWindowTitle("Chronico")
        self.setGeometry(100, 100, 1280, 720)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(8, 2, 8, 0)
        self.title_bar = TitleBar(self)
        self.layout.addWidget(self.title_bar)
        self.browser_container = QWidget()
        self.browser_layout = QVBoxLayout(self.browser_container)
        self.browser_layout.setSpacing(8)
        self.browser_layout.setContentsMargins(12, 12, 12, 6)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(8)

        nav_buttons = [
            ("←", lambda: self.tabs.currentWidget().web_view.back()),
            ("→", lambda: self.tabs.currentWidget().web_view.forward()),
            ("↻", lambda: self.tabs.currentWidget().web_view.reload())
        ]

        for symbol, action in nav_buttons:
            btn = QPushButton(symbol)
            btn.setFixedSize(36, 36)
            btn.clicked.connect(action)
            self.nav_layout.addWidget(btn)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search or enter URL")
        self.nav_layout.addWidget(self.search_bar)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.new_tab_button = QToolButton(self)
        self.new_tab_button.setText("+")
        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.tabs.setCornerWidget(self.new_tab_button, Qt.TopRightCorner)

        self.layout.addLayout(self.nav_layout)
        self.layout.addWidget(self.tabs)
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
            QTabWidget::pane {{
                border: none;
                background: {COLORS['bg_primary']};
            }}
            QTabBar::tab {{
                padding: 8px 24px;
                background: {COLORS['bg_secondary']};
                border-radius: 8px 8px 0 0;
                color: {COLORS['text_primary']};
                margin-right: 2px;
                font-size: 11px;
                margin-bottom:2px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
            }}
            QTabBar::close-button {{
                image: url(close_icon.png);
                subcontrol-position: right;
                margin-right: 4px;
            }}
            QLineEdit {{
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                font-size: 14px;
                width : 100%;
            }}
            QPushButton {{
                background: {COLORS['bg_tertiary']};
                border: none;
                border-radius: 8px;
                color: {COLORS['text_primary']};
                font-size: 16px;
                padding-bottom:5px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_secondary']};
            }}
            QToolButton {{
                background: {COLORS['bg_tertiary']};
                border: none;
                border-radius: 8px;
                color: {COLORS['text_primary']};
                font-size: 16px;
                padding: 4px 8px;
            }}
            QToolButton:hover {{
                background: {COLORS['bg_secondary']};
            }}
            QMainWindow {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['bg_tertiary']};
                border-radius: 8px;
                padding:10px;
            }}

        """)
        self.layout.addWidget(self.browser_container)

        self.add_new_tab()
        self.search_bar.returnPressed.connect(self.navigate_to_url)
        self.tabs.currentChanged.connect(self.tab_changed)

        QShortcut(QKeySequence("Ctrl+T"), self, self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+Shift+A"), self, self.analyze_current_page)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.move_page_to_ai_search)

    def move_page_to_ai_search(self):
        current_tab = self.tabs.currentWidget()
        if not current_tab:
            return

        web_view = current_tab.web_view
        ai_panel = current_tab.ai_panel

        def handle_page_content(content):
            ai_panel.input_area.setText(content)

        web_view.page().toPlainText(handle_page_content)

    def add_new_tab(self):
        new_tab = WebTab()
        index = self.tabs.addTab(new_tab, "New Tab")
        self.tabs.setCurrentIndex(index)

        web_view = new_tab.web_view
        web_view.loadFinished.connect(lambda: self.update_tab_info(web_view))
        web_view.setUrl(self.new_tab_path)

        ai_panel = new_tab.ai_panel
        ai_panel.send_button.clicked.connect(lambda: self.process_ai_request(ai_panel))
        ai_panel.stop_button.clicked.connect(self.stop_ai_request)

        return new_tab

    def stop_ai_request(self):
        if self.current_worker:
            self.current_worker.stop()
            current_tab = self.tabs.currentWidget()
            ai_panel = current_tab.ai_panel
            ai_panel.stop_button.hide()
            ai_panel.send_button.show()
            ai_panel.progress.hide()

    def process_ai_request(self, ai_panel : AISidePanel):
        ai_panel.progress.show()
        ai_panel.send_button.hide()
        ai_panel.stop_button.show()
        ai_panel.response_area.clear()

        self.current_worker = AIWorker(ai_panel.input_area.toPlainText(), model = ai_panel.model)
        ai_panel.input_area.setText("")

        self.current_worker.chunk_received.connect(lambda chunk: self.handle_ai_chunk(chunk, ai_panel))
        self.current_worker.finished.connect(lambda: self.handle_ai_finished(ai_panel))
        self.current_worker.start()

    def handle_ai_chunk(self, chunk, ai_panel):
        cursor = ai_panel.response_area.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        ai_panel.response_area.setTextCursor(cursor)

    def handle_ai_finished(self, ai_panel):
        ai_panel.progress.hide()
        ai_panel.stop_button.hide()
        ai_panel.send_button.show()
        self.current_worker = None

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.add_new_tab()

    def navigate_to_url(self):
        url = self.search_bar.text().strip()
        if not url.startswith(("http://", "https://", "file://")):
            if "." in url:
                url = "https://" + url
            else:
                url = f"https://www.google.com/search?q={url}"

        current_tab = self.tabs.currentWidget()
        current_tab.web_view.setUrl(QUrl(url))

    def update_tab_info(self, web_view):
        index = self.tab_index_from_web_view(web_view)
        if index >= 0:
            title = web_view.title()
            if title:
                self.tabs.setTabText(index, title[:20] + "..." if len(title) > 20 else title)
                self.title_bar.title.setText(title + " - Chronico" if len(title)<=20 else title[:20]+"..." + " - Chronico")
            self.search_bar.setText(web_view.url().toString())

    def tab_index_from_web_view(self, web_view):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).web_view == web_view:
                return i
        return -1

    def tab_changed(self, index):
        if index >= 0:
            current_tab = self.tabs.widget(index)
            self.search_bar.setText(current_tab.web_view.url().toString())
            title = current_tab.web_view.title()
            self.title_bar.title.setText(title + " - Chronico" if len(title)<=20 else title[:20]+"..." + " - Chronico")

    def analyze_current_page(self):
        current_tab = self.tabs.currentWidget()
        current_tab.web_view.page().toPlainText(lambda text: self.handle_page_content(text, current_tab.ai_panel))

    def handle_page_content(self, text, ai_panel):
        ai_panel.input_area.setText(f"Summarize this page content:\n\n{text}...")
        self.process_ai_request(ai_panel)

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('logo.svg'))

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1E1E1E"))
    palette.setColor(QPalette.WindowText, QColor("white"))
    app.setPalette(palette)

    browser = Browser()
    browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
