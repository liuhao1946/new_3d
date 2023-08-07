import re
import threading
from queue import Queue
import queue
import struct
# from datetime import datetime
# import binascii

thread_lock = threading.Lock()


class PacketParser:
    def __init__(self):
        self.buffer = b''
        self.last_pack_ser = None
        self.last_packet = None

    def add_data(self, data):
        self.buffer += data
        while True:
            packet_data = self.extract_packet()
            if packet_data is None:
                break
            packet_parts = self.parse_packet(packet_data)
            self.check_packet_loss(packet_parts)
            self.last_packet = packet_parts
            yield packet_data, packet_parts

    def extract_packet(self):
        while self.buffer[:4] != b'\xAA\xAA\xAA\xAA' and len(self.buffer) >= 4:
            self.buffer = self.buffer[1:]

        if len(self.buffer) < 4 + 1 + 2 + 2 + 2:
            return None

        _, _, payloads_len, _ = struct.unpack('<B H H H', self.buffer[4:4 + 1 + 2 + 2 + 2])
        packet_length = 4 + 1 + 2 + 2 + payloads_len + 2

        if len(self.buffer) < packet_length:
            return None

        packet_data = self.buffer[:packet_length]

        sum_check = struct.unpack('<H', self.buffer[4 + 1 + 2 + 2 + payloads_len:4 + 1 + 2 + 2 + payloads_len + 2])[0]

        if sum_check != sum(packet_data[0:4 + 1 + 2 + 2 + payloads_len]) & 0xFFFF:
            self.buffer = self.buffer[1:]
            return None

        self.buffer = self.buffer[packet_length:]
        return packet_data

    def parse_packet(self, packet_data):
        head = list(packet_data[:4])
        trans_direction, pack_ser, payloads_len, event_type = struct.unpack('<B H H H', packet_data[4:4 + 1 + 2 + 2 + 2])
        user_data = list(packet_data[4 + 1 + 2 + 2 + 2:4 + 1 + 2 + 2 + payloads_len])
        sum_check = struct.unpack('<H', packet_data[4 + 1 + 2 + 2 + payloads_len:4 + 1 + 2 + 2 + payloads_len + 2])[0]

        return {
            'head': head,
            'trans_direction': trans_direction,
            'pack_ser': pack_ser,
            'payloads_len': payloads_len,
            'event_type': event_type,
            'user_data': user_data,
            'sum': sum_check,
        }

    def check_packet_loss(self, packet_parts):
        if self.last_pack_ser is not None:
            expected_pack_ser = (self.last_pack_ser + 1) % 0x10000
            if packet_parts['pack_ser'] != expected_pack_ser:
                print(f"Packet loss detected: expected pack_ser={expected_pack_ser}, got {packet_parts['pack_ser']}")

        self.last_pack_ser = packet_parts['pack_ser']


def find_key(text, key):
    pattern = fr"{key}\((\d+)\)"
    match = re.search(pattern, text)
    if match:
        sn_value = int(match.group(1))
        return sn_value
    return None


def find_group(text, key):
    pattern = fr"{key}\*(\d+)\((-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*)\)"
    match = re.search(pattern, text)
    if match:
        n = int(match.group(1))
        x = int(match.group(2))/(10**n) if n != 0 else int(match.group(2))
        y = int(match.group(3))/(10**n) if n != 0 else int(match.group(3))
        z = int(match.group(4))/(10**n) if n != 0 else int(match.group(4))
        return [x, y, z]
    return []


