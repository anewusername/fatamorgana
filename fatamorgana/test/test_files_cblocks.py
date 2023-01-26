# type: ignore

from io import BytesIO, BufferedIOBase

from numpy.testing import assert_equal

from .utils import HEADER, FOOTER
from ..basic import write_uint, write_bstring, write_byte
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
    assert layout.cells[0].name.string == 'ABCDH'
    assert not layout.cells[0].properties


def write_file_1(buf: BufferedIOBase) -> BufferedIOBase:
    '''
    '''
    buf.write(HEADER)

    write_uint(buf, 14)          # CELL record (explicit)
    write_bstring(buf, b'ABCDH')   # Cell name

    cblock_data = bytes.fromhex('''
        22 00 b0 02 b2 02 13
        a9 66 60 98 c3 32 89 e5 0e e3 1b 61 91 4a c6 15
        ac 8f 58 3a f8 be f0 8a 5a b0 30 57 5f 64 6d e4
        4f bd c8 7a 87 ed 81 f8 02 79 a0 88 68 f5 42 b6
        4e be 80 99 4c 3b 99 35 97 30 4f 14 d7 3c 14 f4
        52 50 e4 24 e3 0b f6 9b c2 1a 9a 27 18 57 4b 8a
        04 ae 65 3f 12 04 24 36 0b 8b 2c f2 e9 14 16 3d
        c6 73 92 4d 64 21 e3 0b 9e cf 9a 15 4f 59 6f 08
        83 cc 5d c8 f8 91 7b 25 7f ea 4e e6 03 3c 5b a4
        66 88 01 85 d8 37 b2 fc 64 bd c8 25 5a 79 92 b1
        99 4b a3 93 65 26 7b 33 bf e6 69 b6 39 7c a9 4b
        40 2e e1 3b 28 a6 79 82 69 41 98 f6 14 ae 60 9b
        d7 4c a2 9a 3d 8c 37 f9 6c 03 3f 32 b6 68 2c 64
        5c cb f3 9a 49 f3 33 e3 0c a6 dd da 29 2f 98 76
        80 d4 73 df 64 f9 cb b3 58 33 60 36 d3 13 d6 9b
        9c b6 9a 3b 98 5f b2 07 2e 64 dc c9 7c 91 4b 24
        f8 08 cb 6e 45 8d 47 32 1d 12 77 b8 81 4a 59 17
        68 6a 1f 60 df 28 ac a9 3d 85 b5 5b b6 62 0a ff
        0c 69 90 7b 36 b3 6c 65 d3 9c c9 f4 40 b1 93 a5
        47 e0 32 7f 8a e6 54 d6 93 6c a2 0f 14 17 c8 03
        00''')
    for byte in cblock_data:
        write_byte(buf, byte)

    buf.write(FOOTER)
    return buf


def test_file_1() -> None:
    buf = write_file_1(BytesIO())

    buf.seek(0)
    layout = OasisLayout.read(buf)

    base_tests(layout)

    geometry = layout.cells[0].geometry
    assert len(geometry) == 10

    for ii, gg in enumerate(geometry):
        msg = f'Failed on geometry {ii}'
        assert gg.x == [110, 900, 1520, -370, 1690, -50, 180, 1540, 970, 2160][ii], msg
        assert gg.y == [1270, 890, 2000, 1260, 1420, 850, 860, 750, 1740, 2000][ii], msg
        if ii == 0:
            assert gg.layer == 0, msg
        else:
            assert gg.layer == 1, msg
        assert gg.datatype == 0, msg

        assert not gg.properties, msg
        assert gg.repetition is None, msg

    assert geometry[0].height == 530
    assert geometry[0].width == 540
    assert geometry[1].height == 610
    assert geometry[1].width == 680

    assert_equal(geometry[2].point_list, [
        [-30, -360],
        [480, -50],
        [180, 430],
        [-630, -20],
        ])

    assert_equal(geometry[3].point_list, [
        [-30, -400],
        [450, 40],
        [70, -220],
        [10, 210],
        [740, -20],
        [0, 660],
        [570, 10],
        [50, 500],
        [630, 20],
        [10, 100],
        [-810, 10],
        [20, -470],
        [-660, 0],
        [20, -470],
        [-620, 10],
        [0, 610],
        [610, -10],
        [0, -100],
        [210, 10],
        [40, 820],
        [-1340, 60],
        [30, -1370],
        ])

    assert_equal(geometry[4].point_list, [
        [40, -760],
        [490, -50],
        [110, 800],
        [-640, 10],
        ])

    assert_equal(geometry[5].point_list, [
        [140, -380],
        [340, -10],
        [30, -100],
        [-320, 20],
        [130, -460],
        [-480, -20],
        [-210, 910],
        [370, 40],
        ])

    assert_equal(geometry[6].point_list, [
        [720, -20],
        [20, 20],
        [690, 0],
        [-10, 650],
        [-20, 30],
        [-90, -10],
        [10, 70],
        [470, -30],
        [20, -120],
        [-320, 0],
        [40, -790],
        [-90, -20],
        [-60, 140],
        [-1390, 50],
        [10, 30],
        ])

    assert_equal(geometry[7].point_list, [
        [150, -830],
        [-1320, 40],
        [-70, 370],
        [310, -30],
        [10, 220],
        [250, -40],
        [40, -220],
        [340, 10],
        [-20, 290],
        [-1070, 20],
        [0, 230],
        [1380, -60],
        ])

    assert_equal(geometry[8].point_list, [
        [330, 0],
        [-10, 480],
        [620, -20],
        [-10, 330],
        [-930, 60],
        [0, -850],
        ])

    assert_equal(geometry[9].point_list, [
        [-140, -410],
        [10, -140],
        [270, 0],
        [130, 1030],
        [-500, 50],
        [10, -330],
        [210, -10],
        [10, -190],
        ])
