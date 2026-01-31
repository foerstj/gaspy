import argparse
import os
import sys
import re

from pathlib import Path

from landscaping.replace_objs import parse_replacement_args


# Primitive helper functions for gas files that treat them as mere text, not trying to parse anything.


def replace_strs_in_file(file_path, replacements: dict[str, str], word=False) -> bool:
    with open(file_path) as map_gas_file:
        text = map_gas_file.read()
    text_pre = text
    for old_str, new_str in replacements.items():
        if word:
            if old_str in text:
                text = re.sub(r"\b%s\b" % old_str, new_str, text)
        else:
            text = text.replace(old_str, new_str)
    if text != text_pre:
        with open(file_path, 'w') as map_gas_file:
            map_gas_file.write(text)
    return text != text_pre


def replace_strs_in_dir(dir_path, replacements: dict[str, str], word=False, rglob_pattern='*.gas', print_path: bool = None):
    path_list = Path(dir_path).rglob(rglob_pattern)
    for path in path_list:
        changed = replace_strs_in_file(path, replacements, word)
        if print_path:
            print(path)
        elif print_path is None and changed:
            print(path)


def replace_strs(path: str, replacement_args: list[str], word=False):
    replacements = parse_replacement_args(replacement_args)
    if os.path.isdir(path):
        replace_strs_in_dir(path, replacements, word)
    elif os.path.isfile(path):
        replace_strs_in_file(path, replacements, word)
    else:
        assert False, f'{path} does not exist'


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy replace strs')
    parser.add_argument('path')
    parser.add_argument('replace', nargs='+')
    parser.add_argument('--word', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)

    replace_strs(args.path, args.replace or list(), args.word)

    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
