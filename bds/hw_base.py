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
            packet = self.parse_packet()
            if packet is None:
                break
            self.check_packet_loss(packet)
            self.last_packet = packet
            yield packet

    def parse_packet(self):
        # If the buffer doesn't start with the correct header, discard data until it does
        while self.buffer[:4] != b'\xAA\xAA\xAA\xAA' and len(self.buffer) >= 4:
            self.buffer = self.buffer[1:]

        # If we don't have enough data for a complete packet, return None
        if len(self.buffer) < 4 + 1 + 2 + 2 + 2:  # size of each section of the packet
            return None

        # Parse the packet
        head = list(self.buffer[:4])
        trans_direction, pack_ser, payloads_len, event_type = struct.unpack('<B H H H', self.buffer[4:4 + 1 + 2 + 2 + 2])

        # Check if we have all the user data
        if len(self.buffer) < 4 + 1 + 2 + 2 + payloads_len + 2:  # size of each section of the packet and user data
            return None

        user_data = list(self.buffer[4 + 1 + 2 + 2 + 2:4 + 1 + 2 + 2 + payloads_len])

        sum_check = struct.unpack('<H', self.buffer[4 + 1 + 2 + 2 + payloads_len:4 + 1 + 2 + 2 + payloads_len + 2])[0]

        # Validate checksum
        if sum_check != sum(self.buffer[0:4 + 1 + 2 + 2 + payloads_len]) & 0xFFFF:
            # Checksum failed; discard this packet and look for the next one
            self.buffer = self.buffer[1:]
            return None

        # Remove this packet from the buffer
        self.buffer = self.buffer[4 + 1 + 2 + 2 + payloads_len + 2:]

        return {
            'head': head,
            'trans_direction': trans_direction,
            'pack_ser': pack_ser,
            'payloads_len': payloads_len,
            'event_type': event_type,
            'user_data': user_data,
            'sum': sum_check,
        }

    def check_packet_loss(self, packet):
        if self.last_pack_ser is not None:
            expected_pack_ser = (self.last_pack_ser + 1) % 0x10000  # We use modulo operation to handle overflow
            if packet['pack_ser'] != expected_pack_ser:
                print(f"Packet loss detected: expected pack_ser={expected_pack_ser}, got {packet['pack_ser']}")
                # print(f"Last packet: {self.last_packet}")
                # print(f"Current packet: {packet}")

        self.last_pack_ser = packet['pack_ser']


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

        self.xyzw_q = Queue()
        self.euler_q = Queue()

        self.parser = PacketParser()

        self.downsample_rate = 10
        self.packet_counter = 0

        self.evt_cb = {
                0x0505: self.__fetch_xyzw,
                0x0405: self.__fetch_euler,
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

    def __fetch_euler(self, data):
        bytes_data = bytes(data)

        # 将每4个字节转换为一个浮点数
        yaw = struct.unpack('<f', bytes_data[0:4])[0]
        pitch = struct.unpack('<f', bytes_data[4:8])[0]
        roll = struct.unpack('<f', bytes_data[8:12])[0]
        self.euler_q.put([yaw, pitch, roll])

    def __fetch_xyzw(self, data):
        bytes_data = bytes(data)

        # 将每4个字节转换为一个浮点数
        x = struct.unpack('<f', bytes_data[0:4])[0]
        y = struct.unpack('<f', bytes_data[4:8])[0]
        z = struct.unpack('<f', bytes_data[8:12])[0]
        w = struct.unpack('<f', bytes_data[12:16])[0]

        self.xyzw_q.put([x, y, z, w])

    def hw_data_hex_handle(self, byte_stream):
        if byte_stream != b'':
            for packet in self.parser.add_data(byte_stream):
                self.packet_counter += 1
                if self.packet_counter == self.downsample_rate:
                    self.packet_counter = 0
                    self.evt_cb[packet['event_type']](packet['user_data'])

    def hw_write(self, data):
        pass

    def hw_para_init(self):
        self.packet_counter = 0

    def get_hw_serial_number(self):
        pass

    def read_euler(self):
        pass

    def read_xyzw(self):
        data_list = []
        while not self.xyzw_q.empty():
            try:
                data_list.append(self.xyzw_q.get())
            except queue.Empty:
                pass
        return data_list


if __name__ == '__main__':
    pass
