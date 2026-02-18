import os


def csv_cell(data, quote=True) -> str:
    if data is None:
        return ''
    if quote:
        if isinstance(data, str):
            assert '"' not in data, data
        return f'"{data}"'
    else:
        return f'{data}'


def parse_csv_cell(cell: str):
    cell = cell.strip('"')
    return cell


def write_csv(name: str, data: list[list], sep=',', quote_cells=True):
    out_file_path = os.path.join('output', f'{name}.csv')
    lines = [sep.join([csv_cell(x, quote_cells) for x in y]) + '\n' for y in data]
    with open(out_file_path, 'w', encoding='UTF-8') as csv_file:
        csv_file.writelines(lines)
    print(f'wrote {out_file_path}')


def read_csv(name: str, sep=',') -> list[list]:
    in_file_path = os.path.join('input', f'{name}.csv')
    with open(in_file_path, 'r', encoding='UTF-8') as csv_file:
        lines = csv_file.readlines()
    data = [[parse_csv_cell(cell) for cell in line.rstrip('\n').split(sep)] for line in lines]
    return data


def write_csv_dict(name: str, keys: list[str], header_dict: dict[str, str], data_dicts: list[dict], sep=',', quote_cells=True):
    header_row = [header_dict[key] for key in keys]
    csv = [header_row]
    for data_dict in data_dicts:
        data_row = [data_dict[key] for key in keys]
        csv.append(data_row)
    write_csv(name, csv, sep, quote_cells)
