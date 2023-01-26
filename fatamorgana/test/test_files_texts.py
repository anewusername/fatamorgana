# type: ignore
from typing import IO
from io import BytesIO

import pytest

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, write_bstring, write_byte
from ..basic import InvalidRecordError, InvalidDataError
from ..basic import GridRepetition, ArbitraryRepetition
from ..main import OasisLayout


def base_tests(layout: OasisLayout) -> None:
    assert layout.version.string == '1.0'
    assert layout.unit == 1000
    assert layout.validation.checksum_type == 0

    assert not layout.properties
    assert not layout.propnames
    assert not layout.xnames
    assert not layout.cellnames
    assert not layout.propstrings
    assert not layout.layers


def common_tests(layout: OasisLayout) -> None:
    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'ABC'

    geometry = layout.cells[0].geometry

    geometry[0].layer == 1
    geometry[0].datatype == 2
    for ii, gg in enumerate(geometry[1:]):
        assert gg.layer == 2, f'textstring #{ii + 1}'
        assert gg.datatype == 1, f'textstring #{ii + 1}'

    assert geometry[0].x == 100
    assert geometry[0].y == -200
    assert geometry[1].x == 200
    assert geometry[1].y == -400
    assert geometry[2].y == -400
    for ii, gg in enumerate(geometry[2:]):
        assert gg.x == 300, f'textstring #{ii + 2}'

    for ii, gg in enumerate(geometry[3:]):
        assert gg.y == -300 - 200 * ii, f'textstring #{ii + 3}'

    for ii, gg in enumerate(geometry):
        if ii < 4:
            assert gg.repetition is None, f'textstring #{ii}'
        elif ii in (4, 5, 6, 7, 12, 13, 14, 15):
            assert isinstance(gg.repetition, GridRepetition), f'textstring #{ii}'
        else:
            assert isinstance(gg.repetition, ArbitraryRepetition), f'textstring #{ii}'

    for ii in (4, 5):
        assert geometry[ii].repetition.a_count == 3, f'textstring #{ii}'
        assert geometry[ii].repetition.b_count == 4, f'textstring #{ii}'
        assert geometry[ii].repetition.a_vector == [10, 0], f'textstring #{ii}'
        assert geometry[ii].repetition.b_vector == [0, 12], f'textstring #{ii}'

    assert geometry[6].repetition.a_count == 3
    assert geometry[6].repetition.a_vector == [10, 0]

    assert geometry[7].repetition.a_count == 4
    assert geometry[7].repetition.a_vector == [0, 12]

    assert geometry[8].repetition.x_displacements == [12, 13, 14]
    assert geometry[9].repetition.x_displacements == [4 * 3, 5 * 3, 6 * 3]
    assert geometry[10].repetition.y_displacements == [10, 11]
    assert geometry[11].repetition.y_displacements == [2 * 5, 3 * 5]

    assert geometry[12].repetition.a_count == 3
    assert geometry[12].repetition.b_count == 4
    assert geometry[12].repetition.a_vector == [10, 0]
    assert geometry[12].repetition.b_vector == [-11, -12]

    assert geometry[13].repetition.a_count == 3
    assert geometry[13].repetition.b_count == 4
    assert geometry[13].repetition.a_vector == [11, 12]
    assert geometry[13].repetition.b_vector == [-10, 10]

    assert geometry[14].repetition.a_count == 3
    assert geometry[14].repetition.b_count is None
    assert geometry[14].repetition.a_vector == [11, 12]
    assert geometry[14].repetition.b_vector is None

    assert geometry[15].repetition.a_count == 4
    assert geometry[15].repetition.b_count is None
    assert geometry[15].repetition.a_vector == [-10, 10]
    assert geometry[15].repetition.b_vector is None

    assert geometry[17].repetition.x_displacements == [-11, 10]
    assert geometry[17].repetition.y_displacements == [12, -10]

    assert geometry[19].repetition.x_displacements == [-12, 9]
    assert geometry[19].repetition.y_displacements == [12, -9]


