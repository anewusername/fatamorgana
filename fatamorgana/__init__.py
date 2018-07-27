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
    - Python 3.5 or later
    - numpy (optional, no additional functionality)
"""
from .main import OasisLayout, Cell, XName
from .basic import NString, AString, Validation, OffsetTable, OffsetEntry, \
        EOFError, SignedError, InvalidDataError, InvalidRecordError


__author__ = 'Jan Petykiewicz'

version = '0.4'
