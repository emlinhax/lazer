from globals import *

class ChannelSelector(QDialog):
    def __init__(self):
        super().__init__()
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
        
        self.fetcher = DataFetcher()
        self.fetcher.data_loaded.connect(self.populate_ui)
        self.fetcher.error_occurred.connect(self.show_error)
        self.fetcher.start()

    def set_background_image(self):
        pixmap = QPixmap("assets/background.jpg")
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