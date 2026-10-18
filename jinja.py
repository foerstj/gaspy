import math
import os
import sys
import argparse
from os import path

from jinja2 import select_autoescape, FileSystemLoader, Template
from jinja_comprehensions import ComprehensionEnvironment

from bits.bits import Bits


def parse_cell(cell: str):
    cell = cell.strip('"')

    try:
        int_val = int(cell)
        if str(int_val) == cell:
            return int_val
        else:
            return cell  # had leading zeroes -> treat as text
    except ValueError:
        pass

    try:
        return float(cell)
    except ValueError:
        pass

    return cell


def load_csv_as_dicts(csv_file_path: str) -> list[dict]:
    data_dicts = list()
    with open(csv_file_path, 'r', encoding='UTF-8') as csv_file:
        lines = csv_file.readlines()
        header_line = lines[0]
        header_cells = [c.strip() for c in header_line.split(';')]
        header_cells = [parse_cell(c) for c in header_cells]
        data_lines = lines[1:]
        for data_line in data_lines:
            data_cells = [c.strip() for c in data_line.split(';')]
            if set(data_cells) == {''}:
                continue  # ignore empty line
            data_cells = [parse_cell(c) for c in data_cells]
            data_dict = dict()
            for i in range(0, len(header_cells)):
                header_cell = header_cells[i]
                data_cell = data_cells[i]
                data_dict[header_cell] = data_cell
            data_dicts.append(data_dict)
    return data_dicts


def load_csvs_as_dicts(csv_file_paths: list[str]) -> list[dict]:
    data_dicts = list()
    for csv_file_path in csv_file_paths:
        data_dicts.extend(load_csv_as_dicts(csv_file_path))
    return data_dicts


def jinja_file_for_each(file_content_jinja_template: Template, file_name_jinja_template: Template, iter_dicts: list[dict], data_dicts_dict: dict[str, list[dict]], values: dict, abs_dest_dir_path: str):
    for iter_dict in iter_dicts:
        iter_dict.update(values)
        dest_file_name = file_name_jinja_template.render(**iter_dict)
        print(dest_file_name)
        with open(path.join(abs_dest_dir_path, dest_file_name), 'w', encoding='UTF-8') as file:
            file.write(file_content_jinja_template.render(**iter_dict, **data_dicts_dict))


def sqrt_if(value, flag=False):
    return value if not flag else math.sqrt(value)


def resolve_data_csv_file_path(rel_data_csv_file_path: str, bits_path: str) -> str:
    abs_data_csv_file_path = path.join(bits_path, rel_data_csv_file_path)
    if path.isdir(abs_data_csv_file_path):
        csv_files = [f for f in os.listdir(abs_data_csv_file_path) if f.endswith('.csv')]
        assert len(csv_files) == 1, csv_files
        rel_data_csv_file_path = path.join(rel_data_csv_file_path, csv_files[0])
        abs_data_csv_file_path = path.join(bits_path, rel_data_csv_file_path)
    assert rel_data_csv_file_path.endswith('.csv'), rel_data_csv_file_path
    assert path.isfile(abs_data_csv_file_path), abs_data_csv_file_path
    return abs_data_csv_file_path


def resolve_data_csv_file_paths(rel_data_csv_file_paths: list[str], bits_path: str, rel_jinja_template_file_path: str) -> list[str]:
    if rel_data_csv_file_paths is None:
        base_file_path = rel_jinja_template_file_path[:-6]  # cut off ".jinja"
        rel_data_csv_file_path = base_file_path + '.csv'
        rel_data_csv_file_paths = [rel_data_csv_file_path]
    return [resolve_data_csv_file_path(rel_data_csv_file_path, bits_path) for rel_data_csv_file_path in rel_data_csv_file_paths]


def make_paths_dict(paths_with_names: list[str]) -> dict[str, list[str]]:
    paths_dict = dict()
    for path_with_name in paths_with_names:
        if '=' in path_with_name:
            name, path = path_with_name.split('=')
        else:
            name = 'data'
            path = path_with_name
        if name not in paths_dict:
            paths_dict[name] = list()
        paths_dict[name].append(path)
    return paths_dict


