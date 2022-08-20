import math
import random
import string


class Hex(int):
    @classmethod
    def random(cls):
        random_hex_str = '0x' + ''.join([random.choice(string.digits + 'abcdef') for _ in range(8)])
        return cls.parse(random_hex_str)

    @staticmethod
    def parse(value: str):
        return Hex(int(value, 0))

    def __str__(self):
        return self.to_str_upper()

    def to_str_lower(self):
        return '0x{:08x}'.format(self)

    def to_str_upper(self):
        return '0x{:08X}'.format(self)


class Position:
    def __init__(self, x: float, y: float, z: float, node_guid: Hex):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.node_guid = node_guid

    def __str__(self):
        return ','.join([str(x) for x in [self.x, self.y, self.z, self.node_guid]])

    @classmethod
    def parse(cls, value: str):
        x, y, z, node_guid = value.split(',')
        return Position(float(x), float(y), float(z), node_guid)


class Quaternion:
    def __init__(self, x: float, y: float, z: float, w: float):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __str__(self):
        return ','.join([self.format_float(x) for x in [self.x, self.y, self.z, self.w]])

    @classmethod
    def format_float(cls, value: float) -> str:
        formatted = f'{value:.6f}'
        while formatted.endswith('0'):
            formatted = formatted[:-1]
        if formatted.endswith('.'):
            formatted = formatted[:-1]
        return formatted

    @classmethod
    def parse(cls, value: str):
        x, y, z, w = value.split(',')
        return Quaternion(float(x), float(y), float(z), float(w))

    @staticmethod
    def rad_to_quat(rad):
        y = math.sin(rad / 2)
        w = math.cos(rad / 2)
        return Quaternion(0, y, 0, w)

    def vector(self):
        return [self.x, self.y, self.z, self.w]

    def equals(self, other: 'Quaternion') -> bool:
        a = self.vector()
        b = other.vector()
        for i in range(4):
            if a[i] != b[i]:
                return False
        return True
