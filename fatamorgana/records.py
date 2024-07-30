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
from typing import Any, TypeVar, IO, Union, Protocol
from collections.abc import Sequence
from abc import ABCMeta, abstractmethod
import copy
import math
import zlib
import io
import logging
import pprint
from warnings import warn
from .basic import (
    AString, NString, repetition_t, property_value_t, real_t,
    ReuseRepetition, OffsetTable, Validation, read_point_list, read_property_value,
    read_bstring, read_uint, read_sint, read_real, read_repetition, read_interval,
    write_bstring, write_uint, write_sint, write_real, write_interval, write_point_list,
    write_property_value, read_bool_byte, write_bool_byte, read_byte, write_byte,
    InvalidDataError, UnfilledModalError, PathExtensionScheme, _USE_NUMPY,
    )

if _USE_NUMPY:
    import numpy


logger = logging.getLogger(__name__)


'''
    Type definitions
'''
geometry_t = Union['Text', 'Rectangle', 'Polygon', 'Path', 'Trapezoid',
                   'CTrapezoid', 'Circle', 'XElement', 'XGeometry']
pathextension_t = tuple['PathExtensionScheme', int | None]
point_list_t = Sequence[Sequence[int]]


class Modals:
    """
    Modal variables, used to store data about previously-written or -read records.
    """
    repetition: repetition_t | None = None
    placement_x: int = 0
    placement_y: int = 0
    placement_cell: NString | None = None
    layer: int | None = None
    datatype: int | None = None
    text_layer: int | None = None
    text_datatype: int | None = None
    text_x: int = 0
    text_y: int = 0
    text_string: AString | int | None = None
    geometry_x: int = 0
    geometry_y: int = 0
    xy_relative: bool = False
    geometry_w: int | None = None
    geometry_h: int | None = None
    polygon_point_list: point_list_t | None = None
    path_half_width: int | None = None
    path_point_list: point_list_t | None = None
    path_extension_start: pathextension_t | None = None
    path_extension_end: pathextension_t | None = None
    ctrapezoid_type: int | None = None
    circle_radius: int | None = None
    property_value_list: Sequence[property_value_t] | None = None
    property_name: int | NString | None = None
    property_is_standard: bool | None = None

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
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
def verify_modal(var: T | None) -> T:
    if var is None:
        raise UnfilledModalError
    return var


#
#
#    Records
#
#

class Record(metaclass=ABCMeta):
    """
    Common interface for records.
    """
    @abstractmethod
    def merge_with_modals(self, modals: Modals) -> None:
        """
        Copy all defined values from this record into the modal variables.
        Fill all undefined values in this record from the modal variables.

        Args:
            modals: Modal variables to merge with.
        """
        pass

    @abstractmethod
    def deduplicate_with_modals(self, modals: Modals) -> None:
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
    def read(stream: IO[bytes], record_id: int) -> 'Record':
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
    def write(self, stream: IO[bytes]) -> int:
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

    def dedup_write(self, stream: IO[bytes], modals: Modals) -> int:
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
        return f'{self.__class__}: ' + pprint.pformat(self.__dict__)


class HasRepetition(Protocol):
    repetition: repetition_t | None


class HasXY(Protocol):
    x: int | None
    y: int | None


class GeometryMixin(metaclass=ABCMeta):
    """
    Mixin defining common functions for geometry records
    """
    x: int | None
    y: int | None
    layer: int | None
    datatype: int | None

    def get_x(self) -> int:
        return verify_modal(self.x)

    def get_y(self) -> int:
        return verify_modal(self.y)

    def get_xy(self) -> tuple[int, int]:
        return (self.get_x(), self.get_y())

    def get_layer(self) -> int:
        return verify_modal(self.layer)

    def get_datatype(self) -> int:
        return verify_modal(self.datatype)

    def get_layer_tuple(self) -> tuple[int, int]:
        return (self.get_layer(), self.get_datatype())


def read_refname(
        stream: IO[bytes],
        is_present: bool | int,
        is_reference: bool | int,
        ) -> int | NString | None:
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
    if is_reference:
        return read_uint(stream)
    return NString.read(stream)


def read_refstring(
        stream: IO[bytes],
        is_present: bool | int,
        is_reference: bool | int,
        ) -> int | AString | None:
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
    if is_reference:
        return read_uint(stream)
    return AString.read(stream)


class Pad(Record):
    """
    Pad record (ID 0)
    """
    def merge_with_modals(self, modals: Modals) -> None:
        pass

    def deduplicate_with_modals(self, modals: Modals) -> None:
        pass

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Pad':
        if record_id != 0:
            raise InvalidDataError(f'Invalid record id for Pad {record_id}')
        record = Pad()
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        return write_uint(stream, 0)


class XYMode(Record):
    """
    XYMode record (ID 15, 16)
    """
    relative: bool

    @property
    def absolute(self) -> bool:
        return not self.relative

    @absolute.setter
    def absolute(self, b: bool) -> None:
        self.relative = not b

    def __init__(self, relative: bool) -> None:
        """
        Args:
            relative: `True` if the mode is 'relative', `False` if 'absolute'.
        """
        self.relative = relative

    def merge_with_modals(self, modals: Modals) -> None:
        modals.xy_relative = self.relative

    def deduplicate_with_modals(self, modals: Modals) -> None:
        pass

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'XYMode':
        if record_id not in (15, 16):
            raise InvalidDataError('Invalid record id for XYMode')
        record = XYMode(record_id == 16)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        return write_uint(stream, 15 + self.relative)


