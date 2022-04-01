import os
import sys

from gas.gas import Hex
from pathlib import Path


# Primitive helper functions for gas files that treat them as mere text, not trying to parse anything.


def replace_hexes_in_file(file_path, hexes: list[(Hex, Hex)]):  # Hex-Hex! lol
    with open(file_path) as map_gas_file:
        text = map_gas_file.read()
    text_pre = text
    for old_hex, new_hex in hexes:
        text = text.replace(old_hex.to_str_lower(), new_hex.to_str_lower())
        text = text.replace(old_hex.to_str_upper(), new_hex.to_str_upper())
    if text != text_pre:
        with open(file_path, 'w') as map_gas_file:
            map_gas_file.write(text)


def replace_hexes_in_dir(dir_path, hexes: list[(Hex, Hex)], rglob_pattern='*.gas', print_path=True):
    path_list = Path(dir_path).rglob(rglob_pattern)
    for path in path_list:
        if print_path:
            print(path)
        replace_hexes_in_file(path, hexes)


def main(argv):
    path = argv[0]
    hexes = [(Hex.parse(hex_hex.split(',')[0]), Hex.parse(hex_hex.split(',')[1])) for hex_hex in argv[1].split(';')]
    if os.path.isdir(path):
        replace_hexes_in_dir(path, hexes)
    elif os.path.isfile(path):
        replace_hexes_in_file(path, hexes)
    else:
        assert False, f'{path} does not exist'
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
