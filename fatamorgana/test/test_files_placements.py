# mypy: disable-error-code="union-attr"
from typing import IO, cast
from io import BytesIO

from numpy.testing import assert_equal

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, write_bstring, write_byte, write_float32, write_float64
from ..records import Rectangle
from ..main import OasisLayout


def base_tests(layout: OasisLayout) -> None:
    assert layout.version.string == '1.0'
    assert layout.unit == 1000
    assert layout.validation.checksum_type == 0

    assert not layout.properties
    assert not layout.propnames
    assert not layout.xnames
    assert not layout.textstrings
    assert not layout.layers


def write_rectangle(buf: IO[bytes], pos: tuple[int, int] = (300, -400)) -> None:
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0111_1011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, pos[0])       # geometry-x (absolute)
    write_sint(buf, pos[1])       # geometry-y (absolute)


def write_file_1(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'A')       # Cell name

    write_rectangle(buf)

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'TOP')     # Cell name

    write_uint(buf, 16)            # XYRELATIVE record

    # PLACEMENT 0
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b1011_0000)   # CNXY_RAAF
    write_bstring(buf, b'A')       # cell reference
    write_sint(buf, -300)          # placement-x (relative)
    write_sint(buf, 400)           # placement-y (relative)

    # PLACEMENT 1
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_0000)   # CNXY_RAAF
    write_sint(buf, 0)             # placement-x (relative)
    write_sint(buf, 400)           # placement-y (relative)

    # PLACEMENT 2
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0001_0000)   # CNXY_RAAF
    write_sint(buf, 400)           # placement-y (relative)

    # PLACEMENT 3
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0010_0000)   # CNXY_RAAF
    write_sint(buf, 300)           # placement-x (relative)

    write_uint(buf, 15)            # XYABSOLUTE record

    # PLACEMENT 4
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_0001)   # CNXY_RAAF
    write_sint(buf, 700)           # placement-x (absolute)
    write_sint(buf, 400)           # placement-y (absolute)

    write_uint(buf, 16)            # XYRELATIVE record

    # PLACEMENT 5
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0001_0010)   # CNXY_RAAF
    write_sint(buf, 1000)          # placement-y (relative)

    # PLACEMENT 6
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0001_0011)   # CNXY_RAAF
    write_sint(buf, 1000)          # placement-y (relative)

    write_uint(buf, 15)            # XYABSOLUTE record

    # PLACEMENT 7
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_1111)   # CNXY_RAAF
    write_sint(buf, 2000)          # placement-x (absolute)
    write_sint(buf, 0)             # placement-y (absolute)
    write_uint(buf, 1)             # repetition (3x4 matrix)
    write_uint(buf, 1)             # (repetition) x-dimension
    write_uint(buf, 2)             # (repetition) y-dimension
    write_uint(buf, 300)           # (repetition) x-spacing
    write_uint(buf, 300)           # (repetition) y-spacing

    write_uint(buf, 16)            # XYRELATIVE record

    # PLACEMENT 8
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_1111)   # CNXY_RAAF
    write_sint(buf, 2000)          # placement-x (relative)
    write_sint(buf, 0)             # placement-y (relative)
    write_uint(buf, 0)             # repetition (reuse)

    # PLACEMENT 9
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_1111)   # CNXY_RAAF
    write_sint(buf, 2000)          # placement-x (relative)
    write_sint(buf, 0)             # placement-y (relative)
    write_uint(buf, 2)             # repetition (3 cols.)
    write_uint(buf, 1)             # (repetition) count
    write_uint(buf, 320)           # (repetition) spacing

    # PLACEMENT 10
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_1111)   # CNXY_RAAF
    write_sint(buf, 2000)          # placement-x (relative)
    write_sint(buf, 0)             # placement-y (relative)
    write_uint(buf, 3)             # repetition (4 rows)
    write_uint(buf, 2)             # (repetition) count
    write_uint(buf, 310)           # (repetition) spacing

    # PLACEMENT 11
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_1111)   # CNXY_RAAF
    write_sint(buf, 2000)          # placement-x (relative)
    write_sint(buf, 0)             # placement-y (relative)
    write_uint(buf, 4)             # repetition (4 arbitrary cols.)
    write_uint(buf, 2)             # (repetition) dimension
    write_uint(buf, 320)           # (repetition) spacing
    write_uint(buf, 330)           # (repetition) spacing
    write_uint(buf, 340)           # (repetition) spacing

    # PLACEMENT 12
    write_uint(buf, 17)            # PLACEMENT (simple)
    write_byte(buf, 0b0011_1111)   # CNXY_RAAF
    write_sint(buf, 2000)          # placement-x (relative)
    write_sint(buf, 0)             # placement-y (relative)
    write_uint(buf, 8)             # repetition (3x4 matrix, arbitrary vectors)
    write_uint(buf, 1)             # (repetition) n-dimension
    write_uint(buf, 2)             # (repetition) m-dimension
    write_uint(buf, 310 << 2 | 0b01)    # (repetition) n-displacement g-delta: (310, 320)
    write_sint(buf, 320)                # (repetition g-delta)
    write_uint(buf, 330 << 4 | 0b1010)  # (repetition) m-displacement g-delta: 330-northwest (-330, 330)

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 2
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties
    assert not layout.cells[0].placements
    assert layout.cells[1].name.string == 'TOP'
    assert not layout.cells[1].properties
    assert not layout.cells[1].geometry

    geometry = cast(list[Rectangle], layout.cells[0].geometry)
    assert len(geometry) == 1
    assert geometry[0].layer == 1
    assert geometry[0].datatype == 2
    assert geometry[0].width == 100
    assert geometry[0].height == 200
    assert geometry[0].x == 300
    assert geometry[0].y == -400

    placements = layout.cells[1].placements
    assert len(placements) == 13
    for ii, pp in enumerate(placements):
        msg = f'Failed on placement {ii}'

        assert not pp.properties, msg
        assert pp.name.string == 'A', msg

        if ii < 3:
            assert pp.x == -300, msg
        elif ii == 3:
            assert pp.x == 0, msg
        elif 4 <= ii < 7:
            assert pp.x == 700, msg
        else:
            assert pp.x == 2000 * (ii - 6), msg

        if ii < 3:
            assert pp.y == 400 * (ii + 1), msg
        elif ii >= 7:
            assert pp.y == 0, msg

        if ii < 4 or ii == 5:
            assert not bool(pp.flip), msg
        else:
            assert bool(pp.flip), msg

        if ii < 5:
            assert pp.angle == 0, msg
        elif ii in (5, 6):
            assert pp.angle == 90, msg
        elif ii >= 7:
            assert pp.angle == 270, msg

        if ii < 7:
            assert pp.repetition is None, msg
        elif ii in (7, 8):
            assert pp.repetition.a_count == 3, msg
            assert pp.repetition.b_count == 4, msg
            assert pp.repetition.a_vector == [300, 0], msg
            assert pp.repetition.b_vector == [0, 300], msg

    assert placements[3].y == 1200
    assert placements[4].y == 400
    assert placements[5].y == 1400
    assert placements[6].y == 2400

    assert placements[9].repetition.a_count == 3
    assert placements[9].repetition.b_count is None
    assert placements[9].repetition.a_vector == [320, 0]
    assert placements[9].repetition.b_vector is None

    assert placements[10].repetition.a_count == 4
    assert placements[10].repetition.b_count is None
    assert placements[10].repetition.a_vector == [0, 310]
    assert placements[10].repetition.b_vector is None

    assert_equal(placements[11].repetition.x_displacements, [320, 330, 340])
    assert_equal(placements[11].repetition.y_displacements, [0, 0, 0])

    assert placements[12].repetition.a_count == 3
    assert placements[12].repetition.b_count == 4
    assert placements[12].repetition.a_vector == [310, 320]
    assert placements[12].repetition.b_vector == [-330, 330]


