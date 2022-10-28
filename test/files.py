import os
import shutil
import time


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

    def copy_map_region(self, map_name, region_name):
        # copy map base files & one region into self.bits_dir
        src = os.path.join(self.maps_bits_dir, 'world', 'maps', map_name)
        dst = os.path.join(self.bits_dir, 'world', 'maps', map_name)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('regions'))
        time.sleep(0.1)  # shutil...
        shutil.copytree(os.path.join(src, 'regions', region_name), os.path.join(dst, 'regions', region_name))
        time.sleep(0.1)  # shutil...

    def cleanup_map(self, map_name):
        shutil.rmtree(os.path.join(self.bits_dir, 'world', 'maps', map_name))
        time.sleep(0.1)  # shutil...
