from __future__ import annotations

from gas.gas import Hex, Position, Section, Attribute, Gas
from gas.gas_file import GasFile


class ConversationItem:
    def __init__(self, screen_text: str = None):
        self.screen_text = screen_text

    @classmethod
    def from_gas(cls, item_section: Section) -> ConversationItem:
        assert item_section.header == 'text*'
        screen_text = item_section.get_attr_value('screen_text')
        return ConversationItem(screen_text)

    def to_gas(self) -> Section:
        return Section('text*', [
            Attribute('screen_text', self.screen_text)
        ])


class ConversationsGas:
    def __init__(self, conversations: dict[str, list[ConversationItem]]):
        self.conversations = conversations

    @classmethod
    def load(cls, gas_file: GasFile) -> ConversationsGas:
        conversations = dict()
        for section in gas_file.get_gas().get_sections():
            conversation_name = section.header
            conversation_items = [ConversationItem.from_gas(s) for s in section.get_sections()]
            conversations[conversation_name] = conversation_items
        return ConversationsGas(conversations)

    def write_gas(self) -> Gas:
        return Gas([
            Section(name, [item.to_gas() for item in items]) for name, items in self.conversations.items()
        ])
