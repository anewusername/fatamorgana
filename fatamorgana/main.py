"""
This module contains data structures and functions for reading from and
 writing to whole OASIS layout files, and provides a few additional
 abstractions for the data contained inside them.
"""
import io
import logging

from . import records
from .records import Modals
from .basic import OffsetEntry, OffsetTable, NString, AString, real_t, Validation, \
        read_magic_bytes, write_magic_bytes, read_uint, EOFError, \
        InvalidDataError, InvalidRecordError


__author__ = 'Jan Petykiewicz'


logger = logging.getLogger(__name__)


class FileModals:
    """
    File-scoped modal variables
    """
    cellname_implicit = None        # type: bool or None
    propname_implicit = None        # type: bool or None
    xname_implicit = None           # type: bool or None
    textstring_implicit = None      # type: bool or None
    propstring_implicit = None      # type: bool or None
    cellname_implicit = None        # type: bool or None

    within_cell = False             # type: bool
    within_cblock = False           # type: bool
    end_has_offset_table = None     # type: bool
    started = False                 # type: bool


class OasisLayout:
    """
    Representation of a full OASIS layout file.

    Names and strings are stored in dicts, indexed by reference number.
    Layer names and properties are stored directly using their associated
        record objects.
    Cells are stored using Cell objects (different from Cell record objects).

    Properties:
        File properties:
            .version            AString: Version string ('1.0')
            .unit               real number: grid steps per micron
            .validation         Validation: checksum data

        Names:
            .cellnames          Dict[int, NString]
            .propnames          Dict[int, NString]
            .xnames             Dict[int, XName]

        Strings:
            .textstrings        Dict[int, AString]
            .propstrings        Dict[int, AString]

        Data:
            .layers             List[records.LayerName]
            .properties         List[records.Property]
            .cells              List[Cell]
    """
    version = None                  # type: AString
    unit = None                     # type: real_t
    validation = None               # type: Validation

    properties = None               # type: List[records.Property]
    cells = None                    # type: List[Cell]

    cellnames = None                # type: Dict[int, NString]
    propnames = None                # type: Dict[int, NString]
    xnames = None                   # type: Dict[int, XName]

    textstrings = None              # type: Dict[int, AString]
    propstrings = None              # type: Dict[int, AString]
    layers = None                   # type: List[records.LayerName]


    def __init__(self, unit: real_t, validation: Validation = None):
        """
        :param unit: Real number (i.e. int, float, or Fraction), grid steps per micron.
        :param validation: Validation object containing checksum data.
                    Default creates a Validation object of the "no checksum" type.
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
    def read(stream: io.BufferedIOBase) -> 'OasisLayout':
        """
        Read an entire .oas file into an OasisLayout object.

        :param stream: Stream to read from.
        :return: New OasisLayout object.
        """
        file_state = FileModals()
        modals = Modals()
        layout = OasisLayout(unit=None)

        read_magic_bytes(stream)

        while not layout.read_record(stream, modals, file_state):
            pass
        return layout

    def read_record(self,
                    stream: io.BufferedIOBase,
                    modals: Modals,
                    file_state: FileModals
                    ) -> bool:
        """
        Read a single record of unspecified type from a stream, adding its
         contents into this OasisLayout object.

        :param stream: Stream to read from.
        :param modals: Modal variable data, used to fill unfilled record
            fields and updated using filled record fields.
        :param file_state: File status data.
        :return: True if EOF was reached without error, False otherwise.
        :raises: InvalidRecordError from unexpected records;
            InvalidDataError from within record parsers.
        """
        try:
            record_id = read_uint(stream)
        except EOFError as e:
            if file_state.within_cblock:
                return True
            else:
                raise e

        logger.info('read_record of type {} at position 0x{:x}'.format(record_id, stream.tell()))

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
            raise InvalidRecordError('Non-Start record {} before Start'.format(record_id))
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
        elif record_id in range(15, 29) or record_id in (32, 33):
            if not file_state.within_cell:
                raise Exception('Geometry outside Cell')
        elif record_id in (13, 14):
            file_state.within_cell = True
        else:
            raise InvalidRecordError('Unknown record id: {}'.format(record_id))

        if record_id == 0:
            # Pad
            pass
        elif record_id == 1:
            record = records.Start.read(stream, record_id)
            record.merge_with_modals(modals)
            self.unit = record.unit
            self.version = record.version
            file_state.end_has_offset_table = record.offset_table is None
            # TODO Offset table strict check
        elif record_id == 2:
            record = records.End.read(stream, record_id, file_state.end_has_offset_table)
            record.merge_with_modals(modals)
            self.validation = record.validation
            if not len(stream.read(1)) == 0:
                raise InvalidRecordError('Stream continues past End record')
            return True
        elif record_id in (3, 4):
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
            self.cellnames[key] = record.nstring
        elif record_id in (5, 6):
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
            record = records.LayerName.read(stream, record_id)
            record.merge_with_modals(modals)
            self.layers.append(record)
        elif record_id in (28, 29):
            record = records.Property.read(stream, record_id)
            record.merge_with_modals(modals)
            if not file_state.within_cell:
                self.properties.append(record)
            else:
                self.cells[-1].properties.append(record)
        elif record_id in (30, 31):
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

        #
        # Cell and elements
        #
        elif record_id in (13, 14):
            record = records.Cell.read(stream, record_id)
            record.merge_with_modals(modals)
            self.cells.append(Cell(record.name))
        elif record_id in (15, 16):
            record = records.XYMode.read(stream, record_id)
            record.merge_with_modals(modals)
        elif record_id in (17, 18):
            record = records.Placement.read(stream, record_id)
            record.merge_with_modals(modals)
            self.cells[-1].placements.append(record)
        elif record_id in _GEOMETRY:
            record = _GEOMETRY[record_id].read(stream, record_id)
            record.merge_with_modals(modals)
            self.cells[-1].geometry.append(record)
        else:
            raise InvalidRecordError('Unknown record id: {}'.format(record_id))
        return False

    def write(self, stream: io.BufferedIOBase) -> int:
        """
        Write this object in OASIS fromat to a stream.

        :param stream: Stream to write to.
        :return: Number of bytes written.
        :raises: InvalidDataError if contained records are invalid.
        """
        modals = Modals()

        size = 0
        size += write_magic_bytes(stream)
        size += records.Start(self.unit, self.version).dedup_write(stream, modals)

        cellnames_offset = OffsetEntry(False, size)
        size += sum(records.CellName(name, refnum).dedup_write(stream, modals)
                    for refnum, name in self.cellnames.items())

        propnames_offset = OffsetEntry(False, size)
        size += sum(records.PropName(name, refnum).dedup_write(stream, modals)
                    for refnum, name in self.propnames.items())

        xnames_offset = OffsetEntry(False, size)
        size += sum(records.XName(x.attribute, x.string, refnum).dedup_write(stream, modals)
                    for refnum, x in self.xnames.items())

        textstrings_offset = OffsetEntry(False, size)
        size += sum(records.TextString(s, refnum).dedup_write(stream, modals)
                    for refnum, s in self.textstrings.items())

        propstrings_offset = OffsetEntry(False, size)
        size += sum(records.PropString(s, refnum).dedup_write(stream, modals)
                    for refnum, s in self.propstrings.items())

        layernames_offset = OffsetEntry(False, size)
        size += sum(r.dedup_write(stream, modals) for r in self.layers)

        size += sum(p.dedup_write(stream, modals) for p in self.properties)

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

    Properties:
        .name           NString or int (CellName reference number)

        .properties     List of records.Property
        .placements     List of records.Placement
        .geometry       List of geometry record objectes
    """
    name = None                 # type: NString or int
    properties = None           # type: List[records.Property]
    placements = None           # type: List[records.Placement]
    geometry = None             # type: List[records.geometry_t]

    def __init__(self, name: NString or int):
        """
        :param name: NString or int (CellName reference number)
        """
        self.name = name
        self.properties = []
        self.placements = []
        self.geometry = []

    def dedup_write(self, stream: io.BufferedIOBase, modals: Modals) -> int:
        """
        Write this cell to a stream, using the provided modal variables to
         deduplicate any repeated data.

        :param stream: Stream to write to.
        :param modals: Modal variables to use for deduplication.
        :return: Number of bytes written.
        :raises: InvalidDataError if contained records are invalid.
        """
        size = records.Cell(self.name).dedup_write(stream, modals)
        size += sum(p.dedup_write(stream, modals) for p in self.properties)
        size += sum(p.dedup_write(stream, modals) for p in self.placements)
        size += sum(g.dedup_write(stream, modals) for g in self.geometry)
        return size


class XName:
    """
    Representation of an XName.

    This class is effectively a simplified form of a records.XName,
     with the reference data stripped out.
    """
    attribute = None        # type: int
    bstring = None          # type: bytes

    def __init__(self, attribute: int, bstring: bytes):
        """
        :param attribute: Attribute number.
        :param bstring: Binary data.
        """
        self.attribute = attribute
        self.bstring = bstring

    @staticmethod
    def from_record(record: records.XName) -> 'XName':
        """
        Create an XName object from a records.XName record.

        :param record: XName record to use.
        :return: XName object.
        """
        return XName(record.attribute, record.bstring)


# Mapping from record id to record class.
_GEOMETRY = {
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
