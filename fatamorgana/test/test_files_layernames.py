# type: ignore

from typing import List, Tuple, Iterable, Sequence
from itertools import chain
from io import BytesIO, BufferedIOBase

import pytest       # type: ignore
import numpy
from numpy.testing import assert_equal

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, read_uint, read_sint, write_bstring, write_byte, PathExtensionScheme
from ..basic import InvalidRecordError, InvalidDataError
from ..main import OasisLayout


LAYERS = [(1, 2), (1, 5), (1, 6), (1, 8),
          (5, 2), (5, 5), (5, 6), (5, 8),
          (6, 2), (6, 5), (6, 6), (6, 8),
          (7, 2), (7, 5), (7, 6), (7, 8),
          ]

def base_tests(layout: OasisLayout) -> None:
    assert layout.version.string == '1.0'
    assert layout.unit == 1000
    assert layout.validation.checksum_type == 0

    assert not layout.properties
    assert not layout.propnames
    assert not layout.xnames
    assert not layout.textstrings
    assert not layout.cellnames

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties


def write_names_geom(buf: BufferedIOBase, short: bool = False) -> BufferedIOBase:
    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'AA')   # name
    write_uint(buf, 0)          # all layers
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'L5A')  # name
    write_uint(buf, 1)          # layer <=5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'H5A')  # name
    write_uint(buf, 2)          # layer >=5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'E5A')  # name
    write_uint(buf, 3)          # layer ==5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'I56A') # name
    write_uint(buf, 4)          # layer 5 to 6
    write_uint(buf, 5)          # (...)
    write_uint(buf, 6)          # (...)
    write_uint(buf, 0)          # all datatypes

    if short:
        return buf

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'E5L4') # name
    write_uint(buf, 3)          # layer ==5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 1)          # datatype <=4
    write_uint(buf, 4)          # (...)

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'E5H4') # name
    write_uint(buf, 3)          # layer ==5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 2)          # datatype >=4
    write_uint(buf, 4)          # (...)

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'E5E4') # name
    write_uint(buf, 3)          # layer ==5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 3)          # datatype ==4
    write_uint(buf, 4)          # (...)

    write_uint(buf, 11)         # LAYERNAME record (geometry)
    write_bstring(buf, b'E5I47') # name
    write_uint(buf, 3)          # layer ==5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 4)          # datatype 4 to 7
    write_uint(buf, 4)          # (...)
    write_uint(buf, 7)          # (...)

    return buf


def write_names_text(buf: BufferedIOBase, prefix: bytes = b'') -> BufferedIOBase:
    write_uint(buf, 12)         # LAYERNAME record (geometry)
    write_bstring(buf, prefix + b'AA')   # name
    write_uint(buf, 0)          # all layers
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 12)         # LAYERNAME record (geometry)
    write_bstring(buf, prefix + b'L5A')  # name
    write_uint(buf, 1)          # layer <=5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 12)         # LAYERNAME record (geometry)
    write_bstring(buf, prefix + b'H5A')  # name
    write_uint(buf, 2)          # layer >=5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 12)         # LAYERNAME record (geometry)
    write_bstring(buf, prefix + b'E5A')  # name
    write_uint(buf, 3)          # layer ==5
    write_uint(buf, 5)          # (...)
    write_uint(buf, 0)          # all datatypes

    write_uint(buf, 12)         # LAYERNAME record (geometry)
    write_bstring(buf, prefix + b'I56A') # name
    write_uint(buf, 4)          # layer 5 to 6
    write_uint(buf, 5)          # (...)
    write_uint(buf, 6)          # (...)
    write_uint(buf, 0)          # all datatypes
    return buf

def write_geom(buf: BufferedIOBase) -> BufferedIOBase:
    for ll, dt in LAYERS:
        write_uint(buf, 27)           # CIRCLE record
        write_byte(buf, 0b0011_1011)  # 00rX_YRDL
        write_uint(buf, ll)           # layer
        write_uint(buf, dt)           # datatype
        write_uint(buf, 150)          # radius
        write_sint(buf, ll * 1000)    # geometry-x (absolute)
        write_sint(buf, dt * 1000)    # geometry-y (absolute)
    return buf


def write_text(buf: BufferedIOBase) -> BufferedIOBase:
    for ll, dt in LAYERS:
        write_uint(buf, 19)              # TEXT record
        write_byte(buf, 0b0101_1011)     # 0CNX_YRTL
        write_bstring(buf, b'A')         # text-string
        write_uint(buf, ll)              # text-layer
        write_uint(buf, dt)              # text-datatype
        write_sint(buf, ll * 1000)       # geometry-x
        write_sint(buf, dt * 1000)       # geometry-y
    return buf


