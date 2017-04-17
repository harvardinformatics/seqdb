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
import subprocess
from seqdb import connect
from BioSQL import BioSeqDatabase

connectargs = {
    'driver'    : os.environ.get('SEQDB_LOADER_TEST_DRIVER'),
    'user'      : os.environ.get('SEQDB_LOADER_TEST_USER'),
    'passwd'    : os.environ.get('SEQDB_LOADER_TEST_PASSWORD'),
    'host'      : os.environ.get('SEQDB_LOADER_TEST_HOST'),
    'db'        : os.environ.get('SEQDB_LOADER_TEST_DATABASE'),
    'namespace' : os.environ.get('SEQDB_LOADER_TEST_NS','test'),
}

for k,v in connectargs.iteritems():
    if v is None:
        raise Exception('Connection argument %s is required.' % k)


loaderscript = os.path.join(os.path.dirname(os.path.dirname(__file__)),'loader.py')
testdatafile = os.path.join(os.path.dirname(__file__),'uniprot-test.xml')
testsampledatafile = os.path.join(os.path.dirname(__file__),'uniprot-sample.xml')


def runCmd(cmd):
    print 'Running %s' % cmd
    proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = proc.communicate()
    return (proc.returncode,stdout,stderr)


class Test(unittest.TestCase):

    def setUp(self):
        '''
        Clean up before hand
        '''
        self.resetTestDb()

    def tearDown(self):
        '''
        Clean up afterward
        '''
        self.resetTestDb()

    def resetTestDb(self):
        '''
        Remove all of the entries in the database for the namespace and create a new one.
        '''
        args = connectargs.copy()
        del args['namespace']
        server = BioSeqDatabase.open_database(**args)
        if connectargs['namespace'] in server:
            del server[connectargs['namespace']]

        server.new_database(connectargs['namespace'])
        server.commit()

    def testLoaderArgs(self):
        '''
        Make sure envs are applied
        '''

        args = [
            loaderscript,
            '-h'
        ]
        envs = {
            'SEQDB_LOADER_LOGLEVEL' : 'testloglevel',
            'SEQDB_LOADER_PARSER'   : 'testparser',
            'SEQDB_LOADER_USER'     : 'testuser',
            'SEQDB_LOADER_PASSWORD' : 'testpassword',
            'SEQDB_LOADER_HOST'     : 'testhost',
            'SEQDB_LOADER_DATABASE' : 'testdatabase',
            'SEQDB_LOADER_SAMPLE'   : 'testsample',
            'SEQDB_LOADER_NS'       : 'testns',
            'SEQDB_LOADER_DRIVER'   : 'testdriver',
        }

        # set env with k=v k=v, etc.
        cmdstr = ' '.join(['%s=%s' % (k,v) for k,v in envs.iteritems()])
        cmdstr += ' ' + ' '.join(args)
        returncode,stdout,stderr = runCmd(cmdstr)
        for k,v in envs.iteritems():
            self.assertTrue('[default: %s]' % v in stdout, 'Missing %s in stdout:\n%s\n%s' % (v,stdout,stderr))

    def testMissingFile(self):
        '''
        Fail if input file is not specified
        '''
        args = [
            loaderscript,
            '-p', 'uniprot-xml',
            '--user', connectargs['user'],
            '--password', connectargs['passwd'],
            '--host', connectargs['host'],
            '--database', connectargs['db'],
            '--namespace', connectargs['namespace'],
            '--driver', connectargs['driver'],
        ]
        cmdstr = ' '.join(args)
        returncode,stdout,stderr = runCmd(cmdstr)
        self.assertTrue(returncode != 0,'Command succeeded? %s' % cmdstr)
        self.assertTrue('too few arguments' in stderr, 'Incorrect stderr: %s' % stderr)

    def testSimpleLoad(self):
        '''
        Load the test file successfully
        '''
        args = [
            loaderscript,
            '-p', 'uniprot-xml',
            '--user', connectargs['user'],
            '--password', connectargs['passwd'],
            '--host', connectargs['host'],
            '--database', connectargs['db'],
            '--namespace', connectargs['namespace'],
            '--driver', connectargs['driver'],
            testdatafile,
        ]
        cmdstr = ' '.join(args)
        returncode,stdout,stderr = runCmd(cmdstr)
        self.assertTrue(returncode == 0,'Command %s failed:\n%s' % (cmdstr,stderr))
        self.assertTrue('2 records loaded out of 2' in stdout, 'Incorrect output message %s\n%s' % (stdout,stderr))

        # Did they get loaded?
        db = connect(**connectargs)
        seq = db.lookup(accession='P12345')
        self.assertTrue(seq.name == 'AATM_RABIT','Wrong name %s' % str(seq))
        self.assertTrue(seq.annotations['sequence_checksum'][0] == '12F54284974D27A5','Wrong checksum %s' % str(seq.annotations))

        seq = db.lookup(accession='P12346')
        self.assertTrue(seq.name == 'TRFE_RAT','Wrong name %s' % str(seq))
        self.assertTrue(seq.annotations['sequence_checksum'][0] == 'B91ABB41CA447194','Wrong checksum %s' % str(seq.annotations))

    def testDuplicateLoad(self):
        '''
        Load the test file successfully, try a second time
        '''
        args = [
            loaderscript,
            '-p', 'uniprot-xml',
            '--user', connectargs['user'],
            '--password', connectargs['passwd'],
            '--host', connectargs['host'],
            '--database', connectargs['db'],
            '--namespace', connectargs['namespace'],
            '--driver', connectargs['driver'],
            testdatafile,
        ]
        cmdstr = ' '.join(args)
        returncode,stdout,stderr = runCmd(cmdstr)
        self.assertTrue(returncode == 0,'Command %s failed:\n%s' % (cmdstr,stderr))
        self.assertTrue('2 records loaded out of 2' in stdout, 'Incorrect output message %s\n%s' % (stdout,stderr))

        returncode,stdout,stderr = runCmd(cmdstr)
        self.assertTrue(returncode == 0,'Command %s failed:\n%s' % (cmdstr,stderr))
        self.assertTrue('0 records loaded out of 2' in stdout, 'Incorrect output message %s\n%s' % (stdout,stderr))
        self.assertTrue('(1062, "Duplicate entry \'P12345' in stdout, 'Incorrect output message %s\n%s' % (stdout,stderr))
        self.assertTrue('(1062, "Duplicate entry \'P12346' in stdout, 'Incorrect output message %s\n%s' % (stdout,stderr))

    def testSampleById(self):
        '''
        Make sure sample by id works
        '''
        args = [
            loaderscript,
            '-p', 'uniprot-xml',
            '--user', connectargs['user'],
            '--password', connectargs['passwd'],
            '--host', connectargs['host'],
            '--database', connectargs['db'],
            '--namespace', connectargs['namespace'],
            '--driver', connectargs['driver'],
            '--sample', 'P12345',
            testdatafile,
        ]
        cmdstr = ' '.join(args)
        returncode,stdout,stderr = runCmd(cmdstr)
        self.assertTrue(returncode == 0,'Command %s failed:\n%s' % (cmdstr,stderr))
        self.assertTrue('1 records loaded out of 2' in stdout, 'Incorrect output message %s\n%s' % (stdout,stderr))

        # Did they get loaded?
        db = connect(**connectargs)
        seq = db.lookup(accession='P12345')
        self.assertTrue(seq.name == 'AATM_RABIT','Wrong name %s' % str(seq))
        self.assertTrue(seq.annotations['sequence_checksum'][0] == '12F54284974D27A5','Wrong checksum %s' % str(seq.annotations))

        try:
            seq = db.lookup(accession='P12346')
            self.assertTrue(False,'For some reason P12346 got loaded.')
        except Exception as e:
            self.assertTrue("Cannot find accession 'P12346'" in str(e), 'Incorrect exception string %s' % str(e))

    def testSampleSize(self):
        '''
        Test the <samplesize>:<total> version of sampling
        '''
        args = [
            loaderscript,
            '-p', 'uniprot-xml',
            '--user', connectargs['user'],
            '--password', connectargs['passwd'],
            '--host', connectargs['host'],
            '--database', connectargs['db'],
            '--namespace', connectargs['namespace'],
            '--driver', connectargs['driver'],
            '--sample', '3:30',
            testsampledatafile,
        ]
        cmdstr = ' '.join(args)
        returncode,stdout,stderr = runCmd(cmdstr)
        self.assertTrue(returncode == 0,'Command %s failed:\n%s' % (cmdstr,stderr))
        self.assertTrue('3 records loaded out of' in stdout, 'Incorrect output message %s\n%s' % (stdout,stderr))
