"""
This module contains all 'record' or 'block'-level datastructures and their
 associated writing and parsing code, as well as a few helper functions.

Additionally, this module contains definitions for the record-level modal
 variables (stored in the Modals class).

Higher-level code (e.g. monitoring for combinations of records with
 implicit and explicit references, code for deciding which record type to
 parse, or code for dealing with nested records in a CBlock) should live
 in main.py instead.
"""
from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Union, Optional, Sequence, Any, TypeVar
import copy
import math
import zlib
import io
import logging
import pprint
from warnings import warn
from .basic import AString, NString, repetition_t, property_value_t, real_t, \
        ReuseRepetition, OffsetTable, Validation, read_point_list, read_property_value, \
        read_bstring, read_uint, read_sint, read_real, read_repetition, read_interval, \
        write_bstring, write_uint, write_sint, write_real, write_interval, write_point_list, \
        write_property_value, read_bool_byte, write_bool_byte, read_byte, write_byte, \
        InvalidDataError, UnfilledModalError, PathExtensionScheme, _USE_NUMPY

if _USE_NUMPY:
    import numpy


logger = logging.getLogger(__name__)


'''
    Type definitions
'''
geometry_t = Union['Text', 'Rectangle', 'Polygon', 'Path', 'Trapezoid',
                  'CTrapezoid', 'Circle', 'XElement', 'XGeometry']
pathextension_t = Tuple['PathExtensionScheme', Optional[int]]
point_list_t = Sequence[Sequence[int]]


class Modals:
    """
    Modal variables, used to store data about previously-written or
     -read records.
    """
    repetition: Optional[repetition_t] = None
    placement_x: int = 0
    placement_y: int = 0
    placement_cell: Optional[NString] = None
    layer: Optional[int] = None
    datatype: Optional[int] = None
    text_layer: Optional[int] = None
    text_datatype: Optional[int] = None
    text_x: int = 0
    text_y: int = 0
    text_string: Union[AString, int, None] = None
    geometry_x: int = 0
    geometry_y: int = 0
    xy_relative: bool = False
    geometry_w: Optional[int] = None
    geometry_h: Optional[int] = None
    polygon_point_list: Optional[point_list_t] = None
    path_half_width: Optional[int] = None
    path_point_list: Optional[point_list_t] = None
    path_extension_start: Optional[pathextension_t] = None
    path_extension_end: Optional[pathextension_t] = None
    ctrapezoid_type: Optional[int] = None
    circle_radius: Optional[int] = None
    property_value_list: Optional[Sequence[property_value_t]] = None
    property_name: Union[int, NString, None] = None
    property_is_standard: Optional[bool] = None

    def __init__(self):
        self.reset()

    def reset(self):
        """
        Resets all modal variables to their default values.
        Default values are:
            `0` for placement_{x,y}, text_{x,y}, geometry_{x,y}
            `False` for xy_relative
            Undefined (`None`) for all others
        """
        self.repetition = None
        self.placement_x = 0
        self.placement_y = 0
        self.placement_cell = None
        self.layer = None
        self.datatype = None
        self.text_layer = None
        self.text_datatype = None
        self.text_x = 0
        self.text_y = 0
        self.text_string = None
        self.geometry_x = 0
        self.geometry_y = 0
        self.xy_relative = False
        self.geometry_w = None
        self.geometry_h = None
        self.polygon_point_list = None
        self.path_half_width = None
        self.path_point_list = None
        self.path_extension_start = None
        self.path_extension_end = None
        self.ctrapezoid_type = None
        self.circle_radius = None
        self.property_value_list = None
        self.property_name = None
        self.property_is_standard = None


T = TypeVar('T')
def verify_modal(var: Optional[T]) -> T:
    if var is None:
        raise UnfilledModalError
    return var

'''

    Records

'''

class Record(metaclass=ABCMeta):
    """
    Common interface for records.
    """
    @abstractmethod
    def merge_with_modals(self, modals: Modals):
        """
        Copy all defined values from this record into the modal variables.
        Fill all undefined values in this record from the modal variables.

        Args:
            modals: Modal variables to merge with.
        """
        pass

    @abstractmethod
    def deduplicate_with_modals(self, modals: Modals):
        """
        Check all defined values in this record against those in the
         modal variables. If any values are equal, remove them from
         the record and indicate that the modal variables should be
         used instead. Update the modal variables using the remaining
         (unequal) values.

        Args:
            modals: Modal variables to deduplicate with.
        """
        pass

    @staticmethod
    @abstractmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Record':
        """
        Read a record of this type from a stream.
        This function does not merge with modal variables.

        Args:
            stream: Stream to read from.
            record_id: Record id of the record to read. The
                record id is often used to specify which variant
                of the record is stored.

        Returns:
            The record that was read.

        Raises:
            InvalidDataError: if the record is malformed.
        """
        pass

    @abstractmethod
    def write(self, stream: io.BufferedIOBase) -> int:
        """
        Write this record to a stream as-is.
        This function does not merge or deduplicate with modal variables.

        Args:
            stream: Stream to write to.

        Returns:
            Number of bytes written.

        Raises:
            InvalidDataError: if the record contains invalid data.
        """
        pass

    def dedup_write(self, stream: io.BufferedIOBase, modals: Modals) -> int:
        """
        Run `.deduplicate_with_modals()` and then `.write()` to the stream.

        Args:
            stream: Stream to write to.
            modals: Modal variables to merge with.

        Returns:
            Number of bytes written.

        Raises:
            InvalidDataError: if the record contains invalid data.
        """
        # TODO logging
        #print(type(self), stream.tell())
        self.deduplicate_with_modals(modals)
        return self.write(stream)

    def copy(self) -> 'Record':
        """
        Perform a deep copy of this record.

        Returns:
            A deep copy of this record.
        """
        return copy.deepcopy(self)

    def __repr__(self) -> str:
        return '{}: {}'.format(self.__class__, pprint.pformat(self.__dict__))


class GeometryMixin(metaclass=ABCMeta):
    """
    Mixin defining common functions for geometry records
    """
    x: Optional[int]
    y: Optional[int]
    layer: Optional[int]
    datatype: Optional[int]

    def get_x(self) -> int:
        return verify_modal(self.x)

    def get_y(self) -> int:
        return verify_modal(self.y)

    def get_xy(self) -> Tuple[int, int]:
        return (self.get_x(), self.get_y())

    def get_layer(self) -> int:
        return verify_modal(self.layer)

    def get_datatype(self) -> int:
        return verify_modal(self.datatype)

    def get_layer_tuple(self) -> Tuple[int, int]:
        return (self.get_layer(), self.get_datatype())


def read_refname(stream: io.BufferedIOBase,
                 is_present: Union[bool, int],
                 is_reference: Union[bool, int]
                 ) -> Union[None, int, NString]:
    """
    Helper function for reading a possibly-absent, possibly-referenced NString.

    Args:
        stream: Stream to read from.
        is_present: If `False`, read nothing and return `None`
        is_reference: If `True`, read a uint (reference id),
                          otherwise read an `NString`.

    Returns:
        `None`, reference id, or `NString`
    """
    if not is_present:
        return None
    elif is_reference:
        return read_uint(stream)
    else:
        return NString.read(stream)


def read_refstring(stream: io.BufferedIOBase,
                   is_present: Union[bool, int],
                   is_reference: Union[bool, int],
                   ) -> Union[None, int, AString]:
    """
    Helper function for reading a possibly-absent, possibly-referenced `AString`.

    Args:
        stream: Stream to read from.
        is_present: If `False`, read nothing and return `None`
        is_reference: If `True`, read a uint (reference id),
                          otherwise read an `AString`.

    Returns:
        `None`, reference id, or `AString`
    """
    if not is_present:
        return None
    elif is_reference:
        return read_uint(stream)
    else:
        return AString.read(stream)


class Pad(Record):
    """
    Pad record (ID 0)
    """
    def merge_with_modals(self, modals: Modals):
        pass

    def deduplicate_with_modals(self, modals: Modals):
        pass

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Pad':
        if record_id != 0:
            raise InvalidDataError('Invalid record id for Pad '
                                   '{}'.format(record_id))
        record = Pad()
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        return write_uint(stream, 0)


