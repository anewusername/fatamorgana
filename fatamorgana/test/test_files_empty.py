from typing import IO
from io import BytesIO
import struct

from .utils import MAGIC_BYTES, FOOTER
from ..basic import write_uint, write_bstring
from ..main import OasisLayout


def base_tests(layout: OasisLayout) -> None:
    assert layout.version.string == '1.0'
    assert layout.validation.checksum_type == 0

    assert not layout.properties
    assert not layout.cells
    assert not layout.cellnames
    assert not layout.propnames
    assert not layout.xnames
    assert not layout.textstrings
    assert not layout.propstrings
    assert not layout.layers


def write_file_1(buf: IO[bytes]) -> IO[bytes]:
    """
    File contains one PAD record.
    1000 units/micron
    Offset table inside START.
    """
    buf.write(MAGIC_BYTES)

    write_uint(buf, 1)           # START record
    write_bstring(buf, b'1.0')   # version
    write_uint(buf, 0)           # dbu real type: uint
    write_uint(buf, 1000)        # dbu value: 1000 per micron
    write_uint(buf, 0)           # offset table is present here
    for _ in range(6):
        write_uint(buf, 0)       # offset table (0: not strict)
        write_uint(buf, 0)       # offset table (0: no entry present)

    write_uint(buf, 0)           # PAD record

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert layout.unit == 1000


def write_file_2(buf: IO[bytes]) -> IO[bytes]:
    """
    File contains no records.
    1/2 unit/micron
    Offset table inside START.
    """
    buf.write(MAGIC_BYTES)

    write_uint(buf, 1)           # START record
    write_bstring(buf, b'1.0')   # version
    write_uint(buf, 2)           # dbu real type: fraction 1/x
    write_uint(buf, 2)           # dbu value: 1/2 per micron
    write_uint(buf, 0)           # offset table is present here
    for _ in range(6):
        write_uint(buf, 0)       # offset table (0: not strict)
        write_uint(buf, 0)       # offset table (0: no entry present)

    buf.write(FOOTER)
    return buf


def test_file_2() -> None:
    buf = write_file_2(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert layout.unit == 0.5


def write_file_3(buf: IO[bytes]) -> IO[bytes]:
    """
    File contains no records.
    10/4 unit/micron
    Offset table inside START.
    """
    buf.write(MAGIC_BYTES)

    write_uint(buf, 1)           # START record
    write_bstring(buf, b'1.0')   # version
    write_uint(buf, 4)           # dbu real type: fraction a/b
    write_uint(buf, 10)           # dbu value a
    write_uint(buf, 4)           # dbu value b: 10/4 per micron
    write_uint(buf, 0)           # offset table is present here
    for _ in range(6):
        write_uint(buf, 0)       # offset table (0: not strict)
        write_uint(buf, 0)       # offset table (0: no entry present)

    buf.write(FOOTER)
    return buf


def test_file_3() -> None:
    buf = write_file_3(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert layout.unit == 10 / 4


def write_file_4(buf: IO[bytes]) -> IO[bytes]:
    """
    File contains no records.
    12.5 unit/micron (float32)
    Offset table inside START.
    """
    buf.write(MAGIC_BYTES)

    write_uint(buf, 1)           # START record
    write_bstring(buf, b'1.0')   # version
    write_uint(buf, 6)           # dbu real type: float32
    buf.write(struct.pack("<f", 12.5))   # dbu value: 12.5
    write_uint(buf, 0)           # offset table is present here
    for _ in range(6):
        write_uint(buf, 0)       # offset table (0: not strict)
        write_uint(buf, 0)       # offset table (0: no entry present)

    buf.write(FOOTER)
    return buf


def test_file_4() -> None:
    buf = write_file_4(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert layout.unit == 12.5


def write_file_5(buf: IO[bytes]) -> IO[bytes]:
    """
    File contains no records.
    12.5 unit/micron (float64)
    Offset table inside START.
    """
    buf.write(MAGIC_BYTES)

    write_uint(buf, 1)           # START record
    write_bstring(buf, b'1.0')   # version
    write_uint(buf, 7)           # dbu real type: float64
    buf.write(struct.pack("<d", 12.5))   # dbu value: 12.5
    write_uint(buf, 0)           # offset table is present here
    for _ in range(6):
        write_uint(buf, 0)       # offset table (0: not strict)
        write_uint(buf, 0)       # offset table (0: no entry present)

    buf.write(FOOTER)
    return buf


def test_file_5() -> None:
    buf = write_file_5(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert layout.unit == 12.5
