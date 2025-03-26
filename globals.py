# dependencies
import sys
import time
import base64
import requests
import json
from types import SimpleNamespace
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    QProgressBar, QHBoxLayout, QMessageBox, QListWidget, QListWidgetItem, 
    QScrollArea, QGroupBox, QAbstractItemView, QDialogButtonBox
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize

# define constants (this has to be done before importing the rest otherwise they cant access them)
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

# global state where everything is stored
class LazerContext:
    token = None
    user = {}

# create instance of ZE DEADLY LAZERRRRRRRR
context = LazerContext()

# own modules (the order matters so they can access eachother)
from discord import api
from workers.fetcher import DataFetcher
from workers.deletion import DeletionWorker
from gui.channel_selector import ChannelSelector
from gui.login import LoginWindow
from gui.dashboard import MainWindow