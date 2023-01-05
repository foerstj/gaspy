import os

from gas.gas_dir import GasDir


class NNK:
    def __init__(self, art_dir: GasDir):
        self.art_dir = art_dir
        self.nnk: dict[str, str] = dict()
        if art_dir is not None:
            self._load_nnk(art_dir)

    def _load_nnk(self, art_dir: GasDir):
        for filename in os.listdir(art_dir.path):
            if filename.endswith('.nnk'):
                self._load_nnk_file(os.path.join(art_dir.path, filename))

    def _load_nnk_file(self, file_path):
        with open(file_path, 'r') as file:
            for line in file.readlines():
                if not line.startswith('TREE ='):
                    continue
                tree_def = [x.strip() for x in line[6:].split(',')]
                assert len(tree_def) >= 3, line
                prefix, sub_path = tree_def[:2]
                prefix = prefix.lower()
                self.nnk[prefix] = sub_path

    def lookup_prefix(self, prefix: str):
        prefix_segments = prefix.lower().split('_')
        path = ''
        for n in range(len(prefix_segments)):
            sub_prefix = '_'.join(prefix_segments[:n+1])
            assert sub_prefix in self.nnk, sub_prefix
            sub_path = self.nnk[sub_prefix]
            path = os.path.join(path, sub_path)
        return path

    def lookup_file(self, filename: str):
        filename_segments = filename.lower().split('_')
        path = ''
        for n in range(len(filename_segments)):
            sub_prefix = '_'.join(filename_segments[:n+1])
            if sub_prefix not in self.nnk:
                break
            sub_path = self.nnk[sub_prefix]
            path = os.path.join(path, sub_path)
        assert path != '', f'filename {filename} did not match any NNK prefix'
        return os.path.join(path, filename)

    def print(self):
        for prefix in self.nnk.keys():
            print(f'{prefix}: {self.lookup_prefix(prefix)}')
