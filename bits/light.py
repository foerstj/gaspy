import math

from gas.gas import Section, Attribute
from gas.molecules import Hex


class PosDir:
    def __init__(self, x: float, y: float, z: float, node_guid: Hex = None):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.node_guid = node_guid

    @classmethod
    def from_gas_section(cls, section: Section):
        x = section.get_attr_value('x')
        y = section.get_attr_value('y')
        z = section.get_attr_value('z')
        node = section.get_attr_value('node')
        return PosDir(x, y, z, node)

    def to_gas_section(self, is_pos):
        return Section('position' if is_pos else 'direction', [
            Attribute('x', self.x),
            Attribute('y', self.y),
            Attribute('z', self.z),
            Attribute('node', self.node_guid),
        ])


class Light:
    def __init__(
            self,
            light_id: Hex = None,
            color: Hex = 0xffffffff,
            intensity: float = 1,
            draw_shadow: bool = False,
            occlude_geometry: bool = False,
            on_timer: bool = False,
            inner_radius: float = 0,
            outer_radius: float = 1,
            active: bool = True,
            affects_actors: bool = True,
            affects_items: bool = True,
            affects_terrain: bool = True
            ):
        if light_id is None:
            light_id = Hex.random()
        self.id = light_id

        self.color = color
        self.intensity = intensity
        self.draw_shadow = draw_shadow
        self.occlude_geometry = occlude_geometry
        self.on_timer = on_timer
        self.active = active
        self.affects_actors = affects_actors
        self.affects_items = affects_items
        self.affects_terrain = affects_terrain
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius

    def _to_gas_section(self, type_name, direction: PosDir = None, position: PosDir = None) -> Section:
        section = Section(f't:{type_name},n:light_{self.id.to_str_lower()}', [
            Attribute('active', self.active),
            Attribute('affects_actors', self.affects_actors),
            Attribute('affects_items', self.affects_items),
            Attribute('affects_terrain', self.affects_terrain),
            Attribute('color', self.color),
            Attribute('draw_shadow', self.draw_shadow),
            Attribute('inner_radius', float(self.inner_radius)),
            Attribute('intensity', float(self.intensity)),
            Attribute('occlude_geometry', self.occlude_geometry),
            Attribute('on_timer', self.on_timer),
            Attribute('outer_radius', float(self.outer_radius))
        ])
        if direction is not None:
            section.items.append(direction.to_gas_section(False))
        if position is not None:
            section.items.append(position.to_gas_section(True))
        return section

    def to_gas_section(self) -> Section:
        raise NotImplementedError()  # to be overwritten by subclasses


class DirectionalLight(Light):
    def __init__(self, dl_id: Hex = None, color: Hex = 0xffffffff, intensity: float = 1, draw_shadow: bool = False, occlude_geometry: bool = False, on_timer: bool = False,
                 direction: PosDir = PosDir(0, 1, 0)):
        super().__init__(dl_id, color, intensity, draw_shadow, occlude_geometry, on_timer, inner_radius=0, outer_radius=0)
        self.direction = direction  # pointing where the light comes from (relative to north vector); node guid from target node

    def to_gas_section(self) -> Section:
        return self._to_gas_section('directional', direction=self.direction)

    @classmethod
    def direction_from_orbit_and_azimuth(cls, orbit_deg: int, azimuth_deg: int) -> PosDir:
        """ Orbit is degrees *counter-clockwise* from *north vector*, azimuth is degrees up from ground. """
        assert 0 <= orbit_deg < 360
        assert 0 <= azimuth_deg <= 90
        # only allowing the above inputs as only these can be entered in the SE GUI either.
        orbit_rad = orbit_deg / 360 * math.tau
        azimuth_rad = azimuth_deg / 360 * math.tau
        x = math.cos(orbit_rad)
        z = -math.sin(orbit_rad)
        y = math.sin(azimuth_rad)
        x *= math.cos(azimuth_rad)
        z *= math.cos(azimuth_rad)
        return PosDir(x, y, z)


class PointLight(Light):
    def __init__(self, dl_id: Hex = None, color: Hex = 0xffffffff, intensity: float = 1, position: PosDir = PosDir(0, 0, 0)):
        super().__init__(dl_id, color, intensity, inner_radius=0, outer_radius=20)
        self.position = position

    def to_gas_section(self) -> Section:
        return self._to_gas_section('point', position=self.position)


class SpotLight(Light):
    def __init__(self, dl_id: Hex = None, color: Hex = 0xffffffff, intensity: float = 1, position: PosDir = PosDir(0, 0, 0), direction: PosDir = PosDir(0, 1, 0)):
        super().__init__(dl_id, color, intensity, inner_radius=0, outer_radius=1)
        self.position = position
        self.direction = direction

    def to_gas_section(self) -> Section:
        return self._to_gas_section('spot', direction=self.direction, position=self.position)
