import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QByteArray
from PyQt5.QtWidgets import QMessageBox
import time
import bds.bds_serial as bds_ser
from PyQt5.QtGui import QPixmap, QIcon, QFont
import bds.bds_3d as bds_3d
import json

global ser_obj


class Worker(QThread):
    eulerDataReceived = pyqtSignal(float, float, float)
    quatDataReceived = pyqtSignal(float, float, float, float)
    quatDataReceived_3d = pyqtSignal(float, float, float, float)

    def run(self):
        quat_display_clk = 0

        while True:
            ser_obj.hw_read()

            xyzw = ser_obj.read_xyzw()
            euler = ser_obj.read_euler()
            if xyzw:
                x, y, z, w = xyzw[-1]
                self.quatDataReceived_3d.emit(w, x, y, z)

                quat_display_clk += 1
                if quat_display_clk >= 10:
                    self.quatDataReceived.emit(w, x, y, z)
                    quat_display_clk = 0

            if euler:
                # rx: yaw-euler[0], pitch-euler[1], roll-euler[2]
                # ui: pitch, yaw, roll
                # self.on_euler_data_received(euler[1], euler[0], euler[2])
                pass

            # 暂停一段时间模拟读取数据的过程
            time.sleep(0.005)


class MyWindow(QWidget):
    def __init__(self, obj):
        super().__init__()

        # 读取json配置文件
        with open('config.json', 'r') as f:
            self.js_cfg = json.load(f)
        self.com_des_list = []
        self.com_name_list = []
        self.baud_list = self.js_cfg['ser_baud']
        self.baud = 115200
        self.obj = obj
        self.ser_hot_plug_timer = 0

        exe_icon = b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAA99JREFUaEPtmVtIFGEUx/9n1m72FIRQFAnZbSN0VyM0o8DsspuFuK4+9ZR0oZforQcffCvwJXqICgoqUFtSLJcgDKMQ19Cxi2ZGdLGHKHpJK5FmTnyzKXuZdWZ3Z6yN/UAGnO875/8758y3M+cjZPigDNePLMDfzqClGWAG4V6RDwrtgEQbwFyoARI9hcqv4OBH2DcUIAJbBW4JAHcVbwGrtSD4AGwyEPcSjABIukXegefpgqQMwG3OhVi60KeJZqpOSQhxuwbzfTpA/pHpVGwkDcCdxW44VBFp8bcuFac6a14DCECRAnRwYDAZm6YA+E5x7qxoRlUyDpKeS7gzC1M18MNovSEAB12nwTgJIN/ImMX334FwgTxy81x2EwJw0OUEcB6MCouFJWeO0A2H0kB7n73VW6gL8Ed8Gxibk/Nm02xCDxzKAdr77HusB32ALtcTACU2yUnV7BXyyg2GABx014G5JVUvtq5TsZuq5O5IH3EZ4C73XYC9kZNGxgn1zRLE9UAJ40ilql2tHIFewrUHEu7JBOdqRstpVbtGDUIneeRDBgCuVwDWR056OEyoaHRE2VqxDGjYo8Jfxti4KjWYobdCNKH1sYQv36K1djcp2Lk5zu4YeeUNcwME3T/BvDg2uvXNDogo6Q2RjdrtKqq3MXIXzZ2XySngeo+k2RKB0Ru+MpEBJf4W0RR5BpcYZSBhOEXE2kOEjj7C8Hi8c5EV/x+Qcme0GSFWiA70xkdbCMrPA3ylKmrKGFsLEmeUvHKUY51nwGWqHjr7BYyEjhBh4md8sNavZJQUAIsXMPrGSHt+9IbHzfCVhYUvNcieWG8ZwIyYj1+BjpCE9r7EJRErfE0eo7aUDaOtB2w5QKST3tFwid3uI7z/rB/xs4dVHNunmor2vAPE7lxnbkgIjYVBVi8HLp1QUFloqkIT7gS2ZiDWa05Nzuy/bp5SUFeennhbnoFEoXrxgVB0KvzbIbbWT1d/GW6xc2/A4bvzloHL9yUcvyhpTkXkRQasGPMG0NQmoak1DNBYp6LRr1qhf/4ykAVIkK9sCZkt5GwJpVFC4tUs7nXabORn5tmUgSnyyoav0y8BbExWcOx8mwBGyStHtS5NfVKmAmMLgKlPSos+6m0BMPNRL6LNFrRVbAAw11bRAMJdubQaW5GNgP5zCtxr03gTZX6MH9P7yT8yGVvOtrYWB98QJqag110w/1iJ1iKko+QZeKO36P9t7kbSZnR7PTZtGXnAoVd7GXvEpAuTiYd8uiAzx6yqtAvEztnzBcIwmEYgqT3/5DGr+T3R+pmG26j1Lq21mAWwNp7JW/sNV5joQICi7RQAAAAASUVORK5CYII='

        self.set_exe_icon(exe_icon)
        self.initUI()

    def set_exe_icon(self, exe_icon):
        ba = QByteArray.fromBase64(exe_icon)
        pixmap = QPixmap()
        pixmap.loadFromData(ba, "PNG")
        self.setWindowIcon(QIcon(pixmap))

    def initUI(self):
        self.com_des_list, self.com_name_list = bds_ser.serial_find()
        if not self.com_des_list:
            self.com_des_list.append('')
        if not self.com_name_list:
            self.com_name_list.append('')

        self.setMinimumSize(800, 600)
        grid = QGridLayout()

        font = QFont("Arial", 11)
        font.setBold(True)
        # 第一行
        self.label1 = QLabel("COM")
        self.label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 设置文本右对齐
        self.label1.setFont(font)
        grid.addWidget(self.label1, 0, 0)

        self.combo1 = QComboBox()
        self.combo1.addItems(self.com_des_list)
        self.combo1.setFixedWidth(180)
        grid.addWidget(self.combo1, 0, 1)

        self.label2 = QLabel("波特率")
        self.label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 设置文本右对齐
        self.label2.setFont(font)
        grid.addWidget(self.label2, 0, 2)

        self.combo2 = QComboBox()
        self.combo2.addItems([str(v) for v in self.baud_list])
        self.combo2.setFixedWidth(100)
        grid.addWidget(self.combo2, 0, 3)

        # 把'打开串口'按钮对齐到第二行的第3个文本输入框
        self.btn = QPushButton("打开串口")
        self.btn.clicked.connect(self.on_btn_clicked)
        grid.addWidget(self.btn, 0, 5)

        # 第二行
        self.eulerEdits = []
        for i, label in enumerate(["pitch", "yaw", "roll", "mag_cal"]):

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFont(font)
            grid.addWidget(lbl, 1, i*2)

            edit = QLineEdit("0.0")
            edit.setFixedWidth(100)
            grid.addWidget(edit, 1, i*2+1)
            self.eulerEdits.append(edit)

        # 第三行
        self.quatEdits = []
        for i, label in enumerate(["w", "x", "y", "z"]):

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFont(font)
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

        # grid.addWidget(QPushButton("预留"), 3, 3)

        # 第五行
        # grid.addWidget(QLabel(""), 4, 0, 1, 6)
        self.opengl = bds_3d.OpenGLWidget()
        grid.addWidget(self.opengl, 4, 0, 1, 8)

        self.setLayout(grid)
        self.setWindowTitle('Cyweemotion 3D')
        self.show()

        # 新建一个10ms的精准定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(100)
        self.ser_hot_plug_timer = 0

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

                self.js_cfg['ser_baud'] = bds_ser.ser_buad_list_adjust(cur_baud, self.js_cfg['ser_baud'])
                with open('config.json', 'w') as f:
                    json.dump(self.js_cfg, f, indent=4)

                self.btn.setText("关闭串口")
                self.btn.setStyleSheet("background-color: green")
            except Exception as e:
                QMessageBox.information(self, "错误:", str(e))
        else:
            try:
                self.btn.setText("打开串口")
                self.btn.setStyleSheet("")
                self.obj.hw_close()
            except Exception as e:
                QMessageBox.information(self, "错误:", str(e))

    def on_btn_reset_clicked(self):
        print("3d reset")
        self.opengl.store_current_pose()

    def on_timer(self):
        self.ser_hot_plug_timer += 1
        if self.ser_hot_plug_timer > 10:
            self.ser_hot_plug_timer = 0
            self.ser_hot_plug_timer_detect()

    def ser_hot_plug_timer_detect(self):
        default_des = bds_ser.ser_hot_plug_detect(self.combo1.currentText(), self.com_des_list, self.com_name_list)
        try:
            if default_des != '':
                self.combo1.clear()
                self.combo1.addItems(self.com_des_list)
                self.combo1.setCurrentIndex(self.com_des_list.index(default_des))
        except ValueError as e:
            print(e)

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
