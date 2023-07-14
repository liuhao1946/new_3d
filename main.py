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

        # Initialize the base and current quaternions as unit quaternions
        self.base_quaternion = [1, 0, 0, 0]
        self.current_quaternion = [1, 0, 0, 0]

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10)
        glRotatef(-90, 1, 0, 0)
        glRotatef(self.angle, self.x, self.y, self.z)
        self.drawAxes(3, 3)  # 在这里调用刚才添加的函数以绘制坐标轴
        self.drawCube(3, 0.5, 3)
        self.update()  # Force window to repaint

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

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

        r, g, b = self.normalize_rgb(0xee, 0x63, 0x63)
        glColor3f(r, g, b)  # Blue
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

    def normalize_rgb(self, red, green, blue):
        """
        Normalize RGB colors to a [0, 1] scale for OpenGL.

        :param red: Red component of the color (0-255).
        :param green: Green component of the color (0-255).
        :param blue: Blue component of the color (0-255).
        :return: Tuple of (red, green, blue) normalized to [0, 1].
        """

        return red / 255.0, green / 255.0, blue / 255.0

    def drawAxes(self, axisLength, lineWidth):
        '''
        Draw 3D axes
        axisLength - length of the axes
        arrowSize - size of the arrow heads
        lineWidth - width of the axes lines
        '''
        arrowSize = 0.3

        # Set the line width
        glLineWidth(lineWidth)

        # Draw the X axis in red
        glColor3f(1, 0, 0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(axisLength, 0, 0)
        glEnd()
        self.drawArrowHead(axisLength, 0, 0, arrowSize, 1, 0, 0)

        # Draw the Y axis in green
        glColor3f(0, 1, 0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, axisLength, 0)
        glEnd()
        self.drawArrowHead(0, axisLength, 0, arrowSize, 0, 1, 0)

        # Draw the Z axis in blue
        glColor3f(0, 0, 1)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, axisLength)
        glEnd()
        self.drawArrowHead(0, 0, axisLength, arrowSize, 0, 0, 1)

    def drawArrowHead(self, x, y, z, size, dx, dy, dz):
        '''
        Draw an arrow head
        x, y, z - position of the arrow head
        size - size of the arrow head
        dx, dy, dz - direction of the arrow
        '''

        # The arrow head is a set of lines that extend from the end of the axis
        glBegin(GL_LINES)

        if dx:
            # For X-axis, arrow head is in YZ plane
            glVertex3f(x-size, y, z + size)
            glVertex3f(x, y, z)
            glVertex3f(x-size, y, z - size)
            glVertex3f(x, y, z)
        elif dy:
            # For Y-axis, arrow head is in XZ plane
            glVertex3f(x + size, y - size, z)
            glVertex3f(x, y, z)
            glVertex3f(x - size, y - size, z)
            glVertex3f(x, y, z)
        elif dz:
            # For Z-axis, arrow head is in XY plane
            glVertex3f(x + size, y, z - size)
            glVertex3f(x, y, z)
            glVertex3f(x - size, y, z - size)
            glVertex3f(x, y, z)

        glEnd()

    def quaternion_to_euler(self, w, x, y, z):
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)

        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)

        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)

        return roll_x, pitch_y, yaw_z  # in radians

    def radians_to_degrees(self, radians):
        """
        Convert radians to degrees.
        """
        return radians * 180 / math.pi

    def store_current_pose(self):
        """
        Store the current pose as the base quaternion.
        """
        self.base_quaternion = self.quaternion_inverse(self.current_quaternion)

    def rotate_relative_to_base(self, w, x, y, z):
        """
        Rotate the object relative to the stored base pose.
        The input parameters w, x, y, z represent a quaternion.
        """

        # Compute the new rotation as the product of the inverse of the base quaternion and the input quaternion
        new_rotation = self.quaternion_multiply(self.base_quaternion, [w, x, y, z])
        # Update the current quaternion and the rotation parameters for the object
        self.current_quaternion = [w, x, y, z]
        self.angle, self.x, self.y, self.z = self.quaternion_to_angle_axis(*new_rotation)

    def quaternion_inverse(self, q):
        """
        Compute the inverse of a quaternion.
        """
        w, x, y, z = q
        norm = w**2 + x**2 + y**2 + z**2
        return [w/norm, -x/norm, -y/norm, -z/norm]

    def quaternion_multiply(self, q1, q2):
        """
        Compute the product of two quaternions.
        """
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2

        # normalize the quaternion
        norm = (w ** 2 + x ** 2 + y ** 2 + z ** 2) ** 0.5
        return [w / norm, x / norm, y / norm, z / norm]


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
        self.btn_reset.clicked.connect(self.on_btn_reset_clicked)

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

    def on_btn_reset_clicked(self):
        print("3d reset")
        self.opengl.store_current_pose()

    def on_timer(self):
        # import random
        # w = random.random()
        # x = random.random()
        # y = random.random()
        # z = random.random()
        # self.opengl.update_rotation(w, x, y, z)
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

        roll_rad, pitch_rad, yaw_rad = self.opengl.quaternion_to_euler(w, x, y, z)
        roll = self.opengl.radians_to_degrees(roll_rad)
        pitch = self.opengl.radians_to_degrees(pitch_rad)
        yaw = self.opengl.radians_to_degrees(yaw_rad)

        # eulerEdits[0]~[2] ->  pitch, yaw, roll
        self.eulerEdits[0].setText('%0.3f' % pitch)
        self.eulerEdits[1].setText('%0.3f' % yaw)
        self.eulerEdits[2].setText('%0.3f' % roll)

    def on_quat_data_received_3d(self, w, x, y, z):
        self.opengl.rotate_relative_to_base(w, x, y, z)

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