class XYMode(Record):
    """
    XYMode record (ID 15, 16)

    Attributes:
        relative (bool): default `False`
    """
    relative: bool = False

    @property
    def absolute(self) -> bool:
        return not self.relative

    @absolute.setter
    def absolute(self, b: bool):
        self.relative = not b

    def __init__(self, relative: bool):
        """
        Args:
            relative: `True` if the mode is 'relative', `False` if 'absolute'.
        """
        self.relative = relative

    def merge_with_modals(self, modals: Modals):
        modals.xy_relative = self.relative

    def deduplicate_with_modals(self, modals: Modals):
        pass

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'XYMode':
        if record_id not in (15, 16):
            raise InvalidDataError('Invalid record id for XYMode')
        record = XYMode(record_id == 16)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        return write_uint(stream, 15 + self.relative)


class Start(Record):
    """
    Start Record (ID 1)

    Attributes:
        version (AString): "1.0"
        unit (real_t): positive real number, grid steps per micron
        offset_table (Optional[OffsetTable]): If `None` then table must be
                                            placed in the `End` record)
    """
    version: AString
    unit: real_t
    offset_table: Optional[OffsetTable] = None

    def __init__(self,
                 unit: real_t,
                 version: Union[AString, str] = None,
                 offset_table: Optional[OffsetTable] = None):
        """
        Args
            unit: Grid steps per micron (positive real number)
            version: Version string, default "1.0"
            offset_table: `OffsetTable` for the file, or `None` to place
                    it in the `End` record instead.
        """
        if unit <= 0:
            raise InvalidDataError('Non-positive unit: {}'.format(unit))
        if math.isnan(unit):
            raise InvalidDataError('NaN unit')
        if math.isinf(unit):
            raise InvalidDataError('Non-finite unit')
        self.unit = unit

        if version is None:
            version = AString('1.0')
        if isinstance(version, AString):
            self.version = version
        else:
            self.version = AString(version)

        if self.version.string != '1.0':
            raise InvalidDataError('Invalid version string, '
                                   'only "1.0" is allowed: '
                                   + str(self.version.string))
        self.offset_table = offset_table

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Start':
        if record_id != 1:
            raise InvalidDataError('Invalid record id for Start: '
                                   '{}'.format(record_id))
        version = AString.read(stream)
        unit = read_real(stream)
        has_offset_table = read_uint(stream) == 0
        offset_table: Optional[OffsetTable]
        if has_offset_table:
            offset_table = OffsetTable.read(stream)
        else:
            offset_table = None
        record = Start(unit, version, offset_table)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        size = write_uint(stream, 1)
        size += self.version.write(stream)
        size += write_real(stream, self.unit)
        size += write_uint(stream, self.offset_table is None)
        if self.offset_table is not None:
            size += self.offset_table.write(stream)
        return size


class End(Record):
    """
    End record (ID 2)

    The end record is always padded to a total length of 256 bytes.

    Attributes:
        offset_table (Optional[OffsetTable]): `None` if offset table was
                                  written into the `Start` record instead
        validation (Validation): object containing checksum
    """
    offset_table: Optional[OffsetTable] = None
    validation: Validation

    def __init__(self,
                 validation: Validation,
                 offset_table: Optional[OffsetTable] = None):
        """
        Args:
            validation: `Validation` object for this file.
            offset_table: `OffsetTable`, or `None` if the `Start` record
                    contained an `OffsetTable`. Default `None`.
        """
        self.validation = validation
        self.offset_table = offset_table

    def merge_with_modals(self, modals: Modals):
        pass

    def deduplicate_with_modals(self, modals: Modals):
        pass

    @staticmethod
    def read(stream: io.BufferedIOBase,
             record_id: int,
             has_offset_table: bool
             ) -> 'End':
        if record_id != 2:
            raise InvalidDataError('Invalid record id for End {}'.format(record_id))
        if has_offset_table:
            offset_table: Optional[OffsetTable] = OffsetTable.read(stream)
        else:
            offset_table = None
        _padding_string = read_bstring(stream)
        validation = Validation.read(stream)
        record = End(validation, offset_table)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        size = write_uint(stream, 2)
        if self.offset_table is not None:
            size += self.offset_table.write(stream)

        buf = io.BytesIO()
        self.validation.write(buf)
        validation_bytes = buf.getvalue()

        pad_len = 256 - size - len(validation_bytes)
        if pad_len > 0:
            pad = [0x80] * (pad_len - 1) + [0x00]
            stream.write(bytes(pad))
        stream.write(validation_bytes)
        return 256


class CBlock(Record):
    """
    CBlock (Compressed Block) record (ID 34)

    Attributes:
        compression_type (int): `0` for zlib
        decompressed_byte_count (int): size after decompressing
        compressed_bytes (bytes): compressed data
    """
    compression_type: int
    decompressed_byte_count: int
    compressed_bytes: bytes

    def __init__(self,
                 compression_type: int,
                 decompressed_byte_count: int,
                 compressed_bytes: bytes):
        """
        Args:
            compression_type: `0` (zlib)
            decompressed_byte_count: Number of bytes in the decompressed data.
            compressed_bytes: The compressed data.
        """
        if compression_type != 0:
            raise InvalidDataError('CBlock: Invalid compression scheme '
                                   '{}'.format(compression_type))

        self.compression_type = compression_type
        self.decompressed_byte_count = decompressed_byte_count
        self.compressed_bytes = compressed_bytes

    def merge_with_modals(self, modals: Modals):
        pass

    def deduplicate_with_modals(self, modals: Modals):
        pass

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'CBlock':
        if record_id != 34:
            raise InvalidDataError('Invalid record id for CBlock: '
                                   '{}'.format(record_id))
        compression_type = read_uint(stream)
        decompressed_count = read_uint(stream)
        compressed_bytes = read_bstring(stream)
        record = CBlock(compression_type, decompressed_count, compressed_bytes)
        logger.debug('CBlock ending at 0x{:x} was read successfully'.format(stream.tell()))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        size = write_uint(stream, 34)
        size += write_uint(stream, self.compression_type)
        size += write_uint(stream, self.decompressed_byte_count)
        size += write_bstring(stream, self.compressed_bytes)
        return size

    @staticmethod
    def from_decompressed(decompressed_bytes: bytes,
                          compression_type: int = 0,
                          compression_args: Dict = None
                          ) -> 'CBlock':
        """
        Create a CBlock record from uncompressed data.

        Args:
            decompressed_bytes: Uncompressed data (one or more non-CBlock records)
            compression_type: Compression type (0: zlib). Default `0`
            compression_args: Passed as kwargs to `zlib.compressobj()`. Default `{}`.

        Returns:
            CBlock object constructed from the data.

        Raises:
            InvalidDataError: if invalid `compression_type`.
        """
        if compression_args is None:
            compression_args = {}

        if compression_type == 0:
            count = len(decompressed_bytes)
            compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS, **compression_args)
            compressed_bytes = compressor.compress(decompressed_bytes) + \
                               compressor.flush()
        else:
            raise InvalidDataError('Unknown compression type: '
                                   '{}'.format(compression_type))

        return CBlock(compression_type, count, compressed_bytes)

    def decompress(self, decompression_args: Dict = None) -> bytes:
        """
        Decompress the contents of this CBlock.

        Args:
            decompression_args: Passed as kwargs to `zlib.decompressobj()`.

        Returns:
            Decompressed `bytes` object.

        Raises:
            InvalidDataError: if data is malformed or compression type is
                    unknonwn.
        """
        if decompression_args is None:
            decompression_args = {}
        if self.compression_type == 0:
            decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS, **decompression_args)
            decompressed_bytes = decompressor.decompress(self.compressed_bytes) + \
                                 decompressor.flush()
            if len(decompressed_bytes) != self.decompressed_byte_count:
                raise InvalidDataError('Decompressed data length does not match!')
        else:
            raise InvalidDataError('Unknown compression type: '
                                   '{}'.format(self.compression_type))
        return decompressed_bytes


class CellName(Record):
    """
    CellName record (ID 3, 4)

    Attributes:
        nstring (NString): name
        reference_number (Optional[int]): `None` results in implicit assignment
    """
    nstring: NString
    reference_number: Optional[int] = None

    def __init__(self,
                 nstring: Union[NString, str],
                 reference_number: int = None):
        """
        Args:
            nstring: The contained string.
            reference_number: Reference id number for the string.
                     Default is to use an implicitly-assigned number.
        """
        if isinstance(nstring, NString):
            self.nstring = nstring
        else:
            self.nstring = NString(nstring)
        self.reference_number = reference_number

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'CellName':
        if record_id not in (3, 4):
            raise InvalidDataError('Invalid record id for CellName '
                                   '{}'.format(record_id))
        nstring = NString.read(stream)
        if record_id == 4:
            reference_number: Optional[int] = read_uint(stream)
        else:
            reference_number = None
        record = CellName(nstring, reference_number)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        record_id = 3 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.nstring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size

