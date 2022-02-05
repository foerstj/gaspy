import os


class PlantDistribution:
    def __init__(self, perlin_offset, perlin_spread, seed_factor, plant_templates, size=None):
        self.perlin_offset = perlin_offset
        self.perlin_spread = perlin_spread
        self.seed_factor = seed_factor  # seeds/m²
        self.plant_templates = plant_templates
        if not size:
            size = (1, 1, 0)
        self.size_from = size[0]
        self.size_to = size[1]
        self.size_perlin = size[2] if len(size) > 2 else 0

    def __str__(self):
        return '{} {} {} {} {} {} {}'.format(self.perlin_offset, self.perlin_spread, self.seed_factor, self.plant_templates, self.size_from, self.size_to, self.size_perlin)


class PlantsProfile:
    def __init__(self, plant_distributions: list[PlantDistribution]):
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


def load_plants_profile_txt(txt_file_path):
    plants_profile = []
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
            plants_profile.append(PlantDistribution(perlin_offset, perlin_spread, seed_factor, plant_templates, size))
    return PlantsProfile(plants_profile)


def load_plants_profile(name) -> PlantsProfile:
    file_path = os.path.join('input', 'perlin-distros', f'{name}.txt')
    plants_profile = load_plants_profile_txt(file_path)
    return plants_profile
