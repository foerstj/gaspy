from gas.gas import Hex, Gas, Section, Attribute
from gas.gas_file import GasFile


class StitchEditor:
    def __init__(self, dest_region: str, node_ids: dict[Hex, tuple[Hex, int]]):
        self.dest_region = dest_region
        self.node_ids: dict[Hex, tuple[Hex, int]] = node_ids


# Handler for editor/stitch_helper.gas file
class StitchHelperGas:
    def __init__(self, source_region_guid: Hex, source_region_name: str, stitch_editors: list[StitchEditor] = None):
        self.source_region_guid: Hex = source_region_guid
        self.source_region_name: str = source_region_name
        self.stitch_editors = stitch_editors if stitch_editors is not None else list()

    @classmethod
    def load(cls, gas_file: GasFile):
        gas = gas_file.get_gas()
        shd_section = gas.get_section('stitch_helper_data')
        srg = Hex.convert(shd_section.get_attr_value('source_region_guid'))
        srn = shd_section.get_attr_value('source_region_name')
        ses = list()
        stitch_editor_sections = shd_section.get_sections()
        for se_section in stitch_editor_sections:
            dest_region = se_section.get_attr_value('dest_region')
            assert se_section.header == f't:stitch_editor,n:{dest_region}'
            node_ids = dict()
            node_id_attrs = se_section.get_section('node_ids').get_attrs()
            for ni_attr in node_id_attrs:
                stitch_id = Hex.parse(ni_attr.name)
                node_guid, door = ni_attr.value.split(',')
                node_ids[stitch_id] = (Hex.parse(node_guid), int(door))
            se = StitchEditor(dest_region, node_ids)
            ses.append(se)
        stitch_helper_gas = StitchHelperGas(srg, srn, ses)
        return stitch_helper_gas

    def write_gas(self) -> Gas:
        se_sections = [
            Section(f't:stitch_editor,n:{se.dest_region}', [
                Attribute('dest_region', se.dest_region),
                Section('node_ids', [Attribute(Hex(stitch_id).to_str_lower(), f'{node_guid},{door}') for stitch_id, (node_guid, door) in se.node_ids.items()])
            ]) for se in self.stitch_editors
        ]
        return Gas([
            Section('stitch_helper_data', [
                Attribute('source_region_guid', str(Hex(self.source_region_guid))),
                Attribute('source_region_name', self.source_region_name),
            ] + se_sections)
        ])
