import os.path
from pathlib import Path

from bits.gas_dir_handler import GasDirHandler
from gas.color import Color
from gas.gas import Section, Attribute
from gas.gas_dir import GasDir
from gas.gas_file import GasFile
from gas.molecules import Hex


def non_null_attrs(attrs: list[Attribute], sort=False) -> list[Attribute]:
    attrs = [attr for attr in attrs if attr is not None and attr.value is not None]
    if sort:
        attrs.sort(key=lambda x: x.name)
    return attrs


class MoodFog:
    def __init__(self, color: Color, density: float, near_dist: float, far_dist: float, lowdetail_near_dist: float, lowdetail_far_dist: float):
        self.color = color
        self.density = density
        self.near_dist = near_dist
        self.far_dist = far_dist
        self.lowdetail_near_dist = lowdetail_near_dist
        self.lowdetails_far_dist = lowdetail_far_dist

    @classmethod
    def parse_color(cls, color_value) -> Color or None:
        if color_value is None:
            return None
        if isinstance(color_value, str):
            color_value = Hex.parse(color_value)
        return Color(color_value)

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'fog'
        return MoodFog(
            cls.parse_color(section.get_attr_value('fog_color')),
            section.get_attr_value('fog_density'),
            parse_float(section.get_attr_value('fog_near_dist')),
            parse_float(section.get_attr_value('fog_far_dist')),
            parse_float(section.get_attr_value('fog_lowdetail_near_dist')),
            parse_float(section.get_attr_value('fog_lowdetail_far_dist'))
        )

    def to_gas(self) -> Section:
        return Section('fog', non_null_attrs([
            Attribute('fog_near_dist', self.near_dist),
            Attribute('fog_far_dist', self.far_dist),
            Attribute('fog_lowdetail_near_dist', self.lowdetail_near_dist),
            Attribute('fog_lowdetail_far_dist', self.lowdetails_far_dist),
            Attribute('fog_color', self.color),
            Attribute('fog_density', self.density),
        ]))


class MoodFrustum:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'frustum'
        return MoodFrustum(
            parse_float(section.get_attr_value('frustum_width')),
            parse_float(section.get_attr_value('frustum_height')),
        )

    def to_gas(self) -> Section:
        return Section('frustum', non_null_attrs([
            Attribute('frustum_width', self.width),
            Attribute('frustum_height', self.height),
        ]))


class MoodMusic:
    class Sub:
        def __init__(self, track: str = None, intro_delay: float = None, repeat_delay: float = None):
            self.track = track
            self.intro_delay = intro_delay
            self.repeat_delay = repeat_delay

        @classmethod
        def from_gas(cls, section: Section, prefix: str):
            return MoodMusic.Sub(
                section.get_attr_value(prefix + 'track'),
                section.get_attr_value(prefix + 'intro_delay'),
                section.get_attr_value(prefix + 'repeat_delay')
            )

        def to_gas(self, prefix: str) -> list[Attribute]:
            return [
                Attribute(prefix + 'intro_delay', self.intro_delay),
                Attribute(prefix + 'repeat_delay', self.repeat_delay),
                Attribute(prefix + 'track', self.track),
            ]

    def __init__(self, ambient: Sub = None, standard: Sub = None, battle: Sub = None, room_type: str = None):
        self.ambient = ambient if ambient is not None else MoodMusic.Sub()
        self.standard = standard if standard is not None else MoodMusic.Sub()
        self.battle = battle if battle is not None else MoodMusic.Sub()
        self.room_type = room_type

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'music'
        return MoodMusic(
            MoodMusic.Sub.from_gas(section, 'ambient_'),
            MoodMusic.Sub.from_gas(section, 'standard_'),
            MoodMusic.Sub.from_gas(section, 'battle_'),
            section.get_attr_value('room_type')
        )

    def to_gas(self) -> Section:
        return Section('music', non_null_attrs(self.ambient.to_gas('ambient_') + self.standard.to_gas('standard_') + self.battle.to_gas('battle_') + [
            Attribute('room_type', self.room_type)
        ]))