class PropName(Record):
    """
    PropName record (ID 7, 8)

    Attributes:
        nstring (NString): name
        reference_number (Optional[int]): `None` results in implicit assignment
    """
    nstring: NString
    reference_number: Optional[int] = None

    def __init__(self,
                 nstring: Union[NString, str],
                 reference_number: int = None):
        """
        Args:
            nstring: The contained string.
            reference_number: Reference id number for the string.
                         Default is to use an implicitly-assigned number.
        """
        if isinstance(nstring, NString):
            self.nstring = nstring
        else:
            self.nstring = NString(nstring)
        self.reference_number = reference_number

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'PropName':
        if record_id not in (7, 8):
            raise InvalidDataError('Invalid record id for PropName '
                                   '{}'.format(record_id))
        nstring = NString.read(stream)
        if record_id == 8:
            reference_number: Optional[int] = read_uint(stream)
        else:
            reference_number = None
        record = PropName(nstring, reference_number)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        record_id = 7 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.nstring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size


class TextString(Record):
    """
    TextString record (ID 5, 6)

    Attributes:
        astring (AString): string data
        reference_number (Optional[int]): `None` results in implicit assignment
    """
    astring: AString
    reference_number: Optional[int] = None

    def __init__(self,
                 string: Union[AString, str],
                 reference_number: int = None):
        """
        Args:
            string: The contained string.
            reference_number: Reference id number for the string.
                         Default is to use an implicitly-assigned number.
        """
        if isinstance(string, AString):
            self.astring = string
        else:
            self.astring = AString(string)
        self.reference_number = reference_number

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'TextString':
        if record_id not in (5, 6):
            raise InvalidDataError('Invalid record id for TextString: '
                                   '{}'.format(record_id))
        astring = AString.read(stream)
        if record_id == 6:
            reference_number: Optional[int] = read_uint(stream)
        else:
            reference_number = None
        record = TextString(astring, reference_number)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        record_id = 5 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.astring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size


class PropString(Record):
    """
    PropString record (ID 9, 10)

    Attributes:
        astring (AString): string data
        reference_number (Optional[int]): `None` results in implicit assignment
    """
    astring: AString
    reference_number: Optional[int] = None

    def __init__(self,
                 string: Union[AString, str],
                 reference_number: int = None):
        """
        Args:
            string: The contained string.
            reference_number: Reference id number for the string.
                         Default is to use an implicitly-assigned number.
        """
        if isinstance(string, AString):
            self.astring = string
        else:
            self.astring = AString(string)
        self.reference_number = reference_number

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'PropString':
        if record_id not in (9, 10):
            raise InvalidDataError('Invalid record id for PropString: '
                                   '{}'.format(record_id))
        astring = AString.read(stream)
        if record_id == 10:
            reference_number: Optional[int] = read_uint(stream)
        else:
            reference_number = None
        record = PropString(astring, reference_number)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        record_id = 9 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.astring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size


class LayerName(Record):
    """
    LayerName record (ID 11, 12)

    Attributes:
        nstring (NString): name
        layer_interval (Tuple[Optional[int], Optional[int]]): bounds on the interval
        type_interval (Tuple[Optional[int], Optional[int]]): bounds on the interval
        is_textlayer (bool): Is this a text layer?
    """
    nstring: NString
    layer_interval: Tuple
    type_interval: Tuple
    is_textlayer: bool

    def __init__(self,
                 nstring: Union[NString, str],
                 layer_interval: Tuple,
                 type_interval: Tuple,
                 is_textlayer: bool):
        """
        Args:
            nstring: The layer name.
            layer_interval: Tuple (int or None, int or None) giving bounds
                     (or lack of thereof) on the layer number.
            type_interval: Tuple (int or None, int or None) giving bounds
                     (or lack of thereof) on the type number.
            is_textlayer: `True` if the layer is a text layer.
        """
        if isinstance(nstring, NString):
            self.nstring = nstring
        else:
            self.nstring = NString(nstring)
        self.layer_interval = layer_interval
        self.type_interval = type_interval
        self.is_textlayer = is_textlayer

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'LayerName':
        if record_id not in (11, 12):
            raise InvalidDataError('Invalid record id for LayerName: '
                                   '{}'.format(record_id))
        is_textlayer = (record_id == 12)
        nstring = NString.read(stream)
        layer_interval = read_interval(stream)
        type_interval = read_interval(stream)
        record = LayerName(nstring, layer_interval, type_interval, is_textlayer)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        record_id = 11 + self.is_textlayer
        size = write_uint(stream, record_id)
        size += self.nstring.write(stream)
        size += write_interval(stream, *self.layer_interval)
        size += write_interval(stream, *self.type_interval)
        return size


class Property(Record):
    """
    LayerName record (ID 28, 29)

    Attributes:
        name (Union[NString, int, None]): `int` is an explicit reference,
                                       `None` is a flag to use Modal)
        values (Optional[List[property_value_t]]): List of property values.
        is_standard (bool): Whether this is a standard property.
    """
    name: Optional[Union[NString, int]] = None
    values: Optional[List[property_value_t]] = None
    is_standard: Optional[bool] = None

    def __init__(self,
                 name: Union[NString, str, int, None] = None,
                 values: Optional[List[property_value_t]] = None,
                 is_standard: Optional[bool] = None):
        """
        Args:
            name: Property name, reference number, or `None` (i.e. use modal)
                Default `None.
            values: List of property values, or `None` (i.e. use modal)
                Default `None`.
            is_standard: `True` if this is a standard property. `None` to use modal.
                Default `None`.
        """
        if isinstance(name, (NString, int)) or name is None:
            self.name = name
        else:
            self.name = NString(name)
        self.values = values
        self.is_standard = is_standard

    def get_name(self) -> Union[NString, int]:
        return verify_modal(self.name)  # type: ignore

    def get_values(self) -> List[property_value_t]:
        return verify_modal(self.values)

    def get_is_standard(self) -> bool:
        return verify_modal(self.is_standard)

    def merge_with_modals(self, modals: Modals):
        adjust_field(self, 'name', modals, 'property_name')
        adjust_field(self, 'values', modals, 'property_value_list')
        adjust_field(self, 'is_standard', modals, 'property_is_standard')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_field(self, 'name', modals, 'property_name')
        dedup_field(self, 'values', modals, 'property_value_list')
        if self.values is None and self.name is None:
            dedup_field(self, 'is_standard', modals, 'property_is_standard')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Property':
        if record_id not in (28, 29):
            raise InvalidDataError('Invalid record id for PropertyValue: '
                                   '{}'.format(record_id))
        if record_id == 29:
            record = Property()
        else:
            byte = read_byte(stream)      #UUUUVCNS
            u = 0x0f & (byte >> 4)
            v = 0x01 & (byte >> 3)
            c = 0x01 & (byte >> 2)
            n = 0x01 & (byte >> 1)
            s = 0x01 & (byte >> 0)

            name = read_refname(stream, c, n)
            if v == 0:
                if u < 0x0f:
                    value_count = u
                else:
                    value_count = read_uint(stream)
                values: Optional[List[property_value_t]] = [read_property_value(stream)
                                                            for _ in range(value_count)]
            else:
                values = None
                if u != 0:
                    raise InvalidDataError('Malformed property record header')
            record = Property(name, values, bool(s))
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        if self.is_standard is None and self.values is None and self.name is None:
            return write_uint(stream, 29)
        else:
            if self.is_standard is None:
                raise InvalidDataError('Property has value or name, '
                                       'but no is_standard flag!')
            if self.values is not None:
                value_count = len(self.values)
                v = 0
                if value_count >= 0x0f:
                    u = 0x0f
                else:
                    u = value_count
            else:
                v = 1
                u = 0

            c = self.name is not None
            n = c and isinstance(self.name, int)
            s = self.is_standard

            size = write_uint(stream, 28)
            size += write_byte(stream, (u << 4) | (v << 3) | (c << 2) | (n << 1) | s)
            if c:
                if n:
                    size += write_uint(stream, self.name)   # type: ignore
                else:
                    size += self.name.write(stream)         # type: ignore
            if not v:
                if u == 0x0f:
                    size += write_uint(stream, self.name)   # type: ignore
                size += sum(write_property_value(stream, p) for p in self.values)   # type: ignore
        return size


