import sys

from bits.bits import Bits
from bits.maps.conversations_gas import ConversationsGas
from bits.maps.region import Region
from gas.gas import Section


def check_conversations_in_region(region: Region):
    num_invalid_convos = 0
    region.load_conversations()
    convos: ConversationsGas = region.conversations
    convo_ids = convos.conversations.keys() if convos is not None else list()
    for actor in region.get_actors():
        convo_section = actor.section.get_section('conversation')
        if not convo_section:
            continue
        actor_convo_ids = [a.value for a in convo_section.get_section('conversations').get_attrs('*')]
        for actor_convo_id in actor_convo_ids:
            if actor_convo_id not in convo_ids:
                print(f'  Invalid conversation id in {region.get_name()} {actor.object_id}: {actor_convo_id}')
                num_invalid_convos += 1
    return num_invalid_convos


def check_conversations(bits: Bits, map_name: str):
    _map = bits.maps[map_name]
    num_invalid_convos = 0
    print(f'Checking Conversations in {map_name}...')
    for region in _map.get_regions().values():
        region_invalid_convos = check_conversations_in_region(region)
        num_invalid_convos += region_invalid_convos
    print(f'Checking Conversations in {map_name}: {num_invalid_convos} invalid conversation ids')
    return num_invalid_convos == 0


def main(argv):
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    valid = check_conversations(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
