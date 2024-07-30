# type: ignore
from typing import IO
from io import BytesIO

import pytest
from numpy.testing import assert_equal

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, write_bstring, write_byte
from ..basic import InvalidDataError
from ..main import OasisLayout


def base_tests(layout: OasisLayout) -> None:
    assert layout.version.string == '1.0'
    assert layout.unit == 1000
    assert layout.validation.checksum_type == 0

    assert not layout.properties
    assert not layout.xnames
    assert not layout.textstrings
    assert not layout.cellnames
    assert not layout.layers


def write_file_common(buf: IO[bytes], variant: int) -> IO[bytes]:
    """
    """
    include_repetitions = variant in (2, 5)

    def var_byte(buf, byte):
        if include_repetitions:
            byte |= 0b0100
        write_byte(buf, byte)

    buf.write(HEADER)

    if variant in (1, 2):
        write_uint(buf, 10)     # PROPSTRING (explicit id)
        write_bstring(buf, b'PropStringId12')
        write_uint(buf, 12)     # id

        write_uint(buf, 10)     # PROPSTRING record (explicit id)
        write_bstring(buf, b'Property string value for ID 13')
        write_uint(buf, 13)     # id

        write_uint(buf, 7)      # PROPNAME record (implicit id 0)
        write_bstring(buf, b'PROP0')

        write_uint(buf, 7)      # PROPNAME record (implicit id 1)
        write_bstring(buf, b'PROP1')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    write_uint(buf, 16)          # XYRELATIVE record

    # RECTANGLE 0
    write_uint(buf, 20)          # RECTANGLE record
    var_byte(buf, 0b0110_0011)   # SWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 100)         # width
    write_uint(buf, 200)         # height
    if include_repetitions:
        write_uint(buf, 1)           # repetition (3x2 matrix)
        write_uint(buf, 1)           # (repetition) x-dimension
        write_uint(buf, 0)           # (repetition) y-dimension
        write_uint(buf, 300)         # (repetition) x-spacing
        write_uint(buf, 320)         # (repetition) y-spacing

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0000_0100)  # UUUU_VCNS
    write_bstring(buf, b'PROPX')

    # RECTANGLE 1
    write_uint(buf, 20)           # RECTANGLE record
    var_byte(buf, 0b0111_1011)    # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 0)            # geometry-x (relative)
    write_sint(buf, 1000)         # geometry-y (relative)
    if include_repetitions:
        write_uint(buf, 0)        # repetition (reuse)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0001_0110)  # UUUU_VCNS
    write_uint(buf, 0)            # propname id
    write_uint(buf, 1)            # property value 0 (real type 1, negative int)
    write_uint(buf, 5)            # (real 1)

    # RECTANGLE 2
    write_uint(buf, 20)          # RECTANGLE record
    var_byte(buf, 0b0111_1011)   # SWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 100)         # width
    write_uint(buf, 200)         # height
    write_sint(buf, 0)           # geometry-x (relative)
    write_sint(buf, 1000)        # geometry-y (relative)
    if include_repetitions:
        write_uint(buf, 0)       # repetition (reuse)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0100_0110)  # UUUU_VCNS
    write_uint(buf, 0)            # propname id
    write_uint(buf, 8)            # prop value 0 (unsigned int)
    write_uint(buf, 25)           # (prop value)
    write_uint(buf, 9)            # prop value 1 (signed int)
    write_sint(buf, -124)         # (prop value)
    write_uint(buf, 10)           # prop value 2 (a-string)
    write_bstring(buf, b'PROP_VALUE2')
    write_uint(buf, 13)           # prop value 3 (propstring ref.)
    write_uint(buf, 12)

    # RECTANGLE 3
    write_uint(buf, 20)          # RECTANGLE record
    var_byte(buf, 0b0111_1011)   # SWHX_YRDL
    write_uint(buf, 1)           # layer
    write_uint(buf, 2)           # datatype
    write_uint(buf, 100)         # width
    write_uint(buf, 200)         # height
    write_sint(buf, 0)           # geometry-x (relative)
    write_sint(buf, 1000)        # geometry-y (relative)
    if include_repetitions:
        write_uint(buf, 0)       # repetition (reuse)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b1111_0000)  # UUUU_VCNS
    write_uint(buf, 3)            # number of values
    write_uint(buf, 0)            # prop value 0 (unsigned int)
    write_uint(buf, 25)           # (prop value)
    write_uint(buf, 9)            # prop value 1 (signed int)
    write_sint(buf, -124)         # (prop value)
    write_uint(buf, 14)           # prop value 2 (propstring ref.)
    write_uint(buf, 13)

    # RECTANGLE 4
    write_uint(buf, 20)           # RECTANGLE record
    var_byte(buf, 0b0111_1011)    # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 0)            # geometry-x (relative)
    write_sint(buf, 1000)         # geometry-y (relative)
    if include_repetitions:
        write_uint(buf, 0)        # repetition (reuse)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0000_1000)  # UUUU_VCNS

    write_uint(buf, 15)           # XYABSOLUTE record

    # TEXT 5
    write_uint(buf, 19)          # TEXT record
    var_byte(buf, 0b0101_1011)   # 0CNX_YRTL
    write_bstring(buf, b'A')     # text-string
    write_uint(buf, 2)           # text-layer
    write_uint(buf, 1)           # text-datatype
    write_sint(buf, 1000)        # geometry-x (absolute)
    write_sint(buf, 0)           # geometry-y (absolute)
    if include_repetitions:
        write_uint(buf, 0)       # repetition (reuse)

    write_uint(buf, 29)          # PROPERTY (reuse)

    # PATH 6
    write_uint(buf, 22)           # PATH record
    var_byte(buf, 0b1111_1011)    # EWPX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 10)           # half-width
    write_byte(buf, 0b0000_1111)  # extension-scheme 0000_SSEE
    write_sint(buf, 5)            # (extension-scheme)
    write_sint(buf, -5)           # (extension-scheme)
    write_uint(buf, 0)            # pointlist (1-delta, horiz. first)
    write_uint(buf, 3)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 2000)         # geometry-x (absolute)
    write_sint(buf, 0)            # geometry-y (absolute)
    if include_repetitions:
        write_uint(buf, 0)        # repetition (reuse)

    write_uint(buf, 29)           # PROPERTY (reuse)

    # POLYGON 7
    write_uint(buf, 21)           # POLYGON record
    var_byte(buf, 0b0011_1011)    # 00PX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 0)            # pointlist (1-delta, horiz. first)
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, 3000)         # geometry-x (absolute)
    write_sint(buf, 0)            # geometry-y (absolute)
    if include_repetitions:
        write_uint(buf, 0)        # repetition (reuse)

    write_uint(buf, 29)           # PROPERTY (reuse)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0000_0110)  # UUUU_VCNS
    write_uint(buf, 1)            # propname id

    if variant == 5:
        write_uint(buf, 10)     # PROPSTRING (explicit id)
        write_bstring(buf, b'PropStringId12')
        write_uint(buf, 12)     # id

        write_uint(buf, 10)     # PROPSTRING record (explicit id)
        write_bstring(buf, b'Property string value for ID 13')
        write_uint(buf, 13)     # id

        write_uint(buf, 7)      # PROPNAME record (implicit id 0)
        write_bstring(buf, b'PROP0')

        write_uint(buf, 7)      # PROPNAME record (implicit id 1)
        write_bstring(buf, b'PROP1')
    buf.write(FOOTER)
    return buf