class XName(Record):
    """
    XName record (ID 30, 31)

    Attributes:
        attribute (int): Attribute number
        bstring (bytes): XName data
        reference_number (Optional[int]): None means to use implicit numbering
    """
    attribute: int
    bstring: bytes
    reference_number: Optional[int] = None

    def __init__(self,
                 attribute: int,
                 bstring: bytes,
                 reference_number: int = None):
        """
        Args:
            attribute: Attribute number.
            bstring: Binary XName data.
            reference_number: Reference number for this `XName`.
                Default `None` (implicit).
        """
        self.attribute = attribute
        self.bstring = bstring
        self.reference_number = reference_number

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'XName':
        if record_id not in (30, 31):
            raise InvalidDataError('Invalid record id for XName: '
                                   '{}'.format(record_id))
        attribute = read_uint(stream)
        bstring = read_bstring(stream)
        if record_id == 31:
            reference_number: Optional[int] = read_uint(stream)
        else:
            reference_number = None
        record = XName(attribute, bstring, reference_number)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        record_id = 30 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += write_uint(stream, self.attribute)
        size += write_bstring(stream, self.bstring)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size


class XElement(Record):
    """
    XElement record (ID 32)

    Attributes:
        attribute (int): Attribute number.
        bstring (bytes): XElement data.
    """
    attribute: int
    bstring: bytes

    def __init__(self, attribute: int, bstring: bytes):
        """
        Args:
            attribute: Attribute number.
            bstring: Binary data for this XElement.
        """
        self.attribute = attribute
        self.bstring = bstring

    def merge_with_modals(self, modals: Modals):
        pass

    def deduplicate_with_modals(self, modals: Modals):
        pass

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'XElement':
        if record_id != 32:
            raise InvalidDataError('Invalid record id for XElement: '
                                   '{}'.format(record_id))
        attribute = read_uint(stream)
        bstring = read_bstring(stream)
        record = XElement(attribute, bstring)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        size = write_uint(stream, 32)
        size += write_uint(stream, self.attribute)
        size += write_bstring(stream, self.bstring)
        return size


class XGeometry(Record, GeometryMixin):
    """
    XGeometry record (ID 33)

    Attributes:
        attribute (int): Attribute number.
        bstring (bytes): XGeometry data.
        layer (Optional[int]): None means reuse modal
        datatype (Optional[int]): None means reuse modal
        x (Optional[int]): None means reuse modal
        y (Optional[int]): None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any
    """
    attribute: int
    bstring: bytes
    layer: Optional[int] = None
    datatype: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None

    def __init__(self,
                 attribute: int,
                 bstring: bytes,
                 layer: Optional[int] = None,
                 datatype: Optional[int] = None,
                 x: Optional[int] = None,
                 y: Optional[int] = None,
                 repetition: Optional[repetition_t] = None):
        """
        Args:
            attribute: Attribute number for this XGeometry.
            bstring: Binary data for this XGeometry.
            layer: Layer number. Default `None` (reuse modal).
            datatype: Datatype number. Default `None` (reuse modal).
            x: X-offset. Default `None` (use modal).
            y: Y-offset. Default `None` (use modal).
            repetition: Repetition. Default `None` (no repetition).
        """
        self.attribute = attribute
        self.bstring = bstring
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'XGeometry':
        if record_id != 33:
            raise InvalidDataError('Invalid record id for XGeometry: '
                                   '{}'.format(record_id))

        z0, z1, z2, x, y, r, d, l = read_bool_byte(stream)
        if z0 or z1 or z2:
            raise InvalidDataError('Malformed XGeometry header')
        attribute = read_uint(stream)
        optional: Dict[str, Any] = {}
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        bstring = read_bstring(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)

        record = XGeometry(attribute, bstring, **optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        size = write_uint(stream, 33)
        size += write_bool_byte(stream, (0, 0, 0, x, y, r, d, l))
        size += write_uint(stream, self.attribute)
        if l:
            size += write_uint(stream, self.layer)      # type: ignore
        if d:
            size += write_uint(stream, self.datatype)   # type: ignore
        size += write_bstring(stream, self.bstring)
        if x:
            size += write_sint(stream, self.x)          # type: ignore
        if y:
            size += write_sint(stream, self.y)          # type: ignore
        if r:
            size += self.repetition.write(stream)       # type: ignore
        return size


class Cell(Record):
    """
    Cell record (ID 13, 14)

    Attributes:
        name (Union[int, NString]): int specifies "CellName reference" number
    """
    name: Union[int, NString]

    def __init__(self, name: Union[int, str, NString]):
        """
        Args:
            name: `NString`, or an int specifying a `CellName` reference number.
        """
        self.name = name if isinstance(name, (int, NString)) else NString(name)

    def merge_with_modals(self, modals: Modals):
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals):
        modals.reset()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Cell':
        name: Union[int, NString]
        if record_id == 13:
            name = read_uint(stream)
        elif record_id == 14:
            name = NString.read(stream)
        else:
            raise InvalidDataError('Invalid record id for Cell: '
                                   '{}'.format(record_id))
        record = Cell(name)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        size = 0
        if isinstance(self.name, int):
            size += write_uint(stream, 13)
            size += write_uint(stream, self.name)
        else:
            size += write_uint(stream, 14)
            size += self.name.write(stream)
        return size


