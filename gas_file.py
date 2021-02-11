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
            multiline_comment = False
            for line in gas_file:
                line = line.strip()
                current_section = stack[-1]
                # print(line)
                if multiline_comment:
                    if line.endswith('*/'):
                        multiline_comment = False
                else:
                    line = line.split('//', 1)[0].strip()  # ignore end-of-line comment
                    while line != '':
                        if line.startswith('['):
                            assert line.endswith(']')
                            header = line[1:-1]
                            section = Section(header)
                            current_section.items.append(section)
                            line = ''
                        elif line == '{':
                            stack.append(current_section.items[-1])
                            line = ''
                        elif line == '}':
                            stack.pop()
                            line = ''
                        elif line.startswith('/*'):
                            multiline_comment = True
                            line = ''
                        else:
                            [name, value] = line.split('=', 1)
                            name = name.strip()
                            datatype = None
                            if len(name) > 1 and name[1] == ' ':
                                datatype = name[0]
                                name = name[2:]
                            value: str = value.strip()
                            if value.startswith('"'):
                                endquote = value.index('"', 1)
                                assert endquote > 0
                                if len(value) >= endquote + 2 and value[endquote+1] == ';':
                                    endquote += 1
                                line = value[endquote+1:].strip()
                                value = value[:endquote+1]
                            else:
                                assert ';' not in value[:-1]
                                line = ''
                            if value.endswith(';'):
                                value = value[:-1]
                            attr = Attribute(name, value, datatype)
                            current_section.items.append(attr)
            assert multiline_comment is False, 'Unexpected end of gas: multiline comment'
            assert len(stack) == 1, 'Unexpected end of gas: ' + str(len(stack)-1) + ' open sections'


def main(argv):
    the_path = argv[0]
    print(the_path)
    gas_file = GasFile(the_path)
    gas_file.gas.print()
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
