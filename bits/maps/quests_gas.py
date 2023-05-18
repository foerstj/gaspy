from gas.gas import Section, Gas, Attribute
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

    @classmethod
    def _write_gas_chapter_update(cls, update: ChapterUpdate) -> Section:
        return Section('*', [
            Attribute('description', update.description),
            Attribute('order', update.order),
            Attribute('sample', update.sample),
        ])

    @classmethod
    def _write_gas_chapter(cls, chapter_name: str, chapter: Chapter) -> Section:
        update_sections = [cls._write_gas_chapter_update(update) for update in chapter.updates]
        return Section(chapter_name, [
            Attribute('chapter_image', chapter.chapter_image),
            Attribute('screen_name', chapter.screen_name)
        ] + update_sections)

    @classmethod
    def _write_gas_quest_update(cls, update: QuestUpdate) -> Section:
        return Section('*', [
            Attribute('address', update.address),
            Attribute('description', update.description),
            Attribute('order', update.order),
            Attribute('required', update.required),
            Attribute('speaker', update.speaker)
        ])

    @classmethod
    def _write_gas_quest(cls, quest_name: str, quest: Quest) -> Section:
        update_sections = [cls._write_gas_quest_update(update) for update in quest.updates]
        return Section(quest_name, [
            Attribute('chapter', quest.chapter),
            Attribute('quest_image', quest.quest_image),
            Attribute('screen_name', quest.screen_name)
        ] + update_sections)

    def write_gas(self) -> Gas:
        chapters_section = Section('chapters', [self._write_gas_chapter(chapter_name, chapter) for chapter_name, chapter in self.chapters.items()])
        quests_section = Section('quests', [self._write_gas_quest(quest_name, quest) for quest_name, quest in self.quests.items()])
        return Gas([chapters_section, quests_section])
