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
        self.assertIsNone(root.compute_value('physics', 'break_particulate', 'some_frag'))

        base = Template(Section('t:template,n:base_baddie', [
            Attribute('specializes', 'root'),
            Attribute('doc', 'Any mean kind of guy'),
            Section('aspect', [
                Section('textures', [
                    Attribute('0', 'b_i_baddie'),
                    Attribute('1', 'b_i_baddie_head'),
                ])
            ]),
            Section('common', [Attribute('screen_name', 'Baddie')]),
        ]))
        base.parent_template = root
        self.assertEqual('Any mean kind of guy', base.compute_value('doc'))
        self.assertEqual('Baddie', base.compute_value('common', 'screen_name'))
        self.assertEqual('b_i_baddie', base.compute_value('aspect', 'textures', '0'))
        self.assertEqual('b_i_baddie_head', base.compute_value('aspect', 'textures', '1'))

        leaf = Template(Section('t:template,n:baddie', [
            Attribute('specializes', 'base_baddie'),
            Section('aspect', [
                Section('textures', [Attribute('0', 'b_i_baddie_final')])
            ])
        ]))
        leaf.parent_template = base
        self.assertEqual('Any mean kind of guy', leaf.compute_value('doc'))
        self.assertEqual('Baddie', leaf.compute_value('common', 'screen_name'))
        self.assertEqual('b_i_baddie_final', leaf.compute_value('aspect', 'textures', '0'))
        self.assertIsNone(leaf.compute_value('aspect', 'textures', '1'))
