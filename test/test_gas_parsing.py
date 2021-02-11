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


if __name__ == '__main__':
    unittest.main()
