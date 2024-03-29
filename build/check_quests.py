import argparse
import sys

from bits.bits import Bits
from bits.maps.conversations_gas import ConversationItem
from bits.maps.region import Region


def check_quests_in_region(region: Region, quest_names: list[str]) -> int:
    num_invalid_quest_names = 0

    # quests referenced in triggers
    special_objects = region.objects.do_load_objects_special() or list()
    for obj in special_objects:
        common = obj.section.get_section('common')
        if not common:
            continue
        instance_triggers_section = common.get_section('instance_triggers')
        if not instance_triggers_section:
            continue
        instance_triggers = instance_triggers_section.get_sections('*')
        for trigger in instance_triggers:
            action_attrs = trigger.get_attrs('action*')
            for attr in action_attrs:
                if attr.value.startswith('change_quest_state'):
                    quest_name = attr.value.split('"')[1].strip()
                    if quest_name not in quest_names:
                        print(f'Invalid quest name in {region.get_name()} triggers: {quest_name}')
                        num_invalid_quest_names += 1

    # quests referenced in conversations
    if region.conversations is None:
        region.load_conversations()
    if region.conversations is not None:
        for name, items in region.conversations.conversations.items():
            for item in items:
                assert isinstance(item, ConversationItem)
                for quest_name in item.activate_quests + item.complete_quests:
                    quest_name = quest_name.split(',')[0]
                    if quest_name not in quest_names:
                        print(f'Invalid quest name in {region.get_name()} conversations: {quest_name}')
                        num_invalid_quest_names += 1

    return num_invalid_quest_names


def check_quests(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    _map.load_quests()
    quest_names = list(_map.quests.quests.keys())
    num_invalid_quest_names = 0
    print(f'Checking quests in {map_name}...')
    for region in _map.get_regions().values():
        region_invalid_quest_names = check_quests_in_region(region, quest_names)
        num_invalid_quest_names += region_invalid_quest_names
    print(f'Checking quests in {map_name}: {num_invalid_quest_names} invalid quest names')
    return num_invalid_quest_names == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_quests')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    map_name = args.map
    bits_path = args.bits
    bits = Bits(bits_path)
    valid = check_quests(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
