import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, QLineEdit, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import time
import bds.bds_serial as bds_ser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
from PyQt5.QtGui import QSurfaceFormat


global ser_obj


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        fmt = QSurfaceFormat()
        fmt.setSamples(4)  # Set the number of samples used for multisampling
        QSurfaceFormat.setDefaultFormat(fmt)  # Apply the format to the widget

        super(OpenGLWidget, self).__init__(parent)
        self.angle = 0
        self.x = 0
        self.y = 0
        self.z = 1

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10)
        glRotatef(self.angle, self.x, self.y, self.z)
        self.drawCube(3, 3, 0.5)
        self.update()  # Force window to repaint

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def update_rotation(self, w, x, y, z):
        self.angle, self.x, self.y, self.z = self.quaternion_to_angle_axis(w, x, y, z)

    def quaternion_to_angle_axis(self, w, x, y, z):
        angle = 2 * math.acos(w) * 180.0 / math.pi
        norm = math.sqrt(x * x + y * y + z * z)
        if norm == 0:
            return 0, 1, 0, 0
        return angle, x / norm, y / norm, z / norm

    def drawCube(self, length, width, height):
        half_length = length / 2
        half_width = width / 2
        half_height = height / 2

        glBegin(GL_QUADS)
        glColor3f(1, 0, 0)  # Red
        glVertex3f(half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, -half_width)
        glVertex3f(half_length, half_height, -half_width)

        glColor3f(0, 1, 0)  # Green
        glVertex3f(half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, half_width)
        glVertex3f(half_length, -half_height, half_width)

        glColor3f(0, 0, 1)  # Blue
        glVertex3f(half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, half_width)
        glVertex3f(-half_length, -half_height, half_width)
        glVertex3f(half_length, -half_height, half_width)

        glColor3f(1, 1, 0)  # Yellow
        glVertex3f(half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, -half_width)
        glVertex3f(-half_length, half_height, -half_width)
        glVertex3f(half_length, half_height, -half_width)

        glColor3f(1, 0, 1)  # Magenta
        glVertex3f(-half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, -half_width)
        glVertex3f(-half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, half_width)

        glColor3f(0, 1, 1)  # Cyan
        glVertex3f(half_length, half_height, -half_width)
        glVertex3f(half_length, half_height, half_width)
        glVertex3f(half_length, -half_height, half_width)
        glVertex3f(half_length, -half_height, -half_width)
        glEnd()

class Worker(QThread):
    eulerDataReceived = pyqtSignal(float, float, float)
    quatDataReceived = pyqtSignal(float, float, float, float)
    quatDataReceived_3d = pyqtSignal(float, float, float, float)

    def run(self):
        quat_display_clk = 0

        while True:
            ser_obj.hw_read()

            xyzw = ser_obj.read_xyzw()
            if xyzw:
                x, y, z, w = xyzw[-1]
                self.quatDataReceived_3d.emit(w, x, y, z)

                quat_display_clk += 1
                if quat_display_clk >= 10:
                    self.quatDataReceived.emit(w, x, y, z)
                    quat_display_clk = 0

            # 暂停一段时间模拟读取数据的过程
            time.sleep(0.005)


class MyWindow(QWidget):
    def __init__(self, obj):
        super().__init__()
        self.com_des_list = []
        self.com_name_list = []
        self.baud_list = ['1000000', '2000000', '9600', '115200']
        self.baud = 115200
        self.obj = obj

        self.initUI()

    def initUI(self):
        self.com_des_list, self.com_name_list = bds_ser.serial_find()
        if not self.com_des_list:
            self.com_des_list.append('')
        if not self.com_name_list:
            self.com_name_list.append('')

        self.setMinimumSize(700, 500)
        grid = QGridLayout()

        # 第一行
        self.label1 = QLabel("串口选择")
        self.label1.setAlignment(Qt.AlignRight)  # 设置文本右对齐
        grid.addWidget(self.label1, 0, 0)
        self.combo1 = QComboBox()
        self.combo1.addItems(self.com_des_list)
        self.combo1.setFixedWidth(180)
        grid.addWidget(self.combo1, 0, 1)
        self.label2 = QLabel("波特率")
        self.label2.setAlignment(Qt.AlignRight)  # 设置文本右对齐
        grid.addWidget(self.label2, 0, 2)
        self.combo2 = QComboBox()
        self.combo2.addItems(self.baud_list)
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
        self.btn_reset =QPushButton("复位姿态")
        grid.addWidget(self.btn_reset, 3, 1)
        self.btn_reset.setFixedWidth(100)
        grid.addWidget(QPushButton("预留"), 3, 3)

        # 第五行
        # grid.addWidget(QLabel(""), 4, 0, 1, 6)
        self.opengl = OpenGLWidget()
        grid.addWidget(self.opengl, 4, 0, 1, 8)

        self.setLayout(grid)
        self.setWindowTitle('Cyweemotion 3D(www.cyweemotion.com)')
        self.show()

        # 新建一个10ms的精准定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(100)

        # 创建新线程
        self.worker = Worker()
        self.worker.eulerDataReceived.connect(self.on_euler_data_received)
        self.worker.quatDataReceived.connect(self.on_quat_data_received)
        self.worker.quatDataReceived_3d.connect(self.on_quat_data_received_3d)
        self.worker.start()

    def on_btn_clicked(self):
        if self.btn.text() == "打开串口":
            ser_num = self.com_name_list[self.com_des_list.index(self.combo1.currentText())]
            cur_baud = int(self.combo2.currentText())

            print("ser number: %s" % ser_num)
            print("cur baud: %s" % cur_baud)
            try:
                self.obj.hw_open(port=ser_num, baud=cur_baud, rx_buffer_size=10240)
                self.btn.setText("关闭串口")
            except Exception as e:
                QMessageBox.information(self, "错误:", str(e))
            # print(self.combo1.currentText(), self.combo2.currentText(), self.label1.text(), self.label2.text())
        else:
            try:
                self.btn.setText("打开串口")
                self.obj.hw_close()
            except Exception as e:
                QMessageBox.information(self, "错误:", str(e))

    def on_timer(self):
        import random
        w = random.random()
        x = random.random()
        y = random.random()
        z = random.random()
        print(w, x, y, z)
        self.opengl.update_rotation(w, x, y, z)
        pass

    def on_euler_data_received(self, pitch, yaw, roll):
        self.eulerEdits[0].setText(str(pitch))
        self.eulerEdits[1].setText(str(yaw))
        self.eulerEdits[2].setText(str(roll))

    def on_quat_data_received(self, w, x, y, z):
        self.quatEdits[0].setText('%0.6f' % w)
        self.quatEdits[1].setText('%0.6f' % x)
        self.quatEdits[2].setText('%0.6f' % y)
        self.quatEdits[3].setText('%0.6f' % z)

    def on_quat_data_received_3d(self, w, x, y, z):
        pass

    def closeEvent(self, event):
        # 在这里释放你的资源
        print("Window is closing...")

        if ser_obj.hw_is_open():
            ser_obj.hw_close()
        # 然后调用父类的 closeEvent 方法，以确保窗口被正确关闭
        super().closeEvent(event)


def hw_error(err):
    print(err)


def hw_warn(err):
    print(err)


if __name__ == '__main__':
    ser_obj = bds_ser.BDS_Serial(hw_error, hw_warn, char_format='hex')
    app = QApplication(sys.argv)
    ex = MyWindow(ser_obj)
    sys.exit(app.exec_())
