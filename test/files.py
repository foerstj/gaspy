import os


class Files:
    def __init__(self):
        self.files_dir = 'files'
        assert os.path.isdir(self.files_dir)

        self.extracts_dir = os.path.join(self.files_dir, 'extracts')
        assert os.path.isdir(self.extracts_dir)
        self.logic_bits_dir = os.path.join(self.extracts_dir, 'Logic')
        assert os.path.isdir(self.logic_bits_dir)
        self.expansion_bits_dir = os.path.join(self.extracts_dir, 'Expansion')
        assert os.path.isdir(self.expansion_bits_dir)
        self.siege_editor_extras_bits_dir = os.path.join(self.extracts_dir, 'SiegeEditorExtras')
        assert os.path.isdir(self.siege_editor_extras_bits_dir)
        self.maps_bits_dir = os.path.join(self.extracts_dir, 'Maps')
        assert os.path.isdir(self.maps_bits_dir)

        self.bits_dir = os.path.join(self.files_dir, 'Bits')
        assert os.path.isdir(self.bits_dir)