def common_geometry_tests(layout: OasisLayout) -> None:
    geometry = layout.cells[0].geometry
    assert len(geometry) == 8

    for ii, gg in enumerate(geometry):
        msg = f'Failed on element {ii}'
        assert gg.x == [0, 0, 0, 0, 0, 1000, 2000, 3000][ii], msg
        assert gg.y == [0, 1000, 2000, 3000, 4000, 0, 0, 0][ii], msg

        if ii == 5:
            assert gg.layer == 2, msg
            assert gg.datatype == 1, msg
        else:
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg

        if ii < 5:
            assert gg.width == 100, msg
            assert gg.height == 200, msg
    assert geometry[5].string.string == 'A'
    assert_equal(geometry[6].point_list, [(150, 0), (0, 50), (-50, 0)])
    assert_equal(geometry[7].point_list, [(150, 0), (0, 50), (-50, 0),
                                          (0, 50), (-100, 0), (0, -100)])


def common_property_tests(layout: OasisLayout) -> None:
    geometry = layout.cells[0].geometry
    assert len(geometry[0].properties) == 1
    assert geometry[0].properties[0].name.string == 'PROPX'
    assert len(geometry[0].properties[0].values) == 0

    assert len(geometry[1].properties) == 1
    assert geometry[1].properties[0].name == 0
    assert len(geometry[1].properties[0].values) == 1
    assert geometry[1].properties[0].values[0] == -5

    assert len(geometry[2].properties) == 1
    assert geometry[2].properties[0].name == 0
    assert len(geometry[2].properties[0].values) == 4
    assert geometry[2].properties[0].values[0] == 25
    assert geometry[2].properties[0].values[1] == -124
    assert geometry[2].properties[0].values[2].string == 'PROP_VALUE2'
    assert geometry[2].properties[0].values[3].ref == 12

    for ii in range(3, 8):
        msg = f'Failed on element {ii}'
        assert geometry[ii].properties[0].name == 0, msg
        assert len(geometry[ii].properties[0].values) == 3, msg
        assert geometry[ii].properties[0].values[0] == 25, msg
        assert geometry[ii].properties[0].values[1] == -124, msg
        assert geometry[ii].properties[0].values[2].ref == 13, msg

    for ii in range(3, 7):
        msg = f'Failed on element {ii}'
        assert len(geometry[ii].properties) == 1, msg

    assert len(geometry[7].properties) == 2
    assert geometry[7].properties[1].name == 1


