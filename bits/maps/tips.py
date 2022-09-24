class Tip:
    def __init__(self, texts: list[str]):
        self.texts = texts


class Tips:
    def __init__(self, tips: dict[str, Tip]):
        self.tips = tips
