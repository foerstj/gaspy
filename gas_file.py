import sys

from gas import Gas, Section, Attribute
from gas_parser import GasParser


class GasFile:
    def __init__(self, path):
        self.path = path
        self.gas = None

    def load(self):
        self.gas = GasParser.get_instance().parse_file(self.path)


def main(argv):
    the_path = argv[0]
    print(the_path)
    gas_file = GasFile(the_path)
    gas_file.load()
    gas_file.gas.print()
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
