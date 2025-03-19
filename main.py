import sys
import time
import base64
import requests
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    QTextEdit, QProgressBar, QHBoxLayout
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt

BASE_URL = "https://discord.com/api/v9"


# ------------------------ Login Window ------------------------
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login - Discord Tool")
        self.setFixedSize(350, 150)  # Fixed window size (cannot be resized)

        # Set background image using QLabel
        self.set_background_image()

        layout = QVBoxLayout()

        # Token Input Label (Make font size slightly bigger for readability)
        self.token_label = QLabel("Enter Token")
        self.token_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Slightly smaller font
        self.token_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text

        # Token Input Field (with style applied)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)  # Mask input
        self.token_input.setFont(QFont("Arial", 12))  # Slightly smaller font for better readability
        self.token_input.setStyleSheet("background-color: transparent; border: 1px solid rgba(255, 255, 255, 0.5);")  # Transparent background with border

        # Login Button (with transparent background and same font)
        self.submit_btn = QPushButton("Login")
        self.submit_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Slightly smaller font
        self.submit_btn.setFixedSize(120, 40)
        self.submit_btn.setStyleSheet("background-color: rgba(255, 255, 255, 0.3); border-radius: 10px; border: none; padding: 10px;")  # Transparent button
        self.submit_btn.clicked.connect(self.accept)

        # Create an HBoxLayout to center the button
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.submit_btn)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the button in the layout

        # Add widgets to the main layout
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_input)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_token(self):
        return self.token_input.text()

    def set_background_image(self):
        """ Set background image using QLabel """
        pixmap = QPixmap("background.jpg")  # Ensure this file exists in your directory
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())  # Fill the window
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)  # Auto-fill background


# ------------------------ Main Window ------------------------
class MainWindow(QWidget):
    def __init__(self, token):
        super().__init__()

        self.token = token
        self.setWindowTitle("Discord Tool - Progress")

        # Set a wider, shorter fixed size for the window
        self.setFixedSize(700, 300)  # Wider and less tall (adjust as needed)

        # Set background image (using QLabel)
        self.set_background_image()

        layout = QVBoxLayout()

        # Progress Label with Bold Text
        self.status_label = QLabel("Progress:")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Slightly smaller and bold

        # Progress Bar (Pink Themed)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)

        # Channel ID Input Label (Make it slightly bigger for readability)
        self.channel_label = QLabel("Enter Channel ID to Delete Messages:")
        self.channel_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))  # Slightly smaller font for clarity
        self.channel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the label text

        # Channel ID Input Field
        self.channel_input = QLineEdit()
        self.channel_input.setStyleSheet("background-color: transparent; border: 1px solid rgba(255, 255, 255, 0.5);")  # Transparent input field
        self.channel_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Submit Button for Start Deletion (Centered and Styled)
        self.submit_btn = QPushButton("Start Deletion")
        self.submit_btn.setFixedSize(120, 40)
        self.submit_btn.setStyleSheet("background-color: rgba(255, 255, 255, 0.3); border-radius: 10px; border: none; padding: 10px; text-align: center;")
        self.submit_btn.clicked.connect(self.start_deletion)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: transparent; border: 1px solid rgba(255, 255, 255, 0.5);")  # Transparent log area

        # Add widgets to layout
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)  # Center progress text
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.channel_label)
        layout.addWidget(self.channel_input)
        
        # Use HBoxLayout to center the button in the window
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.submit_btn)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the button
        
        layout.addLayout(button_layout)

        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def set_background_image(self):
        """ Set background image using QLabel """
        pixmap = QPixmap("background.jpg")  # Ensure this file exists in your directory
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())  # Fill the window
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)  # Auto-fill background

    def update_progress(self, value, total):
        """ Updates progress bar with percentage based on number of deleted messages """
        progress = (value / total) * 100  # Calculate progress
        self.progress_bar.setValue(int(progress))  # Ensure the value passed is an integer

    def log_message(self, message):
        """ Appends log messages """
        self.log_output.append(message)

    def start_deletion(self):
        """ Start the deletion process when the user clicks the button """
        channel_id = self.channel_input.text()
        if not channel_id:
            self.log_message("Please enter a Channel ID.")
            return

        headers = {"Authorization": self.token, "Content-Type": "application/json"}
        user_id = self.extract_user_id(self.token)

        if user_id:
            self.log_message(f"Starting deletion process for channel: {channel_id}")
            self.count_and_delete_messages(channel_id, headers, user_id)
        else:
            self.log_message("Failed to decode user ID. Check your token.")

    def extract_user_id(self, token):
        """ Extracts user ID from Discord token """
        try:
            encoded_user_id = token.split('.')[0]
            decoded_bytes = base64.b64decode(encoded_user_id + '==')
            return decoded_bytes.decode('utf-8')
        except Exception:
            return None

    def count_and_delete_messages(self, channel_id, headers, user_id):
        """ Counts the messages from the user before starting deletion and updates progress """
        last_message_id = None
        user_messages = 0

        # Count messages from the user before deletion
        while True:
            messages = self.get_messages(channel_id, headers, last_message_id)
            if not messages:
                self.log_message("No more messages to delete.")
                break

            # Count only messages that belong to the user
            user_messages += sum(1 for msg in messages if msg["author"]["id"] == user_id)

            last_message_id = messages[-1]['id']

        if user_messages == 0:
            self.log_message("No messages from this user found.")
            return

        # Display how many messages are found before deletion
        self.log_message(f"Found {user_messages} messages to delete.")
        self.progress_bar.setMaximum(user_messages)

        # Now delete the messages
        processed_count = 1
        last_message_id = None

        while True:
            messages = self.get_messages(channel_id, headers, last_message_id)
            if not messages:
                self.log_message(f"Messages deleted: {processed_count}")
                break

            for msg in messages:
                if msg["author"]["id"] == user_id:
                    self.delete_message(channel_id, msg["id"], headers)
                    processed_count += 1
                    self.update_progress(processed_count, user_messages)

            last_message_id = messages[-1]['id']
            time.sleep(0.3)

    def get_messages(self, channel_id, headers, before=None):
        """ Fetch messages from Discord with rate-limiting handling """
        url = f"{BASE_URL}/channels/{channel_id}/messages?limit=100"
        if before:
            url += f"&before={before}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                time.sleep(retry_after)
                return self.get_messages(channel_id, headers, before)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def delete_message(self, channel_id, message_id, headers):
        """ Deletes a single message and handles retries for rate-limiting """
        url = f"{BASE_URL}/channels/{channel_id}/messages/{message_id}"
        try:
            response = requests.delete(url, headers=headers)
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                time.sleep(retry_after)
                self.delete_message(channel_id, message_id, headers)
            elif response.status_code == 204:
                pass  # No need to log individual messages anymore
        except requests.exceptions.RequestException:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Display login window
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        token = login_window.get_token()
        main_window = MainWindow(token)
        main_window.show()
        sys.exit(app.exec())
