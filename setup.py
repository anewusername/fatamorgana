#!/usr/bin/env python3

from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

with open('fatamorgana/VERSION', 'r') as f:
    version = f.read().strip()

setup(name='fatamorgana',
      version=version,
      description='OASIS layout format parser and writer',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Jan Petykiewicz',
      author_email='anewusername@gmail.com',
      url='https://mpxd.net/code/jan/fatamorgana',
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
      classifiers=[
            'Programming Language :: Python :: 3',
            'Development Status :: 3 - Alpha',
            'Environment :: Other Environment',
            'Intended Audience :: Developers',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Manufacturing',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU Affero General Public License v3',
            'Operating System :: POSIX :: Linux',
            'Operating System :: Microsoft :: Windows',
            'Topic :: Scientific/Engineering',
            'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
      ],
      packages=find_packages(),
      package_data={
          'fatamorgana': ['VERSION',
                          'py.typed',
                          ],
      },
      install_requires=[
            'typing',
      ],
      extras_require={
          'numpy': ['numpy'],
      },
      )

