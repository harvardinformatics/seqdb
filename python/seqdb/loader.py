#!/usr/bin/env python

# -*- coding: utf-8 -*-

'''
seqdb loader script

Created on  2017-04-12 16:32:46

@author: Aaron Kitzmiller <aaron_kitzmiller@harvad.edu>
@copyright: 2017 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''

import sys,os,traceback

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

import logging
logger = logging.getLogger()


def main():
    #
    # Initialize the configuration with defaults and user config file
    #
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
        if os.environ.get(parameterdef['name'],None) != None:
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
    print args         
        
if __name__ == "__main__":
    sys.exit(main())
