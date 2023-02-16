from bits.maps.map import Map
from printouts.csv import write_csv


class Shrine:
    def __init__(self, scid: str, region_name: str, data: dict):
        self.scid = scid
        self.region_name = region_name
        self.data = data


def print_world_level_shrines(_map: Map):
    shrines: dict[str, Shrine] = {}
    for region in _map.get_regions().values():
        objs_dir = region.gas_dir.get_subdir('objects')
        for wl in ['regular', 'veteran', 'elite']:
            wl_dir = objs_dir.get_subdir(wl)
            gas_file = wl_dir.get_gas_file('special')
            for go in gas_file.get_gas().get_sections():
                t, n = go.get_t_n_header()
                if t != 'life_shrine':  # life_shrine / mana_shrine
                    continue
                if n not in shrines:
                    shrines[n] = Shrine(n, region.get_name(), {'regular': None, 'veteran': None, 'elite': None})
                f = go.get_section('fountain')
                shrines[n].data[wl] = {'heal_amount': f.get_attr_value('heal_amount'), 'health_left': f.get_attr_value('health_left'), 'health_regen': f.get_attr_value('health_regen')}
    shrines_list: list[Shrine] = sorted(shrines.values(), key=lambda x: x.data['regular']['heal_amount'])
    csv = [
        [
            'SCID',
            'Region',
            'heal_amount regular',
            'heal_amount veteran',
            'heal_amount elite',
            'health_left regular',
            'health_left veteran',
            'health_left elite',
            'health_regen regular',
            'health_regen veteran',
            'health_regen elite'
        ]
    ]
    for shrine in shrines_list:
        r, v, e = shrine.data['regular'], shrine.data['veteran'], shrine.data['elite']
        ar, lr, rr = r['heal_amount'], r['health_left'], r['health_regen']
        av, lv, rv = v['heal_amount'], v['health_left'], v['health_regen']
        ae, le, re = e['heal_amount'], e['health_left'], e['health_regen']
        print(f'{shrine.scid}: heal_amount {ar}/{av}/{ae}, health_left {lr}/{lv}/{le}, health_regen {rr}/{rv}/{re}  ({shrine.region_name})')
        csv.append([shrine.scid, shrine.region_name, ar, av, ae, lr, lv, le, rr, rv, re])
    write_csv('World-Level Shrines', csv)
