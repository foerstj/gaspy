import argparse
import sys

from bits.bits import Bits
from build.check_cam_blocks import check_cam_blocks
from build.check_conversations import check_conversations
from build.check_dupe_node_ids import check_dupe_node_ids
from build.check_lore import check_lore
from build.check_moods import check_moods
from build.check_player_world_locations import check_player_world_locations
from build.check_quests import check_quests
from build.check_tips import check_tips


def pre_build_checks(bits_path: str, map_name: str, checks: list[str]) -> bool:
    bits = Bits(bits_path)
    valid = True
    check_all = 'all' in checks
    check_standard = check_all or 'standard' in checks
    check_advanced = check_all or 'advanced' in checks
    if check_advanced or 'cam_blocks' in checks:
        valid &= check_cam_blocks(bits, map_name)
    if check_standard or 'conversations' in checks:
        valid &= check_conversations(bits, map_name)
    if check_standard or 'dupe_node_ids' in checks:
        valid &= check_dupe_node_ids(bits, map_name)
    if check_standard or 'lore' in checks:
        valid &= check_lore(bits, map_name)
    if check_standard or 'moods' in checks:
        valid &= check_moods(bits, map_name)
    if check_standard or 'player_world_locations' in checks:
        valid &= check_player_world_locations(bits, map_name)
    if check_standard or 'quests' in checks:
        valid &= check_quests(bits, map_name)
    if check_standard or 'tips' in checks:
        valid &= check_tips(bits, map_name)
    return valid


def init_arg_parser():
    checks = {
        'cam_blocks',
        'conversations',
        'dupe_node_ids',
        'lore',
        'moods',
        'player_world_locations',
        'quests',
        'tips',
        'standard',
        'advanced',
        'all'
    }
    parser = argparse.ArgumentParser(description='GasPy pre_build_checks')
    parser.add_argument('map')
    parser.add_argument('--check', nargs='+', choices=checks)
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv: list[str]):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    valid = pre_build_checks(args.bits, args.map, args.check)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
