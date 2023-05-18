from gas.gas import Section
from gas.gas_file import GasFile


class ChapterUpdate:
    def __init__(self, description: str, order: int, sample: str):
        self.description = description
        self.order = order
        self.sample = sample


class Chapter:
    def __init__(self, screen_name: str, chapter_image: str, updates: list[ChapterUpdate]):
        self.screen_name = screen_name
        self.chapter_image = chapter_image
        self.updates = updates


class QuestUpdate:
    def __init__(self, description: str, required: bool, order: int, speaker: str, address: str):
        self.description = description
        self.required = required
        self.order = order
        self.speaker = speaker
        self.address = address


class Quest:
    def __init__(self, chapter: str, screen_name: str, quest_image: str, updates: list[QuestUpdate]):
        self.chapter = chapter
        self.screen_name = screen_name
        self.quest_image = quest_image
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
                description = update_section.get_attr_value('description')
                order = update_section.get_attr_value('order')
                sample = update_section.get_attr_value('sample')
                updates.append(ChapterUpdate(description, order, sample))
            screen_name = chapter_section.get_attr_value('screen_name')
            chapter_image = chapter_section.get_attr_value('chapter_image')
            chapter = Chapter(screen_name, chapter_image, updates)
            chapters[name] = chapter
        return chapters

    @classmethod
    def _load_quests(cls, section: Section) -> dict[str, Quest]:
        quests = dict()
        for quest_section in section.get_sections():
            name = quest_section.header
            updates = list()
            for update_section in quest_section.get_sections():
                description = update_section.get_attr_value('description')
                required = update_section.get_attr_value('required')
                order = update_section.get_attr_value('order')
                speaker = update_section.get_attr_value('speaker')
                address = update_section.get_attr_value('address')
                updates.append(QuestUpdate(description, required, order, speaker, address))
            chapter = quest_section.get_attr_value('chapter')
            screen_name = quest_section.get_attr_value('screen_name')
            quest_image = quest_section.get_attr_value('quest_image')
            quest = Quest(chapter, screen_name, quest_image, updates)
            quests[name] = quest
        return quests

    @classmethod
    def load(cls, gas_file: GasFile):
        quests_gas = gas_file.get_gas()
        chapters = cls._load_chapters(quests_gas.get_section('chapters'))
        quests = cls._load_quests(quests_gas.get_section('quests'))
        return QuestsGas(chapters, quests)
