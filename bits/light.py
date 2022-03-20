import math

from gas.molecules import Hex


class DirectionalLight:
    def __init__(
            self,
            dl_id: Hex = None,
            color: Hex = 0xffffffff,
            draw_shadow: bool = False,
            intensity: float = 1,
            occlude_geometry: bool = False,
            on_timer: bool = False,
            direction: (float, float, float) = (0, 1, 0)):
        if dl_id is None:
            dl_id = Hex.random()
        self.id = dl_id
        self.color = color
        self.draw_shadow = draw_shadow
        self.intensity = intensity
        self.occlude_geometry = occlude_geometry
        self.on_timer = on_timer
        self.direction = direction  # x,y,z vector pointing where the light comes from

    @classmethod
    def direction_from_orbit_and_azimuth(cls, orbit_deg: int, azimuth_deg: int) -> (float, float, float):
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
        return x, y, z