def test_file_1() -> None:
    buf = write_file_common(BytesIO(), 1)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties
    common_geometry_tests(layout)
    common_property_tests(layout)

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        msg = f'Failed on element {ii}'
        assert gg.repetition is None, msg


def test_file_2() -> None:
    buf = write_file_common(BytesIO(), 2)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties
    common_geometry_tests(layout)
    common_property_tests(layout)

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        msg = f'Failed on element {ii}'
        assert gg.repetition.a_count == 3, msg
        assert gg.repetition.b_count == 2, msg
        assert gg.repetition.a_vector == [300, 0], msg
        assert gg.repetition.b_vector == [0, 320], msg


def test_file_5() -> None:
    buf = write_file_common(BytesIO(), 5)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties
    common_geometry_tests(layout)
    common_property_tests(layout)

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        msg = f'Failed on element {ii}'
        assert gg.repetition.a_count == 3, msg
        assert gg.repetition.b_count == 2, msg
        assert gg.repetition.a_vector == [300, 0], msg
        assert gg.repetition.b_vector == [0, 320], msg


def write_file_3(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 10)     # PROPSTRING (explicit id)
    write_bstring(buf, b'PropStringId12')
    write_uint(buf, 12)     # id

    write_uint(buf, 10)     # PROPSTRING record (explicit id)
    write_bstring(buf, b'Property string value for ID 13')
    write_uint(buf, 13)     # id

    write_uint(buf, 7)      # PROPNAME record (implicit id 0)
    write_bstring(buf, b'S_GDS_PROPERTY')

    # ** CELL **
    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    write_uint(buf, 16)          # XYRELATIVE record

    # RECTANGLE 0
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_1011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 0)            # geometry-x (relative)
    write_sint(buf, 1000)         # geometry-y (relative)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0010_0111)  # UUUU_VCNS
    write_uint(buf, 0)            # propname id
    write_uint(buf, 8)            # property value 0 (unsigned int)
    write_uint(buf, 25)           # (...)
    write_uint(buf, 10)           # property value 1 (a-string)
    write_bstring(buf, b'PROP_VALUE2')

    # RECTANGLE 1
    write_uint(buf, 20)            # RECTANGLE record
    write_byte(buf, 0b0111_1011)   # SWHX_YRDL
    write_uint(buf, 1)             # layer
    write_uint(buf, 2)             # datatype
    write_uint(buf, 100)           # width
    write_uint(buf, 200)           # height
    write_sint(buf, 0)             # geometry-x (relative)
    write_sint(buf, 1000)          # geometry-y (relative)

    write_uint(buf, 28)            # PROPERTY record
    write_byte(buf, 0b1111_0001)   # UUUU_VCNS
    write_uint(buf, 2)             # number of values
    write_uint(buf, 8)             # property value 0 (unsigned int)
    write_uint(buf, 10)            # (...)
    write_uint(buf, 14)            # property value 1 (prop-string ref.)
    write_uint(buf, 13)            # (...)

    # RECTANGLE 2
    write_uint(buf, 20)            # RECTANGLE record
    write_byte(buf, 0b0111_1011)   # SWHX_YRDL
    write_uint(buf, 1)             # layer
    write_uint(buf, 2)             # datatype
    write_uint(buf, 100)           # width
    write_uint(buf, 200)           # height
    write_sint(buf, 0)             # geometry-x (relative)
    write_sint(buf, 1000)          # geometry-y (relative)

    write_uint(buf, 28)            # PROPERTY record
    write_byte(buf, 0b0000_1001)   # UUUU_VCNS

    # RECTANGLE 3
    write_uint(buf, 20)            # RECTANGLE record
    write_byte(buf, 0b0111_1011)   # SWHX_YRDL
    write_uint(buf, 1)             # layer
    write_uint(buf, 2)             # datatype
    write_uint(buf, 100)           # width
    write_uint(buf, 200)           # height
    write_sint(buf, 0)             # geometry-x (relative)
    write_sint(buf, 1000)          # geometry-y (relative)

    write_uint(buf, 29)            # PROPERTY (reuse)

    # RECTANGLE 4
    write_uint(buf, 20)            # RECTANGLE record
    write_byte(buf, 0b0111_1011)   # SWHX_YRDL
    write_uint(buf, 1)             # layer
    write_uint(buf, 2)             # datatype
    write_uint(buf, 100)           # width
    write_uint(buf, 200)           # height
    write_sint(buf, 0)             # geometry-x (relative)
    write_sint(buf, 1000)          # geometry-y (relative)

    write_uint(buf, 28)            # PROPERTY record
    write_byte(buf, 0b0000_1001)   # UUUU_VCNS

    write_uint(buf, 28)            # PROPERTY record
    write_byte(buf, 0b0010_0111)   # UUUU_VCNS
    write_uint(buf, 0)             # propname id
    write_uint(buf, 8)             # prop value 0 (unsigned int)
    write_uint(buf, 25)            # (...)
    write_uint(buf, 10)            # prop-value 1 (a-string)
    write_bstring(buf, b'PROP_VALUE2')  # (...)

    write_uint(buf, 15)          # XYABSOLUTE record

    # TEXT 5
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0101_1011)  # 0CNX_YRTL
    write_bstring(buf, b'A')      # text-string
    write_uint(buf, 2)            # text-layer
    write_uint(buf, 1)            # text-datatype
    write_sint(buf, 1000)         # geometry-x (absolute)
    write_sint(buf, 0)            # geometry-y (absolute)

    write_uint(buf, 29)           # PROPERTY (reuse)

    # PATH 6
    write_uint(buf, 22)            # PATH record
    write_byte(buf, 0b1111_1011)   # EWPX_YRDL
    write_uint(buf, 1)             # layer
    write_uint(buf, 2)             # datatype
    write_uint(buf, 10)            # half-width
    write_byte(buf, 0b0000_1111)   # extension-scheme 0000_SSEE
    write_sint(buf, 5)             # (extension-scheme)
    write_sint(buf, -5)            # (extension-scheme)
    write_uint(buf, 0)             # pointlist (1-delta, horiz. first)
    write_uint(buf, 3)             # (pointlist) dimension
    write_sint(buf, 150)           # (pointlist)
    write_sint(buf, 50)            # (pointlist)
    write_sint(buf, -50)           # (pointlist)
    write_sint(buf, 2000)          # geometry-x (absolute)
    write_sint(buf, 0)             # geometry-y (absolute)

    write_uint(buf, 29)            # PROPERTY (reuse)

    # POLYGON 7
    write_uint(buf, 21)            # POLYGON record
    write_byte(buf, 0b0011_1011)   # 00PX_YRDL
    write_uint(buf, 1)             # layer
    write_uint(buf, 2)             # datatype
    write_uint(buf, 0)             # pointlist (1-delta, horiz. first)
    write_uint(buf, 4)             # (pointlist) dimension
    write_sint(buf, 150)           # (pointlist)
    write_sint(buf, 50)            # (pointlist)
    write_sint(buf, -50)           # (pointlist)
    write_sint(buf, 50)            # (pointlist)
    write_sint(buf, 3000)          # geometry-x (absolute)
    write_sint(buf, 0)             # geometry-y (absolute)

    write_uint(buf, 29)            # PROPERTY (reuse)

    buf.write(FOOTER)
    return buf


