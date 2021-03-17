class Hex(int):
    @staticmethod
    def parse(value: str):
        return Hex(int(value, 0))

    def __str__(self):
        return self.to_str_upper()

    def to_str_lower(self):
        return '0x{:08x}'.format(self)

    def to_str_upper(self):
        return '0x{:08X}'.format(self)


class Position:
    def __init__(self, x, y, z, node_guid):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.node_guid = node_guid

    def __str__(self):
        return ','.join([str(x) for x in [self.x, self.y, self.z, self.node_guid]])


class Quaternion:
    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __str__(self):
        return ','.join([str(x) for x in [self.x, self.y, self.z, self.w]])


class Attribute:
    def __init__(self, name, value, datatype=None):
        value, datatype = self.process_value(value, datatype)
        self.name = name
        self.value = value
        self.datatype = datatype

    @staticmethod
    def process_value(value, datatype=None):
        if datatype is not None:
            assert datatype in ['b', 'i', 'f', 'x', 'p', 'q', 'v'], datatype  # p = position, q = orientation, v = vector
            if value is not None:
                assert isinstance(value, str)
                if datatype == 'b':
                    assert value in ['true', 'false']
                    value = True if value == 'true' else False
                elif datatype == 'i':
                    value = int(value)
                elif datatype == 'f':
                    value = float(value)
                elif datatype == 'x':
                    value = Hex.parse(value)
        elif not isinstance(value, str):
            if isinstance(value, bool):
                datatype = 'b'
            elif isinstance(value, Hex):
                datatype = 'x'
            elif isinstance(value, int):
                datatype = 'i'
            elif isinstance(value, float):
                datatype = 'f'
            elif isinstance(value, Position):
                datatype = 'p'
            elif isinstance(value, Quaternion):
                datatype = 'q'
        return value, datatype

    def set_value(self, value, datatype=None):
        value, datatype = self.process_value(value, datatype)
        self.value = value
        self.datatype = datatype

    @property
    def value_str(self):
        if isinstance(self.value, bool):
            return 'true' if self.value else 'false'
        elif isinstance(self.value, float):
            return '{:.6f}'.format(self.value)
        else:
            return str(self.value)

    def __str__(self):
        datatype_str = ' (' + self.datatype + ')' if self.datatype is not None else ''
        return self.name + datatype_str + ' = ' + self.value_str

    def print(self, indent=''):
        print(indent + str(self))


class Gas:  # content of a gas file
    def __init__(self, items=None):
        self.items = items if items is not None else list()  # sections

    def print(self, indent=''):
        for item in self.items:
            item.print(indent)

    def get_sections(self, header=None):
        sections = [item for item in self.items if isinstance(item, Section)]
        if header is not None:
            sections = [section for section in sections if section.header == header]
        return sections

    def get_section(self, header):
        sections = self.get_sections(header)
        assert len(sections) < 2, 'get_section: multiple sections found'
        return sections[0] if len(sections) == 1 else None

    def find_sections_recursive(self, header, results=None):
        if results is None:
            results = list()
        for item in self.items:
            if isinstance(item, Section):
                if item.header == header:
                    results.append(item)
                item.find_sections_recursive(header, results)
        return results

    def get_or_create_section(self, header):
        section = self.get_section(header)
        if section is None:
            section = Section(header)
            self.items.append(section)
        return section


class Section(Gas):
    def __init__(self, header='', items=None):
        super().__init__(items)  # self.items contains attributes & sub-sections
        self.header = header

    def print(self, indent=''):
        print(indent + self.header)
        for item in self.items:
            item.print(indent + '  ')

    def get_attr(self, name):
        attr = None
        for item in self.items:
            if isinstance(item, Attribute):
                if item.name == name:
                    assert attr is None, 'get_attr: multiple attributes found'
                    attr = item
        return attr

    def get_attr_value(self, name):
        attr = self.get_attr(name)
        return attr.value if attr is not None else None

    def set_attr_value(self, name, value):
        attr = self.get_attr(name)
        if attr is not None:
            if value is not None:
                attr.set_value(value)
            else:
                self.items.remove(attr)
        else:
            if value is not None:
                self.items.append(Attribute(name, value))
