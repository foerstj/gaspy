import os.path
from pathlib import Path

from sno.sno_handler import SnoHandler


class SNOs:
    def __init__(self, path: str):
        self.path = path
        self.snos: dict[str, SnoHandler] = dict()
        self._load_sno_paths()

    def _load_sno_paths(self):
        for path in self._get_paths():
            self.snos[path] = None

    def _get_paths(self):
        path_list = Path(self.path).rglob('*.sno')
        return [os.path.relpath(path, self.path) for path in path_list]

    def _load_sno(self, sno_path: str):
        return SnoHandler(os.path.join(self.path, sno_path))

    def get_sno_by_path(self, path):
        if self.snos[path] is None:
            self.snos[path] = self._load_sno(path)
        return self.snos[path]

    def print(self):
        for sno_path in self.snos:
            print(sno_path)
            try:
                sno = self.get_sno_by_path(sno_path)
                sno.print('  ')
            except Exception as e:
                print(f'  {e.__class__.__name__} Exception: {e}')
