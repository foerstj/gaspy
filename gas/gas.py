from gas.molecules import Hex, Position, Quaternion


class Attribute:
    def __init__(self, name: str, value, datatype: str = None):
        value, datatype = self.process_value(value, datatype)
        self.name = name
        self.value = value
        self.datatype = datatype

    @classmethod
    def parse_bool(cls, value):
        assert value in ['true', 'false'], value
        return True if value == 'true' else False

    @classmethod
    def process_value(cls, value, datatype=None):
        if datatype is not None:
            assert datatype in ['b', 'i', 'f', 'x', 'p', 'q', 'v', 'd'], datatype  # p = position, q = orientation, v = vector
            if value is not None:
                assert isinstance(value, str)
                if datatype == 'b':
                    value = cls.parse_bool(value)
                elif datatype == 'i':
                    value = int(value)
                elif datatype == 'f' or datatype == 'd':  # DS2 introduced 'd', probably means double
                    value = float(value)
                elif datatype == 'x':
                    value = Hex.parse(value)
                elif datatype == 'p':
                    value = Position.parse(value)
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

    @classmethod
    def format_float(cls, value: float, six_decimals=True) -> str:
        formatted = f'{value:.6f}'
        if not six_decimals:
            while formatted.endswith('0'):
                formatted = formatted[:-1]
            if formatted.endswith('.'):
                formatted = formatted[:-1]
        return formatted

    @property
    def value_str(self):
        assert self.value is not None, self.name
        if isinstance(self.value, bool):
            return 'true' if self.value else 'false'
        elif isinstance(self.value, float):
            return self.format_float(self.value)
        else:
            return str(self.value)

    def __str__(self):
        datatype_str = ' (' + self.datatype + ')' if self.datatype is not None else ''
        return self.name + datatype_str + ' = ' + self.value_str

    def print(self, indent=''):
        print(indent + str(self))

    def copy(self):
        copy = Attribute(self.name, self.value_str, self.datatype)
        assert str(copy) == str(self)  # safety check
        return copy


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
        assert len(sections) < 2, f'get_section: multiple sections found: {len(sections)} {header}'
        return sections[0] if len(sections) == 1 else None

    def find_sections_recursive(self, header, results=None):
        if results is None:
            results = list()
        for section in self.get_sections():
            if section.header == header:
                results.append(section)
            section.find_sections_recursive(header, results)
        return results

    def insert_item(self, item):
        self.items.append(item)

    def get_or_create_section(self, header):
        section = self.get_section(header)
        if section is None:
            section = Section(header)
            self.insert_item(section)
        return section

    def resolve_attr(self, *attr_path: str) -> Attribute:
        assert len(attr_path) > 1
        sub_name = attr_path[0]
        sub_sections = self.get_sections(sub_name)
        attrs = [s.resolve_attr(*attr_path[1:]) for s in sub_sections]
        attrs = [a for a in attrs if a is not None]
        return attrs[-1] if len(attrs) > 0 else None  # yep, multiple findings. looking at you, braak_magic_base (common:screen_name)


class Section(Gas):
    def __init__(self, header='', items: list = None):
        super().__init__(items)  # self.items contains attributes & sub-sections
        self.header = header

    def print(self, indent=''):
        print(indent + self.header)
        for item in self.items:
            item.print(indent + '  ')

    def get_attrs(self, name=None) -> list[Attribute]:
        attrs = [item for item in self.items if isinstance(item, Attribute)]
        if name is not None:
            attrs = [attr for attr in attrs if attr.name.lower() == name.lower()]
        return attrs

    def get_attr(self, name: str):
        attr = None
        for item in self.items:
            if isinstance(item, Attribute):
                if item.name.lower() == name.lower():
                    assert attr is None, f'get_attr: multiple attributes found: {name}'
                    attr = item
        return attr

    def get_last_attr(self, name: str) -> Attribute:
        attrs = self.get_attrs(name)
        return attrs[-1] if len(attrs) > 0 else None

    def get_attr_value(self, name: str):
        attr = self.get_attr(name)
        return attr.value if attr is not None else None

    @property
    def name(self):
        return self.header

    def insert_item(self, item):
        item_name: str = item.name
        item_is_attr = isinstance(item, Attribute)
        for i in range(len(self.items)):
            other_item = self.items[i]
            other_item_name: str = other_item.name
            other_item_is_attr = isinstance(other_item, Attribute)

            # attrs before sections
            if item_is_attr and not other_item_is_attr:
                self.items.insert(i, item)
                return
            elif not item_is_attr and other_item_is_attr:
                continue

            # attrs / sections in alphabetical order
            if item_name < other_item_name:
                self.items.insert(i, item)
                return
        self.items.append(item)

    def set_attr_value(self, name: str, value):
        attr = self.get_attr(name)
        if attr is not None:
            if value is not None:
                attr.set_value(value)
            else:
                self.items.remove(attr)
        else:
            if value is not None:
                self.insert_item(Attribute(name, value))

    def has_t_n_header(self, t: str = None) -> bool:
        split_header = self.header.split(',')
        if len(split_header) != 2:
            return False
        [t_split, n_split] = split_header
        if not (t_split.startswith('t:') and n_split.startswith('n:')):
            return False
        if t is not None:
            return t_split[2:].lower() == t.lower()
        return True

    def get_t_n_header(self) -> (str, str):
        assert self.has_t_n_header()
        [t, n] = self.header.split(',')
        assert t.startswith('t:') and n.startswith('n:')
        t: str = t[2:]
        n: str = n[2:]
        return t, n

    @classmethod
    def make_t_n_header(cls, t, n):
        return 't:' + t + ',n:' + n

    def set_t_n_header(self, t, n):
        self.header = self.make_t_n_header(t, n)
        assert self.has_t_n_header()

    def resolve_attr(self, *attr_path: str) -> Attribute:
        sub_name = attr_path[0]
        if len(attr_path) == 1:
            return self.get_last_attr(sub_name)  # yep, multiple attrs in one block. looking at you, dsx_troll_mountain (aspect:scale_base)
        sub_sections = self.get_sections(sub_name)
        attrs = [s.resolve_attr(*attr_path[1:]) for s in sub_sections]  # recurse
        attrs = [a for a in attrs if a is not None]
        return attrs[-1] if len(attrs) > 0 else None  # yep, multiple findings. looking at you, braak_magic_base (common:screen_name)

    def resolve_section(self, *section_path: str) -> 'Section':
        sub_name = section_path[0]
        if len(section_path) == 1:
            return self.get_section(sub_name)  # hopefully no multiples here
        sub_sections = self.get_sections(sub_name)
        sections = [s.resolve_section(*section_path[1:]) for s in sub_sections]  # recurse
        sections = [s for s in sections if s is not None]
        assert len(sections) < 2  # hopefully no multiples here
        return sections[-1] if len(sections) > 0 else None

    def find_attrs_recursive(self, name, results=None):
        if results is None:
            results = list()
        for attr in self.get_attrs():
            if attr.name.lower() == name.lower():
                results.append(attr)
        for section in self.get_sections():
            section.find_attrs_recursive(name, results)
        return results

    def copy(self):
        return Section(self.header, [item.copy() for item in self.items])
