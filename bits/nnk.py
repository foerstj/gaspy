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
                prefix_segments = prefix.split('_')
                if len(prefix_segments) > 1:
                    parent_prefix = '_'.join(prefix_segments[:-1])
                    assert parent_prefix in self.nnk
                    sub_path = os.path.join(self.nnk[parent_prefix], sub_path)
                self.nnk[prefix] = sub_path

    def print(self):
        for prefix, path in self.nnk.items():
            print(f'{prefix}: {path}')
