#!/usr/bin/env python

# -*- coding: utf-8 -*-

'''
seqdb loader script

Created on  2017-04-12 16:32:46

@author: Aaron Kitzmiller <aaron_kitzmiller@harvad.edu>
@copyright: 2017 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''

import sys, os, re
import logging
import random

from Bio import SeqIO
from BioSQL import Loader

from seqdb import connect

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

# Do a commit after COMMIT_COUNT records
COMMIT_COUNT = 100 

# If the error count goes above this number, processing stops
ERROR_COUNT = 100

logger = logging.getLogger()


def initArgs():
    '''
    Setup arguments with parameterdef, check envs, parse commandline, return args
    '''

    parameterdefs = [
        {
            'name'      : 'SEQDB_LOADER_LOGLEVEL',
            'switches'  : ['--loglevel'],
            'required'  : False,
            'help'      : 'Log level (e.g. DEBUG, INFO)',
            'default'   : 'ERROR',
        },
        {
            'name'      : 'SEQDB_LOADER_PARSER',
            'switches'  : ['-p','--parser'],
            'required'  : True,
            'help'      : 'The BioPython SeqIO parser name',            
        },
        {
            'name'      : 'SEQDB_LOADER_USER',
            'switches'  : ['--user'],
            'required'  : False,
            'help'      : 'BioSQL database user',
        },
        {
            'name'      : 'SEQDB_LOADER_PASSWORD',
            'switches'  : ['--password'],
            'required'  : False,
            'help'      : 'BioSQL database password',
        },
        {
            'name'      : 'SEQDB_LOADER_HOST',
            'switches'  : ['--host'],
            'required'  : False,
            'help'      : 'BioSQL database hostname',
        },
        {
            'name'      : 'SEQDB_LOADER_DATABASE',
            'switches'  : ['--database'],
            'required'  : False,
            'help'      : 'BioSQL database name',
        },
        {
            'name'      : 'SEQDB_LOADER_SAMPLE',
            'switches'  : ['--sample'],
            'required'  : False,
            'help'      : '''Sample of data from the input file.  Takes one of two forms: 
either n:N where n is the number of samples and N is the total (10:100000)
or a comma-separated list of identifiers (P12345,P98765)
            ''',
        },
        {
            'name'      : 'SEQDB_LOADER_NS',
            'switches'  : ['--namespace'],
            'required'  : False,
            'help'      : 'BioSQL namespace',
            'default'   : 'db',
        },
        {
            'name'      : 'SEQDB_LOADER_DRIVER',
            'switches'  : ['--driver'],
            'required'  : False,
            'help'      : 'BioSQL database driver',
            'default'   : 'MySQLdb',
        }
    ]
        
    # Check for environment variable values
    # Set to 'default' if they are found
    for parameterdef in parameterdefs:
        if os.environ.get(parameterdef['name'],None) is not None:
            parameterdef['default'] = os.environ.get(parameterdef['name'])
            
    # Setup argument parser
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version='1.0')
    parser.add_argument('FILE',help='Sequence data file')
    
    # Use the parameterdefs for the ArgumentParser
    for parameterdef in parameterdefs:
        switches = parameterdef.pop('switches')
        if not isinstance(switches, list):
            switches = [switches]
            
        # Gotta take it off for add_argument
        name = parameterdef.pop('name')
        parameterdef['dest'] = name
        if 'default' in parameterdef:
            parameterdef['help'] += '  [default: %s]' % parameterdef['default']
        parser.add_argument(*switches,**parameterdef)
        
        # Gotta put it back on for later
        parameterdef['name'] = name
        
    args = parser.parse_args()
    return args


def main():
    args = initArgs()

    parser          = args.SEQDB_LOADER_PARSER
    inputfile       = args.FILE
    connectargs     = {
        'driver'    : args.SEQDB_LOADER_DRIVER,
        'user'      : args.SEQDB_LOADER_USER,
        'passwd'    : args.SEQDB_LOADER_PASSWORD,
        'host'      : args.SEQDB_LOADER_HOST,
        'db'        : args.SEQDB_LOADER_DATABASE,
        'namespace' : args.SEQDB_LOADER_NS,
    }
    sample          = args.SEQDB_LOADER_SAMPLE

    # Setup sample if specified
    sampleids = samplesize = sampletotal = None
    if sample:
        if re.match(r'^\d+:\d+$',sample):
            samplesize, sampletotal = sample.split(':')
            samplesize = int(samplesize)
            sampletotal = int(sampletotal)
        else:
            sampleids = sample.split(',')
    
    # Connect to server; create BioSQL database if necessary
    db = connect(**connectargs)
    loader = Loader.DatabaseLoader(db.adaptor, db.dbid, False)

    recordcount = 0
    loadedcount = 0

    if samplesize is not None:
        nextsample = random.randint(0,int(sampletotal / samplesize))

    # Go through the file records
    errors = []
    with open(inputfile, 'r') as f:

        for record in SeqIO.parse(f,parser):
            logger.debug('Record %s parsed.' % str(record.id))
            if not sample or \
                (sampleids is not None and record.id in sampleids) or \
                    (samplesize is not None and recordcount == nextsample):
                try:
                    loader.load_seqrecord(record)
                    recordcount += 1
                except Exception as e:
                    errors.append(str(e))

            if samplesize is not None and recordcount == nextsample:
                nextsample += random.randint(0,int(sampletotal / samplesize))
                logger.debug('Sample %s selected' % str(record.id))

            if recordcount % COMMIT_COUNT == 0:
                db.adaptor.commit()
                logger.info('%d records loaded.' % recordcount)

            if len(errors) == ERROR_COUNT:
                db.adaptor.commit()  # Commit anything that is pending
                raise Exception('Processing aborted due to too many (%d) sequence errors:\n%s' % (ERROR_COUNT, '\n'.join(errors)))

            loadedcount += 1

    db.adaptor.commit()

    print '\n%d records loaded out of %d.\n' % (recordcount,loadedcount)
    if len(errors) > 0:
        print 'Errors:\n    %s' % '\n    '.join(errors)


if __name__ == "__main__":
    sys.exit(main())
