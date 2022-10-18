import argparse
import math
import sys
import random

from autosize_plants import Sizing
from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from gas.molecules import Quaternion


directional_plants = ['roots', 'tree_swp_dead', 'log_jng_mossy', 'cliff', 'ivy', 'vine', 'leaning', 'tree_grs_sequoia_03', 'uproot', 'tree_jng_willow_01']


def contains(string: str, substrings: list[str]):
    for substring in substrings:
        if substring in string:
            return True
    return False


def brush_up_obj_scale(obj: GameObject, override: bool, sizing: Sizing) -> bool:
    if not override:
        if obj.get_own_value('aspect', 'scale_multiplier') is not None:
            return False
    new_scale_multiplier = sizing.random()
    template_scale_multiplier = obj.compute_value('aspect', 'scale_multiplier')
    if template_scale_multiplier is not None:
        new_scale_multiplier *= float(template_scale_multiplier)
    new_scale_multiplier = float(f'{new_scale_multiplier:.5f}')  # limit to 5 decimals to generate less diff on saving with SE
    obj.section.get_or_create_section('aspect').set_attr_value('scale_multiplier', new_scale_multiplier)
    return True


def is_square_orientation(orientation: Quaternion) -> bool:
    for turns in range(4):
        rad = turns*math.tau/4
        rad_ori = Quaternion.rad_to_quat(rad)
        if orientation.equals(rad_ori):
            # print('square orientation found!')
            return True
    return False


def brush_up_obj_orientation(obj: GameObject, override: bool) -> bool:
    if not override:
        obj_orientation = obj.get_own_value('placement', 'orientation')
        if obj_orientation is not None:
            obj_orientation = Quaternion.parse(obj_orientation)
            if not is_square_orientation(obj_orientation):
                return False
    new_orientation = random.uniform(0, math.tau)
    obj.section.get_section('placement').set_attr_value('orientation', Quaternion.rad_to_quat(new_orientation))
    return True


def brush_up_plant(plant: GameObject, override: bool, sizing: Sizing) -> bool:
    changed = False
    changed |= brush_up_obj_scale(plant, override, sizing)
    is_directional = contains(plant.template_name, directional_plants)
    if not is_directional:
        changed |= brush_up_obj_orientation(plant, override)
    return changed


def brush_up_region(r: Region, override: bool, sizing: Sizing):
    r.objects.load_objects()
    changed = 0
    for obj in r.objects.objects_non_interactive:
        assert isinstance(obj, GameObject)
        if obj.is_plant():
            changed += brush_up_plant(obj, override, sizing)
    print(f'{r.get_name()}: {changed} plants changed')
    if changed:
        r.save()


def brush_up(bits_path: str, map_name: str, region_name: str, override: bool, sizing_str: str):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    sizing = Sizing(sizing_str)
    if region_name is not None:
        r = m.get_region(region_name)
        brush_up_region(r, override, sizing)
    else:
        for r in m.get_regions().values():
            brush_up_region(r, override, sizing)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy brush-up')
    parser.add_argument('map')
    parser.add_argument('region', nargs='?')
    parser.add_argument('--override', action='store_true')
    parser.add_argument('--size', default='0.8-1.2', help="Fixed size, size range, or range with median")
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    brush_up(args.bits, args.map, args.region, args.override, args.size)


if __name__ == '__main__':
    main(sys.argv[1:])
