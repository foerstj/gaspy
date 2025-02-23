import argparse
import os.path
import shutil
import sys
import time

from bits.bits import Bits
from bits.moods import Moods, MoodRain, MoodSnow, MoodWind
from landscaping.colors import make_color_blue, make_color_half_gray


def mult_float(value, multiplier):
    if value is None:
        return None
    if isinstance(value, str):
        value = float(value.rstrip('f'))
    return float(value) * multiplier


def half_float(value):
    return mult_float(value, 0.5)


def edit_fog(moods: Moods, edit: list[str]):
    if edit[0] == 'near-dists':
        edit = edit[1:]
        if edit == ['half']:
            for mood in moods.get_all_moods():
                mood.fog.near_dist = half_float(mood.fog.near_dist)
                mood.fog.lowdetail_near_dist = half_float(mood.fog.lowdetail_near_dist)
        elif edit[0] == 'mult' and len(edit) == 2:
            mult = float(edit[1])
            for mood in moods.get_all_moods():
                mood.fog.near_dist = mult_float(mood.fog.near_dist, mult)
                mood.fog.lowdetail_near_dist = mult_float(mood.fog.lowdetail_near_dist, mult)
        else:
            assert False, f'near-dists {edit}'
    elif edit[0] == 'far-dists':
        edit = edit[1:]
        if edit[0] == 'mult' and len(edit) == 2:
            mult = float(edit[1])
            for mood in moods.get_all_moods():
                mood.fog.far_dist = mult_float(mood.fog.far_dist, mult)
                mood.fog.lowdetail_far_dist = mult_float(mood.fog.lowdetail_far_dist, mult)
        else:
            assert False, f'far-dists {edit}'
    elif edit == ['color', 'half-gray']:
        for mood in moods.get_all_moods():
            mood.fog.color = make_color_half_gray(mood.fog.color)
    elif edit == ['color', 'cold-outside']:
        for mood in moods.get_all_moods():
            if not mood.interior:
                mood.fog.color = make_color_blue(mood.fog.color)
    else:
        assert False, edit


def list_starts_with(the_list: list[str], start: list[str]):
    if len(start) > len(the_list):
        return False
    for i, s in enumerate(start):
        if the_list[i] != s:
            return False
    return True


def edit_music(moods: Moods, edit: list[str]):
    if list_starts_with(edit, ['default-ambience']) and len(edit) == 2:
        default_ambience = edit[1]
        for mood in moods.get_all_moods():
            if mood.music is None:
                continue
            if mood.music.ambient.track is None:
                continue
            if mood.music.ambient.track.strip('" ') == '':
                mood.music.ambient.track = default_ambience
    elif list_starts_with(edit, ['replace-standard']) and len(edit) == 3:
        old_track = edit[1]
        new_track = edit[2]
        for mood in moods.get_all_moods():
            if mood.music is None:
                continue
            if mood.music.standard.track is None:
                continue
            if mood.music.standard.track.strip('" ').lower() == old_track.lower():
                mood.music.standard.track = new_track
    elif list_starts_with(edit, ['replace-ambience']) and len(edit) == 3:
        old_track = edit[1]
        new_track = edit[2]
        for mood in moods.get_all_moods():
            if mood.music is None:
                continue
            if mood.music.ambient.track is None:
                continue
            if mood.music.ambient.track.strip('" ').lower() == old_track.lower():
                mood.music.ambient.track = new_track
    elif list_starts_with(edit, ['standard-repeat-delay']) and len(edit) == 3:
        standard_track = edit[1]
        repeat_delay = edit[2]
        for mood in moods.get_all_moods():
            if mood.music is None:
                continue
            if mood.music.standard.track is None:
                continue
            if mood.music.standard.track.strip('" ').lower() == standard_track.lower():
                mood.music.standard.repeat_delay = repeat_delay
    else:
        assert False, edit


def edit_rain(moods: Moods, edit: list[str]):
    if list_starts_with(edit, ['add-density']) and len(edit) == 2:
        inc = float(edit[1])
        for mood in moods.get_all_moods():
            if mood.interior is True:
                continue  # no rain indoors
            if mood.sun is not None or mood.snow is not None:
                continue  # no rain in snow areas
            if mood.rain is None:
                mood.rain = MoodRain(None, None)
            if mood.rain.density is None:
                mood.rain.density = 0
            mood.rain.density += inc
    elif list_starts_with(edit, ['lightning']) and len(edit) == 2:
        lightning = edit[1].lower()
        assert lightning == 'true', lightning
        for mood in moods.get_all_moods():
            if mood.rain is None:
                continue
            mood.rain.lightning = True
    else:
        assert False, edit


