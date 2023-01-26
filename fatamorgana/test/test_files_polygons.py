# type: ignore

from io import BytesIO, BufferedIOBase

import numpy
from numpy.testing import assert_equal

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, write_bstring, write_byte
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

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'ABC'
    assert not layout.cells[0].properties


def common_tests(layout: OasisLayout) -> None:
    geometry = layout.cells[0].geometry
    assert len(geometry) == 12

    assert geometry[0].x == 0
    assert geometry[0].y == 100
    assert geometry[1].x == -200
    assert geometry[1].y == 400
    assert geometry[2].x == 0
    assert geometry[2].y == 400
    assert geometry[3].x == 0
    assert geometry[3].y == 1000
    assert geometry[4].x == 200
    assert geometry[4].y == 1000
    assert geometry[5].x == 400
    assert geometry[5].y == 1000
    assert geometry[6].x == 700
    assert geometry[6].y == 1000
    assert geometry[7].x == 900
    assert geometry[7].y == 1000
    assert geometry[8].x == 1100
    assert geometry[8].y == 1000
    assert geometry[9].x == 0
    assert geometry[9].y == 2000
    assert geometry[10].x == 1000
    assert geometry[10].y == 2000
    assert geometry[11].x == 2000
    assert geometry[11].y == 2000

    for ii, gg in enumerate(geometry):
        msg = f'Failed on polygon {ii}'
        if ii < 2:
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg
        elif ii < 10:
            assert gg.layer == 2, msg
            assert gg.datatype == 3, msg
        else:
            assert gg.layer == 2, msg
            assert gg.datatype == 1, msg

        if ii < 9:
            assert gg.repetition is None, msg
        elif ii in (9, 10):
            assert gg.repetition.a_count == 3, msg
            assert gg.repetition.b_count == 4, msg
            assert gg.repetition.a_vector == [200, 0], msg
            assert gg.repetition.b_vector == [0, 300], msg

    assert geometry[11].repetition.y_displacements == [200, 300]

    for ii in range(4):
        msg = f'Fail on poly {ii}'
        assert len(geometry[0].point_list) == 6, msg
        assert_equal(
            geometry[0].point_list,
            [[150, 0], [0, 50], [-50, 0], [0, 50], [-100, 0], [0, -100]],
            err_msg=msg,
            )
    assert len(geometry[4].point_list) == 6
    assert_equal(geometry[4].point_list, [[0, 150], [50, 0], [0, -50], [50, 0], [0, -100], [-100, 0]])

    assert len(geometry[5].point_list) == 8
    assert_equal(geometry[5].point_list, [[150, 0], [0, 50], [-50, 0], [0, 50], [-50, 0], [0, -50], [-50, 0], [0, -50]])
    assert len(geometry[6].point_list) == 9
    assert_equal(geometry[6].point_list, [[25, 0], [50, 50], [0, 50], [-50, 50], [-50, 0], [-50, -50], [0, -50], [50, -50], [25, 0]])
    assert len(geometry[7].point_list) == 9
    assert_equal(geometry[7].point_list, [[25, 0], [50, 50], [0, 50], [-50, 50], [-50, 0], [-50, -50], [10, -75], [25, -25], [40, 0]])
    assert len(geometry[8].point_list) == 9
    assert_equal(
        geometry[8].point_list,
        numpy.cumsum([[25, 0], [50, 50], [0, 50], [-50, 50], [-50, 0], [-50, -50], [10, -75], [25, -25], [45, -575]], axis=0),
        )

    for ii in range(9, 12):
        msg = f'Fail on poly {ii}'
        assert len(geometry[ii].point_list) == 6, msg
        assert_equal(geometry[ii].point_list, [[0, 150], [50, 0], [0, -50], [50, 0], [0, -100], [-100, 0]], err_msg=msg)


