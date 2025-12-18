import math
import os
import sys
import argparse
from os import path

from jinja2 import select_autoescape, FileSystemLoader, Template
from jinja_comprehensions import ComprehensionEnvironment

from bits.bits import Bits


def parse_cell(cell: str):
    try:
        return int(cell)
    except ValueError:
        pass

    try:
        return float(cell)
    except ValueError:
        pass

    return cell


def load_csv_as_dicts(csv_file_path):
    data_dicts = list()
    with open(csv_file_path, 'r', encoding='UTF-8') as csv_file:
        lines = csv_file.readlines()
        header_line = lines[0]
        header_cells = [c.strip() for c in header_line.split(';')]
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


def jinja_file_for_each(file_content_jinja_template: Template, file_name_jinja_template: Template, data_dicts: list[dict], values: dict, abs_dest_dir_path: str):
    for data_dict in data_dicts:
        data_dict.update(values)
        dest_file_name = file_name_jinja_template.render(**data_dict)
        print(dest_file_name)
        with open(path.join(abs_dest_dir_path, dest_file_name), 'w', encoding='UTF-8') as file:
            file.write(file_content_jinja_template.render(**data_dict))


def jinja_file_for_all(file_content_jinja_template: Template, file_name_jinja_template: Template, data_dicts: list[dict], values: dict, abs_dest_dir_path: str):
    dest_file_name = file_name_jinja_template.render(**values)
    print(dest_file_name)
    with open(path.join(abs_dest_dir_path, dest_file_name), 'w', encoding='UTF-8') as file:
        file.write(file_content_jinja_template.render(data=data_dicts))


def sqrt_if(value, flag=False):
    return value if not flag else math.sqrt(value)


# Generate all *.jinja templates in src to files in dst.
# Load values for template content and filenames from corresponding *.csv files.
def jinja(bits_dir: str, rel_jinja_template_file_path: str, rel_dest_dir_path: str, dest_name: str, iter_type: str, rel_data_csv_file_path: str, values: dict):
    assert iter_type in {'each', 'all'}
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
    abs_dest_dir_path = path.join(bits.gas_dir.path, rel_dest_dir_path)
    assert path.isdir(abs_dest_dir_path), abs_dest_dir_path
    if rel_data_csv_file_path is None:
        base_file_path = rel_jinja_template_file_path[:-6]  # cut off ".jinja"
        rel_data_csv_file_path = base_file_path + '.csv'
    abs_data_csv_file_path = path.join(bits.gas_dir.path, rel_data_csv_file_path)
    if path.isdir(abs_data_csv_file_path):
        csv_files = [f for f in os.listdir(abs_data_csv_file_path) if f.endswith('.csv')]
        assert len(csv_files) == 1, csv_files
        rel_data_csv_file_path = path.join(rel_data_csv_file_path, csv_files[0])
        abs_data_csv_file_path = path.join(bits.gas_dir.path, rel_data_csv_file_path)
    assert rel_data_csv_file_path.endswith('.csv'), rel_data_csv_file_path
    assert path.isfile(abs_data_csv_file_path), abs_data_csv_file_path

    data_dicts = load_csv_as_dicts(abs_data_csv_file_path)
    file_content_jinja_template = env.get_template(rel_jinja_template_file_path.replace('\\', '/'))
    if not dest_name:
        dest_name = path.basename(rel_jinja_template_file_path)[:-6]  # cut off ".jinja"
    file_name_jinja_template = Template(dest_name)
    if iter_type == 'each':
        jinja_file_for_each(file_content_jinja_template, file_name_jinja_template, data_dicts, values, abs_dest_dir_path)
    elif iter_type == 'all':
        jinja_file_for_all(file_content_jinja_template, file_name_jinja_template, data_dicts, values, abs_dest_dir_path)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy jinja')
    parser.add_argument('jinja_template', help='Path to Jinja template file, relative to Bits; if dir is given, finds the single .jinja file inside')
    parser.add_argument('dest_dir', help='Path to destination directory, relative to Bits')
    parser.add_argument('dest_name', nargs='?', help='Template string for destination file name; defaults to Jinja template file name without the ".jinja" extension')
    parser.add_argument('--for-each', default=None, help='Path to CSV file, relative to Bits; defaults to file with same name as Jinja template next to it')
    parser.add_argument('--for-all', default=None, help='Path to CSV file, relative to Bits; defaults to file with same name as Jinja template next to it')
    parser.add_argument('--bits', default=None, help='Bits directory serving as base path')
    parser.add_argument('--value', action='append', dest='values', type=lambda kv: kv.split('=', 1), default=list(), help='Additional values to add/override in each data row')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    if args.for_all is not None:
        iter_type = 'all'
        iter_file = args.for_all
    else:
        iter_type = 'each'
        iter_file = args.for_each
    values = {k: parse_cell(v) for k, v in args.values}
    jinja(args.bits, args.jinja_template, args.dest_dir, args.dest_name, iter_type, iter_file, values)


if __name__ == '__main__':
    main(sys.argv[1:])
