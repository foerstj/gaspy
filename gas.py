class Attribute:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def print(self, indent=''):
        print(indent + self.name + ' = ' + self.value)


class Section:
    def __init__(self, header=''):
        self.header = header
        self.items = list()  # attributes & sub-sections

    def print(self, indent=''):
        print(indent + self.header)
        for item in self.items:
            item.print(indent + '  ')


class Gas:  # content of a gas file
    def __init__(self):
        self.items = list()  # sections

    def print(self, indent=''):
        for item in self.items:
            item.print(indent)