def write_file_common(buf: IO[bytes], variant: int) -> IO[bytes]:
    '''
    Single cell with explicit name 'XYZ'
    '''
    assert variant in (1, 2, 5, 12), 'Error in test!!'

    buf.write(HEADER)

    if variant == 2:
        write_uint(buf, 6)           # TEXTSTRING record (explicit id)
        write_bstring(buf, b'A')
        write_uint(buf, 1)           # id

        write_uint(buf, 6)           # TEXTSTRING record (explicit id)
        write_bstring(buf, b'B')
        write_uint(buf, 2)           # id
    elif variant == 5:
        write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
        write_bstring(buf, b'A')

        write_uint(buf, 5)           # TEXTSTRING record (implicit id 1)
        write_bstring(buf, b'B')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    # TEXT 0
    write_uint(buf, 19)              # TEXT record
    if variant == 1:
        write_byte(buf, 0b0101_1011)     # 0CNX_YRTL
        write_bstring(buf, b'TEXT_ABC')  # text string
    elif variant in (2, 5, 12):
        write_byte(buf, 0b0111_1011)     # 0CNX_YRTL
        write_uint(buf, 1)               # textstring id
    write_uint(buf, 1)               # layer
    write_uint(buf, 2)               # datatype
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y

    write_uint(buf, 16)              # XYRELATIVE

    # TEXT 1
    write_uint(buf, 19)              # TEXT record
    if variant == 1:
        write_byte(buf, 0b0101_1011)     # 0CNX_YRTL
        write_bstring(buf, b'TEXT_ABC')  # text string
    elif variant in (2, 12):
        write_byte(buf, 0b0111_1011)     # 0CNX_YRTL
        write_uint(buf, 2)               # textstring id
    elif variant == 5:
        write_byte(buf, 0b0111_1011)     # 0CNX_YRTL
        write_uint(buf, 0)               # textstring id
    write_uint(buf, 2)               # layer
    write_uint(buf, 1)               # datatype
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y

    write_uint(buf, 15)              # XYABSOLUTE

    # TEXT 2
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0001_0000)     # 0CNX_YRTL
    write_sint(buf, 300)             # x

    # TEXT 3
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1000)     # 0CNX_YRTL
    write_sint(buf, -300)            # y

    write_uint(buf, 16)              # XYRELATIVE

    # TEXT 4
    write_uint(buf, 19)              # TEXT record
    if variant == 1:
        write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    elif variant in (2, 5, 12):
        write_byte(buf, 0b0110_1100)     # 0CNX_YRTL
        write_uint(buf, 1)               # textstring id
    write_sint(buf, -200)            # y
    write_uint(buf, 1)               # repetition (3x4)
    write_uint(buf, 1)               # (repetition)
    write_uint(buf, 2)               # (repetition)
    write_uint(buf, 10)              # (repetition)
    write_uint(buf, 12)              # (repetition)

    # TEXT 5
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 0)               # repetition (reuse)

    # TEXT 6
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 2)               # repetition (3 cols.)
    write_uint(buf, 1)               # (repetition)
    write_uint(buf, 10)              # (repetition)

    # TEXT 7
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 3)               # repetition (4 cols.)
    write_uint(buf, 2)               # (repetition)
    write_uint(buf, 12)              # (repetition)

    # TEXT 8
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 4)               # repetition (4 arbitrary cols.)
    write_uint(buf, 2)               # (repetition)
    write_uint(buf, 12)              # (repetition)
    write_uint(buf, 13)              # (repetition)
    write_uint(buf, 14)              # (repetition)

    # TEXT 9
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 5)               # repetition (4 arbitrary cols., grid 3)
    write_uint(buf, 2)               # (repetition)
    write_uint(buf, 3)               # (repetition)
    write_uint(buf, 4)               # (repetition)
    write_uint(buf, 5)               # (repetition)
    write_uint(buf, 6)               # (repetition)

    # TEXT 10
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 6)               # repetition (4 arbitrary cols., grid 3)
    write_uint(buf, 1)               # (repetition)
    write_uint(buf, 10)              # (repetition)
    write_uint(buf, 11)              # (repetition)

    # TEXT 11
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 7)               # repetition (3 arbitrary cols., grid 5)
    write_uint(buf, 1)               # (repetition)
    write_uint(buf, 5)               # (repetition)
    write_uint(buf, 2)               # (repetition)
    write_uint(buf, 3)               # (repetition)

    # TEXT 12
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 8)               # repetition (3x4 matrix w/arb. vectors)
    write_uint(buf, 1)               # (repetition) n-dimension
    write_uint(buf, 2)               # (repetition) m-dimension
    write_uint(buf, (10 << 4) | 0b0000)  # (repetition) n-displacement g-delta: 10/east = (10, 0)
    write_uint(buf, (11 << 2) | 0b11)    # (repetition) m-displacement g-delta: (-11, -12)
    write_sint(buf, -12)                 # (repetition g-delta)

    # TEXT 13
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 8)               # repetition (3x4 matrix w/arb. vectors)
    write_uint(buf, 1)               # (repetition) n-dimension
    write_uint(buf, 2)               # (repetition) m-dimension
    write_uint(buf, (11 << 2) | 0b01)    # (repetition) n-displacement g-delta: (11, 12)
    write_sint(buf, 12)
    write_uint(buf, (10 << 4) | 0b1010)  # (repetition) n-displacement g-delta: 10/northwest = (-10, 10)

    # TEXT 14
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 9)               # repetition (3x arb. vector)
    write_uint(buf, 1)               # (repetition) dimension
    write_uint(buf, (11 << 2) | 0b01)   # (repetition) n-displacement g-delta: (11, 12)
    write_sint(buf, 12)                 # (repetition g-delta)

    # TEXT 15
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 9)               # repetition (4x arb. vector)
    write_uint(buf, 2)               # (repetition) dimension
    write_uint(buf, (10 << 4) | 0b1010)   # (repetition) n-displacement g-delta: 10/northwest = (-10, 10)

    # TEXT 16
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 10)              # repetition (9x / 8 arb. displacements)
    write_uint(buf, 7)               # (repetition) dimension
    write_uint(buf, (10 << 4) | 0b0000)   # (repetition) g-delta: 10/east = (10, 0)
    write_uint(buf, (10 << 4) | 0b0010)   # (repetition) g-delta: 10/north = (0, 10)
    write_uint(buf, (10 << 4) | 0b0100)   # (repetition) g-delta: 10/west = (-10, 0)
    if variant == 12:
        write_uint(buf, (10 << 4) | 0b0110)   # (repetition) g-delta: 10/south = (0, -10)
    else:
        write_uint(buf, (40 << 4) | 0b0110)   # (repetition) g-delta: 40/south = (0, -40)
    write_uint(buf, (10 << 4) | 0b1000)   # (repetition) g-delta: 10/northeast = (10, 10)
    write_uint(buf, (10 << 4) | 0b1010)   # (repetition) g-delta: 10/northwest = (-10, 10)
    write_uint(buf, (10 << 4) | 0b1100)   # (repetition) g-delta: 10/southwest = (-10, -10)
    if variant == 12:
        write_uint(buf, (10 << 4) | 0b1110)   # (repetition) g-delta: 20/southeast = (10, -10)
    else:
        write_uint(buf, (20 << 4) | 0b1110)   # (repetition) g-delta: 20/southeast = (20, -20)

    # TEXT 17
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 10)              # repetition (3x / 2 arb. displacements)
    write_uint(buf, 1)               # (repetition) dimension
    write_uint(buf, (11 << 2) | 0b11)   # (repetition) g-delta: (-11, 12)
    write_sint(buf, 12)                # (repetition g-delta)
    write_uint(buf, (10 << 4) | 0b1110)   # (repetition) n-displacement g-delta: 10/southeast = (10, -10)

    # TEXT 18
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 11)              # repetition (9x / grid 2 / 8 arb. displacements)
    write_uint(buf, 7)               # (repetition) dimension (9)
    write_uint(buf, 2)               # (repetition) grid
    write_uint(buf, ( 5 << 4) | 0b0000)   # (repetition) g-delta: 10/east = (10, 0)
    write_uint(buf, ( 5 << 4) | 0b0010)   # (repetition) g-delta: 10/north = (0, 10)
    write_uint(buf, ( 5 << 4) | 0b0100)   # (repetition) g-delta: 10/west = (-10, 0)
    if variant == 12:
        write_uint(buf, (5 << 4) | 0b0110)   # (repetition) g-delta: 10/south = (0, -10)
    else:
        write_uint(buf, (20 << 4) | 0b0110)   # (repetition) g-delta: 40/south = (0, -40)
    write_uint(buf, ( 5 << 4) | 0b1000)   # (repetition) g-delta: 10/northeast = (10, 10)
    write_uint(buf, ( 5 << 4) | 0b1010)   # (repetition) g-delta: 10/northwest = (-10, 10)
    write_uint(buf, ( 5 << 4) | 0b1100)   # (repetition) g-delta: 10/southwest = (-10, -10)
    if variant == 12:
        write_uint(buf, (5 << 4) | 0b1110)   # (repetition) g-delta: 20/southeast = (-10, -10)
    else:
        write_uint(buf, (10 << 4) | 0b1110)   # (repetition) g-delta: 20/southeast = (-20, -20)

    # TEXT 19
    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0000_1100)     # 0CNX_YRTL
    write_sint(buf, -200)            # y
    write_uint(buf, 11)              # repetition (3x / grid 3 / 2 arb. displacements)
    write_uint(buf, 1)               # (repetition) dimension
    write_uint(buf, 3)               # (repetition) grid
    write_uint(buf, (4 << 2) | 0b11)   # (repetition) g-delta: (-12, 12)
    write_sint(buf, 4)                 # (repetition g-delta)
    write_uint(buf, (3 << 4) | 0b1110)   # (repetition) n-displacement g-delta: 9/southeast = (9, -9)

    if variant == 12:
        write_uint(buf, 6)           # TEXTSTRING record (explicit id)
        write_bstring(buf, b'A')
        write_uint(buf, 1)           # id

        write_uint(buf, 6)           # TEXTSTRING record (explicit id)
        write_bstring(buf, b'B')
        write_uint(buf, 2)           # id

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_common(BytesIO(), 1)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    common_tests(layout)

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        assert gg.string.string == 'TEXT_ABC', f'textstring #{ii}'

    assert geometry[16].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 20]
    assert geometry[16].repetition.y_displacements == [0, 10, 0, -40, 10, 10, -10, -20]

    assert geometry[18].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 20]
    assert geometry[18].repetition.y_displacements == [0, 10, 0, -40, 10, 10, -10, -20]


