from .gas import Section, Attribute, Gas


class GasParser:
    _instance = None

    @staticmethod
    def get_instance():
        if GasParser._instance is None:
            GasParser._instance = GasParser()
        return GasParser._instance

    def __init__(self):
        self.warnings = []
        self.print_warnings = True
        # temp vars
        self.gas = None
        self.stack = None
        self.multiline_value = None
        self.multiline_value_delimiter = None
        self.multiline_value_attr = None

    def warn(self, warning):
        self.warnings.append(warning)
        if self.print_warnings:
            print('Warning: ' + warning)

    def clear_warnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def start_multiline_parsing(self, value, delimiter, attr):
        assert self.multiline_value is None
        self.multiline_value = value
        self.multiline_value_delimiter = delimiter
        self.multiline_value_attr = attr

    def finish_multiline_parsing(self):
        assert (self.multiline_value_delimiter == '*/') != (self.multiline_value_attr is not None)  # xor
        if self.multiline_value_attr is not None:
            self.multiline_value_attr.value = self.multiline_value
        self.multiline_value = None
        self.multiline_value_attr = None
        self.multiline_value_delimiter = None

    def parse_multiline_value(self, line):
        assert self.multiline_value is not None
        value = line.rstrip('\r\n')
        if self.multiline_value_delimiter is None:
            val_start = value.lstrip()[:2]
            if val_start.startswith('"'):
                self.multiline_value_delimiter = '"'
                self.multiline_value += '"'
                value = value.lstrip()[1:]
            elif val_start.startswith('[['):
                self.multiline_value_delimiter = ']]'
            else:
                assert False, 'Unclear multiline value delimiter, value starts with ' + val_start

        end_index = value.find(self.multiline_value_delimiter)
        if end_index == -1:
            # not finished yet - append whole line & continue
            self.multiline_value += '\n' + value
            line = ''
        else:
            assert end_index >= 0
            line = value[end_index + len(self.multiline_value_delimiter):].strip()
            value = value[:end_index + len(self.multiline_value_delimiter)]
            if self.multiline_value_delimiter != ';':
                if line.startswith(';'):
                    line = line[1:].strip()
            else:
                assert value.endswith(';')
                value = value[:-1]
            self.multiline_value += '\n' + value
            self.finish_multiline_parsing()
        return line

    def parse_attribute(self, line):
        current_section = self.stack[-1]
        name_value = line.split('=', 1)
        if len(name_value) != 2:
            self.warn('could not parse: ' + line.strip())
            if '{' in line:
                return line[line.find('{'):]
            return ''  # discard
        [name, value] = name_value
        name = name.strip()
        datatype = None
        if len(name) > 1 and name[1] == ' ':
            datatype = name[0]
            name = name[2:]
        attr = Attribute(name, None, datatype)
        current_section.items.append(attr)

        value: str = value.lstrip().rstrip('\r\n')
        if value.startswith('"'):
            end_index = value.find('"', 1)
            if end_index == -1:
                self.start_multiline_parsing(value, '"', attr)
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
                self.start_multiline_parsing(value, ']]', attr)
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
                self.start_multiline_parsing(value, ';' if value != '' else None, attr)
                line = ''
            else:
                line = value[semicolon + 1:].strip()
                value = value[:semicolon]
            assert len(value) == 0 or value[-1] != ';'
        if self.multiline_value is None:
            if value.endswith(';'):
                value = value[:-1]
            attr.set_value(value, attr.datatype)
        return line

    def parse_line(self, line):
        # print(line)
        current_section = self.stack[-1]
        while line != '':
            if self.multiline_value is not None:
                line = self.parse_multiline_value(line)
            else:
                line = line.lstrip()
                if line == '':
                    pass
                elif line.startswith('//'):
                    line = ''  # ignore end-of-line comment
                elif line.startswith('/*'):
                    endcomment = line.find('*/')
                    if endcomment == -1:
                        self.start_multiline_parsing(line, '*/', None)
                        line = ''
                    else:
                        line = line[endcomment + 2:]
                elif line.startswith('['):
                    endheader_index = line.index(']')  # raises error if not present
                    header = line[1:endheader_index]
                    section = Section(header)
                    current_section.items.append(section)
                    line = line[endheader_index + 1:]
                elif line.startswith('{'):
                    while not isinstance(current_section.items[-1], Section):
                        rogue_attr = current_section.items.pop()
                        self.warn('discarding rogue attribute ' + str(rogue_attr))
                    self.stack.append(current_section.items[-1])
                    line = line[1:]
                    current_section = self.stack[-1]
                elif line.startswith('}'):
                    if len(self.stack) < 2:
                        self.warn('additional closing brace')
                    else:
                        self.stack.pop()
                    current_section = self.stack[-1]
                    line = line[1:]
                else:
                    # attribute
                    line = self.parse_attribute(line)
        assert line == ''

    def parse_file_content(self, open_file):
        gas = Gas()
        self.gas = gas
        self.stack = [self.gas]
        self.multiline_value = None
        self.multiline_value_attr = None
        self.multiline_value_delimiter = None
        for line in open_file:
            self.parse_line(line)
        assert self.multiline_value is None, 'Unexpected end of gas: multiline element'
        assert self.multiline_value_attr is None, 'Unexpected end of gas: multiline element'
        assert self.multiline_value_delimiter is None, 'Unexpected end of gas: multiline element'
        if len(self.stack) != 1:
            self.warn('Unexpected end of gas: ' + str(len(self.stack) - 1) + ' open sections')
        self.stack = None
        self.gas = None
        return gas

    def parse_file(self, path):
        with open(path, encoding='ANSI') as open_file:
            return self.parse_file_content(open_file)
