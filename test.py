import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QApplication
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

class DownloadDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('download')
        self.setFixedSize(300, 200)
        layout = QVBoxLayout()

        # 第一行：文本控件
        self.text_label = QLabel('下载进度')
        layout.addWidget(self.text_label)
        # self.text_label.setText('下载123')

        # 第二行：进度条控件
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 第三行：超链接
        link_label = QLabel('<a href="http://www.google.com">www.google.com</a>')
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)

        # 第四行：两个按钮
        download_button = QPushButton('立刻下载')
        # remind_button = QPushButton('下次提醒')
        layout.addWidget(download_button)
        #layout.addWidget(remind_button)

        download_button.clicked.connect(self.start_download)
        # remind_button.clicked.connect(self.remind_later)

        self.setLayout(layout)

    def start_download(self):
        # 示例：设置进度条的进度
        for i in range(101):
            self.progress_bar.setValue(i)

    def remind_later(self):
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = DownloadDialog()
    dialog.exec_()
