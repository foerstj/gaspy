class Linear:
    def __init__(self, m: float, c: float):
        self.m = m
        self.c = c

    def calc(self, x: float) -> float:
        return self.m * x + self.c


# Linear interpolation: y = m*x + c
# These values were interpolated from the original templates with help of stats.py and a spreadsheet app
STATS_SCALES = {
    'veteran': {
        'experience_value': {'m': 2.771, 'c': 42530},
        'defense': {'m': 1.265, 'c': 496},
        'damage_min': {'m': 1.281, 'c': 142.2},
        'damage_max': {'m': 1.405, 'c': 222.4},
        'life': {'m': 1.154, 'c': 794.5},
        'max_life': {'m': 1.153, 'c': 817.4},
        'mana': {'m': 3.335, 'c': 104.5},
        'max_mana': {'m': 3.335, 'c': 107},
        'strength': {'m': 1.716, 'c': 7.6},
        'dexterity': {'m': 1.565, 'c': 1.846},
        'intelligence': {'m': 1.231, 'c': 0.773},
        'melee': {'m': 0.844, 'c': 46.28},
        'ranged': {'m': 0.876, 'c': 45.57},
        'combat_magic': {'m': 0.919, 'c': 43.28},
        'nature_magic': {'m': 1.002, 'c': 43.3},
    },
    'elite': {
        'experience_value': {'m': 86.08, 'c': 1122000},
        'defense': {'m': 1.509, 'c': 814.7},
        'damage_min': {'m': 1.616, 'c': 235.5},
        'damage_max': {'m': 1.716, 'c': 365.5},
        'life': {'m': 1.307, 'c': 1336},
        'max_life': {'m': 1.304, 'c': 1375},
        'mana': {'m': 4.88, 'c': 186.7},
        'max_mana': {'m': 4.88, 'c': 190.9},
        'strength': {'m': 2.276, 'c': 11.71},
        'dexterity': {'m': 1.997, 'c': 2.656},
        'intelligence': {'m': 1.404, 'c': 1.215},
        'melee': {'m': 0.848, 'c': 76.26},
        'ranged': {'m': 0.924, 'c': 74.99},
        'combat_magic': {'m': 0.995, 'c': 71.14},
        'nature_magic': {'m': 1.034, 'c': 71.95}
    },
}
GOLD_SCALES = {
    'veteran': {
        'min': {'m': 4.38, 'c': 34480},
        'max': {'m': 2.134, 'c': 61520},
    },
    'elite': {
        'min': {'m': 10.89, 'c': 155600},
        'max': {'m': 4.027, 'c': 256600},
    },
}
PCONTENT_POWER_SCALES = {
    'veteran': {
        'spell': {'m': 1.26, 'c': 28.71},
        'armor': {'m': 1.484, 'c': 197.1},
        'jewelry': {'m': 0.853, 'c': 105.3},
        'weapon': {'m': 1.047, 'c': 115.4},
        'spellbook': {'m': 0.624, 'c': 118.8},
        '*': {'m': 1.031, 'c': 114.5},
    },
    'elite': {
        'spell': {'m': 1.401, 'c': 46.86},
        'armor': {'m': 1.768, 'c': 324.3},
        'jewelry': {'m': 0.794, 'c': 169.9},
        'weapon': {'m': 1.064, 'c': 188.5},
        'spellbook': {'m': 0.32, 'c': 188.4},
        '*': {'m': 1.056, 'c': 186},
    },
}


def make_scalers(scales: dict, wl: str):
    scalers = dict()
    for attr, wl_scales in scales[wl].items():
        scalers[attr] = Linear(wl_scales['m'], wl_scales['c'])
    return scalers


POTION_MAPPING = {
    'veteran': {
        'small': 'medium',
        'medium': 'large',
        'large': 'super'
    },
    'elite': {
        'small': 'large',
        'medium': 'super',
        'large': 'super'
    }
}


class WLScaler:
    def __init__(self, wl: str):
        assert wl in ['veteran', 'elite']
        self.wl = wl
        self.stats_scalers = make_scalers(STATS_SCALES, wl)
        self.gold_scalers = make_scalers(GOLD_SCALES, wl)
        self.pcontent_power_scalers = make_scalers(PCONTENT_POWER_SCALES, wl)
        self.potion_mapping = POTION_MAPPING[wl]

    def scale_stat(self, attr_name: str, regular_value):
        if not regular_value:
            return regular_value  # keep zero values, e.g. xp of summons
        stats_scaler = self.stats_scalers[attr_name]
        return stats_scaler.calc(float(regular_value))

    def scale_gold(self, attr_name: str, regular_value):
        gold_scaler = self.gold_scalers[attr_name]
        return gold_scaler.calc(float(regular_value))

    def scale_potion(self, regular_size: str):
        if regular_size not in self.potion_mapping:
            return regular_size
        return self.potion_mapping[regular_size]

    def scale_pcontent_power(self, pcontent_category, regular_value):
        pcontent_power_scaler = self.pcontent_power_scalers[pcontent_category]
        return pcontent_power_scaler.calc(float(regular_value))
