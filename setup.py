#!/usr/bin/env python3

from setuptools import setup, find_packages
import fatamorgana

with open('README.md', 'r') as f:
    long_description = f.read()

setup(name='fatamorgana',
      version=fatamorgana.version,
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
            'Programming Language :: Python',
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
            'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      packages=find_packages(),
      install_requires=[
            'typing',
      ],
      extras_require={
          'numpy': ['numpy'],
      },
      )

