from gas.gas import Position, Hex, Quaternion, Section, Attribute


class Aspect:
    def __init__(self, scale_multiplier: float = None):
        self.scale_multiplier = scale_multiplier

    def make_gas(self) -> Section:
        attrs = []
        if self.scale_multiplier is not None:
            attrs.append(Attribute('scale_multiplier', self.scale_multiplier))
        return Section('aspect', attrs)


class TriggerInstance:
    def __init__(self, condition: str = None, action: str = None):
        self.condition = condition
        self.action = action

    def make_gas(self) -> Section:
        return Section('*', [
            Attribute('condition*', self.condition),
            Attribute('action*', self.action)
        ])


class Common:
    def __init__(self, instance_triggers: list = None):
        self.instance_triggers = instance_triggers

    def make_gas(self) -> Section:
        sections = []
        if self.instance_triggers is not None:
            sections.append(Section('instance_triggers', [ti.make_gas() for ti in self.instance_triggers]))
        return Section('common', sections)


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
    def __init__(self, template_name: str, scid: Hex = None, aspect: Aspect = None, common: Common = None, placement: Placement = None):
        self.template_name = template_name
        self.scid = scid
        self.aspect = aspect
        self.common = common
        self.placement = placement

    def make_gas(self) -> Section:
        sections = []
        if self.aspect is not None:
            sections.append(self.aspect.make_gas())
        if self.common is not None:
            sections.append(self.common.make_gas())
        if self.placement is not None:
            sections.append(self.placement.make_gas())
        return Section(f't:{self.template_name},n:{self.scid}', sections)
