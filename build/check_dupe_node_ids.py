import sys

from bits.bits import Bits
from bits.maps.region import Region
from region_import.check_dupe_node_ids import check_map, dupes_in_list


def check_moods_in_region(region: Region, mood_names: list[str]) -> int:
    num_invalid_mood_names = 0
    special_objects = region.objects.do_load_objects_special() or list()
    for obj in special_objects:
        common = obj.section.get_section('common')
        if not common:
            continue
        instance_triggers_section = common.get_section('instance_triggers')
        if not instance_triggers_section:
            continue
        instance_triggers = instance_triggers_section.get_sections('*')
        for trigger in instance_triggers:
            action_attrs = trigger.get_attrs('action*')
            for attr in action_attrs:
                if attr.value.startswith('mood_change'):
                    mood_name = attr.value.split('"')[1].strip()
                    if mood_name not in mood_names:
                        print(f'Invalid mood name in {region.get_name()}: {mood_name}')
                        num_invalid_mood_names += 1
    return num_invalid_mood_names


def check_dupe_node_ids(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    print(f'Checking dupe node ids in {map_name}...')
    num_dupes = check_map(_map, False)
    print(f'Checking dupe node ids in {map_name}: {num_dupes} duplicate node ids')
    return num_dupes == 0


def main(argv) -> int:
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    valid = check_dupe_node_ids(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