def write_file_common(buf: IO[bytes], variant: int) -> IO[bytes]:
    """
    """
    assert variant in (2, 3, 5, 7), 'Error in test definition!'

    buf.write(HEADER)

    if variant in (3, 5):
        write_uint(buf, 3)           # CELLNAME record (implicit id 0)
        write_bstring(buf, b'A')

        write_uint(buf, 3)           # CELLNAME record (implicit id 1)
        write_bstring(buf, b'TOP')

    if variant == 3:
        write_uint(buf, 13)          # CELL record (name ref.)
        write_uint(buf, 0)           # Cell name 0 (A)

        write_rectangle(buf)

    if variant == 2:
        write_uint(buf, 14)          # CELL record (explicit)
        write_bstring(buf, b'TOP')     # Cell name
    else:
        write_uint(buf, 13)          # CELL record (name ref.)
        write_uint(buf, 1)           # Cell name 1 (TOP)

    write_uint(buf, 16)          # XYRELATIVE record

    # PLACEMENT 0
    write_uint(buf, 17)          # PLACEMENT (simple)
    if variant == 2:
        write_byte(buf, 0b1011_0000)  # CNXY_RAAF
        write_bstring(buf, b'A')      # cell reference
    else:
        write_byte(buf, 0b1111_0000)  # CNXY_RAAF
        write_uint(buf, 0)            # cell reference
    write_sint(buf, -300)             # placement-x (relative)
    write_sint(buf, 400)              # placement-y (relative)

    # PLACEMENT 1
    write_uint(buf, 17)               # PLACEMENT (simple)
    write_byte(buf, 0b0011_0000)      # CNXY_RAAF
    write_sint(buf, 0)                # placement-x (relative)
    write_sint(buf, 400)              # placement-y (relative)

    # PLACEMENT 2
    write_uint(buf, 17)               # PLACEMENT (simple)
    write_byte(buf, 0b0001_0000)      # CNXY_RAAF
    write_sint(buf, 400)              # placement-y (relative)

    # PLACEMENT 3
    write_uint(buf, 17)               # PLACEMENT (simple)
    write_byte(buf, 0b0010_0000)      # CNXY_RAAF
    write_sint(buf, 300)              # placement-x (relative)

    write_uint(buf, 15)               # XYABSOLUTE record

    # PLACEMENT 4
    write_uint(buf, 17)               # PLACEMENT (simple)
    write_byte(buf, 0b0011_0001)      # CNXY_RAAF
    write_sint(buf, 700)              # placement-x (absolute)
    write_sint(buf, 400)              # placement-y (absolute)

    write_uint(buf, 16)               # XYRELATIVE record

    # PLACEMENT 5
    write_uint(buf, 17)               # PLACEMENT (simple)
    write_byte(buf, 0b0001_0010)      # CNXY_RAAF
    write_sint(buf, 1000)             # placement-y (relative)

    # PLACEMENT 6
    write_uint(buf, 17)               # PLACEMENT (simple)
    write_byte(buf, 0b0001_0011)      # CNXY_RAAF
    write_sint(buf, 1000)             # placement-y (relative)

    if variant == 2:
        write_uint(buf, 14)          # CELL record (explicit)
        write_bstring(buf, b'A')     # Cell name

        write_rectangle(buf)
    elif variant in (5, 7):
        write_uint(buf, 13)          # CELL record (name ref.)
        write_uint(buf, 0)           # Cell name 0 (A)

        write_rectangle(buf)

    if variant == 7:
        write_uint(buf, 3)           # CELLNAME record (implicit id 0)
        write_bstring(buf, b'A')

        write_uint(buf, 3)           # CELLNAME record (implicit id 1)
        write_bstring(buf, b'TOP')

    buf.write(FOOTER)
    return buf