class HardWareBase:
    def __init__(self, err_cb, warn_cb, tag_detect_timeout_s, read_rtt_data_interval_s, char_format, **kwargs):
        self.err_cb = err_cb
        self.warn_cb = warn_cb
        self.char_format = char_format

        self.a_cal_state = 0
        self.g_cal_state = 0
        self.hw_mag_cal_state = 0
        self.sf_mag_cal_state = 0

        self.xyzw_q = Queue()
        self.euler_q = Queue()

        self.err_q = Queue()
        self.log_q = Queue()
        self.save_log = False

        self.parser = PacketParser()

        self.downsample_rate = 1
        self.packet_counter = 0
        self.sensor_odr = 0
        self.uart_odr = 0

        self.ag_yaw = -1000
        self.ag_pitch = -1000
        self.ag_roll = -1000
        self.agm_yaw = -1000
        self.agm_pitch = -1000
        self.agm_roll = -1000

        self.evt_cb = {
                0x0505: self.__fetch_xyzw,
                0x0405: self.__fetch_euler,
                0x0403: self.__fetch_cal_inf,
                0x0303: self.__fetch_odr,
                0x0506: self.__fetch_alg_result,
                0x0406: self.__fetch_err_inf,
              }

    def hw_open(self, **kwargs):
        pass

    def hw_is_open(self):
        pass

    def hw_close(self):
        pass

    def hw_set_char_format(self, c_format):
        self.char_format = c_format

    def hw_data_handle(self, s1):
        pass

    def __fetch_err_inf(self, data):
        self.err_q.put(''.join([chr(v) for v in data]))

    def __fetch_alg_result(self, data):
        bytes_data = bytes(data)
        self.ag_yaw, self.ag_pitch, self.ag_roll = struct.unpack('<fff', bytes_data[0:12])
        print(self.ag_yaw, self.ag_pitch, self.ag_roll)
        ag_x, ag_y, ag_y, ag_w = struct.unpack('<ffff', bytes_data[12:28])
        self.agm_yaw, self.agm_pitch, self.agm_roll = struct.unpack('<fff', bytes_data[28:40])
        agm_x, agm_y, agm_z, agm_w = struct.unpack('<ffff', bytes_data[40:56])
        print(self.agm_yaw, self.agm_pitch, self.agm_roll)

    def __fetch_odr(self, data):
        bytes_data = bytes(data)
        self.sensor_odr = struct.unpack('<i', bytes_data[0:4])[0]
        self.uart_odr = struct.unpack('<H', bytes_data[4:6])[0]

        print(self.sensor_odr, self.uart_odr)

    def __fetch_cal_inf(self, data):
        self.a_cal_state = data[0] & 0x0f
        self.g_cal_state = (data[0] & 0xf0) >> 4
        self.hw_mag_cal_state = data[1] & 0x0f
        self.sf_mag_cal_state = (data[1] & 0xf0) >> 4

        print('a_cal:%d g_cal:%d hw_mag_cal:%d sf_mag_cal:%d ' % (self.a_cal_state, self.g_cal_state,
                                                                  self.hw_mag_cal_state, self.sf_mag_cal_state))

    def __fetch_log_string(self):
        pass

    def __fetch_euler(self, data):
        bytes_data = bytes(data)

        # 将每4个字节转换为一个浮点数
        yaw, pitch, roll = struct.unpack('<fff', bytes_data[0:12])
        self.euler_q.put([yaw, pitch, roll])

    def __fetch_xyzw(self, data):
        bytes_data = bytes(data)

        # 将每4个字节转换为一个浮点数
        x, y, z, w = struct.unpack('<ffff', bytes_data[0:16])
        self.xyzw_q.put([x, y, z, w])

    def hw_data_hex_handle(self, byte_stream):
        if byte_stream == b'':
            return

        for packet_data, packet_parts in self.parser.add_data(byte_stream):
            try:
                # print(hex(packet_parts['event_type']))
                self.evt_cb[packet_parts['event_type']](packet_parts['user_data'])
            except Exception as e:
                print(e)
            if self.save_log:
                thread_lock.acquire()
                self.log_q.put(packet_data)
                thread_lock.release()

    def hw_save_log(self, state):
        self.save_log = state

        thread_lock.acquire()
        self.log_q.queue.clear()
        thread_lock.release()

    def hw_write(self, data):
        pass

    def hw_para_init(self):
        self.packet_counter = 0

    def get_hw_serial_number(self):
        pass

    def read_euler(self):
        data_list = []
        while not self.euler_q.empty():
            try:
                data_list.append(self.euler_q.get())
            except queue.Empty:
                pass
        return data_list

    def read_xyzw(self):
        data_list = []
        while not self.xyzw_q.empty():
            try:
                data_list.append(self.xyzw_q.get())
            except queue.Empty:
                pass
        return data_list

    def read_a_cal_state(self):
        return self.a_cal_state

    def read_g_cal_state(self):
        return self.g_cal_state

    def read_hw_mag_cal_state(self):
        return self.hw_mag_cal_state

    def read_sf_mag_cal_state(self):
        return self.sf_mag_cal_state

    def read_odr(self):
        return [self.sensor_odr, self.uart_odr]

    def hw_read_log(self):
        data_bytes = b''
        while not self.log_q.empty():
            try:
                data_bytes += bytes(self.log_q.get())
            except queue.Empty:
                pass

        return data_bytes

    def hw_read_err(self):
        data_list = ''
        while not self.err_q.empty():
            try:
                data_list += self.err_q.get()
            except queue.Empty:
                pass
        return data_list

    def hw_read_ag_alg_output(self):
        if self.ag_yaw == -1000:
            return []

        ag = [self.ag_yaw, self.ag_pitch, self.ag_roll]
        self.ag_yaw = self.ag_pitch = self.ag_roll = -1000

        return ag

    def hw_read_agm_alg_output(self):
        if self.agm_yaw == -1000:
            return []

        agm = [self.agm_yaw, self.agm_pitch, self.agm_roll]
        self.agm_yaw = self.agm_pitch = self.agm_roll = -1000

        return agm


if __name__ == '__main__':
    pass