def name_test(layers: Sequence, is_textlayer: bool) -> None:
    for ii, nn in enumerate(layers):
        assert is_textlayer == nn.is_textlayer, f'Fail on layername {ii}'

        assert nn.nstring.string == ['AA', 'L5A', 'H5A', 'E5A', 'I56A',
                                     'E5L4', 'E5H4', 'E5E4', 'E5I47'][ii], msg
        assert nn.layer_interval[0] == [None, None, 5, 5, 5, 5, 5, 5, 5][ii], msg
        assert nn.layer_interval[1] == [None, 5, None, 5, 6, 5, 5, 5, 5][ii], msg
        assert nn.type_interval[0] == [None, None, None, None, None, None, 4, 4, 4][ii], msg
        assert nn.type_interval[1] == [None, None, None, None, None, 4, None, 4, 7][ii], msg


def name_test_text(layers: Sequence) -> None:
    for ii, nn in enumerate(layers):
        assert nn.is_textlayer, f'Fail on layername {ii}'

        assert nn.nstring.string == ['TAA', 'TL5A', 'TH5A', 'TE5A', 'TI56A'][ii], msg
        assert nn.layer_interval[0] == [None, None, 5, 5, 5][ii], msg
        assert nn.layer_interval[1] == [None, 5, None, 5, 6][ii], msg
        assert nn.type_interval[0] == [None, None, None, None, None][ii], msg
        assert nn.type_interval[1] == [None, None, None, None, None][ii], msg


def elem_test_geom(geometry: Sequence) -> None:
    for ii, gg in enumerate(geometry):
        msg = f'Failed on circle ({ii})'
        assert gg.x == 1000 * LAYERS[ii][0], msg
        assert gg.y == 1000 * LAYERS[ii][1], msg
        assert gg.radius == 150, msg

        assert gg.layer == LAYERS[ii][0], msg
        assert gg.datatype == LAYERS[ii][1], msg

        assert gg.repetition is None, msg
        assert not gg.properties, msg


def elem_test_text(geometry: Sequence) -> None:
    for ii, gg in enumerate(geometry):
        msg = f'Failed on text ({ii})'
        assert gg.x == 1000 * LAYERS[ii][0], msg
        assert gg.y == 1000 * LAYERS[ii][1], msg
        assert gg.string.string == 'A', msg

        assert gg.layer == LAYERS[ii][0], msg
        assert gg.datatype == LAYERS[ii][1], msg

        assert gg.repetition is None, msg
        assert not gg.properties, msg


def write_file_1(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)
    write_names_geom(buf)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    write_geom(buf)
    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == len(LAYERS)
    elem_test_geom(geometry)

    assert len(layout.layers) == 9
    name_test(layout.layers, is_textlayer=False)


def write_file_2(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)
    write_names_text(buf)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    write_text(buf)
    buf.write(FOOTER)
    return buf


def test_file_2() -> None:
    buf = write_file_2(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == len(LAYERS)
    elem_test_text(geometry)

    assert len(layout.layers) == 5
    name_test(layout.layers, is_textlayer=True)


def write_file_3(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)
    write_names_text(buf, prefix=b'T')
    write_names_geom(buf, short=True)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    write_text(buf)
    write_geom(buf)
    buf.write(FOOTER)
    return buf


def write_file_4(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    write_text(buf)
    write_geom(buf)

    write_names_text(buf, prefix=b'T')
    write_names_geom(buf, short=True)
    buf.write(FOOTER)
    return buf


def test_file_3() -> None:
    buf = write_file_3(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == 2 * len(LAYERS)
    elem_test_text(geometry[:len(LAYERS)])
    elem_test_geom(geometry[len(LAYERS):])

    assert len(layout.layers) == 2 * 5
    name_test_text(layout.layers[:5])
    name_test(layout.layers[5:], is_textlayer=False)


def test_file_4() -> None:
    buf = write_file_4(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == 2 * len(LAYERS)
    elem_test_text(geometry[:len(LAYERS)])
    elem_test_geom(geometry[len(LAYERS):])

    assert len(layout.layers) == 2 * 5
    name_test_text(layout.layers[:5])
    name_test(layout.layers[5:], is_textlayer=False)
