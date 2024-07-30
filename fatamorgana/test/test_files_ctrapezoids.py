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


def write_file_1(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 14)           # CELL record (explicit)
    write_bstring(buf, b'A')      # Cell name

    write_uint(buf, 26)           # CTRAPEZOID record
    write_byte(buf, 0b1111_1011)  # TWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 24)           # ctrapezoid type
    write_uint(buf, 100)          # width
    write_uint(buf, 200)          # height
    write_sint(buf, -100)         # geometry-x (absolute)
    write_sint(buf, 200)          # geometry-y (absolute)

    write_uint(buf, 16)           # XYRELATIVE record

    write_uint(buf, 26)           # CTRAPEZOID record
    write_byte(buf, 0b0000_1000)  # TWHX_YRDL
    write_sint(buf, 400)          # geometry-y (relative)

    write_uint(buf, 20)           # RECTANGLE record
    write_byte(buf, 0b0000_0011)  # SWHX_YRDL
    write_uint(buf, 2)            # layer
    write_uint(buf, 3)            # datatype

    h = [250, 100]
    v = [100, 250]

    wh = [h] * 8 + [v] * 8 + [h] * 6 + [v] * 2 + [h] * 2

    wh_en = ([0b11] * 16
           + [0b10] * 4
           + [0b01] * 2
           + [0b10] * 2
           + [0b11, 0b10]
           )

    for t, (x, x_en) in enumerate(zip(wh, wh_en)):
        write_uint(buf, 26)           # CTRAPEZOID record
        write_byte(buf, 0b1000_1011 | (x_en << 5))    # TWHX_YRDL
        write_uint(buf, 1)            # layer
        write_uint(buf, 2)            # datatype
        write_uint(buf, t)            # ctrapezoid type
        if x_en & 0b10:
            write_uint(buf, x[0])     # width
        if x_en & 0b01:
            write_uint(buf, x[1])     # height
        write_sint(buf, 400)          # geometry-y (relative)

        write_uint(buf, 20)           # RECTANGLE record
        write_byte(buf, 0b0000_0011)  # SWHX_YRDL
        write_uint(buf, 2)            # layer
        write_uint(buf, 3)            # datatype

    write_uint(buf, 26)           # CTRAPEZOID record
    write_byte(buf, 0b0000_1100)  # TWHX_YRDL
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

    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'A'
    assert not layout.cells[0].properties

    geometry = layout.cells[0].geometry
    assert len(geometry) == 3 + 26 * 2 + 1

    for ii, gg in enumerate(geometry):
        msg = f'Failed on shape {ii}'
        assert gg.x == -100, msg
        assert gg.y == 200 + 400 * ((ii + 1) // 2), msg

        if ii < 2 or (3 <= ii < 55 and ii % 2 == 1):
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg
        else:
            assert gg.layer == 2, msg
            assert gg.datatype == 3, msg

        if ii < 3:
            assert gg.width == 100, msg
            assert gg.height == 200, msg

        assert not gg.properties, msg

        if 3 <= ii < 55:
            ct_type = (ii - 3) // 2
            is_ctrapz = ii % 2 == 1
            if is_ctrapz:
                assert gg.ctrapezoid_type == ct_type, msg
            if ct_type in range(16, 20):
                assert gg.height == [250, None][is_ctrapz], msg
            elif ct_type in (20, 21):
                assert gg.width == [250, None][is_ctrapz], msg
            elif ct_type in range(22, 24) or ct_type == 25:
                assert gg.height == [100, None][is_ctrapz], msg
            else:
                if ct_type < 8 or 16 <= ct_type < 25 or 26 <= ct_type:
                    assert gg.width == 250, msg
                    assert gg.height == 100, msg
                else:
                    assert gg.width == 100, msg
                    assert gg.height == 250, msg
        elif ii < 3 and ii % 2:
            assert gg.ctrapezoid_type == 24, msg
        elif ii == 55:
            assert gg.ctrapezoid_type == 25, msg

    assert geometry[55].repetition.a_count == 3
    assert geometry[55].repetition.b_count == 4
    assert geometry[55].repetition.a_vector == [400, 0]
    assert geometry[55].repetition.b_vector == [0, 300]


def write_file_2(buf: IO[bytes]) -> IO[bytes]:
    """
    """
    buf.write(HEADER)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'A')     # Cell name

    # Shouldn't access (undefined) height modal, despite not having a height.
    write_uint(buf, 26)           # CTRAPEZOID record
    write_byte(buf, 0b1101_1011)  # TWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 16)           # ctrapezoid type
    write_uint(buf, 200)          # width
    write_sint(buf, -100)         # geometry-x (absolute)
    write_sint(buf, 200)          # geometry-y (absolute)

    write_uint(buf, 16)           # XYRELATIVE record

    write_uint(buf, 26)           # CTRAPEZOID record
    write_byte(buf, 0b0000_1000)  # TWHX_YRDL
    write_sint(buf, 400)          # geometry-y (relative)

    write_uint(buf, 14)           # CELL record (explicit)
    write_bstring(buf, b'B')      # Cell name

    # Shouldn't access (undefined) width modal, despite not having a width.
    write_uint(buf, 26)           # CTRAPEZOID record
    write_byte(buf, 0b1011_1011)  # TWHX_YRDL
    write_uint(buf, 1)            # layer
    write_uint(buf, 2)            # datatype
    write_uint(buf, 20)           # ctrapezoid type
    write_uint(buf, 200)          # height
    write_sint(buf, -100)         # geometry-x (absolute)
    write_sint(buf, 200)          # geometry-y (absolute)

    write_uint(buf, 16)           # XYRELATIVE record

    write_uint(buf, 26)           # CTRAPEZOID record
    write_byte(buf, 0b0000_1000)  # TWHX_YRDL
    write_sint(buf, 400)          # geometry-y (relative)

    buf.write(FOOTER)
    return buf


def test_file_2() -> None:
    buf = write_file_2(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    assert len(layout.cells) == 2
    assert layout.cells[0].name.string == 'A'
    assert layout.cells[1].name.string == 'B'
    assert not layout.cells[0].properties
    assert not layout.cells[1].properties

    for ii, cc in enumerate(layout.cells):
        for jj, gg in enumerate(cc.geometry):
            msg = f'Fail in cell {ii}, ctrapezoid {jj}'
            assert not gg.properties, msg
            assert gg.layer == 1, msg
            assert gg.datatype == 2, msg
            assert gg.x == -100, msg

    geometry = layout.cells[0].geometry
    assert geometry[0].width == 200
    assert geometry[1].width == 200
    assert geometry[0].ctrapezoid_type == 16
    assert geometry[1].ctrapezoid_type == 16
    assert geometry[0].y == 200
    assert geometry[1].y == 600

    geometry = layout.cells[1].geometry
    assert geometry[0].height == 200
    assert geometry[1].height == 200
    assert geometry[0].ctrapezoid_type == 20
    assert geometry[1].ctrapezoid_type == 20
    assert geometry[0].y == 200
    assert geometry[1].y == 600

