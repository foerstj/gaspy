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
        self.moods: list[Mood] = None

    def load_moods(self):
        assert self.moods is None
        self.moods = self.do_load_moods()

    def do_load_moods(self):
        moods: list[Mood] = []
        path_list = Path(self.gas_dir.path).rglob('*.gas')
        for path in path_list:
            # print(path)
            mood_file = GasFile(path)
            mood_gas = mood_file.get_gas()
            mood_sections = mood_gas.get_sections('mood_setting*')
            for mood_section in mood_sections:
                moods.append(Mood.from_gas(mood_section))
        return moods

    def get_moods(self) -> list[Mood]:
        if self.moods is None:
            self.load_moods()
        return self.moods

    def get_mood_names(self) -> list[str]:
        return [mood.mood_name for mood in self.get_moods()]
