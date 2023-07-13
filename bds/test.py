import struct


class PacketParser:
    def __init__(self):
        self.buffer = b''

    def add_data(self, data):
        self.buffer += data
        while True:
            packet = self.parse_packet()
            if packet is None:
                break
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
        trans_direction, pack_ser, payloads_len, event_type = struct.unpack('<B H H H',
                                                                            self.buffer[4:4 + 1 + 2 + 2 + 2])

        # Check if we have all the user data
        if len(self.buffer) < 4 + 1 + 2 + 2 + payloads_len + 2:  # size of each section of the packet and user data
            return None

        user_data = list(self.buffer[4 + 1 + 2 + 2:4 + 1 + 2 + 2 + payloads_len])

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


# data = [0xAA, 0xAA, 0xAA, 0xAA, 0x01, 0x16, 0xEA, 0x0E, 0x00, 0x05, 0x04, 0x0C, 0x63, 0x2C, 0x43, 0xBE, 0xA0, 0xF3,
#         0xBF, 0x1F, 0x3A, 0x34, 0x3F, 0x7A, 0x08, 0XAA, 0xAA, 0xAA, 0xAA, 0x01, 0x16, 0xEA, 0x0E, 0x00, 0x05, 0x04, 0x0C, 0x63, 0x2C, 0x43, 0xBE, 0xA0, 0xF3,
#          0xBF, 0x1F, 0x3A, 0x34, 0x3F, 0x7A, 0x08]
#
# parser = PacketParser()
# for packet in parser.add_data(bytes(data)):
#     print(packet)
#
# data1 = [0xAA, 0x01, 0x16, 0xEA, 0x0E, 0x00, 0x05, 0x04, 0x0C, 0x63, 0x2C, 0x43, 0xBE, 0xA0, 0xF3,
#          0xBF, 0x1F, 0x3A, 0x34, 0x3F, 0x7A, 0x8]
#
# for packet in parser.add_data(bytes(data1)):
#     print(packet)


# 给定的列表
data = [146, 96, 134, 188, 88, 174, 237, 187, 117, 229, 93, 63, 142, 41, 255, 62]

# 将列表中的整数转换为字节
bytes_data = bytes(data)

# 将每4个字节转换为一个浮点数
x = struct.unpack('<f', bytes_data[0:4])[0]
y = struct.unpack('<f', bytes_data[4:8])[0]
z = struct.unpack('<f', bytes_data[8:12])[0]
w = struct.unpack('<f', bytes_data[12:16])[0]

print(f"x: {x}, y: {y}, z: {z}, w: {w}")

