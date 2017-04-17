# -*- coding: utf-8 -*-

'''


Created on  2017-04-12 16:13:05

@author: =
@copyright: 2016 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''

from setuptools import setup, find_packages

setup(
    name="seqdb",
    version="0.5.4",
    author='Aaron Kitzmiller <aaron_kitzmiller@harvard.edu>',
    author_email='aaron_kitzmiller@harvard.edu',
    description='A BioSQL sequence database loader',
    license='LICENSE.txt',
    url='http://pypi.python.org/pypi/seqdb/',
    packages=find_packages(),
    long_description='Harvard Annotator',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ],
    entry_points={
        'console_scripts': [
            'seqdb-loader = seqdb.loader:main'
        ]
    },
    install_requires=[
        'biopython>=1.69',
        'MySQL-python>=1.2.5',
    ],
)
