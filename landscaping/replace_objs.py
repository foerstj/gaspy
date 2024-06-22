import argparse
import random
import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from gas.molecules import Position
from landscaping.node_mask import NodeMasks


def print_changes(name: str, changes: dict[str, int], print_all=False):
    changes_strs = [f'{c} {t}' for t, c in changes.items() if c or print_all]
    changes_str = ', '.join(changes_strs) if len(changes_strs) else 'none'
    print(f'{name} replacements: {changes_str}')


def occurs(chance: float) -> bool:
    assert 0 <= chance <= 1
    if chance == 1:
        return True
    if chance == 0:
        return False
    return random.uniform(0, 1) < chance


def replace_objs_in_region(region: Region, replacements: dict[str, str], node_masks: NodeMasks, chance: float = 1) -> dict[str, int]:
    region.objects.load_objects()
    changes = {t: 0 for t in replacements}
    for objs in region.objects.get_objects_dict().values():
        for obj in objs:
            assert isinstance(obj, GameObject)
            if node_masks.has_filters():
                pos: Position = obj.section.get_section('placement').get_attr_value('position')
                node = region.get_terrain().find_node(pos.node_guid)
                if not node_masks.is_included(node):
                    continue
            if obj.template_name in replacements and occurs(chance):
                t, n = obj.section.get_t_n_header()
                t = replacements[obj.template_name]
                obj.section.set_t_n_header(t, n)
                changes[obj.template_name] += 1
            for ctn_attr in obj.section.find_attrs_recursive('child_template_name'):
                child_template_name = ctn_attr.value.strip('"')
                if child_template_name in replacements and occurs(chance):
                    ctn_attr.set_value('"'+replacements[child_template_name]+'"')
                    changes[child_template_name] += 1
    if sum(changes.values()):
        region.save()
        print_changes(region.get_name(), changes)
    return changes


def combine_changes(changes: dict[str, int], new_changes: dict[str, int]):
    for t in new_changes:
        changes[t] += new_changes[t]


def parse_replacement_args(args: list[str]) -> dict[str, str]:
    d = dict()
    for arg in args:
        arg = arg.strip()
        if not arg or arg.startswith('#'):
            continue  # ignore empty lines & comment lines
        arg = arg.split('#')[0]  # ignore comments at line ends
        arg = arg.split('=')
        assert len(arg) == 2, arg
        d[arg[0].strip().lower()] = arg[1].strip().lower()
    return d


def replace_objs(bits_path: str, map_name: str, region_names: list[str], replacement_args: list[str], replacement_files: list[str], chance: float = 1, nodes: list[str] = None, exclude_nodes: list[str] = None):
    replacements = dict()
    for replacement_file in replacement_files:
        with open(replacement_file, 'r') as f:
            replacements.update(parse_replacement_args(f.readlines()))
    replacements.update(parse_replacement_args(replacement_args))  # direct cli args last to allow overriding file contents
    node_masks = NodeMasks(nodes, exclude_nodes)

    bits = Bits(bits_path)
    m = bits.maps[map_name]

    changes = {t: 0 for t in replacements}
    if len(region_names) > 0:
        for region_name in region_names:
            region_changes = replace_objs_in_region(m.get_region(region_name), replacements, node_masks, chance)
            combine_changes(changes, region_changes)
    else:
        for region in m.get_regions().values():
            region_changes = replace_objs_in_region(region, replacements, node_masks, chance)
            combine_changes(changes, region_changes)
    print_changes(m.get_name(), changes)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Replace Objs')
    parser.add_argument('map')
    parser.add_argument('region', nargs='*')
    parser.add_argument('--replace', nargs='+', help='--replace wolf_gray=wolf_gray_zombie wolf_white=wolf_white_zombie')
    parser.add_argument('--replace-from-file', nargs='+', help='--replace-from-file input/my-replacements.txt')
    parser.add_argument('--nodes', nargs='*', default=[])
    parser.add_argument('--exclude-nodes', nargs='*', default=[])
    parser.add_argument('--chance', type=float, default=1)
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    replace_objs(args.bits, args.map, args.region, args.replace or list(), args.replace_from_file or list(), args.chance, args.nodes, args.exclude_nodes)


if __name__ == '__main__':
    main(sys.argv[1:])