def test_file_3() -> None:
    buf = write_file_3(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties

    geometry = layout.cells[0].geometry
    assert len(geometry) == 8
    for ii, gg in enumerate(geometry):
        msg = f'Failed on element {ii}'
        assert gg.x == [0, 0, 0, 0, 0, 1000, 2000, 3000][ii], msg
        assert gg.y == [1000, 2000, 3000, 4000, 5000, 0, 0, 0][ii], msg

        if ii == 5:
            assert gg.layer == 2, msg
            assert gg.datatype == 1, msg
        else:
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg

        if ii < 5:
            assert gg.width == 100, msg
            assert gg.height == 200, msg

        assert gg.repetition is None, msg
    assert geometry[5].string.string == 'A'
    assert_equal(geometry[6].point_list, [(150, 0), (0, 50), (-50, 0)])
    assert_equal(geometry[7].point_list, [(150, 0), (0, 50), (-50, 0),
                                          (0, 50), (-100, 0), (0, -100)])

    assert len(geometry[0].properties) == 1
    assert geometry[0].properties[0].name == 0
    assert len(geometry[0].properties[0].values) == 2
    assert geometry[0].properties[0].values[0] == 25
    assert geometry[0].properties[0].values[1].string == 'PROP_VALUE2'

    for ii in range(1, 4):
        msg = f'Failed on element {ii}'
        assert len(geometry[ii].properties) == 1, msg
        assert geometry[ii].properties[0].name == 0, msg
        assert len(geometry[ii].properties[0].values) == 2, msg
        assert geometry[ii].properties[0].values[0] == 10, msg
        assert geometry[ii].properties[0].values[1].ref == 13, msg

    assert len(geometry[4].properties) == 2
    assert geometry[4].properties[0].name == 0
    assert geometry[4].properties[1].name == 0
    assert len(geometry[4].properties[0].values) == 2
    assert len(geometry[4].properties[1].values) == 2
    assert geometry[4].properties[0].values[0] == 10
    assert geometry[4].properties[0].values[1].ref == 13
    assert geometry[4].properties[1].values[0] == 25
    assert geometry[4].properties[1].values[1].string == 'PROP_VALUE2'

    for ii in range(5, 8):
        msg = f'Failed on element {ii}'
        assert len(geometry[ii].properties) == 1, msg
        assert geometry[ii].properties[0].name == 0, msg
        assert len(geometry[ii].properties[0].values) == 2, msg
        assert geometry[ii].properties[0].values[0] == 25, msg
        assert geometry[ii].properties[0].values[1].string == 'PROP_VALUE2', msg


def write_file_4_6(buf: IO[bytes], variant: int) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 10)     # PROPSTRING (explicit id)
    write_bstring(buf, b'PropStringId12')
    write_uint(buf, 12)     # id

    write_uint(buf, 10)     # PROPSTRING record (explicit id)
    write_bstring(buf, b'Property string value for ID 13')
    write_uint(buf, 13)     # id

    if variant == 4:
        write_uint(buf, 7)      # PROPNAME record (implicit id 0)
        write_bstring(buf, b'S_GDS_PROPERTY')

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    # RECTANGLE 0
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_1011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 300)          # geometry-x (relative)
    write_sint(buf, -400)         # geometry-y (relative)

    # ** CELL **
    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'TOP')   # Cell name

    # PLACEMENT 0
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b1011_0000)  # CNXY_RAAF
    write_bstring(buf, b'A')      # cell name
    write_sint(buf, -300)         # placement-x
    write_sint(buf, 400)          # placement-y

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0010_0111)  # UUUU_VCNS
    write_uint(buf, 0)            # propname-id
    write_uint(buf, 8)            # prop-value 0 (unsigned int)
    write_uint(buf, 25)           # (...)
    write_uint(buf, 10)           # prop-value 1 (a-string)
    write_bstring(buf, b'PROP_VALUE2')

    if variant == 6:
        write_uint(buf, 28)           # PROPERTY record
        write_byte(buf, 0b0010_0111)  # UUUU_VCNS
        write_uint(buf, 0)            # propname-id
        write_uint(buf, 8)            # prop-value 0 (unsigned int)
        write_uint(buf, 26)           # (...)
        write_uint(buf, 10)           # prop-value 1 (a-string)
        write_bstring(buf, b'PROP_VALUE26')

    # PLACEMENT 1
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_0000)  # CNXY_RAAF
    write_sint(buf, 0)            # placement-x
    if variant == 4:
        write_sint(buf, 200)         # placement-y
    else:
        write_sint(buf, 400)         # placement-y

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b1111_0001)  # UUUU_VCNS
    write_uint(buf, 2)            # number of values
    write_uint(buf, 8)            # prop-value 0 (unsigned int)
    write_uint(buf, 10)           # (...)
    write_uint(buf, 14)           # prop-value 1 (prop-string ref.)
    write_uint(buf, 13)           # (...)

    # PLACEMENT 2
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0001_0000)  # CNXY_RAAF
    write_sint(buf, 400)          # placement-y

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0000_1001)  # UUUU_VCNS

    # PLACEMENT 3
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0010_0000)  # CNXY_RAAF
    write_sint(buf, 300)          # placement-x

    write_uint(buf, 29)           # PROPERTY (reuse)

    write_uint(buf, 15)           # XYABSOLUTE record

    # PLACEMENT 4
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_0001)  # CNXY_RAAF
    write_sint(buf, 700)          # placement-x (absolute)
    write_sint(buf, 400)          # placement-y (absolute)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0000_1001)  # UUUU_VCNS

    write_uint(buf, 16)           # XYRELATIVE record

    # PLACEMENT 5
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0001_0010)  # CNXY_RAAF
    write_sint(buf, 1000)         # placement-y (relative)

    write_uint(buf, 28)           # PROPERTY record
    write_byte(buf, 0b0010_0111)  # UUUU_VCNS
    write_uint(buf, 0)            # propname-id
    write_uint(buf, 8)            # prop-value 0 (unsigned int)
    write_uint(buf, 25)           # (...)
    write_uint(buf, 10)           # prop-value 1 (a-string)
    write_bstring(buf, b'PROP_VALUE2')

    # PLACEMENT 6
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0001_0011)  # CNXY_RAAF
    write_sint(buf, 1000)         # placement-y (relative)

    write_uint(buf, 29)           # PROPERTY (reuse)

    write_uint(buf, 15)           # XYABSOLUTE record

    # PLACEMENT 7
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_1111)  # CNXY_RAAF
    write_sint(buf, 2000)         # placement-x (absolute)
    write_sint(buf, 0)            # placement-y (absolute)
    write_uint(buf, 1)            # repetition (3x4 matrix)
    write_uint(buf, 1)            # (repetition) x-dimension
    write_uint(buf, 2)            # (repetition) y-dimension
    write_uint(buf, 300)          # (repetition) x-spacing
    write_uint(buf, 300)          # (repetition) y-spacing

    write_uint(buf, 29)           # PROPERTY (reuse)

    write_uint(buf, 16)           # XYRELATIVE record

    # PLACEMENT 8
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_1111)  # CNXY_RAAF
    write_sint(buf, 2000)         # placement-x
    write_sint(buf, 0)            # placement-y
    write_uint(buf, 0)            # repetition (reuse)

    write_uint(buf, 29)           # PROPERTY (reuse)

    # PLACEMENT 9
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_1111)  # CNXY_RAAF
    write_sint(buf, 2000)         # placement-x
    write_sint(buf, 0)            # placement-y
    write_uint(buf, 2)            # repetition (3 cols.)
    write_uint(buf, 1)            # (repetition) dimension
    write_uint(buf, 320)          # (repetition) offset

    write_uint(buf, 29)           # PROPERTY (reuse)

    # PLACEMENT 10
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_1111)  # CNXY_RAAF
    write_sint(buf, 2000)         # placement-x
    write_sint(buf, 0)            # placement-y
    write_uint(buf, 3)            # repetition (4 rows)
    write_uint(buf, 2)            # (repetition) dimension
    write_uint(buf, 310)          # (repetition) offset

    write_uint(buf, 29)           # PROPERTY (reuse)

    # PLACEMENT 11
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_1111)  # CNXY_RAAF
    write_sint(buf, 2000)         # placement-x
    write_sint(buf, 0)            # placement-y
    write_uint(buf, 4)            # repetition (4 arbitrary cols.)
    write_uint(buf, 2)            # (repetition) dimension
    write_uint(buf, 320)          # (repetition)
    write_uint(buf, 330)          # (repetition)
    write_uint(buf, 340)          # (repetition)

    write_uint(buf, 29)           # PROPERTY (reuse)

    # PLACEMENT 12
    write_uint(buf, 17)           # PLACEMENT record (no mag, manhattan)
    write_byte(buf, 0b0011_1111)  # CNXY_RAAF
    write_sint(buf, 2000)         # placement-x
    write_sint(buf, 0)            # placement-y
    write_uint(buf, 8)            # repetition (3x4 matrix, arbitrary vectors)
    write_uint(buf, 1)            # (repetition) n-dimension
    write_uint(buf, 2)            # (repetition) m-dimension
    write_uint(buf, 310 << 2 | 0b01)    # (repetition) n-displacement g-delta (310, 320)
    write_sint(buf, 320)
    write_uint(buf, 330 << 4 | 0b1010)  # (repetition) m-dispalcement g-delta 330/northwest = (-330, 330)

    write_uint(buf, 29)          # PROPERTY (reuse)

    if variant == 6:
        write_uint(buf, 7)      # PROPNAME record (implicit id 0)
        write_bstring(buf, b'S_GDS_PROPERTY')

    buf.write(FOOTER)
    return buf


