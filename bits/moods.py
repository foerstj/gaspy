import os
from pathlib import Path

from bits.gas_dir_handler import GasDirHandler
from gas.gas_file import GasFile


class Moods(GasDirHandler):
    def get_mood_names(self) -> list[str]:
        mood_names = []
        path_list = Path(self.gas_dir.path).rglob('*.gas')
        for path in path_list:
            # print(path)
            mood_file = GasFile(path)
            mood_gas = mood_file.get_gas()
            mood_sections = mood_gas.get_sections('mood_setting*')
            for mood_section in mood_sections:
                mood_name = mood_section.get_attr_value('mood_name')
                # print('  ' + mood_name)
                mood_names.append(mood_name)
        return mood_names
