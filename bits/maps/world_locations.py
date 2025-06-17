class Location:
    def __init__(self, id: int, screen_name: str):
        self.id: int = id
        self.screen_name = screen_name


class WorldLocations:
    def __init__(self, locations: dict[str, Location]):
        self.locations: dict[str, Location] = locations

    def screen_names_by_key(self) -> dict[str, str]:
        return {k: v.screen_name for k, v in self.locations.items()}

    def new_location_id(self) -> int:
        return max([x.id for x in self.locations.values()]) + 1
