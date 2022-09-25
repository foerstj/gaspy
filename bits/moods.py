import os.path
from pathlib import Path

from bits.gas_dir_handler import GasDirHandler
from gas.gas import Section, Attribute
from gas.gas_dir import GasDir
from gas.gas_file import GasFile
from gas.molecules import Hex


def non_null_attrs(attrs: list[Attribute], sort=True) -> list[Attribute]:
    attrs = [attr for attr in attrs if attr is not None and attr.value is not None]
    if sort:
        attrs.sort(key=lambda x: x.name)
    return attrs


class MoodFog:
    def __init__(self, color: Hex, density: float, near_dist: float, far_dist: float, lowdetail_near_dist: float, lowdetail_far_dist: float):
        self.color = color
        self.density = density
        self.near_dist = near_dist
        self.far_dist = far_dist
        self.lowdetail_near_dist = lowdetail_near_dist
        self.lowdetails_far_dist = lowdetail_far_dist

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'fog'
        return MoodFog(
            section.get_attr_value('fog_color'),
            section.get_attr_value('fog_density'),
            section.get_attr_value('fog_near_dist'),
            section.get_attr_value('fog_far_dist'),
            section.get_attr_value('fog_lowdetail_near_dist'),
            section.get_attr_value('fog_lowdetail_far_dist')
        )

    def to_gas(self) -> Section:
        return Section('fog', non_null_attrs([
            Attribute('fog_color', self.color),
            Attribute('fog_density', self.density),
            Attribute('fog_near_dist', self.near_dist),
            Attribute('fog_far_dist', self.far_dist),
            Attribute('fog_lowdetail_near_dist', self.lowdetail_near_dist),
            Attribute('fog_lowdetail_far_dist', self.lowdetails_far_dist)
        ]))


class MoodFrustum:
    def __init__(self, height: float, width: float):
        self.height = height
        self.width = width

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'frustum'
        return MoodFrustum(
            section.get_attr_value('frustum_height'),
            section.get_attr_value('frustum_width')
        )

    def to_gas(self) -> Section:
        return Section('frustum', non_null_attrs([
            Attribute('frustum_height', self.height),
            Attribute('frustum_width', self.width)
        ]))


class MoodRain:
    def __init__(self, density: float, lightning: bool):
        self.density = density
        self.lightning = lightning

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'rain'
        return MoodRain(
            section.get_attr_value('rain_density'),
            section.get_attr_value('lightning')
        )

    def to_gas(self) -> Section:
        return Section('rain', non_null_attrs([
            Attribute('rain_density', self.density),
            Attribute('lightning', self.lightning)
        ]))


class MoodWind:
    def __init__(self, velocity: float, direction: float):
        self.velocity = velocity
        self.direction = direction

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'wind'
        return MoodWind(
            section.get_attr_value('wind_velocity'),
            section.get_attr_value('wind_direction')
        )

    def to_gas(self) -> Section:
        return Section('wind', non_null_attrs([
            Attribute('wind_velocity', self.velocity),
            Attribute('wind_direction', self.direction)
        ]))


class Mood:
    def __init__(self, mood_name: str, transition_time: float, interior: bool, fog: MoodFog, frustum: MoodFrustum, rain: MoodRain, wind: MoodWind):
        self.mood_name = mood_name
        self.transition_time = transition_time
        self.interior = interior
        self.fog = fog
        self.frustum = frustum
        self.rain = rain
        self.wind = wind

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'mood_setting*'
        mood_name = section.get_attr_value('mood_name')
        transition_time = section.get_attr_value('transition_time')
        interior = section.get_attr_value('interior')
        fog = MoodFog.from_gas(section.get_section('fog')) if section.get_section('fog') else None
        frustum = MoodFrustum.from_gas(section.get_section('frustum')) if section.get_section('frustum') else None
        rain = MoodRain.from_gas(section.get_section('rain')) if section.get_section('rain') else None
        wind = MoodWind.from_gas(section.get_section('wind')) if section.get_section('wind') else None
        return Mood(mood_name, transition_time, interior, fog, frustum, rain, wind)

    def to_gas(self) -> Section:
        items = [
            Attribute('interior', self.interior),
            Attribute('mood_name', self.mood_name),
            Attribute('transition_time', self.transition_time),
            self.fog.to_gas() if self.fog is not None else None,
            self.frustum.to_gas() if self.frustum is not None else None,
            self.rain.to_gas() if self.rain is not None else None,
            self.wind.to_gas() if self.wind is not None else None
        ]
        return Section('mood_setting*', [item for item in items if item is not None])


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

    def save(self):
        assert self.moods is not None
        for key, file_moods in self.moods.items():
            rel_path = key.replace('/', os.path.sep) + '.gas'
            path = os.path.join(self.gas_dir.path, rel_path)
            mood_file = GasFile(path)
            mood_file.get_gas().items = [mood.to_gas() for mood in file_moods]
            mood_file.save()
