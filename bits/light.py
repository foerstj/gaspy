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
            draw_shadow: bool = False,
            intensity: float = 1,
            occlude_geometry: bool = False,
            on_timer: bool = False):
        if light_id is None:
            light_id = Hex.random()
        self.id = light_id
        self.color = color
        self.draw_shadow = draw_shadow
        self.intensity = intensity
        self.occlude_geometry = occlude_geometry
        self.on_timer = on_timer
        self.active = True
        self.affects_actors = True
        self.affects_items = True
        self.affects_terrain = True
        self.inner_radius = 0
        self.outer_radius = 1


class DirectionalLight(Light):
    def __init__(self, dl_id: Hex = None, color: Hex = 0xffffffff, draw_shadow: bool = False, intensity: float = 1, occlude_geometry: bool = False, on_timer: bool = False,
                 direction: PosDir = PosDir(0, 1, 0)):
        super().__init__(dl_id, color, draw_shadow, intensity, occlude_geometry, on_timer)
        self.direction = direction  # pointing where the light comes from (relative to north vector); node guid from target node

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