class Start(Record):
    """
    Start Record (ID 1)
    """
    version: AString
    """File format version string"""

    unit: real_t
    """positive real number, grid steps per micron"""

    offset_table: OffsetTable | None
    """If `None` then table must be placed in the `End` record"""

    def __init__(
            self,
            unit: real_t,
            version: AString | str = "1.0",
            offset_table: OffsetTable | None = None,
            ) -> None:
        """
        Args
            unit: Grid steps per micron (positive real number)
            version: Version string, default "1.0"
            offset_table: `OffsetTable` for the file, or `None` to place
                    it in the `End` record instead.
        """
        if unit <= 0:
            raise InvalidDataError(f'Non-positive unit: {unit}')
        if math.isnan(unit):
            raise InvalidDataError('NaN unit')
        if math.isinf(unit):
            raise InvalidDataError('Non-finite unit')
        self.unit = unit

        if isinstance(version, AString):
            self.version = version
        else:
            self.version = AString(version)

        if self.version.string != '1.0':
            raise InvalidDataError(f'Invalid version string, only "1.0" is allowed: "{self.version.string}"')
        self.offset_table = offset_table

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Start':
        if record_id != 1:
            raise InvalidDataError(f'Invalid record id for Start: {record_id}')
        version = AString.read(stream)
        unit = read_real(stream)
        has_offset_table = read_uint(stream) == 0
        offset_table: OffsetTable | None
        if has_offset_table:
            offset_table = OffsetTable.read(stream)
        else:
            offset_table = None
        record = Start(unit, version, offset_table)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
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
    """
    offset_table: OffsetTable | None
    """`None` if offset table was written into the `Start` record instead"""

    validation: Validation
    """object containing checksum"""

    def __init__(
            self,
            validation: Validation,
            offset_table: OffsetTable | None = None,
            ) -> None:
        """
        Args:
            validation: `Validation` object for this file.
            offset_table: `OffsetTable`, or `None` if the `Start` record
                    contained an `OffsetTable`. Default `None`.
        """
        self.validation = validation
        self.offset_table = offset_table

    def merge_with_modals(self, modals: Modals) -> None:
        pass

    def deduplicate_with_modals(self, modals: Modals) -> None:
        pass

    @staticmethod
    def read(
            stream: IO[bytes],
            record_id: int,
            has_offset_table: bool
            ) -> 'End':
        if record_id != 2:
            raise InvalidDataError(f'Invalid record id for End {record_id}')
        if has_offset_table:
            offset_table: OffsetTable | None = OffsetTable.read(stream)
        else:
            offset_table = None
        _padding_string = read_bstring(stream)      # noqa
        validation = Validation.read(stream)
        record = End(validation, offset_table)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
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
    """
    compression_type: int
    """ `0` for zlib"""

    decompressed_byte_count: int
    """size after decompressing"""

    compressed_bytes: bytes
    """compressed data"""

    def __init__(
            self,
            compression_type: int,
            decompressed_byte_count: int,
            compressed_bytes: bytes,
            ) -> None:
        """
        Args:
            compression_type: `0` (zlib)
            decompressed_byte_count: Number of bytes in the decompressed data.
            compressed_bytes: The compressed data.
        """
        if compression_type != 0:
            raise InvalidDataError(f'CBlock: Invalid compression scheme {compression_type}')

        self.compression_type = compression_type
        self.decompressed_byte_count = decompressed_byte_count
        self.compressed_bytes = compressed_bytes

    def merge_with_modals(self, modals: Modals) -> None:
        pass

    def deduplicate_with_modals(self, modals: Modals) -> None:
        pass

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'CBlock':
        if record_id != 34:
            raise InvalidDataError(f'Invalid record id for CBlock: {record_id}')
        compression_type = read_uint(stream)
        decompressed_count = read_uint(stream)
        compressed_bytes = read_bstring(stream)
        record = CBlock(compression_type, decompressed_count, compressed_bytes)
        logger.debug(f'CBlock ending at 0x{stream.tell():x} was read successfully')
        return record

    def write(self, stream: IO[bytes]) -> int:
        size = write_uint(stream, 34)
        size += write_uint(stream, self.compression_type)
        size += write_uint(stream, self.decompressed_byte_count)
        size += write_bstring(stream, self.compressed_bytes)
        return size

    @staticmethod
    def from_decompressed(
            decompressed_bytes: bytes,
            compression_type: int = 0,
            compression_args: dict[str, Any] | None = None,
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
            compressed_bytes = (compressor.compress(decompressed_bytes)
                                + compressor.flush())
        else:
            raise InvalidDataError(f'Unknown compression type: {compression_type}')

        return CBlock(compression_type, count, compressed_bytes)

    def decompress(self, decompression_args: dict[str, Any] | None = None) -> bytes:
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
            decompressed_bytes = (decompressor.decompress(self.compressed_bytes)
                                  + decompressor.flush())
            if len(decompressed_bytes) != self.decompressed_byte_count:
                raise InvalidDataError('Decompressed data length does not match!')
        else:
            raise InvalidDataError(f'Unknown compression type: {self.compression_type}')
        return decompressed_bytes


class CellName(Record):
    """
    CellName record (ID 3, 4)
    """
    nstring: NString
    """name string"""

    reference_number: int | None
    """`None` results in implicit assignment"""

    def __init__(
            self,
            nstring: str | NString,
            reference_number: int | None = None,
            ) -> None:
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

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'CellName':
        if record_id not in (3, 4):
            raise InvalidDataError(f'Invalid record id for CellName {record_id}')
        nstring = NString.read(stream)
        if record_id == 4:
            reference_number: int | None = read_uint(stream)
        else:
            reference_number = None
        record = CellName(nstring, reference_number)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        record_id = 3 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.nstring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size

class PropName(Record):
    """
    PropName record (ID 7, 8)
    """
    nstring: NString
    """name string"""

    reference_number: int | None = None
    """`None` results in implicit assignment"""

    def __init__(
            self,
            nstring: str | NString,
            reference_number: int | None = None,
            ) -> None:
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

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'PropName':
        if record_id not in (7, 8):
            raise InvalidDataError(f'Invalid record id for PropName {record_id}')
        nstring = NString.read(stream)
        if record_id == 8:
            reference_number: int | None = read_uint(stream)
        else:
            reference_number = None
        record = PropName(nstring, reference_number)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        record_id = 7 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.nstring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size


class TextString(Record):
    """
    TextString record (ID 5, 6)
    """
    astring: AString
    """string contents"""

    reference_number: int | None = None
    """`None` results in implicit assignment"""

    def __init__(
            self,
            string: AString | str,
            reference_number: int | None = None,
            ) -> None:
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

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'TextString':
        if record_id not in (5, 6):
            raise InvalidDataError(f'Invalid record id for TextString: {record_id}')
        astring = AString.read(stream)
        if record_id == 6:
            reference_number: int | None = read_uint(stream)
        else:
            reference_number = None
        record = TextString(astring, reference_number)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        record_id = 5 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.astring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size


class PropString(Record):
    """
    PropString record (ID 9, 10)
    """
    astring: AString
    """string contents"""

    reference_number: int | None
    """`None` results in implicit assignment"""

    def __init__(
            self,
            string: AString | str,
            reference_number: int | None = None,
            ) -> None:
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

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'PropString':
        if record_id not in (9, 10):
            raise InvalidDataError(f'Invalid record id for PropString: {record_id}')
        astring = AString.read(stream)
        if record_id == 10:
            reference_number: int | None = read_uint(stream)
        else:
            reference_number = None
        record = PropString(astring, reference_number)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        record_id = 9 + (self.reference_number is not None)
        size = write_uint(stream, record_id)
        size += self.astring.write(stream)
        if self.reference_number is not None:
            size += write_uint(stream, self.reference_number)
        return size


class LayerName(Record):
    """
    LayerName record (ID 11, 12)
    """
    nstring: NString
    """name string"""

    layer_interval: tuple[int | None, int | None]
    """bounds on the interval"""

    type_interval: tuple[int | None, int | None]
    """bounds on the interval"""

    is_textlayer: bool
    """Is this a text layer?"""

    def __init__(
            self,
            nstring: str | NString,
            layer_interval: tuple[int | None, int | None],
            type_interval: tuple[int | None, int | None],
            is_textlayer: bool,
            ) -> None:
        """
        Args:
            nstring: The layer name.
            layer_interval: Tuple giving bounds (or lack of thereof) on the layer number.
            type_interval: Tuple giving bounds (or lack of thereof) on the type number.
            is_textlayer: `True` if the layer is a text layer.
        """
        if isinstance(nstring, NString):
            self.nstring = nstring
        else:
            self.nstring = NString(nstring)
        self.layer_interval = layer_interval
        self.type_interval = type_interval
        self.is_textlayer = is_textlayer

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'LayerName':
        if record_id not in (11, 12):
            raise InvalidDataError(f'Invalid record id for LayerName: {record_id}')
        is_textlayer = (record_id == 12)
        nstring = NString.read(stream)
        layer_interval = read_interval(stream)
        type_interval = read_interval(stream)
        record = LayerName(nstring, layer_interval, type_interval, is_textlayer)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        record_id = 11 + self.is_textlayer
        size = write_uint(stream, record_id)
        size += self.nstring.write(stream)
        size += write_interval(stream, *self.layer_interval)
        size += write_interval(stream, *self.type_interval)
        return size


class Property(Record):
    """
    LayerName record (ID 28, 29)
    """
    name: NString | int | None
    """`int` is an explicit reference, `None` is a flag to use Modal"""
    values: list[property_value_t] | None
    is_standard: bool | None
    """Whether this is a standard property."""

    def __init__(
            self,
            name: NString | str | int | None = None,
            values: list[property_value_t] | None= None,
            is_standard: bool | None = None,
            ) -> None:
        """
        Args:
            name: Property name, reference number, or `None` (i.e. use modal)
                Default `None.
            values: List of property values, or `None` (i.e. use modal)
                Default `None`.
            is_standard: `True` if this is a standard property. `None` to use modal.
                Default `None`.
        """
        if isinstance(name, NString | int) or name is None:
            self.name = name
        else:
            self.name = NString(name)
        self.values = values
        self.is_standard = is_standard

    def get_name(self) -> NString | int:
        return verify_modal(self.name)  # type: ignore

    def get_values(self) -> list[property_value_t]:
        return verify_modal(self.values)

    def get_is_standard(self) -> bool:
        return verify_modal(self.is_standard)

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_field(self, 'name', modals, 'property_name')
        adjust_field(self, 'values', modals, 'property_value_list')
        adjust_field(self, 'is_standard', modals, 'property_is_standard')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_field(self, 'name', modals, 'property_name')
        dedup_field(self, 'values', modals, 'property_value_list')
        if self.values is None and self.name is None:
            dedup_field(self, 'is_standard', modals, 'property_is_standard')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Property':
        if record_id not in (28, 29):
            raise InvalidDataError(f'Invalid record id for PropertyValue: {record_id}')
        if record_id == 29:
            record = Property()
        else:
            byte = read_byte(stream)      # UUUUVCNS
            uu = 0x0f & (byte >> 4)
            vv = 0x01 & (byte >> 3)
            cc = 0x01 & (byte >> 2)
            nn = 0x01 & (byte >> 1)
            ss = 0x01 & (byte >> 0)

            name = read_refname(stream, cc, nn)
            if vv == 0:
                if uu < 0x0f:
                    value_count = uu
                else:
                    value_count = read_uint(stream)
                values: list[property_value_t] | None = [read_property_value(stream)
                                                         for _ in range(value_count)]
            else:
                values = None
#                if uu != 0:
#                    logger.warning('Malformed property record header; requested modal'
#                                   ' values but had nonzero count. Ignoring count.')
            record = Property(name, values, bool(ss))
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        if self.is_standard is None and self.values is None and self.name is None:
            return write_uint(stream, 29)

        if self.is_standard is None:
            raise InvalidDataError('Property has value or name, but no is_standard flag!')

        if self.values is not None:
            value_count = len(self.values)
            vv = 0
            uu = 0x0f if value_count >= 0x0f else value_count
        else:
            vv = 1
            uu = 0

        cc = self.name is not None
        nn = cc and isinstance(self.name, int)
        ss = self.is_standard

        size = write_uint(stream, 28)
        size += write_byte(stream, (uu << 4) | (vv << 3) | (cc << 2) | (nn << 1) | ss)
        if cc:
            if nn:
                size += write_uint(stream, self.name)   # type: ignore
            else:
                size += self.name.write(stream)         # type: ignore
        if not vv:
            if uu == 0x0f:
                size += write_uint(stream, len(self.values))   # type: ignore
            size += sum(write_property_value(stream, pp) for pp in self.values)   # type: ignore
        return size


class XName(Record):
    """
    XName record (ID 30, 31)
    """
    attribute: int
    """Attribute number"""

    bstring: bytes
    """XName data"""

    reference_number: int | None
    """None means to use implicit numbering"""

    def __init__(
            self,
            attribute: int,
            bstring: bytes,
            reference_number: int | None = None,
            ) -> None:
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

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'XName':
        if record_id not in (30, 31):
            raise InvalidDataError(f'Invalid record id for XName: {record_id}')
        attribute = read_uint(stream)
        bstring = read_bstring(stream)
        if record_id == 31:
            reference_number: int | None = read_uint(stream)
        else:
            reference_number = None
        record = XName(attribute, bstring, reference_number)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
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
    """
    attribute: int
    """Attribute number"""

    bstring: bytes
    """XElement data"""

    properties: list['Property']

    def __init__(
            self,
            attribute: int,
            bstring: bytes,
            properties: list['Property'] | None = None,
            ) -> None:
        """
        Args:
            attribute: Attribute number.
            bstring: Binary data for this XElement.
            properties: List of property records associated with this record.
        """
        self.attribute = attribute
        self.bstring = bstring
        self.properties = [] if properties is None else properties

    def merge_with_modals(self, modals: Modals) -> None:
        pass

    def deduplicate_with_modals(self, modals: Modals) -> None:
        pass

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'XElement':
        if record_id != 32:
            raise InvalidDataError(f'Invalid record id for XElement: {record_id}')
        attribute = read_uint(stream)
        bstring = read_bstring(stream)
        record = XElement(attribute, bstring)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        size = write_uint(stream, 32)
        size += write_uint(stream, self.attribute)
        size += write_bstring(stream, self.bstring)
        return size


class XGeometry(Record, GeometryMixin):
    """
    XGeometry record (ID 33)
    """
    attribute: int
    """Attribute number"""

    bstring: bytes
    """XGeometry data"""

    layer: int | None = None
    datatype: int | None = None
    x: int | None = None
    y: int | None = None
    repetition: repetition_t | None = None
    properties: list['Property']

    def __init__(
            self,
            attribute: int,
            bstring: bytes,
            layer: int | None = None,
            datatype: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
        """
        Args:
            attribute: Attribute number for this XGeometry.
            bstring: Binary data for this XGeometry.
            layer: Layer number. Default `None` (reuse modal).
            datatype: Datatype number. Default `None` (reuse modal).
            x: X-offset. Default `None` (use modal).
            y: Y-offset. Default `None` (use modal).
            repetition: Repetition. Default `None` (no repetition).
            properties: List of property records associated with this record.
        """
        self.attribute = attribute
        self.bstring = bstring
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        self.properties = [] if properties is None else properties

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'XGeometry':
        if record_id != 33:
            raise InvalidDataError(f'Invalid record id for XGeometry: {record_id}')

        z0, z1, z2, xx, yy, rr, dd, ll = read_bool_byte(stream)
        if z0 or z1 or z2:
            raise InvalidDataError('Malformed XGeometry header')
        attribute = read_uint(stream)
        optional: dict[str, Any] = {}
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        bstring = read_bstring(stream)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)

        record = XGeometry(attribute, bstring, **optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        size = write_uint(stream, 33)
        size += write_bool_byte(stream, (0, 0, 0, xx, yy, rr, dd, ll))
        size += write_uint(stream, self.attribute)
        if ll:
            size += write_uint(stream, self.layer)      # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)   # type: ignore
        size += write_bstring(stream, self.bstring)
        if xx:
            size += write_sint(stream, self.x)          # type: ignore
        if yy:
            size += write_sint(stream, self.y)          # type: ignore
        if rr:
            size += self.repetition.write(stream)       # type: ignore
        return size


class Cell(Record):
    """
    Cell record (ID 13, 14)
    """
    name: int | NString
    """int specifies "CellName reference" number"""

    def __init__(self, name: int | str | NString) -> None:
        """
        Args:
            name: `NString`, or an int specifying a `CellName` reference number.
        """
        self.name = name if isinstance(name, int | NString) else NString(name)

    def merge_with_modals(self, modals: Modals) -> None:
        modals.reset()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        modals.reset()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Cell':
        name: int | NString
        if record_id == 13:
            name = read_uint(stream)
        elif record_id == 14:
            name = NString.read(stream)
        else:
            raise InvalidDataError(f'Invalid record id for Cell: {record_id}')
        record = Cell(name)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
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
    """
    name: int | NString | None = None
    """name, "CellName reference" number, or reuse modal"""

    magnification: real_t | None = None
    """magnification factor"""

    angle: real_t | None = None
    """Rotation, degrees counterclockwise"""

    x: int | None = None
    y: int | None = None
    repetition: repetition_t | None = None
    flip: bool
    """Whether to perform reflection about the x-axis"""

    properties: list['Property']

    def __init__(
            self,
            flip: bool,
            name: NString | str | int | None = None,
            magnification: real_t | None = None,
            angle: real_t | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
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
            properties: List of property records associated with this record.
        """
        self.x = x
        self.y = y
        self.repetition = repetition
        self.flip = flip
        self.magnification = magnification
        self.angle = angle
        if isinstance(name, int | NString) or name is None:
            self.name = name
        else:
            self.name = NString(name)
        self.properties = [] if properties is None else properties

    def get_name(self) -> NString | int:
        return verify_modal(self.name)  # type: ignore

    def get_x(self) -> int:
        return verify_modal(self.x)

    def get_y(self) -> int:
        return verify_modal(self.y)

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'placement_x', 'placement_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'name', modals, 'placement_cell')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'placement_x', 'placement_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'name', modals, 'placement_cell')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Placement':
        if record_id not in (17, 18):
            raise InvalidDataError(f'Invalid record id for Placement: {record_id}')

        #CNXYRAAF (17) or CNXYRMAF (18)
        cc, nn, xx, yy, rr, ma0, ma1, flip = read_bool_byte(stream)

        optional: dict[str, Any] = {}
        name = read_refname(stream, cc, nn)
        if record_id == 17:
            aa = int((ma0 << 1) | ma1)
            optional['angle'] = aa * 90
        elif record_id == 18:
            mm = ma0
            aa1 = ma1
            if mm:
                optional['magnification'] = read_real(stream)
            if aa1:
                optional['angle'] = read_real(stream)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)

        record = Placement(flip, name, **optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        cc = self.name is not None
        nn = cc and isinstance(self.name, int)
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        ff = self.flip

        if (self.magnification == 1
                and self.angle is not None
                and abs(self.angle % 90.0) < 1e-14):
            aa = int((self.angle / 90) % 4.0)
            bools = (cc, nn, xx, yy, rr, aa & 0b10, aa & 0b01, ff)
            mm = False
            aq = False
            record_id = 17
        else:
            mm = self.magnification is not None
            aq = self.angle is not None
            bools = (cc, nn, xx, yy, rr, mm, aq, ff)
            record_id = 18

        size = write_uint(stream, record_id)
        size += write_bool_byte(stream, bools)
        if cc:
            if nn:
                size += write_uint(stream, self.name)       # type: ignore
            else:
                size += self.name.write(stream)             # type: ignore
        if mm:
            size += write_real(stream, self.magnification)  # type: ignore
        if aa:
            size += write_real(stream, self.angle)          # type: ignore
        if xx:
            size += write_sint(stream, self.x)              # type: ignore
        if yy:
            size += write_sint(stream, self.y)              # type: ignore
        if rr:
            size += self.repetition.write(stream)           # type: ignore
        return size


class Text(Record, GeometryMixin):
    """
    Text record (ID 19)
    """
    string: AString | int | None = None
    layer: int | None = None
    datatype: int | None = None
    x: int | None = None
    y: int | None = None
    repetition: repetition_t | None = None
    properties: list['Property']

    def __init__(
            self,
            string: AString | str | int | None = None,
            layer: int | None = None,
            datatype: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
        """
        Args:
            string: Text content, or `TextString` reference number.
                Default `None` (use modal).
            layer: Layer number. Default `None` (reuse modal).
            datatype: Datatype number. Default `None` (reuse modal).
            x: X-offset. Default `None` (use modal).
            y: Y-offset. Default `None` (use modal).
            repetition: Repetition. Default `None` (no repetition).
            properties: List of property records associated with this record.
        """
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        if isinstance(string, int | AString) or string is None:
            self.string = string
        else:
            self.string = AString(string)
        self.properties = [] if properties is None else properties

    def get_string(self) -> AString | int:
        return verify_modal(self.string)          # type: ignore

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'text_x', 'text_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'string', modals, 'text_string')
        adjust_field(self, 'layer', modals, 'text_layer')
        adjust_field(self, 'datatype', modals, 'text_datatype')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'text_x', 'text_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'string', modals, 'text_string')
        dedup_field(self, 'layer', modals, 'text_layer')
        dedup_field(self, 'datatype', modals, 'text_datatype')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Text':
        if record_id != 19:
            raise InvalidDataError(f'Invalid record id for Text: {record_id}')

        z0, cc, nn, xx, yy, rr, dd, ll = read_bool_byte(stream)
        if z0:
            raise InvalidDataError('Malformed Text header')

        optional: dict[str, Any] = {}
        string = read_refstring(stream, cc, nn)
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)

        record = Text(string, **optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        cc = self.string is not None
        nn = cc and isinstance(self.string, int)
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        size = write_uint(stream, 19)
        size += write_bool_byte(stream, (0, cc, nn, xx, yy, rr, dd, ll))
        if cc:
            if nn:
                size += write_uint(stream, self.string)  # type: ignore
            else:
                size += self.string.write(stream)        # type: ignore
        if ll:
            size += write_uint(stream, self.layer)       # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)    # type: ignore
        if xx:
            size += write_sint(stream, self.x)           # type: ignore
        if yy:
            size += write_sint(stream, self.y)           # type: ignore
        if rr:
            size += self.repetition.write(stream)        # type: ignore
        return size


class Rectangle(Record, GeometryMixin):
    """
    Rectangle record (ID 20)

    (x, y) denotes the lower-left (min-x, min-y) corner of the rectangle.
    """
    layer: int | None
    datatype: int | None
    width: int | None
    """X-width. `None` means reuse modal"""

    height: int | None
    """Y-height. Must be `None` if `is_square` is `True`.
       If `is_square` is `False`, `None` means reuse modal
    """

    x: int | None
    """x-offset of the rectangle's lower-left (min-x) point.
       None means reuse modal.
    """
    y: int | None
    """y-offset of the rectangle's lower-left (min-y) point.
       None means reuse modal
    """

    repetition: repetition_t | None
    is_square: bool
    """If `True`, `height` must be `None`"""

    properties: list['Property']

    def __init__(
            self,
            is_square: bool = False,
            layer: int | None = None,
            datatype: int | None = None,
            width: int | None = None,
            height: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
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
        self.properties = [] if properties is None else properties

    def get_width(self) -> int:
        return verify_modal(self.width)

    def get_height(self) -> int:
        if self.is_square:
            return verify_modal(self.width)
        return verify_modal(self.height)

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'width', modals, 'geometry_w')
        if self.is_square:
            adjust_field(self, 'width', modals, 'geometry_h')
        else:
            adjust_field(self, 'height', modals, 'geometry_h')

    def deduplicate_with_modals(self, modals: Modals) -> None:
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
    def read(stream: IO[bytes], record_id: int) -> 'Rectangle':
        if record_id != 20:
            raise InvalidDataError(f'Invalid record id for Rectangle: {record_id}')

        is_square, ww, hh, xx, yy, rr, dd, ll = read_bool_byte(stream)
        optional: dict[str, Any] = {}
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        if ww:
            optional['width'] = read_uint(stream)
        if hh:
            optional['height'] = read_uint(stream)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)
        record = Rectangle(is_square, **optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        ss = self.is_square
        ww = self.width is not None
        hh = self.height is not None
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        size = write_uint(stream, 20)
        size += write_bool_byte(stream, (ss, ww, hh, xx, yy, rr, dd, ll))
        if ll:
            size += write_uint(stream, self.layer)      # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)   # type: ignore
        if ww:
            size += write_uint(stream, self.width)      # type: ignore
        if hh:
            size += write_uint(stream, self.height)     # type: ignore
        if xx:
            size += write_sint(stream, self.x)          # type: ignore
        if yy:
            size += write_sint(stream, self.y)          # type: ignore
        if rr:
            size += self.repetition.write(stream)       # type: ignore
        return size


class Polygon(Record, GeometryMixin):
    """
    Polygon record (ID 21)
    """
    layer: int | None
    datatype: int | None
    x: int | None
    """x-offset of the polygon's first point.
       None means reuse modal
    """
    y: int | None
    """y-offset of the polygon's first point.
       None means reuse modal
    """
    repetition: repetition_t | None
    point_list: point_list_t | None
    """
    List of offsets from the initial vertex (x, y) to the remaining
    vertices, `[[dx0, dy0], [dx1, dy1], ...]`.
    The list is an implicitly closed path, vertices are [int, int].
    The initial vertex is located at (x, y) and is not represented in `point_list`.
    `None` means reuse modal.
    """

    properties: list['Property']

    def __init__(
            self,
            point_list: point_list_t | None = None,
            layer: int | None = None,
            datatype: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        self.point_list = point_list
        self.properties = [] if properties is None else properties

        if point_list is not None and len(point_list) < 3:
            warn('Polygon with < 3 points', stacklevel=2)

    def get_point_list(self) -> point_list_t:
        return verify_modal(self.point_list)

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'point_list', modals, 'polygon_point_list')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'point_list', modals, 'polygon_point_list')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Polygon':
        if record_id != 21:
            raise InvalidDataError(f'Invalid record id for Polygon: {record_id}')

        z0, z1, pp, xx, yy, rr, dd, ll = read_bool_byte(stream)
        if z0 or z1:
            raise InvalidDataError('Invalid polygon header')

        optional: dict[str, Any] = {}
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        if pp:
            optional['point_list'] = read_point_list(stream, implicit_closed=True)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)
        record = Polygon(**optional)
        logger.debug('Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes], fast: bool = False) -> int:
        pp = self.point_list is not None
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        size = write_uint(stream, 21)
        size += write_bool_byte(stream, (0, 0, pp, xx, yy, rr, dd, ll))
        if ll:
            size += write_uint(stream, self.layer)          # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)       # type: ignore
        if pp:
            size += write_point_list(stream, self.point_list,   # type: ignore
                                     implicit_closed=True, fast=fast)
        if xx:
            size += write_sint(stream, self.x)      # type: ignore
        if yy:
            size += write_sint(stream, self.y)      # type: ignore
        if rr:
            size += self.repetition.write(stream)   # type: ignore
        return size


class Path(Record, GeometryMixin):
    """
    Polygon record (ID 22)
    """
    layer: int | None = None
    datatype: int | None = None
    x: int | None = None
    y: int | None = None
    repetition: repetition_t | None = None
    point_list: point_list_t | None = None
    """
    List of offsets from the initial vertex (x, y) to the remaining vertices,
    `[[dx0, dy0], [dx1, dy1], ...]`.
    The initial vertex is located at (x, y) and is not represented in `point_list`.
    Offsets are [int, int]; `None` means reuse modal.
    """

    half_width: int | None = None
    """None means reuse modal"""

    extension_start: pathextension_t | None = None
    """
    `None` means reuse modal.
    Tuple is of the form (`PathExtensionScheme`, int | None)
    Second value is None unless using `PathExtensionScheme.Arbitrary`
    Value determines extension past start point.
    """

    extension_end: pathextension_t | None = None
    """
    Same form as `extension_end`. Value determines extension past end point.
    """

    properties: list['Property']

    def __init__(
            self,
            point_list: point_list_t | None = None,
            half_width: int | None = None,
            extension_start: pathextension_t | None = None,
            extension_end: pathextension_t | None = None,
            layer: int | None = None,
            datatype: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        self.point_list = point_list
        self.half_width = half_width
        self.extension_start = extension_start
        self.extension_end = extension_end
        self.properties = [] if properties is None else properties

    def get_point_list(self) -> point_list_t:
        return verify_modal(self.point_list)

    def get_half_width(self) -> int:
        return verify_modal(self.half_width)

    def get_extension_start(self) -> pathextension_t:
        return verify_modal(self.extension_start)

    def get_extension_end(self) -> pathextension_t:
        return verify_modal(self.extension_end)

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'point_list', modals, 'path_point_list')
        adjust_field(self, 'half_width', modals, 'path_half_width')
        adjust_field(self, 'extension_start', modals, 'path_extension_start')
        adjust_field(self, 'extension_end', modals, 'path_extension_end')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'point_list', modals, 'path_point_list')
        dedup_field(self, 'half_width', modals, 'path_half_width')
        dedup_field(self, 'extension_start', modals, 'path_extension_start')
        dedup_field(self, 'extension_end', modals, 'path_extension_end')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Path':
        if record_id != 22:
            raise InvalidDataError(f'Invalid record id for Path: {record_id}')

        ee, ww, pp, xx, yy, rr, dd, ll = read_bool_byte(stream)
        optional: dict[str, Any] = {}
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        if ww:
            optional['half_width'] = read_uint(stream)
        if ee:
            scheme = read_uint(stream)
            scheme_end = scheme & 0b11
            scheme_start = (scheme >> 2) & 0b11

            def get_pathext(ext_scheme: int) -> pathextension_t | None:
                if ext_scheme == 0:
                    return None
                if ext_scheme == 1:
                    return PathExtensionScheme.Flush, None
                if ext_scheme == 2:
                    return PathExtensionScheme.HalfWidth, None
                if ext_scheme == 3:
                    return PathExtensionScheme.Arbitrary, read_sint(stream)
                raise InvalidDataError(f'Invalid ext_scheme: {ext_scheme}')

            optional['extension_start'] = get_pathext(scheme_start)
            optional['extension_end'] = get_pathext(scheme_end)
        if pp:
            optional['point_list'] = read_point_list(stream, implicit_closed=False)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)
        record = Path(**optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes], fast: bool = False) -> int:
        ee = self.extension_start is not None or self.extension_end is not None
        ww = self.half_width is not None
        pp = self.point_list is not None
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        size = write_uint(stream, 21)
        size += write_bool_byte(stream, (ee, ww, pp, xx, yy, rr, dd, ll))
        if ll:
            size += write_uint(stream, self.layer)       # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)    # type: ignore
        if ww:
            size += write_uint(stream, self.half_width)  # type: ignore
        if ee:
            scheme = 0
            if self.extension_start is not None:
                scheme += self.extension_start[0].value << 2
            if self.extension_end is not None:
                scheme += self.extension_end[0].value
            size += write_uint(stream, scheme)
            if scheme & 0b1100 == 0b1100:
                size += write_sint(stream, self.extension_start[1])  # type: ignore
            if scheme & 0b0011 == 0b0011:
                size += write_sint(stream, self.extension_end[1])    # type: ignore
        if pp:
            size += write_point_list(stream, self.point_list,        # type: ignore
                                     implicit_closed=False, fast=fast)
        if xx:
            size += write_sint(stream, self.x)      # type: ignore
        if yy:
            size += write_sint(stream, self.y)      # type: ignore
        if rr:
            size += self.repetition.write(stream)   # type: ignore
        return size


class Trapezoid(Record, GeometryMixin):
    """
    Trapezoid record (ID 23, 24, 25)

    Trapezoid with at least two sides parallel to the x- or y-axis.
    (x, y) denotes the lower-left (min-x, min-y) corner of the trapezoid's bounding box.
    """
    layer: int | None = None
    datatype: int | None = None
    width: int | None = None
    """Bounding box x-width, None means reuse modal."""

    height: int | None = None
    """Bounding box y-height, None means reuse modal."""

    x: int | None = None
    """x-offset to lower-left corner of the trapezoid's bounding box.
       None means reuse modal
    """

    y: int | None = None
    """y-offset to lower-left corner of the trapezoid's bounding box.
       None means reuse modal
    """

    repetition: repetition_t | None = None
    delta_a: int = 0
    """
    If horizontal, signed x-distance from top left vertex to bottom left vertex.
    If vertical, signed y-distance from bottom left vertex to bottom right vertex.
    None means reuse modal.
    """

    delta_b: int = 0
    """
    If horizontal, signed x-distance from bottom right vertex to top right vertex.
    If vertical, signed y-distance from top right vertex to top left vertex.
    None means reuse modal.
    """

    is_vertical: bool
    """
    `True` if the left and right sides are aligned to the y-axis.
    If the trapezoid is a rectangle, either `True` or `False` can be used.
    """

    properties: list['Property']

    def __init__(
            self,
            is_vertical: bool,
            delta_a: int = 0,
            delta_b: int = 0,
            layer: int | None = None,
            datatype: int | None = None,
            width: int | None = None,
            height: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
        """
        Raises:
            InvalidDataError: if dimensions are impossible.
        """
        self.is_vertical = bool(is_vertical)
        self.delta_a = delta_a
        self.delta_b = delta_b
        self.layer = layer
        self.datatype = datatype
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.repetition = repetition
        self.properties = [] if properties is None else properties

        if self.is_vertical:
            if height is not None and delta_b - delta_a > height:
                raise InvalidDataError(f'Trapezoid: h < delta_b - delta_a ({height} < {delta_b} - {delta_a})')
        elif width is not None and delta_b - delta_a > width:
            raise InvalidDataError(f'Trapezoid: w < delta_b - delta_a ({width} < {delta_b} - {delta_a})')

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

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'width', modals, 'geometry_w')
        adjust_field(self, 'height', modals, 'geometry_h')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'width', modals, 'geometry_w')
        dedup_field(self, 'height', modals, 'geometry_h')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Trapezoid':
        if record_id not in (23, 24, 25):
            raise InvalidDataError(f'Invalid record id for Trapezoid: {record_id}')

        is_vertical, ww, hh, xx, yy, rr, dd, ll = read_bool_byte(stream)
        optional: dict[str, Any] = {}
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        if ww:
            optional['width'] = read_uint(stream)
        if hh:
            optional['height'] = read_uint(stream)
        if record_id != 25:
            optional['delta_a'] = read_sint(stream)
        if record_id != 24:
            optional['delta_b'] = read_sint(stream)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)
        record = Trapezoid(bool(is_vertical), **optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        vv = self.is_vertical
        ww = self.width is not None
        hh = self.height is not None
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        if self.delta_b == 0:
            record_id = 24
        elif self.delta_a == 0:
            record_id = 25
        else:
            record_id = 23
        size = write_uint(stream, record_id)
        size += write_bool_byte(stream, (vv, ww, hh, xx, yy, rr, dd, ll))
        if ll:
            size += write_uint(stream, self.layer)      # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)   # type: ignore
        if ww:
            size += write_uint(stream, self.width)      # type: ignore
        if hh:
            size += write_uint(stream, self.height)     # type: ignore
        if record_id != 25:
            size += write_sint(stream, self.delta_a)    # type: ignore
        if record_id != 24:
            size += write_sint(stream, self.delta_b)    # type: ignore
        if xx:
            size += write_sint(stream, self.x)          # type: ignore
        if yy:
            size += write_sint(stream, self.y)          # type: ignore
        if rr:
            size += self.repetition.write(stream)       # type: ignore
        return size


class CTrapezoid(Record, GeometryMixin):
    r"""
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

    """
    ctrapezoid_type: int | None = None
    """See class docstring for details. None means reuse modal."""

    layer: int | None = None
    datatype: int | None = None
    width: int | None = None
    """width: Bounding box x-width
       None means unnecessary, or reuse modal if necessary.
    """

    height: int | None = None
    """Bounding box y-height.
       None means unnecessary, or reuse modal if necessary.
    """

    x: int | None = None
    """x-offset of lower-left (min-x) point of bounding box.
       None means reuse modal
    """
    y: int | None = None
    """y-offset of lower-left (min-y) point of bounding box.
       None means reuse modal
    """

    repetition: repetition_t | None = None
    properties: list['Property']

    def __init__(
            self,
            ctrapezoid_type: int | None = None,
            layer: int | None = None,
            datatype: int | None = None,
            width: int | None = None,
            height: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
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
        self.properties = [] if properties is None else properties

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

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'ctrapezoid_type', modals, 'ctrapezoid_type')

        if self.ctrapezoid_type in (20, 21):
            if self.width is not None:
                raise InvalidDataError(f'CTrapezoid has spurious width entry: {self.width}')
        else:
            adjust_field(self, 'width', modals, 'geometry_w')

        if self.ctrapezoid_type in (16, 17, 18, 19, 22, 23, 25):
            if self.height is not None:
                raise InvalidDataError(f'CTrapezoid has spurious height entry: {self.height}')
        else:
            adjust_field(self, 'height', modals, 'geometry_h')

        self.check_valid()

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'width', modals, 'geometry_w')
        dedup_field(self, 'height', modals, 'geometry_h')
        dedup_field(self, 'ctrapezoid_type', modals, 'ctrapezoid_type')

        if self.ctrapezoid_type in (20, 21):
            if self.width is not None:
                raise InvalidDataError(f'CTrapezoid has spurious width entry: {self.width}')
        else:
            dedup_field(self, 'width', modals, 'geometry_w')

        if self.ctrapezoid_type in (16, 17, 18, 19, 22, 23, 25):
            if self.height is not None:
                raise InvalidDataError(f'CTrapezoid has spurious height entry: {self.height}')
        else:
            dedup_field(self, 'height', modals, 'geometry_h')

        self.check_valid()

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'CTrapezoid':
        if record_id != 26:
            raise InvalidDataError(f'Invalid record id for CTrapezoid: {record_id}')

        tt, ww, hh, xx, yy, rr, dd, ll = read_bool_byte(stream)
        optional: dict[str, Any] = {}
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        if tt:
            optional['ctrapezoid_type'] = read_uint(stream)
        if ww:
            optional['width'] = read_uint(stream)
        if hh:
            optional['height'] = read_uint(stream)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)
        record = CTrapezoid(**optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        tt = self.ctrapezoid_type is not None
        ww = self.width is not None
        hh = self.height is not None
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        size = write_uint(stream, 26)
        size += write_bool_byte(stream, (tt, ww, hh, xx, yy, rr, dd, ll))
        if ll:
            size += write_uint(stream, self.layer)      # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)   # type: ignore
        if tt:
            size += write_uint(stream, self.ctrapezoid_type)  # type: ignore
        if ww:
            size += write_uint(stream, self.width)      # type: ignore
        if hh:
            size += write_uint(stream, self.height)     # type: ignore
        if xx:
            size += write_sint(stream, self.x)          # type: ignore
        if yy:
            size += write_sint(stream, self.y)          # type: ignore
        if rr:
            size += self.repetition.write(stream)       # type: ignore
        return size

    def check_valid(self) -> None:
        ctrapezoid_type = self.ctrapezoid_type
        width = self.width
        height = self.height

        if ctrapezoid_type in (20, 21) and width is not None:
            raise InvalidDataError(f'CTrapezoid has spurious width entry: {width}')
        if ctrapezoid_type in (16, 17, 18, 19, 22, 23, 25) and height is not None:
            raise InvalidDataError(f'CTrapezoid has spurious height entry: {height}')

        if width is not None and height is not None:
            if ctrapezoid_type in range(0, 4) and width < height:           # noqa: PIE808
                raise InvalidDataError(f'CTrapezoid has width < height ({width} < {height})')
            if ctrapezoid_type in range(4, 8) and width < 2 * height:
                raise InvalidDataError(f'CTrapezoid has width < 2*height ({width} < 2 * {height})')
            if ctrapezoid_type in range(8, 12) and width > height:
                raise InvalidDataError(f'CTrapezoid has width > height ({width} > {height})')
            if ctrapezoid_type in range(12, 16) and 2 * width > height:
                raise InvalidDataError(f'CTrapezoid has 2*width > height ({width} > 2 * {height})')

        if ctrapezoid_type is not None and ctrapezoid_type not in range(0, 26):   # noqa: PIE808
            raise InvalidDataError(f'CTrapezoid has invalid type: {ctrapezoid_type}')


class Circle(Record, GeometryMixin):
    """
    Circle record (ID 27)
    """
    layer: int | None
    datatype: int | None
    x: int | None
    y: int | None
    repetition: repetition_t | None
    radius: int | None
    properties: list['Property']

    def __init__(
            self,
            radius: int | None = None,
            layer: int | None = None,
            datatype: int | None = None,
            x: int | None = None,
            y: int | None = None,
            repetition: repetition_t | None = None,
            properties: list['Property'] | None = None,
            ) -> None:
        """
        Args:
            radius: Radius. Default `None` (reuse modal).
            layer: Layer number. Default `None` (reuse modal).
            datatype: Datatype number. Default `None` (reuse modal).
            x: X-offset. Default `None` (use modal).
            y: Y-offset. Default `None` (use modal).
            repetition: Repetition. Default `None` (no repetition).
            properties: List of property records associated with this record.

        Raises:
            InvalidDataError: if dimensions are invalid.
        """
        self.radius = radius
        self.layer = layer
        self.datatype = datatype
        self.x = x
        self.y = y
        self.repetition = repetition
        self.properties = [] if properties is None else properties

    def get_radius(self) -> int:
        return verify_modal(self.radius)

    def merge_with_modals(self, modals: Modals) -> None:
        adjust_coordinates(self, modals, 'geometry_x', 'geometry_y')
        adjust_repetition(self, modals)
        adjust_field(self, 'layer', modals, 'layer')
        adjust_field(self, 'datatype', modals, 'datatype')
        adjust_field(self, 'radius', modals, 'circle_radius')

    def deduplicate_with_modals(self, modals: Modals) -> None:
        dedup_coordinates(self, modals, 'geometry_x', 'geometry_y')
        dedup_repetition(self, modals)
        dedup_field(self, 'layer', modals, 'layer')
        dedup_field(self, 'datatype', modals, 'datatype')
        dedup_field(self, 'radius', modals, 'circle_radius')

    @staticmethod
    def read(stream: IO[bytes], record_id: int) -> 'Circle':
        if record_id != 27:
            raise InvalidDataError(f'Invalid record id for Circle: {record_id}')

        z0, z1, has_radius, xx, yy, rr, dd, ll = read_bool_byte(stream)
        if z0 or z1:
            raise InvalidDataError('Malformed circle header')

        optional: dict[str, Any] = {}
        if ll:
            optional['layer'] = read_uint(stream)
        if dd:
            optional['datatype'] = read_uint(stream)
        if has_radius:
            optional['radius'] = read_uint(stream)
        if xx:
            optional['x'] = read_sint(stream)
        if yy:
            optional['y'] = read_sint(stream)
        if rr:
            optional['repetition'] = read_repetition(stream)
        record = Circle(**optional)
        logger.debug(f'Record ending at 0x{stream.tell():x}:\n {record}')
        return record

    def write(self, stream: IO[bytes]) -> int:
        ss = self.radius is not None
        xx = self.x is not None
        yy = self.y is not None
        rr = self.repetition is not None
        dd = self.datatype is not None
        ll = self.layer is not None

        size = write_uint(stream, 27)
        size += write_bool_byte(stream, (0, 0, ss, xx, yy, rr, dd, ll))
        if ll:
            size += write_uint(stream, self.layer)      # type: ignore
        if dd:
            size += write_uint(stream, self.datatype)   # type: ignore
        if ss:
            size += write_uint(stream, self.radius)     # type: ignore
        if xx:
            size += write_sint(stream, self.x)          # type: ignore
        if yy:
            size += write_sint(stream, self.y)          # type: ignore
        if rr:
            size += self.repetition.write(stream)       # type: ignore
        return size


def adjust_repetition(record: HasRepetition, modals: Modals) -> None:
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
            record.repetition = copy.copy(modals.repetition)
        else:
            modals.repetition = copy.copy(record.repetition)


def adjust_field(record: Record, r_field: str, modals: Modals, m_field: str) -> None:
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
            raise InvalidDataError(f'Unfillable field: {m_field}')


def adjust_coordinates(record: HasXY, modals: Modals, mx_field: str, my_field: str) -> None:
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
def dedup_repetition(record: HasRepetition, modals: Modals) -> None:
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


def dedup_field(record: Record, r_field: str, modals: Modals, m_field: str) -> None:
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
    rr = getattr(record, r_field)
    mm = getattr(modals, m_field)
    if rr is not None:
        if m_field in ('polygon_point_list', 'path_point_list'):
            if _USE_NUMPY:
                equal = numpy.array_equal(mm, rr)
            else:
                equal = (mm is not None) and all(tuple(mmm) == tuple(rrr) for mmm, rrr in zip(mm, rr, strict=True))
        else:
            equal = (mm is not None) and mm == rr

        if equal:
            setattr(record, r_field, None)
        else:
            setattr(modals, m_field, rr)
    elif mm is None:
        raise InvalidDataError('Unfillable field')


def dedup_coordinates(record: HasXY, modals: Modals, mx_field: str, my_field: str) -> None:
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
        elif record.x == mx:
            record.x = None
        else:
            setattr(modals, mx_field, record.x)

    if record.y is not None:
        my = getattr(modals, my_field)
        if modals.xy_relative:
            record.y -= my
            setattr(modals, my_field, record.y)
        elif record.y == my:
            record.y = None
        else:
            setattr(modals, my_field, record.y)

