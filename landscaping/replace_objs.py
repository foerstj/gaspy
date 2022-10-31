import argparse
import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region


def print_changes(name: str, changes: dict[str, int], print_all=False):
    changes_strs = [f'{c} {t}' for t, c in changes.items() if c or print_all]
    changes_str = ', '.join(changes_strs) if len(changes_strs) else 'none'
    print(f'{name} replacements: {changes_str}')


def replace_objs_in_region(region: Region, replacements: dict[str, str]) -> dict[str, int]:
    region.objects.load_objects()
    changes = {t: 0 for t in replacements}
    for objs in [region.objects.objects_actor, region.objects.objects_interactive, region.objects.objects_non_interactive]:
        for obj in objs:
            assert isinstance(obj, GameObject)
            if obj.template_name in replacements:
                t, n = obj.section.get_t_n_header()
                t = replacements[obj.template_name]
                obj.section.set_t_n_header(t, n)
                changes[obj.template_name] += 1
    if sum(changes.values()):
        region.save()
        print_changes(region.get_name(), changes)
    return changes


def combine_changes(changes: dict[str, int], new_changes: dict[str, int]):
    for t in new_changes:
        changes[t] += new_changes[t]


def replace_objs(bits_path: str, map_name: str, region_names: list[str], replacements: dict[str, str]):
    bits = Bits(bits_path)
    m = bits.maps[map_name]

    changes = {t: 0 for t in replacements}
    if len(region_names) > 0:
        for region_name in region_names:
            region_changes = replace_objs_in_region(m.get_region(region_name), replacements)
            combine_changes(changes, region_changes)
    else:
        for region in m.get_regions().values():
            region_changes = replace_objs_in_region(region, replacements)
            combine_changes(changes, region_changes)
    print_changes(m.get_name(), changes)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Replace Objs')
    parser.add_argument('map')
    parser.add_argument('region', nargs='*')
    parser.add_argument('--replace', nargs='+', required=True, help='--replace wolf_gray=wolf_gray_zombie wolf_white=wolf_white_zombie')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def parse_replacements(args: list[str]) -> dict[str, str]:
    d = dict()
    for arg in args:
        arg = arg.split('=')
        assert len(arg) == 2
        d[arg[0].strip().lower()] = arg[1].strip().lower()
    return d


def main(argv):
    args = parse_args(argv)
    replace_objs(args.bits, args.map, args.region, parse_replacements(args.replace))


if __name__ == '__main__':
    main(sys.argv[1:])
