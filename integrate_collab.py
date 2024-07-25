import argparse
import os

import sys

from bits.bits import Bits
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

    parts_path = os.path.join(path, 'parts')
    assert os.path.isdir(parts_path)
    part_maps: list[Map] = list()
    for part in os.listdir(parts_path):
        part_path = os.path.join(parts_path, part)
        part_bits = Bits(part_path)
        for part_map_name, part_map in part_bits.maps.items():
            if not part_map_name.lower().startswith(name.lower()):
                continue
            part_map.print()
            part_maps.append(part_map)
    assert len(part_maps) > 0, 'No part maps found'

    # integrate hotpoints
    print('integrate hotpoints')
    w = GasWriter()
    hotpoints_gases = [pm.gas_dir.get_subdir('info').get_gas_file('hotpoints').get_gas() for pm in part_maps]
    hotpoints_strs = {'\n'.join(w.format_gas(hs)) for hs in hotpoints_gases}
    assert len(hotpoints_strs) == 1, 'Hotpoints not matching'
    info_dir = m.gas_dir.get_or_create_subdir('info')
    info_dir.get_or_create_gas_file('hotpoints').gas = hotpoints_gases[0]

    # integrate start positions
    print('integrate start positions')
    for pm in part_maps:
        pm.load_start_positions()
    start_positions = [pm.start_positions for pm in part_maps]
    m.start_positions = StartPositions(dict(), 'default')
    start_group_ids = set()
    for psp in start_positions:
        for group_name, group in psp.start_groups.items():
            assert group_name not in m.start_positions.start_groups
            assert group.id not in start_group_ids
            m.start_positions.start_groups[group_name] = group
            start_group_ids.add(group.id)
    assert m.start_positions.default in m.start_positions.start_groups

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

    # integrate quests
    print('integrate quests')
    for pm in part_maps:
        pm.load_quests()
    quests = [pm.quests for pm in part_maps]
    m.quests = QuestsGas(dict(), dict())
    for pqg in quests:
        for chapter_name, chapter in pqg.chapters.items():
            assert chapter_name not in m.quests.chapters
            m.quests.chapters[chapter_name] = chapter
        for quest_name, quest in pqg.quests.items():
            assert quest_name not in m.quests.quests
            m.quests.quests[quest_name] = quest

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

    print('integrate_collab done')
    m.save()
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
