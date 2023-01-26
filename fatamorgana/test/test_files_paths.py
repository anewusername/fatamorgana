# type: ignore

from io import BytesIO, BufferedIOBase

from numpy.testing import assert_equal

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, write_bstring, write_byte, PathExtensionScheme
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

    write_uint(buf, 14)           # CELL record (explicit)
    write_bstring(buf, b'ABC')    # Cell name

    # PATH 0
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b1111_1011)  # EWPX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 10)           # half-width
    write_byte(buf, 0b0000_1111)  # extension-scheme 0000_SSEE
    write_sint(buf, 5)            # (extension-scheme) start
    write_sint(buf, -5)           # (extension-scheme) end
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 3)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 0)            # geometry-x (absolute)
    write_sint(buf, 100)          # geometry-y (absolute)

    write_uint(buf, 16)           # XYRELATIVE record

    # PATH 1
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b1110_1011)  # EWPX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 10)           # half-width
    write_byte(buf, 0b0000_0000)  # extension-scheme 0000_SSEE
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 3)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 200)          # geometry-y (relative)

    # PATH 2
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b1110_1001)  # EWPX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 10)           # half-width
    write_byte(buf, 0b0000_0100)  # extension-scheme 0000_SSEE
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 3)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 200)          # geometry-y (relative)

    # PATH 3
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b1110_1010)  # EWPX_YRDL
    write_uint(buf, 2)            # datatype
    write_uint(buf, 12)           # half-width
    write_byte(buf, 0b0000_0101)  # extension-scheme 0000_SSEE
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 3)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 200)          # geometry-y (relative)

    # PATH 4
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b1010_1011)  # EWPX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_byte(buf, 0b0000_1010)  # extension-scheme 0000_SSEE
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 3)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 200)          # geometry-y (relative)

    # PATH 5
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b0000_1011)  # EWPX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_sint(buf, 200)          # geometry-y (relative)

    # PATH 6
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b0000_1111)  # EWPX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_sint(buf, 200)          # geometry-y (relative)
    write_uint(buf, 1)            # repetition (3x4 matrix)
    write_uint(buf, 1)            # (repetition) x-dimension
    write_uint(buf, 2)            # (repetition) y-dimension
    write_uint(buf, 200)          # (repetition) x-spacing
    write_uint(buf, 300)          # (repetition) y-spacing

    write_uint(buf, 16)           # XYRELATIVE record

    # PATH 7
    write_uint(buf, 22)           # PATH record
    write_byte(buf, 0b0001_0101)  # EWPX_YRDL
    write_uint(buf, 1)            # layer
    write_sint(buf, 1000)         # geometry-x (relative)
    write_uint(buf, 0)            # repetition (reuse)

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == 8

    for ii, gg in enumerate(geometry):
        msg = f'Failed on path {ii}'
        if ii < 7:
            assert gg.y == 100 + ii * 200, msg
            assert gg.x == 0, msg
        else:
            assert gg.x == 1000, msg
            assert gg.y == 1300, msg

        if ii < 5:
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg
        elif ii < 7:
            assert gg.layer == 2, msg
            assert gg.datatype == 3, msg
        else:
            assert gg.layer == 1, msg
            assert gg.datatype == 3, msg

        if ii < 6:
            assert gg.repetition is None, msg
        elif ii in (7, 8):
            assert gg.repetition.a_count == 3, msg
            assert gg.repetition.b_count == 4, msg
            assert gg.repetition.a_vector == [200, 0], msg
            assert gg.repetition.b_vector == [0, 300], msg
        assert not gg.properties, msg

        if ii < 3:
            assert gg.half_width == 10, msg
        else:
            assert gg.half_width == 12, msg

        assert len(gg.point_list) == 3, msg
        assert_equal(gg.point_list, [[150, 0], [0, 50], [-50, 0]], err_msg=msg)

        if ii >= 4:
            assert gg.extension_start == (PathExtensionScheme.HalfWidth, None)
            assert gg.extension_end == (PathExtensionScheme.HalfWidth, None)

    assert geometry[0].extension_start == (PathExtensionScheme.Arbitrary, 5)
    assert geometry[1].extension_start == (PathExtensionScheme.Arbitrary, 5)
    assert geometry[2].extension_start == (PathExtensionScheme.Flush, None)
    assert geometry[3].extension_start == (PathExtensionScheme.Flush, None)
    assert geometry[0].extension_end == (PathExtensionScheme.Arbitrary, -5)
    assert geometry[1].extension_end == (PathExtensionScheme.Arbitrary, -5)
    assert geometry[2].extension_end == (PathExtensionScheme.Arbitrary, -5)
    assert geometry[3].extension_end == (PathExtensionScheme.Flush, None)
