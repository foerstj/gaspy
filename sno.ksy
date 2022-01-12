meta:
  id: sno
  file-extension: sno
  endian: le
seq:
  - id: magic
    contents: SNOD
  - id: version
    type: version
  - id: door_count
    type: u4
  - id: spot_count
    type: u4
  - id: corner_count
    type: u4
  - id: face_count
    type: u4
  - id: texture_count
    type: u4
  - id: bounding_box
    type: bounding_box
  - id: unk1
    type: u4
  - id: unk2
    type: u4
  - id: unk3
    type: u4
  - id: unk4
    type: u4
  - id: unk5
    type: u4
  - id: unk6
    type: u4
  - id: unk7
    type: u4
  - id: checksum
    type: u4
  - id: spot_array
    type: spot
    repeat: expr
    repeat-expr: spot_count
  - id: door_array
    type: door
    repeat: expr
    repeat-expr: door_count
  - id: corner_array
    type: corner
    repeat: expr
    repeat-expr: corner_count
  - id: surface_array
    type: surface
    repeat: expr
    repeat-expr: texture_count
  - id: mystery_section_count
    type: u4
  - id: mystery
    type: mystery_section
    repeat: expr
    repeat-expr: mystery_section_count
enums:
  floor:
     0x40000001: floor
     0x80000000: water
     0x20000000: ignored
types:
  v3:
    seq:
      - id: x
        type: f4
      - id: y
        type: f4
      - id: z
        type: f4
  bounding_box:
    seq:
      - id: min
        type: v3
      - id: max
        type: v3
  triangle:
    seq:
      - id: a
        type: v3
      - id: b
        type: v3
      - id: c
        type: v3
  color:
    seq:
      - id: r
        type: u1
      - id: g
        type: u1
      - id: b
        type: u1
      - id: a
        type: u1
  tcoords:
    seq:
      - id: u
        type: f4
      - id: v
        type: f4
  version:
    seq:
      - id: major
        type: u4
      - id: minor
        type: u4
  face:
    seq:
      - id: a
        type: u2
      - id: b
        type: u2
      - id: c
        type: u2
  spot:
    seq:
      - id: r0
        type: f4
      - id: r1
        type: f4
      - id: r2
        type: f4
      - id: r3
        type: f4
      - id: r4
        type: f4
      - id: r5
        type: f4
      - id: r6
        type: f4
      - id: r7
        type: f4
      - id: r8
        type: f4
      - id: x
        type: f4
      - id: y
        type: f4
      - id: z
        type: f4
      - id: iunno
        type: str
        encoding: ASCII
        terminator: 0x00
  door:
    seq:
      - id: index
        type: u4
      - id: x
        type: f4
      - id: y
        type: f4
      - id: z
        type: f4
      - id: r0
        type: f4
      - id: r1
        type: f4
      - id: r2
        type: f4
      - id: r3
        type: f4
      - id: r4
        type: f4
      - id: r5
        type: f4
      - id: r6
        type: f4
      - id: r7
        type: f4
      - id: r8
        type: f4
      - id: hot_spot_count
        type: u4
      - id: hot_spot_array
        type: u4
        repeat: expr
        repeat-expr: hot_spot_count
  corner:
    seq:
      - id: position
        type: v3
      - id: normal
        type: v3
      - id: color
        type: color
      - id: uvcoords
        type: tcoords
  surface:
    seq:
      - id: texture
        type: str
        encoding: ASCII
        terminator: 0x00
      - id: start_corner
        type: u4
      - id: span_corner
        type: u4
      - id: corner_count
        type: u4
      - id: face_array
        type: face
        repeat: expr
        repeat-expr: corner_count / 3
  mystery_section:
    seq:
      - id: index
        type: u1
      - id: bounding_box
        type: bounding_box
      - id: floor
        type: u4
        enum: floor
      - id: crazy_section_count
        type: u4
      - id: crazy_section_array_6_2
        type: crazy_section_6_2
        if: _root.version.major == 6 and _root.version.minor == 2
        repeat: expr
        repeat-expr: crazy_section_count
      - id: crazy_section_array_7
        type: crazy_section_7
        if: _root.version.major == 7
        repeat: expr
        repeat-expr: crazy_section_count
      - id: short_pair_section_count
        type: u4
      - id: short_pair_section_array
        type: short_pair_section
        repeat: expr
        repeat-expr: short_pair_section_count
      - id: triangle_section_count
        type: u4
      - id: triangle_section
        type: triangle_section
        repeat: expr
        repeat-expr: triangle_section_count
      - id: wtf
        type: wtf_section
  crazy_section_6_2:
    seq:
      - id: index
        type: u2
      - id: r0
        type: f4
      - id: r1
        type: f4
      - id: r2
        type: f4
      - id: r3
        type: f4
      - id: r4
        type: f4
      - id: r5
        type: f4
      - id: count1
        type: u2
      - id: short_array_1
        type: u2
        repeat: expr
        repeat-expr: count1
      - id: count2
        type: u4
      - id: short_array_2
        type: u2
        repeat: expr
        repeat-expr: count2
  crazy_section_7:
    seq:
      - id: index
        type: u2
      - id: r0
        type: f4
      - id: r1
        type: f4
      - id: r2
        type: f4
      - id: r3
        type: f4
      - id: r4
        type: f4
      - id: r5
        type: f4
      - id: r6
        type: f4
      - id: r7
        type: f4
      - id: r8
        type: f4
      - id: count1
        type: u2
      - id: short_array_1
        type: u2
        repeat: expr
        repeat-expr: count1
      - id: count2
        type: u4
      - id: short_array_2
        type: u2
        repeat: expr
        repeat-expr: count2
  short_pair_section:
    seq:
      - id: unk
        type: u1
      - id: count
        type: u4
      - id: data
        type: u2
        repeat: expr
        repeat-expr: count * 2
  triangle_section:
    seq:
      - id: triangle
        type: triangle
      - id: normal
        type: v3
  wtf_section:
    seq:
      - id: bounding_box
        type: bounding_box
      - id: unk
        type: u1
      - id: count
        type: u2
      - id: data
        type: u2
        repeat: expr
        repeat-expr: count
      - id: ind
        type: u1
      - id: moar
        type: wtf_section
        repeat: expr
        repeat-expr: ind