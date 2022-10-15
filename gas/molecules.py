from __future__ import annotations

import math
import random
import string


class Hex(int):
    @classmethod
    def random(cls):
        random_hex_str = '0x' + ''.join([random.choice(string.digits + 'abcdef') for _ in range(8)])
        return cls.parse(random_hex_str)

    @staticmethod
    def parse(value: str) -> Hex:
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
    def parse(cls, value: str) -> Position:
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
    def parse(cls, value: str) -> Quaternion:
        x, y, z, w = value.split(',')
        return Quaternion(float(x), float(y), float(z), float(w))

    @staticmethod
    def rad_to_quat(rad):
        y = math.sin(rad / 2)
        w = math.cos(rad / 2)
        return Quaternion(0, y, 0, w)

    def vector(self):
        return [self.x, self.y, self.z, self.w]

    def equals(self, other: Quaternion) -> bool:
        a = self.vector()
        b = other.vector()
        for i in range(4):
            if a[i] != b[i]:
                return False
        return True


class PContentSelector:
    def __init__(self, item_type: str, item_sub_type: str, modifier: str, power: int | tuple[int, int]):
        self.item_type = item_type
        self.item_sub_type = item_sub_type
        self.modifier = modifier
        self.power = power

    @classmethod
    def parse(cls, value: str) -> PContentSelector:
        # example pcontent selector: #weapon,r/-unique(2)/41-52
        # example pcontent selector: #*/42
        assert value.startswith('#')
        segments = value[1:].split('/')
        assert 2 <= len(segments) <= 3, value
        item_type_segments = segments[0].split(',')
        assert 1 <= len(item_type_segments) <= 2
        item_type = item_type_segments[0]
        item_sub_type = item_type_segments[1] if len(item_type_segments) == 2 else None
        modifier = segments[1] if len(segments) == 3 else None
        power_str = segments[-1]
        if '-' in power_str:
            power_segments = power_str.split('-')
            assert len(power_segments) == 2
            power_min = int(power_segments[0])
            power_max = int(power_segments[1])
            power = (power_min, power_max)
        else:
            power = int(power_str)
        return PContentSelector(item_type, item_sub_type, modifier, power)

    def __str__(self):
        item_type_str = self.item_type
        if self.item_sub_type is not None:
            item_type_str += ',' + self.item_sub_type
        power_str = str(self.power) if isinstance(self.power, int) else f'{self.power[0]}-{self.power[1]}'
        segments = [item_type_str, self.modifier, power_str] if self.modifier is not None else [item_type_str, power_str]
        return '#' + '/'.join(segments)
