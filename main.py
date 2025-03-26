from globals import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(TOOLTIP_STYLE)
    
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())