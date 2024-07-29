"""
This module contains data structures and functions for reading from and
 writing to whole OASIS layout files, and provides a few additional
 abstractions for the data contained inside them.
"""
from typing import IO
import io
import logging

from . import records
from .records import Modals, Record
from .basic import (
    OffsetEntry, OffsetTable, NString, AString, real_t, Validation,
    read_magic_bytes, write_magic_bytes, read_uint, EOFError,
    InvalidRecordError,
    )


__author__ = 'Jan Petykiewicz'

#logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class FileModals:
    """
    File-scoped modal variables
    """
    cellname_implicit: bool | None = None
    propname_implicit: bool | None = None
    xname_implicit: bool | None = None
    textstring_implicit: bool | None = None
    propstring_implicit: bool | None = None

    property_target: list[records.Property]

    within_cell: bool = False
    within_cblock: bool = False
    end_has_offset_table: bool = False
    started: bool = False

    def __init__(self, property_target: list[records.Property]) -> None:
        self.property_target = property_target


class OasisLayout:
    """
    Representation of a full OASIS layout file.

    Names and strings are stored in dicts, indexed by reference number.
    Layer names and properties are stored directly using their associated
        record objects.
    Cells are stored using `Cell` objects (different from `records.Cell`
        record objects).
    """
    # File properties
    version: AString
    """File format version string ('1.0')"""

    unit: real_t
    """grid steps per micron"""

    validation: Validation
    """checksum data"""

    # Data
    properties: list[records.Property]
    """Property values"""

    cells: list['Cell']
    """Layout cells"""

    layers: list[records.LayerName]
    """Layer definitions"""

    # Names
    cellnames: dict[int, 'CellName']
    """Cell names"""

    propnames: dict[int, NString]
    """Property names"""

    xnames: dict[int, 'XName']
    """Custom names"""

    # String storage
    textstrings: dict[int, AString]
    """Text strings"""

    propstrings: dict[int, AString]
    """Property strings"""

    def __init__(
            self,
            unit: real_t,
            validation: Validation | None = None,
            ) -> None:
        """
        Args:
            unit: Real number (i.e. int, float, or `Fraction`), grid steps per micron.
            validation: `Validation` object containing checksum data.
                 Default creates a `Validation` object of the "no checksum" type.
        """
        if validation is None:
            validation = Validation(0)

        self.unit = unit
        self.validation = validation
        self.version = AString("1.0")
        self.properties = []
        self.cells = []
        self.cellnames = {}
        self.propnames = {}
        self.xnames = {}
        self.textstrings = {}
        self.propstrings = {}
        self.layers = []

    @staticmethod
    def read(stream: IO[bytes]) -> 'OasisLayout':
        """
        Read an entire .oas file into an `OasisLayout` object.

        Args:
            stream: Stream to read from.

        Returns:
            New `OasisLayout` object.
        """
        layout = OasisLayout(unit=-1)    # dummy unit
        modals = Modals()
        file_state = FileModals(layout.properties)

        read_magic_bytes(stream)

        while not layout.read_record(stream, modals, file_state):
            pass
        return layout

    def read_record(
            self,
            stream: IO[bytes],
            modals: Modals,
            file_state: FileModals
            ) -> bool:
        """
        Read a single record of unspecified type from a stream, adding its
         contents into this `OasisLayout` object.

        Args:
            stream: Stream to read from.
            modals: Modal variable data, used to fill unfilled record
                fields and updated using filled record fields.
            file_state: File status data.

        Returns:
            `True` if EOF was reached without error, `False` otherwise.

        Raises:
            InvalidRecordError: from unexpected records
            InvalidDataError: from within record parsers
        """
        try:
            record_id = read_uint(stream)
        except EOFError as e:
            if file_state.within_cblock:
                return True
            else:
                raise e

        logger.info(f'read_record of type {record_id} at position 0x{stream.tell():x}')

        record: Record

        # CBlock
        if record_id == 34:
            if file_state.within_cblock:
                raise InvalidRecordError('Nested CBlock')
            record = records.CBlock.read(stream, record_id)
            decoded_data = record.decompress()

            file_state.within_cblock = True
            decoded_stream = io.BytesIO(decoded_data)
            while not self.read_record(decoded_stream, modals, file_state):
                pass
            file_state.within_cblock = False
            return False

        # Make sure order is valid (eg, no out-of-cell geometry)
        if not file_state.started and record_id != 1:
            raise InvalidRecordError(f'Non-Start record {record_id} before Start')
        if record_id == 1:
            if file_state.started:
                raise InvalidRecordError('Duplicate Start record')
            else:
                file_state.started = True
        if record_id == 2 and file_state.within_cblock:
            raise InvalidRecordError('End within CBlock')

        if record_id in (0, 1, 2, 28, 29):
            pass
        elif record_id in range(3, 13) or record_id in (28, 29):
            file_state.within_cell = False
        elif record_id in range(15, 28) or record_id in (32, 33):
            if not file_state.within_cell:
                raise Exception('Geometry outside Cell')
        elif record_id in (13, 14):
            file_state.within_cell = True
        else:
            raise InvalidRecordError(f'Unknown record id: {record_id}')

        if record_id == 0:
            ''' Pad '''
            pass
        elif record_id == 1:
            ''' Start '''
            record = records.Start.read(stream, record_id)
            record.merge_with_modals(modals)
            self.unit = record.unit
            self.version = record.version
            file_state.end_has_offset_table = record.offset_table is None
            file_state.property_target = self.properties
            # TODO Offset table strict check
        elif record_id == 2:
            ''' End '''
            record = records.End.read(stream, record_id, file_state.end_has_offset_table)
            record.merge_with_modals(modals)
            self.validation = record.validation
            if not len(stream.read(1)) == 0:
                raise InvalidRecordError('Stream continues past End record')
            return True
        elif record_id in (3, 4):
            ''' CellName '''
            implicit = record_id == 3
            if file_state.cellname_implicit is None:
                file_state.cellname_implicit = implicit
            elif file_state.cellname_implicit != implicit:
                raise InvalidRecordError('Mix of implicit and non-implicit cellnames')

            record = records.CellName.read(stream, record_id)
            record.merge_with_modals(modals)
            key = record.reference_number
            if key is None:
                key = len(self.cellnames)

            cellname = CellName.from_record(record)
            self.cellnames[key] = cellname
            file_state.property_target = cellname.properties
        elif record_id in (5, 6):
            ''' TextString '''
            implicit = record_id == 5
            if file_state.textstring_implicit is None:
                file_state.textstring_implicit = implicit
            elif file_state.textstring_implicit != implicit:
                raise InvalidRecordError('Mix of implicit and non-implicit textstrings')

            record = records.TextString.read(stream, record_id)
            record.merge_with_modals(modals)
            key = record.reference_number
            if key is None:
                key = len(self.textstrings)
            self.textstrings[key] = record.astring
        elif record_id in (7, 8):
            ''' PropName '''
            implicit = record_id == 7
            if file_state.propname_implicit is None:
                file_state.propname_implicit = implicit
            elif file_state.propname_implicit != implicit:
                raise InvalidRecordError('Mix of implicit and non-implicit propnames')

            record = records.PropName.read(stream, record_id)
            record.merge_with_modals(modals)
            key = record.reference_number
            if key is None:
                key = len(self.propnames)
            self.propnames[key] = record.nstring
        elif record_id in (9, 10):
            ''' PropString '''
            implicit = record_id == 9
            if file_state.propstring_implicit is None:
                file_state.propstring_implicit = implicit
            elif file_state.propstring_implicit != implicit:
                raise InvalidRecordError('Mix of implicit and non-implicit propstrings')

            record = records.PropString.read(stream, record_id)
            record.merge_with_modals(modals)
            key = record.reference_number
            if key is None:
                key = len(self.propstrings)
            self.propstrings[key] = record.astring
        elif record_id in (11, 12):
            ''' LayerName '''
            record = records.LayerName.read(stream, record_id)
            record.merge_with_modals(modals)
            self.layers.append(record)
        elif record_id in (28, 29):
            ''' Property '''
            record = records.Property.read(stream, record_id)
            record.merge_with_modals(modals)
            file_state.property_target.append(record)
        elif record_id in (30, 31):
            ''' XName '''
            implicit = record_id == 30
            if file_state.xname_implicit is None:
                file_state.xname_implicit = implicit
            elif file_state.xname_implicit != implicit:
                raise InvalidRecordError('Mix of implicit and non-implicit xnames')

            record = records.XName.read(stream, record_id)
            record.merge_with_modals(modals)
            key = record.reference_number
            if key is None:
                key = len(self.xnames)
            self.xnames[key] = XName.from_record(record)
            # TODO: do anything with property target?

        #
        # Cell and elements
        #
        elif record_id in (13, 14):
            ''' Cell '''
            record = records.Cell.read(stream, record_id)
            record.merge_with_modals(modals)
            cell = Cell(record.name)
            self.cells.append(cell)
            file_state.property_target = cell.properties
        elif record_id in (15, 16):
            ''' XYMode '''
            record = records.XYMode.read(stream, record_id)
            record.merge_with_modals(modals)
        elif record_id in (17, 18):
            ''' Placement '''
            record = records.Placement.read(stream, record_id)
            record.merge_with_modals(modals)
            self.cells[-1].placements.append(record)
            file_state.property_target = record.properties
        elif record_id in _GEOMETRY:
            ''' Geometry '''
            record = _GEOMETRY[record_id].read(stream, record_id)
            record.merge_with_modals(modals)
            self.cells[-1].geometry.append(record)
            file_state.property_target = record.properties
        else:
            raise InvalidRecordError(f'Unknown record id: {record_id}')
        return False

    def write(self, stream: IO[bytes]) -> int:
        """
        Write this object in OASIS fromat to a stream.

        Args:
            stream: Stream to write to.

        Returns:
            Number of bytes written.

        Raises:
            InvalidDataError: if contained records are invalid.
        """
        modals = Modals()

        size = 0
        size += write_magic_bytes(stream)
        size += records.Start(self.unit, self.version).dedup_write(stream, modals)
        size += sum(p.dedup_write(stream, modals) for p in self.properties)

        cellnames_offset = OffsetEntry(False, size)
        for refnum, cn in self.cellnames.items():
            size += records.CellName(cn.nstring, refnum).dedup_write(stream, modals)
            size += sum(p.dedup_write(stream, modals) for p in cn.properties)

        propnames_offset = OffsetEntry(False, size)
        size += sum(records.PropName(name, refnum).dedup_write(stream, modals)
                    for refnum, name in self.propnames.items())

        xnames_offset = OffsetEntry(False, size)
        size += sum(records.XName(x.attribute, x.bstring, refnum).dedup_write(stream, modals)
                    for refnum, x in self.xnames.items())

        textstrings_offset = OffsetEntry(False, size)
        size += sum(records.TextString(s, refnum).dedup_write(stream, modals)
                    for refnum, s in self.textstrings.items())

        propstrings_offset = OffsetEntry(False, size)
        size += sum(records.PropString(s, refnum).dedup_write(stream, modals)
                    for refnum, s in self.propstrings.items())

        layernames_offset = OffsetEntry(False, size)
        size += sum(r.dedup_write(stream, modals) for r in self.layers)

        size += sum(c.dedup_write(stream, modals) for c in self.cells)

        offset_table = OffsetTable(
            cellnames_offset,
            textstrings_offset,
            propnames_offset,
            propstrings_offset,
            layernames_offset,
            xnames_offset,
            )
        size += records.End(self.validation, offset_table).dedup_write(stream, modals)
        return size


