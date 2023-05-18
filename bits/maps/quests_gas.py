from gas.gas import Section
from gas.gas_file import GasFile


class ChapterUpdate:
    def __init__(self, description: str):
        self.description = description


class Chapter:
    def __init__(self, screen_name: str, updates: list[ChapterUpdate]):
        self.screen_name = screen_name
        self.updates = updates


class QuestUpdate:
    def __init__(self, description: str):
        self.description = description


class Quest:
    def __init__(self, screen_name: str, updates: list[QuestUpdate]):
        self.screen_name = screen_name
        self.updates = updates


# Handler for quests/quests.gas file
class QuestsGas:
    def __init__(self, chapters: dict[str, Chapter], quests: dict[str, Quest]):
        self.chapters = chapters
        self.quests = quests

    @classmethod
    def _load_chapters(cls, section: Section) -> dict[str, Chapter]:
        chapters = dict()
        for chapter_section in section.get_sections():
            name = chapter_section.header
            updates = list()
            for update_section in chapter_section.get_sections():
                updates.append(ChapterUpdate(update_section.get_attr_value('description')))
            quest = Chapter(chapter_section.get_attr_value('screen_name'), updates)
            chapters[name] = quest
        return chapters

    @classmethod
    def _load_quests(cls, section: Section) -> dict[str, Quest]:
        quests = dict()
        for quest_section in section.get_sections():
            name = quest_section.header
            updates = list()
            for update_section in quest_section.get_sections():
                updates.append(QuestUpdate(update_section.get_attr_value('description')))
            quest = Quest(quest_section.get_attr_value('screen_name'), updates)
            quests[name] = quest
        return quests

    @classmethod
    def load(cls, gas_file: GasFile):
        quests_gas = gas_file.get_gas()
        chapters = cls._load_chapters(quests_gas.get_section('chapters'))
        quests = cls._load_quests(quests_gas.get_section('quests'))
        return QuestsGas(chapters, quests)
