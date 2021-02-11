import os
import unittest

from gas_file import GasFile


class TestGasParsing(unittest.TestCase):
    bits_dir = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
    assert os.path.isdir(bits_dir)

    def test_map_world_main_simple(self):
        # This is a very simple gas file
        map_world_main_file = os.path.join(self.bits_dir, 'world', 'maps', 'map_world', 'main.gas')
        gas_file = GasFile(map_world_main_file)
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('t:map,n:map', section.header)
        self.assertEqual(11, len(section.items))

    def test_map_expansion_main_datatypes(self):
        # This gas file has attributes with datatypes
        map_expansion_main_file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'main.gas')
        gas_file = GasFile(map_expansion_main_file)
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('t:map,n:map', section.header)
        self.assertEqual(12, len(section.items))
        dev_only = section.items[1]
        self.assertEqual('dev_only', dev_only.name)
        self.assertEqual('b', dev_only.datatype)
        self.assertEqual('false', dev_only.value)

    def test_expansion_lore_multiline_comments(self):
        # This file contains /* multiline comments */
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'lore.gas')
        gas_file = GasFile(file)
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('lore', section.header)
        self.assertEqual(38, len(section.items))

    def test_expansion_overheadmap_singlechar_attrnames(self):
        # This file contains single-character attribute names - not to be confused with datatypes
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'overheadmap.gas')
        gas_file = GasFile(file)
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

    def test_expansion_victory_missing_semicolon(self):
        # This file is missing a semicolon after an attribute
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'victory.gas')
        gas_file = GasFile(file)
        self.assertEqual(1, len(gas_file.gas.items))
        victory = gas_file.gas.items[0]
        self.assertEqual('victory', victory.header)
        self.assertEqual(2, len(victory.items))
        condition = victory.items[1]
        self.assertEqual('condition*', condition.header)
        self.assertEqual(4, len(condition.items))
        self.assertEqual('dsx_end_game', condition.items[0].value)  # semicolon should be cut
        self.assertEqual('"get staff of stars"', condition.items[1].value)  # missing semicolon, value should not be cut

    def test_multiplayer_quests_1line_multiattr(self):
        # This file contains a line that defines multiple attributes
        file = os.path.join(self.bits_dir, 'world', 'maps', 'multiplayer_world', 'quests', 'quests.gas')
        gas_file = GasFile(file)
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

    def test_expansion_quests_no_endquote_multiline_str(self):
        # This file contains an attr val that starts with a quote but ends with only a semicolon.
        # In Siege Editor, this is treated as a multi-line string that ends 5 lines further down; the rest of the last line is ignored.
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'quests', 'quests.gas')
        gas_file = GasFile(file)
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

    def test_expansion_lore_semicolon_in_quotes(self):
        # This file contains "a semicolon; inside a quoted string"
        file = os.path.join(self.bits_dir, 'world', 'maps', 'map_expansion', 'info', 'lore.gas')
        gas_file = GasFile(file)
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('lore', section.header)
        self.assertEqual(38, len(section.items))
        lore_2arhok = section.items[7]
        self.assertEqual('lore_2arhok', lore_2arhok.header)
        description = repr("Another part of your Mother's journal.\n\n'... The land is quite amazing. The flora here is like nothing in Arhok, which spends a great deal of time buried in the harsh winter snow. Here great plants and trees tower above us ...'\n\n '... The creatures attacked us on the beach, leaving poor K'thon lifeless on the sand. I tried to rescue him while he still lived; I dropped my shield and pack so I could drag him across the sand, but he was dead before I lost sight of the sea, and there was no way to return through the lizard armies to retrieve my equipment ...'\n\n'For now the shield will have to be a marker for K'thon's spirit; I will try to find it again when we return to Arhok ...'\n\n'Our Utraean friends have given a name to our foe: the Zaurask. These lizard beasts are fierce fighters and attack in well-organized packs. We have been told that they are led by a great king whose name is Nosirrom and that this beast has but one goal - to make the Utraeans' Fortress Emarard its home. It has ambition, I'll give it that, but we have taken up the cause of these strange wizard folk, and we will not let the Zaurask overwhelm them ...'")
        self.assertEqual(description, lore_2arhok.items[0].value)


if __name__ == '__main__':
    unittest.main()
