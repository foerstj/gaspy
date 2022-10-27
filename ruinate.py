import argparse
import sys
from argparse import Namespace

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region


def rem_objs(objs: list[GameObject], match) -> bool:
    objs_to_delete = list()
    for obj in objs:
        if match(obj):
            objs_to_delete.append(obj)
    for obj in objs_to_delete:
        objs.remove(obj)
    return len(objs_to_delete) > 0


def remove_signs(region: Region):
    changed = False
    changed |= rem_objs(region.objects.objects_interactive, lambda x: x.template_name in ['sign_glb_01'])
    changed |= rem_objs(region.objects.objects_non_interactive, lambda x: x.template_name in ['post_glb_01'])
    return changed


def ruin_region(region: Region, args: Namespace):
    region.objects.load_objects()
    changed = False
    if args.remove_signs:
        changed |= remove_signs(region)
    if changed:
        region.save()


def ruin(map_name: str, region_name: str, args: Namespace):
    bits = Bits()
    m = bits.maps[map_name]

    if region_name is not None:
        ruin_region(m.get_region(region_name), args)
    else:
        for region in m.get_regions().values():
            ruin_region(region, args)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Ruinate')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--remove-signs', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    ruin(args.map, args.region, args)


if __name__ == '__main__':
    main(sys.argv[1:])