def test_file_2() -> None:
    buf = write_file_common(BytesIO(), 2)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    common_tests(layout)

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        if ii in (1, 2, 3):
            assert gg.string == 2, f'textstring #{ii}'
        else:
            assert gg.string == 1, f'textstring #{ii}'

    assert geometry[16].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 20]
    assert geometry[16].repetition.y_displacements == [0, 10, 0, -40, 10, 10, -10, -20]

    assert geometry[18].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 20]
    assert geometry[18].repetition.y_displacements == [0, 10, 0, -40, 10, 10, -10, -20]

    assert layout.textstrings[1].string == 'A'
    assert layout.textstrings[2].string == 'B'


def test_file_5() -> None:
    buf = write_file_common(BytesIO(), 5)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    common_tests(layout)

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        if ii in (1, 2, 3):
            assert gg.string == 0, f'textstring #{ii}'
        else:
            assert gg.string == 1, f'textstring #{ii}'

    assert geometry[16].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 20]
    assert geometry[16].repetition.y_displacements == [0, 10, 0, -40, 10, 10, -10, -20]

    assert geometry[18].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 20]
    assert geometry[18].repetition.y_displacements == [0, 10, 0, -40, 10, 10, -10, -20]

    assert layout.textstrings[0].string == 'A'
    assert layout.textstrings[1].string == 'B'


