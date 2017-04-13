# -*- coding: utf-8 -*-

'''
Test the loader

Created on  2017-04-13 15:35:02

@author: =
@copyright: 2016 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''

import unittest
import os
from seqdb import connect

connectargs = {
    'driver'    : os.environ.get('SEQDB_LOADER_TEST_DRIVER'),
    'user'      : os.environ.get('SEQDB_LOADER_TEST_USER'),
    'passwd'    : os.environ.get('SEQDB_LOADER_TEST_PASSWORD'),
    'host'      : os.environ.get('SEQDB_LOADER_TEST_HOST'),
    'db'        : os.environ.get('SEQDB_LOADER_TEST_DATABASE'),
    'namespace' : os.environ.get('SEQDB_LOADER_TEST_NS'),
}


# BioSQL namespace
NAMESPACE = 'test'

class Test(unittest.TestCase):


    def setUp(self):
        '''
        '''
        pass

    def tearDown(self):
        '''
        '''
        pass

    def removeEntries(self):
        '''
        Remove all of the entries in the database
        '''
        pass