def test_file_4() -> None:
    """
    """
    buf = write_file_4_6(BytesIO(), 4)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 2
    assert layout.cells[0].name.string == 'A'
    assert layout.cells[1].name.string == 'TOP'
    assert not layout.cells[0].properties
    assert not layout.cells[1].properties
    assert not layout.cells[0].placements
    assert not layout.cells[1].geometry

    geometry = layout.cells[0].geometry
    assert len(geometry) == 1
    assert geometry[0].x == 300
    assert geometry[0].y == -400
    assert geometry[0].layer == 1
    assert geometry[0].datatype == 2
    assert geometry[0].width == 100
    assert geometry[0].height == 200

    assert layout.propstrings[12].string == 'PropStringId12'
    assert layout.propstrings[13].string == 'Property string value for ID 13'
    assert layout.propnames[0].string == 'S_GDS_PROPERTY'

    placements = layout.cells[1].placements
    assert len(placements) == 13
    for ii, pp in enumerate(placements):
        msg = f'Failed on placement {ii}'
        assert pp.x == [-300, 0, 0, 300, 700, 700, 700, 2000, 4000, 6000, 8000, 10000, 12000][ii], msg
        assert pp.y == [400, 200, 400, 400, 400, 1400, 2400, 0, 0, 0, 0, 0, 0][ii], msg

        if ii == 4 or 6 <= ii:
            assert pp.flip, msg
        else:
            assert not pp.flip, msg

        if ii < 7:
            assert pp.repetition is None, msg

    assert len(placements[0].properties) == 1
    assert placements[0].properties[0].name == 0
    assert len(placements[0].properties[0].values) == 2
    assert placements[0].properties[0].values[0] == 25
    assert placements[0].properties[0].values[1].string == 'PROP_VALUE2'

    for ii in range(1, 5):
        msg = f'Failed on placement {ii}'
        assert len(placements[ii].properties) == 1, msg
        assert placements[ii].properties[0].name == 0, msg
        assert len(placements[ii].properties[0].values) == 2, msg
        assert placements[ii].properties[0].values[0] == 10, msg
        assert placements[ii].properties[0].values[1].ref == 13, msg

    for ii in range(5, 13):
        msg = f'Failed on placement {ii}'
        assert len(placements[ii].properties) == 1, msg
        assert placements[ii].properties[0].name == 0, msg
        assert len(placements[ii].properties[0].values) == 2, msg
        assert placements[ii].properties[0].values[0] == 25, msg
        assert placements[ii].properties[0].values[1].string == 'PROP_VALUE2', msg