class Cell:
    """
    Representation of an OASIS cell.
    """
    name: NString | int
    """name or "CellName reference" number"""

    properties: list[records.Property]
    placements: list[records.Placement]
    geometry: list[records.geometry_t]

    def __init__(
            self,
            name: NString | str | int,
            *,
            properties: list[records.Property] | None = None,
            placements: list[records.Placement] | None = None,
            geometry: list[records.geometry_t] | None = None,
            ) -> None:
        self.name = name if isinstance(name, (NString, int)) else NString(name)
        self.properties = [] if properties is None else properties
        self.placements = [] if placements is None else placements
        self.geometry = [] if geometry is None else geometry

    def dedup_write(self, stream: IO[bytes], modals: Modals) -> int:
        """
        Write this cell to a stream, using the provided modal variables to
         deduplicate any repeated data.

        Args:
            stream: Stream to write to.
            modals: Modal variables to use for deduplication.

        Returns:
            Number of bytes written.

        Raises:
            InvalidDataError: if contained records are invalid.
        """
        size = records.Cell(self.name).dedup_write(stream, modals)
        size += sum(p.dedup_write(stream, modals) for p in self.properties)
        for placement in self.placements:
            size += placement.dedup_write(stream, modals)
            size += sum(p.dedup_write(stream, modals) for p in placement.properties)
        for shape in self.geometry:
            size += shape.dedup_write(stream, modals)
            size += sum(p.dedup_write(stream, modals) for p in shape.properties)
        return size


