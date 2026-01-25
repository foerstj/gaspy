import unittest

from bits.templates import Template
from gas.gas import Attribute, Hex, Section


class TestTemplates(unittest.TestCase):
    def test_compute_value(self):
        root = Template(Section('t:template,n:root', [
            Attribute('doc', 'This is my root template'),
            Section('aspect', [
                Section('textures', [Attribute('0', 'b_i_my_texture')])
            ]),
            Section('common', [
                Attribute('screen_name', 'Root')
            ]),
        ]))
        self.assertEqual('This is my root template', root.compute_value('doc'))
        self.assertEqual('Root', root.compute_value('common', 'screen_name'))
        self.assertEqual('b_i_my_texture', root.compute_value('aspect', 'textures', '0'))
        self.assertIsNone(root.compute_value('arglbargl'))
        self.assertIsNone(root.compute_value('common', 'auto_expiration_class'))
        self.assertIsNone(root.compute_value('aspect', 'textures', '1'))
