import os
import sys

from pathlib import Path


# Primitive helper functions for gas files that treat them as mere text, not trying to parse anything.


def replace_strs_in_file(file_path, strs: list[(str, str)]) -> bool:
    with open(file_path) as map_gas_file:
        text = map_gas_file.read()
    text_pre = text
    for old_str, new_str in strs:
        text = text.replace(old_str, new_str)
    if text != text_pre:
        with open(file_path, 'w') as map_gas_file:
            map_gas_file.write(text)
    return text != text_pre


def replace_strs_in_dir(dir_path, strs: list[(str, str)], rglob_pattern='*.gas', print_path: bool = None):
    path_list = Path(dir_path).rglob(rglob_pattern)
    for path in path_list:
        changed = replace_strs_in_file(path, strs)
        if print_path:
            print(path)
        elif print_path is None and changed:
            print(path)


def main(argv):
    path = argv[0]
    strs = [(str_str.split(',')[0], str_str.split(',')[1]) for str_str in argv[1].split(';')]
    if os.path.isdir(path):
        replace_strs_in_dir(path, strs)
    elif os.path.isfile(path):
        replace_strs_in_file(path, strs)
    else:
        assert False, f'{path} does not exist'
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
