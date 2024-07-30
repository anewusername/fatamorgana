"""
 fatamorgana

 fatamorgana is a python package for reading and writing to the
  OASIS layout format. The OASIS format ('.oas') is the successor to
  GDSII ('.gds') and boasts
     - Additional primitive shapes
     - Arbitrary-length integers and fractions
     - Extra ways to represent arrays of repeated shapes
     - Better support for arbitrary ASCII text data
     - More compact data storage format
     - Inline compression

 fatamorana is written in pure python and only optionally depends on
  numpy to speed up reading/writing.

 Dependencies:
    - Python 3.11 or later
    - numpy (optional, faster but no additional functionality)

 To get started, try:
 ```python3
    import fatamorgana
    help(fatamorgana.OasisLayout)
 ```
"""
from .main import (
    OasisLayout as OasisLayout,
    Cell as Cell,
    XName as XName,
    )
from .basic import (
    NString as NString,
    AString as AString,
    Validation as Validation,
    OffsetTable as OffsetTable,
    OffsetEntry as OffsetEntry,
    EOFError as EOFError,
    SignedError as SignedError,
    InvalidDataError as InvalidDataError,
    InvalidRecordError as InvalidRecordError,
    UnfilledModalError as UnfilledModalError,
    ReuseRepetition as ReuseRepetition,
    GridRepetition as GridRepetition,
    ArbitraryRepetition as ArbitraryRepetition,
    )


__author__ = 'Jan Petykiewicz'
__version__ = '0.13'
version = __version__
