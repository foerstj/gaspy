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
from build.check_rivers import check_rivers
from build.check_gizmo_placement import check_gizmo_placement
from build.check_tips import check_tips
from build.check_waters import check_waters


class PreBuildCheck:
    effort = 'standard'

    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        raise NotImplementedError()


class CheckCamFlags(PreBuildCheck):
    effort = 'advanced'

    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_cam_flags(bits, map_name, fix)


class CheckRivers(PreBuildCheck):
    effort = 'advanced'

    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_rivers(bits, map_name)


class CheckWaters(PreBuildCheck):
    effort = 'advanced'

    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_waters(bits, map_name)


class CheckConversations(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_conversations(bits, map_name)


class CheckDupeNodeIds(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_dupe_node_ids(bits, map_name)


class CheckEmptyEmitters(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_empty_emitters(bits, map_name)


class CheckGizmoPlacement(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_gizmo_placement(bits, map_name, fix)


class CheckLore(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_lore(bits, map_name)


class CheckMoods(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_moods(bits, map_name)


class CheckPlayerWorldLocations(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_player_world_locations(bits, map_name, fix)


class CheckQuests(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_quests(bits, map_name)


class CheckTips(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_tips(bits, map_name)


class CheckRegionIds(PreBuildCheck):
    def run_check(self, bits: Bits, map_name: str, fix: bool) -> bool:
        return check_region_ids(bits, map_name)


PRE_BUILD_CHECKS = {
    'cam_flags': CheckCamFlags(),
    'rivers': CheckRivers(),
    'waters': CheckWaters(),
    'conversations': CheckConversations(),
    'dupe_node_ids': CheckDupeNodeIds(),
    'empty_emitters': CheckEmptyEmitters(),
    'gizmo_placement': CheckGizmoPlacement(),
    'lore': CheckLore(),
    'moods': CheckMoods(),
    'player_world_locations': CheckPlayerWorldLocations(),
    'quests': CheckQuests(),
    'tips': CheckTips(),
    'region_ids': CheckRegionIds(),
}


def pre_build_checks(bits_path: str, map_name: str, checks: list[str], exclude: list[str], fix: bool) -> bool:
    if checks is None:
        checks = list()
    if exclude is None:
        exclude = list()

    bits = Bits(bits_path)
    num_failed_checks = 0
    check_all = 'all' in checks
    check_standard = check_all or 'standard' in checks
    check_advanced = check_all or 'advanced' in checks

    for check_name, check in PRE_BUILD_CHECKS.items():
        do_it = check_name in checks
        do_it = do_it or (check.effort == 'standard' and check_standard)
        do_it = do_it or (check.effort == 'advanced' and check_advanced)
        do_it = do_it and check_name not in exclude
        if do_it:
            num_failed_checks += not check.run_check(bits, map_name, fix)

    print(f'pre build checks: {num_failed_checks} checks failed')
    return num_failed_checks == 0


def init_arg_parser():
    checks = set(PRE_BUILD_CHECKS.keys()).union({
        'standard',
        'advanced',
        'all'
    })
    parser = argparse.ArgumentParser(description='GasPy pre_build_checks')
    parser.add_argument('map')
    parser.add_argument('--check', nargs='+', choices=checks)
    parser.add_argument('--exclude', nargs='+', choices=set(PRE_BUILD_CHECKS.keys()))
    parser.add_argument('--fix', action='store_true')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv: list[str]):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    valid = pre_build_checks(args.bits, args.map, args.check, args.exclude, args.fix)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
