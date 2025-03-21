import sys
import time
import base64
import requests
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    QProgressBar, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal

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

# ------------------------ Worker Thread ------------------------
class DeletionWorker(QThread):
    update_progress = pyqtSignal(int, int)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, token, channel_id):
        super().__init__()
        self.token = token
        self.channel_id = channel_id
        self.running = True

    def run(self):
        try:
            headers = {"Authorization": self.token}
            user_id = self.extract_user_id()

            # First count all messages
            total = self.count_messages(headers, user_id)
            if total == 0:
                self.finished.emit()
                return

            # Then perform deletion
            self.delete_messages(headers, user_id, total)
            self.finished.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def extract_user_id(self):
        try:
            encoded_user_id = self.token.split('.')[0]
            decoded_bytes = base64.b64decode(encoded_user_id + '==')
            return decoded_bytes.decode('utf-8')
        except Exception:
            raise ValueError("Invalid token format")

    def count_messages(self, headers, user_id):
        last_message_id = None
        count = 0
        
        while self.running:
            messages = self.get_messages_batch(last_message_id, headers)
            if not messages:
                break

            count += sum(1 for msg in messages if msg["author"]["id"] == user_id)
            last_message_id = messages[-1]['id']

        return count

    def delete_messages(self, headers, user_id, total):
        last_message_id = None
        processed = 0
        
        while self.running:
            messages = self.get_messages_batch(last_message_id, headers)
            if not messages:
                break

            for msg in messages:
                if not self.running:
                    return
                if msg["author"]["id"] == user_id:
                    if self.delete_message(msg["id"], headers):
                        processed += 1
                        self.update_progress.emit(processed, total)

            last_message_id = messages[-1]['id']
            time.sleep(0.55)

    def get_messages_batch(self, before, headers):
        url = f"{BASE_URL}/channels/{self.channel_id}/messages?limit=100"
        if before:
            url += f"&before={before}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                time.sleep(retry_after)
                return self.get_messages_batch(before, headers)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    def delete_message(self, message_id, headers):
        url = f"{BASE_URL}/channels/{self.channel_id}/messages/{message_id}"
        try:
            response = requests.delete(url, headers=headers)
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                time.sleep(retry_after)
                return self.delete_message(message_id, headers)
            return response.status_code == 204
        except Exception:
            return False

    def stop(self):
        self.running = False

