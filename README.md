# gaspy

Tooling for .gas files &amp; Bits folders (Gas Powered Games, Dungeon Siege), written in Python.


## Overview


### gas module

This module is for basic handling of the GPG Gas format.

- gas.py: Basic classes for gas content
- gas_dir.py: Class GasDir to handle files & subdirs\
  **CLI** to test-parse contained .gas files recursively, given the dir path
- gas_file.py: Class GasFile to handle a .gas file\
  **CLI** to parse & print a .gas file, given its path
- gas_parser.py: Class GasParser with the parse method
- gas_writer.py: Class GasWriter with the write_file method

### bits module

This module is for handling the Bits folder structure.

- bits.py: Class Bits to handle the whole "Bits" folder\
  **CLI** to print info about the maps or templates
- game_object.py: Handler for GameObject gas
- game_object_data.py: Handler for GameObject data (more abstracted from gas)
- gas_dir_handler.py: Base class for Map & Region
- map.py: Class Map to handle a DS map
- nodes_gas.py: Handler for the nodes.gas file
- region.py: Class Region to handle a DS map region
- start_position.py: Classes to handle start positions
- stitch_helper_gas.py: Handler for the stitch_helper.gas file
- templates.py: Class Templates to handle the templates
- terrain.py: Class to handle terrain


### sno module

Handling for SNO (siege terrain node) files


### mapgen module

A little map generator I built, producing flat terrain with "intelligent random" plant placements.\
Still not very useful tho.

- mapgen.py: **CLI** to generate/delete maps/regions
- mapgen_plants.py: Plant handler for the mapgen
- mapgen_terrain.py: Class Terrain that helps with handling terrain nodes

Another map generator I built, producing mountainous terrain from a perlin heightmap.\
Hopefully useful one day.

- mapgen_heightmap.py: **CLI** to generate regions from a heightmap


### region_import module

These are CLI script files I found useful when importing regions from other maps into my own.

- check_dupe_node_ids.py: **CLI** that asserts that a map does not contain duplicate node ids, and also no common node ids with the other maps.\
  This is checked to ensure other people can import your regions as well as existing ones.
- convert_to_node_mesh_index.py: **CLI** that converts a region (or an entire map) to using node_mesh_index.\
  Required to use LoA nodes.\
  You have to open the converted region(s) in Siege Editor to complete the process.
- edit_region_ids.py: **CLI** to edit a region's guid, mesh_range or scid_range.
- inc_node_ids.py: **CLI** that increments all node ids of a region (or an entire map).\
  Useful for making the check_dupe_node_ids.py green.\
  You have to open & save the converted region(s) in Siege Editor to complete the process.
- rename_region.py: **CLI** to rename a region, incl. adapting stitch references.


### build module

These are CLI script files that I found useful for building maps.

- start_positions_required_levels: **CLI** that fixes the "i" in front of the "required_level" attributes.\
  Siege Editor adds the "i" but it breaks the required level of the multiplayer start position.


### top-level

- autosize_plants.py: **CLI** to assign existing plants a random size.\
  Useful if you forgot using random size during creation.
- csv.py: **CLI** to generate various statistical spreadsheets in CSV format.\
  Some require additional information in form of certain files in the "input" folder.\
  Files are written into the "output" folder.
- plant_gen.py: **CLI** to generate plants on *existing* regions (therefore not considered mapgen)
- untranslate.py: **CLI** to generate language translation files that translate the strings
  to the original (e.g. English) strings.\
  Use if you have a non-English DS but want to play without translation (some texts are baked into exe tho).
- world_levels.py: **CLI** to add/remove these world level sub-folders (regular/veteran/elite)
  in the objects dir of a region


### Unit tests

Unit tests are in folder "test".\
Some require certain bits to be present in the "Bits" folder.\
Disclaimer: I didn't even bother to check the coverage.
