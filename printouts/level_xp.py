from printouts.csv import read_csv


def load_level_xp() -> list[int]:
    csv_data = read_csv('XP Chart', ',')
    level_xp = [int(line[1]) for line in csv_data]
    return level_xp


def get_level(xp: int, level_xp: list[int]) -> int:
    level = 0
    while level + 1 < len(level_xp) and level_xp[level + 1] <= xp:
        level += 1
    return level