class Placement(Record):
    """
    Placement record (ID 17, 18)

    Attributes:
        name (Union[NString, int, None]): name, "CellName reference"
                    number, or reuse modal
        magnification (real_t): Magnification factor
        angle (real_t): Rotation, degrees counterclockwise
        x (Optional[int]): x-offset, None means reuse modal
        y (Optional[int]): y-offset, None means reuse modal
        repetition (repetition_t or None): Repetition, if any
        flip (bool): Whether to perform reflection about the x-axis.
    """
    name: Union[NString, int, None] = None
    magnification: Optional[real_t] = None
    angle: Optional[real_t] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None
    flip: bool

    def __init__(self,
                 flip: bool,
                 name: Union[NString, str, int, None] = None,
                 magnification: Optional[real_t] = None,
                 angle: Optional[real_t] = None,
                 x: Optional[int] = None,
                 y: Optional[int] = None,
                 repetition: Optional[repetition_t] = None):
        """
        Args:
            flip: Whether to perform reflection about the x-axis.
            name: `NString`, an int specifying a `CellName` reference number,
                or `None` (reuse modal).
            magnification: Magnification factor. Default `None` (use modal).
            angle: Rotation angle in degrees, counterclockwise.
                Default `None` (reuse modal).
            x: X-offset. Default `None` (use modal).
            y: Y-offset. Default `None` (use modal).
            repetition: Repetition. Default `None` (no repetition).
        """
        self.x = x
        self.y = y
        self.repetition = repetition
        self.flip = flip
        self.magnification = magnification
        self.angle = angle
        if isinstance(name, (int, NString)) or name is None:
            self.name = name
        else:
            self.name = NString(name)

    def get_name(self) -> Union[NString, int]:
        return verify_modal(self.name)  # type: ignore

    def get_x(self) -> int:
        return verify_modal(self.x)

    def get_y(self) -> int:
        return verify_modal(self.y)

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'placement_x', 'placement_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'name', modals, 'placement_cell')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'placement_x', 'placement_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'name', modals, 'placement_cell')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Placement':
        if record_id not in (17, 18):
            raise InvalidDataError('Invalid record id for Placement: '
                                   '{}'.format(record_id))

        #CNXYRAAF (17) or CNXYRMAF (18)
        c, n, x, y, r, ma0, ma1, flip = read_bool_byte(stream)

        optional: Dict[str, Any] = {}
        name = read_refname(stream, c, n)
        if record_id == 17:
            aa = (ma0 << 1) | ma1
            optional['angle'] = aa * 90
        elif record_id == 18:
            m = ma0
            a = ma1
            if m:
                optional['magnification'] = read_real(stream)
            if a:
                optional['angle'] = read_real(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)

        record = Placement(flip, name, **optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        c = self.name is not None
        n = c and isinstance(self.name, int)
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        f = self.flip

        if ((self.magnification is None or self.magnification == 1) and
                ((self.angle is None or abs(self.angle % 90.0) < 1e-14))):
            aa = int((self.angle / 90) % 4.0)                 # type: ignore
            bools = (c, n, x, y, r, aa & 0b10, aa & 0b01, f)
            m = False
            a = False
            record_id = 17
        else:
            m = self.magnification is not None
            a = self.angle is not None
            bools = (c, n, x, y, r, m, a, f)
            record_id = 18

        size = write_uint(stream, record_id)
        size += write_bool_byte(stream, bools)
        if c:
            if n:
                size += write_uint(stream, self.name)       # type: ignore
            else:
                size += self.name.write(stream)             # type: ignore
        if m:
            size += write_real(stream, self.magnification)  # type: ignore
        if a:
            size += write_real(stream, self.angle)          # type: ignore
        if x:
            size += write_sint(stream, self.x)              # type: ignore
        if y:
            size += write_sint(stream, self.y)              # type: ignore
        if r:
            size += self.repetition.write(stream)           # type: ignore
        return size


class Text(Record, GeometryMixin):
    """
    Text record (ID 19)

    Attributes:
        string (Union[AString, int, None]): None means reuse modal
        layer (Optiona[int]): None means reuse modal
        datatype (Optional[int]): None means reuse modal
        x (Optional[int]): x-offset, None means reuse modal
        y (Optional[int]): y-offset, None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any
    """
    string: Optional[Union[AString, int]] = None
    layer: Optional[int] = None
    datatype: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None

    def __init__(self,
                 string: Union[AString, str, int, None] = None,
                 layer: Optional[int] = None,
                 datatype: Optional[int] = None,
                 x: Optional[int] = None,
                 y: Optional[int] = None,
                 repetition: Optional[repetition_t] = None):
        """
        Args:
            string: Text content, or `TextString` reference number.
                Default `None` (use modal).
            layer: Layer number. Default `None` (reuse modal).
            datatype: Datatype number. Default `None` (reuse modal).
            x: X-offset. Default `None` (use modal).
            y: Y-offset. Default `None` (use modal).
            repetition: Repetition. Default `None` (no repetition).
        """
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        if isinstance(string, (AString, int)) or string is None:
            self.string = string
        else:
            self.string = AString(string)

    def get_string(self) -> Union[AString, int]:
        return verify_modal(self.string)          # type: ignore

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'text_x', 'text_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'string', modals, 'text_string')
        adjust_field(self, 'layer', modals, 'text_layer')
        adjust_field(self, 'datatype', modals, 'text_datatype')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'text_x', 'text_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'string', modals, 'text_string')
        dedup_field(self, 'layer', modals, 'text_layer')
        dedup_field(self, 'datatype', modals, 'text_datatype')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Text':
        if record_id != 19:
            raise InvalidDataError('Invalid record id for Text: '
                                   '{}'.format(record_id))

        z0, c, n, x, y, r, d, l = read_bool_byte(stream)
        if z0:
            raise InvalidDataError('Malformed Text header')

        optional: Dict[str, Any] = {}
        string = read_refstring(stream, c, n)
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)

        record = Text(string, **optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        c = self.string is not None
        n = c and isinstance(self.string, int)
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        size = write_uint(stream, 19)
        size += write_bool_byte(stream, (0, c, n, x, y, r, d, l))
        if c:
            if n:
                size += write_uint(stream, self.string) # type: ignore
            else:
                size += self.string.write(stream)       # type: ignore
        if l:
            size += write_uint(stream, self.layer)      # type: ignore
        if d:
            size += write_uint(stream, self.datatype)   # type: ignore
        if x:
            size += write_sint(stream, self.x)          # type: ignore
        if y:
            size += write_sint(stream, self.y)          # type: ignore
        if r:
            size += self.repetition.write(stream)       # type: ignore
        return size


class Rectangle(Record, GeometryMixin):
    """
    Rectangle record (ID 20)

    (x, y) denotes the lower-left (min-x, min-y) corner of the rectangle.

    Attributes:
        is_square (bool): `True` if this is a square.
                        If `True`, `height` must be `None`.
        width (Optional[int]): X-width. `None` means reuse modal.
        height (Optional[int]): Y-height. Must be `None` if `is_square` is `True`.
                        If `is_square` is `False`, `None` means reuse modal.
        layer (Optional[int]): None means reuse modal
        datatype (Optional[int]): None means reuse modal
        x (Optional[int]): x-offset of the rectangle's lower-left (min-x) point.
            None means reuse modal.
        y (Optional[int]): y-offset of the rectangle's lower-left (min-y) point.
            None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any.
    """
    layer: Optional[int] = None
    datatype: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None
    is_square: bool = False

    def __init__(self,
                 is_square: bool = False,
                 layer: Optional[int] = None,
                 datatype: Optional[int] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 x: Optional[int] = None,
                 y: Optional[int] = None,
                 repetition: Optional[repetition_t] = None):
        self.is_square = is_square
        self.layer = layer
        self.datatype = datatype
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.repetition = repetition
        if is_square and self.height is not None:
            raise InvalidDataError('Rectangle is square and also has height')

    def get_width(self) -> int:
        return verify_modal(self.width)

    def get_height(self) -> int:
        if self.is_square:
            return verify_modal(self.width)
        return verify_modal(self.height)

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'width', modals, 'geometry_w')
        if self.is_square:
            adjust_field(self, 'width', modals, 'geometry_h')
        else:
            adjust_field(self, 'height', modals, 'geometry_h')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'width', modals, 'geometry_w')
        if self.is_square:
            dedup_field(self, 'width', modals, 'geometry_h')
        else:
            dedup_field(self, 'height', modals, 'geometry_h')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Rectangle':
        if record_id != 20:
            raise InvalidDataError('Invalid record id for Rectangle: '
                                   '{}'.format(record_id))

        is_square, w, h, x, y, r, d, l = read_bool_byte(stream)
        optional: Dict[str, Any] = {}
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        if w:
            optional['width'] = read_uint(stream)
        if h:
            optional['height'] = read_uint(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)
        record = Rectangle(is_square, **optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        s = self.is_square
        w = self.width is not None
        h = self.height is not None
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        size = write_uint(stream, 20)
        size += write_bool_byte(stream, (s, w, h, x, y, r, d, l))
        if l:
            size += write_uint(stream, self.layer)      # type: ignore
        if d:
            size += write_uint(stream, self.datatype)   # type: ignore
        if w:
            size += write_uint(stream, self.width)      # type: ignore
        if h:
            size += write_uint(stream, self.height)     # type: ignore
        if x:
            size += write_sint(stream, self.x)          # type: ignore
        if y:
            size += write_sint(stream, self.y)          # type: ignore
        if r:
            size += self.repetition.write(stream)       # type: ignore
        return size


class Polygon(Record, GeometryMixin):
    """
    Polygon record (ID 21)

    Attributes:
        point_list (Optional[point_list_t]): List of offsets from the
            initial vertex (x, y) to the remaining vertices,
            `[[dx0, dy0], [dx1, dy1], ...]`.
            The list is an implicitly closed path, vertices are [int, int],
            The initial vertex is located at (x, y) and is not represented
              in `point_list`.
            `None` means reuse modal.
        layer (Optional[int]): Layer number. None means reuse modal
        datatype (Optional[int]): Datatype number. None means reuse modal
        x (Optional[int]): x-offset of the polygon's first point.
            None means reuse modal
        y (Optional[int]): y-offset of the polygon's first point.
            None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any.
            Default no repetition.
    """
    layer: Optional[int] = None
    datatype: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None
    point_list: Optional[point_list_t] = None

    def __init__(self,
                 point_list: Optional[point_list_t] = None,
                 layer: Optional[int] = None,
                 datatype: Optional[int] = None,
                 x: Optional[int] = None,
                 y: Optional[int] = None,
                 repetition: Optional[repetition_t] = None):
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        self.point_list = point_list

        if point_list is not None:
            if len(point_list) < 3:
                warn('Polygon with < 3 points')

    def get_point_list(self) -> point_list_t:
        return verify_modal(self.point_list)

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'point_list', modals, 'polygon_point_list')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'point_list', modals, 'polygon_point_list')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Polygon':
        if record_id != 21:
            raise InvalidDataError('Invalid record id for Polygon: '
                                   '{}'.format(record_id))

        z0, z1, p, x, y, r, d, l = read_bool_byte(stream)
        if z0 or z1:
            raise InvalidDataError('Invalid polygon header')

        optional: Dict[str, Any] = {}
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        if p:
            optional['point_list'] = read_point_list(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)
        record = Polygon(**optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase, fast: bool = False) -> int:
        p = self.point_list is not None
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        size = write_uint(stream, 21)
        size += write_bool_byte(stream, (0, 0, p, x, y, r, d, l))
        if l:
            size += write_uint(stream, self.layer)          # type: ignore
        if d:
            size += write_uint(stream, self.datatype)       # type: ignore
        if p:
            size += write_point_list(stream, self.point_list,   # type: ignore
                                     implicit_closed=True, fast=fast)
        if x:
            size += write_sint(stream, self.x)      # type: ignore
        if y:
            size += write_sint(stream, self.y)      # type: ignore
        if r:
            size += self.repetition.write(stream)   # type: ignore
        return size


