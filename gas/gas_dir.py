import shutil
import sys
import os
import time

from .gas import Gas
from .gas_file import GasFile
from .gas_parser import GasParser


class GasDir:
    def __init__(self, path, subs=None):
        self.path = path
        self.dir_name = os.path.basename(path)

        self.subdirs: dict[str, GasDir] = dict()
        self.gas_files: dict[str, GasFile] = dict()  # key is filename WITHOUT .gas extension
        if subs is not None:
            for name, sub in subs.items():
                if isinstance(sub, Gas):
                    self.gas_files[name] = GasFile(os.path.join(path, name+'.gas'), sub)
                elif isinstance(sub, dict):
                    self.subdirs[name] = GasDir(os.path.join(path, name), sub)

        self.loaded = False

    def clear_cache(self):
        self.subdirs: dict[str, GasDir] = dict()
        self.gas_files: dict[str, GasFile] = dict()
        self.loaded = False

    def load_if_required(self, load: bool = None):
        if not self.loaded:
            if load is True or (self.exists() and load is not False):  # load=None means load if exists
                self.load()

    def load(self):
        for entry in os.listdir(self.path):
            sub_path = os.path.join(self.path, entry)
            if os.path.isdir(sub_path):
                self.subdirs[entry] = GasDir(sub_path)
            elif os.path.isfile(sub_path) and entry.endswith('.gas'):
                self.gas_files[entry[:-4]] = GasFile(sub_path)
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
            time.sleep(0.1)  # shutil...

    def print(self, indent='', what='gas'):
        assert what in ['dirs', 'files', 'gas']
        if not self.loaded:
            self.load()
        for name, gas_dir in self.subdirs.items():
            print(indent + name)
            gas_dir.print(indent + '  ', what)
        if what == 'files' or what == 'gas':
            for name, gas_file in self.gas_files.items():
                print(indent + name + '.gas')
                if what == 'gas':
                    if gas_file.gas is None:
                        gas_file.load()
                    gas_file.gas.print(indent + '  ')

    def iter_parse(self, print_gas=True, print_files=True, print_dirs=True, indent=''):
        self.load()
        for name, gas_file in self.gas_files.items():
            if print_files:
                print(indent + name + '.gas')
            gas_file.load()
            if print_gas:
                gas_file.gas.print(indent + '  ')
        for name, gas_dir in self.subdirs.items():
            if print_dirs:
                print(indent + name)
            gas_dir.iter_parse(print_gas, print_files, print_dirs, indent + '  ')

    def iter_rewrite(self, print_files=True, print_dirs=True, indent=''):
        self.load()
        for name, gas_file in self.gas_files.items():
            if print_files:
                print(indent + name + '.gas')
            gas_file.load()  # read in gas...
            gas_file.save()  # ...and write it out again, therefore applying gaspy standard formatting
        for name, gas_dir in self.subdirs.items():
            if print_dirs:
                print(indent + name)
            gas_dir.iter_rewrite(print_files, print_dirs, indent + '  ')

    def get_subdirs(self, load: bool = None):
        self.load_if_required(load)
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

    def get_or_create_subdir(self, name_path, load: bool = None):
        if isinstance(name_path, str):
            name_path = [name_path]
        subdir = self
        for name in name_path:
            subdirs = subdir.get_subdirs(load)
            if name in subdirs:
                subdir = subdirs[name]
            else:
                subdir = GasDir(os.path.join(subdir.path, name))
                subdirs[name] = subdir
        return subdir

    def create_subdir(self, name, subs=None):
        assert name not in self.subdirs
        subdir = GasDir(os.path.join(self.path, name), subs)
        self.subdirs[name] = subdir
        return subdir

    def has_subdir(self, name, load: bool = None):
        return name in self.get_subdirs(load)

    def get_gas_files(self, load: bool = None):
        self.load_if_required(load)
        return self.gas_files

    def get_gas_file(self, gas_file_name):
        return self.get_gas_files().get(gas_file_name)

    def get_or_create_gas_file(self, gas_file_name, load: bool = None):
        gas_files = self.get_gas_files(load)
        if gas_file_name in gas_files:
            return gas_files[gas_file_name]
        else:
            gas_file = GasFile(os.path.join(self.path, gas_file_name + '.gas'), Gas())
            gas_files[gas_file_name] = gas_file
            return gas_file

    def create_gas_file(self, name, gas=None):
        assert name not in self.gas_files
        gas_file = GasFile(os.path.join(self.path, name+'.gas'), gas)
        self.gas_files[name] = gas_file
        return gas_file

    def has_gas_file(self, name, load: bool = None):
        return name in self.get_gas_files(load)

    def exists(self) -> bool:
        return os.path.exists(self.path)


def main(argv):
    the_folder = argv[0]
    print(the_folder)
    gas_dir = GasDir(the_folder)
    # gas_dir.iter_parse(False, False, False)
    gas_dir.iter_rewrite(False)
    return len(GasParser.get_instance().warnings)


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
