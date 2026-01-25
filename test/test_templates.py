import unittest

from bits.templates import Template
from gas.gas import Attribute, Hex, Section


class TestTemplates(unittest.TestCase):
    def test_compute_value(self):
        root = Template(Section('t:template,n:root', [
            Attribute('doc', 'This is my root template'),
            Section('aspect', [
                Section('textures', [Attribute('0', 'b_i_my_texture')]),
            ]),
            Section('common', [
                Attribute('screen_name', 'Root'),
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
                ]),
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
                Section('textures', [Attribute('0', 'b_i_baddie_final')]),
            ]),
        ]))
        leaf.parent_template = base
        self.assertEqual('Any mean kind of guy', leaf.compute_value('doc'))
        self.assertEqual('Baddie', leaf.compute_value('common', 'screen_name'))
        self.assertEqual('b_i_baddie_final', leaf.compute_value('aspect', 'textures', '0'))
        self.assertIsNone(leaf.compute_value('aspect', 'textures', '1'))

    def test_resolve_section(self):
        root = Template(Section('t:template,n:root', [
            Section('aspect', [
                Section('textures', [Attribute('0', 'b_i_my_texture')]),
            ]),
            Section('common', [
                Attribute('screen_name', 'Root'),
            ]),
        ]))
        textures_section = root.resolve_section('aspect', 'textures')
        self.assertIsNotNone(textures_section)
        self.assertEqual('b_i_my_texture', textures_section.get_attr_value('0'))
        self.assertIsNone(root.resolve_section('common', 'template_triggers'))
        self.assertIsNone(root.resolve_section('physics', 'break_particulate'))

        base = Template(Section('t:template,n:base_baddie', [
            Attribute('specializes', 'root'),
            Section('aspect', [
                Section('textures', [
                    Attribute('0', 'b_i_baddie'),
                    Attribute('1', 'b_i_baddie_head'),
                ]),
            ]),
            Section('common', [Attribute('screen_name', 'Baddie')]),
            Section('physics', [
                Section('break_particulate', [
                    Attribute('dummy_frag', 0),
                ]),
            ]),
        ]))
        base.parent_template = root
        textures_section = base.resolve_section('aspect', 'textures')
        self.assertIsNotNone(textures_section)
        self.assertEqual('b_i_baddie', textures_section.get_attr_value('0'))
        frags_section = base.resolve_section('physics', 'break_particulate')
        self.assertIsNotNone(frags_section)
        self.assertEqual('dummy_frag', frags_section.items[0].name)

        leaf = Template(Section('t:template,n:baddie', [
            Attribute('specializes', 'base_baddie'),
            Section('aspect'),
            Section('physics', [
                Section('break_particulate', [
                    Attribute('baddie_frag_01', 7),
                    Attribute('baddie_frag_02', 3),
                ]),
            ]),
        ]))
        leaf.parent_template = base
        textures_section = leaf.resolve_section('aspect', 'textures')
        self.assertIsNotNone(textures_section)
        self.assertEqual('b_i_baddie', textures_section.get_attr_value('0'))
        frags_section = leaf.resolve_section('physics', 'break_particulate')
        self.assertIsNotNone(frags_section)
        self.assertEqual('baddie_frag_01', frags_section.items[0].name)
