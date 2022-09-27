from gas.gas import Section

from bits.templates import Template


class GameObject:
    def __init__(self, section: Section, bits):
        self._bits = bits
        self.section = section
        [t, n] = section.header.split(',')
        assert t.startswith('t:')
        assert n.startswith('n:')
        self.template_name: str = t[2:]
        self.object_id: str = n[2:]

    def get_template(self) -> Template:
        template = self._bits.templates.get_templates().get(self.template_name.lower())
        assert template is not None, self.template_name
        return template

    def get_own_value(self, section_header, attr_name):
        section = self.section.get_section(section_header) if section_header is not None else self.section
        if section is not None:
            attr = section.get_attr(attr_name)
            if attr is not None:
                return attr.value
        return None

    def compute_value(self, section_header, attr_name):
        own_value = self.get_own_value(section_header, attr_name)
        if own_value is not None:
            return own_value
        template = self.get_template()
        return template.compute_value(section_header, attr_name) if section_header is not None else template.compute_value(attr_name)

    def is_plant(self):
        return self.get_template().is_plant()