# ------------------------ Login Window ------------------------
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Lazer")
        self.setFixedSize(350, 150)
        self.set_background_image()

        layout = QVBoxLayout()

        # Token Input Label
        self.token_label = QLabel("Enter Token")
        self.token_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.token_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.token_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 6px;
            margin: 0 80px;
        """)

        # Token Input Field
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
        self.token_input.setFont(QFont("Arial", 12))
        self.token_input.setStyleSheet("background-color: transparent; border: 1px solid rgba(255, 255, 255, 0.5);")

        # Input Controls
        self.help_btn = QPushButton("❓")
        self.help_btn.setFixedSize(28, 28)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 14px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.help_btn.clicked.connect(self.show_token_help)

        self.visibility_btn = QPushButton("👁")
        self.visibility_btn.setFixedSize(28, 28)
        self.visibility_btn.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.15);
            border-radius: 14px;
            border: none;
        """)
        self.visibility_btn.clicked.connect(self.toggle_visibility)

        # Token Layout
        token_layout = QHBoxLayout()
        token_layout.addWidget(self.help_btn)
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(self.visibility_btn)
        token_layout.setContentsMargins(10, 0, 10, 0)

        # Login Button
        self.submit_btn = QPushButton("Login")
        self.submit_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.submit_btn.setFixedSize(120, 40)
        self.submit_btn.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.3);
            border-radius: 10px; 
            border: none; 
            padding: 10px;
        """)
        self.submit_btn.clicked.connect(self.accept)

        # Load cached token
        self.cached_token = self.load_cached_token()
        if self.cached_token:
            self.token_input.setText(self.cached_token)

        # Assemble layout
        layout.addWidget(self.token_label)
        layout.addLayout(token_layout)
        layout.addWidget(self.submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 15, 20, 15)

        self.setLayout(layout)

    def toggle_visibility(self):
        current = self.token_input.echoMode()
        new_mode = QLineEdit.EchoMode.Password if current == QLineEdit.EchoMode.Normal else QLineEdit.EchoMode.Normal
        self.token_input.setEchoMode(new_mode)

    def show_token_help(self):
        help_text = """<b>How to Find Your Discord Token:</b>
        <ol>
            <li>Open Discord in your browser</li>
            <li>Press <kbd>Ctrl+Shift+I</kbd></li>
            <li>Go to: Application → Local Storage → https://discord.com</li>
            <li>Search for 'token' in the key list</li>
            <li>Double-click to copy the value</li>
        </ol>"""
        
        msg = QMessageBox()
        msg.setWindowTitle("Token Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setStyleSheet(TOOLTIP_STYLE)
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

    def set_background_image(self):
        pixmap = QPixmap("background.jpg")
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)

# ------------------------ Main Window ------------------------
class MainWindow(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Lazer")
        self.setFixedSize(550, 200)
        self.set_background_image()

        layout = QVBoxLayout()

        # Header
        self.username = self.fetch_username()
        self.status_label = QLabel(f"Welcome, {self.username}" if self.username else "Welcome!")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 6px;
            margin: 0 100px;
            margin-bottom: 10px;
        """)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedWidth(300)

        # Channel Input
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Enter Channel ID")
        self.channel_input.setStyleSheet("background-color: transparent; border: 1px solid rgba(255, 255, 255, 0.5);")
        self.channel_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Action Buttons
        self.submit_btn = QPushButton("Start Deletion")
        self.submit_btn.setFixedSize(140, 40)
        self.submit_btn.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.3);
            border-radius: 10px; 
            font-size: 14px;
        """)
        self.submit_btn.clicked.connect(self.start_deletion)

        self.back_btn = QPushButton("Back to Login")
        self.back_btn.setFixedSize(140, 40)
        self.back_btn.setStyleSheet("""
            background-color: rgba(255, 75, 75, 0.3);
            border-radius: 10px; 
            padding: 8px;
            font-size: 14px;
        """)
        self.back_btn.clicked.connect(self.confirm_logout)

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.back_btn)
        button_layout.addStretch()
        button_layout.setContentsMargins(0, 15, 0, 15)

        # Main Layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.channel_input)
        layout.addLayout(button_layout)
        layout.setContentsMargins(20, 15, 20, 20)

        self.setLayout(layout)

    def set_background_image(self):
        pixmap = QPixmap("background.jpg")
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)

    def fetch_username(self):
        try:
            response = requests.get(f"{BASE_URL}/users/@me", headers={"Authorization": self.token})
            return response.json().get("username", "User")
        except Exception:
            return None

    def confirm_logout(self):
        confirm = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to switch accounts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.close()
            login_window = LoginWindow()
            if login_window.exec() == QDialog.DialogCode.Accepted:
                new_main = MainWindow(login_window.get_token())
                new_main.show()

    def start_deletion(self):
        if self.worker and self.worker.isRunning():
            return

        channel_id = self.channel_input.text()
        if not channel_id:
            QMessageBox.critical(self, "Error", "Please enter a Channel ID")
            return

        try:
            # Check channel type
            channel_data = requests.get(
                f"{BASE_URL}/channels/{channel_id}",
                headers={"Authorization": self.token}
            ).json()
            
            if channel_data.get('type') in [1, 3]:
                recipients = channel_data.get('recipients', [])
                names = [r.get('username', 'Unknown') for r in recipients]
                confirm_text = f"Delete messages with {', '.join(names)}?" if names else "Delete messages in this DM?"
                
                confirm = QMessageBox.question(
                    self, "Confirm Deletion", confirm_text,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid channel: {str(e)}")
            return

        self.worker = DeletionWorker(self.token, channel_id)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Deleting...")

    def update_progress(self, current, total):
        self.progress_bar.setValue(int((current / total) * 100))

    def on_finished(self):
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Start Deletion")
        self.progress_bar.setValue(0)
        QMessageBox.information(self, "Complete", "Message deletion finished!")

    def show_error(self, message):
        self.on_finished()
        QMessageBox.critical(self, "Error", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(TOOLTIP_STYLE)
    
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        main_window = MainWindow(login_window.get_token())
        main_window.show()
        sys.exit(app.exec())