import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QMainWindow


class Dialog(QDialog):
    def __init__(self):
        super(Dialog, self).__init__()
        self.setWindowTitle('Dialog')

        self.layout = QVBoxLayout(self)

        self.button1 = QPushButton('Button 1')
        self.layout.addWidget(self.button1)

        self.button2 = QPushButton('Button 2')
        self.layout.addWidget(self.button2)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Main Window')

        self.button = QPushButton('Open Dialog', self)
        self.setCentralWidget(self.button)

        self.button.clicked.connect(self.show_dialog)

    def show_dialog(self):
        self.dialog = Dialog()
        self.dialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())