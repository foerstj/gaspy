class QuestUpdate:
    def __init__(self, description: str):
        self.description = description


class Quest:
    def __init__(self, screen_name: str, updates: list[QuestUpdate]):
        self.screen_name = screen_name
        self.updates = updates


class Quests:
    def __init__(self, quests: dict[str, Quest]):
        self.quests: dict[str, Quest] = quests
