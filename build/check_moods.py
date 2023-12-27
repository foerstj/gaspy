import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region


def check_moods_in_region(region: Region, mood_names: list[str]) -> set[str]:
    invalid_mood_names = set()
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
                        print(f'Invalid mood name in {region.get_name()} {obj.object_id}: {mood_name}')
                        invalid_mood_names.add(mood_name)
    return invalid_mood_names


def check_moods(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    mood_names = bits.moods.get_mood_names()
    invalid_mood_names = set()
    print(f'Checking moods in {map_name}...')
    for region in _map.get_regions().values():
        region_invalid_mood_names = check_moods_in_region(region, mood_names)
        invalid_mood_names.update(region_invalid_mood_names)
    print(f'Checking moods in {map_name}: {len(invalid_mood_names)} distinct invalid mood names')
    return len(invalid_mood_names) == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_moods')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    map_name = args.map
    bits_path = args.bits
    bits = Bits(bits_path)
    valid = check_moods(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