def write_file_common(buf: BufferedIOBase, variant: int) -> BufferedIOBase:
    '''
    '''
    assert variant in (1, 3), 'Error in test!!'

    buf.write(HEADER)

    if variant == 3:
        write_uint(buf, 7)            # PROPNAME record (implict id 0)
        write_bstring(buf, b'PROP0')  # property name

    write_uint(buf, 14)               # CELL record (explicit)
    write_bstring(buf, b'ABC')        # Cell name

    # POLYGON 0
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_1011)  # 00PX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, 0)            # geometry-x (absolute)
    write_sint(buf, 100)          # geometry-y (absolute)

    if variant == 3:
        # PROPERTY 0
        write_uint(buf, 28)           # PROPERTY record (explicit)
        write_byte(buf, 0b0001_0110)  # UUUU_VCNS
        write_uint(buf, 0)            # propname id
        write_uint(buf, 2)            # property value (real: positive reciprocal)
        write_uint(buf, 5)            # (real) 1/5

    write_uint(buf, 16)          # XYRELATIVE record

    # Polygon 1
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_1011)  # 00PX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -200)         # geometry-x (relative)
    write_sint(buf, 300)          # geometry-y (relative)

    if variant == 3:
        # PROPERTY 1
        write_uint(buf, 29)          # PROPERTY record (repeat)

    write_uint(buf, 15)          # XYABSOLUTE record

    # Polygon 2
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0011)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 0)            # pointlist: 1-delta, horiz-fisrt
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, 0)            # geometry-x (absolute)

    if variant == 3:
        # PROPERTY 2
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 3
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0000_1000)  # 00PX_YRDL
    write_sint(buf, 1000)         # geometry-y (absolute)

    if variant == 3:
        # PROPERTY 3
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 4
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0011)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 1)            # pointlist: 1-delta, vert-fisrt
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf, 50)           # (pointlist)
    write_sint(buf, 200)          # geometry-x (absolute)

    if variant == 3:
        # PROPERTY 4
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 5
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0011)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 2)            # pointlist: 2-delta
    write_uint(buf, 7)            # (pointlist) dimension
    write_uint(buf, 150 << 2 | 0b00)  # (pointlist)
    write_uint(buf,  50 << 2 | 0b01)  # (pointlist)
    write_uint(buf,  50 << 2 | 0b10)  # (pointlist)
    write_uint(buf,  50 << 2 | 0b01)  # (pointlist)
    write_uint(buf,  50 << 2 | 0b10)  # (pointlist)
    write_uint(buf,  50 << 2 | 0b11)  # (pointlist)
    write_uint(buf,  50 << 2 | 0b10)  # (pointlist)
    write_sint(buf, 400)         # geometry-x (absolute)

    if variant == 3:
        # PROPERTY 5
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 6
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0011)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 3)            # pointlist: 3-delta
    write_uint(buf, 8)            # (pointlist) dimension
    write_uint(buf, 25 << 3 | 0b000)  # (pointlist)
    write_uint(buf, 50 << 3 | 0b100)  # (pointlist)
    write_uint(buf, 50 << 3 | 0b001)  # (pointlist)
    write_uint(buf, 50 << 3 | 0b101)  # (pointlist)
    write_uint(buf, 50 << 3 | 0b010)  # (pointlist)
    write_uint(buf, 50 << 3 | 0b110)  # (pointlist)
    write_uint(buf, 50 << 3 | 0b011)  # (pointlist)
    write_uint(buf, 50 << 3 | 0b111)  # (pointlist)
    write_sint(buf, 700)         # geometry-x (absolute)

    if variant == 3:
        # PROPERTY 6
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 7
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0011)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 4)            # pointlist: g-delta
    write_uint(buf, 8)            # (pointlist) dimension
    write_uint(buf, 25 << 4 | 0b0000)  # (pointlist)
    write_uint(buf, 50 << 4 | 0b1000)  # (pointlist)
    write_uint(buf, 50 << 4 | 0b0010)  # (pointlist)
    write_uint(buf, 50 << 2 | 0b11)    # (pointlist)
    write_sint(buf, 50)
    write_uint(buf, 50 << 4 | 0b0100)  # (pointlist)
    write_uint(buf, 50 << 4 | 0b1100)  # (pointlist)
    write_uint(buf, 10 << 2 | 0b01)    # (pointlist)
    write_sint(buf, -75)
    write_uint(buf, 25 << 4 | 0b1110)  # (pointlist)
    write_sint(buf, 900)         # geometry-x (absolute)

    if variant == 3:
        # PROPERTY 7
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 8
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0011)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 5)            # pointlist: double g-delta
    write_uint(buf, 8)            # (pointlist) dimension
    write_uint(buf, 25 << 4 | 0b0000)  # (pointlist)
    write_uint(buf, 50 << 4 | 0b1000)  # (pointlist)
    write_uint(buf, 50 << 4 | 0b0010)  # (pointlist)
    write_uint(buf, 50 << 2 | 0b11)    # (pointlist)
    write_sint(buf, 50)
    write_uint(buf, 50 << 4 | 0b0100)  # (pointlist)
    write_uint(buf, 50 << 4 | 0b1100)  # (pointlist)
    write_uint(buf, 10 << 2 | 0b01)    # (pointlist)
    write_sint(buf, -75)
    write_uint(buf, 25 << 4 | 0b1110)  # (pointlist)
    write_sint(buf, 1100)         # geometry-x (absolute)

    if variant == 3:
        # PROPERTY 8
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 9
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_1111)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 1)            # pointlist: 1-delta (vert. first)
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf,  50)          # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf,  50)          # (pointlist)
    write_sint(buf,    0)         # geometry-x (absolute)
    write_sint(buf, 2000)         # geometry-y (absolute)
    write_uint(buf, 1)            # repetition (3x4 matrix)
    write_uint(buf, 1)            # (repetition) x-dimension
    write_uint(buf, 2)            # (repetition) y-dimension
    write_uint(buf, 200)          # (repetition) x-spacing
    write_uint(buf, 300)          # (repetition) y-spacing

    if variant == 3:
        # PROPERTY 9
        write_uint(buf, 29)          # PROPERTY record (repeat)

    write_uint(buf, 16)           # XYRELATIVE record

    # Polygon 10
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0110)  # 00PX_YRDL
    write_uint(buf, 1)            # datatype
    write_uint(buf, 1)            # pointlist: 1-delta (vert. first)
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf,  50)          # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf,  50)          # (pointlist)
    write_sint(buf, 1000)         # geometry-x (relative)
    write_uint(buf, 0)            # repetition (reuse)

    if variant == 3:
        # PROPERTY 10
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # Polygon 11
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0110)  # 00PX_YRDL
    write_uint(buf, 1)            # datatype
    write_uint(buf, 1)            # pointlist: 1-delta (vert. first)
    write_uint(buf, 4)            # (pointlist) dimension
    write_sint(buf, 150)          # (pointlist)
    write_sint(buf,  50)          # (pointlist)
    write_sint(buf, -50)          # (pointlist)
    write_sint(buf,  50)          # (pointlist)
    write_sint(buf, 1000)         # geometry-x (relative)
    write_uint(buf, 6)            # repetition (3 rows)
    write_uint(buf, 1)            # (repetition) dimension
    write_uint(buf, 200)          # (repetition) y-delta
    write_uint(buf, 300)          # (repetition) y-delta

    if variant == 3:
        # PROPERTY 11
        write_uint(buf, 29)          # PROPERTY record (repeat)

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_common(BytesIO(), 1)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    common_tests(layout)
    assert not layout.propnames

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        assert not gg.properties, f'Fail on polygon {ii}'


