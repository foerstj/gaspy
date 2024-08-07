import os

from bits.bits import Bits
from gas.gas_file import GasFile


class PerlinPlantDistribution:
    def __init__(self, perlin_offset, perlin_spread, seed_factor, plant_templates, size=None):
        self.perlin_offset = perlin_offset
        self.perlin_spread = perlin_spread
        self.seed_factor = seed_factor  # seeds/m²
        self.plant_templates = plant_templates
        if not size:
            size = (1, 1, 0)
        self.size_from = size[0]
        self.size_to = size[1] if len(size) > 1 else size[0]
        self.size_perlin = size[2] if len(size) > 2 else 0

    def __str__(self):
        return '{} {} {} {} {} {} {}'.format(self.perlin_offset, self.perlin_spread, self.seed_factor, self.plant_templates, self.size_from, self.size_to, self.size_perlin)


class PerlinPlantProfile:
    def __init__(self, plant_distributions: list[PerlinPlantDistribution]):
        self.plant_distributions = plant_distributions

    def sum_seed_factor(self):
        return sum([pd.seed_factor for pd in self.plant_distributions])

    def select_plant_distribution(self, seed_index):
        sum_seed_factor = 0
        for pd in self.plant_distributions:
            sum_seed_factor += pd.seed_factor
            if sum_seed_factor > seed_index:
                return pd
        return None


def load_plant_profile_gas(gas_file_path):
    plant_distributions = []
    gas_file = GasFile(gas_file_path)
    gas = gas_file.get_gas()
    ppp_section = gas.get_section('perlin_plant_profile')
    seed_default = ppp_section.get_attr_value('seed')
    templates_default = ppp_section.get_attr_value('templates')
    size_default = ppp_section.get_attr_value('size')
    for distro_section in ppp_section.get_sections('*'):
        seed = distro_section.get_attr_value('seed') or seed_default
        templates = distro_section.get_attr_value('templates') or templates_default
        size = distro_section.get_attr_value('size') or size_default
        seed_factor, perlin_offset, perlin_spread = [float(x) for x in seed.split(',')]
        plant_templates = templates.split()
        size = [float(s) for s in size.split()] if size else None
        distro = PerlinPlantDistribution(perlin_offset, perlin_spread, seed_factor, plant_templates, size)
        plant_distributions.append(distro)
    return PerlinPlantProfile(plant_distributions)


def load_plant_profile_txt(txt_file_path):
    plant_distributions = []
    with open(txt_file_path) as pf:
        for line in pf:
            if not line.strip() or line.startswith('#'):
                continue
            line_parts = line.split(',')
            (seed_factor, perlin_offset, perlin_spread, plant_templates) = line_parts[:4]
            size = line_parts[4] if len(line_parts) > 4 else None
            perlin_offset = float(perlin_offset)
            perlin_spread = float(perlin_spread)
            seed_factor = float(seed_factor)
            plant_templates = plant_templates.split()
            size = [float(s) for s in size.split()] if size else None
            distro = PerlinPlantDistribution(perlin_offset, perlin_spread, seed_factor, plant_templates, size)
            plant_distributions.append(distro)
    return PerlinPlantProfile(plant_distributions)


def load_perlin_plant_profile(name, bits_path=Bits.DSLOA_PATH) -> PerlinPlantProfile:
    for base_path in [os.path.join(bits_path, 'gaspy'), 'input']:
        file_path_base = os.path.join(base_path, 'perlin-distros', name)
        if os.path.exists(file_path_base+'.gas'):
            return load_plant_profile_gas(file_path_base+'.gas')
        if os.path.exists(file_path_base+'.txt'):
            return load_plant_profile_txt(file_path_base+'.txt')
