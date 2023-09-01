import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QByteArray, QMutex, pyqtSlot
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QDialog, QTextEdit, QSizePolicy, QAction, QProgressBar, QVBoxLayout
from PyQt5.QtWidgets import QStatusBar
import time
import bds.bds_serial as bds_ser
from PyQt5.QtGui import QPixmap, QIcon, QFont
import bds.bds_3d as bds_3d
import json
import struct
import bds.time_diff as td
import logging as log
import datetime
import csv
import os
import requests
import re

download_test_json = {'id': 326968, 'tag_name': 'v1.2.1', 'target_commitish': 'd1ead002c3591d91ae442965d019d76da0cb395f', 'prerelease': False, 'name': 'v1.2.1', 'body': '1、新增log显示区域\r\n2、新增录制原始数据log\r\n3、新增欧拉角求差并保存到文件\r\n4、新增一键跳转按钮', 'author': {'id': 13296607, 'login': 'cyweemotion-public', 'name': 'cyweemotion_public', 'avatar_url': 'https://gitee.com/assets/no_portrait.png', 'url': 'https://gitee.com/api/v5/users/cyweemotion-public', 'html_url': 'https://gitee.com/cyweemotion-public', 'remark': '', 'followers_url': 'https://gitee.com/api/v5/users/cyweemotion-public/followers', 'following_url': 'https://gitee.com/api/v5/users/cyweemotion-public/following_url{/other_user}', 'gists_url': 'https://gitee.com/api/v5/users/cyweemotion-public/gists{/gist_id}', 'starred_url': 'https://gitee.com/api/v5/users/cyweemotion-public/starred{/owner}{/repo}', 'subscriptions_url': 'https://gitee.com/api/v5/users/cyweemotion-public/subscriptions', 'organizations_url': 'https://gitee.com/api/v5/users/cyweemotion-public/orgs', 'repos_url': 'https://gitee.com/api/v5/users/cyweemotion-public/repos', 'events_url': 'https://gitee.com/api/v5/users/cyweemotion-public/events{/privacy}', 'received_events_url': 'https://gitee.com/api/v5/users/cyweemotion-public/received_events', 'type': 'User'}, 'created_at': '2023-08-09T13:13:25+08:00', 'assets': [{'browser_download_url': 'https://gitee.com/cyweemotion-public/cwm_3d/releases/download/v1.2.1/CWM_3D.msi', 'name': 'CWM_3D.msi'}, {'browser_download_url': 'https://gitee.com/cyweemotion-public/cwm_3d/archive/refs/tags/v1.2.1.zip'}]}

global ser_obj

CWM_VERSION = 'Cyweemotion 3D(v1.3.1)'

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
    data_len = to_2bytes(len(sid + user_data))
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


def short_to_b(n):
    return list(struct.pack('<H', n))


def uint_to_b(n):
    return list(struct.pack('<I', n))


class VerDetectWorker(QThread):
    ver_remind = pyqtSignal(dict)

    def __init__(self, ver):
        QThread.__init__(self)
        self.ver = ver

    def run(self):
        try:
            print('Download from gitee')
            latest_release = requests.get("https://gitee.com/api/v5/repos/cyweemotion-public/cwm_3d/releases",
                                          timeout=5).json()[-1]
            log.info('download source: gitee')

            print(self.ver, latest_release['tag_name'])
            if self.ver != latest_release['tag_name']:
                # ver_info = '软件更新:' + latest_release['tag_name'] + '\n'
                # ver_info += latest_release['body']
                self.ver_remind.emit(latest_release)
        except Exception as e:
            log.info('download error: ' + str(e))
            print('download error:' + str(e))


