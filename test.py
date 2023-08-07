import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QMenu, QAction

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.textEdit = QTextEdit()
        self.textEdit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.textEdit.setReadOnly(True)
        self.setCentralWidget(self.textEdit)

        # 连接信号和槽
        self.textEdit.customContextMenuRequested.connect(self.showContextMenu)
        self.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)

        self.setGeometry(100, 100, 400, 300)

    def showContextMenu(self, position):
        print(position)
        # 创建标准上下文菜单
        menu = self.textEdit.createStandardContextMenu()

        # 创建清除动作并连接到槽函数
        clear_action = QAction('清除', self)
        clear_action.triggered.connect(self.textEdit.clear)

        # 将清除动作添加到菜单中
        menu.addAction(clear_action)

        # 使用 QTextEdit 的 mapToGlobal 方法转换位置
        menu.exec_(self.textEdit.mapToGlobal(position))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
