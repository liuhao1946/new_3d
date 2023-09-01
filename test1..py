from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QAction
import sys


def main():
    app = QApplication(sys.argv)
    window = QMainWindow()

    # 创建状态栏
    status_bar = window.statusBar()

    # 在状态栏中添加标签用于显示信息
    label = QLabel("Ready")
    status_bar.addWidget(label)

    # 创建一个动作（可选）
    action = QAction("Do Something", window)
    action.triggered.connect(lambda: label.setText("Doing Something"))

    # 将动作添加到菜单栏（可选）
    menu_bar = window.menuBar()
    file_menu = menu_bar.addMenu("File")
    file_menu.addAction(action)

    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