def test_file_6() -> None:
    """
    """
    buf = write_file_4_6(BytesIO(), 6)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 2
    assert layout.cells[0].name.string == 'A'
    assert layout.cells[1].name.string == 'TOP'
    assert not layout.cells[0].properties
    assert not layout.cells[1].properties
    assert not layout.cells[0].placements
    assert not layout.cells[1].geometry

    geometry = layout.cells[0].geometry
    assert len(geometry) == 1
    assert geometry[0].x == 300
    assert geometry[0].y == -400
    assert geometry[0].layer == 1
    assert geometry[0].datatype == 2
    assert geometry[0].width == 100
    assert geometry[0].height == 200

    assert layout.propstrings[12].string == 'PropStringId12'
    assert layout.propstrings[13].string == 'Property string value for ID 13'
    assert layout.propnames[0].string == 'S_GDS_PROPERTY'

    placements = layout.cells[1].placements
    assert len(placements) == 13
    for ii, pp in enumerate(placements):
        msg = f'Failed on placement {ii}'
        assert pp.x == [-300, 0, 0, 300, 700, 700, 700, 2000, 4000, 6000, 8000, 10000, 12000][ii], msg
        assert pp.y == [400, 400, 400, 400, 400, 1400, 2400, 0, 0, 0, 0, 0, 0][ii], msg

        if ii == 4 or 6 <= ii:
            assert pp.flip, msg
        else:
            assert not pp.flip, msg

        if ii < 7:
            assert pp.repetition is None, msg

    assert len(placements[0].properties) == 2
    assert placements[0].properties[0].name == 0
    assert len(placements[0].properties[0].values) == 2
    assert placements[0].properties[0].values[0] == 25
    assert placements[0].properties[0].values[1].string == 'PROP_VALUE2'
    assert placements[0].properties[1].name == 0
    assert len(placements[0].properties[1].values) == 2
    assert placements[0].properties[1].values[0] == 26
    assert placements[0].properties[1].values[1].string == 'PROP_VALUE26'

    for ii in range(1, 5):
        msg = f'Failed on placement {ii}'
        assert len(placements[ii].properties) == 1, msg
        assert placements[ii].properties[0].name == 0, msg
        assert len(placements[ii].properties[0].values) == 2, msg
        assert placements[ii].properties[0].values[0] == 10, msg
        assert placements[ii].properties[0].values[1].ref == 13, msg

    for ii in range(5, 13):
        msg = f'Failed on placement {ii}'
        assert len(placements[ii].properties) == 1, msg
        assert placements[ii].properties[0].name == 0, msg
        assert len(placements[ii].properties[0].values) == 2, msg
        assert placements[ii].properties[0].values[0] == 25, msg
        assert placements[ii].properties[0].values[1].string == 'PROP_VALUE2', msg


