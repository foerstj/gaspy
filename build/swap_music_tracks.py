import argparse
import sys

from bits.bits import Bits


# swaps standard_track with the unused battle_track, if both are defined,
# for maintaining fallback music directly in the mood def.
def swap_music_tracks(bits: Bits):
    bits.moods.load_moods()
    num_changed = 0
    for mood in bits.moods.get_all_moods():
        if mood.music:
            if mood.music.standard.track and mood.music.battle.track:
                tmp_track = mood.music.standard.track
                mood.music.standard.track = mood.music.battle.track
                mood.music.battle.track = tmp_track
                num_changed += 1
    if num_changed > 0:
        print(f'Swapped music in {num_changed} moods.')
        bits.moods.save()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy swap music tracks')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits_path = args.bits
    bits = Bits(bits_path)
    swap_music_tracks(bits)


if __name__ == '__main__':
    main(sys.argv[1:])
