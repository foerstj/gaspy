import sys
import os

from gas_file import GasFile
from gas_parser import GasParser


class GasDir:
    def __init__(self, path):
        self.path = path
        self.subdirs = dict()
        self.gas_files = dict()
        self.loaded = False

    def load(self):
        for entry in os.listdir(self.path):
            sub_path = os.path.join(self.path, entry)
            if os.path.isdir(sub_path):
                self.subdirs[entry] = GasDir(sub_path)
            elif os.path.isfile(sub_path) and entry.endswith('.gas'):
                self.gas_files[entry] = GasFile(sub_path)
        self.loaded = True

    def print(self, indent=''):
        if not self.loaded:
            self.load()
        for name, gas_file in self.gas_files.items():
            if gas_file.gas is None:
                gas_file.load()
            print(indent + name)
            gas_file.gas.print(indent + '  ')
        for name, gas_dir in self.subdirs.items():
            print(indent + name)
            gas_dir.print(indent + '  ')

    def iter_parse(self, print_gas=True, print_files=True, print_dirs=True, indent=''):
        self.load()
        for name, gas_file in self.gas_files.items():
            if print_files:
                print(indent + name)
            gas_file.load()
            if print_gas:
                gas_file.gas.print(indent + '  ')
        for name, gas_dir in self.subdirs.items():
            if print_dirs:
                print(indent + name)
            gas_dir.iter_parse(print_gas, print_files, print_dirs, indent + '  ')


def main(argv):
    the_folder = argv[0]
    print(the_folder)
    gas_dir = GasDir(the_folder)
    gas_dir.iter_parse(False, False, False)
    return len(GasParser.get_instance().warnings)


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
