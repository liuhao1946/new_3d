import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, QLineEdit, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import time
import bds.bds_serial as bds_ser


global ser_obj


class Worker(QThread):
    eulerDataReceived = pyqtSignal(float, float, float)
    quatDataReceived = pyqtSignal(float, float, float, float)

    def run(self):
        x = 0
        # 在这里读取数据
        while True:
            ser_obj.hw_read()




            # 假设我们读取到了欧拉角数据 (pitch, yaw, roll)
            pitch = 1.0
            yaw = 2.0
            roll = 3.0
            self.eulerDataReceived.emit(pitch, yaw, roll)

            # 假设我们读取到了四元数数据 (w, x, y, z)
            w = 4.0
            x += 1.0
            y = 6.0
            z = 7.0
            self.quatDataReceived.emit(w, x, y, z)

            # 暂停一段时间模拟读取数据的过程
            time.sleep(0.01)


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setMinimumSize(700, 500)
        grid = QGridLayout()

        # 第一行
        self.label1 = QLabel("串口选择")
        self.label1.setAlignment(Qt.AlignRight)  # 设置文本右对齐
        grid.addWidget(self.label1, 0, 0)
        self.combo1 = QComboBox()
        self.combo1.addItem("COM1")
        self.combo1.setFixedWidth(100)
        grid.addWidget(self.combo1, 0, 1)
        self.label2 = QLabel("波特率")
        self.label2.setAlignment(Qt.AlignRight)  # 设置文本右对齐
        grid.addWidget(self.label2, 0, 2)
        self.combo2 = QComboBox()
        self.combo2.addItem("115200")
        self.combo2.setFixedWidth(100)
        grid.addWidget(self.combo2, 0, 3)

        # 把'打开串口'按钮对齐到第二行的第3个文本输入框
        self.btn = QPushButton("打开串口")
        self.btn.clicked.connect(self.on_btn_clicked)
        grid.addWidget(self.btn, 0, 5)

        # 第二行
        self.eulerEdits = []
        for i, label in enumerate(["pitch", "yaw", "roll"]):
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight)  # 设置文本右对齐
            grid.addWidget(lbl, 1, i*2)
            edit = QLineEdit("0.0")
            edit.setFixedWidth(100)
            grid.addWidget(edit, 1, i*2+1)
            self.eulerEdits.append(edit)

        # 第三行
        self.quatEdits = []
        for i, label in enumerate(["w", "x", "y", "z"]):
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight)  # 设置文本右对齐
            grid.addWidget(lbl, 2, i*2)
            edit = QLineEdit("0.0")
            edit.setFixedWidth(100)
            grid.addWidget(edit, 2, i*2+1)
            self.quatEdits.append(edit)

        # 第四行的按钮一次对齐到第三行的文本输入框
        grid.addWidget(QPushButton("复位姿态"), 3, 1)
        grid.addWidget(QPushButton("预留"), 3, 3)

        # 第五行
        grid.addWidget(QLabel(""), 4, 0, 1, 6)

        self.setLayout(grid)
        self.setWindowTitle('My Window')
        self.show()

        # 新建一个10ms的精准定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(10)

        # 创建新线程
        self.worker = Worker()
        self.worker.eulerDataReceived.connect(self.on_euler_data_received)
        self.worker.quatDataReceived.connect(self.on_quat_data_received)
        self.worker.start()

    def on_btn_clicked(self):
        if self.btn.text() == "打开串口":
            self.btn.setText("关闭串口")
            print(self.combo1.currentText(), self.combo2.currentText(), self.label1.text(), self.label2.text())
        else:
            self.btn.setText("打开串口")

    def on_timer(self):
        # 这里是定时器每10ms要执行的代码
        pass

    def on_euler_data_received(self, pitch, yaw, roll):
        self.eulerEdits[0].setText(str(pitch))
        self.eulerEdits[1].setText(str(yaw))
        self.eulerEdits[2].setText(str(roll))

    def on_quat_data_received(self, w, x, y, z):
        self.quatEdits[0].setText(str(w))
        self.quatEdits[1].setText(str(x))
        self.quatEdits[2].setText(str(y))
        self.quatEdits[3].setText(str(z))


def hw_error(err):
    pass


def hw_warn(err):
    pass


if __name__ == '__main__':
    ser_obj = bds_ser.BDS_Serial(hw_error, hw_warn, char_format='hex')
    app = QApplication(sys.argv)
    ex = MyWindow()
    sys.exit(app.exec_())
