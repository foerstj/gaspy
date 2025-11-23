class Linear:
    def __init__(self, m: float, c: float):
        self.m = m
        self.c = c

    def calc(self, x: float) -> float:
        return self.m * x + self.c


# Linear interpolation: y = m*x + c
# These values were calculated from the original Vanilla+LoA templates with help of linear_regression.py
STATS_SCALES = {
    'veteran': {
        'experience_value': {'m': 2.7294478234853, 'c': 47384.268270862616},
        'defense': {'m': 1.2669717784656467, 'c': 495.8891098661553},
        'damage_min': {'m': 1.2301856168375906, 'c': 149.56687745799772},
        'damage_max': {'m': 1.3366313768592097, 'c': 233.99580221295577},
        'life': {'m': 1.1543109377256886, 'c': 794.660177276828},
        'max_life': {'m': 1.1526143488489977, 'c': 817.6032890973673},
        'mana': {'m': 3.335112777243808, 'c': 110.37623376409657},
        'max_mana': {'m': 3.3350724019155766, 'c': 112.94806840229352},
        'strength': {'m': 1.7203858493956456, 'c': 7.567698816256484},
        'dexterity': {'m': 1.5647887517292667, 'c': 1.8614193305880598},
        'intelligence': {'m': 1.230540371506726, 'c': 0.7809801812339797},
        'melee': {'m': 0.838169991628117, 'c': 46.48586811007681},
        'ranged': {'m': 0.8756175554210393, 'c': 45.56939503447643},
        'combat_magic': {'m': 0.8394560001530021, 'c': 46.397685259368075},
        'nature_magic': {'m': 1.001758438243833, 'c': 43.3018325954095},
    },
    'elite': {
        'experience_value': {'m': 84.9857818614555, 'c': 1251291.5051795451},
        'defense': {'m': 1.5094955511315888, 'c': 814.6815076912454},
        'damage_min': {'m': 1.5278351913494315, 'c': 247.86957710778546},
        'damage_max': {'m': 1.598071549014744, 'c': 384.79773147117646},
        'life': {'m': 1.3072537148956231, 'c': 1336.259125593477},
        'max_life': {'m': 1.3044189742552963, 'c': 1374.883548585098},
        'mana': {'m': 4.879883388016795, 'c': 192.93794040223918},
        'max_mana': {'m': 4.87981572490678, 'c': 197.23259404071146},
        'strength': {'m': 2.2743986465024464, 'c': 11.760707642070486},
        'dexterity': {'m': 1.9962594815866939, 'c': 2.6771785749774093},
        'intelligence': {'m': 1.4032934245199629, 'c': 1.2250804260808346},
        'melee': {'m': 0.8375506547672154, 'c': 76.61572233112489},
        'ranged': {'m': 0.9238922091475847, 'c': 74.9875202677719},
        'combat_magic': {'m': 0.8631574249944861, 'c': 76.26455457168264},
        'nature_magic': {'m': 1.0342889033545652, 'c': 71.94760153316288},
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


class AbstractWLScaler:
    def scale_stat(self, attr_name: str, regular_value, regular_values: dict):
        return regular_value

    def scale_gold(self, attr_name: str, regular_value):
        return regular_value

    def scale_potion(self, regular_size: str):
        return regular_size

    def scale_pcontent_power(self, pcontent_category, regular_value):
        return regular_value


class AbstractWLStatsScaler:
    def scale_stat(self, attr_name: str, regular_value, regular_values: dict):
        return regular_value


class AbstractWLInventoryScaler:
    def scale_gold(self, attr_name: str, regular_value):
        return regular_value

    def scale_potion(self, regular_size: str):
        return regular_size

    def scale_pcontent_power(self, pcontent_category, regular_value):
        return regular_value


class CompositeWLScaler(AbstractWLScaler):
    def __init__(self, stats_scaler: AbstractWLStatsScaler, inventory_scaler: AbstractWLInventoryScaler):
        self.stats_scaler = stats_scaler
        self.inventory_scaler = inventory_scaler

    def scale_stat(self, attr_name: str, regular_value, regular_values: dict):
        return self.stats_scaler.scale_stat(attr_name, regular_value, regular_values)

    def scale_gold(self, attr_name: str, regular_value):
        return self.inventory_scaler.scale_gold(attr_name, regular_value)

    def scale_potion(self, regular_size: str):
        return self.inventory_scaler.scale_potion(regular_size)

    def scale_pcontent_power(self, pcontent_category, regular_value):
        return self.inventory_scaler.scale_pcontent_power(pcontent_category, regular_value)


def make_simple_linreg(stat_linreg: dict, stat: str):
    assert stat_linreg.keys() == {stat, 'c'}
    return {'m': stat_linreg[stat], 'c': stat_linreg['c']}


def make_simple_linregs(linregs: dict) -> dict:
    return {wl: {stat: make_simple_linreg(stat_linreg, stat) for stat, stat_linreg in wl_linregs.items()} for wl, wl_linregs in linregs.items()}


class SimpleWLStatsScaler(AbstractWLStatsScaler):
    def __init__(self, wl: str, stats_scales: dict = None):
        if stats_scales is None:
            stats_scales = STATS_SCALES
        self.stats_scalers = dict()
        for stat, scale in stats_scales[wl].items():
            assert scale.keys() == {'m', 'c'}
            self.stats_scalers[stat] = Linear(scale['m'], scale['c'])

    def scale_stat(self, attr_name: str, regular_value, regular_values: dict):
        if not regular_value:
            return regular_value  # keep zero values, e.g. xp of summons
        stats_scaler = self.stats_scalers[attr_name]
        return stats_scaler.calc(float(regular_value))


class SimpleWLInventoryScaler(AbstractWLInventoryScaler):
    def __init__(self, wl: str):
        self.gold_scalers = make_scalers(GOLD_SCALES, wl)
        self.pcontent_power_scalers = make_scalers(PCONTENT_POWER_SCALES, wl)
        self.potion_mapping = POTION_MAPPING[wl]

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


class MultiLinear:
    def __init__(self, coeffs: dict[str, float]):
        self.coeffs = coeffs

    def calc(self, x, values: dict[str, float]):
        # coeffs = {xp: 0.1, life: 4, c: 100}, values = {xp: 50, life: 10, mana: 7}
        # -> return 0.1*50 + 4*10 + 100 = 145
        assert 'm' not in values and 'c' not in values
        values = {**values, 'm': x, 'c': 1}
        return sum([coeff_value * (values[coeff_name] or 0) for coeff_name, coeff_value in self.coeffs.items()])


class MultiLinearWLStatsScaler(AbstractWLStatsScaler):
    def __init__(self, wl_stats_scales: dict):
        self.stats_scalers = {stat: MultiLinear(scale) for stat, scale in wl_stats_scales.items()}

    def scale_stat(self, attr_name: str, regular_value, regular_values: dict):
        if not regular_value:
            return regular_value  # keep zero values, e.g. xp of summons
        stats_scaler: MultiLinear = self.stats_scalers[attr_name]
        return stats_scaler.calc(float(regular_value), regular_values)
