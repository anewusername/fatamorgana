# type: ignore

from typing import List, Tuple, Iterable
from itertools import chain
from io import BytesIO, BufferedIOBase
import struct

import pytest       # type: ignore
import numpy
from numpy.testing import assert_equal

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, read_uint, read_sint, write_bstring, write_byte, PathExtensionScheme
from ..basic import InvalidRecordError, InvalidDataError
from ..main import OasisLayout


def base_tests(layout: OasisLayout) -> None:
    assert layout.version.string == '1.0'
    assert layout.unit == 1000
    assert layout.validation.checksum_type == 0

    assert not layout.properties
    assert not layout.propnames
    assert not layout.xnames
    assert not layout.textstrings
    assert not layout.cellnames
    assert not layout.layers

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'ABC'
    assert not layout.cells[0].properties


def write_file_1(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    # Trapezoid 0
    write_uint(buf, 23)          # TRAPEZOID record
    write_byte(buf, 0b0111_1011) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 100)         # width
    write_uint(buf, 50)          # height
    write_sint(buf, -20)         # delta-a
    write_sint(buf,  40)         # delta-b
    write_sint(buf, 0)           # geometry-x (absolute)
    write_sint(buf, 100)         # geometry-y (absolute)

    write_uint(buf, 16)          # XYRELATIVE record

    # Trapezoid 1
    write_uint(buf, 23)          # TRAPEZOID record
    write_byte(buf, 0b1010_1011) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 50)          # height
    write_sint(buf, 20)          # delta-a
    write_sint(buf, 40)          # delta-b
    write_sint(buf, 300)         # geometry-y (absolute)

    # Trapezoid 2
    write_uint(buf, 23)          # TRAPEZOID record
    write_byte(buf, 0b1100_1001) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 150)         # width
    write_sint(buf, 20)          # delta-a
    write_sint(buf, -20)         # delta-b
    write_sint(buf, 300)         # geometry-y (relative)

    # Trapezoid 3
    write_uint(buf, 23)          # TRAPEZOID record
    write_byte(buf, 0b0100_1101) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 150)         # width
    write_sint(buf, 20)          # delta-a
    write_sint(buf, -20)         # delta-b
    write_sint(buf, 300)         # geometry-y (relative)
    write_uint(buf, 1)           # repetition (3x4 matrix)
    write_uint(buf, 1)           # (repetition) x-dimension
    write_uint(buf, 2)           # (repetition) y-dimension
    write_uint(buf, 200)         # (repetition) x-spacing
    write_uint(buf, 300)         # (repetition) y-spacing

    write_uint(buf, 15)          # XYABSOLUTE record

    # Trapezoid 4
    write_uint(buf, 24)          # TRAPEZOID record
    write_byte(buf, 0b0111_1011) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 100)         # width
    write_uint(buf, 50)          # height
    write_sint(buf, -20)         # delta-a
    write_sint(buf, 1000)        # geometry-x (absolute)
    write_sint(buf, 100)         # geometry-y (absolute)

    write_uint(buf, 16)          # XYRELATIVE record

    # Trapezoid 5
    write_uint(buf, 24)          # TRAPEZOID record
    write_byte(buf, 0b1010_1011) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 50)          # height
    write_sint(buf, 20)          # delta-a
    write_sint(buf, 300)         # geometry-y (relative)

    # Trapezoid 6
    write_uint(buf, 24)          # TRAPEZOID record
    write_byte(buf, 0b1100_1001) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 150)         # width
    write_sint(buf, 20)          # delta-a
    write_sint(buf, 300)         # geometry-y (relative)

    # Trapezoid 7
    write_uint(buf, 24)          # TRAPEZOID record
    write_byte(buf, 0b0100_1101) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 150)         # width
    write_sint(buf, 20)          # delta-a
    write_sint(buf, 300)         # geometry-y (relative)
    write_uint(buf, 1)           # repetition (3x4 matrix)
    write_uint(buf, 1)           # (repetition) x-dimension
    write_uint(buf, 2)           # (repetition) y-dimension
    write_uint(buf, 200)         # (repetition) x-spacing
    write_uint(buf, 300)         # (repetition) y-spacing

    write_uint(buf, 15)          # XYABSOLUTE record

    # Trapezoid 8
    write_uint(buf, 25)          # TRAPEZOID record
    write_byte(buf, 0b0111_1011) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 100)         # width
    write_uint(buf, 50)          # height
    write_sint(buf, 40)          # delta-b
    write_sint(buf, 2000)        # geometry-x (absolute)
    write_sint(buf, 100)         # geometry-y (absolute)

    write_uint(buf, 16)          # XYRELATIVE record

    # Trapezoid 9
    write_uint(buf, 25)          # TRAPEZOID record
    write_byte(buf, 0b1010_1011) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 50)          # height
    write_sint(buf, 40)          # delta-b
    write_sint(buf, 300)         # geometry-y (relative)

    # Trapezoid 10
    write_uint(buf, 25)          # TRAPEZOID record
    write_byte(buf, 0b1100_1001) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 150)         # width
    write_sint(buf, -20)         # delta-b
    write_sint(buf, 300)         # geometry-y (relative)

    # Trapezoid 11
    write_uint(buf, 25)          # TRAPEZOID record
    write_byte(buf, 0b0100_1101) # OWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 150)         # width
    write_sint(buf, -20)         # delta-b
    write_sint(buf, 300)         # geometry-y (relative)
    write_uint(buf, 1)           # repetition (3x4 matrix)
    write_uint(buf, 1)           # (repetition) x-dimension
    write_uint(buf, 2)           # (repetition) y-dimension
    write_uint(buf, 200)         # (repetition) x-spacing
    write_uint(buf, 300)         # (repetition) y-spacing

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == 12

    for ii, gg in enumerate(geometry):
        msg = f'Failed on trapezoid {ii}'
        assert gg.x == 1000 * (ii // 4), msg
        assert gg.y == 100 + 300 * (ii % 4), msg

        assert gg.layer == 1, msg
        assert gg.datatype == 2, msg

        if ii % 4 == 3:
            assert gg.repetition.a_count == 3, msg
            assert gg.repetition.b_count == 4, msg
            assert gg.repetition.a_vector == [200, 0], msg
            assert gg.repetition.b_vector == [0, 300], msg
        else:
            assert gg.repetition is None, msg
        assert not gg.properties, msg

        assert gg.height == 50, msg
        if ii % 4 < 2:
            assert gg.width == 100, msg
        else:
            assert gg.width == 150, msg

        if ii in (0, 4):
            assert gg.delta_a == -20, msg
        elif 8 <= ii:
            assert gg.delta_a == 0, msg
        else:
            assert gg.delta_a == 20, msg

        if ii in (0, 1, 8, 9):
            assert gg.delta_b == 40, msg
        elif 4 <= ii < 8:
            assert gg.delta_b == 0, msg
        else:
            assert gg.delta_b == -20, msg

        assert gg.is_vertical == ((ii % 4) in (1, 2)), msg

        assert not gg.properties
