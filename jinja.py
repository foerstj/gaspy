import sys
import argparse
from os import path

from jinja2 import Environment, select_autoescape, FileSystemLoader, Template
from pathlib import Path

from bits.bits import Bits


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy jinja')
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('--bits', default=None)
    return parser.parse_args(argv)


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
    with open(csv_file_path, 'r') as csv_file:
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


# Generate all *.jinja templates in src to files in dst.
# Load values for template content and filenames from corresponding *.csv files.
def jinja(bits_dir: str, rel_jinja_src_path: str, rel_jinja_dest_path: str):
    bits = Bits(bits_dir)
    env = Environment(
        loader=FileSystemLoader(bits.gas_dir.path),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )
    abs_jinja_src_path = path.join(bits.gas_dir.path, rel_jinja_src_path)
    abs_jinja_dest_path = path.join(bits.gas_dir.path, rel_jinja_dest_path)
    if path.exists(abs_jinja_src_path):
        for globbed_file_path in Path(abs_jinja_src_path).rglob('*.jinja'):
            jinja_file_path = str(path.relpath(globbed_file_path, abs_jinja_src_path))
            base_file_path = jinja_file_path[:-6]
            csv_file_path = base_file_path + '.csv'
            data_dicts = load_csv_as_dicts(path.join(abs_jinja_src_path, csv_file_path))
            template = env.get_template(path.join(rel_jinja_src_path, jinja_file_path).replace('\\', '/'))
            file_name_template = Template(base_file_path)
            for data_dict in data_dicts:
                dest_file_path = file_name_template.render(**data_dict)
                print(dest_file_path)
                with open(path.join(abs_jinja_dest_path, dest_file_path), 'w') as file:
                    file.write(template.render(**data_dict))


def main(argv):
    args = parse_args(argv)
    jinja(args.bits, args.src, args.dst)


if __name__ == '__main__':
    main(sys.argv[1:])
