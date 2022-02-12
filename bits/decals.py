from __future__ import annotations

from gas.gas import Hex, Position, Section, Attribute, Gas
from gas.gas_file import GasFile


class Decal:
    def __init__(
            self,
            guid: Hex = None,
            texture: str = None,
            near_plane: float = 0.1,
            far_plane: float = 1.1,
            vertical_meters: float = None,
            horizontal_meters: float = None,
            decal_origin: Position = None,
            decal_orientation: list[float] = None,
            lod: float = 1.0
    ):
        if vertical_meters is None:
            vertical_meters = 4.0 / 1.1 * far_plane
        if horizontal_meters is None:
            horizontal_meters = 4.0 / 1.1 * far_plane
        self.guid = guid
        self.texture = texture
        self.near_plane = near_plane
        self.far_plane = far_plane
        self.vertical_meters = vertical_meters
        self.horizontal_meters = horizontal_meters
        self.decal_origin = decal_origin if decal_origin is not None else Position(0, 1, 0, None)
        self.decal_orientation = decal_orientation if decal_orientation is not None else [0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0]  # default orientation, no idea what these numbers mean
        self.lod = lod  # level of detail

    @classmethod
    def from_gas(cls, decal_section: Section) -> Decal:
        assert decal_section.header == 't:decal,n:*'
        guid = decal_section.get_attr_value('guid')
        texture = decal_section.get_attr_value('texture')
        near_plane = decal_section.get_attr_value('near_plane')
        far_plane = decal_section.get_attr_value('far_plane')
        vertical_meters = decal_section.get_attr_value('vertical_meters')
        horizontal_meters = decal_section.get_attr_value('horizontal_meters')
        decal_origin = Position.parse(decal_section.get_attr_value('decal_origin'))
        decal_orientation = [float(x) for x in decal_section.get_attr_value('decal_orientation').split(',')]
        lod = decal_section.get_attr_value('lod')
        return Decal(guid, texture, near_plane, far_plane, vertical_meters, horizontal_meters, decal_origin, decal_orientation, lod)

    def to_gas(self) -> Section:
        return Section('t:decal,n:*', [
            Attribute('decal_orientation', ','.join([str(x) for x in self.decal_orientation])),
            Attribute('decal_origin', str(self.decal_origin)),
            Attribute('far_plane', self.far_plane),
            Attribute('guid', self.guid),
            Attribute('horizontal_meters', self.horizontal_meters),
            Attribute('lod', self.lod),
            Attribute('near_plane', self.near_plane),
            Attribute('texture', self.texture),
            Attribute('vertical_meters', self.vertical_meters)
        ])


class DecalsGas:
    def __init__(self, decals: list[Decal]):
        self.decals = decals

    @classmethod
    def load(cls, gas_file: GasFile) -> DecalsGas:
        decals_section = gas_file.get_gas().get_section('decals')
        decals = [Decal.from_gas(decal_section) for decal_section in decals_section.get_sections('t:decal,n:*')]
        return DecalsGas(decals)

    def write_gas(self) -> Gas:
        return Gas([
            Section('decals', [decal.to_gas() for decal in self.decals])
        ])
