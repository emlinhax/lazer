import sys
import time
import base64
import requests
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    QProgressBar, QHBoxLayout, QMessageBox, QListWidget, QListWidgetItem, 
    QScrollArea, QGroupBox, QAbstractItemView, QDialogButtonBox
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize

BASE_URL = "https://discord.com/api/v9"

TOOLTIP_STYLE = """
QToolTip { 
    background-color: #2b2d31;
    color: #dcddde;
    border: 1px solid #40444b;
    padding: 8px;
    border-radius: 4px;
    font-size: 12px;
}
"""

class DataFetcher(QThread):
    data_loaded = pyqtSignal(list, list)
    error_occurred = pyqtSignal(str)

    def __init__(self, token):
        super().__init__()
        self.token = token
        self.headers = {"Authorization": self.token}

    def run(self):
        try:
            dms = self.fetch_dms()
            servers = self.fetch_servers()
            self.data_loaded.emit(dms, servers)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def fetch_dms(self):
        try:
            dms = []
            channels = requests.get(f"{BASE_URL}/users/@me/channels", headers=self.headers).json()
            for ch in channels:
                if ch["type"] in [1, 3]:
                    recipients = [u["username"] for u in ch.get("recipients", [])]
                    # get timestamp for sorting
                    last_message_id = ch.get('last_message_id')
                    if last_message_id:
                        timestamp = (int(last_message_id) >> 22) + 1420070400000
                    else:
                        channel_id = int(ch['id'])
                        timestamp = (channel_id >> 22) + 1420070400000
                    dms.append({
                        "id": ch["id"],
                        "name": "DM with " + ", ".join(recipients),
                        "type": "dm",
                        "timestamp": timestamp
                    })
            # forgot this lowkey
            dms.sort(key=lambda x: x['timestamp'], reverse=True)
            return dms
        except Exception as e:
            print(f"Error fetching DMs: {e}")
            return []

    def fetch_servers(self):
        try:
            servers = []
            guilds = requests.get(f"{BASE_URL}/users/@me/guilds", headers=self.headers).json()
            for guild in guilds:
                servers.append({
                    "id": guild["id"],
                    "name": guild["name"],
                    "type": "server"
                })
            return servers
        except Exception as e:
            print(f"Error fetching servers: {e}")
            return []

class DeletionWorker(QThread):
    update_progress = pyqtSignal(int, int, str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str, str)

    def __init__(self, token, channels):
        super().__init__()
        self.token = token
        self.channels = channels
        self.running = True
        self.headers = {"Authorization": self.token}
        self.user_id = None

    def run(self):
        try:
            self.user_id = self.get_user_id()
            total = len(self.channels)
            
            for idx, channel in enumerate(self.channels):
                if not self.running:
                    break
                
                try:
                    if channel["type"] == "dm":
                        self.process_dm(channel)
                    elif channel["type"] == "server":
                        self.process_server(channel)
                    
                    self.update_progress.emit(idx + 1, total, channel["name"])
                except Exception as e:
                    self.error_occurred.emit(str(e), channel["name"])
            
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e), "Global")

    def get_user_id(self):
        try:
            return requests.get(f"{BASE_URL}/users/@me", headers=self.headers).json()["id"]
        except:
            raise ValueError("Failed to get user ID")

    def process_dm(self, channel):
        self.delete_messages(channel["id"], channel["name"])

    def process_server(self, server):
        try:
            channels = requests.get(
                f"{BASE_URL}/guilds/{server['id']}/channels",
                headers=self.headers
            ).json()
            
            for ch in channels:
                if ch["type"] in [0, 5]:
                    self.delete_messages(ch["id"], f"{server['name']}/#{ch['name']}")
        except Exception as e:
            raise Exception(f"Server error: {str(e)}")

    def delete_messages(self, channel_id, context):
        before = None
        while self.running:
            params = {"limit": 100}
            if before:
                params["before"] = before
                
            try:
                messages = requests.get(
                    f"{BASE_URL}/channels/{channel_id}/messages",
                    headers=self.headers,
                    params=params
                ).json()
                
                for msg in messages:
                    if msg["author"]["id"] == self.user_id:
                        self.delete_message(msg["id"], channel_id)
                        time.sleep(0.95)
                
                if len(messages) < 100:
                    break
                before = messages[-1]["id"]
            except Exception as e:
                raise Exception(f"Message deletion failed: {str(e)}")

    def delete_message(self, message_id, channel_id):
        try:
            response = requests.delete(
                f"{BASE_URL}/channels/{channel_id}/messages/{message_id}",
                headers=self.headers
            )
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                time.sleep(retry_after)
                self.delete_message(message_id, channel_id)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")

    def stop(self):
        self.running = False

