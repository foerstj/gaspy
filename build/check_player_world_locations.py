import sys

from bits.bits import Bits
from bits.region import Region


def check_player_world_locations_in_region(region: Region, pwl_names: list[str]):
    num_invalid_pwl_names = 0
    num_single_player_pwls = 0
    special_objects = region.do_load_objects_special() or list()
    for obj in special_objects:
        common = obj.section.get_section('common')
        if not common:
            continue
        instance_triggers_section = common.get_section('instance_triggers')
        if not instance_triggers_section:
            continue
        instance_triggers = instance_triggers_section.get_sections('*')
        for trigger in instance_triggers:
            is_pwl = False
            action_attrs = trigger.get_attrs('action*')
            for attr in action_attrs:
                if attr.value.startswith('set_player_world_location'):
                    is_pwl = True
                    pwl_name = attr.value.split('"')[1].strip()
                    if pwl_name not in pwl_names:
                        print(f'Invalid PWL name in {region.get_name()}: {pwl_name}')
                        num_invalid_pwl_names += 1
            if is_pwl:
                is_trigger_instance_sp = trigger.get_attr_value('single_player')
                is_trigger_object_sp = obj.compute_value('common', 'is_single_player')
                is_sp = is_trigger_instance_sp is not False and is_trigger_object_sp is not False
                if is_sp:
                    print(f'Single-player PWL in {region.get_name()}: {obj.object_id}')
                    num_single_player_pwls += 1
    return num_invalid_pwl_names, num_single_player_pwls


def check_player_world_locations(bits: Bits, map_name: str):
    _map = bits.maps[map_name]
    _map.load_world_locations()
    pwl_names = list(_map.world_locations.locations.keys())
    num_invalid_pwl_names = 0
    num_single_player_pwls = 0
    for region in _map.get_regions().values():
        region_invalid_pwl_names, region_single_player_pwls = check_player_world_locations_in_region(region, pwl_names)
        num_invalid_pwl_names += region_invalid_pwl_names
        num_single_player_pwls += region_single_player_pwls
    return num_invalid_pwl_names == 0 and num_single_player_pwls == 0


def main(argv):
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    valid = check_player_world_locations(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
