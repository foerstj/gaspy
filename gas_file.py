import sys

from gas import Gas, Section, Attribute


class GasFile:
    def __init__(self, path):
        self.path = path
        self.gas = Gas()
        self.load()

    def load(self):
        stack = [self.gas]

        with open(self.path) as gas_file:
            for line in gas_file:
                line = line.strip()
                current_section = stack[-1]
                line = line.split('//', 1)[0].strip()  # ignore end-of-line comment
                if line == '':
                    continue  # empty line
                if line.startswith('['):
                    assert line.endswith(']')
                    header = line[1:-1]
                    section = Section(header)
                    current_section.items.append(section)
                elif line == '{':
                    stack.append(current_section.items[-1])
                elif line == '}':
                    stack.pop()
                else:
                    [name, value] = line.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    assert value.endswith(';')
                    value = value[:-1]
                    attr = Attribute(name, value)
                    current_section.items.append(attr)


def main(argv):
    the_path = argv[0]
    print(the_path)
    gas_file = GasFile(the_path)
    gas_file.gas.print()
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
