import argparse
import os
import shutil
import sys
import time
from shutil import ignore_patterns

from bits.bits import Bits


def install_minibits_templates(bits: Bits, minibits_single_path: str):
    minibits_name = os.path.basename(os.path.dirname(minibits_single_path))
    src_templates_path = os.path.join(minibits_single_path, 'world', 'contentdb', 'templates')
    if not os.path.exists(src_templates_path):
        return
    print('  templates')
    dst_templates_path = os.path.join(bits.gas_dir.path, 'world', 'contentdb', 'templates', 'minibits', minibits_name)
    if os.path.exists(dst_templates_path):
        shutil.rmtree(dst_templates_path)
        time.sleep(0.1)  # shutil...
    shutil.copytree(src_templates_path, dst_templates_path)
    time.sleep(0.1)  # shutil...


def install_minibits_components(bits: Bits, minibits_single_path: str):
    minibits_name = os.path.basename(os.path.dirname(minibits_single_path))
    src_components_path = os.path.join(minibits_single_path, 'world', 'contentdb', 'components')
    if not os.path.exists(src_components_path):
        return
    print('  components')
    dst_components_path = os.path.join(bits.gas_dir.path, 'world', 'contentdb', 'components', 'minibits', minibits_name)
    shutil.copytree(src_components_path, dst_components_path, dirs_exist_ok=True)
    time.sleep(0.1)  # shutil...


def install_minibits_translations(bits: Bits, minibits_single_path: str):
    src_language_path = os.path.join(minibits_single_path, 'language')
    if not os.path.exists(src_language_path):
        return
    print('  translations')
    dst_language_path = os.path.join(bits.gas_dir.path, 'language')
    shutil.copytree(src_language_path, dst_language_path, dirs_exist_ok=True)
    time.sleep(0.1)  # shutil...


def install_minibits_jobs(bits: Bits, minibits_single_path: str):
    minibits_name = os.path.basename(os.path.dirname(minibits_single_path))
    src_jobs_path = os.path.join(minibits_single_path, 'world', 'ai', 'jobs', minibits_name)
    if not os.path.exists(src_jobs_path):
        return
    print('  jobs')
    dst_jobs_path = os.path.join(bits.gas_dir.path, 'world', 'ai', 'jobs', 'minibits', minibits_name)
    if os.path.exists(dst_jobs_path):
        shutil.rmtree(dst_jobs_path)
        time.sleep(0.1)  # shutil...
    shutil.copytree(src_jobs_path, dst_jobs_path)
    time.sleep(0.1)  # shutil...


def install_minibits_art(bits: Bits, minibits_single_path: str):
    src_art_path = os.path.join(minibits_single_path, 'art')
    if not os.path.exists(src_art_path):
        return
    print('  art')
    dst_art_path = os.path.join(bits.gas_dir.path, 'art')
    shutil.copytree(src_art_path, dst_art_path, dirs_exist_ok=True, ignore=ignore_patterns('*.psd', '*.xcf'))
    time.sleep(0.1)  # shutil...


def install_minibits_sound(bits: Bits, minibits_single_path: str):
    src_sound_path = os.path.join(minibits_single_path, 'sound')
    if not os.path.exists(src_sound_path):
        return
    print('  sound')
    dst_sound_path = os.path.join(bits.gas_dir.path, 'sound')
    shutil.copytree(src_sound_path, dst_sound_path, dirs_exist_ok=True)
    time.sleep(0.1)  # shutil...


def install_minibits_siege_nodes(bits: Bits, minibits_single_path: str):
    src_path = os.path.join(minibits_single_path, 'world', 'global', 'siege_nodes')
    if not os.path.exists(src_path):
        return
    print('  siege_nodes')
    dst_path = os.path.join(bits.gas_dir.path, 'world', 'global', 'siege_nodes')
    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
    time.sleep(0.1)  # shutil...


def install_minibits_effects(bits: Bits, minibits_single_path: str):
    minibits_name = os.path.basename(os.path.dirname(minibits_single_path))
    src_path = os.path.join(minibits_single_path, 'world', 'global', 'effects')
    if not os.path.exists(src_path):
        return
    print('  effects')
    dst_path = os.path.join(bits.gas_dir.path, 'world', 'global', 'effects')
    for filename in os.listdir(src_path):
        shutil.copyfile(os.path.join(src_path, filename), os.path.join(dst_path, f'minibits-{minibits_name}-{filename}'))
    time.sleep(0.1)  # shutil...


def install_minibits_single(bits: Bits, minibits_path: str, minibits_single: str):
    print(minibits_single)
    minibits_single_path = os.path.join(minibits_path, minibits_single, 'Bits')
    assert os.path.exists(minibits_single_path)
    install_minibits_templates(bits, minibits_single_path)
    install_minibits_components(bits, minibits_single_path)
    install_minibits_art(bits, minibits_single_path)
    install_minibits_sound(bits, minibits_single_path)
    install_minibits_jobs(bits, minibits_single_path)
    install_minibits_siege_nodes(bits, minibits_single_path)
    install_minibits_effects(bits, minibits_single_path)
    install_minibits_translations(bits, minibits_single_path)


def install_minibits_list(bits: Bits, minibits_path: str, minibits_list: list[str]):
    for minibits_single in minibits_list:
        install_minibits_single(bits, minibits_path, minibits_single)


def install_minibits(bits_path: str, minibits_path: str):
    print('Begin installing minibits')
    assert os.path.exists(minibits_path)
    bits = Bits(bits_path)
    minibits_txt_path = os.path.join(bits.gas_dir.path, 'minibits.txt')
    assert os.path.exists(minibits_txt_path)
    with open(minibits_txt_path, 'r') as minibits_txt:
        minibits_list = minibits_txt.readlines()
    minibits_list = [x.strip() for x in minibits_list]
    install_minibits_list(bits, minibits_path, minibits_list)
    print('Finished installing minibits')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy install_minibits')
    parser.add_argument('--bits', default='DSLOA')
    parser.add_argument('--minibits', required=True)
    return parser


def parse_args(argv: list[str]):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str]):
    args = parse_args(argv)
    install_minibits(args.bits, args.minibits)


if __name__ == '__main__':
    main(sys.argv[1:])
