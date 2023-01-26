# type: ignore
from typing import IO
from io import BytesIO

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

    geometry = layout.cells[0].geometry

    assert geometry[0].x == 300
    assert geometry[0].y == -400
    assert geometry[1].x == 400
    assert geometry[1].y == -500
    assert geometry[2].x == 600
    assert geometry[2].y == -300
    assert geometry[3].x == 800
    assert geometry[3].y == -300

    assert geometry[4].y == -600
    assert geometry[5].y == -900
    assert geometry[6].y == -1200
    assert geometry[7].y == -1500
    assert geometry[8].y == -1800
    assert geometry[9].y == 500
    assert geometry[10].y == 2000

    for ii, gg in enumerate(geometry[3:]):
        assert gg.x == 800, f'Failed on rectangle {ii + 3}'

    for ii, gg in enumerate(geometry):
        msg = f'Failed on rectangle {ii}'
        if ii < 4:
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg
        else:
            assert gg.layer == 2, msg
            assert gg.datatype == 3, msg

        if ii < 7:
            assert gg.width == 100, msg
            assert gg.height == 200, msg
        elif ii == 7:
            assert gg.width == 150, msg
            assert gg.height is None, msg
        else:
            assert gg.width == 150, msg
            assert gg.height == 150, msg

        if ii < 9:
            assert gg.repetition is None, msg

    assert geometry[9].repetition.a_count == 3
    assert geometry[9].repetition.b_count == 4
    assert geometry[9].repetition.a_vector == [200, 0]
    assert geometry[9].repetition.b_vector == [0, 300]

    assert geometry[10].repetition.x_displacements == [200, 300]


def write_file_common(buf: IO[bytes], variant: int) -> IO[bytes]:
    '''
    '''
    assert variant in (1, 2), 'Error in test!!'

    buf.write(HEADER)

    if variant == 2:
        write_uint(buf, 7)            # PROPNAME record (implict id 0)
        write_bstring(buf, b'PROP0')  # property name

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABC')   # Cell name

    # RECTANGLE 0
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_1011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 300)          # geometry-x (absolute)
    write_sint(buf, -400)         # geometry-y (absolute)

    if variant == 2:
        # PROPERTY 0
        write_uint(buf, 28)           # PROPERTY record (explicit)
        write_byte(buf, 0b0001_0110)  # UUUU_VCNS
        write_uint(buf, 0)            # propname id
        write_uint(buf, 2)            # property value (real: positive reciprocal)
        write_uint(buf, 5)            # (real) 1/5

    write_uint(buf, 16)          # XYRELATIVE record

    # RECTANGLE 1
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_1011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 100)          # geometry-x (relative)
    write_sint(buf, -100)         # geometry-y (relative)

    if variant == 2:
        # PROPERTY 1
        write_uint(buf, 29)          # PROPERTY record (repeat)

    write_uint(buf, 15)           # XYABSOLUTE record

    # RECTANGLE 2
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_1011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 600)          # geometry-x (absolute)
    write_sint(buf, -300)         # geometry-y (absolute)

    if variant == 2:
        # PROPERTY 2
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 3
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_0011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, 800)          # geometry-x (absolute)

    if variant == 2:
        # PROPERTY 3
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 4
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0110_1011)  # SWHX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, -600)         # geometry-y (absolute)

    if variant == 2:
        # PROPERTY 4
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 5
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0110_1000)  # SWHX_YRDL
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, -900)         # geometry-y (absolute)

    if variant == 2:
        # PROPERTY 5
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 6
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0000_1000)  # SWHX_YRDL
    write_sint(buf, -1200)        # geometry-y (absolute)

    if variant == 2:
        # PROPERTY 6
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 7
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b1100_1000)  # SWHX_YRDL
    write_uint(buf, 150)          # width
    write_sint(buf, -1500)        # geometry-y (absolute)

    if variant == 2:
        # PROPERTY 7
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 8
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0000_1000)  # SWHX_YRDL
    write_sint(buf, -1800)        # geometry-y (absolute)

    if variant == 2:
        # PROPERTY 8
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 9
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0000_1100)  # SWHX_YRDL
    write_sint(buf, 500)          # geometry-y (absolute)
    write_uint(buf, 1)            # repetition (3x4 matrix)
    write_uint(buf, 1)            # (repetition) x-dimension
    write_uint(buf, 2)            # (repetition) y-dimension
    write_uint(buf, 200)          # (repetition) x-spacing
    write_uint(buf, 300)          # (repetition) y-spacing

    if variant == 2:
        # PROPERTY 9
        write_uint(buf, 29)          # PROPERTY record (repeat)

    # RECTANGLE 10
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0000_1100)  # SWHX_YRDL
    write_sint(buf, 2000)         # geometry-y (absolute)
    write_uint(buf, 4)            # repetition (3 arbitrary cols.)
    write_uint(buf, 1)            # (repetition) dimension
    write_uint(buf, 200)          # (repetition) x-delta
    write_uint(buf, 300)          # (repetition) x-delta

    if variant == 2:
        # PROPERTY 10
        write_uint(buf, 29)          # PROPERTY record (repeat)

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_common(BytesIO(), 1)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert not layout.propnames

    geometry = layout.cells[0].geometry
    for ii, gg in enumerate(geometry):
        assert not gg.properties, f'Fail on rectangle {ii}'


def test_file_2() -> None:
    buf = write_file_common(BytesIO(), 2)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.propnames) == 1
    assert layout.propnames[0].string == 'PROP0'

    geometry = layout.cells[0].geometry

    for ii, gg in enumerate(geometry):
        msg = f'Failed on rectangle {ii}'
        assert len(gg.properties) == 1, msg
        prop = gg.properties[0]

        assert prop.name == 0, msg
        assert len(prop.values) == 1, msg
        assert prop.values[0].numerator == 1, msg
        assert prop.values[0].denominator == 5, msg

