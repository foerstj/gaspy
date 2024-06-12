import os


def csv_cell(data) -> str:
    if data is None:
        return ''
    return f'"{data}"'


def write_csv(name: str, data: list[list], sep=','):
    out_file_path = os.path.join('output', f'{name}.csv')
    with open(out_file_path, 'w') as csv_file:
        csv_file.writelines([sep.join([csv_cell(x) for x in y]) + '\n' for y in data])
    print(f'wrote {out_file_path}')
