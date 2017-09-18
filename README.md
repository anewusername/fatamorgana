# fatamorgana 

**fatamorgana** is a Python package for reading and writing OASIS format layout files.

**Homepage:** https://mpxd.net/gogs/jan/fatamorgana

**Capabilities:**
* This package is a work-in-progress and is largely untested -- it works for
    the tasks I usually use it for, but I can't guarantee I've even 
    tried the features you happen to use! Use at your own risk!
* Interfaces and datastructures are subject to change!
* That said the following work for me:
    - polygons
    - layer info
    - cell names
    - compressed blocks
    - basic property I/O


## Installation

**Dependencies:**
* python 3.5 or newer
* (optional) numpy


Install with pip from PyPi (preferred):
```bash
pip install fatamorgana
```

Install directly from git repository:
```bash
pip install git+https://mpxd.net/gogs/jan/fatamorgana.git@release
```

## Documentation
Most functions and classes are documented inline.

To read the inline help,
```python3
import fatamorgana
help(fatamorgana.OasisLayout)
```
The documentation is currently very sparse and I expect to improve it whenever possible!


## Examples

Read an OASIS file and write it back out:
```python3
    import fatamorgana

    with open('test.oas', 'rb') as f:
        layout = fatamorgana.OasisLayout.read(f)
    
    with open('test_write.oas', 'wb') as f:
        layout.write(f)
```
