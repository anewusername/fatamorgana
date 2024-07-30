# mypy: disable-error-code="union-attr"
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
    assert not layout.propnames
    assert not layout.xnames
    assert not layout.textstrings
    assert not layout.cellnames
    assert not layout.layers

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties


def write_file_1(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 14)           # CELL record (explicit)
    write_bstring(buf, b'A')      # Cell name

    write_uint(buf, 27)           # CIRCLE record
    write_byte(buf, 0b0011_1011)  # 00rX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 150)          # radius
    write_sint(buf, -100)         # geometry-x (absolute)
    write_sint(buf, 200)          # geometry-y (absolute)

    write_uint(buf, 16)           # XYRELATIVE record

    write_uint(buf, 27)           # CIRCLE record
    write_byte(buf, 0b0000_1000)  # 00rX_YRDL
    write_sint(buf, 400)          # geometry-y (relative)

    write_uint(buf, 27)           # CIRCLE record
    write_byte(buf, 0b0010_1000)  # 00rX_YRDL
    write_uint(buf, 0)            # radius
    write_sint(buf, 400)          # geometry-y (relative)

    write_uint(buf, 27)           # CIRCLE record
    write_byte(buf, 0b0010_1000)  # 00rX_YRDL
    write_uint(buf, 1)            # radius
    write_sint(buf, 400)          # geometry-y (relative)

    write_uint(buf, 27)           # CIRCLE record
    write_byte(buf, 0b0010_1000)  # 00rX_YRDL
    write_uint(buf, 6)            # radius
    write_sint(buf, 400)          # geometry-y (relative)

    write_uint(buf, 27)           # CIRCLE record
    write_byte(buf, 0b0010_1000)  # 00rX_YRDL
    write_uint(buf, 20)           # radius
    write_sint(buf, 400)          # geometry-y (relative)

    write_uint(buf, 27)           # CIRCLE record
    write_byte(buf, 0b0010_1100)  # 00rX_YRDL
    write_uint(buf, 100)          # radius
    write_sint(buf, 400)          # geometry-y (relative)
    write_uint(buf, 1)            # repetition (3x4 matrix)
    write_uint(buf, 1)            # (repetition) x-dimension
    write_uint(buf, 2)            # (repetition) y-dimension
    write_uint(buf, 400)          # (repetition) x-spacing
    write_uint(buf, 300)          # (repetition) y-spacing

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == 7
    for ii, gg in enumerate(geometry):
        msg = f'Failed on circle {ii}'
        assert gg.x == -100, msg
        assert gg.y == 200 + 400 * ii, msg

        assert gg.layer == 1, msg
        assert gg.datatype == 2, msg
        assert not gg.properties, msg
        assert gg.radius == [150, 150, 0, 1, 6, 20, 100][ii], msg

        if ii != 6:
            assert gg.repetition is None, msg

    assert geometry[6].repetition.a_count == 3, msg
    assert geometry[6].repetition.b_count == 4, msg
    assert geometry[6].repetition.a_vector == [400, 0], msg
    assert geometry[6].repetition.b_vector == [0, 300], msg