class Path(Record, GeometryMixin):
    """
    Polygon record (ID 22)

    Attributes:
        point_list (Optional[point_list_t]): List of offsets from the
            initial vertex (x, y) to the remaining vertices,
            `[[dx0, dy0], [dx1, dy1], ...]`.
            The initial vertex is located at (x, y) and is not represented
              in `point_list`.
            Offsets are [int, int]; `None` means reuse modal.
        half_width (Optional[int]): None means reuse modal
        extension_start (Optional[Tuple]): None means reuse modal.
            Tuple is of the form (`PathExtensionScheme`, Optional[int])
            Second value is None unless using `PathExtensionScheme.Arbitrary`
            Value determines extension past start point.
        extension_end (Optional[Tuple]): Same form as `extension_end`.
            Value determines extension past end point.
        layer (Optional[int]): None means reuse modal
        datatype (Optional[int]): None means reuse modal
        x (Optional[int]): x-offset, None means reuse modal
        y (Optional[int]): y-offset, None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any
    """
    layer: Optional[int] = None
    datatype: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None
    point_list: Optional[point_list_t] = None
    half_width: Optional[int] = None
    extension_start: Optional[pathextension_t] = None
    extension_end: Optional[pathextension_t] = None

    def __init__(self,
                 point_list: Optional[point_list_t] = None,
                 half_width: Optional[int] = None,
                 extension_start: Optional[pathextension_t] = None,
                 extension_end: Optional[pathextension_t] = None,
                 layer: Optional[int] = None,
                 datatype: Optional[int] = None,
                 x: Optional[int] = None,
                 y: Optional[int] = None,
                 repetition: Optional[repetition_t] = None):
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        self.point_list = point_list
        self.half_width = half_width
        self.extension_start = extension_start
        self.extension_end = extension_end

    def get_point_list(self) -> point_list_t:
        return verify_modal(self.point_list)

    def get_half_width(self) -> int:
        return verify_modal(self.half_width)

    def get_extension_start(self) -> pathextension_t:
        return verify_modal(self.extension_start)

    def get_extension_end(self) -> pathextension_t:
        return verify_modal(self.extension_end)

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'point_list', modals, 'path_point_list')
        adjust_field(self, 'half_width', modals, 'path_half_width')
        adjust_field(self, 'extension_start', modals, 'path_extension_start')
        adjust_field(self, 'extension_end', modals, 'path_extension_end')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'point_list', modals, 'path_point_list')
        dedup_field(self, 'half_width', modals, 'path_half_width')
        dedup_field(self, 'extension_start', modals, 'path_extension_start')
        dedup_field(self, 'extension_end', modals, 'path_extension_end')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Path':
        if record_id != 22:
            raise InvalidDataError('Invalid record id for Path: '
                                   '{}'.format(record_id))

        e, w, p, x, y, r, d, l = read_bool_byte(stream)
        optional: Dict[str, Any] = {}
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        if w:
            optional['half_width'] = read_uint(stream)
        if e:
            scheme = read_uint(stream)
            scheme_end = scheme & 0b11
            scheme_start = (scheme >> 2) & 0b11

            def get_pathext(ext_scheme: int) -> Optional[pathextension_t]:
                if ext_scheme == 0:
                    return None
                elif ext_scheme == 1:
                    return PathExtensionScheme.Flush, None
                elif ext_scheme == 2:
                    return PathExtensionScheme.HalfWidth, None
                elif ext_scheme == 3:
                    return PathExtensionScheme.Arbitrary, read_sint(stream)
                else:
                    raise InvalidDataError('Invalid ext_scheme: {}'.format(ext_scheme))

            optional['extension_start'] = get_pathext(scheme_start)
            optional['extension_end'] = get_pathext(scheme_end)
        if p:
            optional['point_list'] = read_point_list(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)
        record = Path(**optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase, fast: bool = False) -> int:
        e = self.extension_start is not None or self.extension_end is not None
        w = self.half_width is not None
        p = self.point_list is not None
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        size = write_uint(stream, 21)
        size += write_bool_byte(stream, (e, w, p, x, y, r, d, l))
        if l:
            size += write_uint(stream, self.layer)      # type: ignore
        if d:
            size += write_uint(stream, self.datatype)   # type: ignore
        if w:
            size += write_uint(stream, self.half_width) # type: ignore
        if e:
            scheme = 0
            if self.extension_start is not None:
                scheme += self.extension_start[0].value << 2
            if self.extension_end is not None:
                scheme += self.extension_end[0].value
            size += write_uint(stream, scheme)
            if scheme & 0b1100 == 0b1100:
                size += write_sint(stream, self.extension_start[1]) # type: ignore
            if scheme & 0b0011 == 0b0011:
                size += write_sint(stream, self.extension_end[1])   # type: ignore
        if p:
            size += write_point_list(stream, self.point_list,       # type: ignore
                                     implicit_closed=False, fast=fast)
        if x:
            size += write_sint(stream, self.x)      # type: ignore
        if y:
            size += write_sint(stream, self.y)      # type: ignore
        if r:
            size += self.repetition.write(stream)   # type: ignore
        return size


