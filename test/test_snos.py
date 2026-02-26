import unittest

from bits.bits import Bits
from test.files import Files


class TestSNOs(unittest.TestCase):
    files = Files()

    def test_sno_print(self):
        bits = Bits(self.files.terrain_bits_dir)
        sno = bits.snos.get_sno_by_path('generic\\floor\\t_xxx_flr_04x04-v0.sno')
        sno.print()  # runs kaitaistruct


if __name__ == '__main__':
    unittest.main()
