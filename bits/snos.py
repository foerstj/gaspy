import os.path
from pathlib import Path

from sno.sno_handler import SnoHandler


class SNOs:
    def __init__(self, path):
        self.path = path
        self.snos = None

    def print(self):
        path_list = Path(self.path).rglob('*.sno')
        for path in path_list:
            sno_path = os.path.relpath(path, self.path)
            print(sno_path)
            sno = SnoHandler(path)
            sno.print('  ')
