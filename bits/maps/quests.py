class Quest:
    def __init__(self, screen_name: str):
        self.screen_name = screen_name


class Quests:
    def __init__(self, quests: dict[str, Quest]):
        self.quests: dict[str, Quest] = quests
