from gas import Position, Hex, Quaternion, Section, Attribute


class Aspect:
    def __init__(self, scale_multiplier: float = None):
        self.scale_multiplier = scale_multiplier

    def make_gas(self) -> Section:
        attrs = []
        if self.scale_multiplier is not None:
            attrs.append(Attribute('scale_multiplier', self.scale_multiplier))
        return Section('aspect', attrs)


class Placement:
    def __init__(self, position: Position = None, orientation: Quaternion = None):
        self.position = position
        self.orientation = orientation

    def make_gas(self) -> Section:
        attrs = []
        if self.orientation is not None:
            attrs.append(Attribute('orientation', self.orientation))
        if self.position is not None:
            attrs.append(Attribute('position', self.position))
        return Section('placement', attrs)


class GameObjectData:
    def __init__(self, template_name: str, scid: Hex = None, aspect: Aspect = None, placement: Placement = None):
        self.template_name = template_name
        self.scid = scid
        self.aspect = aspect
        self.placement = placement

    def make_gas(self) -> Section:
        sections = []
        if self.aspect is not None:
            sections.append(self.aspect.make_gas())
        if self.placement is not None:
            sections.append(self.placement.make_gas())
        return Section(f't:{self.template_name},n:{self.scid}', sections)
