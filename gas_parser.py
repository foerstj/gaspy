from gas import Section, Attribute
from gas_file import Gas


class GasParser:
    _instance = None

    @staticmethod
    def get_instance():
        if GasParser._instance is None:
            GasParser._instance = GasParser()
        return GasParser._instance

    def parse_file_content(self, open_file):
        # I am ashamed of this function
        gas = Gas()
        stack = [gas]
        multiline_comment = False
        multiline_value = None
        multiline_value_attr = None
        multiline_value_delimiter = None
        for line in open_file:
            line = line.rstrip()
            current_section = stack[-1]
            # print(line)
            if multiline_comment:
                if line.endswith('*/'):
                    multiline_comment = False
            elif multiline_value is not None:
                value = line
                if multiline_value_delimiter is None:
                    val_start = value.lstrip()[:2]
                    if val_start.startswith('"'):
                        multiline_value_delimiter = '"'
                        multiline_value += '"'
                        value = value.lstrip()[1:]
                    elif val_start.startswith('[['):
                        multiline_value_delimiter = ']]'
                    else:
                        assert False, 'Unclear multiline value delimiter, value starts with ' + val_start
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
                        line = line[endheader_index + 1:].strip()
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
                            line = line[endcomment + 2:]
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
                                if len(value) >= end_index + 2 and value[end_index + 1] == ';':
                                    end_index += 1
                                line = value[end_index + 1:].strip()
                                if line == ';':
                                    line = ''
                                value = value[:end_index + 1]
                        elif value.startswith('[['):
                            end_index = value.find(']]')
                            if end_index == -1:
                                multiline_value = value
                                multiline_value_attr = attr
                                multiline_value_delimiter = ']]'
                                line = ''
                            else:
                                assert end_index > 0
                                line = value[end_index + 2:].lstrip()
                                assert line.startswith(';')
                                line = line[1:].lstrip()
                                value = value[:end_index + 2]
                        else:
                            semicolon = value.find(';')
                            if semicolon == -1:
                                multiline_value = value
                                multiline_value_attr = attr
                                if value == '':
                                    pass  # delimiter yet unknown
                                else:
                                    multiline_value_delimiter = ';'
                                line = ''
                            else:
                                line = value[semicolon + 1:].strip()
                                value = value[:semicolon]
                            assert len(value) == 0 or value[-1] != ';'
                        if multiline_value is None:
                            if value.endswith(';'):
                                value = value[:-1]
                            attr.value = value
        assert multiline_comment is False, 'Unexpected end of gas: multiline comment'
        assert len(stack) == 1, 'Unexpected end of gas: ' + str(len(stack) - 1) + ' open sections'
        assert multiline_value is None, 'Unexpected end of gas: multiline value'
        assert multiline_value_attr is None, 'Unexpected end of gas: multiline value'
        assert multiline_value_delimiter is None, 'Unexpected end of gas: multiline value'

        return gas

    def parse_file(self, path):
        with open(path, encoding='ANSI') as open_file:
            return self.parse_file_content(open_file)