def write_file_7_8_9(buf: IO[bytes], variant: int) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 28)               # PROPERTY record
    write_byte(buf, 0b0001_0100)      # UUUU_VCNS
    write_bstring(buf, b'FileProp1')  # property name
    write_uint(buf, 10)               # prop-value 0 (a-string)
    write_bstring(buf, b'FileProp1Value')

    write_uint(buf, 28)              # PROPERTY record
    write_byte(buf, 0b0001_0110)     # UUUU_VCNS
    write_uint(buf, 13)              # prop-name reference
    write_uint(buf, 10)              # prop-value 0 (a-string)
    write_bstring(buf, b'FileProp1Value')

    write_uint(buf, 8)      # PROPNAME record (explicit id)
    write_bstring(buf, b'FileProp2')
    write_uint(buf, 13)     # id

    # associated with PROPNAME?
    write_uint(buf, 28)          # PROPERTY record
    if variant == 8:
        # Will give an error since the value modal variable is reset by PROPNAME_ID
        write_byte(buf, 0b0001_1110)  # UUUU_VCNS
    else:
        write_byte(buf, 0b0001_0110)  # UUUU_VCNS
    write_uint(buf, 13)               # prop-name reference
    if variant != 8:
        write_uint(buf, 8)            # prop-value 0 (unsigned int)
        write_uint(buf, 17)           # (...)

    write_uint(buf, 10)     # PROPSTRING (explicit id)
    write_bstring(buf, b'FileProp2Value')
    write_uint(buf, 12)     # id

    # associated with PROPSTRING?
    write_uint(buf, 28)               # PROPERTY record
    if variant == 9:
        # Will give an error since the value modal variable is unset
        write_byte(buf, 0b0001_1110)  # UUUU_VCNS
    else:
        write_byte(buf, 0b0001_0110)  # UUUU_VCNS
    write_uint(buf, 13)               # prop-name reference
    if variant != 9:
        write_uint(buf, 8)            # prop-value 0 (unsigned int)
        write_uint(buf, 42)           # (...)

    write_uint(buf, 3)           # CELLNAME record (implicit id 0)
    write_bstring(buf, b'A')

    # associated with cell A, through CELLNAME      # TODO
    write_uint(buf, 28)               # PROPERTY record
    write_byte(buf, 0b0001_0100)      # UUUU_VCNS
    write_bstring(buf, b'CellProp0')  # prop name
    write_uint(buf, 10)               # prop-value 0 (a-string)
    write_bstring(buf, b'CPValue0')

    # ** CELL **
    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 0)           # Cell name 0 (XYZ)

    # associated with cell A
    write_uint(buf, 28)               # PROPERTY record
    write_byte(buf, 0b0001_0100)      # UUUU_VCNS
    write_bstring(buf, b'CellProp1')  # prop name
    write_uint(buf, 10)               # prop-value 0 (a-string)
    write_bstring(buf, b'CPValue')

    write_uint(buf, 28)               # PROPERTY record
    write_byte(buf, 0b0001_1100)      # UUUU_VCNS
    write_bstring(buf, b'CellProp2')  # prop name

    # RECTANGLE 0
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_1011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 300)          # geometry-x
    write_sint(buf, -400)         # geometry-y

    buf.write(FOOTER)
    return buf


