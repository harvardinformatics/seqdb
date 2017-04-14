# -*- coding: utf-8 -*-

'''
seqdb.connect Returns a BioSQL database

Created on  2017-04-13 15:40:55

@author: =
@copyright: 2016 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''
from BioSQL import BioSeqDatabase


def connect(**kwargs):
    '''
    Pass driver, user, passwd, host, database, and namespace 
    Returns a BioSQL db
    '''
    ns = kwargs.get('namespace','db')
    if 'namespace' in kwargs:
        del kwargs['namespace']

    server = BioSeqDatabase.open_database(**kwargs)
    create = kwargs.get('create')
    if create and ns not in server:
        server.new_database(ns)
        server.commit()

    db = server[ns]

    return db
