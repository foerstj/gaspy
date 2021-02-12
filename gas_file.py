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
            multiline_value = None
            multiline_value_attr = None
            multiline_value_delimiter = None
            for line in gas_file:
                line = line.rstrip()
                current_section = stack[-1]
                # print(line)
                if multiline_comment:
                    if line.endswith('*/'):
                        multiline_comment = False
                elif multiline_value is not None:
                    value = line
                    end_index = value.find(multiline_value_delimiter)
                    if end_index == -1:
                        multiline_value += '\n' + value
                    else:
                        assert end_index >= 0
                        line = value[end_index + len(multiline_value_delimiter):].strip()
                        if line.startswith(';'):
                            line = line[1:].strip()
                        value = value[:end_index + len(multiline_value_delimiter)]
                        if value.endswith(';'):
                            value = value[:-1]
                        multiline_value += '\n' + value
                        multiline_value_attr.value = multiline_value
                        if line:
                            print('Warning: ignoring line remainder after multi-line value: ' + line)
                        multiline_value = None
                        multiline_value_attr = None
                        multiline_value_delimiter = None
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
                            while type(current_section.items[-1]) != Section:
                                rogue_attr = current_section.items.pop()
                                print('Warning: discarding rogue attribute ' + str(rogue_attr))
                            stack.append(current_section.items[-1])
                            line = line[1:].strip()
                            current_section = stack[-1]
                        elif line.startswith('}'):
                            stack.pop()
                            line = line[1:].strip()
                            current_section = stack[-1]
                        elif line.startswith('/*'):
                            endcomment = line.find('*/')
                            if endcomment == -1:
                                multiline_comment = True
                                line = ''
                            else:
                                line = line[endcomment+2:]
                        else:
                            name_value = line.split('=', 1)
                            if len(name_value) != 2:
                                print('Warning: could not parse: ' + line)
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
                                end_index = value.find('"', 1)
                                if end_index == -1:
                                    multiline_value = value
                                    multiline_value_attr = attr
                                    multiline_value_delimiter = '"'
                                    line = ''
                                else:
                                    assert end_index > 0
                                    if len(value) >= end_index + 2 and value[end_index+1] == ';':
                                        end_index += 1
                                    line = value[end_index+1:].strip()
                                    if line == ';':
                                        line = ''
                                    value = value[:end_index+1]
                            else:
                                semicolon = value.find(';')
                                if semicolon == -1:
                                    multiline_value = value
                                    multiline_value_attr = attr
                                    if value == '':
                                        multiline_value_delimiter = ']]'
                                    else:
                                        multiline_value_delimiter = ';'
                                    line = ''
                                else:
                                    line = value[semicolon+1:].strip()
                                    value = value[:semicolon]
                                assert len(value) == 0 or value[-1] != ';'
                            if multiline_value is None:
                                if value.endswith(';'):
                                    value = value[:-1]
                                attr.value = value
            assert multiline_comment is False, 'Unexpected end of gas: multiline comment'
            assert len(stack) == 1, 'Unexpected end of gas: ' + str(len(stack)-1) + ' open sections'
            assert multiline_value is None, 'Unexpected end of gas: multiline value'
            assert multiline_value_attr is None, 'Unexpected end of gas: multiline value'
            assert multiline_value_delimiter is None, 'Unexpected end of gas: multiline value'


def main(argv):
    the_path = argv[0]
    print(the_path)
    gas_file = GasFile(the_path)
    gas_file.load()
    gas_file.gas.print()
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