# Generate all *.jinja templates in src to files in dst.
# Load values for template content and filenames from corresponding *.csv files.
def jinja(bits_dir: str, rel_jinja_template_file_path: str, rel_dest_dir_path_template: str, dest_name: str, rel_iter_csv_file_paths: list[str], rel_data_csv_file_paths: list[str], values: dict):
    bits = Bits(bits_dir)
    env = ComprehensionEnvironment(
        loader=FileSystemLoader(bits.gas_dir.path),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )
    env.filters['sqrt_if'] = sqrt_if

    abs_jinja_template_file_path = path.join(bits.gas_dir.path, rel_jinja_template_file_path)
    if path.isdir(abs_jinja_template_file_path):
        jinja_files = [f for f in os.listdir(abs_jinja_template_file_path) if f.endswith('.jinja')]
        assert len(jinja_files) == 1, jinja_files
        rel_jinja_template_file_path = path.join(rel_jinja_template_file_path, jinja_files[0])
        abs_jinja_template_file_path = path.join(bits.gas_dir.path, rel_jinja_template_file_path)
    assert rel_jinja_template_file_path.endswith(".jinja"), rel_jinja_template_file_path
    assert path.isfile(abs_jinja_template_file_path), abs_jinja_template_file_path
    rel_dest_dir_path_jinja_template = Template(rel_dest_dir_path_template)
    rel_dest_dir_path = rel_dest_dir_path_jinja_template.render(**values)
    abs_dest_dir_path = path.join(bits.gas_dir.path, rel_dest_dir_path)
    assert path.isdir(abs_dest_dir_path), abs_dest_dir_path
    if rel_data_csv_file_paths is None:
        data_dicts_dict = dict()
    else:
        rel_data_csv_file_paths_dict = make_paths_dict(rel_data_csv_file_paths)
        abs_data_csv_file_paths_dict = {
            name: resolve_data_csv_file_paths(rel_data_csv_file_paths, bits.gas_dir.path, rel_jinja_template_file_path)
            for name, rel_data_csv_file_paths in rel_data_csv_file_paths_dict.items()
        }
        data_dicts_dict = {var_name: load_csvs_as_dicts(paths) for var_name, paths in abs_data_csv_file_paths_dict.items()}

    file_content_jinja_template = env.get_template(rel_jinja_template_file_path.replace('\\', '/'))
    if not dest_name:
        dest_name = path.basename(rel_jinja_template_file_path)[:-6]  # cut off ".jinja"
    file_name_jinja_template = Template(dest_name)
    if rel_iter_csv_file_paths is not None:
        abs_iter_csv_file_paths = resolve_data_csv_file_paths(rel_iter_csv_file_paths, bits.gas_dir.path, rel_jinja_template_file_path)
        iter_dicts = load_csvs_as_dicts(abs_iter_csv_file_paths)
    else:
        iter_dicts = [{}]
    jinja_file_for_each(file_content_jinja_template, file_name_jinja_template, iter_dicts, data_dicts_dict, values, abs_dest_dir_path)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy jinja')
    parser.add_argument('jinja_template', help='Path to Jinja template file, relative to Bits; if dir is given, finds the single .jinja file inside')
    parser.add_argument('dest_dir', help='Path to destination directory, relative to Bits')
    parser.add_argument('dest_name', nargs='?', help='Template string for destination file name; defaults to Jinja template file name without the ".jinja" extension')
    parser.add_argument('--for-each', nargs='+', default=None, help='Path to CSV file, relative to Bits')
    parser.add_argument('--for-all', nargs='+', default=None, help='Path to CSV file, relative to Bits')
    parser.add_argument('--bits', default=None, help='Bits directory serving as base path')
    parser.add_argument('--value', action='append', dest='values', type=lambda kv: kv.split('=', 1), default=list(), help='Additional values to add/override in each data row')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    values = {k: parse_cell(v) for k, v in args.values}
    assert args.for_each or args.for_all, 'Explicit --for-each is required now'  # quick hint for legacy callers of old interface relying on default conventions
    jinja(args.bits, args.jinja_template, args.dest_dir, args.dest_name, args.for_each, args.for_all, values)


if __name__ == '__main__':
    main(sys.argv[1:])