def test_file_7() -> None:
    buf = write_file_7_8_9(BytesIO(), 7)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    assert len(layout.properties) == 4
    assert layout.properties[0].name.string == 'FileProp1'
    assert layout.properties[1].name == 13
    assert layout.properties[2].name == 13
    assert layout.properties[3].name == 13
    assert len(layout.properties[0].values) == 1
    assert len(layout.properties[1].values) == 1
    assert len(layout.properties[2].values) == 1
    assert len(layout.properties[3].values) == 1
    assert layout.properties[1].values[0].string == 'FileProp1Value'
    assert layout.properties[1].values[0].string == 'FileProp1Value'
    assert layout.properties[2].values[0] == 17
    assert layout.properties[3].values[0] == 42

    assert len(layout.cells) == 1
    cprops = layout.cells[0].properties
    assert len(cprops) == 2
    assert cprops[0].name.string == 'CellProp1'
    assert cprops[1].name.string == 'CellProp2'
    assert len(cprops[0].values) == 1
    assert len(cprops[1].values) == 1
    assert cprops[0].values[0].string == 'CPValue'
    assert cprops[1].values[0].string == 'CPValue'

    assert len(layout.cellnames) == 1
    cnprops = layout.cellnames[0].properties
    assert len(cnprops) == 1
    assert cnprops[0].name.string == 'CellProp0'
    assert len(cnprops[0].values) == 1
    assert cnprops[0].values[0].string == 'CPValue0'

    # TODO Document that cell properties can be attached to both
    #  the cell and the cellname

    # TODO Document that value count is ignored when using modal


def test_file_8() -> None:
    """
    """
    buf = write_file_7_8_9(BytesIO(), 8)

    buf.seek(0)
    with pytest.raises(InvalidDataError):
        _layout = OasisLayout.read(buf)


def test_file_9() -> None:
    """
    """
    buf = write_file_7_8_9(BytesIO(), 9)

    buf.seek(0)
    with pytest.raises(InvalidDataError):
        _layout = OasisLayout.read(buf)
