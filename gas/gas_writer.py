from .gas import Gas, Section, Attribute


class GasWriter:
    @staticmethod
    def format_attr(attr: Attribute, lines: list, indent: int):
        attr_line = '\t'*indent if attr.datatype is None else '\t'*(indent-1) + '  {} '.format(attr.datatype)
        attr_line += '{} = {};\n'.format(attr.name, attr.value_str)
        lines.append(attr_line)

    def _format_section(self, section: Section, lines: list, indent=0):
        lines.append('\t'*indent + '[{}]\n'.format(section.header))
        lines.append('\t'*indent + '{\n')

        for item in section.items:
            if isinstance(item, Attribute):
                self.format_attr(item, lines, indent+1)
            else:
                assert isinstance(item, Section)
                self._format_section(item, lines, indent + 1)

        lines.append('\t'*indent + '}\n')

    # format the content of a gas file into lines
    def format_gas(self, gas: Gas) -> list[str]:
        lines = []
        for section in gas.items:
            self._format_section(section, lines)
        return lines

    def format_gas_str(self, gas: Gas) -> str:
        return '\n'.join(self.format_gas(gas))

    # format a section into a string
    def format_section_str(self, section: Section, indent=0) -> str:
        lines = []
        self._format_section(section, lines, indent)
        return '\n'.join(lines)

    def write_file(self, path: str, gas: Gas):
        gas_lines = self.format_gas(gas)
        with open(path, 'w') as file:
            file.writelines(gas_lines)
