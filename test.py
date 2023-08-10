
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
                pass
                # print(f"Packet loss detected: expected pack_ser={expected_pack_ser}, got {packet_parts['pack_ser']}")
                # print(packet_parts)

        self.last_pack_ser = packet_parts['pack_ser']

parser = PacketParser()

byte_stream = [0xAA,0xAA,0xAA,0xAA,0x01,0xDE,0x74,0x12,0x00,0x05,0x05,0x10,0xDC,0x1A,0xBE,0xF9,0x62,0x4C,0xBC,0x08,0xDD,0x9E,0xBB,0x4F,0x08,0x7D,0x3F,0x8F,0x0B,
               0xAA,0xAA,0xAA,0xAA,0x01,0xDF,0x74,0x0E,0x00,0x05,0x04,
               0xAA,0xAA,0xAA,0xAA,0xAA,0x01,0xE1,0x74,0x3A,0x00,0x07,0x05,0xAA,0xA7,0xAA,0x3E,0x4D,0x17,
               0x8B,0xC1,0x2B,0xE6,0xBF,0xBF,0x9C,0xCB,0x1A,0xBE,0x81,0xAE,0x4C,0xBC,0xA8,0x00,0x9F,0xBB,0xEB,0x08,0x7D,0x3F,0x06,0x95,0x43,0xC2,0x3A,0x17,0x8B,
               0xC1,0x54,0xE6,0xBF,0xBF,0x98,0x66,0x07,0xBE,0x28,0x35,0x98,0xBD,0x35,0x86,0xD0,0x3E,0x2E,0x8F,0x66,0x3F,0x78,0x1F,
               0xAA,0xAA,0xAA,0xAA,0x01,0xE2,0x74,0x12,0x00,0x06,0x04,0x49,0x49,0x43,0x5F,0x48,0x41,0x4C,0x5F,0x54,0x49,0x4D,0x45,0x4F,0x55,0x54,0x0A,0xB4,0x08,
               0xAA,0xAA,0xAA,0xAA,0x01,0xE3,0x74,0x0E,0x00,0x05,0x04,0xDB,0xCB,0xAA,0x3E,0xA7,0x08,0x8B,0xC1,0xE0,0x59,0xC0,0xBF,0x58,0x0B
               ]

for packet_data, packet_parts in parser.add_data(bytes(byte_stream)):
    # print(packet_data)
    print(packet_parts)
