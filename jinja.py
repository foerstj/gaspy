import sys
import argparse
from os import path

from jinja2 import Environment, select_autoescape, FileSystemLoader
from pathlib import Path

from bits.bits import Bits


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy jinja')
    parser.add_argument('--bits', default=None)
    return parser.parse_args(argv)


def load_csv_as_dicts(csv_file_path):
    data_dicts = list()
    with open(csv_file_path, 'r') as csv_file:
        lines = csv_file.readlines()
        header_line = lines[0]
        header_cells = header_line.split(';')
        data_lines = lines[1:]
        for data_line in data_lines:
            data_cells = data_line.split(';')
            data_dict = dict()
            for i in range(0, len(header_cells)):
                header_cell = header_cells[i]
                data_cell = data_cells[i]
                data_dict[header_cell.strip()] = data_cell.strip()
            data_dicts.append(data_dict)
    return data_dicts


def jinja(bits_dir):
    bits = Bits(bits_dir)
    env = Environment(
        loader=FileSystemLoader(bits.gas_dir.path),
        autoescape=select_autoescape()
    )
    jinja_src_path = path.join(bits.gas_dir.path, 'world', 'contentdb', 'templates.jinja')
    if path.exists(jinja_src_path):
        for jinja_file_path in Path(jinja_src_path).rglob('*.jinja'):
            csv_file_path = str(jinja_file_path)[:-6] + '.csv'
            data_dicts = load_csv_as_dicts(path.join(str(jinja_src_path), csv_file_path))
            print(data_dicts)


def main(argv):
    args = parse_args(argv)
    jinja(args.bits)

    env = Environment(
        loader=FileSystemLoader('input'),
        autoescape=select_autoescape()
    )
    template = env.get_template('jinja-test.txt.jinja')
    print(template.render(foo='bar', jinja='bazinga'))


if __name__ == '__main__':
    main(sys.argv[1:])
