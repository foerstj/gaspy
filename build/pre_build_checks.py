import argparse
import sys

from bits.bits import Bits
from build.check_cam_flags import check_cam_flags
from build.check_conversations import check_conversations
from build.check_dupe_node_ids import check_dupe_node_ids
from build.check_empty_emitters import check_empty_emitters
from build.check_lore import check_lore
from build.check_moods import check_moods
from build.check_player_world_locations import check_player_world_locations
from build.check_quests import check_quests
from build.check_region_ids import check_region_ids
from build.check_tips import check_tips


def pre_build_checks(bits_path: str, map_name: str, checks: list[str]) -> bool:
    bits = Bits(bits_path)
    num_failed_checks = 0
    check_all = 'all' in checks
    check_standard = check_all or 'standard' in checks
    check_advanced = check_all or 'advanced' in checks
    if check_advanced or 'cam_flags' in checks:
        num_failed_checks += not check_cam_flags(bits, map_name)
    if check_standard or 'conversations' in checks:
        num_failed_checks += not check_conversations(bits, map_name)
    if check_standard or 'dupe_node_ids' in checks:
        num_failed_checks += not check_dupe_node_ids(bits, map_name)
    if check_standard or 'empty_emitters' in checks:
        num_failed_checks += not check_empty_emitters(bits, map_name)
    if check_standard or 'lore' in checks:
        num_failed_checks += not check_lore(bits, map_name)
    if check_standard or 'moods' in checks:
        num_failed_checks += not check_moods(bits, map_name)
    if check_standard or 'player_world_locations' in checks:
        num_failed_checks += not check_player_world_locations(bits, map_name)
    if check_standard or 'quests' in checks:
        num_failed_checks += not check_quests(bits, map_name)
    if check_standard or 'tips' in checks:
        num_failed_checks += not check_tips(bits, map_name)
    if check_standard or 'region_ids' in checks:
        num_failed_checks += not check_region_ids(bits, map_name)
    print(f'pre build checks: {num_failed_checks} checks failed')
    return num_failed_checks == 0


def init_arg_parser():
    checks = {
        'cam_flags',
        'conversations',
        'dupe_node_ids',
        'empty_emitters',
        'lore',
        'moods',
        'player_world_locations',
        'quests',
        'tips',
        'region_ids',
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