def test_file_2() -> None:
    buf = write_file_common(BytesIO(), 2)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    assert len(layout.cells) == 2
    assert layout.cells[0].name.string == 'TOP'
    assert not layout.cells[0].properties
    assert not layout.cells[0].geometry
    assert layout.cells[1].name.string == 'A'
    assert not layout.cells[1].properties
    assert not layout.cells[1].placements
    assert not layout.cellnames

    common_tests(layout, 2)


def test_file_3() -> None:
    buf = write_file_common(BytesIO(), 3)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    assert len(layout.cells) == 2
    assert layout.cells[0].name == 0
    assert not layout.cells[1].properties
    assert not layout.cells[1].geometry
    assert layout.cells[1].name == 1
    assert not layout.cells[0].properties
    assert not layout.cells[0].placements

    assert len(layout.cellnames) == 2
    assert layout.cellnames[0].nstring.string == 'A'
    assert layout.cellnames[1].nstring.string == 'TOP'

    common_tests(layout, 3)


def test_file_4() -> None:
    buf = write_file_4(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    assert len(layout.cells) == 2
    assert layout.cells[0].name == 1
    assert not layout.cells[0].properties
    assert not layout.cells[0].geometry
    assert layout.cells[1].name == 0
    assert not layout.cells[1].properties
    assert not layout.cells[1].placements

    assert len(layout.cellnames) == 2
    assert layout.cellnames[0].nstring.string == 'A'
    assert layout.cellnames[1].nstring.string == 'TOP'

    common_tests(layout, 4)

    for ii, pp in enumerate(layout.cells[0].placements):
        msg = f'Fail on placement {ii}'
        assert pp.repetition.a_count == 3, msg
        assert pp.repetition.b_count == 4, msg
        assert pp.repetition.a_vector == [20, 0], msg
        assert pp.repetition.b_vector == [0, 30], msg


def test_file_5() -> None:
    buf = write_file_common(BytesIO(), 5)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    assert len(layout.cells) == 2
    assert layout.cells[0].name == 1
    assert not layout.cells[0].properties
    assert not layout.cells[0].geometry
    assert layout.cells[1].name == 0
    assert not layout.cells[1].properties
    assert not layout.cells[1].placements

    assert len(layout.cellnames) == 2
    assert layout.cellnames[0].nstring.string == 'A'
    assert layout.cellnames[1].nstring.string == 'TOP'

    common_tests(layout, 5)


def test_file_7() -> None:
    buf = write_file_common(BytesIO(), 7)

    buf.seek(0)
    layout = OasisLayout.read(buf)

    assert len(layout.cells) == 2
    assert layout.cells[0].name == 1
    assert not layout.cells[0].properties
    assert not layout.cells[0].geometry
    assert layout.cells[1].name == 0
    assert not layout.cells[1].properties
    assert not layout.cells[1].placements

    assert len(layout.cellnames) == 2
    assert layout.cellnames[0].nstring.string == 'A'
    assert layout.cellnames[1].nstring.string == 'TOP'

    common_tests(layout, 7)


def common_tests(layout: OasisLayout, variant: int) -> None:
    base_tests(layout)

    if variant == 3:
        geom_cell = 0
        top_cell = 1
    else:
        geom_cell = 1
        top_cell = 0

    geometry = layout.cells[geom_cell].geometry
    assert len(geometry) == 1
    assert geometry[0].layer == 1
    assert geometry[0].datatype == 2
    assert geometry[0].width == 100
    assert geometry[0].height == 200
    assert geometry[0].x == 300
    assert geometry[0].y == -400

    placements = layout.cells[top_cell].placements
    assert len(placements) == 7
    for ii, pp in enumerate(placements):
        msg = f'Failed on placement {ii}'

        assert not pp.properties, msg
        if variant == 2:
            assert pp.name.string == 'A', msg
        else:
            assert pp.name == 0, msg

        if ii < 3:
            assert pp.x == -300, msg
        elif ii == 3:
            assert pp.x == 0, msg
        else:
            assert pp.x == 700, msg

        if ii < 3:
            assert pp.y == 400 * (ii + 1), msg

        if ii in (4, 6):
            assert bool(pp.flip), msg
        else:
            assert not bool(pp.flip), msg

        if ii in (5, 6):
            assert pp.angle == 90, msg
        else:
            assert pp.angle == 0, msg

        if variant != 4:
            assert pp.repetition is None, msg

    assert placements[3].y == 1200
    assert placements[4].y == 400
    assert placements[5].y == 1400
    assert placements[6].y == 2400


def write_file_4(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 3)            # CELLNAME record (implicit id 0)
    write_bstring(buf, b'A')

    write_uint(buf, 3)            # CELLNAME record (implicit id 1)
    write_bstring(buf, b'TOP')

    write_uint(buf, 13)           # CELL record (name ref.)
    write_uint(buf, 1)            # Cell name 1 (TOP)

    write_uint(buf, 16)           # XYRELATIVE record

    # PLACEMENT 0
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b1111_1000)  # CNXY_RAAF
    write_uint(buf, 0)            # cell reference
    write_sint(buf, -300)         # placement-x (relative)
    write_sint(buf, 400)          # placement-y (relative)
    write_uint(buf, 1)            # repetition (3x4 matrix)
    write_uint(buf, 1)            # (repetition) x-dimension
    write_uint(buf, 2)            # (repetition) y-dimension
    write_uint(buf, 20)           # (repetition) x-spacing
    write_uint(buf, 30)           # (repetition) y-spacing

    # PLACEMENT 1
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b0011_1000)  # CNXY_RAAF
    write_sint(buf, 0)            # placement-x (relative)
    write_sint(buf, 400)          # placement-y (relative)
    write_uint(buf, 0)            # repetition (reuse)

    # PLACEMENT 2
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b0001_1000)  # CNXY_RAAF
    write_sint(buf, 400)          # placement-y (relative)
    write_uint(buf, 0)            # repetition (reuse)

    # PLACEMENT 3
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b0010_1000)  # CNXY_RAAF
    write_sint(buf, 300)          # placement-x (relative)
    write_uint(buf, 0)            # repetition (reuse)

    write_uint(buf, 15)           # XYABSOLUTE record

    # PLACEMENT 4
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b0011_1001)  # CNXY_RAAF
    write_sint(buf, 700)          # placement-x (absolute)
    write_sint(buf, 400)          # placement-y (absolute)
    write_uint(buf, 0)            # repetition (reuse)

    write_uint(buf, 16)           # XYRELATIVE record

    # PLACEMENT 5
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b0001_1010)  # CNXY_RAAF
    write_sint(buf, 1000)         # placement-y (relative)
    write_uint(buf, 0)            # repetition (reuse)

    # PLACEMENT 6
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b0001_1011)  # CNXY_RAAF
    write_sint(buf, 1000)         # placement-y (relative)
    write_uint(buf, 0)            # repetition (reuse)

    write_uint(buf, 13)           # CELL record (name ref.)
    write_uint(buf, 0)            # Cell name 0 (A)

    write_rectangle(buf)

    buf.write(FOOTER)
    return buf


