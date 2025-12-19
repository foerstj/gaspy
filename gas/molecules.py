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

    @staticmethod
    def convert(value) -> Hex:
        if isinstance(value, str):
            return Hex.parse(value)
        return Hex(value)

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
        return Position(float(x), float(y), float(z), Hex.parse(node_guid))


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

    @staticmethod
    def multiply(a: Quaternion, b: Quaternion) -> Quaternion:
        return Quaternion(
            a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
            a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
            a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
        )

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
    def __init__(self, item_type: str, item_sub_type: str, modifiers: list[str], power: int | tuple[int, int]):
        self.item_type = item_type
        self.item_sub_type = item_sub_type
        self.modifiers = modifiers
        self.power = power

    @classmethod
    def parse(cls, value: str) -> PContentSelector:
        # example pcontent selector: #weapon,r/-unique(2)/41-52
        # example pcontent selector: #*/42
        # also valid: #spellbook/79-87/-mod(1)
        # also valid: #book_glb_magic_07/79-87/+ofconvoking
        # also valid lol: #shovel/+praised/+ofomniscience
        assert value.startswith('#')
        segments = value[1:].split('/')
        item_type_segments = segments[0].split(',')
        assert 1 <= len(item_type_segments) <= 2
        item_type = item_type_segments[0]
        item_sub_type = item_type_segments[1] if len(item_type_segments) == 2 else None
        power = None
        modifiers = list()
        for segment in segments[1:]:
            if not segment:
                continue
            if segment.startswith('-') or segment.startswith('+'):
                modifiers.append(segment)
            else:
                assert power is None
                if '-' in segment:
                    power_segments = segment.split('-')
                    assert len(power_segments) == 2
                    power_min = int(power_segments[0])
                    power_max = int(power_segments[1])
                    power = (power_min, power_max)
                else:
                    power = int(segment)
        return PContentSelector(item_type, item_sub_type, modifiers, power)

    def __str__(self):
        item_type_str = self.item_type
        if self.item_sub_type is not None:
            item_type_str += ',' + self.item_sub_type
        segments = [item_type_str] + self.modifiers
        if self.power is not None:
            power_str = str(self.power) if isinstance(self.power, int) else f'{self.power[0]}-{self.power[1]}'
            segments.append(power_str)
        return '#' + '/'.join(segments)
