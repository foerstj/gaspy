from __future__ import annotations

import os
import random

from perlin_noise import PerlinNoise

from gas.gas import Gas, Section
from gas.gas_file import GasFile
from mapgen.flat.perlin_plant_profile import load_perlin_plant_profile


class SingleProfile:
    COUNT = 1

    def __init__(self, profile_name):
        self.profile = load_perlin_plant_profile(profile_name)
        self.count = SingleProfile.COUNT  # just for color value for image printout
        SingleProfile.COUNT += 1

    def hydrate(self, _):  # end of recursion
        pass

    def max_sum_seed_factor(self):  # end of recursion
        return self.profile.sum_seed_factor()

    def choose_profile(self, _, __) -> SingleProfile:  # end of recursion
        return self


class ProfileVariants:
    def __init__(self, a: SingleProfile | ProfileVariants | None, b: SingleProfile | ProfileVariants | None, perlin_name, tx='sharp'):
        assert tx in ['sharp', 'blur', 'gap']
        self.a = a
        self.b = b
        self.perlin_name = perlin_name
        self.perlin = None
        self.tx = tx

    def hydrate(self, perlins: dict[str, PerlinNoise]):
        self.perlin = perlins[self.perlin_name]
        if self.a is not None:
            self.a.hydrate(perlins)
        if self.b is not None:
            self.b.hydrate(perlins)

    def max_sum_seed_factor(self):
        profiles = [p for p in [self.a, self.b] if p is not None]
        if len(profiles) == 0:
            return 0
        return max([p.max_sum_seed_factor() for p in profiles])

    def choose_profile(self, map_norm_x, map_norm_z) -> SingleProfile | None:
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

    def hydrate(self, perlins: dict[str, PerlinNoise], _):
        if self.plants_profile is not None:
            self.plants_profile.hydrate(perlins)
        if self.enemies_profile is not None:
            self.enemies_profile.hydrate(perlins)

    def get_profile(self, plants=True):
        return self.plants_profile if plants else self.enemies_profile

    def max_sum_seed_factor(self, plants=True):
        profile = self.get_profile(plants)
        if profile is None:
            return 0
        return profile.max_sum_seed_factor()

    @classmethod
    def load_profiles(cls, parent_section: Section, name) -> SingleProfile | ProfileVariants | None:
        profiles_section = parent_section.get_section(name)
        if profiles_section is None:
            return None
        profile_attr = profiles_section.get_attr('profile')
        if profile_attr is not None:
            profile_name = profile_attr.value
            return SingleProfile(profile_name)
        perlin_name = profiles_section.get_attr_value('perlin').strip()
        tx = profiles_section.get_attr_value('tx').strip()
        variant_a = cls.load_profiles(profiles_section, 'a')
        variant_b = cls.load_profiles(profiles_section, 'b')
        return ProfileVariants(variant_a, variant_b, perlin_name, tx)

    @classmethod
    def load_gas(cls, section: Section) -> ProgressionStep:
        plants_profile = cls.load_profiles(section, 'plants')
        enemies_profile = cls.load_profiles(section, 'enemies')
        return ProgressionStep(plants_profile, enemies_profile)


class Progression:
    def __init__(self, steps: list[tuple[float, ProgressionStep | Progression]], direction: str, perlin_curve_name: str, perlin_curve_factor, tx_factor):
        self.steps = steps
        assert direction in ['sw2ne', 'nw2se']
        self.direction = direction
        self.perlin_curve_name = perlin_curve_name
        self.perlin_curve = None
        self.perlin_curve_factor = perlin_curve_factor
        self.tx_factor = tx_factor
        self.max_size_xz = 0

    def hydrate(self, perlins: dict[str, PerlinNoise], max_size_xz):
        self.perlin_curve = perlins[self.perlin_curve_name]
        self.max_size_xz = max_size_xz
        for step in self.steps:
            step[1].hydrate(perlins, max_size_xz)

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
        progression_value += curve_perlin_value * self.perlin_curve_factor/self.max_size_xz  # curve the border
        if tx == 'blur':
            # blur the border by random fuzziness - used for plants
            tx_random_value = random.uniform(-0.5, 0.5) * self.tx_factor/self.max_size_xz * 2  # blur area is twice as wide as gap area
            progression_value += tx_random_value  # blur the border
        chosen_step = None
        for step_value, step in self.steps:
            chosen_step = step
            if tx == 'gap':
                # leave a gap between steps - used for enemies
                if step_value != 1 and abs(step_value - progression_value) < self.tx_factor/self.max_size_xz/2:
                    chosen_step = None
                    break
            if step_value > progression_value:
                break
        if isinstance(chosen_step, Progression):
            chosen_step = chosen_step.choose_progression_step(map_norm_x, map_norm_z, tx)  # recurse into nested progression
        return chosen_step

    @classmethod
    def load_gas(cls, gas: Gas) -> Progression:
        ppp_section = gas.get_section('perlin_plant_progression')
        direction = ppp_section.get_attr_value('direction')
        assert direction in ['sw2ne', 'nw2se']
        perlin_name = ppp_section.get_attr_value('perlin').strip()
        perlin_curve_factor = float(ppp_section.get_attr_value('perlin_curve_factor'))
        tx_factor = float(ppp_section.get_attr_value('tx_factor'))
        steps_section = ppp_section.get_section('steps')
        steps = []
        for step_section in steps_section.get_sections():
            step_value = float(step_section.header)
            sub_progression_section = step_section.get_section('perlin_plant_progression')
            if sub_progression_section is not None:
                step = cls.load_gas(step_section)
            else:
                step = ProgressionStep.load_gas(step_section)
            steps.append((step_value, step))
        return Progression(steps, direction, perlin_name, perlin_curve_factor, tx_factor)

    @classmethod
    def load(cls, name: str) -> Progression:
        file_path = os.path.join('input', f'{name}.progression.gas')
        assert os.path.isfile(file_path)
        return cls.load_gas(GasFile(file_path).get_gas())
