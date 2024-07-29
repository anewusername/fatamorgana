# type: ignore
from typing import IO
from io import BytesIO

import pytest

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_bstring
from ..basic import InvalidRecordError, InvalidDataError
from ..main import OasisLayout


def base_tests(layout: OasisLayout) -> None:
    assert layout.version.string == '1.0'
    assert layout.unit == 1000
    assert layout.validation.checksum_type == 0

    assert not layout.properties
    assert not layout.propnames
    assert not layout.xnames
    assert not layout.textstrings
    assert not layout.propstrings
    assert not layout.layers


def write_file_1(buf: IO[bytes]) -> IO[bytes]:
    '''
    Single cell with explicit name 'XYZ'
    '''
    buf.write(HEADER)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'XYZ')   # Cell name

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert len(layout.cells) == 1
    assert layout.cells[0].name.string == 'XYZ'
    assert not layout.cellnames


def write_file_2(buf: IO[bytes]) -> IO[bytes]:
    '''
    Two cellnames ('XYZ', 'ABC') and two cells with name references.
    '''
    buf.write(HEADER)

    write_uint(buf, 3)           # CELLNAME record (implicit id 0)
    write_bstring(buf, b'XYZ')

    write_uint(buf, 3)           # CELLNAME record (implicit id 1)
    write_bstring(buf, b'ABC')

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 0)           # Cell name 0 (XYZ)

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 1)           # Cell name 1 (ABC)

    buf.write(FOOTER)
    return buf


def test_file_2() -> None:
    buf = write_file_2(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert len(layout.cellnames) == 2
    assert len(layout.cells) == 2
    assert layout.cellnames[0].nstring.string == 'XYZ'
    assert layout.cellnames[1].nstring.string == 'ABC'
    assert layout.cells[0].name == 0
    assert layout.cells[1].name == 1


def write_file_3(buf: IO[bytes]) -> IO[bytes]:
    '''
    Invalid file, contains a mix of explicit and implicit cellnames
    '''
    buf.write(HEADER)

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'ABC')
    write_uint(buf, 1)           # id 1

    write_uint(buf, 3)           # CELLNAME record (implicit id 0) -- Expect failure due to mix of explicit/implicit ids
    write_bstring(buf, b'XYZ')

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 0)           # Cell name 0 (XYZ)

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 1)           # Cell name 1 (ABC)

    buf.write(FOOTER)
    return buf


def test_file_3() -> None:
    buf = write_file_3(BytesIO())

    buf.seek(0)
    with pytest.raises(InvalidRecordError):
        _layout = OasisLayout.read(buf)


def write_file_4(buf: IO[bytes]) -> IO[bytes]:
    '''
    Two cells referencing two names with explicit ids (unsorted)
    '''
    buf.write(HEADER)

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'ABC')
    write_uint(buf, 1)           # id 1

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'XYZ')
    write_uint(buf, 0)           # id 0

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 0)           # Cell name 0 (XYZ)

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 1)           # Cell name 1 (ABC)

    buf.write(FOOTER)
    return buf


def test_file_4() -> None:
    buf = write_file_4(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert len(layout.cellnames) == 2
    assert len(layout.cells) == 2
    assert layout.cellnames[0].nstring.string == 'XYZ'
    assert layout.cellnames[1].nstring.string == 'ABC'
    assert layout.cells[0].name == 0
    assert layout.cells[1].name == 1


def write_file_5(buf: IO[bytes]) -> IO[bytes]:
    '''
    Reference to non-existent cell name.
    '''
    buf.write(HEADER)

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'ABC')
    write_uint(buf, 1)           # id 1

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'XYZ')
    write_uint(buf, 0)           # id 0

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 0)           # Cell name 0 (XYZ)

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 2)           # Cell name 2 -- Reference to non-existent CELLNAME!!!

    buf.write(FOOTER)
    return buf


def test_file_5() -> None:
    buf = write_file_5(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert len(layout.cellnames) == 2
    assert len(layout.cells) == 2
    assert layout.cellnames[0].nstring.string == 'XYZ'
    assert layout.cellnames[1].nstring.string == 'ABC'
    assert layout.cells[0].name == 0
    assert layout.cells[1].name == 2

    #TODO add optional error checking for this case


def write_file_6(buf: IO[bytes]) -> IO[bytes]:
    '''
    Cellname with invalid n-string.
    '''
    buf.write(HEADER)

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'ABC')
    write_uint(buf, 1)           # id 1

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b' XYZ')
    write_uint(buf, 0)           # id 0

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 0)           # Cell name 0 (XYZ)

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 1)           # Cell name 1

    buf.write(FOOTER)
    return buf


def test_file_6() -> None:
    buf = write_file_6(BytesIO())

    buf.seek(0)

    with pytest.raises(InvalidDataError):
        _layout = OasisLayout.read(buf)

    #base_tests(layout)
    #assert len(layout.cellnames) == 2
    #assert len(layout.cells) == 2
    #assert layout.cellnames[0].nstring.string == ' XYZ'
    #assert layout.cellnames[1].nstring.string == 'ABC'
    #assert layout.cells[0].name == 0
    #assert layout.cells[1].name == 1


def write_file_7(buf: IO[bytes]) -> IO[bytes]:
    '''
    Unused cellname.
    '''
    buf.write(HEADER)

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'ABC')
    write_uint(buf, 1)           # id 1

    write_uint(buf, 4)           # CELLNAME record (explicit id)
    write_bstring(buf, b'XYZ')
    write_uint(buf, 0)           # id 0

    write_uint(buf, 13)          # CELL record (name ref.)
    write_uint(buf, 0)           # Cell name 0 (XYZ)

    buf.write(FOOTER)
    return buf


def test_file_7() -> None:
    buf = write_file_7(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)
    assert len(layout.cellnames) == 2
    assert len(layout.cells) == 1
    assert layout.cellnames[0].nstring.string == 'XYZ'
    assert layout.cellnames[1].nstring.string == 'ABC'
    assert layout.cells[0].name == 0
