from bits.gas_dir_handler import GasDirHandler
from gas.gas_dir import GasDir


LANGS = {'de': '0x0407', 'fr': '0x040c'}


class Language(GasDirHandler):
    def __init__(self, gas_dir: GasDir):
        super().__init__(gas_dir)

    def get_translations(self, lang_code: str):
        translations = dict()
        if self.gas_dir is None:
            return translations
        for gas_file in self.gas_dir.get_gas_files().values():
            for lang_section in gas_file.get_gas().get_sections():
                assert lang_section.has_t_n_header()
                t, n = lang_section.get_t_n_header()
                if n != 'text':
                    continue  # ui translations
                section_lang_code = t
                if section_lang_code != lang_code:
                    continue
                for section in lang_section.get_sections():
                    frm = section.get_attr_value('from').strip('"')
                    to = section.get_attr_value('to').strip('"')
                    if not frm or not to:
                        continue
                    if frm in translations:
                        # print(f'Dupe translation found: {frm}')
                        # assert translations[frm] == to
                        if translations[frm] != to:
                            print(f'Conflicting translations found: {frm} -> {translations[frm]} / {to}')
                    translations[frm] = to  # not sure about precedence of duplicate/conflicting translations
        return translations