def write_file_6(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'TOPTOP')  # Cell name

    write_uint(buf, 16)            # XYRELATIVE record

    write_uint(buf, 18)            # PLACEMENT (mag 0.5, manhattan)
    write_byte(buf, 0b1011_0110)   # CNXY_RMAF
    write_bstring(buf, b'TOP')     # Cell reference
    write_uint(buf, 6)             # magnitude, float32
    write_float32(buf, 0.5)        # (magnitude)
    write_uint(buf, 7)             # angle, float64
    write_float64(buf, 90.0)       # (angle)
    write_sint(buf, 100)           # placement-x (relative)
    write_sint(buf, 0)             # placement-y (relative)

    write_uint(buf, 18)            # PLACEMENT (no mag, manhattan)
    write_byte(buf, 0b0011_0000)   # CNXY_RMAF
    write_sint(buf, 100)           # placement-x (relative)
    write_sint(buf, 1000)          # placement-y (relative)

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'TOP')     # Cell name

    write_uint(buf, 16)            # XYRELATIVE record

    # PLACEMENT 0
    write_uint(buf, 18)            # PLACEMENT (mag 0.5, manhattan)
    write_byte(buf, 0b1011_0110)   # CNXY_RMAF
    write_bstring(buf, b'A')       # Cell reference
    write_uint(buf, 6)             # magnitude, float32
    write_float32(buf, 0.5)        # (magnitude)
    write_uint(buf, 7)             # angle, float64
    write_float64(buf, 0.0)        # (angle)
    write_sint(buf, -150)          # placement-x (relative)
    write_sint(buf, 200)           # placement-y (relative)

    # PLACEMENT 1
    write_uint(buf, 18)            # PLACEMENT (no mag, manhattan)
    write_byte(buf, 0b0011_0000)   # CNXY_RMAF
    write_sint(buf, -150)          # placement-x (relative)
    write_sint(buf, 600)           # placement-y (relative)

    # PLACEMENT 2
    write_uint(buf, 18)            # PLACEMENT (no mag, manhattan)
    write_byte(buf, 0b0001_0000)   # CNXY_RMAF
    write_sint(buf, 400)           # placement-y (relative)

    # PLACEMENT 3
    write_uint(buf, 18)            # PLACEMENT (no mag, manhattan)
    write_byte(buf, 0b0010_0000)   # CNXY_RMAF
    write_sint(buf, 300)           # placement-x (relative)

    write_uint(buf, 15)            # XYABSOLUTE record

    # PLACEMENT 4
    write_uint(buf, 18)            # PLACEMENT (no mag, manhattan)
    write_byte(buf, 0b0011_0001)   # CNXY_RMAF
    write_sint(buf, 700)           # placement-x (absolute)
    write_sint(buf, 400)           # placement-y (absolute)

    write_uint(buf, 16)            # XYRELATIVE record

    # PLACEMENT 5
    write_uint(buf, 18)            # PLACEMENT (no mag, manhattan)
    write_byte(buf, 0b0001_0010)   # CNXY_RMAF
    write_uint(buf, 0)             # angle (uint, positive)
    write_uint(buf, 90)            # (angle)
    write_sint(buf, 1000)          # placement-y (relative)

    # PLACEMENT 6
    write_uint(buf, 18)            # PLACEMENT (no mag, manhattan)
    write_byte(buf, 0b0001_0011)   # CNXY_RMAF
    write_uint(buf, 1)             # angle (uint, negative)
    write_uint(buf, 90)            # (angle)
    write_sint(buf, 1000)          # placement-y (relative)

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'A')       # Cell name

    write_rectangle(buf)

    buf.write(FOOTER)
    return buf


