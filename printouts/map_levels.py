# Ordered regions -> how much XP, and what lvl the player will be at
from bits.maps.map import Map
from printouts.common import load_regions_xp
from printouts.csv import write_csv


def write_map_levels_csv(m: Map):
    regions_xp = load_regions_xp(m)
    data = [['world level', 'region', 'xp', 'weight', 'xp', 'sum', 'level pre', 'level post']]
    for r in regions_xp:
        print(f'{r.name} {r.xp*r.weight}')
        data.append([r.world_level, r.name, r.xp, r.weight, r.xp*r.weight, r.xp_post, r.pre_level, r.post_level])
    write_csv(m.gas_dir.dir_name, data)