class CellName:
    """
    Representation of a CellName.

    This class is effectively a simplified form of a `records.CellName`,
     with the reference data stripped out.
    """
    nstring: NString
    properties: list[records.Property]

    def __init__(
            self,
            nstring: NString | str,
            properties: list[records.Property] | None = None,
            ) -> None:
        """
        Args:
            nstring: The contained string.
            properties: Properties which apply to this CellName's cell, but
                    are placed following the CellName record.
        """
        if isinstance(nstring, NString):
            self.nstring = nstring
        else:
            self.nstring = NString(nstring)
        self.properties = [] if properties is None else properties

    @staticmethod
    def from_record(record: records.CellName) -> 'CellName':
        """
        Create an `CellName` object from a `records.CellName` record.

        Args:
            record: CellName record to use.

        Returns:
            A new `CellName` object.
        """
        return CellName(record.nstring)


class XName:
    """
    Representation of an XName.

    This class is effectively a simplified form of a `records.XName`,
     with the reference data stripped out.
    """
    attribute: int
    bstring: bytes

    def __init__(self, attribute: int, bstring: bytes) -> None:
        """
        Args:
            attribute: Attribute number.
            bstring: Binary data.
        """
        self.attribute = attribute
        self.bstring = bstring

    @staticmethod
    def from_record(record: records.XName) -> 'XName':
        """
        Create an `XName` object from a `records.XName` record.

        Args:
            record: XName record to use.

        Returns:
            a new `XName` object.
        """
        return XName(record.attribute, record.bstring)


# Mapping from record id to record class.
_GEOMETRY: dict[int, type[records.geometry_t]] = {
    19: records.Text,
    20: records.Rectangle,
    21: records.Polygon,
    22: records.Path,
    23: records.Trapezoid,
    24: records.Trapezoid,
    25: records.Trapezoid,
    26: records.CTrapezoid,
    27: records.Circle,
    32: records.XElement,
    33: records.XGeometry,
    }
