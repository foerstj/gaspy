import os.path
from pathlib import Path

from bits.gas_dir_handler import GasDirHandler
from gas.gas import Section
from gas.gas_dir import GasDir
from gas.gas_file import GasFile


class Mood:
    def __init__(self, mood_name: str, transition_time: float, interior: bool):
        self.mood_name = mood_name
        self.transition_time = transition_time
        self.interior = interior

    @classmethod
    def from_gas(cls, section: Section):
        mood_name = section.get_attr_value('mood_name')
        transition_time = section.get_attr_value('transition_time')
        interior = section.get_attr_value('interior')
        return Mood(mood_name, transition_time, interior)


class Moods(GasDirHandler):
    def __init__(self, gas_dir: GasDir):
        super().__init__(gas_dir)
        self.moods: dict[str, list[Mood]] = None  # dict: sub-path -> moods

    def load_moods(self):
        assert self.moods is None
        self.moods = self.do_load_moods()

    def do_load_moods(self):
        moods: dict[str, list[Mood]] = dict()
        path_list = Path(self.gas_dir.path).rglob('*.gas')
        for path in path_list:
            rel_path = str(os.path.relpath(path, self.gas_dir.path))
            key = rel_path[:-4].replace(os.path.sep, '/')
            mood_file = GasFile(path)
            mood_gas = mood_file.get_gas()
            mood_sections = mood_gas.get_sections('mood_setting*')
            file_moods = list()
            for mood_section in mood_sections:
                file_moods.append(Mood.from_gas(mood_section))
            moods[key] = file_moods
        return moods

    def get_moods(self) -> dict[str, list[Mood]]:
        if self.moods is None:
            self.load_moods()
        return self.moods

    def get_all_moods(self) -> list[Mood]:
        all_moods = list()
        for file_moods in self.get_moods().values():
            all_moods.extend(file_moods)
        return all_moods

    def get_mood_names(self) -> list[str]:
        return [mood.mood_name for mood in self.get_all_moods()]