def test_file_6() -> None:
    buf = write_file_6(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 3
    assert layout.cells[0].name.string == 'TOPTOP'
    assert not layout.cells[0].properties
    assert not layout.cells[0].geometry
    assert layout.cells[1].name.string == 'TOP'
    assert not layout.cells[1].properties
    assert not layout.cells[1].geometry
    assert layout.cells[2].name.string == 'A'
    assert not layout.cells[2].properties
    assert not layout.cells[2].placements

    geometry = layout.cells[2].geometry
    assert len(geometry) == 1
    assert geometry[0].layer == 1
    assert geometry[0].datatype == 2
    assert geometry[0].width == 100
    assert geometry[0].height == 200
    assert geometry[0].x == 300
    assert geometry[0].y == -400

    placements = layout.cells[1].placements
    assert len(placements) == 7
    for ii, pp in enumerate(placements):
        msg = f'Failed on placement {ii} in cell TOP'

        assert not pp.properties, msg
        assert pp.name.string == 'A', msg
        assert pp.flip == (ii in (4, 6)), msg
        assert pp.repetition is None, msg

        if ii == 0:
            assert pp.magnification == 0.5, msg
        else:
            assert pp.magnification is None, msg

        assert pp.x == [-150, -300, -300, 0, 700, 700, 700][ii], msg
        assert pp.y == [200, 800, 1200, 1200, 400, 1400, 2400][ii], msg
        assert pp.angle == [0, None, None, None, None, 90, -90][ii], msg

    placements2 = layout.cells[0].placements
    assert len(placements2) == 2
    for ii, pp in enumerate(placements2):
        msg = f'Failed on placement {ii} in cell TOPTOP'

        assert not pp.properties, msg
        assert pp.name.string == 'TOP', msg
        assert not pp.flip, msg
        assert pp.repetition is None, msg

        assert pp.angle == [90, None][ii], msg
        assert pp.magnification == [0.5, None][ii], msg
        assert pp.x == [100, 200][ii], msg
        assert pp.y == [0, 1000][ii], msg


def write_file_8(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'TOPTOP')  # Cell name

    write_uint(buf, 15)            # XYABSOLUTE record

    write_uint(buf, 18)            # PLACEMENT (mag 0.5, arbitrary angle)
    write_byte(buf, 0b1011_0110)   # CNXY_RMAF
    write_bstring(buf, b'TOP')     # Cell reference
    write_uint(buf, 6)             # magnitude, float32
    write_float32(buf, 0.5)        # (magnitude)
    write_uint(buf, 7)             # angle, float64
    write_float64(buf, 22.5)       # (angle)
    write_sint(buf, 100)           # placement-x (absolute)
    write_sint(buf, 0)             # placement-y (absolute)

    write_uint(buf, 18)            # PLACEMENT (mag 1.0, manhattan)
    write_byte(buf, 0b1011_0110)   # CNXY_RMAF
    write_bstring(buf, b'TOP')     # Cell reference
    write_uint(buf, 6)             # magnitude, float32
    write_float32(buf, 1.0)        # (magnitude)
    write_uint(buf, 7)             # angle, float64
    write_float64(buf, 0.0)        # (angle)
    write_sint(buf, 1100)          # placement-x (absolute)
    write_sint(buf, 0)             # placement-y (absolute)

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'TOP')     # Cell name

    write_uint(buf, 18)            # PLACEMENT (mag 2.0, manhattan)
    write_byte(buf, 0b1011_0110)   # CNXY_RMAF
    write_bstring(buf, b'A')       # Cell reference
    write_uint(buf, 6)             # magnitude, float32
    write_float32(buf, 2.0)        # (magnitude)
    write_uint(buf, 7)             # angle, float64
    write_float64(buf, 0.0)        # (angle)
    write_sint(buf, -100)          # placement-x (absolute)
    write_sint(buf, 100)           # placement-y (absolute)

    write_uint(buf, 18)            # PLACEMENT (mag 1.0, arbitrary angle)
    write_byte(buf, 0b1011_0110)   # CNXY_RMAF
    write_bstring(buf, b'A')       # Cell reference
    write_uint(buf, 6)             # magnitude, float32
    write_float32(buf, 1.0)        # (magnitude)
    write_uint(buf, 7)             # angle, float64
    write_float64(buf, 45.0)       # (angle)
    write_sint(buf, -150)          # placement-x (absolute)
    write_sint(buf, 1100)          # placement-y (absolute)

    write_uint(buf, 18)            # PLACEMENT (mag 0.5, arbitrary angle)
    write_byte(buf, 0b1011_1111)   # CNXY_RMAF
    write_bstring(buf, b'A')       # Cell reference
    write_uint(buf, 6)             # magnitude, float32
    write_float32(buf, 0.5)        # (magnitude)
    write_uint(buf, 7)             # angle, float64
    write_float64(buf, 135.0)      # (angle)
    write_sint(buf, -200)          # placement-x (absolute)
    write_sint(buf, 2100)          # placement-y (absolute)
    write_uint(buf, 1)             # repetition (3x4 matrix)
    write_uint(buf, 1)             # (repetition) x-dimension
    write_uint(buf, 2)             # (repetition) y-dimension
    write_uint(buf, 200)           # (repetition) x-spacing
    write_uint(buf, 300)           # (repetition) y-spacing

    write_uint(buf, 14)            # CELL record (explicit)
    write_bstring(buf, b'A')       # Cell name

    write_rectangle(buf, pos=(30, -40))

    buf.write(FOOTER)
    return buf