def test_file_12() -> None:
    buf = write_file_common(BytesIO(), 12)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    common_tests(layout)

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        if ii in (1, 2, 3):
            assert gg.string == 2, f'textstring #{ii}'
        else:
            assert gg.string == 1, f'textstring #{ii}'

    assert geometry[16].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 10]
    assert geometry[16].repetition.y_displacements == [0, 10, 0, -10, 10, 10, -10, -10]

    assert geometry[18].repetition.x_displacements == [10, 0, -10, 0, 10, -10, -10, 10]
    assert geometry[18].repetition.y_displacements == [0, 10, 0, -10, 10, 10, -10, -10]

    assert layout.textstrings[1].string == 'A'
    assert layout.textstrings[2].string == 'B'


def write_file_3(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with one textstring with explicit id, and one with an implicit id.
    Should fail.
    '''
    buf.write(HEADER)

    write_uint(buf, 6)           # TEXTSTRING record (explicit id)
    write_bstring(buf, b'A')
    write_uint(buf, 1)           # id

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)    (FAIL due to mix)
    write_bstring(buf, b'B')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0111_1011)     # 0CNX_YRTL
    write_uint(buf, 1)               # textstring id
    write_uint(buf, 1)               # layer
    write_uint(buf, 2)               # datatype
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y

    buf.write(FOOTER)
    return buf


def test_file_3() -> None:
    buf = write_file_3(BytesIO())

    buf.seek(0)
    with pytest.raises(InvalidRecordError):
        layout = OasisLayout.read(buf)


def write_file_4(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with a TEXT record that references a non-existent TEXTSTRING

    TODO add an optional check for valid references
    '''
    buf.write(HEADER)

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 1)
    write_bstring(buf, b'B')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0111_1011)     # 0CNX_YRTL
    write_uint(buf, 2)               # textstring id    # INVALID ID
    write_uint(buf, 1)               # layer
    write_uint(buf, 2)               # datatype
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y

    buf.write(FOOTER)
    return buf


