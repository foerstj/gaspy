from gas import Position, Hex, Quaternion


class Aspect:
    def __init__(self, scale_multiplier: float = None):
        self.scale_multiplier = scale_multiplier


class Placement:
    def __init__(self, position: Position = None, orientation: Quaternion = None):
        self.position = position
        self.orientation = orientation


class GameObjectData:
    def __init__(self, template_name: str, scid: Hex = None, aspect: Aspect = None, placement: Placement = None):
        self.template_name = template_name
        self.scid = scid
        self.aspect = aspect
        self.placement = placement
