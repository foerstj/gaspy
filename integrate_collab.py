import argparse
import os

import sys

from bits.bits import Bits
from bits.maps.bookmarks_gas import BookmarksGas
from bits.maps.lore_gas import LoreGas
from bits.maps.map import Map
from bits.maps.quests_gas import QuestsGas
from bits.maps.start_positions import StartPositions
from bits.maps.world_locations import WorldLocations
from gas.gas_writer import GasWriter


def integrate_collab(path: str, name: str):
    print('integrate_collab start')
    bits = Bits(path)
    m = bits.maps[name]
    m.print()

    part_maps: list[Map] = list()
    parts_path = os.path.join(path, 'parts')
    assert os.path.isdir(parts_path)
    for part in os.listdir(parts_path):
        part_path = os.path.join(parts_path, part)
        part_bits = Bits(part_path)
        for part_map_name, part_map in part_bits.maps.items():
            part_map.print()
            part_maps.append(part_map)
    for part_map_name, part_map in bits.maps.items():
        if part_map_name == name:
            continue
        part_map.print()
        part_maps.append(part_map)
    assert len(part_maps) > 0, 'No part maps found'

    w = GasWriter()  # for checking gas equality

    # integrate hotpoints
    print('integrate hotpoints')
    hotpoints_gases = [pm.gas_dir.get_subdir('info').get_gas_file('hotpoints').get_gas() for pm in part_maps]
    hotpoints_strs = {w.format_gas_str(hs) for hs in hotpoints_gases}
    assert len(hotpoints_strs) == 1, 'Hotpoints not matching'
    info_dir = m.gas_dir.get_or_create_subdir('info')
    info_dir.get_or_create_gas_file('hotpoints').gas = hotpoints_gases[0]
    m.save()

    # integrate start positions
    print('integrate start positions')
    for pm in part_maps:
        pm.load_start_positions()
    start_positions = [pm.start_positions for pm in part_maps]
    m.start_positions = StartPositions(dict(), 'default')
    start_group_ids = set()
    for psp in start_positions:
        for group_name, group in psp.start_groups.items():
            if group_name.endswith('_pre') or group_name.endswith('_post'):
                continue
            assert group_name not in m.start_positions.start_groups, group_name
            assert group.id not in start_group_ids, group.id
            m.start_positions.start_groups[group_name] = group
            start_group_ids.add(group.id)
    assert m.start_positions.default in m.start_positions.start_groups
    m.save()

    # integrate world locations
    print('integrate world locations')
    for pm in part_maps:
        pm.load_world_locations()
    world_locations = [pm.world_locations for pm in part_maps]
    m.world_locations = WorldLocations(dict())
    location_ids = set()
    for pwl in world_locations:
        for location_name, location in pwl.locations.items():
            assert location_name not in m.world_locations.locations
            assert location.id not in location_ids
            m.world_locations.locations[location_name] = location
            location_ids.add(location.id)
    m.save()

    # integrate lore
    print('integrate lore')
    for pm in part_maps:
        pm.load_lore()
    lores = [pm.lore for pm in part_maps]
    m.lore = LoreGas(dict())
    for lore in lores:
        for lore_key, lore_text in lore.lore.items():
            assert lore_key not in m.lore.lore, lore_key
            m.lore.lore[lore_key] = lore_text
    m.save()

    # integrate bookmarks
    print('integrate bookmarks')
    for pm in part_maps:
        pm.load_bookmarks()
    bookmarkses = [pm.bookmarks for pm in part_maps]
    m.bookmarks = BookmarksGas(dict())
    for bookmarks in bookmarkses:
        for bookmark_key, bookmark in bookmarks.bookmarks.items():
            assert bookmark_key not in m.bookmarks.bookmarks, bookmark_key
            m.bookmarks.bookmarks[bookmark_key] = bookmark
    m.save()

    # integrate quests
    print('integrate quests')
    for pm in part_maps:
        pm.load_quests()
    quests = [pm.quests for pm in part_maps]
    m.quests = QuestsGas(dict(), dict())
    for pqg in quests:
        for chapter_name, chapter in pqg.chapters.items():
            if chapter_name in m.quests.chapters:
                assert w.format_section_str(chapter.to_gas(chapter_name)) == w.format_section_str(m.quests.chapters[chapter_name].to_gas(chapter_name)), chapter_name
            m.quests.chapters[chapter_name] = chapter
        for quest_name, quest in pqg.quests.items():
            if quest_name in m.quests.quests:
                assert w.format_section_str(quest.to_gas(quest_name)) == w.format_section_str(m.quests.quests[quest_name].to_gas(quest_name)), quest_name
            m.quests.quests[quest_name] = quest
    m.save()

    # mend stitches
    print('mend stitches')
    for region_name, region in m.get_regions().items():
        change_in_region = False
        for stitch_group in region.get_stitch_helper().stitch_editors:
            if stitch_group.dest_region not in m.get_regions():
                first_stitch_id = list(stitch_group.node_ids.keys())[0]
                for region_name_2, region_2 in m.get_regions().items():
                    if region_name_2 == region_name:
                        continue
                    for stitch_group_2 in region_2.get_stitch_helper().stitch_editors:
                        if first_stitch_id in stitch_group_2.node_ids:
                            stitch_group.dest_region = region_name_2
                            # print(f'  {region_name} {first_stitch_id} -> {region_name_2}')
                            change_in_region = True
        if change_in_region:
            region.save()
    m.save()

    print('integrate_collab done')
    print('don\'t forget to build the stitch index')


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description='GasPy integrate collab')
    parser.add_argument('path')
    parser.add_argument('name')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    integrate_collab(args.path, args.name)


if __name__ == '__main__':
    main(sys.argv[1:])
