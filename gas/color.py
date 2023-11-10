from gas.molecules import Hex


class Color(Hex):
    def get_argb(self) -> (int, int, int, int):
        hex_value = self
        b = hex_value % 0x100
        hex_value //= 0x100
        g = hex_value % 0x100
        hex_value //= 0x100
        r = hex_value % 0x100
        hex_value //= 0x100
        a = hex_value
        return a, r, g, b

    @classmethod
    def from_argb(cls, a: int, r: int, g: int, b: int):
        for x in [a, r, g, b]:
            assert x >= 0
            assert x <= 255
        hex_value = 0
        hex_value += a
        hex_value *= 0x100
        hex_value += r
        hex_value *= 0x100
        hex_value += g
        hex_value *= 0x100
        hex_value += b
        return Color(hex_value)
