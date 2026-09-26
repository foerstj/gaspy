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


def get_xp(level: int, level_xp: list[int]) -> int:
    return level_xp[level]


def get_level_float(xp: int, level_xp: list[int]) -> float:
    base_level = get_level(xp, level_xp)
    base_level_xp = get_xp(base_level, level_xp)
    if base_level_xp == xp:
        return base_level
    next_level = base_level + 1
    next_level_xp = get_xp(next_level, level_xp)
    xp_to_next_level = next_level_xp - base_level_xp
    additional_xp = xp - base_level_xp
    return base_level + (additional_xp / xp_to_next_level)


def get_xp_float(level: float, level_xp: list[int]) -> float:
    base_level = int(level)
    base_level_xp = get_xp(base_level, level_xp)
    if base_level == level:
        return base_level_xp
    next_level = base_level + 1
    next_level_xp = get_xp(next_level, level_xp)
    xp_to_next_level = next_level_xp - base_level_xp
    additional_level = level - base_level
    return base_level_xp + (xp_to_next_level * additional_level)
