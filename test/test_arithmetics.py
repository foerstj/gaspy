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

    def test_variables_general(self):
        self.assertEqual(eval_expression('a', {'a': 7}), 7)
        self.assertEqual(eval_expression('(a+1)*2', {'a': 7}), 16)
        self.assertAlmostEqual(eval_expression('a+b-c*d/e', {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}), 0.6)

    def test_variables_ds1(self):
        # spell_summon_braak_desert
        self.assertEqual(eval_expression('(#magic+1)*16-.7', {'#magic': 69}), 1119.3)  # mana_cost_modifier
        self.assertAlmostEqual(eval_expression('((((#magic*0.64)+10)*.56)-#str)', {'#magic': 69, '#str': 19}), 11.3296)  # alter_strength
        self.assertEqual(eval_expression('((((#magic*4.2)*.9)-194)*0.9)', {'#magic': 69}), 60.138)  # alter_cmagic_damage_min

    def test_variables_ds2(self):
        # ds2 style merc/vet/elite formula for monster_level
        self.assertEqual(eval_expression('(12.0 * #is_normal) + (51.0 * #is_veteran) + (78.0 * #is_elite)', {'#is_normal': 0, '#is_veteran': 1, '#is_elite': 0}), 51)  # boggrot_stats
