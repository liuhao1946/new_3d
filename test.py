import struct


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
        while True:
            # 查找0xAA序列的开始位置，如果未找到或缓冲区长度不足，则返回None
            while self.buffer[:4] != b'\xAA\xAA\xAA\xAA' and len(self.buffer) >= 4:
                self.buffer = self.buffer[1:]
            if len(self.buffer) < 4 + 1 + 2 + 2 + 2:
                # print("self.buffer len error: %d " % len(self.buffer), self.buffer)
                return None

            # 解包长度和其他字段
            _, _, payloads_len, _ = struct.unpack('<B H H H', self.buffer[4:4 + 1 + 2 + 2 + 2])
            packet_length = 4 + 1 + 2 + 2 + payloads_len + 2

            # 如果缓冲区长度不足以包含完整的数据包，保留现有数据
            if len(self.buffer) < packet_length:
                # print('len(self.buffer) < packet length, %d, %d\n' % (len(self.buffer), packet_length))
                # print(' '.join("%02x" % v for v in self.buffer))
                # 如果有5个AA，删除一个
                if self.buffer[:5] == b'\xAA\xAA\xAA\xAA\xAA':
                    self.buffer = self.buffer[1:]
                    continue
                else:
                    idx = self.buffer[1:].find(b'\xAA\xAA\xAA\xAA')
                    if idx >= 0 and (idx < packet_length):
                        # 数据头后面存在问题数据，删除这包数据的头部
                        self.buffer = self.buffer[4:]
                        continue
                    else:
                        # 保留数据
                        return None

            # 提取数据包
            packet_data = self.buffer[:packet_length]

            # 计算校验和
            sum_check = struct.unpack('<H', self.buffer[4 + 1 + 2 + 2 + payloads_len:4 + 1 + 2 + 2 + payloads_len + 2])[
                0]

            # 如果校验和不匹配，则跳过当前字节并继续循环
            if sum_check != sum(packet_data[0:4 + 1 + 2 + 2 + payloads_len]) & 0xFFFF:
                self.buffer = self.buffer[1:]
                continue

            # 删除已处理的数据包并返回
            self.buffer = self.buffer[packet_length:]
            return packet_data

    def parse_packet(self, packet_data):
        head = list(packet_data[:4])
        trans_direction, pack_ser, payloads_len, event_type = struct.unpack('<B H H H',
                                                                            packet_data[4:4 + 1 + 2 + 2 + 2])
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
                pass
                # print(f"Packet loss detected: 期望包序号: {expected_pack_ser}(0x{expected_pack_ser:X}) "
                #      f"实际包序号:{packet_parts['pack_ser']}(0x{packet_parts['pack_ser']:X})")

        self.last_pack_ser = packet_parts['pack_ser']




parser = PacketParser()

byte_stream = [0xAA, 0xAA, 0xAA, 0xAA, 0x01, 0xDE, 0x74, 0x12, 0x00, 0x05, 0x05, 0x10, 0xDC, 0x1A, 0xBE, 0xF9, 0x62,
               0x4C, 0xBC, 0x08, 0xDD, 0x9E, 0xBB, 0x4F, 0x08, 0x7D, 0x3F, 0x8F, 0x0B,
               0xAA, 0xAA, 0xAA, 0xAA, 0x01, 0xDF, 0x74, 0x0E, 0x00, 0x05, 0x04,
               0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0x01, 0xE1, 0x74, 0x3A, 0x00, 0x07, 0x05, 0xAA, 0xA7, 0xAA, 0x3E, 0x4D,
               0x17, 0x8B, 0xC1, 0x2B, 0xE6, 0xBF, 0xBF, 0x9C, 0xCB, 0x1A, 0xBE, 0x81, 0xAE, 0x4C, 0xBC, 0xA8, 0x00,
               0x9F,
               0xBB, 0xEB, 0x08, 0x7D, 0x3F, 0x06, 0x95, 0x43, 0xC2, 0x3A, 0x17, 0x8B,
               0xC1, 0x54, 0xE6, 0xBF, 0xBF, 0x98, 0x66, 0x07, 0xBE, 0x28, 0x35, 0x98, 0xBD, 0x35, 0x86, 0xD0, 0x3E,
               0x2E, 0x8F, 0x66, 0x3F, 0x78, 0x1F,
               0xAA, 0xAA, 0xAA, 0xAA, 0x01, 0xE2, 0x74, 0x12, 0x00, 0x06, 0x04, 0x49, 0x49, 0x43, 0x5F, 0x48, 0x41,
               0x4C, 0x5F, 0x54, 0x49, 0x4D, 0x45, 0x4F, 0x55, 0x54, 0x0A, 0xB4, 0x08,
               0xAA, 0xAA, 0xAA, 0xAA, 0x01, 0xE3, 0x74, 0x0E, 0x00, 0x05, 0x04, 0xDB, 0xCB, 0xAA, 0x3E, 0xA7, 0x08,
               0x8B, 0xC1, 0xE0, 0x59, 0xC0, 0xBF, 0x58, 0x0B
               ]

