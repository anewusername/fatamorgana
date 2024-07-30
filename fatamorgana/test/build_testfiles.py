"""
Build files equivalent to the test cases used by KLayout.
"""

from typing import IO
from collections.abc import Callable
from pathlib import Path


from . import (
    test_files_properties, test_files_cblocks, test_files_layernames,
    test_files_circles, test_files_ctrapezoids, test_files_trapezoids,
    test_files_placements, test_files_paths, test_files_modals,
    test_files_polygons, test_files_rectangles, test_files_empty,
    test_files_texts, test_files_cells,
    )


def build_file(num: str, func: Callable[[IO[bytes]], IO[bytes]]) -> None:
    with Path('t' + num + '.oas').open('wb') as ff:
        func(ff)


def write_all_files() -> None:
    build_file('1.1', test_files_empty.write_file_1)
    build_file('1.2', test_files_empty.write_file_2)
    build_file('1.3', test_files_empty.write_file_3)
    build_file('1.4', test_files_empty.write_file_4)
    build_file('1.5', test_files_empty.write_file_5)

    build_file('2.1', test_files_cells.write_file_1)
    build_file('2.2', test_files_cells.write_file_2)
    build_file('2.3', test_files_cells.write_file_3)
    build_file('2.4', test_files_cells.write_file_4)
    build_file('2.5', test_files_cells.write_file_5)
    build_file('2.6', test_files_cells.write_file_6)
    build_file('2.7', test_files_cells.write_file_7)

    build_file('3.1', lambda f: test_files_texts.write_file_common(f, 1))
    build_file('3.2', lambda f: test_files_texts.write_file_common(f, 2))
    build_file('3.3', test_files_texts.write_file_3)
    build_file('3.4', test_files_texts.write_file_4)
    build_file('3.5', lambda f: test_files_texts.write_file_common(f, 5))
    build_file('3.6', test_files_texts.write_file_6)
    build_file('3.7', test_files_texts.write_file_7)
    build_file('3.8', test_files_texts.write_file_8)
    build_file('3.9', test_files_texts.write_file_9)
    build_file('3.10', test_files_texts.write_file_10)
    build_file('3.11', test_files_texts.write_file_11)

    build_file('4.1', lambda f: test_files_rectangles.write_file_common(f, 1))
    build_file('4.2', lambda f: test_files_rectangles.write_file_common(f, 2))

    build_file('5.1', lambda f: test_files_polygons.write_file_common(f, 1))
    build_file('5.2', test_files_polygons.write_file_2)
    build_file('5.3', lambda f: test_files_polygons.write_file_common(f, 3))

    build_file('6.1', test_files_paths.write_file_1)

    build_file('7.1', test_files_trapezoids.write_file_1)

    build_file('8.1', test_files_placements.write_file_1)
    build_file('8.2', lambda f: test_files_placements.write_file_common(f, 2))
    build_file('8.3', lambda f: test_files_placements.write_file_common(f, 3))
    build_file('8.4', test_files_placements.write_file_4)
    build_file('8.5', lambda f: test_files_placements.write_file_common(f, 5))
    build_file('8.6', test_files_placements.write_file_6)
    build_file('8.7', lambda f: test_files_placements.write_file_common(f, 7))
    build_file('8.8', test_files_placements.write_file_8)

    build_file('9.1', test_files_ctrapezoids.write_file_1)
    build_file('9.2', test_files_ctrapezoids.write_file_2)

    build_file('10.1', test_files_modals.write_file_1)

    build_file('11.1', lambda f: test_files_properties.write_file_common(f, 1))
    build_file('11.2', lambda f: test_files_properties.write_file_common(f, 2))
    build_file('11.3', test_files_properties.write_file_3)
    build_file('11.4', lambda f: test_files_properties.write_file_4_6(f, 4))
    build_file('11.5', lambda f: test_files_properties.write_file_common(f, 5))
    build_file('11.6', lambda f: test_files_properties.write_file_4_6(f, 6))
    build_file('11.7', lambda f: test_files_properties.write_file_7_8_9(f, 7))
    build_file('11.8', lambda f: test_files_properties.write_file_7_8_9(f, 8))
    build_file('11.9', lambda f: test_files_properties.write_file_7_8_9(f, 9))

    build_file('12.1', test_files_circles.write_file_1)

    build_file('13.1', test_files_layernames.write_file_1)
    build_file('13.2', test_files_layernames.write_file_2)
    build_file('13.3', test_files_layernames.write_file_3)
    build_file('13.4', test_files_layernames.write_file_4)

    build_file('14.1', test_files_cblocks.write_file_1)


if __name__ == '__main__':
    write_all_files()
