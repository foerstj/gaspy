import os

from bits.moods import Moods
from bits.snos import SNOs
from gas.gas_dir import GasDir

from .gas_dir_handler import GasDirHandler
from .language import Language
from bits.maps.map import Map
from .nnk import NNK
from .templates import Templates


class Bits(GasDirHandler):
    DSLOA_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
    DS1_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege', 'Bits')
    DS2_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'My Games', 'Dungeon Siege 2', 'Bits')  # I'm not sure this is correct
    DS2BW_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'My Games', 'Dungeon Siege 2', 'Bits BW')  # I'm sure this is not correct

    def __init__(self, path: str = None):
        if path is None or path.upper() == 'DSLOA':
            path = Bits.DSLOA_PATH
        elif path.upper() == 'DS1':
            path = Bits.DS1_PATH
        elif path.upper() == 'DS2':
            path = Bits.DS2_PATH
        elif path.upper() == 'DS2BW':
            path = Bits.DS2BW_PATH
        assert os.path.isdir(path), path
        super().__init__(GasDir(path))
        self.templates = self.init_templates()
        self.maps: dict[str, Map] = self.init_maps()
        self.moods = self.init_moods()
        self.language = self.init_language()
        self.nnk = self.init_nnk()
        self.snos = self.init_snos()

    def init_maps(self):
        maps_dir = self.gas_dir.get_subdir(['world', 'maps'])
        map_dirs = maps_dir.get_subdirs() if maps_dir is not None else {}
        return {name: Map(map_dir, self) for name, map_dir in map_dirs.items()}

    def init_templates(self):
        templates_dir = self.gas_dir.get_subdir(['world', 'contentdb', 'templates'])
        return Templates(templates_dir)

    def init_moods(self):
        moods_dir = self.gas_dir.get_subdir(['world', 'global', 'moods'])
        return Moods(moods_dir)

    def init_snos(self):
        snos_dir = self.gas_dir.get_subdir(['art', 'terrain'])
        return SNOs(snos_dir.path, self.nnk) if snos_dir is not None else None

    def init_language(self) -> Language:
        language_dir = self.gas_dir.get_subdir('language')
        return Language(language_dir)

    def init_nnk(self):
        art_dir = self.gas_dir.get_subdir(['art'])
        return NNK(art_dir)
