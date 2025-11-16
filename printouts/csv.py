import os


def csv_cell(data) -> str:
    if data is None:
        return ''
    if isinstance(data, str):
        assert '"' not in data, data
    return f'"{data}"'


def write_csv(name: str, data: list[list], sep=','):
    out_file_path = os.path.join('output', f'{name}.csv')
    lines = [sep.join([csv_cell(x) for x in y]) + '\n' for y in data]
    with open(out_file_path, 'w') as csv_file:
        csv_file.writelines(lines)
    print(f'wrote {out_file_path}')


def write_csv_dict(name: str, keys: list[str], header_dict: dict[str, str], data_dicts: list[dict], sep=','):
    header_row = [header_dict[key] for key in keys]
    csv = [header_row]
    for data_dict in data_dicts:
        data_row = [data_dict[key] for key in keys]
        csv.append(data_row)
    write_csv(name, csv, sep)
