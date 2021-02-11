import sys
import os

from gas_file import GasFile


class GasDir:
    def __init__(self, path):
        self.path = path
        self.subdirs = dict()
        self.gas_files = dict()
        self.loaded = False

    def load(self):
        for entry in os.listdir(self.path):
            sub_path = os.path.join(self.path, entry)
            if entry == 'regions' or entry == 'stitch_index.gas':
                continue  # slowly slowly
            if os.path.isdir(sub_path):
                self.subdirs[entry] = GasDir(sub_path)
            elif os.path.isfile(sub_path) and entry.endswith('.gas'):
                self.gas_files[entry] = GasFile(sub_path)
        self.loaded = True

    def print(self, indent=''):
        if not self.loaded:
            self.load()
        for name, gas_file in self.gas_files.items():
            print(indent + name)
            gas_file.gas.print(indent + '  ')
        for name, gas_dir in self.subdirs.items():
            print(indent + name)
            gas_dir.print(indent + '  ')


def main(argv):
    the_folder = argv[0]
    print(the_folder)
    gas_dir = GasDir(the_folder)
    gas_dir.print()
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
