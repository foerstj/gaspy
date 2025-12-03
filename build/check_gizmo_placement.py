import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region
from gas.molecules import Quaternion, Position


def check_gizmo_placement_in_region(region: Region, fix=False):
    num_misaligned = 0

    objs_special = region.objects.do_load_objects_special()
    if objs_special is not None:
        shrines = [obj for obj in objs_special if obj.template_name in ['mana_shrine', 'life_shrine']]
        for shrine in shrines:
            problems = []
            pos: Position = shrine.get_own_value('placement', 'position')
            ori: Quaternion = shrine.get_own_value('placement', 'orientation')
            if ori is not None:
                problems.append('misoriented')  # shrine gizmos should be default-oriented
                if fix:
                    placement = shrine.section.get_section('placement')
                    attr = placement.get_attr('orientation')
                    placement.items.remove(attr)
            correct_y = 0 if shrine.template_name == 'mana_shrine' else -0.5
            if pos.x != 0 or pos.y != correct_y or pos.z != 0:
                problems.append('misplaced')
                if fix:
                    placement = shrine.section.get_section('placement')
                    attr = placement.get_attr('position')
                    attr.value = Position(0, correct_y, 0, pos.node_guid)
            if len(problems) > 0:
                print(f'  {shrine.template_name} in region {region.get_name()}: ' + ', '.join(problems))
                num_misaligned += 1

    objs_elevator = region.objects.do_load_objects_elevator()
    teleporters = [obj for obj in objs_elevator if obj.template_name == 'elevator_instant_4s_1c']
    for teleporter in teleporters:
        problems = []
        pos: Position = teleporter.get_own_value('placement', 'position')
        ori: Quaternion = teleporter.get_own_value('placement', 'orientation')
        if ori is not None:
            problems.append('misoriented')  # teleporter gizmos should be default-oriented
            if fix:
                placement = teleporter.section.get_section('placement')
                attr = placement.get_attr('orientation')
                placement.items.remove(attr)
        node_guid = pos.node_guid
        node = region.get_terrain().find_node(node_guid)
        node_mesh = node.mesh_name
        correct_y = 9 if node_mesh == 't_xxx_wal_displacer_pad' else 5
        if pos.x != 0 or pos.y != correct_y or pos.z != 0:
            problems.append('misplaced')
            if fix:
                placement = teleporter.section.get_section('placement')
                attr = placement.get_attr('position')
                attr.value = Position(0, correct_y, 0, pos.node_guid)
        if len(problems) > 0:
            print(f'  {teleporter.template_name} in region {region.get_name()}: ' + ', '.join(problems))
            num_misaligned += 1

    return num_misaligned


def check_gizmo_placement(bits: Bits, map_name: str, fix=False):
    m = bits.maps[map_name]
    num_misaligned = 0
    print(f'Checking gizmo placements in {map_name}...')
    for region in m.get_regions().values():
        region_num_misaligned = check_gizmo_placement_in_region(region, fix)
        if region_num_misaligned and fix:
            region.save()
        num_misaligned += region_num_misaligned
    print(f'Checking gizmo placements in {map_name}: {num_misaligned} misaligned gizmos')
    return num_misaligned == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_gizmo_placement')
    parser.add_argument('map')
    parser.add_argument('--fix', action='store_true')
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
    valid = check_gizmo_placement(bits, map_name, args.fix)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
