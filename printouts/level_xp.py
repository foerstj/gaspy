import os


def load_level_xp():
    level_file_path = os.path.join('input', 'XP Chart.csv')
    with open(level_file_path) as level_file:
        level_xp = [int(line.split(',')[1]) for line in level_file]
    return level_xp


def get_level(xp, level_xp):
    level = 0
    while level + 1 < len(level_xp) and level_xp[level + 1] <= xp:
        level += 1
    return level
