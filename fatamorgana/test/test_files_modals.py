# type: ignore

from io import BytesIO, BufferedIOBase

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_sint, write_bstring, write_byte
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


def write_file_1(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)

    write_uint(buf, 14)           # CELL record (explicit)
    write_bstring(buf, b'A')      # Cell name

    # RECTANGLE 0
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0110_0011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 10)           # width
    write_uint(buf, 20)           # height

    # TEXT 1
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0100_0011)  # 0CNX_YRTL
    write_bstring(buf, b'A')      # text string
    write_uint(buf, 2)            # layer
    write_uint(buf, 1)            # datatype

    # RECTANGLE 2
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0001_1000)  # SWHX_YRDL
    write_sint(buf, 100)          # geometry-x (absolute)
    write_sint(buf, -100)         # geometry-y (absolute)

    # TEXT 3
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0001_1000)  # 0CNX_YRTL
    write_sint(buf, 100)          # text-x (absolute)
    write_sint(buf, -100)         # text-y (absolute)

    # RECTANGLE 4
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0001_1000)  # SWHX_YRDL
    write_sint(buf, 200)          # geometry-x (absolute)
    write_sint(buf, -200)         # geometry-y (absolute)

    # TEXT 5
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0001_1000)  # 0CNX_YRTL
    write_sint(buf, 200)          # text-x (absolute)
    write_sint(buf, -200)         # text-y (absolute)

    write_uint(buf, 16)           # XYRELATIVE record

    # RECTANGLE 6
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0001_1000)  # SWHX_YRDL
    write_sint(buf, 100)          # geometry-x (relative)
    write_sint(buf, -100)         # geometry-y (relative)

    # TEXT 7
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0001_1000)  # 0CNX_YRTL
    write_sint(buf, 100)          # text-x (relative)
    write_sint(buf, -100)         # text-y (relative)

    write_uint(buf, 14)           # CELL record (explicit)
    write_bstring(buf, b'B')      # Cell name

    # RECTANGLE 0
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0110_0011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 20)           # width
    write_uint(buf, 10)           # height

    # TEXT 1
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0100_0011)  # 0CNX_YRTL
    write_bstring(buf, b'B')      # text string
    write_uint(buf, 2)            # layer
    write_uint(buf, 1)            # datatype

    # RECTANGLE 2
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0001_1000)  # SWHX_YRDL
    write_sint(buf, 100)          # geometry-x (absolute)
    write_sint(buf, 100)          # geometry-y (absolute)

    # TEXT 3
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0001_1000)  # 0CNX_YRTL
    write_sint(buf, 100)          # text-x (absolute)
    write_sint(buf, 100)          # text-y (absolute)

    # RECTANGLE 4
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0001_1000)  # SWHX_YRDL
    write_sint(buf, 200)          # geometry-x (absolute)
    write_sint(buf, 200)          # geometry-y (absolute)

    # TEXT 5
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0001_1000)  # 0CNX_YRTL
    write_sint(buf, 200)          # text-x (absolute)
    write_sint(buf, 200)          # text-y (absolute)

    write_uint(buf, 16)           # XYRELATIVE record

    # RECTANGLE 6
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0001_1000)  # SWHX_YRDL
    write_sint(buf, 100)          # geometry-x (relative)
    write_sint(buf, 100)          # geometry-y (relative)

    # TEXT 7
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0001_1000)  # 0CNX_YRTL
    write_sint(buf, 100)          # text-x (relative)
    write_sint(buf, 100)          # text-y (relative)

    # PLACEMENT 0
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b1000_0000)  # CNXY_RAAF
    write_bstring(buf, b'A')      # Cell reference

    # PLACEMENT 1
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b0011_0000)  # CNXY_RAAF
    write_sint(buf, 50)           # placement-x (relative)
    write_sint(buf, 50)           # placement-y (relative)

    write_uint(buf, 14)           # CELL record (explicit)
    write_bstring(buf, b'TOP')    # Cell name

    # PLACEMENT 0
    write_uint(buf, 17)           # PLACEMENT (simple)
    write_byte(buf, 0b1000_0000)  # CNXY_RAAF
    write_bstring(buf, b'B')      # Cell reference

    # RECTANGLE 0
    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0110_0011)  # SWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 50)           # width
    write_uint(buf, 5)            # height

    # TEXT 1
    write_uint(buf, 19)           # TEXT record
    write_byte(buf, 0b0100_0011)  # 0CNX_YRTL
    write_bstring(buf, b'TOP')    # text string
    write_uint(buf, 2)            # layer
    write_uint(buf, 1)            # datatype

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 3
    assert layout.cells[0].name.string == 'A'
    assert layout.cells[1].name.string == 'B'
    assert layout.cells[2].name.string == 'TOP'
    assert not layout.cells[0].properties
    assert not layout.cells[1].properties
    assert not layout.cells[2].properties

    geometry = layout.cells[0].geometry
    assert len(geometry) == 8
    for ii, gg in enumerate(geometry):
        msg = f'Failed on geometry {ii} in cell A'

        if ii % 2 == 0:
            assert gg.width == 10, msg
            assert gg.height == 20, msg
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg
        else:
            assert gg.string.string == 'A', msg
            assert gg.layer == 2, msg
            assert gg.datatype == 1, msg
        assert not gg.properties, msg
        assert gg.x == (ii // 2) * 100, msg
        assert gg.y == (ii // 2) * -100, msg

    geometry = layout.cells[1].geometry
    assert len(geometry) == 8
    for ii, gg in enumerate(geometry):
        msg = f'Failed on geometry {ii} in cell B'

        if ii % 2 == 0:
            assert gg.width == 20, msg
            assert gg.height == 10, msg
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg
        else:
            assert gg.string.string == 'B', msg
            assert gg.layer == 2, msg
            assert gg.datatype == 1, msg
        assert not gg.properties, msg
        assert gg.x == (ii // 2) * 100, msg
        assert gg.y == (ii // 2) * 100, msg

    assert layout.cells[1].placements[0].name.string == 'A'
    assert layout.cells[1].placements[1].name.string == 'A'
    assert layout.cells[1].placements[0].x == 0
    assert layout.cells[1].placements[0].y == 0
    assert layout.cells[1].placements[1].x == 50
    assert layout.cells[1].placements[1].y == 50

    assert layout.cells[2].placements[0].name.string == 'B'
    assert layout.cells[2].placements[0].x == 0
    assert layout.cells[2].placements[0].y == 0

    assert layout.cells[2].geometry[0].layer == 1
    assert layout.cells[2].geometry[0].datatype == 2
    assert layout.cells[2].geometry[0].width == 50
    assert layout.cells[2].geometry[0].height == 5
    assert layout.cells[2].geometry[0].x == 0
    assert layout.cells[2].geometry[0].y == 0

    assert layout.cells[2].geometry[1].layer == 2
    assert layout.cells[2].geometry[1].datatype == 1
    assert layout.cells[2].geometry[1].string.string == 'TOP'
    assert layout.cells[2].geometry[1].x == 0
    assert layout.cells[2].geometry[1].y == 0
