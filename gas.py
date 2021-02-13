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
    def __init__(self):
        self.items = list()  # sections

    def print(self, indent=''):
        for item in self.items:
            item.print(indent)

    def get_section(self, header):
        section = None
        for item in self.items:
            if isinstance(item, Section):
                if item.header == header:
                    assert section is None, 'get_section: multiple sections found'
                    section = item
        return section

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
    def __init__(self, header=''):
        super().__init__()  # self.items contains attributes & sub-sections
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