def parse_float(value):
    if isinstance(value, str):
        if value.endswith('f'):
            value = value[:-1]
        value = float(value)
    return value


def parse_bool(value):
    if isinstance(value, str):
        value = Attribute.parse_bool(value)
    return value


class MoodRain:
    def __init__(self, density: float, lightning: bool):
        self.density = density
        self.lightning = lightning

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'rain'
        density = parse_float(section.get_attr_value('rain_density'))
        lightning = section.get_attr_value('lightning')
        if isinstance(lightning, str):
            lightning = Attribute.parse_bool(lightning)
        return MoodRain(density, lightning)

    def to_gas(self) -> Section:
        return Section('rain', non_null_attrs([
            Attribute('rain_density', self.density),
            Attribute('lightning', self.lightning)
        ]))


class MoodSnow:
    def __init__(self, density: float):
        self.density = density

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'snow'
        density = parse_float(section.get_attr_value('snow_density'))
        return MoodSnow(density)

    def to_gas(self) -> Section:
        return Section('snow', non_null_attrs([
            Attribute('snow_density', self.density)
        ]))


class MoodSun:
    def __init__(self, sun: dict[str, Hex]):
        self.sun = sun

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'sun'
        sun = dict()
        for sub_section in section.get_sections():
            sun[sub_section.header] = Hex.parse(sub_section.get_attr_value('color'))
        return MoodSun(sun)

    def to_gas(self) -> Section:
        return Section('sun', [
            Section(time, [
                Attribute('color', color.to_str_upper())
            ]) for time, color in self.sun.items()
        ])


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
    def __init__(self, mood_name: str, transition_time: float, interior: bool, fog: MoodFog, frustum: MoodFrustum, music: MoodMusic, rain: MoodRain, snow: MoodSnow, sun: MoodSun, wind: MoodWind):
        self.mood_name = mood_name
        self.transition_time = transition_time
        self.interior = interior
        self.fog = fog
        self.frustum = frustum
        self.music = music
        self.rain = rain
        self.snow = snow
        self.sun = sun
        self.wind = wind

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'mood_setting*'
        mood_name = section.get_attr_value('mood_name')
        transition_time = parse_float(section.get_attr_value('transition_time'))
        interior = parse_bool(section.get_attr_value('interior'))
        fog = MoodFog.from_gas(section.get_section('fog')) if section.get_section('fog') else None
        frustum = MoodFrustum.from_gas(section.get_section('frustum')) if section.get_section('frustum') else None
        music = MoodMusic.from_gas(section.get_section('music')) if section.get_section('music') else None
        rain = MoodRain.from_gas(section.get_section('rain')) if section.get_section('rain') else None
        snow = MoodSnow.from_gas(section.get_section('snow')) if section.get_section('snow') else None
        sun = MoodSun.from_gas(section.get_section('sun')) if section.get_section('sun') else None
        wind = MoodWind.from_gas(section.get_section('wind')) if section.get_section('wind') else None
        return Mood(mood_name, transition_time, interior, fog, frustum, music, rain, snow, sun, wind)

    def to_gas(self) -> Section:
        items = [
            Attribute('mood_name', self.mood_name),
            Attribute('transition_time', self.transition_time),
            Attribute('interior', self.interior),
            # order based on vanilla moods, but they don't really have a consistent order
            self.frustum.to_gas() if self.frustum is not None else None,
            self.sun.to_gas() if self.sun is not None else None,
            self.fog.to_gas() if self.fog is not None else None,
            self.rain.to_gas() if self.rain is not None else None,
            self.snow.to_gas() if self.snow is not None else None,
            self.wind.to_gas() if self.wind is not None else None,
            self.music.to_gas() if self.music is not None else None,
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
            if key == 'timeofday':
                continue
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
