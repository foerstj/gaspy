from gas import Hex
from pathlib import Path


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


def replace_hexes_in_dir(dir_path, hexes: list[(Hex, Hex)], rglob_pattern='*.gas'):
    path_list = Path(dir_path).rglob(rglob_pattern)
    for path in path_list:
        print(path)
        replace_hexes_in_file(path, hexes)
