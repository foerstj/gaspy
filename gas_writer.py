from gas import Gas, Section, Attribute


class GasWriter:
    @staticmethod
    def format_attr(attr: Attribute, lines: list, indent: int):
        attr_line = '\t'*indent if attr.datatype is None else '\t'*(indent-1) + '  {} '.format(attr.datatype)
        attr_line += '{} = {};\n'.format(attr.name, attr.value_str)
        lines.append(attr_line)

    def format_section(self, section: Section, lines: list, indent=0):
        lines.append('\t'*indent + '[{}]\n'.format(section.header))
        lines.append('\t'*indent + '{\n')

        for item in section.items:
            if isinstance(item, Attribute):
                self.format_attr(item, lines, indent+1)
            else:
                assert isinstance(item, Section)
                self.format_section(item, lines, indent+1)

        lines.append('\t'*indent + '}\n')

    def format_gas(self, gas: Gas):
        lines = []
        for section in gas.items:
            self.format_section(section, lines)
        return lines

    def write_file(self, path: str, gas: Gas):
        gas_lines = self.format_gas(gas)
        with open(path, 'w') as file:
            file.writelines(gas_lines)
