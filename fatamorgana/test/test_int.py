from typing import List, Tuple, Iterable
from itertools import chain
from io import BytesIO

import pytest       # type: ignore

from ..basic import read_uint, read_sint, write_uint, write_sint


uints = (
    (     0, '00'),
    (   127, '7f'),
    (   128, '80 01'),
    (16_383, 'ff 7f'),
    (16_384, '80 80 01'),
    )

uints_readonly = (
    (     0, '80 80 00'),
    )

sints = (
    (     0, '00'),
    (     1, '02'),
    (    -1, '03'),
    (    63, '7e'),
    (   -64, '81 01'),
    (  8191, 'fe 7f'),
    ( -8192, '81 80 01'),
    )

sints_readonly = (
    )


def test_read_uint() -> None:
    buffer = BytesIO(bytes.fromhex(
        ''.join([hh for _ii, hh in chain(uints, uints_readonly)])))

    for ii, _hh in chain(uints, uints_readonly):
        assert read_uint(buffer) == ii


def test_write_uint() -> None:
    buffer = BytesIO()
    for ii, _hh in uints:
        write_uint(buffer, ii)

    correct_bytes = bytes.fromhex(
        ''.join([hh for _ii, hh in uints]))

    assert buffer.getbuffer() == correct_bytes


def test_read_sint() -> None:
    buffer = BytesIO(bytes.fromhex(
        ''.join([hh for _ii, hh in chain(sints, sints_readonly)])))

    for ii, _hh in chain(sints, sints_readonly):
        assert read_sint(buffer) == ii


def test_write_sint() -> None:
    buffer = BytesIO()
    for ii, _hh in sints:
        write_sint(buffer, ii)

    correct_bytes = bytes.fromhex(
        ''.join([hh for _ii, hh in sints]))

    assert buffer.getbuffer() == correct_bytes
