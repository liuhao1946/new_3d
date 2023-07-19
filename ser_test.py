import PySimpleGUI as sg
import bds.bds_serial as bds_ser
import time
import threading
import struct
import math
import bds.time_diff as td

thread_lock = threading.Lock()

thread_lock.acquire()

DB_OUT = 'db_out' + sg.WRITE_ONLY_KEY

global stop_tx_flag


def tx_hex_data(win, ser_obj):
    head = [0xAA, 0XAA, 0XAA, 0XAA]
    direct = [0x01]
    # 四元数
    q_data_len = [0x12, 0x00]
    q_sid = [0x05, 0x05]
    # 欧拉角
    e_data_len = [0x0e, 0x00]
    e_sid = [0x05, 0x04]
    e_user_data = [0x69, 0x85, 0xC6, 0xC2, 0xEA, 0xBC, 0xE5, 0xBF, 0xEB, 0xAB, 0x5C, 0x3F]

    serial_num = 0
    time_diff = td.TimeDifference()
    theta = 0  # initial rotation angle
    while True:
        # thread_lock.acquire()

        try:
            # calculate quaternion
            theta_rad = math.radians(theta)
            qw = math.cos(theta_rad / 2)
            qx = math.sin(theta_rad / 2)
            qy = 0
            qz = 0
            q_user_data = struct.pack("<ffff", qx, qy, qz, qw)

            serial_num += 1
            if serial_num > 65535:
                serial_num = 0

            serial = list(struct.pack("<H", serial_num))
            data = head + direct + serial + q_data_len + q_sid + list(q_user_data)
            data_sum = list(struct.pack("<H", sum(data)))
            ser_obj.hw_write(data+data_sum)

           # time_diff.time_difference(print_flag=True)

            # serial_num += 1
            # if serial_num > 65535:
            #     serial_num = 0
            # serial = list(struct.pack("<H", serial_num))
            # data = head + direct + serial + e_data_len + e_sid + e_user_data
            # data_sum = list(struct.pack("<H", sum(data)))

            #ser_obj.hw_write(data + data_sum)
        except Exception as e:
            print(e)

        # if not stop_tx_flag:
        #     pass
            # thread_lock.release()

        # update rotation angle
        theta += 1.2
        if theta >= 360:
            theta -= 360

        time.sleep(0.001)


def ser_connect(win, obj, com, baud):
    if win['ser_connect'].get_text() == '串口连接':
        try:
            cur_com_name = com
            cur_baud = baud
            obj.hw_open(port=cur_com_name, baud=cur_baud, rx_buffer_size=10240*3)
            if obj.hw_is_open():
                win['ser_connect'].update('关闭串口', button_color=('grey0', 'green4'))
        except Exception as e:
            print(e)
            obj.hw_close()
            win['ser_connect'].update('串口连接', button_color=('grey0', 'grey100'))
    else:
        obj.hw_close()
        win['ser_connect'].update('串口连接', button_color=('grey0', 'grey100'))
        time.sleep(0.1)


def hw_error(err):
    print(err)


def hw_warn(err):
    print(err)


def main():
    global stop_tx_flag

    com_des_list, com_name_list = bds_ser.serial_find()
    if not com_des_list:
        com_des_list.append('')

    baud_list = [1000000, 2000000, 1152000, 115200, 9600]

    ser_layout = [[sg.T('串口'),
                   sg.Combo(com_des_list, default_value=com_des_list[0], key='com_des_list', readonly=True,
                            size=(30, 1)),
                   sg.T('波特率', pad=((45, 5), (5, 5))),
                   sg.Combo(baud_list, default_value=baud_list[0], key='baud_list', size=(10, 1), pad=((5, 5), (5, 5))),
                   sg.Button('串口连接', key='ser_connect')
                   ],
                  [sg.Button('开始发送', key='ser_tx')],
                  [sg.Multiline(autoscroll=True, key=DB_OUT, size=(80, 10))],
                  ]

    window = sg.Window('串口测试', ser_layout, modal=True)
    ser_obj = bds_ser.BDS_Serial(hw_error, hw_warn, char_format='hex')
    threading.Thread(target=tx_hex_data, args=(window, ser_obj), daemon=True).start()

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            ser_obj.hw_close()
            break
        elif event == 'ser_connect':
            com = com_name_list[com_des_list.index(window['com_des_list'].get())]
            baud = int(window['baud_list'].get())

            print('com: %s' % com)
            print('baud: %d' % baud)
            ser_connect(window, ser_obj, com, baud)
        elif event == 'ser_tx':
            if window['ser_tx'].get_text() == '开始发送':
                window['ser_tx'].update('停止发送', button_color=('grey0', 'green4'))
                stop_tx_flag = False
                thread_lock.release()
                time.sleep(0.1)
            else:
                stop_tx_flag = True
                window['ser_tx'].update('开始发送', button_color=('grey0', 'grey100'))
                time.sleep(0.1)

    window.close()


if __name__ == '__main__':
    main()
