import shutil
import sys
import os

from gas import Gas
from gas_file import GasFile
from gas_parser import GasParser


class GasDir:
    def __init__(self, path, subs=None):
        self.path = path
        self.dir_name = os.path.basename(path)

        self.subdirs: dict[str, GasDir] = dict()
        self.gas_files: dict[str, GasFile] = dict()
        if subs is not None:
            for name, sub in subs.items():
                if isinstance(sub, Gas):
                    self.gas_files[name] = GasFile(os.path.join(path, name+'.gas'), sub)
                elif isinstance(sub, dict):
                    self.subdirs[name] = GasDir(os.path.join(path, name), sub)

        self.loaded = False

    def load(self):
        for entry in os.listdir(self.path):
            sub_path = os.path.join(self.path, entry)
            if os.path.isdir(sub_path):
                self.subdirs[entry] = GasDir(sub_path)
            elif os.path.isfile(sub_path) and entry.endswith('.gas'):
                self.gas_files[entry] = GasFile(sub_path)
        self.loaded = True

    def save(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        for gas_file in self.gas_files.values():
            gas_file.save()
        for subdir in self.subdirs.values():
            subdir.save()

    def delete(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)

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

    def get_subdirs(self):
        if not self.loaded:
            self.load()
        return self.subdirs

    def get_subdir(self, name_path):
        if isinstance(name_path, str):
            name_path = [name_path]
        subdir = self
        for name in name_path:
            subdir = subdir.get_subdirs().get(name)
            if subdir is None:
                return None
        return subdir

    def get_gas_files(self, load=True):
        if not self.loaded and load:
            self.load()
        return self.gas_files

    def get_gas_file(self, gas_file_name):
        return self.get_gas_files().get(gas_file_name + '.gas')

    def get_or_create_gas_file(self, gas_file_name, load=True):
        gas_files = self.get_gas_files(load)
        gas_file_name_full = gas_file_name + '.gas'
        if gas_file_name_full in gas_files:
            return gas_files[gas_file_name_full]
        else:
            gas_file = GasFile(os.path.join(self.path, gas_file_name_full), Gas())
            gas_files[gas_file_name] = gas_file
            return gas_file


def main(argv):
    the_folder = argv[0]
    print(the_folder)
    gas_dir = GasDir(the_folder)
    gas_dir.iter_parse(False, False, False)
    return len(GasParser.get_instance().warnings)


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
