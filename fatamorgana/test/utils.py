from io import BytesIO

from ..basic import write_uint, write_bstring, write_byte


MAGIC_BYTES = b'%SEMI-OASIS\r\n'


def _gen_header() -> bytes:
    buf = BytesIO()
    buf.write(MAGIC_BYTES)

    write_uint(buf, 1)           # START record
    write_bstring(buf, b'1.0')   # version
    write_uint(buf, 0)           # dbu real type: uint
    write_uint(buf, 1000)        # dbu value: 1000 per micron
    write_uint(buf, 0)           # offset table is present here
    for _ in range(6):
        write_uint(buf, 0)       # offset table (0: not strict)
        write_uint(buf, 0)       # offset table (0: no entry present)
    return buf.getvalue()


def _gen_footer() -> bytes:
    buf = BytesIO()

    write_uint(buf, 2)               # END record

    # 254-byte padding, (0-byte bstring with length 0;
    #  length is written as 0x80 0x80 ... 0x80 0x00)
    for _ in range(253):
        write_byte(buf, 0x80)
    write_byte(buf, 0)

    write_uint(buf, 0)               # no validation
    return buf.getvalue()


HEADER = _gen_header()
FOOTER = _gen_footer()

