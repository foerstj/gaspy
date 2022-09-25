from __future__ import annotations

from gas.gas import Section, Attribute, Gas
from gas.gas_file import GasFile


class ConversationItem:
    def __init__(self, screen_text: str = None, activate_quests: list[str] = None, complete_quests: list[str] = None):
        self.screen_text = screen_text
        self.activate_quests = activate_quests or list()  # list of "quest_name(,i)"
        self.complete_quests = complete_quests or list()  # list of quest names

    @classmethod
    def from_gas(cls, item_section: Section) -> ConversationItem:
        assert item_section.header == 'text*'
        screen_text = item_section.get_attr_value('screen_text')
        activate_quests = [a.value for a in item_section.get_attrs('activate_quest*')]
        complete_quests = [a.value for a in item_section.get_attrs('complete_quest*')]
        return ConversationItem(screen_text, activate_quests, complete_quests)

    # Not fit for use - fields incomplete!
    def to_gas(self) -> Section:
        return Section('text*', [
            Attribute('screen_text', self.screen_text)
        ] + [Attribute('activate_quest*', quest_name) for quest_name in self.activate_quests] + [Attribute('complete_quest*', quest_name) for quest_name in self.complete_quests])


# Handler for conversations.gas files
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

    # Not fit for use - fields incomplete!
    def write_gas(self) -> Gas:
        return Gas([
            Section(name, [item.to_gas() for item in items]) for name, items in self.conversations.items()
        ])