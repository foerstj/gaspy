import unittest

from gas.gas import Attribute, Hex


class TestGas(unittest.TestCase):
    def test_attribute(self):
        s = Attribute('s', 'some string')
        self.assertEqual(None, s.datatype)
        self.assertEqual('s = some string', str(s))
        b = Attribute('b', True)
        self.assertEqual('b', b.datatype)
        self.assertEqual('b (b) = true', str(b))
        i = Attribute('i', 42)
        self.assertEqual('i', i.datatype)
        self.assertEqual('i (i) = 42', str(i))
        f = Attribute('f', 13.37)
        self.assertEqual('f', f.datatype)
        self.assertEqual('f (f) = 13.370000', str(f))
        x = Attribute('x', Hex(4711))
        self.assertEqual('x', x.datatype)
        self.assertEqual('x (x) = 0x00001267', str(x))

    def test_attribute_initstr(self):
        s = Attribute('s', 'some string')
        self.assertEqual('some string', s.value)
        b = Attribute('b', 'true', 'b')
        self.assertEqual(True, b.value)
        i = Attribute('i', '42', 'i')
        self.assertEqual(42, i.value)
        f = Attribute('f', '13.370000', 'f')
        self.assertEqual(13.37, f.value)
        x = Attribute('x', '0x00001267', 'x')
        self.assertEqual(4711, x.value)
        self.assertEqual('x (x) = 0x00001267', str(x))
