import os.path
from pathlib import Path

from sno.sno_handler import SnoHandler


class SNOs:
    def __init__(self, path):
        self.path = path
        self.snos = None

    def get_paths(self):
        path_list = Path(self.path).rglob('*.sno')
        return [os.path.relpath(path, self.path) for path in path_list]

    def get_sno(self, sno_path: str):
        return SnoHandler(os.path.join(self.path, sno_path))

    def print(self):
        for sno_path in self.get_paths():
            print(sno_path)
            try:
                sno = self.get_sno(sno_path)
                sno.print('  ')
            except Exception as e:
                print(f'  {e.__class__.__name__} Exception: {e}')