class Trapezoid(Record, GeometryMixin):
    """
    Trapezoid record (ID 23, 24, 25)

    Trapezoid with at least two sides parallel to the x- or y-axis.
    (x, y) denotes the lower-left (min-x, min-y) corner of the trapezoid's bounding box.

    Attributes:
        delta_a (Optional[int]): If horizontal, signed x-distance from top left
            vertex to bottom left vertex. If vertical, signed y-distance from
            bottom left vertex to bottom right vertex.
            None means reuse modal.
        delta_b (Optional[int]): If horizontal, signed x-distance from bottom right
            vertex to top right vertex. If vertical, signed y-distance from top
            right vertex to top left vertex.
            None means reuse modal.
        is_vertical (bool): `True` if the left and right sides are aligned to
            the y-axis. If the trapezoid is a rectangle, either `True` or `False`
            can be used.
        width (Optional[int]): Bounding box x-width, None means reuse modal.
        height (Optional[int]): Bounding box y-height, None means reuse modal.
        layer (Optional[int]): None means reuse modal
        datatype (Optional[int]): None means reuse modal
        x (Optional[int]): x-offset to lower-left corner of the trapezoid's bounding box.
            None means reuse modal
        y (Optional[int]): y-offset to lower-left corner of the trapezoid's bounding box.
            None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any
    """
    layer: Optional[int] = None
    datatype: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None
    delta_a: int = 0
    delta_b: int = 0
    is_vertical: bool

    def __init__(self,
                 is_vertical: bool,
                 delta_a: int = 0,
                 delta_b: int = 0,
                 layer: int = None,
                 datatype: int = None,
                 width: int = None,
                 height: int = None,
                 x: int = None,
                 y: int = None,
                 repetition: repetition_t = None):
        """
        Raises:
            InvalidDataError: if dimensions are impossible.
        """
        self.is_vertical = is_vertical
        self.delta_a = delta_a
        self.delta_b = delta_b
        self.layer = layer
        self.datatype = datatype
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.repetition = repetition

        if self.is_vertical:
            if height is not None and delta_b - delta_a > height:
                raise InvalidDataError('Trapezoid: h < delta_b - delta_a'
                                 ' ({} < {} - {})'.format(height, delta_b, delta_a))
        else:
            if width is not None and delta_b - delta_a > width:
                raise InvalidDataError('Trapezoid: w < delta_b - delta_a'
                                 ' ({} < {} - {})'.format(width, delta_b, delta_a))

    def get_is_vertical(self) -> bool:
        return verify_modal(self.is_vertical)

    def get_delta_a(self) -> int:
        return verify_modal(self.delta_a)

    def get_delta_b(self) -> int:
        return verify_modal(self.delta_b)

    def get_width(self) -> int:
        return verify_modal(self.width)

    def get_height(self) -> int:
        return verify_modal(self.height)

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'width', modals, 'geometry_w')
        adjust_field(self, 'height', modals, 'geometry_h')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'width', modals, 'geometry_w')
        dedup_field(self, 'height', modals, 'geometry_h')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Trapezoid':
        if record_id not in (23, 24, 25):
            raise InvalidDataError('Invalid record id for Trapezoid: '
                                   '{}'.format(record_id))

        is_vertical, w, h, x, y, r, d, l = read_bool_byte(stream)
        optional: Dict[str, Any] = {}
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        if w:
            optional['width'] = read_uint(stream)
        if h:
            optional['height'] = read_uint(stream)
        if record_id != 25:
            optional['delta_a'] = read_sint(stream)
        if record_id != 24:
            optional['delta_b'] = read_sint(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)
        record = Trapezoid(is_vertical, **optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        v = self.is_vertical
        w = self.width is not None
        h = self.height is not None
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        if self.delta_b == 0:
            record_id = 24
        elif self.delta_a == 0:
            record_id = 25
        else:
            record_id = 23
        size = write_uint(stream, record_id)
        size += write_bool_byte(stream, (v, w, h, x, y, r, d, l))
        if l:
            size += write_uint(stream, self.layer)      # type: ignore
        if d:
            size += write_uint(stream, self.datatype)   # type: ignore
        if w:
            size += write_uint(stream, self.width)      # type: ignore
        if h:
            size += write_uint(stream, self.height)     # type: ignore
        if record_id != 25:
            size += write_sint(stream, self.delta_a)    # type: ignore
        if record_id != 24:
            size += write_sint(stream, self.delta_b)    # type: ignore
        if x:
            size += write_sint(stream, self.x)          # type: ignore
        if y:
            size += write_sint(stream, self.y)          # type: ignore
        if r:
            size += self.repetition.write(stream)       # type: ignore
        return size


class CTrapezoid(Record, GeometryMixin):
    """
    CTrapezoid record (ID 26)

    Compact trapezoid formats.
    Two sides are assumed to be parallel to the x- or y-axis, and the remaining
      sides form 45 or 90 degree angles with them.

    `ctrapezoid_type` is in `range(0, 26)`, with the following shapes:
     ____     ____         _____      ______
    | 0  \   / 2  |       /  4  \    /  6  /
    |_____\ /_____|      /_______\  /_____/
     ______ ______       _________  ______
    | 1   / \  3  |      \   5   /  \  7  \
    |____/   \____|       \_____/    \_____\
        w >= h                 w >= 2h

                  ___   ___   |\     /|    /| |\
    |\       /|  |   | |   |  | \   / |   / | | \
    | \     / |  |10 | | 11|  |12| |13|  |14| |15|
    |  \   /  |  |  /   \  |  |  | |  |  |  | |  |
    | 8 | | 9 |  | /     \ |  | /   \ |  | /   \ |
    |___| |___|  |/       \|  |/     \|  |/     \|
       h >= w       h >= w     h >= 2w    h >= 2w

                                            __________
    |\       /|       /\       |\     /|   |    24    | (rect)
    | \     / |      /  \      | \   / |   |__________|
    |16\   /18|     / 20 \     |22\ /23|
    |___\ /___|    /______\    |  / \  |
     ____ ____      ______     | /   \ |
    |   / \   |    \      /    |/     \|      _____
    |17/   \19|     \ 21 /      h = 2w       |     | (sqr)
    | /     \ |      \  /    set h = None    | 25  |
    |/       \|       \/                     |_____|
       w = h        w = 2h                    w = h
    set h = None  set w = None            set h = None


   Attributes:
        ctrapezoid_type (Optional[int]): See above for details.
            None means reuse modal.
        width (Optional[int]): Bounding box x-width.
            None means unnecessary, or reuse modal if necessary.
        height (Optional[int]): Bounding box y-height.
            None means unnecessary, or reuse modal if necessary.
        layer (Optional[int]): None means reuse modal
        datatype (Optional[int]): None means reuse modal
        x (Optional[int]): x-offset of lower-left (min-x) point of bounding box.
            None means reuse modal
        y (Optional[int]): y-offset of lower-left (min-y) point of bounding box.
            None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any
    """
    ctrapezoid_type: Optional[int] = None
    layer: Optional[int] = None
    datatype: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None

    def __init__(self,
                 ctrapezoid_type: int = None,
                 layer: int = None,
                 datatype: int = None,
                 width: int = None,
                 height: int = None,
                 x: int = None,
                 y: int = None,
                 repetition: repetition_t = None):
        """
        Raises:
            InvalidDataError: if dimensions are invalid.
        """
        self.ctrapezoid_type = ctrapezoid_type
        self.layer = layer
        self.datatype = datatype
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.repetition = repetition

        self.check_valid()

    def get_ctrapezoid_type(self) -> int:
        return verify_modal(self.ctrapezoid_type)

    def get_height(self) -> int:
        if self.ctrapezoid_type is None:
            return verify_modal(self.height)
        if self.ctrapezoid_type in (16, 17, 18, 19, 22, 23, 25):
            return verify_modal(self.width)
        return verify_modal(self.height)

    def get_width(self) -> int:
        if self.ctrapezoid_type is None:
            return verify_modal(self.width)
        if self.ctrapezoid_type in (20, 21):
            return verify_modal(self.height)
        return verify_modal(self.width)

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'ctrapezoid_type', modals, 'ctrapezoid_type')

        if self.ctrapezoid_type in (20, 21):
            if self.width is not None:
                raise InvalidDataError('CTrapezoid has spurious width entry: '
                                       '{}'.format(self.width))
        else:
            adjust_field(self, 'width', modals, 'geometry_w')

        if self.ctrapezoid_type in (16, 17, 18, 19, 22, 23, 25):
            if self.height is not None:
                raise InvalidDataError('CTrapezoid has spurious height entry: '
                                       '{}'.format(self.height))
        else:
            adjust_field(self, 'height', modals, 'geometry_h')

        self.check_valid()

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'width', modals, 'geometry_w')
        dedup_field(self, 'height', modals, 'geometry_h')
        dedup_field(self, 'ctrapezoid_type', modals, 'ctrapezoid_type')

        if self.ctrapezoid_type in (20, 21):
            if self.width is not None:
                raise InvalidDataError('CTrapezoid has spurious width entry: '
                                       '{}'.format(self.width))
        else:
            dedup_field(self, 'width', modals, 'geometry_w')

        if self.ctrapezoid_type in (16, 17, 18, 19, 22, 23, 25):
            if self.height is not None:
                raise InvalidDataError('CTrapezoid has spurious height entry: '
                                       '{}'.format(self.height))
        else:
            dedup_field(self, 'height', modals, 'geometry_h')

        self.check_valid()

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'CTrapezoid':
        if record_id != 26:
            raise InvalidDataError('Invalid record id for CTrapezoid: '
                                   '{}'.format(record_id))

        t, w, h, x, y, r, d, l = read_bool_byte(stream)
        optional: Dict[str, Any] = {}
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        if t:
            optional['ctrapezoid_type'] = read_uint(stream)
        if w:
            optional['width'] = read_uint(stream)
        if h:
            optional['height'] = read_uint(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)
        record = CTrapezoid(**optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        t = self.ctrapezoid_type is not None
        w = self.width is not None
        h = self.height is not None
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        size = write_uint(stream, 26)
        size += write_bool_byte(stream, (t, w, h, x, y, r, d, l))
        if l:
            size += write_uint(stream, self.layer)      # type: ignore
        if d:
            size += write_uint(stream, self.datatype)   # type: ignore
        if t:
            size += write_uint(stream, self.ctrapezoid_type) # type: ignore
        if w:
            size += write_uint(stream, self.width)      # type: ignore
        if h:
            size += write_uint(stream, self.height)     # type: ignore
        if x:
            size += write_sint(stream, self.x)          # type: ignore
        if y:
            size += write_sint(stream, self.y)          # type: ignore
        if r:
            size += self.repetition.write(stream)       # type: ignore
        return size

    def check_valid(self):
        ctrapezoid_type = self.ctrapezoid_type
        width = self.width
        height = self.height

        if ctrapezoid_type in (20, 21) and width is not None:
            raise InvalidDataError('CTrapezoid has spurious width entry: '
                                   '{}'.format(width))
        if ctrapezoid_type in (16, 17, 18, 19, 22, 23, 25) and height is not None:
            raise InvalidDataError('CTrapezoid has spurious height entry: '
                                   '{}'.format(height))

        if width is not None and height is not None:
            if ctrapezoid_type in range(0, 4) and width < height:
                raise InvalidDataError('CTrapezoid has width < height'
                                       ' ({} < {})'.format(width, height))
            if ctrapezoid_type in range(4, 8) and width < 2 * height:
                raise InvalidDataError('CTrapezoid has width < 2*height'
                                       ' ({} < 2 * {})'.format(width, height))
            if ctrapezoid_type in range(8, 12) and width > height:
                raise InvalidDataError('CTrapezoid has width > height'
                                       ' ({} > {})'.format(width, height))
            if ctrapezoid_type in range(12, 16) and 2 * width > height:
                raise InvalidDataError('CTrapezoid has 2*width > height'
                                       ' ({} > 2 * {})'.format(width, height))

        if ctrapezoid_type is not None and ctrapezoid_type not in range(0, 26):
            raise InvalidDataError('CTrapezoid has invalid type: '
                                   '{}'.format(ctrapezoid_type))


class Circle(Record, GeometryMixin):
    """
    Circle record (ID 27)

    Attributes:
        radius (Optional[int]): None means reuse modal
        layer (Optional[int]): None means reuse modal
        datatype (Optional[int]): None means reuse modal
        x (Optional[int]): x-offset, None means reuse modal
        y (Optional[int]): y-offset, None means reuse modal
        repetition (Optional[repetition_t]): Repetition, if any
    """
    layer: Optional[int] = None
    datatype: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    repetition: Optional[repetition_t] = None
    radius: Optional[int] = None

    def __init__(self,
                 radius: int = None,
                 layer: int = None,
                 datatype: int = None,
                 x: int = None,
                 y: int = None,
                 repetition: repetition_t = None):
        """
        Args:
            radius: Radius. Default `None` (reuse modal).
            layer: Layer number. Default `None` (reuse modal).
            datatype: Datatype number. Default `None` (reuse modal).
            x: X-offset. Default `None` (use modal).
            y: Y-offset. Default `None` (use modal).
            repetition: Repetition. Default `None` (no repetition).

        Raises:
            InvalidDataError: if dimensions are invalid.
        """
        self.radius = radius
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition

    def get_radius(self) -> int:
        return verify_modal(self.radius)

    def merge_with_modals(self, modals: Modals):
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'radius', modals, 'circle_radius')

    def deduplicate_with_modals(self, modals: Modals):
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'radius', modals, 'circle_radius')

    @staticmethod
    def read(stream: io.BufferedIOBase, record_id: int) -> 'Circle':
        if record_id != 27:
            raise InvalidDataError('Invalid record id for Circle: '
                                   '{}'.format(record_id))

        z0, z1, has_radius, x, y, r, d, l = read_bool_byte(stream)
        if z0 or z1:
            raise InvalidDataError('Malformed circle header')

        optional: Dict[str, Any] = {}
        if l:
            optional['layer'] = read_uint(stream)
        if d:
            optional['datatype'] = read_uint(stream)
        if has_radius:
            optional['radius'] = read_uint(stream)
        if x:
            optional['x'] = read_sint(stream)
        if y:
            optional['y'] = read_sint(stream)
        if r:
            optional['repetition'] = read_repetition(stream)
        record = Circle(**optional)
        logger.debug('Record ending at 0x{:x}:\n {}'.format(stream.tell(), record))
        return record

    def write(self, stream: io.BufferedIOBase) -> int:
        s = self.radius is not None
        x = self.x is not None
        y = self.y is not None
        r = self.repetition is not None
        d = self.datatype is not None
        l = self.layer is not None

        size = write_uint(stream, 27)
        size += write_bool_byte(stream, (0, 0, s, x, y, r, d, l))
        if l:
            size += write_uint(stream, self.layer)      # type: ignore
        if d:
            size += write_uint(stream, self.datatype)   # type: ignore
        if s:
            size += write_uint(stream, self.radius)     # type: ignore
        if x:
            size += write_sint(stream, self.x)          # type: ignore
        if y:
            size += write_sint(stream, self.y)          # type: ignore
        if r:
            size += self.repetition.write(stream)       # type: ignore
        return size


