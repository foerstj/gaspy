from gas.gas import Section, Gas, Attribute
from gas.gas_file import GasFile


def cleanup_none(a: list) -> list:
    return [x for x in a if x is not None]


class ChapterUpdate:
    def __init__(self, description: str, order: int, sample: str):
        self.description = description
        self.order = order
        self.sample = sample

    def to_gas(self) -> Section:
        return Section('*', cleanup_none([
            Attribute('description', self.description),
            Attribute('order', self.order),
            Attribute('sample', self.sample) if self.sample is not None else None,
        ]))


class Chapter:
    def __init__(self, screen_name: str, chapter_image: str, updates: list[ChapterUpdate]):
        self.screen_name = screen_name
        self.chapter_image = chapter_image
        self.updates = updates

    def to_gas(self, chapter_name: str) -> Section:
        update_sections = [update.to_gas() for update in self.updates]
        return Section(chapter_name, cleanup_none([
            Attribute('chapter_image', self.chapter_image) if self.chapter_image is not None else None,
            Attribute('screen_name', self.screen_name)
        ]) + update_sections)


class QuestUpdate:
    def __init__(self, description: str, required: bool, order: int, speaker: str, address: str):
        self.description = description
        self.required = required
        self.order = order
        self.speaker = speaker
        self.address = address

    def to_gas(self) -> Section:
        return Section('*', cleanup_none([
            Attribute('address', self.address) if self.address is not None else None,
            Attribute('description', self.description),
            Attribute('order', self.order),
            Attribute('required', self.required) if self.required is not None else None,
            Attribute('speaker', self.speaker) if self.speaker is not None else None
        ]))


class Quest:
    def __init__(self, chapter: str, screen_name: str, quest_image: str, updates: list[QuestUpdate]):
        self.chapter = chapter
        self.screen_name = screen_name
        self.quest_image = quest_image
        self.updates = updates

    def to_gas(self, quest_name: str) -> Section:
        update_sections = [update.to_gas() for update in self.updates]
        return Section(quest_name, cleanup_none([
            Attribute('chapter', self.chapter) if self.chapter is not None else None,
            Attribute('quest_image', self.quest_image) if self.quest_image is not None else None,
            Attribute('screen_name', self.screen_name)
        ]) + update_sections)


# Handler for quests/quests.gas file
class QuestsGas:
    def __init__(self, chapters: dict[str, Chapter], quests: dict[str, Quest]):
        self.chapters = chapters
        self.quests = quests

    @classmethod
    def _load_chapters(cls, section: Section) -> dict[str, Chapter]:
        assert section
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
        assert section
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
        chapters_section = quests_gas.get_section('chapters')
        chapters = cls._load_chapters(chapters_section) if chapters_section is not None else dict()
        quests = cls._load_quests(quests_gas.get_section('quests'))
        return QuestsGas(chapters, quests)

    def write_gas(self) -> Gas:
        chapters_section = Section('chapters', [chapter.to_gas(chapter_name) for chapter_name, chapter in self.chapters.items()])
        quests_section = Section('quests', [quest.to_gas(quest_name) for quest_name, quest in self.quests.items()])
        return Gas([chapters_section, quests_section])
