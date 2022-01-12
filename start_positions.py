from gas import Position


class Camera:
    def __init__(self, azimuth, distance, orbit, position):
        self.azimuth: float = azimuth
        self.distance: float = distance
        self.orbit: float = orbit
        self.position: Position = position


class StartPos:
    def __init__(self, id, position, camera):
        self.id: int = id
        self.position: Position = position
        self.camera: Camera = camera


class StartGroup:
    def __init__(self, description, dev_only=None, id=None, screen_name=None, start_positions=None):
        self.description: str = description
        self.dev_only: bool = dev_only
        self.id: int = id
        self.screen_name: str = screen_name
        self.start_positions: list[StartPos] = start_positions


class StartPositions:
    def __init__(self, start_groups: dict[str, StartGroup], default: str):
        self.start_groups: dict[str, StartGroup] = start_groups
        self.default: str = default

    def new_start_group_id(self) -> int:
        return max([g.id for g in self.start_groups.values()]) + 1