class download_thread(QThread):
    download_state_notify = pyqtSignal(str, str)

    mux_lock = QMutex()
    mux_lock.lock()

    def __init__(self, ver_info):
        QThread.__init__(self)
        self.ver_info = ver_info

    def run(self):
        try:
            self.mux_lock.lock()
            if not self.isInterruptionRequested():
                # 获取下载路径
                home_dir = os.path.expanduser('~')
                download_dir = os.path.join(home_dir, 'Downloads')

                rtt_latest_version = self.ver_info['tag_name']
                print('rtt latest version %s' % rtt_latest_version)
                app_log.info('rtt latest version %s' % rtt_latest_version)

                download_url = self.ver_info['assets'][0]['browser_download_url']
                tag_name = self.ver_info['assets'][0]['name']
                filename = os.path.join(download_dir, tag_name)

                print('Download url: %s' % download_url)
                print('Download path : %s' % filename)

                app_log.info('Download url: %s' % download_url)

                # # 请求文件
                response = requests.get(download_url, timeout=5, stream=True)
                # 获取文件大小
                total_size_in_bytes = int(response.headers.get('Content-Length', 0))
                block_size = 1024  # 1 Kibibyte
                download_len = 0
                print('file total size: %d' % total_size_in_bytes)
                percent_latest = 0
                with open(filename, 'wb') as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        download_len += len(data)
                        percent = download_len * 100 // total_size_in_bytes
                        if percent_latest != percent:
                            self.download_state_notify.emit('downloading', str(percent))
                            percent_latest = percent
                            print('downloading', percent)
                app_log.info('download_done')
                print('download_done')
                self.download_state_notify.emit('download_done', filename)
        except Exception as e:
                print(e)
                try:
                    self.download_state_notify.emit('download_err',  str(e))
                except:
                    pass


class DownloadDialog(QDialog):
    def __init__(self, ver_info):
        super().__init__()

        self.ver_info = ver_info
        self.setWindowTitle('download')
        self.setFixedSize(500, 300)
        layout = QVBoxLayout()

        update_info = '软件更新:' + ver_info['tag_name'] + '\n'
        update_info += ver_info['body']

        # 第一行：文本控件
        self.text_label = QLabel(update_info)
        layout.addWidget(self.text_label)

        # 第二行：进度条控件
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 第三行：超链接
        link_label = QLabel('<a href="https://gitee.com/cyweemotion-public/cwm_3d/releases">软件托管地址</a>')
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)

        # 第四行：两个按钮
        self.download_button = QPushButton('立即下载')
        layout.addWidget(self.download_button)

        self.download_button.clicked.connect(self.start_download)

        self.d_thread = download_thread(ver_info)
        self.d_thread.download_state_notify.connect(self.download_state_notify)
        self.d_thread.start()

        self.exe_file_name = ''
        self.setLayout(layout)

    def download_state_notify(self, key, value):
        if key == 'downloading':
            self.progress_bar.setValue(int(value))
        elif key == 'download_err':
            self.download_button.setText('立即下载')
            print('download error:', key, value)
            QMessageBox.information(self, "错误:", value)
        elif key == 'download_done':
            print(key, value)
            self.text_label.setText('下载完成，等待自动安装')
            self.download_button.setText('立即下载')
            self.exe_file_name = value
            self.close()

    def get_exe_file_name(self):
        return self.exe_file_name

    def start_download(self):
        if self.download_button.text() == '立即下载':
            self.d_thread.mux_lock.unlock()
            self.download_button.setText('下载中...')
            time.sleep(0.1)
            print('开始下载')
        else:
            QMessageBox.information(self, "错误:", '正在下载')

    def closeEvent(self, event):
        print('download quit....')
        self.d_thread.requestInterruption()
        self.d_thread.mux_lock.unlock()
        # self.d_thread.wait()
        super().closeEvent(event)


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

        while not self.isInterruptionRequested():
            ser_obj.hw_read()

            xyzw = ser_obj.read_xyzw()
            # euler = ser_obj.read_euler()
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

            # if euler:
            #     # serail rx: [yaw, pitch, roll]
            #     euler_display_clk += 1
            #     yaw, pitch, roll = euler[-1]
            #     if euler_display_clk >= 20:
            #         self.eulerDataReceived.emit(yaw, pitch, roll)
            #         euler_display_clk = 0

            # 计算数据率
            data_packets_len += len(xyzw)
            if data_packets_len >= 100:
                data_rate = 1000 / (time_diff.time_difference() / data_packets_len)
                data_packets_len = 0
                self.dtDataReceived.emit(data_rate)

            # time_diff.time_difference(print_flag=True)
            # 暂停一段时间模拟读取数据的过程
            time.sleep(0.005)


