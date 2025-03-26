from globals import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(TOOLTIP_STYLE)

    while True:
        login_window = LoginWindow()
        if login_window.exec() == QDialog.DialogCode.Accepted:
            main_window = MainWindow()
            main_window.show()

            # Run the main window in its own loop
            app.exec()

            # If main window is closed, go back to login
            continue
        else:
            break  # User closed or cancelled login

    sys.exit()