def test_file_8() -> None:
    buf = write_file_8(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 3
    assert layout.cells[0].name.string == 'TOPTOP'
    assert not layout.cells[0].properties
    assert not layout.cells[0].geometry
    assert layout.cells[1].name.string == 'TOP'
    assert not layout.cells[1].properties
    assert not layout.cells[1].geometry
    assert layout.cells[2].name.string == 'A'
    assert not layout.cells[2].properties
    assert not layout.cells[2].placements

    geometry = cast(list[Rectangle], layout.cells[2].geometry)
    assert len(geometry) == 1
    assert geometry[0].layer == 1
    assert geometry[0].datatype == 2
    assert geometry[0].width == 100
    assert geometry[0].height == 200
    assert geometry[0].x == 30
    assert geometry[0].y == -40

    placements = layout.cells[1].placements
    assert len(placements) == 3
    for ii, pp in enumerate(placements):
        msg = f'Failed on placement {ii} in cell TOP'

        assert not pp.properties, msg
        assert pp.name.string == 'A', msg
        assert pp.flip == (ii == 2), msg

        assert pp.magnification == [2, 1, 0.5][ii], msg
        assert pp.angle == [0, 45, 135][ii], msg

        assert pp.x == [-100, -150, -200][ii], msg
        assert pp.y == [100, 1100, 2100][ii], msg

        if ii < 2:
            assert pp.repetition is None, msg
    assert placements[2].repetition.a_count == 3
    assert placements[2].repetition.b_count == 4
    assert placements[2].repetition.a_vector == [200, 0]
    assert placements[2].repetition.b_vector == [0, 300]

    placements2 = layout.cells[0].placements
    assert len(placements2) == 2
    for ii, pp in enumerate(placements2):
        msg = f'Failed on placement {ii} in cell TOPTOP'

        assert not pp.properties, msg
        assert pp.name.string == 'TOP', msg
        assert not pp.flip, msg
        assert pp.repetition is None, msg

        assert pp.angle == [22.5, 0][ii], msg
        assert pp.magnification == [0.5, 1.0][ii], msg
        assert pp.x == [100, 1100][ii], msg
        assert pp.y == [0, 0][ii], msg