class Dialog(QDialog):
    cfg_dialog_state = pyqtSignal(str)  # Define a new signal

    def __init__(self):
        super(Dialog, self).__init__()
        self.setWindowTitle('配置')

        grid = QGridLayout()

        grid.setColumnStretch(0, 1)  # 设置第0列的拉伸因子为1

        # 设置传感器ODR
        self.ODR_com = QComboBox()
        self.ODR_com.addItems([str(v) for v in [125, 250, 500, 1000]])
        self.ODR_com.setFixedWidth(180)
        grid.addWidget(self.ODR_com, 0, 0)

        self.btn = QPushButton("设置传感器ODR(Hz)")
        self.btn.clicked.connect(self.set_sensor_odr)
        grid.addWidget(self.btn, 0, 1)

        # 获得ODR
        self.odr_edit = QLineEdit("")  # 创建文本输入框并设置默认值为500
        self.odr_edit.setReadOnly(True)
        self.odr_edit.setFixedWidth(180)
        grid.addWidget(self.odr_edit, 1, 0)  # 将文本输入框添加到布局中，位于按钮的旁边

        self.get_odr_bnt = QPushButton("获得传感器ODR(HZ)")
        self.get_odr_bnt.clicked.connect(self.get_odr)
        # self.btn.setFixedWidth(180)
        grid.addWidget(self.get_odr_bnt, 1, 1)

        self.setFixedSize(350, 100)  # 设置对话框的固定大小

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(100)

        self.sensor_odr = 0
        self.setLayout(grid)

    def get_odr(self):
        try:
            ser_obj.hw_write(ser_protocol_data([0x03, 0x03], []))
        except Exception as e:
            print(e)

    def set_sensor_odr(self):
        u_odr = [125, 250, 500, 500]
        cur_s_odr = uint_to_b(int(self.ODR_com.currentText()))
        cur_u_odr = short_to_b(u_odr[self.ODR_com.currentIndex()])
        ser_obj.hw_write(ser_protocol_data([0x02, 0x03], cur_s_odr + cur_u_odr))

    def on_timer(self):
        sensor_odr, uart_odr = ser_obj.read_odr()
        if self.sensor_odr != sensor_odr:
            self.sensor_odr = sensor_odr
            self.odr_edit.setText('传感器ODR: %d, 串口ODR: %d' % (sensor_odr, uart_odr))

    def closeEvent(self, event):
        self.cfg_dialog_state.emit('config dialog close')
        super().closeEvent(event)


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
        self.ser_timer_1s = 0

        self.get_alg_output_count = 0

        self.a_cal_state_last = -1
        self.g_cal_state_last = -1
        self.hw_mag_cal_state_last = -1
        self.sf_mag_cal_state_last = -1

        self.cfg_dialog_startup = False
        self.log_file_name = ''
        self.euler_log_file_name = ''
        self.sensor_odr = -1

        self.alg_output_data_file = 'aaa_log_data\\' + 'alg_output_data_' + datetime.datetime.now().strftime(
            '%Y-%m-%d_%H_%M_%S') + '.csv '
        self.t_ag = []
        self.sn = 0
        # self.state_dic = {'串口ODR': 0, '传感器ODR': 0}

        self.exe_file_name = ''

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

        app_log.info("com_des_list:%s" % self.com_des_list)
        app_log.info("com_name_list:%s" % self.com_name_list)

        try:
            self.setMinimumSize(940, 680)
            grid = QGridLayout()

            font = QFont("Arial", 11)
            font.setBold(True)

            # 第一列
            self.label1 = QLabel("串口号")
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

            self.skip_but = QPushButton('一键跳转')
            self.skip_but.clicked.connect(self.skip_to_file)
            grid.addWidget(self.skip_but, 0, 8)

            # 第三列
            self.calEdits = []
            for i, label in enumerate(["acc_cal", "gyr_cal", "hw_mag", "sw_mag"]):
                lbl = QLabel(label)
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                lbl.setFont(font)
                lbl.setFixedWidth(90)
                grid.addWidget(lbl, i, 2)  # change to third column

                edit = QLineEdit("")
                edit.setReadOnly(True)
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
                edit.setReadOnly(True)
                edit.setFixedWidth(100)
                grid.addWidget(edit, i, 5)  # change to third column
                self.quatEdits.append(edit)

            # 第二列
            self.eulerEdits = []
            for i, label in enumerate(["pitch", "yaw", "roll", "U_ODR"]):
                lbl = QLabel(label)
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                lbl.setFont(font)
                lbl.setFixedWidth(65)
                grid.addWidget(lbl, i, 6)  # change to second column

                edit = QLineEdit("0.0")
                edit.setReadOnly(True)
                edit.setFixedWidth(100)
                grid.addWidget(edit, i, 7)  # change to second column
                self.eulerEdits.append(edit)

            self.checkbox = QCheckBox('接收姿态角', self)
            self.checkbox.setChecked(False)
            self.checkbox.stateChanged.connect(self.on_checkbox_state_changed)
            grid.addWidget(self.checkbox, 4, 7)

            self.save_data = QCheckBox('保存原始数据', self)
            self.save_data.setChecked(False)
            self.save_data.stateChanged.connect(self.save_data_cb)
            grid.addWidget(self.save_data, 4, 5)

            # 第四行的按钮一次对齐到第三行的文本输入框
            self.btn_reset = QPushButton("复位姿态")
            self.btn_reset.setFixedWidth(180)
            self.btn_reset.clicked.connect(self.on_btn_reset_clicked)
            grid.addWidget(self.btn_reset, 4, 1)

            # 第四行的按钮一次对齐到第三行的文本输入框
            self.btn_cal = QPushButton("获得校准状态")
            self.btn_cal.setFixedWidth(100)
            self.btn_cal.clicked.connect(self.on_btn_cal_clicked)
            grid.addWidget(self.btn_cal, 4, 3)

            # 第五行
            # grid.addWidget(QLabel(""), 4, 0, 1, 6)
            self.opengl = bds_3d.OpenGLWidget()
            # 起始行6，起始列0，行占用9，列占用5
            # self.opengl.setContentsMargins(0, 0, 0, 20)
            grid.addWidget(self.opengl, 6, 0, 9, 7)

            # log文本框
            self.textEdit = QTextEdit()
            self.textEdit.setLineWrapMode(QTextEdit.WidgetWidth)  # 设置自动换行，这样就没有水平滚动条了
            self.textEdit.setReadOnly(True)  # 设置为只读，如果你需要的话

            self.textEdit.customContextMenuRequested.connect(self.showContextMenu)
            self.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)

            grid.addWidget(self.textEdit, 6, 7, 5, 4)

            # 获得算法结果
            self.cal_but = QPushButton("获得算法结果")
            self.cal_but.clicked.connect(self.get_alg_result)
            self.cal_but.setFixedWidth(140)
            self.cal_but.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            grid.addWidget(self.cal_but, 11, 7)

            # 重新开始
            self.reset_cal_but = QPushButton("重新开始")
            self.reset_cal_but.clicked.connect(self.reset_cal_mf)
            self.reset_cal_but.setFixedWidth(110)
            self.reset_cal_but.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            grid.addWidget(self.reset_cal_but, 11, 8)

            # 设置传感器ODR
            self.ODR_com = QComboBox()
            self.ODR_com.addItems([str(v) for v in [125, 250, 500, 1000]])
            self.ODR_com.setFixedWidth(140)
            self.ODR_com.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            grid.addWidget(self.ODR_com, 12, 7)

            self.set_ODR = QPushButton("设置传感器ODR(Hz)")
            self.set_ODR.clicked.connect(self.set_sensor_odr)
            self.set_ODR.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            grid.addWidget(self.set_ODR, 12, 8)

            self.odr_status_bar = QLabel("串口ODR: 0Hz 传感器ODR: 0Hz")
            self.odr_status_bar.setMaximumHeight(20)
            self.odr_status_bar.setStyleSheet("color: red; font-weight: bold;")
            grid.addWidget(self.odr_status_bar, 15, 0, 1, 2)

            # --------------------------------------------------
            self.setLayout(grid)
            self.setWindowTitle(CWM_VERSION)
            self.show()

            # 新建一个10ms的精准定时器
            self.timer = QTimer()
            self.timer.timeout.connect(self.on_timer)
            self.timer.start(10)

            # 创建新线程
            self.worker = Worker(self.js_cfg)
            self.worker.eulerDataReceived.connect(self.on_euler_data_received)
            self.worker.quatDataReceived.connect(self.on_quat_data_received)
            self.worker.quatDataReceived_3d.connect(self.on_quat_data_received_3d)
            self.worker.dtDataReceived.connect(self.on_dt_data_received)
            self.worker.start()

            # test
            # self.version_remind(download_test_json)

            self.ver_detect = VerDetectWorker(re.search(r'\((.*?)\)', CWM_VERSION).group(1))
            self.ver_detect.ver_remind.connect(self.version_remind)
            self.ver_detect.start()
        except Exception as e:
            app_log.info("error: %s" % str(e))


    def version_remind(self, ver_info):
        print(ver_info)
        download_dialog = DownloadDialog(ver_info)
        download_dialog.exec_()

        if download_dialog.exe_file_name != '':
            self.exe_file_name = download_dialog.exe_file_name

            self.close_timer = QTimer()
            self.close_timer.setSingleShot(True)  # 设置为单次定时器
            self.close_timer.timeout.connect(self.closeWindow)  # 连接 timeout 信号到 self.close 方法
            self.close_timer.start(300)  # 启动定时器，延迟 300 毫秒

    def closeWindow(self):
        self.close()

    def showContextMenu(self, position):
        # 创建标准上下文菜单
        menu = self.textEdit.createStandardContextMenu()

        # 创建清除动作并连接到槽函数
        clear_action = QAction('清除', self)
        clear_action.triggered.connect(self.textEdit.clear)

        # 将清除动作添加到菜单中
        menu.addAction(clear_action)

        # 使用 QTextEdit 的 mapToGlobal 方法转换位置
        menu.exec_(self.textEdit.mapToGlobal(position))

    def skip_to_file(self):
        try:
            os.startfile(os.path.dirname(os.path.realpath(sys.argv[0])) + '\\aaa_log_data')
        except Exception as e:
            print(e)
            app_log.info(str(e))

    def set_sensor_odr(self):
        u_odr = [125, 250, 500, 500]
        cur_s_odr = uint_to_b(int(self.ODR_com.currentText()))
        cur_u_odr = short_to_b(u_odr[self.ODR_com.currentIndex()])
        ser_obj.hw_write(ser_protocol_data([0x02, 0x03], cur_s_odr + cur_u_odr))

    def get_odr(self):
        ser_obj.hw_write(ser_protocol_data([0x03, 0x03], []))

    def get_alg_result(self):
        ser_obj.hw_write(ser_protocol_data([0x07, 0x05], []))
        # self.get_alg_output_count += 1
        time.sleep(0.03)

    def reset_cal_mf(self):
        self.cal_ser = 0
        self.sn = 0
        # self.get_alg_output_count = 0
        self.alg_output_data_file = 'aaa_log_data\\' + 'alg_output_data_' + \
                                    datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv '

    def save_data_cb(self, state):
        state = True if state == Qt.Checked else False
        ser_obj.hw_save_log(state)
        if state:
            self.log_file_name = 'aaa_log_data\\' + 'log_' + \
                                 datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.bin '
            self.euler_log_file_name = 'aaa_log_data\\' + 'euler_log_' + \
                                 datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv '

    def save_log_to_file(self, file_name, data_bytes):
        if data_bytes == b'':
            return
        with open(file_name, 'ab') as file:
            file.write(data_bytes)

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

    def show_dialog(self):
        pass
        # if not self.cfg_dialog_startup:
        #     self.dialog = Dialog()
        #     self.dialog.cfg_dialog_state.connect(self.cfg_dialog_state)
        #     # 非模态
        #     self.dialog.show()
        #     # 模态对话框
        #     # self.dialog.exec_()
        #     self.cfg_dialog_startup = True
        # else:
        #     print('对话框已经启动')

    def show_mf_err(self):
        err_inf = ser_obj.hw_read_err()
        if err_inf != '':
            self.textEdit.append(err_inf)  # 添加新的文本行
            self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())  # 滚动到底部

    def cfg_dialog_state(self, event):
        if event.find('close') >= 0:
            self.cfg_dialog_startup = False
            print('config dialog close...')

    def on_btn_clicked(self):
        if self.btn.text() == "打开串口":
            cur_ser_num = self.com_name_list[self.com_des_list.index(self.combo1.currentText())]
            cur_baud = int(self.combo2.currentText())

            app_log.info('串口打开:ser number: %s , baud: %d' % (cur_ser_num, cur_baud))
            print("ser number: %s" % cur_ser_num)
            print("cur baud: %d" % cur_baud)
            try:
                ser_obj.hw_open(port=cur_ser_num, baud=cur_baud, rx_buffer_size=10240 * 3)

                self.js_cfg['ser_baud'] = bds_ser.ser_buad_list_adjust(cur_baud, self.js_cfg['ser_baud'])
                with open('config.json', 'w') as f:
                    json.dump(self.js_cfg, f, indent=4)

                self.btn.setText("关闭串口")
                self.btn.setStyleSheet("background-color: green")

                if self.combo1.currentText().find('蓝牙') < 0:
                    # 先关闭四元数、欧拉角
                    euler_open(False)
                    quat_open(False)
                    time.sleep(0.03)

                    # 获得校准状态
                    get_agm_cal_state()
                    time.sleep(0.03)
                    # 获得ODR
                    self.get_odr()
                    time.sleep(0.03)

                    # 获得欧拉角、四元数
                    quat_open(True)
                    if not self.js_cfg['euler_own_cal']:
                        time.sleep(0.02)
                        euler_open(True)

                    self.checkbox.setChecked(True)
            except Exception as e:
                print(e)
                app_log.info('错误：%s' % str(e))
                QMessageBox.information(self, "错误:", str(e))
        else:
            try:
                app_log.info('串口关闭')
                self.btn.setText("打开串口")
                self.btn.setStyleSheet("")
                # self.checkbox.setChecked(False)
                # euler_open(False)
                # quat_open(False)
                time.sleep(0.05)
                self.obj.hw_close()
            except Exception as e:
                QMessageBox.information(self, "错误:", str(e))

    def on_btn_reset_clicked(self):
        print("3d reset")
        app_log.info('3d reset')
        self.opengl.store_current_pose()
        if self.js_cfg['display_angle_ref']:
            self.opengl.set_3d_data_text('Angle refer: pitch(%0.1f) yaw(%0.1f) roll(%0.1f)' %
                                         (float(self.eulerEdits[0].text()),
                                          float(self.eulerEdits[1].text()),
                                          float(self.eulerEdits[2].text())))

    def on_btn_cal_clicked(self):
        if self.js_cfg['get_cal_state_en']:
            get_agm_cal_state()
        else:
            print('get cal state disble..')

    def error_rpt(self, err_code):
        QMessageBox.information(self, "错误:", err_code)

    def show_cal_state(self):
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
        self.show_cal_state()
        self.show_odr()
        self.show_mf_err()
        try:
            self.show_alg_output()
        except Exception as e:
            print(e)
            app_log.info(str(e))

        self.ser_timer_1s += 1
        if self.ser_timer_1s > 100:
            self.ser_timer_1s = 0

            self.ser_hot_plug_timer_detect()
            self.save_log_to_file(self.log_file_name, ser_obj.hw_read_log())

    def save_euler2file(self, file_name, euler):
        if not os.path.exists(file_name):
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['yaw_1', 'yaw_1', 'yaw_2', 'yaw_diff', 'pitch_1', 'pitch_2', 'pitch_diff',
                                 'roll_1', 'roll_2', 'roll_diff'])

        with open(file_name, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([str(self.sn), '%0.2f' % self.t_ag[0], '%0.2f' % t_ag[0], '%0.2f' % diff_yaw,
                             '%0.2f' % self.t_ag[1], '%0.2f' % t_ag[1], '%0.2f' % diff_pitch,
                             '%0.2f' % self.t_ag[2], '%0.2f' % t_ag[2], '%0.2f' % diff_roll])
        # self.euler_log_file_name
        pass
        # euler = ser_obj.read_euler()

    def show_alg_output(self):
        ag = ser_obj.hw_read_ag_alg_output()
        agm = ser_obj.hw_read_agm_alg_output()

        t_ag = []
        if len(ag) > 0:
            t_ag = ag
        elif len(agm) > 0:
            t_ag = agm

        if t_ag:
            self.sn += 1
            if self.sn == 1:
                self.textEdit.append('******************************')
                self.textEdit.append('|    | Yaw   | Pitch  | Roll  |')
                self.textEdit.append('------------------------------')
                self.textEdit.append('| %d | %0.2f | %0.2f  | %0.2f |' % (self.sn, t_ag[0], t_ag[1], t_ag[2]))
            else:
                self.textEdit.append('-----------------------------')
                self.textEdit.append('| %d | %0.2f | %0.2f  | %0.2f |' % (self.sn, t_ag[0], t_ag[1], t_ag[2]))
                self.textEdit.append('-----------------------------')

                diff_yaw = (t_ag[0] - self.t_ag[0] + 180 + 360) % 360 - 180
                diff_pitch = (t_ag[1] - self.t_ag[1] + 180 + 360) % 360 - 180
                diff_roll = t_ag[2] - self.t_ag[2]

                self.textEdit.append('|diff| %0.2f | %0.2f  | %0.2f |' % (diff_yaw, diff_pitch, diff_roll))
                self.textEdit.append('-----------------------------')

                # 写标题
                if not os.path.exists(self.alg_output_data_file):
                    with open(self.alg_output_data_file, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['sn', 'yaw_1', 'yaw_2', 'yaw_diff', 'pitch_1', 'pitch_2', 'pitch_diff',
                                         'roll_1', 'roll_2', 'roll_diff'])
                with open(self.alg_output_data_file, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([str(self.sn), '%0.2f' % self.t_ag[0], '%0.2f' % t_ag[0], '%0.2f' % diff_yaw,
                                     '%0.2f' % self.t_ag[1], '%0.2f' % t_ag[1], '%0.2f' % diff_pitch,
                                     '%0.2f' % self.t_ag[2], '%0.2f' % t_ag[2], '%0.2f' % diff_roll])

            self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())  # 滚动到底部
            self.t_ag = t_ag

    def show_odr(self):
        sensor_odr, uart_odr = ser_obj.read_odr()
        if self.sensor_odr != sensor_odr:
            self.sensor_odr = sensor_odr
            self.odr_status_bar.setText("串口ODR:{}Hz, 传感器ODR:{}Hz".format(uart_odr, sensor_odr))

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
            app_log.info(str(v))
            print(v)

    def closeEvent(self, event):
        print("Window is closing...")
        app_log.info("Window is closing...\n")

        self.worker.requestInterruption()

        if self.obj.hw_is_open():
            self.obj.hw_close()

        # 然后调用父类的 closeEvent 方法，以确保窗口被正确关闭
        super().closeEvent(event)

        # 最后一刻再启动安装程序
        if self.exe_file_name != '':
            try:
                print('start install....')
                os.startfile(self.exe_file_name)
            except Exception as e:
                print(e)


def hw_error(err):
    time.sleep(0.05)

    ser_obj.hw_close()
    ex.btn.setText("打开串口")
    ex.btn.setStyleSheet("")
    app_log.info("错误: %s\n" % str(err))
    print("错误: %s\n" % str(err))


def hw_warn(err):
    print(err)


if __name__ == '__main__':
    log.basicConfig(filename='3D.log', filemode='w', level=log.INFO, format='%(asctime)s %(message)s',
                    datefmt='%Y/%m/%d %I:%M:%S')
    app_log = log.getLogger('app_log')

    ser_obj = bds_ser.BDS_Serial(hw_error, hw_warn, char_format='hex')
    app = QApplication(sys.argv)
    ex = MyWindow(ser_obj)
    sys.exit(app.exec_())
