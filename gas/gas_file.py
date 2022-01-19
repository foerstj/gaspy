import sys

from .gas import Gas
from .gas_parser import GasParser
from .gas_writer import GasWriter


class GasFile:
    def __init__(self, path, gas=None):
        self.path = path
        self.gas: Gas = gas

    def load(self):
        self.gas = GasParser.get_instance().parse_file(self.path)

    def save(self):
        if self.gas is not None:
            GasWriter().write_file(self.path, self.gas)

    def get_gas(self):
        if self.gas is None:
            self.load()
        return self.gas


def main(argv):
    the_path = argv[0]
    print(the_path)
    gas_file = GasFile(the_path)
    gas_file.load()
    gas_file.gas.print()
    return len(GasParser.get_instance().warnings)


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
