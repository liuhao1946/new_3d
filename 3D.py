import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QByteArray
from PyQt5.QtWidgets import QMessageBox
import time
import bds.bds_serial as bds_ser
from PyQt5.QtGui import QPixmap, QIcon, QFont
import bds.bds_3d as bds_3d
import json
import struct
import bds.time_diff as td
import logging as log

global ser_obj

CWM_VERSION = 'Cyweemotion 3D(v1.0.1)'

package_number = 0


def add_package_number():
    global package_number

    package_number += 1

    if package_number > 65535:
        package_number = 0

    return to_2bytes(package_number)


def to_2bytes(data):
    try:
        return list(struct.pack("<H", data))
    except:
        raise ValueError


def ser_protocol_data(sid, user_data):
    protocol_fix = [0xAA, 0x5A, 0xAA, 0x5A, 0x01]
    package_num = add_package_number()
    data_len = to_2bytes(len(sid+user_data))
    ser_data = protocol_fix + package_num + data_len + sid + user_data

    return ser_data + to_2bytes(sum(ser_data))


def euler_open(flag):
    if flag:
        # 欧拉角打开
        sid = [0x04, 0x04]
        user_data = [0x01]
        ser_obj.hw_write(ser_protocol_data(sid, user_data))
    else:
        # 欧拉角关闭
        sid = [0x04, 0x04]
        user_data = [0x00]
        ser_obj.hw_write(ser_protocol_data(sid, user_data))


def quat_open(flag):
    if flag:
        # 四元数打开
        sid = [0x04, 0x05]
        user_data = [0x01]
        ser_obj.hw_write(ser_protocol_data(sid, user_data))
    else:
        # 四元数关闭
        sid = [0x04, 0x05]
        user_data = [0x00]
        ser_obj.hw_write(ser_protocol_data(sid, user_data))


def get_agm_cal_state():
    ser_obj.hw_write(ser_protocol_data([0x03, 0x04], []))


