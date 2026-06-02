import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from printouts.equipment import get_pcontent_variants

HERO_NPC_MODELS = ['gah_fg', 'gah_fb', 'gan_df', 'ecm_sk', 'gan_hg']


def is_hero_npc(npc: Template) -> bool:
    model = npc.compute_value('aspect', 'model')
    for hero_model_infix in HERO_NPC_MODELS:
        if model.startswith(f'm_c_{hero_model_infix}_'):
            return True
    return False


def run_printout_clothes(bits_path: str):
    bits = Bits(bits_path)

    armors = bits.templates.get_leaf_templates('armor').values()
    body_armors = [a for a in armors if a.compute_value('gui', 'equip_slot') == 'es_chest']
    print(f'{len(body_armors)} body armors')
    body_armor_textures = set()
    for body_armor in body_armors:
        armor_type = body_armor.compute_value('defend', 'armor_type')
        armor_style = body_armor.compute_value('defend', 'armor_style')
        texture = f'b_c_pos_{armor_type}_{armor_style}'
        body_armor_textures.add(texture)
        if body_armor.has_component('pcontent'):
            variants = get_pcontent_variants(body_armor)
            for variant in variants:
                v_armor_type = variant.armor_type or armor_type
                v_armor_style = variant.armor_style or armor_style
                v_texture = f'b_c_pos_{v_armor_type}_{v_armor_style}'
                body_armor_textures.add(v_texture)
    print(f'{len(body_armor_textures)} body armor textures')
    print(', '.join(sorted(body_armor_textures)))

    actors = bits.templates.get_actor_templates().values()
    npcs = [a for a in actors if a.is_descendant_of('actor_good') or a.is_descendant_of('npc') or a.is_descendant_of('hero')]
    npcs = [n for n in npcs if n.wl_prefix is None]
    npcs = [n for n in npcs if is_hero_npc(n)]
    npcs = [n for n in npcs if not n.name.endswith('_object')]  # monster_magnet_object, spectral_image_object...
    print(f'{len(npcs)} npcs')
    npc_textures = set()
    for npc in npcs:
        texture = npc.compute_value('aspect', 'textures', '1')
        if texture is not None:
            npc_textures.add(texture)
    print(f'{len(npc_textures)} npc textures')

    unavailable_textures = npc_textures.difference(body_armor_textures)
    print(f'{len(unavailable_textures)} unavailable npc textures')
    print(', '.join(sorted(unavailable_textures)))

    known_textures = set()
    for x in range(7):
        known_textures.add(f'b_c_pos_b1_{x+1:03d}')
    for x in range(78):
        known_textures.add(f'b_c_pos_a1_{x+1:03d}')
    for x in range(56):
        known_textures.add(f'b_c_pos_a2_{x+1:03d}')
    for x in range(45):
        known_textures.add(f'b_c_pos_a3_{x+1:03d}')
    for x in range(10):
        known_textures.add(f'b_c_pos_a4_{x+1:03d}')
    for x in range(21):
        known_textures.add(f'b_c_pos_a5_{x+1:03d}')
    for x in range(10):
        known_textures.add(f'b_c_pos_a6_{x+1:03d}')
    for x in range(50):
        known_textures.add(f'b_c_pos_a7_{x+1:03d}')
    print(f'{len(known_textures)} known textures')

    unused_textures = known_textures.difference(npc_textures, body_armor_textures)
    print(f'{len(unused_textures)} unused body textures')
    print(', '.join(sorted(unused_textures)))


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Clothes')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    run_printout_clothes(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