def adjust_repetition(record, modals: Modals):
    """
    Merge the record's repetition entry with the one in the modals

    Args:
        record: Record to read or modify.
        modals: Modals to read or modify.

    Raises:
        InvalidDataError: if a `ReuseRepetition` can't be filled
            from the modals.
    """
    if record.repetition is not None:
        if isinstance(record.repetition, ReuseRepetition):
            if modals.repetition is None:
                raise InvalidDataError('Unfillable repetition')
            else:
                record.repetition = copy.copy(modals.repetition)
        else:
            modals.repetition = copy.copy(record.repetition)


def adjust_field(record, r_field: str, modals: Modals, m_field: str):
    """
    Merge `record.r_field` with `modals.m_field`

    Args:
        record: `Record` to read or modify.
        r_field: Attr of record to access.
        modals: `Modals` to read or modify.
        m_field: Attr of modals to access.

    Raises:
        InvalidDataError: if both fields are `None`
    """
    r = getattr(record, r_field)
    if r is not None:
        setattr(modals, m_field, r)
    else:
        m = getattr(modals, m_field)
        if m is not None:
            setattr(record, r_field, copy.copy(m))
        else:
            raise InvalidDataError('Unfillable field: {}'.format(m_field))


def adjust_coordinates(record, modals: Modals, mx_field: str, my_field: str):
    """
    Merge `record.x` and `record.y` with `modals.mx_field` and `modals.my_field`,
     taking into account the value of `modals.xy_relative`.

    If `modals.xy_relative` is `True` and the record has non-`None` coordinates,
     the modal values are added to the record's coordinates. If `modals.xy_relative`
     is `False`, the coordinates are treated the same way as other fields.

    Args:
        record: `Record` to read or modify.
        modals: `Modals` to read or modify.
        mx_field: Attr of modals corresponding to `record.x`
        my_field: Attr of modals corresponding to `record.y`

    Raises:
        InvalidDataError: if both fields are `None`
    """
    if record.x is not None:
        if modals.xy_relative:
            record.x += getattr(modals, mx_field)
        setattr(modals, mx_field, record.x)
    else:
        record.x = getattr(modals, mx_field)

    if record.y is not None:
        if modals.xy_relative:
            record.y += getattr(modals, my_field)
        setattr(modals, my_field, record.y)
    else:
        record.y = getattr(modals, my_field)


# TODO: Clarify the docs on the dedup_* functions
def dedup_repetition(record, modals: Modals):
    """
    Deduplicate the record's repetition entry with the one in the modals.
    Update the one in the modals if they are different.

    Args:
        record: `Record` to read or modify.
        modals: `Modals` to read or modify.

    Raises:
        InvalidDataError: if a `ReuseRepetition` can't be filled
            from the modals.
    """
    if record.repetition is None:
        return

    if isinstance(record.repetition, ReuseRepetition):
        if modals.repetition is None:
            raise InvalidDataError('Unfillable repetition')
        return

    if record.repetition == modals.repetition:
        record.repetition = ReuseRepetition()
    else:
        modals.repetition = record.repetition


def dedup_field(record, r_field: str, modals: Modals, m_field: str):
    """
    Deduplicate `record.r_field` using `modals.m_field`
    Update the `modals.m_field` if they are different.

    Args:
        record: `Record` to read or modify.
        r_field: Attr of record to access.
        modals: `Modals` to read or modify.
        m_field: Attr of modals to access.

    Args:
        InvalidDataError: if both fields are `None`
    """
    r = getattr(record, r_field)
    m = getattr(modals, m_field)
    if r is not None:
        if m_field in ('polygon_point_list', 'path_point_list'):
            if _USE_NUMPY:
                equal = numpy.array_equal(m, r)
            else:
                equal = (m is not None) and all(tuple(mm) == tuple(rr) for mm, rr in zip(m, r))
        else:
            equal = (m is not None) and m == r

        if equal:
            setattr(record, r_field, None)
        else:
            setattr(modals, m_field, r)
    elif m is None:
        raise InvalidDataError('Unfillable field')


def dedup_coordinates(record, modals: Modals, mx_field: str, my_field: str):
    """
    Deduplicate `record.x` and `record.y` using `modals.mx_field` and `modals.my_field`,
     taking into account the value of `modals.xy_relative`.

    If `modals.xy_relative` is `True` and the record has non-`None` coordinates,
     the modal values are subtracted from the record's coordinates. If `modals.xy_relative`
     is `False`, the coordinates are treated the same way as other fields.

    Args:
        record: `Record` to read or modify.
        modals: `Modals` to read or modify.
        mx_field: Attr of modals corresponding to `record.x`
        my_field: Attr of modals corresponding to `record.y`

    Raises:
        InvalidDataError: if both fields are `None`
    """
    if record.x is not None:
        mx = getattr(modals, mx_field)
        if modals.xy_relative:
            record.x -= mx
            setattr(modals, mx_field, record.x)
        else:
            if record.x == mx:
                record.x = None
            else:
                setattr(modals, mx_field, record.x)

    if record.y is not None:
        my = getattr(modals, my_field)
        if modals.xy_relative:
            record.y -= my
            setattr(modals, my_field, record.y)
        else:
            if record.y == my:
                record.y = None
            else:
                setattr(modals, my_field, record.y)

