import math
import unittest

from arithmetics import eval_expression
from bits.maps.decals_gas import Decal


class TestArithmetics(unittest.TestCase):
    def test_value(self):
        self.assertEqual(eval_expression('42'), 42)
        self.assertEqual(eval_expression('13.37'), 13.37)

    def test_simple_operators(self):
        self.assertEqual(eval_expression('1+1'), 2)
        self.assertEqual(eval_expression('5-2'), 3)
        self.assertEqual(eval_expression(' 7 * 7 '), 49)
        self.assertEqual(eval_expression('12/3'), 4)
        self.assertEqual(eval_expression('12 / 5'), 2.4)

    def test_braces(self):
        self.assertEqual(eval_expression('1+(2*3)'), 7)
        self.assertEqual(eval_expression('(((1+((((2)))*3))))'), 7)
        self.assertEqual(eval_expression('1+(2*(3-(10/5)))'), 3)
        self.assertEqual(eval_expression('(2+3)*(2-3)'), -5)

    def test_variables(self):
        self.assertEqual(eval_expression('a', {'a': 7}), 7)
