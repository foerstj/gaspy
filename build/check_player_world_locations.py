import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region
from gas.gas import Section


def check_player_world_locations_in_region(region: Region, pwl_names: list[str], fix_sp=False):
    num_invalid_pwl_names = 0
    num_single_player_pwls = 0
    special_objects = region.objects.do_load_objects_special() or list()
    for obj in special_objects:
        common = obj.section.get_section('common')
        if not common:
            continue
        instance_triggers_section: Section = common.get_section('instance_triggers')
        if not instance_triggers_section:
            continue
        instance_triggers = instance_triggers_section.get_sections('*')
        for trigger in instance_triggers:
            is_pwl = False
            pwl_action_attr = None
            action_attrs = trigger.get_attrs('action*')
            for attr in action_attrs:
                if attr.value.startswith('set_player_world_location'):
                    assert not is_pwl  # two PWL actions on one trigger?
                    is_pwl = True
                    pwl_action_attr = attr
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
                    if fix_sp:  # kinda makeshift rn
                        if len(action_attrs) > 1:
                            # other actions are present -> copy trigger instance
                            mp_pwl_trigger = trigger.copy()
                            trigger.items.remove(pwl_action_attr)
                            for aa in mp_pwl_trigger.get_attrs('action*'):
                                if not aa.value.startswith('set_player_world_location'):
                                    mp_pwl_trigger.items.remove(aa)
                            mp_pwl_trigger.set_attr_value('single_player', False)
                            instance_triggers_section.insert_item(mp_pwl_trigger)
                        else:
                            trigger.set_attr_value('single_player', False)
                            if len(instance_triggers) == 1:
                                common.set_attr_value('is_single_player', False)
    return num_invalid_pwl_names, num_single_player_pwls


def check_player_world_locations(bits: Bits, map_name: str, fix_sp=False):
    _map = bits.maps[map_name]
    _map.load_world_locations()
    pwl_names = list(_map.world_locations.locations.keys())
    num_invalid_pwl_names = 0
    num_single_player_pwls = 0
    print(f'Checking PWLs in {map_name}...')
    for region in _map.get_regions().values():
        region_invalid_pwl_names, region_single_player_pwls = check_player_world_locations_in_region(region, pwl_names, fix_sp)
        num_invalid_pwl_names += region_invalid_pwl_names
        num_single_player_pwls += region_single_player_pwls
        if region_single_player_pwls and fix_sp:
            region.save()
    print(f'Checking PWLs in {map_name}: {num_invalid_pwl_names} invalid PWL names, {num_single_player_pwls} single-player PWL triggers')
    return num_invalid_pwl_names == 0 and num_single_player_pwls == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_player_world_locations')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits = Bits(args.bits)
    valid = check_player_world_locations(bits, args.map)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