byte_stream1 = [0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0x01, 0xE1, 0x74, 0x3A, 0x00, 0x07, 0x05, 0xAA, 0xA7, 0xAA, 0x3E, 0x4D,
                0x17, 0x8B, 0xC1, 0x2B, 0xE6, 0xBF, 0xBF, 0x9C, 0xCB, 0x1A, 0xBE, 0x81, 0xAE, 0x4C, 0xBC, 0xA8, 0x00,
                0x9F,
                0xBB, 0xEB, 0x08, 0x7D, 0x3F, 0x06, 0x95, 0x43, 0xC2, 0x3A, 0x17, 0x8B,
                0xC1, 0x54, 0xE6, 0xBF, 0xBF, 0x98, 0x66, 0x07, 0xBE, 0x28, 0x35, 0x98, 0xBD, 0x35, 0x86, 0xD0, 0x3E,
                0x2E, 0x8F, 0x66, 0x3F, 0x78, 0x1F,
                ]

byte_stream2 = [0xaa, 0xaa, 0xaa, 0xaa, 0x01, 0x12, 0x92, 0x12, 0x00, 0x05, 0x05, 0xc1, 0x29, 0xe2, 0xbd, 0x71, 0xa5, 0x07, 0xbb, 0xc7, 0xd2, 0xf9, 0xbc, 0x5b, 0x50, 0x7e, 0x3f, 0x80, 0x0c]

byte_stream3 = [0xaa, 0xaa, 0xaa, 0xaa, 0x01, 0x14, 0x92, 0x12, 0x20, 0x05, 0x05, 0x39, 0x2e, 0xe2, 0xbd, 0x27, 0x7f, 0x07, 0xbb, 0x78, 0xd3, 0xf9, 0xbc, 0x4b, 0x50, 0x7e, 0x3f, 0x31, 0x0b]
byte_stream4 = [0xaa, 0xaa, 0xaa, 0xaa, 0x01, 0x97, 0x22, 0x12, 0x00, 0x05, 0x05, 0xb3, 0x91, 0x0f, 0xbe, 0xbd, 0xae, 0x7c, 0x3a, 0xf5, 0xea, 0x24, 0xbd, 0xf9, 0x42, 0x7d, 0x3f, 0x67, 0x0c]

byte_stream5 = [0xaa, 0xaa, 0xaa, 0xaa, 0x01, 0x70, 0x24, 0x0e, 0x00, 0x05, 0x04, 0x32, 0x8f, 0x92, 0x40, 0x87, 0xe7, 0x80, 0xc1]
# 0x56, 0xdd, 0x09, 0xbf, 0x91, 0x09
byte_stream6 = [0x56, 0xdd, 0x09, 0xbf, 0x91, 0x09]

s1 = "aa aa aa aa 01 91 29 12 00 05 05 8e 89 0f be 6f db 5d 3a a6 ac 24 bd 6e 43 7d 3f e4 0a"
s2 = "aa aa aa aa 01 97 22 12 00 05 05 b3 91 0f be bd ae 7c 3a f5 ea 24 bd f9 42 7d 3f 67 0c"

s3 = "aa aa aa aa 01 " \
     "aa aa aa aa 01 dc 10 3a 00 07 05 e3 59 20 3e 6b 08 73 c1 70 e2 78 be 2d 57 07 be 0d e5 fb ba 01 49 d6 ba dc c0 " \
     "7d 3f 2d e5 92 c2 59 d3 72 c1 80 b1 8a be 6d e6 d5 bd cc 8f a5 bd 19 ac 17 3f f7 70 4b 3f b2 21 " \
     "aa aa aa aa 01 dd 10 12 00 06 04 49 49 43 5f 48 41 4c 5f 54 49 4d 45 4f 55 54 0a 4b 08 "\
     "aa aa aa aa 01 de 10 0e 00 05 04 6e 4f 20 3e 03 01 73 c1 f7 e7 79 be 16 09 "\
     "aa aa aa aa 01 df 10 12 00 05 05 14 53 07 be 03 09 fd ba 02 63 d6 ba ff c0 7d 3f 13 0b"


def hex_string_to_list(hex_string: str) -> list:
    return [int(x, 16) for x in hex_string.split()]


bb = hex_string_to_list(s3)
# print(' '.join("%02x" % v for v in bb))

for packet_data, packet_parts in parser.add_data(bytes(byte_stream)):
    # print(packet_data)
    print(packet_parts)


# for packet_data, packet_parts in parser.add_data(bytes(byte_stream6)):
#     # print(packet_data)
#     print(packet_parts)


import re

CWM_VERSION = 'Cyweemotion 3D(v1.3.0)'

print(re.search(r'\((.*?)\)', CWM_VERSION).group(1))