def test_file_4() -> None:
    buf = write_file_4(BytesIO())

    buf.seek(0)
#    with pytest.raises(InvalidRecordError):
    layout = OasisLayout.read(buf)

    # TODO: check for invalid textstring references
    base_tests(layout)


def write_file_6(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with TEXT record that uses an un-filled modal for the repetition
    '''
    buf.write(HEADER)

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0111_1111)     # 0CNX_YRTL
    write_uint(buf, 0)               # textstring id
    write_uint(buf, 1)               # layer
    write_uint(buf, 2)               # datatype
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y
    write_uint(buf, 0)               # reuse repetition (FAIL due to empty modal)

    buf.write(FOOTER)
    return buf


def test_file_6() -> None:
    buf = write_file_6(BytesIO())

    buf.seek(0)
    with pytest.raises(InvalidDataError):
        layout = OasisLayout.read(buf)


def write_file_7(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with TEXT record that uses an un-filled modal for the layer
    '''
    buf.write(HEADER)

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0111_1010)     # 0CNX_YRTL
    write_uint(buf, 0)               # textstring id
    write_uint(buf, 2)               # datatype
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y

    buf.write(FOOTER)
    return buf


def test_file_7() -> None:
    buf = write_file_7(BytesIO())

    buf.seek(0)
    with pytest.raises(InvalidDataError):
        layout = OasisLayout.read(buf)


def write_file_8(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with TEXT record that uses an un-filled modal for the datatype
    '''
    buf.write(HEADER)

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0111_1001)     # 0CNX_YRTL
    write_uint(buf, 0)               # textstring id
    write_uint(buf, 1)               # layer
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y

    buf.write(FOOTER)
    return buf


def test_file_8() -> None:
    buf = write_file_8(BytesIO())

    buf.seek(0)
    with pytest.raises(InvalidDataError):
        layout = OasisLayout.read(buf)


def write_file_9(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with TEXT record that uses a default modal for the x coordinate
    '''
    buf.write(HEADER)

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0110_1011)     # 0CNX_YRTL
    write_uint(buf, 0)               # textstring id
    write_uint(buf, 1)               # layer
    write_uint(buf, 2)               # datatype
    write_sint(buf, -200)            # y

    buf.write(FOOTER)
    return buf


def test_file_9() -> None:
    buf = write_file_9(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    text = layout.cells[0].geometry[0]
    assert text.x == 0
    assert text.layer == 1
    assert text.datatype == 2
    assert text.y == -200


def write_file_10(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with TEXT record that uses a default modal for the y coordinate
    '''
    buf.write(HEADER)

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0111_0011)     # 0CNX_YRTL
    write_uint(buf, 0)               # textstring id
    write_uint(buf, 1)               # layer
    write_uint(buf, 2)               # datatype
    write_sint(buf, 100)             # x

    buf.write(FOOTER)
    return buf


def test_file_10() -> None:
    buf = write_file_10(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    text = layout.cells[0].geometry[0]
    assert text.y == 0
    assert text.layer == 1
    assert text.datatype == 2
    assert text.x == 100


def write_file_11(buf: IO[bytes]) -> IO[bytes]:
    '''
    File with TEXT record that uses an un-filled modal for the text string
    '''
    buf.write(HEADER)

    write_uint(buf, 5)           # TEXTSTRING record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 19)              # TEXT record
    write_byte(buf, 0b0001_1011)     # 0CNX_YRTL
    write_uint(buf, 1)               # layer
    write_uint(buf, 2)               # datatype
    write_sint(buf, 100)             # x
    write_sint(buf, -200)            # y

    buf.write(FOOTER)
    return buf


def test_file_11() -> None:
    buf = write_file_11(BytesIO())

    buf.seek(0)
    with pytest.raises(InvalidDataError):
        layout = OasisLayout.read(buf)
