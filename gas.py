class Attribute:
    def __init__(self, name, value, datatype=None):
        self.name = name
        self.value = value
        self.datatype = datatype

    def __str__(self):
        datatype_str = ' (' + self.datatype + ')' if self.datatype is not None else ''
        return self.name + datatype_str + ' = ' + self.value

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
                    assert attr is None, 'get_section: multiple sections found'
                    attr = item
        return attr