def write_file_2(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    write_uint(buf, 15)          # XYRELATIVE record

    # POLYGON 0
    write_uint(buf, 21)           # POLYGON record
    write_byte(buf, 0b0011_0011)  # 00PX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 4)            # pointlist: g-delta
    write_uint(buf, 8002)         # (pointlist) dimension
    write_uint(buf, 1000 << 2 | 0b11)    # (pointlist)
    write_sint(buf, 0)                   # (pointlist)
    for _ in range(4000):
        write_uint(buf, 10 << 2 | 0b01)  # (pointlist)
        write_sint(buf, 20)              # (pointlist)
        write_uint(buf, 10 << 2 | 0b11)  # (pointlist)
        write_sint(buf, 20)              # (pointlist)
    write_uint(buf, 1000 << 2 | 0b01)    # (pointlist)
    write_sint(buf, 0)                   # (pointlist)
    write_sint(buf, 0)           # geometry-x (absolute)

    buf.write(FOOTER)
    return buf


def test_file_2() -> None:
    buf = write_file_2(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert len(layout.cells[0].geometry) == 1

    poly = layout.cells[0].geometry[0]
    assert poly.layer == 2
    assert poly.datatype == 3
    assert poly.x == 0
    assert poly.y == 0
    assert len(poly.point_list) == 8002 + 1
    assert_equal(poly.point_list,
         ([[-1000, 0]]
        + [[(-1) ** nn * 10, 20] for nn in range(8000)]
        + [[1000, 0], [0, -20 * 8000]]),
        )


def test_file_3() -> None:
    buf = write_file_common(BytesIO(), 3)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    common_tests(layout)

    assert len(layout.propnames) == 1
    assert layout.propnames[0].string == 'PROP0'

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        msg = f'Fail on polygon {ii}'
        assert len(gg.properties) == 1, msg
        assert gg.properties[0].name == 0, msg
        assert len(gg.properties[0].values) == 1, msg
        assert gg.properties[0].values[0] * 5 == 1, msg

