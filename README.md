# gaspy

Tooling for .gas files &amp; Bits folders (Gas Powered Games, Dungeon Siege), written in Python.

## Overview

### Gas parsing

Tools to parse .gas files and print out statistics and stuff.

- gas.py: Basic classes for gas content
- gas_parser.py: Class GasParser with the parse method
- gas_file.py: Class GasFile to handle a .gas file\
  **CLI** to parse & print a .gas file, given its path
- gas_dir.py: Class GasDir to handle files & subdirs\
  **CLI** to test-parse contained .gas files recursively, given the dir path
- gas_dir_handler.py: Base class for Map & Region
- map.py: Class Map to handle a DS map
- region.py: Class Region to handle a DS map region
- start_position.py: Classes to handle start positions
- templates.py: Class Templates to handle the templates
- bits.py: Class Bits to handle the whole "Bits" folder\
  **CLI** to print info about the maps or templates


- csv.py: **CLI** to generate various statistical spreadsheets in CSV format.\
  Some require additional information in form of certain files in the "input" folder.\
  Files are written into the "output" folder.

### Map generator

A little map generator I built, producing flat terrain with "intelligent random" plant placements.\
Still not very useful tho.

- mapgen.py: **CLI** to generate/delete maps/regions
- terrain.py: Class Terrain that helps with handling terrain nodes
- gas_writer.py: Class GasWriter with the write method

One of the plant placement algorithms uses Perlin noise, that's why dependency "perlin-noise" is imported in requirements.txt.

### Region import

Some things I found useful for importing existing regions into my EoS map project.

- check_dupe_node_ids.py: **CLI** that asserts that a map does not contain duplicate node ids, and also no common node ids with the other maps.\
  This is checked to ensure other people can import your regions as well as existing ones.
- inc_node_ids.py: **CLI** that increments all node ids of a region (or an entire map).\
  Useful for making the check_dupe_node_ids.py green.

### Unit tests

Unit tests are in folder "test".\
Some require certain bits to be present in the "Bits" folder.\
Disclaimer: I didn't even bother to check the coverage.