class Worker(QThread):
    eulerDataReceived = pyqtSignal(float, float, float)
    quatDataReceived = pyqtSignal(float, float, float, float)
    quatDataReceived_3d = pyqtSignal(float, float, float, float)
    dtDataReceived = pyqtSignal(float)

    def __init__(self, js_cfg):
        QThread.__init__(self)
        self.js_cfg = js_cfg

    def run(self):
        display_clk_3d = 0
        quat_display_clk = 0
        euler_display_clk = 0
        time_diff = td.TimeDifference()
        data_packets_len = 0

        while True:
            ser_obj.hw_read()

            xyzw = ser_obj.read_xyzw()
            euler = ser_obj.read_euler()
            if xyzw:
                x, y, z, w = xyzw[-1]

                display_clk_3d += 1
                if display_clk_3d >= self.js_cfg['refresh_rate']:
                    self.quatDataReceived_3d.emit(w, x, y, z)
                    display_clk_3d = 0

                quat_display_clk += 1
                if quat_display_clk >= 20:
                    self.quatDataReceived.emit(w, x, y, z)
                    quat_display_clk = 0

            if euler:
                # serail rx: [yaw, pitch, roll]
                euler_display_clk += 1
                yaw, pitch, roll = euler[-1]
                if euler_display_clk >= 20:
                    self.eulerDataReceived.emit(yaw, pitch, roll)
                    euler_display_clk = 0

            # 计算数据率
            data_packets_len += len(xyzw)
            if data_packets_len >= 100:
                data_rate = 1000/(time_diff.time_difference()/data_packets_len)
                data_packets_len = 0
                self.dtDataReceived.emit(data_rate)

            # time_diff.time_difference(print_flag=True)
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

        self.a_cal_state_last = -1
        self.g_cal_state_last = -1
        self.hw_mag_cal_state_last = -1
        self.sf_mag_cal_state_last = -1

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

        self.setMinimumSize(800, 680)
        grid = QGridLayout()

        font = QFont("Arial", 11)
        font.setBold(True)

        # 第一列
        self.label1 = QLabel("串口")
        self.label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label1.setFont(font)
        self.label1.setFixedWidth(50)
        grid.addWidget(self.label1, 0, 0)

        self.combo1 = QComboBox()
        self.combo1.addItems(self.com_des_list)
        self.combo1.setFixedWidth(180)
        grid.addWidget(self.combo1, 0, 1)

        self.label2 = QLabel("波特率")
        self.label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label2.setFont(font)
        # self.label2.setFixedWidth(50)
        grid.addWidget(self.label2, 1, 0)

        self.combo2 = QComboBox()
        self.combo2.addItems([str(v) for v in self.baud_list])
        self.combo2.setFixedWidth(180)
        grid.addWidget(self.combo2, 1, 1)

        self.btn = QPushButton("打开串口")
        self.btn.clicked.connect(self.on_btn_clicked)
        self.btn.setFixedWidth(180)
        grid.addWidget(self.btn, 2, 1)

        # 第三列
        self.calEdits = []
        for i, label in enumerate(["acc_cal", "gyr_cal", "hw_mag_cal", "sf_mag_cal"]):
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFont(font)
            lbl.setFixedWidth(85)
            grid.addWidget(lbl, i, 2)  # change to third column

            edit = QLineEdit("")
            edit.setFixedWidth(100)
            grid.addWidget(edit, i, 3)  # change to third column
            self.calEdits.append(edit)

        # 第三列
        self.quatEdits = []
        for i, label in enumerate(["w", "x", "y", "z"]):
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFont(font)
            lbl.setFixedWidth(30)
            grid.addWidget(lbl, i, 4)  # change to third column

            edit = QLineEdit("0.0")
            edit.setFixedWidth(100)
            grid.addWidget(edit, i, 5)  # change to third column
            self.quatEdits.append(edit)

        # 第二列
        self.eulerEdits = []
        for i, label in enumerate(["pitch", "yaw", "roll", "ODR"]):
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFont(font)
            lbl.setFixedWidth(50)
            grid.addWidget(lbl, i, 6)  # change to second column

            edit = QLineEdit("0.0")
            edit.setFixedWidth(100)
            grid.addWidget(edit, i, 7)  # change to second column
            self.eulerEdits.append(edit)

        self.checkbox = QCheckBox('接收姿态角', self)
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.on_checkbox_state_changed)
        grid.addWidget(self.checkbox, 4, 5)

        # 第四行的按钮一次对齐到第三行的文本输入框
        self.btn_reset =QPushButton("复位姿态")
        self.btn_reset.setFixedWidth(180)
        self.btn_reset.clicked.connect(self.on_btn_reset_clicked)
        grid.addWidget(self.btn_reset, 4, 1)

        # 第四行的按钮一次对齐到第三行的文本输入框
        self.btn_cal =QPushButton("获得校准状态")
        self.btn_cal.setFixedWidth(100)
        self.btn_cal.clicked.connect(self.on_btn_cal_clicked)
        grid.addWidget(self.btn_cal, 4, 3)

        # 第五行
        # grid.addWidget(QLabel(""), 4, 0, 1, 6)
        self.opengl = bds_3d.OpenGLWidget()
        grid.addWidget(self.opengl, 6, 0, 10, 8)

        self.setLayout(grid)
        self.setWindowTitle(CWM_VERSION)
        self.show()

        # 新建一个10ms的精准定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(100)
        self.ser_hot_plug_timer = 0

        # 创建新线程
        self.worker = Worker(self.js_cfg)
        self.worker.eulerDataReceived.connect(self.on_euler_data_received)
        self.worker.quatDataReceived.connect(self.on_quat_data_received)
        self.worker.quatDataReceived_3d.connect(self.on_quat_data_received_3d)
        self.worker.dtDataReceived.connect(self.on_dt_data_received)
        self.worker.start()

    def on_checkbox_state_changed(self, state):
        if state == Qt.Checked:
            if self.js_cfg['euler_own_cal']:
                quat_open(True)
            else:
                quat_open(True)
                euler_open(True)
        else:
            if self.js_cfg['euler_own_cal']:
                quat_open(False)
            else:
                quat_open(False)
                euler_open(False)

    def on_btn_clicked(self):
        if self.btn.text() == "打开串口":
            cur_ser_num = self.com_name_list[self.com_des_list.index(self.combo1.currentText())]
            cur_baud = int(self.combo2.currentText())

            log.info('串口打开:ser number: %s , baud: %d' % (cur_ser_num, cur_baud))
            print("ser number: %s" % cur_ser_num)
            print("cur baud: %d" % cur_baud)
            try:
                ser_obj.hw_open(port=cur_ser_num, baud=cur_baud, rx_buffer_size=10240*3)

                self.js_cfg['ser_baud'] = bds_ser.ser_buad_list_adjust(cur_baud, self.js_cfg['ser_baud'])
                with open('config.json', 'w') as f:
                    json.dump(self.js_cfg, f, indent=4)

                self.btn.setText("关闭串口")
                self.btn.setStyleSheet("background-color: green")

                if self.combo1.currentText().find('蓝牙') < 0:
                    time.sleep(0.02)
                    # 获得欧拉角、四元数
                    quat_open(True)
                    if not self.js_cfg['euler_own_cal']:
                        time.sleep(0.02)
                        quat_open(True)
                    time.sleep(0.02)
                    # 获取校正状态
                    if self.js_cfg['get_cal_state_en']:
                        get_agm_cal_state()
            except Exception as e:
                print(e)
                log.info('错误：%s' % str(e))
                QMessageBox.information(self, "错误:", str(e))
        else:
            try:
                log.info('串口关闭')
                self.btn.setText("打开串口")
                self.btn.setStyleSheet("")
                self.obj.hw_close()
            except Exception as e:
                QMessageBox.information(self, "错误:", str(e))

    def on_btn_reset_clicked(self):
        print("3d reset")
        log.info('3d reset')
        self.opengl.store_current_pose()

    def on_btn_cal_clicked(self):
        if self.js_cfg['get_cal_state_en']:
            get_agm_cal_state()
        else:
            print('get cal state disble..')

    def error_rpt(self, err_code):
        QMessageBox.information(self, "错误:", err_code)

    def cal_state_update(self):
        a_cal_state = ser_obj.read_a_cal_state()
        g_cal_state = ser_obj.read_g_cal_state()
        hw_mag_cal_state = ser_obj.read_hw_mag_cal_state()
        sf_mag_cal_state = ser_obj.read_sf_mag_cal_state()

        if self.a_cal_state_last != a_cal_state:
            self.calEdits[0].setText("%d" % a_cal_state)
            self.a_cal_state_last = a_cal_state

        if self.g_cal_state_last != g_cal_state:
            self.calEdits[1].setText("%d" % g_cal_state)
            self.g_cal_state_last = g_cal_state

        if self.hw_mag_cal_state_last != hw_mag_cal_state:
            self.calEdits[2].setText("%d" % hw_mag_cal_state)
            self.hw_mag_cal_state_last = hw_mag_cal_state

        if self.sf_mag_cal_state_last != sf_mag_cal_state:
            self.calEdits[3].setText("%d" % sf_mag_cal_state)
            self.sf_mag_cal_state_last = sf_mag_cal_state

    def on_timer(self):
        self.cal_state_update()
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

    def on_euler_data_received(self, yaw, pitch, roll):
        if not self.js_cfg['euler_own_cal']:
            # eulerEdits[0]~[2] ->  pitch, yaw, roll
            self.eulerEdits[0].setText('%0.3f' % pitch)
            self.eulerEdits[1].setText('%0.3f' % yaw)
            self.eulerEdits[2].setText('%0.3f' % roll)

    def on_dt_data_received(self, dt):
        self.eulerEdits[3].setText('%0.1f Hz' % dt)

    def on_quat_data_received(self, w, x, y, z):
        self.quatEdits[0].setText('%0.6f' % w)
        self.quatEdits[1].setText('%0.6f' % x)
        self.quatEdits[2].setText('%0.6f' % y)
        self.quatEdits[3].setText('%0.6f' % z)

        # roll_x, pitch_y, yaw_z
        if self.js_cfg['euler_own_cal']:
            roll, pitch, yaw = self.opengl.quaternion_to_euler(w, x, y, z)

            self.eulerEdits[0].setText('%0.3f' % self.opengl.radians_to_degrees(pitch))
            self.eulerEdits[1].setText('%0.3f' % self.opengl.radians_to_degrees(yaw))
            self.eulerEdits[2].setText('%0.3f' % self.opengl.radians_to_degrees(roll))

    def on_quat_data_received_3d(self, w, x, y, z):
        try:
            self.opengl.rotate_relative_to_base(w, x, y, z)
        except ValueError as v:
            log.info(str(v))
            print(v)

    def closeEvent(self, event):
        print("Window is closing...")
        log.info("Window is closing...\n")

        if self.obj.hw_is_open():
            self.obj.hw_close()
        # 然后调用父类的 closeEvent 方法，以确保窗口被正确关闭
        super().closeEvent(event)


def hw_error(err):
    ser_obj.hw_close()
    ex.btn.setText("打开串口")
    ex.btn.setStyleSheet("")
    log.info("错误: %s\n" % str(err))


def hw_warn(err):
    print(err)


if __name__ == '__main__':
    log.basicConfig(filename='3D.log', filemode='w', level=log.INFO, format='%(asctime)s %(message)s',
                    datefmt='%Y/%m/%d %I:%M:%S')
    ser_obj = bds_ser.BDS_Serial(hw_error, hw_warn, char_format='hex')
    app = QApplication(sys.argv)
    ex = MyWindow(ser_obj)
    sys.exit(app.exec_())


