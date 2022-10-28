# gaspy

Tooling for .gas files &amp; Bits folders (Gas Powered Games, Dungeon Siege), written in Python.


## Overview


### gas module

This module is for basic handling of the GPG Gas format.

- gas.py: Basic classes for gas content - attributes & sections
- gas_dir.py: Class GasDir to handle files & subdirs\
  CLI to test-parse contained .gas files recursively, given the dir path
- gas_file.py: Class GasFile to handle a .gas file\
  CLI to parse & print a .gas file, given its path
- gas_parser.py: Class GasParser with the parse method
- gas_writer.py: Class GasWriter with the write_file method
- molecules.py: Helper classes for more complex gas attr value types


### bits module

This module is for handling the Bits folder structure.\
Everything map-specific is in submodule "maps".

- bits.py: Class Bits to handle the whole "Bits" folder
- bits_cli.py: CLI to print info about the maps or templates
- gas_dir_handler.py: Base class for Map & Region
- language.py: Handler for the language dir
- moods.py: Handler for moods and the moods dir
- snos.py: Handler for the SNO terrain node files in art/terrain
- templates.py: Class Templates to handle the templates
- templates_cli.py: CLI to print some template info
- maps submodule:
  - map.py: Class Map to handle a DS map
  - region.py: Class Region to handle a DS map region
  - region_objects.py: Subclass for handling the objects of a region
  - terrain.py: Class to handle terrain - more high-level than nodes_gas.py
  - game_object.py: Handler for GameObject gas
  - game_object_data.py: Handler for GameObject data (more abstracted from gas)
  - ...and lots of files for handling specific gas files.


### sno module

Handling for SNO (siege terrain node) files.\
Based on a sno.ksy file (abstract description of binary format) and sno.py file (Python binding generated from the ksy), courtesy of Orix.


### printouts module

Module with scripts to produce various printouts, be it console text dumps or csv files.


### region_import module

These are CLI script files I found useful when importing regions from other maps into my own.

- High-level scripts:
  - import_region.py: One-stop CLI to import a region from one map into another.
  - copy_region.py: Script to copy a region within a map.
- Low-level scripts:
  - check_dupe_node_ids.py: CLI that asserts that a map does not contain duplicate node ids, and also no common node ids with the other maps.\
    This is checked to ensure other people can import your regions as well as existing ones.
  - convert_to_node_mesh_index.py: CLI that converts a region (or an entire map) to using node_mesh_index.\
    Required to use LoA nodes.\
    You have to open the converted region(s) in Siege Editor to complete the process.
  - edit_region_ids.py: CLI to edit a region's guid, mesh_range or scid_range.
  - inc_node_ids.py: CLI that increments all node ids of a region (or an entire map).\
    Useful for making the check_dupe_node_ids.py green.\
    You have to open & save the converted region(s) in Siege Editor to complete the process.
  - rename_region.py: CLI to rename a region, incl. adapting stitch references.
  - replace_hexes.py
  - replace_strs.py


### build module

These are CLI script files that I found useful for building maps.

- add_world_levels.py: Generate regular/veteran/elite sub-folders in objects and index.\
  This allows to have the plain objects structure for working with Siege Editor, then adding the world level folders on-the-fly when building.
- Checks:
  - check_moods.py
  - check_player_world_locations.py
  - check_quests.py
- Fixes:
  - fix_start_positions_required_levels.py: CLI that fixes the "i" in front of the "required_level" attributes.\
    Siege Editor adds the "i" but it breaks the required level of the multiplayer start position.


### landscaping module

Welcome to Four Seasons Total Landscaping!

- autosize_plants.py: CLI to assign existing plants a random size.\
  Useful if you forgot using random size during creation.
- brush_up.py: A bit more thorough than autosize_plants - this will resize them all and turn them around into the bargain
- edit_lights.py: Script for changing colors, intensities etc.
- edit_moods.py: Automatically edit e.g. colors & distances of fog
- plant_gen.py: CLI to generate plants on existing regions
- rescale_objs.py: Special script to get rid of templates that use scale_multiplier
- ruinate.py: Functions for ruining / weathering regions... WIP


### mapgen module

A module for generating maps and/or regions.\
There are two region generators and a basic map helper:
- basic.py: Script for creating/deleting empty maps/regions
- flat: A little map generator I built, producing flat terrain with "intelligent random" plant placements.\
  My first one. In practice not very useful tho tbh.
- heightmap: Another map generator I built, producing mountainous terrain from a perlin heightmap.\
  This is being used to create the Green Range map.


### top-level

- Translation help
  - extract_translations.py: See which strings are missing translations
  - untranslate.py: CLI to generate language translation files that translate the strings
    to the original (e.g. English) strings.\
    Use if you have a non-English DS but want to play without translation (some texts are baked into exe tho).
- World-Level help (regular/veteran/elite)
  - world_levels.py: CLI to add/remove these world level sub-folders in the objects dir of a region
  - world_level_templates.py: CLI to generate veteran/elite templates from regular ones
- valhalla.py: Script used to create the Valhalla mod, auto-editing veteran/elite actor templates to make them look cooler


### Unit tests

Unit tests are in folder "test".\
Some require certain bits to be present in the files/extracts sub-folder.\
Disclaimer: I didn't even bother to check the coverage.
