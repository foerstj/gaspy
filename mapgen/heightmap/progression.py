from __future__ import annotations

import random

from mapgen.flat.mapgen_plants import load_plants_profile


class SingleProfile:
    def __init__(self, profile_name):
        self.profile = load_plants_profile(profile_name)

    def max_sum_seed_factor(self):  # end of recursion
        return self.profile.sum_seed_factor()

    def choose_profile(self, _, __):  # end of recursion
        return self.profile


class ProfileVariants:
    def __init__(self, a: SingleProfile | ProfileVariants | None, b: SingleProfile | ProfileVariants | None, perlin, tx='sharp'):
        assert tx in ['sharp', 'blur', 'gap']
        self.a = a
        self.b = b
        self.perlin = perlin
        self.tx = tx

    def max_sum_seed_factor(self):
        profiles = [p for p in [self.a, self.b] if p is not None]
        if len(profiles) == 0:
            return 0
        return max([p.max_sum_seed_factor() for p in profiles])

    def choose_profile(self, map_norm_x, map_norm_z):
        variant_perlin_value = self.perlin([map_norm_x, map_norm_z])
        variant_a_probability = variant_perlin_value * 16 + 0.5
        if variant_a_probability < 0:
            p = self.b
        elif variant_a_probability > 1:
            p = self.a
        else:
            if self.tx == 'blur':
                choose_a = random.uniform(0, 1) < variant_a_probability
                p = self.a if choose_a else self.b
            elif self.tx == 'sharp':
                p = self.a if variant_a_probability > 0.5 else self.b
            else:  # tx == gap
                p = None
        if p is None:
            return None
        return p.choose_profile(map_norm_x, map_norm_z)  # recurse into sub-variants


class ProgressionStep:
    COUNT = 1

    def __init__(self, plants_profile: SingleProfile | ProfileVariants | None, enemies_profile: SingleProfile | ProfileVariants = None):
        self.plants_profile = plants_profile
        self.enemies_profile = enemies_profile
        self.count = ProgressionStep.COUNT  # just for color value for image printout
        ProgressionStep.COUNT += 1

    def get_profile(self, plants=True):
        return self.plants_profile if plants else self.enemies_profile

    def max_sum_seed_factor(self, plants=True):
        profile = self.get_profile(plants)
        if profile is None:
            return 0
        return profile.max_sum_seed_factor()


class Progression:
    def __init__(self, steps: list[tuple[float, ProgressionStep | Progression]], direction, perlin_curve, perlin_curve_factor, tx_factor):
        self.steps = steps
        assert direction in ['sw2ne', 'nw2se']
        self.direction = direction
        self.perlin_curve = perlin_curve
        self.perlin_curve_factor = perlin_curve_factor
        self.tx_factor = tx_factor

    def max_sum_seed_factor(self, plants=True) -> float:
        return max([step.max_sum_seed_factor(plants) for _, step in self.steps])

    def choose_progression_step(self, map_norm_x, map_norm_z, tx='sharp') -> ProgressionStep:
        assert tx in ['blur', 'sharp', 'gap']
        curve_perlin_value = self.perlin_curve([map_norm_x, map_norm_z])
        assert self.direction in ['sw2ne', 'nw2se']
        if self.direction == 'sw2ne':
            progression_value = (map_norm_x + (1 - map_norm_z)) / 2  # southwest=0 -> northeast=1
        else:
            progression_value = (map_norm_x + map_norm_z) / 2  # northwest=0 -> southeast=1
        progression_value += curve_perlin_value / self.perlin_curve_factor  # curve the border
        if tx == 'blur':
            # blur the border by random fuzziness - used for plants
            tx_random_value = random.uniform(-0.5, 0.5) * self.tx_factor
            progression_value += tx_random_value  # blur the border
        chosen_step = None
        for step_value, step in self.steps:
            chosen_step = step
            if tx == 'gap':
                # leave a gap between steps - used for enemies
                if step_value != 1 and abs(step_value - progression_value) < self.tx_factor/2:
                    chosen_step = None
                    break
            if step_value > progression_value:
                break
        if isinstance(chosen_step, Progression):
            chosen_step = chosen_step.choose_progression_step(map_norm_x, map_norm_z, tx)  # recurse into nested progression
        return chosen_step
