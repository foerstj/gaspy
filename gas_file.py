import sys

from gas import Gas, Section, Attribute


class GasFile:
    def __init__(self, path):
        self.path = path
        self.gas = None

    def load(self):
        self.gas = Gas()
        stack = [self.gas]

        with open(self.path, encoding='ANSI') as gas_file:
            multiline_comment = False
            multiline_str = None
            multiline_str_attr = None
            for line in gas_file:
                line = line.rstrip()
                current_section = stack[-1]
                # print(line)
                if multiline_comment:
                    if line.endswith('*/'):
                        multiline_comment = False
                elif multiline_str is not None:
                    value = line
                    endquote = value.find('"')
                    if endquote == -1:
                        multiline_str += '\n' + value
                    else:
                        assert endquote >= 0
                        if len(value) >= endquote + 2 and value[endquote + 1] == ';':
                            endquote += 1
                        line = value[endquote + 1:].strip()
                        value = value[:endquote + 1]
                        multiline_str += '\n' + value
                        multiline_str_attr.value = multiline_str
                        if line:
                            print('Warning: ignoring line remainder after multi-line string: ' + line)
                        multiline_str = None
                        multiline_str_attr = None
                else:
                    line = line.split('//', 1)[0].strip()  # ignore end-of-line comment
                    while line != '':
                        if line.startswith('['):
                            endheader_index = line.index(']')  # raises error if not present
                            header = line[1:endheader_index]
                            section = Section(header)
                            current_section.items.append(section)
                            line = line[endheader_index+1:].strip()
                        elif line.startswith('{'):
                            stack.append(current_section.items[-1])
                            line = line[1:].strip()
                            current_section = stack[-1]
                        elif line.startswith('}'):
                            stack.pop()
                            line = line[1:].strip()
                            current_section = stack[-1]
                        elif line.startswith('/*'):
                            multiline_comment = True
                            line = ''
                        else:
                            name_value = line.split('=', 1)
                            if len(name_value) != 2:
                                print('Warning: could not parse attribute: ' + line)
                                line = ''
                                continue
                            [name, value] = name_value
                            name = name.strip()
                            datatype = None
                            if len(name) > 1 and name[1] == ' ':
                                datatype = name[0]
                                name = name[2:]
                            attr = Attribute(name, None, datatype)
                            current_section.items.append(attr)
                            value: str = value.strip()
                            if value.startswith('"'):
                                endquote = value.find('"', 1)
                                if endquote == -1:
                                    multiline_str = value
                                    multiline_str_attr = attr
                                    line = ''
                                else:
                                    assert endquote > 0
                                    if len(value) >= endquote + 2 and value[endquote+1] == ';':
                                        endquote += 1
                                    line = value[endquote+1:].strip()
                                    if line == ';':
                                        line = ''
                                    value = value[:endquote+1]
                            else:
                                assert ';' not in value[:-1]
                                line = ''
                            if multiline_str is None:
                                if value.endswith(';'):
                                    value = value[:-1]
                                attr.value = value
            assert multiline_comment is False, 'Unexpected end of gas: multiline comment'
            assert len(stack) == 1, 'Unexpected end of gas: ' + str(len(stack)-1) + ' open sections'
            assert multiline_str is None
            assert multiline_str_attr is None


def main(argv):
    the_path = argv[0]
    print(the_path)
    gas_file = GasFile(the_path)
    gas_file.load()
    gas_file.gas.print()
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
