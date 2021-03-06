#!/usr/bin/env python

# -*- coding: utf-8 -*-

'''
seqdb loader script

Created on  2017-04-12 16:32:46

@author: Aaron Kitzmiller <aaron_kitzmiller@harvad.edu>
@copyright: 2017 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''

import sys, os, re, traceback
import logging
import random

from Bio import SeqIO
from BioSQL import Loader

from seqdb import connect
from seqdb import __version__ as version

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter


# Do a commit after COMMIT_COUNT records
COMMIT_COUNT = 100 

# If the error count goes above this number, processing stops
ERROR_COUNT = 100

logging.basicConfig(format='%(asctime)s: %(message)s',level=logging.ERROR)
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
            'name'      : 'SEQDB_LOADER_IGNORE_DUPLICATES',
            'switches'  : ['--ignore-duplicates'],
            'required'  : False,
            'help'      : 'Ignore errors due to duplicate entries.',
            'default'   : False,
            'action'    : 'store_true',
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
    parser.add_argument('-V', '--version', action='version', version=version)
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
    logger.setLevel(logging.getLevelName(args.SEQDB_LOADER_LOGLEVEL))
    logger.debug('Running in DEBUG')

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
    ignoredups      = args.SEQDB_LOADER_IGNORE_DUPLICATES

    # Setup sample if specified
    sampleids = samplesize = sampletotal = None
    if sample:
        if re.match(r'^\d+:\d+$',sample):
            samplesize, sampletotal = sample.split(':')
            samplesize = int(samplesize)
            sampletotal = int(sampletotal)
            logger.debug('Taking %d samples over %d total records.' % (samplesize,sampletotal))
        else:
            sampleids = sample.split(',')
            logger.debug('Selecting ids %s' % ' '.join(sampleids))
    
    # Connect to server; create BioSQL database if necessary
    db = connect(**connectargs)
    logger.debug('Connected to BioSQL database.')

    loader = Loader.DatabaseLoader(db.adaptor, db.dbid, False)

    recordcount = 0
    loadedcount = 0

    if samplesize is not None:
        nextsample = random.randint(0,int((sampletotal * 1.4) / samplesize))
        logger.debug('Next sample is %d' % nextsample)

    # Go through the file records
    errors = []
    with open(inputfile, 'r') as f:

        for record in SeqIO.parse(f,parser):
            logger.debug('Record %s parsed.' % str(record.id))
            if samplesize is not None:
                logger.debug('Next sample will be collected at %d' % nextsample)
            if not sample or \
                (sampleids is not None and record.id in sampleids) or \
                    (samplesize is not None and recordcount == nextsample):
                try:
                    loader.load_seqrecord(record)
                    loadedcount += 1
                except Exception as e:
                    if 'Duplicate entry' not in str(e) or not ignoredups:
                        errors.append(str(e))
                    logger.debug('Error loading %s: %s\n%s' % (record.id, str(e), traceback.format_exc()))

            if samplesize is not None and recordcount == nextsample:
                nextsample += random.randint(0,int((sampletotal * 1.4) / samplesize))
                logger.debug('Sample %s selected' % str(record.id))

            if loadedcount > 0 and loadedcount % COMMIT_COUNT == 0:
                db.adaptor.commit()
                logger.info('%d records committed.' % loadedcount)

            if len(errors) == ERROR_COUNT:
                db.adaptor.commit()  # Commit anything that is pending
                raise Exception('Processing aborted due to too many (%d) sequence errors:\n%s' % (ERROR_COUNT, '\n'.join(errors)))

            recordcount += 1

            if samplesize is not None and loadedcount == samplesize:
                db.adaptor.commit()
                break

    db.adaptor.commit()

    print '\n%d records loaded out of %d.\n' % (loadedcount,recordcount)
    if len(errors) > 0:
        print 'Errors:\n    %s' % '\n    '.join(errors)


if __name__ == "__main__":
    sys.exit(main())
