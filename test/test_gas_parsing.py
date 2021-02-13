import os
import unittest

from gas_file import GasFile
from gas_parser import GasParser


class TestGasParsing(unittest.TestCase):
    bits_dir = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
    assert os.path.isdir(bits_dir)

    def test_map_world_main_simple(self):
        # This is a very simple gas file
        map_world_main_file = os.path.join(self.bits_dir, 'world', 'maps', 'map_world', 'main.gas')
        gas_file = GasFile(map_world_main_file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('t:map,n:map', section.header)
        self.assertEqual(11, len(section.items))
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_map_expansion_main_datatypes(self):
        # This gas file has attributes with datatypes
        map_expansion_main_file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'main.gas')
        gas_file = GasFile(map_expansion_main_file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('t:map,n:map', section.header)
        self.assertEqual(12, len(section.items))
        dev_only = section.items[1]
        self.assertEqual('dev_only', dev_only.name)
        self.assertEqual('b', dev_only.datatype)
        self.assertEqual('false', dev_only.value)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_expansion_lore_multiline_comments(self):
        # This file contains /* multiline comments */
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'lore.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('lore', section.header)
        self.assertEqual(38, len(section.items))
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_expansion_overheadmap_singlechar_attrnames(self):
        # This file contains single-character attribute names - not to be confused with datatypes
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'overheadmap.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        overheadmap = gas_file.gas.items[0]
        self.assertEqual('overheadmap', overheadmap.header)
        self.assertEqual(3, len(overheadmap.items))
        pieces = overheadmap.items[1]
        self.assertEqual('pieces', pieces.header)
        self.assertEqual(24, len(pieces.items))
        arhok = pieces.items[0]
        self.assertEqual('arhok', arhok.header)
        self.assertEqual(4, len(arhok.items))
        x = arhok.items[2]
        self.assertEqual('x', x.name)
        self.assertIsNone(x.datatype)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_expansion_victory_missing_semicolon(self):
        # This file is missing a semicolon after an attribute
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'victory.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        victory = gas_file.gas.items[0]
        self.assertEqual('victory', victory.header)
        self.assertEqual(2, len(victory.items))
        condition = victory.items[1]
        self.assertEqual('condition*', condition.header)
        self.assertEqual(4, len(condition.items))
        self.assertEqual('dsx_end_game', condition.items[0].value)  # semicolon should be cut
        self.assertEqual('"get staff of stars"', condition.items[1].value)  # missing semicolon, value should not be cut
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_multiplayer_quests_1line_multiattr(self):
        # This file contains a line that defines multiple attributes
        file = os.path.join(self.bits_dir, 'world', 'maps', 'multiplayer_world', 'quests', 'quests.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        quests = gas_file.gas.items[0]
        self.assertEqual('quests', quests.header)
        self.assertEqual(27, len(quests.items))
        quest_flooded_sanctuary = quests.items[-1]
        self.assertEqual('quest_flooded_sanctuary', quest_flooded_sanctuary.header)
        self.assertEqual(4, len(quest_flooded_sanctuary.items))
        sub = quest_flooded_sanctuary.items[-1]
        self.assertEqual('*', sub.header)
        self.assertEqual(4, len(sub.items))
        self.assertEqual('description', sub.items[2].name)
        self.assertEqual('"Aid the Sanctuary Keeper by clearing the Flooded Sanctuary of creatures."', sub.items[2].value)
        self.assertEqual('address', sub.items[3].name)
        self.assertEqual('of_r1:conversations:conversation_keeper', sub.items[3].value)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_expansion_quests_no_endquote_multiline_str(self):
        # This file contains an attr val that starts with a quote but ends with only a semicolon.
        # In Siege Editor, this is treated as a multi-line string that ends 5 lines further down; the rest of the last line is ignored.
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'quests', 'quests.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(2, len(gas_file.gas.items))
        chapters = gas_file.gas.items[0]
        self.assertEqual('chapters', chapters.header)
        self.assertEqual(5, len(chapters.items))
        dsx_chapter_3 = chapters.items[2]
        self.assertEqual('dsx_chapter_3', dsx_chapter_3.header)
        self.assertEqual(3, len(dsx_chapter_3.items))
        sub = dsx_chapter_3.items[2]
        self.assertEqual('*', sub.header)
        self.assertEqual(2, len(sub.items))
        self.assertEqual('description', sub.items[0].name)
        messy_description = '"The Shadowjumper\'s trail leads the hero through the ancient sources of the Utraean power. The strongholds of legendary mages Jerkhal and Demlock expose new threats, old clues, and everpresent danger.;\n		  i order = 0;\n		}\n		[*]\n		{\n			description = "'
        self.assertEqual(messy_description, sub.items[0].value)
        self.assertEqual('order', sub.items[1].name)
        self.assertEqual('1', sub.items[1].value)
        self.assertEqual('i', sub.items[1].datatype)
        self.assertEqual(1, len(GasParser.get_instance().clear_warnings()))

    def test_expansion_lore_semicolon_in_quotes(self):
        # This file contains "a semicolon; inside a quoted string"
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'lore.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('lore', section.header)
        self.assertEqual(38, len(section.items))
        lore_2arhok = section.items[7]
        self.assertEqual('lore_2arhok', lore_2arhok.header)
        description = repr("Another part of your Mother's journal.\n\n'... The land is quite amazing. The flora here is like nothing in Arhok, which spends a great deal of time buried in the harsh winter snow. Here great plants and trees tower above us ...'\n\n '... The creatures attacked us on the beach, leaving poor K'thon lifeless on the sand. I tried to rescue him while he still lived; I dropped my shield and pack so I could drag him across the sand, but he was dead before I lost sight of the sea, and there was no way to return through the lizard armies to retrieve my equipment ...'\n\n'For now the shield will have to be a marker for K'thon's spirit; I will try to find it again when we return to Arhok ...'\n\n'Our Utraean friends have given a name to our foe: the Zaurask. These lizard beasts are fierce fighters and attack in well-organized packs. We have been told that they are led by a great king whose name is Nosirrom and that this beast has but one goal - to make the Utraeans' Fortress Emarard its home. It has ambition, I'll give it that, but we have taken up the cause of these strange wizard folk, and we will not let the Zaurask overwhelm them ...'")
        self.assertEqual(description, lore_2arhok.items[0].value)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_exp_a9r1mesa_conv_1line_braceattr(self):
        # In this file, an opening brace and an attribute are on the same line
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'regions', 'a9_r1_mesa', 'conversations', 'conversations.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(3, len(gas_file.gas.items))
        therg_hello = gas_file.gas.items[0]
        self.assertEqual('therg_hello', therg_hello.header)
        self.assertEqual(4, len(therg_hello.items))
        sub3 = therg_hello.items[2]
        self.assertEqual('text*', sub3.header)
        self.assertEqual(6, len(sub3.items))
        self.assertEqual('i', sub3.items[0].datatype)
        self.assertEqual('order', sub3.items[0].name)
        self.assertEqual('2', sub3.items[0].value)
        self.assertEqual('sample', sub3.items[1].name)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_koe_acr1_spells_1line_headerbrace(self):
        # In this file, a section header and its opening brace are on the same line
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_world', 'regions', 'ac_r1', 'spells', 'spells.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('n:ac_r1_spells', section.header)
        self.assertEqual(0, len(section.items))
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_koe_dfbandits_nonint_material_garbage(self):
        # This file contains some serious garbage in the value of a completely unimportant attribute. Should not crash.
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_world', 'regions', 'df_bandits', 'objects', 'non_interactive.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(2276, len(gas_file.gas.items))
        broken_foliage = list(filter(lambda x: x.items[0].header == 'aspect' and x.items[0].items[0].name == 'material', gas_file.gas.items))
        self.assertEqual(1, len(broken_foliage))
        broken_foliage = broken_foliage[0]
        self.assertEqual(2, len(broken_foliage.items))
        self.assertEqual(1, len(broken_foliage.items[0].items))
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_logic_components_1line_section(self):
        # This file contains whole sections on a single line
        file = os.path.join(self.bits_dir, 'world', 'contentdb', 'components', 'components.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(23, len(gas_file.gas.items))
        actor = gas_file.gas.items[0]
        self.assertEqual('t:component,n:actor', actor.header)
        self.assertEqual(24, len(actor.items))
        can_level_up = actor.items[6]
        self.assertEqual('can_level_up', can_level_up.header)
        self.assertEqual(3, len(can_level_up.items))
        self.assertEqual('type', can_level_up.items[0].name)
        self.assertEqual('bool', can_level_up.items[0].value)
        self.assertEqual('default', can_level_up.items[1].name)
        self.assertEqual('false', can_level_up.items[1].value)
        self.assertEqual('doc', can_level_up.items[2].name)
        self.assertEqual('"Can this object \'level up\'?"', can_level_up.items[2].value)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_logic_components_multiline_skrit(self):
        # This file contains inline skrit as an attribute value
        file = os.path.join(self.bits_dir, 'world', 'contentdb', 'components', 'components.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(23, len(gas_file.gas.items))
        physics = gas_file.gas.items[19]
        self.assertEqual('t:component,n:physics', physics.header)
        self.assertEqual(37, len(physics.items))
        physics_effect = physics.items[-1]
        self.assertEqual('t:constraint,n:physics_effect', physics_effect.header)
        self.assertEqual(1, len(physics_effect.items))
        self.assertEqual('skrit', physics_effect.items[0].name)
        skrit = physics_effect.items[0].value.strip()
        self.assertTrue(skrit.startswith('[['))
        self.assertTrue(skrit.endswith(']]'))
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_loa_a3r3aaglet_multiline_skritqueryparams(self):
        # This file contains multi-line values that are skrit file names followed by URL-like query params
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'regions', 'a3_r3a_aglet', 'objects', 'regular', 'actor.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(82, len(gas_file.gas.items))
        automaton = gas_file.gas.items[23]
        self.assertEqual('t:dsx_automaton_weathered,n:0x24a00405', automaton.header)
        self.assertEqual(3, len(automaton.items))
        mind = automaton.items[1]
        self.assertEqual('mind', mind.header)
        self.assertEqual(11, len(mind.items))
        jat_brain = mind.items[3]
        self.assertEqual('jat_brain', jat_brain.name)
        self.assertEqual('world\\ai\\jobs\\common\\brain_hero.skrit\n			?actor_joins_existing_party=false\n			&actor_creates_own_party=false', jat_brain.value)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_logic_lavabeast_rogueattr(self):
        # This file contains a rogue attribute between a section header and its opening brace
        file = os.path.join(self.bits_dir, 'world', 'contentdb', 'templates', 'regular', 'actors', 'evil', 'd', 'rock_beast.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(6, len(gas_file.gas.items))
        lava_beast = gas_file.gas.items[4]
        self.assertEqual('t:template,n:lava_beast', lava_beast.header)
        self.assertEqual(10, len(lava_beast.items))
        physics = lava_beast.items[8]
        self.assertEqual('physics', physics.header)
        self.assertEqual(1, len(physics.items))
        self.assertEqual(1, len(GasParser.get_instance().clear_warnings()))

    def test_logic_chargeups_skrit(self):
        # This file contains multiline inline skrit that starts on the same line
        file = os.path.join(self.bits_dir, 'world', 'global', 'effects', 'chargeups.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(42, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('effect_script*', section.header)
        self.assertEqual(2, len(section.items))
        self.assertEqual('script', section.items[1].name)
        self.assertTrue(section.items[1].value.startswith('[['))
        self.assertTrue(section.items[1].value.endswith(']]'))
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_logic_console_multiline_string(self):
        # This file contains multiline string values that do not start on the same line
        file = os.path.join(self.bits_dir, 'config', 'console.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        console = gas_file.gas.items[0]
        self.assertEqual('console', console.header)
        self.assertEqual(1, len(console.items))
        exec = console.items[0]
        self.assertEqual('exec', exec.header)
        self.assertEqual(6, len(exec.items))
        e3 = exec.items[3]
        self.assertEqual('e3', e3.header)
        self.assertEqual(8, len(e3.items))
        hero_cr = e3.items[0]
        self.assertEqual('hero_cr', hero_cr.header)
        self.assertEqual(2, len(hero_cr.items))
        command = hero_cr.items[0]
        self.assertEqual('command', command.name)
        self.assertEqual(242, len(command.value))
        self.assertTrue(command.value.startswith('"'))
        self.assertTrue(command.value.endswith('"'))
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_logic_loadsave_1linesquarebrace_semicolon(self):
        # This file contains single-line [[squarebrace delimited text;]] that contains a semicolon
        file = os.path.join(self.bits_dir, 'ui', 'interfaces', 'backend', 'loadsave_game', 'loadsave_game.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        loadsave_game = gas_file.gas.items[0]
        self.assertEqual('loadsave_game', loadsave_game.header)
        self.assertEqual(18, len(loadsave_game.items))
        edit_box = loadsave_game.items[10]
        self.assertEqual('t:edit_box,n:loadsave_game_name_edit_box', edit_box.header)
        self.assertEqual(20, len(edit_box.items))
        excluded_chars = edit_box.items[14]
        self.assertEqual('excluded_chars', excluded_chars.name)
        self.assertEqual(r'[["<>:/\|?*.%;]]', excluded_chars.value)
        self.assertEqual(0, len(GasParser.get_instance().clear_warnings()))

    def test_siegeeditorextras_effectschema_escaped_quotes(self):
        # This file contains "text with \"escaped\" quotes" (which aren't a thing) and missing end quotes and is a complete mess.
        # Just documenting current parser behavior. Parser behaves the same way as SE, which uses the file.
        file = os.path.join(self.bits_dir, 'config', 'editor', 'effect_schema.gas')
        gas_file = GasFile(file)
        gas_file.load()
        self.assertEqual(1, len(gas_file.gas.items))
        effect_schema = gas_file.gas.items[0]
        self.assertEqual('effect_schema', effect_schema.header)
        self.assertEqual(3, len(effect_schema.items))
        effect_parameters = effect_schema.items[2]
        self.assertEqual('effect_parameters', effect_parameters.header)
        self.assertEqual(6, len(effect_parameters.items))  # supposed to be: 23
        splat = effect_parameters.find_sections_recursive('splat')
        self.assertEqual(1, len(splat))
        splat = splat[0]
        self.assertEqual(1, len(splat.items))
        self.assertEqual('doc', splat.items[0].name)
        self.assertEqual(r'"Causes particles to \"', splat.items[0].value)  # supposed to be: "Causes particles to \"splat\" onto terrain polygon"
        self.assertEqual(5, len(GasParser.get_instance().clear_warnings()))


if __name__ == '__main__':
    unittest.main()
