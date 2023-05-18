from gas.gas_file import GasFile


class QuestUpdate:
    def __init__(self, description: str):
        self.description = description


class Quest:
    def __init__(self, screen_name: str, updates: list[QuestUpdate]):
        self.screen_name = screen_name
        self.updates = updates


# Handler for quests/quests.gas file
class QuestsGas:
    def __init__(self, quests: dict[str, Quest]):
        self.quests: dict[str, Quest] = quests

    @classmethod
    def load(cls, gas_file: GasFile):
        quests = dict()
        quests_gas = gas_file.get_gas()
        for quest_section in quests_gas.get_section('quests').get_sections():
            name = quest_section.header
            updates = list()
            for update_section in quest_section.get_sections():
                updates.append(QuestUpdate(update_section.get_attr_value('description')))
            quest = Quest(quest_section.get_attr_value('screen_name'), updates)
            quests[name] = quest
        return QuestsGas(quests)