class ChannelSelector(QDialog):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.setWindowTitle("Select Channels")
        self.setFixedSize(600, 400)
        self.set_background_image()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        self.loading_label = QLabel("Loading channels...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            color: black;
            font-size: 14px;
            background-color: rgba(255, 255, 255, 0.3);
            border-radius: 5px;
            padding: 8px;
        """)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)
        self.scroll_area.hide()
        
        layout.addWidget(self.loading_label)
        layout.addWidget(self.scroll_area)
        
        self.fetcher = DataFetcher(token)
        self.fetcher.data_loaded.connect(self.populate_ui)
        self.fetcher.error_occurred.connect(self.show_error)
        self.fetcher.start()

    def set_background_image(self):
        pixmap = QPixmap("background.jpg")
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)

    def populate_ui(self, dms, servers):
        self.loading_label.hide()
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        self.scroll_area.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        dm_group = QGroupBox("Direct Messages")
        dm_group.setStyleSheet("""
            QGroupBox {
                color: black;
                font-size: 14px;
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        dm_layout = QVBoxLayout(dm_group)
        self.dm_list = QListWidget()
        self.dm_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: black;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.dm_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        for dm in dms:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, dm)
            item.setSizeHint(QSize(0, 40))
            widget = self.create_list_item(dm["name"])
            self.dm_list.addItem(item)
            self.dm_list.setItemWidget(item, widget)
        
        dm_layout.addWidget(self.dm_list)
        
        server_group = QGroupBox("Servers")
        server_group.setStyleSheet(dm_group.styleSheet())
        server_layout = QVBoxLayout(server_group)
        self.server_list = QListWidget()
        self.server_list.setStyleSheet(self.dm_list.styleSheet())
        self.server_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        for server in servers:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, server)
            item.setSizeHint(QSize(0, 40))
            widget = self.create_list_item(server["name"])
            self.server_list.addItem(item)
            self.server_list.setItemWidget(item, widget)
        
        server_layout.addWidget(self.server_list)
        
        content_layout.addWidget(dm_group)
        content_layout.addWidget(server_group)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)

        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("OK")

        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3);
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """
        cancel_btn.setStyleSheet(button_style)
        ok_btn.setStyleSheet(button_style)

        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()

        self.layout().addLayout(button_layout)
        self.scroll_area.show()

    def create_list_item(self, name):
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            color: black;
            font-size: 13px;
            background-color: transparent;
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        return widget

    def show_error(self, message):
        QMessageBox.critical(self, "Error", f"Failed to load data:\n{message}")
        self.reject()

    def get_selected(self):
        selected = []
        for i in range(self.dm_list.count()):
            if self.dm_list.item(i).isSelected():
                selected.append(self.dm_list.item(i).data(Qt.ItemDataRole.UserRole))
        for i in range(self.server_list.count()):
            if self.server_list.item(i).isSelected():
                selected.append(self.server_list.item(i).data(Qt.ItemDataRole.UserRole))
        return selected

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Lazer")
        self.setFixedSize(350, 150)
        self.set_background_image()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)

        self.token_label = QLabel("Enter Token")
        self.token_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.token_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.token_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 6px;
            margin: 0 30px;
        """)

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setFont(QFont("Arial", 12))
        self.token_input.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 5px;
            padding: 8px;
            color: black;
        """)

        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(28, 28)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 14px;
                color: black;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.help_btn.clicked.connect(self.show_help)

        self.visibility_btn = QPushButton("👁")
        self.visibility_btn.setFixedSize(28, 28)
        self.visibility_btn.setStyleSheet(self.help_btn.styleSheet())
        self.visibility_btn.clicked.connect(self.toggle_visibility)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.help_btn)
        btn_layout.addWidget(self.token_input)
        btn_layout.addWidget(self.visibility_btn)

        self.login_btn = QPushButton("Login")
        self.login_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.login_btn.setFixedSize(120, 40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3);
                color: black;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.login_btn.clicked.connect(self.accept)

        layout.addWidget(self.token_label)
        layout.addLayout(btn_layout)
        layout.addWidget(self.login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        self.cached_token = self.load_cached_token()
        if self.cached_token:
            self.token_input.setText(self.cached_token)

    def set_background_image(self):
        pixmap = QPixmap("background.jpg")
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)

    def toggle_visibility(self):
        current = self.token_input.echoMode()
        new_mode = QLineEdit.EchoMode.Normal if current == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password
        self.token_input.setEchoMode(new_mode)

    def show_help(self):
        help_text = """<b>How to Get Your Discord Token:</b>
        <ol>
            <li>Open Discord in your browser</li>
            <li>Press Ctrl+Shift+I to open developer tools</li>
            <li>Go to the Network tab</li>
            <li>Send a message in any DM</li>
            <li>Look for "messages" requests</li>
            <li>Check request headers for "authorization"</li>
        </ol>"""
        
        msg = QMessageBox()
        msg.setWindowTitle("Token Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()

    def load_cached_token(self):
        try:
            with open(".token_cache", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""

    def get_token(self):
        return self.token_input.text()

    def accept(self):
        token = self.get_token()
        if token:
            with open(".token_cache", "w") as f:
                f.write(token)
        super().accept()

class MainWindow(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Lazer")
        self.setFixedSize(500, 200)
        self.set_background_image()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)

        self.status_label = QLabel(f"Welcome, {self.get_username()}")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 8px;
            margin: 20 70px;
        """)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: rgba(88, 101, 242, 0.9);
                border-radius: 5px;
            }
        """)

        self.select_btn = QPushButton("Select Channels")
        self.select_btn.setFixedSize(140, 40)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3);
                color: black;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.select_btn.clicked.connect(self.show_selector)

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setFixedSize(140, 40)
        self.logout_btn.setStyleSheet(self.select_btn.styleSheet())
        self.logout_btn.clicked.connect(self.confirm_logout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.logout_btn)
        btn_layout.addWidget(self.select_btn)
        btn_layout.addStretch()

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def set_background_image(self):
        pixmap = QPixmap("background.jpg")
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)

    def get_username(self):
        try:
            response = requests.get(f"{BASE_URL}/users/@me", headers={"Authorization": self.token})
            return response.json().get("username", "User")
        except:
            return "Unknown User"

    def confirm_logout(self):
        confirm = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.hide()
            login_window = LoginWindow()
            if login_window.exec() == QDialog.DialogCode.Accepted:
                MainWindow(login_window.get_token()).show()

    def show_selector(self):
        selector = ChannelSelector(self.token)
        if selector.exec() == QDialog.DialogCode.Accepted:
            selected = selector.get_selected()
            if selected:
                self.start_deletion(selected)

    def start_deletion(self, channels):
        if self.worker and self.worker.isRunning():
            return

        self.worker = DeletionWorker(self.token, channels)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

        self.select_btn.setEnabled(False)
        self.select_btn.setText("Deleting...")

    def update_progress(self, current, total, name):
        self.progress_bar.setValue(int((current / total) * 100))
        self.status_label.setText(f"Cleaning {name}")

    def on_finished(self):
        self.select_btn.setEnabled(True)
        self.select_btn.setText("Select Channels")
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Welcome, {self.get_username()}")
        QMessageBox.information(self, "Complete", "Cleaning process finished!")

    def show_error(self, error, context):
        self.on_finished()
        QMessageBox.critical(self, "Error", f"Error in {context}:\n{error}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(TOOLTIP_STYLE)
    
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        main_window = MainWindow(login_window.get_token())
        main_window.show()
        sys.exit(app.exec())