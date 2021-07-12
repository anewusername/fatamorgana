#!/usr/bin/env python3

from setuptools import setup, find_packages


with open('README.md', 'r') as f:
    long_description = f.read()

with open('fatamorgana/VERSION.py', 'rt') as f:
    version = f.readlines()[2].strip()

setup(name='fatamorgana',
      version=version,
      description='OASIS layout format parser and writer',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Jan Petykiewicz',
      author_email='jan@mpxd.net',
      url='https://mpxd.net/code/jan/fatamorgana',
      packages=find_packages(),
      package_data={
          'fatamorgana': ['py.typed'],
      },
      install_requires=[
            'typing',
      ],
      extras_require={
          'numpy': ['numpy'],
      },
      classifiers=[
            'Programming Language :: Python :: 3',
            'Development Status :: 3 - Alpha',
            'Environment :: Other Environment',
            'Intended Audience :: Developers',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Manufacturing',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU Affero General Public License v3',
            'Topic :: Scientific/Engineering',
            'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
      ],
      keywords=[
          'OASIS',
          'layout',
          'design',
          'CAD',
          'EDA',
          'oas',
          'electronics',
          'open',
          'artwork',
          'interchange',
          'standard',
          'mask',
          'pattern',
          'IC',
          'geometry',
          'geometric',
          'polygon',
          'gds',
      ],
      )

