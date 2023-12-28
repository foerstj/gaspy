import argparse
import sys

from bits.bits import Bits
from build.check_quests import check_quests
from build.check_tips import check_tips


def pre_build_checks(bits_path: str, map_name: str, checks: list[str]) -> bool:
    bits = Bits(bits_path)
    valid = True
    if 'quests' in checks:
        valid &= check_quests(bits, map_name)
    if 'tips' in checks:
        valid &= check_tips(bits, map_name)
    return valid


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy pre_build_checks')
    parser.add_argument('map')
    parser.add_argument('--check', nargs='+', choices={'quests', 'tips'})
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