def edit_snow(moods: Moods, edit: list[str]):
    if list_starts_with(edit, ['add-density']) and len(edit) == 2:
        inc = float(edit[1])
        for mood in moods.get_all_moods():
            if mood.interior is True:
                continue  # no snow indoors
            if mood.sun is None or mood.rain is not None:
                continue  # no snow in non-snow areas
            if mood.snow is None:
                mood.snow = MoodSnow(None)
            if mood.snow.density is None:
                mood.snow.density = 0
            mood.snow.density += inc
    else:
        assert False, edit


def edit_wind(moods: Moods, edit: list[str]):
    if list_starts_with(edit, ['add-velocity']) and len(edit) == 2:
        inc = float(edit[1])
        for mood in moods.get_all_moods():
            if mood.interior is True:
                continue  # no wind indoors
            if mood.wind is None:
                mood.wind = MoodWind(None, None)
            if mood.wind.velocity is None:
                mood.wind.velocity = 0
            mood.wind.velocity += inc
    else:
        assert False, edit


def edit_frustum(moods: Moods, edit: list[str]):
    if edit[0] == 'mult' and len(edit) == 2:
        mult = float(edit[1])
        for mood in moods.get_all_moods():
            if mood.frustum is not None:
                mood.frustum.width = mult_float(mood.frustum.width, mult)
                mood.frustum.height = mult_float(mood.frustum.height, mult)
    else:
        assert False, edit


def edit_rain2snow(moods: Moods):
    for mood in moods.get_all_moods():
        if mood.rain is None or mood.rain.density is None:
            continue
        if mood.snow is None:
            mood.snow = MoodSnow(None)
        snow_density = mood.rain.density
        rain_density = mood.snow.density
        mood.rain.density = rain_density
        mood.snow.density = snow_density
        if mood.rain.density is None:
            if mood.mood_name.startswith('multiplayer_world_'):
                # a little hack here - keep empty rain blocks for lightning manipulation on Utraean Peninsula while world is red
                mood.rain.density = None
                mood.rain.lightning = None
            else:
                mood.rain = None


def do_edit_moods(moods: Moods, edit: str):
    edit = edit.split(':')
    if edit[0] == 'fog':
        edit_fog(moods, edit[1:])
    elif edit[0] == 'music':
        edit_music(moods, edit[1:])
    elif edit[0] == 'rain':
        edit_rain(moods, edit[1:])
    elif edit[0] == 'snow':
        edit_snow(moods, edit[1:])
    elif edit[0] == 'wind':
        edit_wind(moods, edit[1:])
    elif edit[0] == 'rain2snow':
        edit_rain2snow(moods)
    elif edit[0] == 'frustum':
        edit_frustum(moods, edit[1:])
    else:
        assert False, edit


def load_edits_file(name: str, bits_path: str) -> list[str]:
    for base_path in [os.path.join(bits_path, 'gaspy'), 'input']:
        file_path = os.path.join(base_path, name)
        print(file_path)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
    raise Exception(f'Edits file {name} not found')


def edit_moods(bits_path: str, src: str, edits: list[str], edits_files: list[str]):
    bits = Bits(bits_path)

    for edits_file in edits_files:
        edits.extend(load_edits_file(edits_file, bits.gas_dir.path))

    if src is not None:
        src_dir = os.path.join(bits.gas_dir.path, src)
        dst_dir = bits.moods.gas_dir.path
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        time.sleep(0.1)  # shutil...

    bits.moods.load_moods()
    for edit in edits:
        do_edit_moods(bits.moods, edit)
    bits.moods.save()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit moods')
    parser.add_argument('--src', nargs='?', help='copy from src before editing')
    parser.add_argument('--edit', nargs='+', help='--edit rain:add-density:100 snow:add-density:100')
    parser.add_argument('--edit-from-file', nargs='+', help='--edit-from-file my-mood-edits.txt')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    edit_moods(args.bits, args.src, args.edit or list(), args.edit_from_file or list())


if __name__ == '__main__':
    main(sys.argv[1:])
