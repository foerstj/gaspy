import os.path
from pathlib import Path

from bits.nnk import NNK
from sno.sno_handler import SnoHandler


class SNOs:
    def __init__(self, path: str, nnk: NNK):
        self.path = path
        self.snos: dict[str, SnoHandler] = dict()
        self._load_sno_paths()
        self.nnk = nnk

    def _load_sno_paths(self):
        for path in self._get_paths():
            self.snos[path.lower()] = None

    def _get_paths(self):
        path_list = Path(self.path).rglob('*.sno')
        return [os.path.relpath(path, self.path) for path in path_list]

    def _load_sno(self, sno_path: str):
        return SnoHandler(os.path.join(self.path, sno_path))

    def get_sno_by_path(self, path):
        path = path.lower()
        if self.snos[path] is None:
            self.snos[path] = self._load_sno(path)
        return self.snos[path]

    def get_sno_by_name(self, name):
        path = self.nnk.lookup_file(name + '.sno').lower()
        root_path = 'terrain' + os.path.sep
        assert path.startswith(root_path), path
        path = path[len(root_path):]
        return self.get_sno_by_path(path)

    @classmethod
    def get_name_for_path(cls, path: str) -> str:
        assert path.endswith('.sno')
        assert os.path.sep in path
        return path[path.rindex(os.path.sep)+1:-4]

    def print(self, indent='', info='data'):
        for sno_path in self.snos:
            print(indent + self.get_name_for_path(sno_path))
            if info == 'data':
                try:
                    sno = self.get_sno_by_path(sno_path)
                    sno.print(indent + '  ')
                except Exception as e:
                    print(indent + f'  {e.__class__.__name__} Exception: {e}')
