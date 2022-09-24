from __future__ import annotations

from gas.gas import Section, Attribute, Gas
from gas.gas_file import GasFile


# Handler for lore.gas files
class LoreGas:
    def __init__(self, lore: dict[str, str]):
        self.lore = lore

    @classmethod
    def load(cls, gas_file: GasFile) -> LoreGas:
        lore = dict()
        for section in gas_file.get_gas().get_section('lore').get_sections():
            lore_key = section.header
            lore_text = section.get_attr_value('description')
            lore[lore_key] = lore_text
        return LoreGas(lore)

    def write_gas(self) -> Gas:
        return Gas([
            Section('lore', [
                Section(lore_key, [Attribute('description', lore_text)]) for lore_key, lore_text in self.lore.items()
            ])
        ])
