import sys

from bits.bits import Bits
from bits.region import Region


def check_player_world_locations_in_region(region: Region, pwl_names: list[str]):
    special_objects = region.do_load_objects_special()
    num_invalid_pwl_names = 0
    for obj in special_objects:
        common = obj.section.get_section('common')
        if not common:
            continue
        instance_triggers = common.get_section('instance_triggers')
        if not instance_triggers:
            continue
        for trigger in instance_triggers.get_sections('*'):
            for attr in trigger.get_attrs('action*'):
                if attr.value.startswith('set_player_world_location'):
                    pwl_name = attr.value.split('"')[1].strip()
                    if pwl_name not in pwl_names:
                        print(f'Invalid PWL name in {region.get_name()}: {pwl_name}')
                        num_invalid_pwl_names += 1
    return num_invalid_pwl_names


def check_player_world_locations(bits: Bits, map_name: str):
    _map = bits.maps[map_name]
    _map.load_world_locations()
    pwl_names = list(_map.world_locations.locations.keys())
    num_invalid_pwl_names = 0
    for region in _map.get_regions().values():
        num_invalid_pwl_names += check_player_world_locations_in_region(region, pwl_names)
    return num_invalid_pwl_names == 0


def main(argv):
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    valid = check_player_world_locations(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
