import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.common import parse_bool_value, parse_value


GENERIC_TEXTURES = ['b_w_weapons']


def frags(bits_path: str):
    print('parsing templates...')
    bits = Bits(bits_path)
    GasParser.get_instance().print_warnings = False
    bits.templates.get_templates()
    print('evaluating frags...')

    # first pass - build enemies list & frag_usages dict
    frag_usages: dict[str, list[Template]] = dict()
    enemies: list[Template] = list()
    all_enemies = bits.templates.get_enemy_templates()
    for enemy in all_enemies.values():
        if enemy.wl_prefix is not None:
            continue
        gib_gore_good = parse_bool_value(enemy.compute_value('physics', 'gib_gore_good'))
        ewk_str = enemy.compute_value('physics', 'explode_when_killed')
        explode_when_killed = False if ewk_str is None else parse_bool_value(ewk_str.split()[0])  # missing semicolon in krug_dog_skeleton
        if not gib_gore_good and not explode_when_killed:
            continue
        break_particulate = enemy.resolve_section('physics', 'break_particulate')
        if break_particulate is None:
            continue
        enemies.append(enemy)

        frag_names = [a.name for a in break_particulate.get_attrs()]
        for frag_name in frag_names:
            if frag_name not in frag_usages:
                frag_usages[frag_name] = list()
            usages = frag_usages[frag_name]
            usages.append(enemy)

    # second pass - check for mismatches
    num_enemies_with_mismatches = 0
    for enemy in enemies:
        actor_texture = enemy.compute_value('aspect', 'textures', '0')
        actor_scale = parse_value(enemy.compute_value('aspect', 'scale_base')) or 1.0
        actor_model = enemy.compute_value('aspect', 'model')
        assert actor_model is not None, enemy.name

        break_particulate = enemy.resolve_section('physics', 'break_particulate')
        frag_names = [a.name for a in break_particulate.get_attrs()]
        frag_templates = [bits.templates.templates[f.lower()] for f in frag_names]

        frag_textures = set([f.compute_value('aspect', 'textures', '0') for f in frag_templates])
        frag_scales = set([parse_value(f.compute_value('aspect', 'scale_base')) for f in frag_templates])
        texture_mismatch = None if actor_texture is None else any([t is not None and t not in GENERIC_TEXTURES and t != actor_texture for t in frag_textures])
        scale_mismatch = None if actor_scale is None else any([s is not None and s != actor_scale for s in frag_scales])
        if texture_mismatch:
            frag_textures_str = ', '.join(frag_textures)
            print(f'{enemy.name}: texture mismatch: {actor_texture} - {frag_textures_str}')
        if scale_mismatch:
            frag_scales_str = ', '.join([str(s) for s in frag_scales])
            print(f'{enemy.name}: scale mismatch: {actor_scale} - {frag_scales_str}')
        if texture_mismatch or scale_mismatch:
            num_enemies_with_mismatches += 1
    print(f'num enemies with mismatches: {num_enemies_with_mismatches}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Frags')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    frags(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
