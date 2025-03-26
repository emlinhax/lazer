from globals import *

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Lazer")
        self.setFixedSize(500, 200)
        self.set_background_image()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)

        self.status_label = QLabel(f"Welcome, {context.user.username}")
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
        pixmap = QPixmap("assets/background.jpg")
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setGeometry(self.rect())
        background_label.setScaledContents(True)
        self.setAutoFillBackground(True)

    def confirm_logout(self):
        confirm = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.close()

    def show_selector(self):
        selector = ChannelSelector()
        if selector.exec() == QDialog.DialogCode.Accepted:
            selected = selector.get_selected()
            if selected:
                self.start_deletion(selected)

    def start_deletion(self, channels):
        if self.worker and self.worker.isRunning():
            return

        self.worker = DeletionWorker(channels)
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
        self.status_label.setText(f"Welcome, {context.user.username}")
        QMessageBox.information(self, "Complete", "Cleaning process finished!")

    def show_error(self, error, context):
        self.on_finished()
        QMessageBox.critical(self, "Error", f"Error in {context}:\n{error}")