#!/usr/bin/env python
# -*- coding: utf-8; -*-

#  This file is part of orm, The Object Relational Membrane Version 2.
#
#  Copyright 2010 by Diedrich Vorberg <diedrich@tux4web.de>
#
#  All Rights Reserved
#
#  For more Information on orm see the README file.
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#  I have added a copy of the GPL in the file gpl.txt.

# Python
import sys, re, os, os.path as op
from string import *

# Zope
import Globals
from OFS.SimpleItem import SimpleItem
from AccessControl import getSecurityManager, Unauthorized

from t4.orm.adapters.pgsql.datasource import datasource as pgsql_datasource
from t4.orm.datasource import datasource_base

class _pool:
    def __init__(self, t4orm_pool):
        self._t4orm_pool = t4orm_pool
        self.psycopg_version = "2.irgendwas"

    def __enter__(self):
        zope_connection = self._t4orm_pool.da()
        self._da = zope_connection()
        self._conn = self._da.getconn(False)
        _connections = self._t4orm_pool.connection_counters()
        
        key = id(self._conn)
        if _connections.has_key(key):
            _connections[key] += 1
        else:
            _connections[key] = 1
        
        self._encoding = "utf-8"
        self._insert_cursor = None

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        _connections = self._t4orm_pool.connection_counters()
        
        if exception_type is not None:
            # Does this have to be here?
            #print_exception(exception_type, exception_value,
            #                exception_traceback)
            
            try:                
                self._conn.rollback()
            except:
                pass

        key = id(self._conn)
        _connections[key] -= 1
        if _connections[key] == 0:
            self._da.putconn(self._conn)            
            self._conn = None

class _pgsql_pool(pgsql_datasource, _pool):
    def __init__(self, t4orm_pool):
        _pool.__init__(self, t4orm_pool)
        datasource_base.__init__(self)
        self.psycopg_version = "2.irgendwas"
            
manage_addt4orm_pool_form = Globals.DTMLFile(
    "skin_files/add_t4orm_pool_form", globals())

def manage_addt4orm_pool(self, id, title, da_id, REQUEST=None):
    """
    Add a new t4download_manager object with id *id*.
    """
    ob = t4orm_pool(id, title, da_id)
    self._setObject(id, ob)
    ob = self._getOb(id)

    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class t4orm_pool(SimpleItem):
    """
    A orm2 Wrapper for a Psycopg2 Connection
    """
    meta_type = "t4orm_pool"

    manage_editForm = Globals.DTMLFile("skin_files/edit_t4orm_pool", globals())
    manage_main = manage_editForm
    manage_editForm._setName("manage_editForm")
    
    manage_options=(
    (
        {"label": "Edit", "action": "manage_editForm",
         "help": ("t4orm_pool", "STX-Document_Edit.stx")},
        )
    + SimpleItem.manage_options
    )

    __ac_permissions__=(
        ("View management screens",
         ("manage_editForm", "manage", "manage_main",)),
        ("Manage Portal", ( ("manage_edit",) ),), )
    
    
    def __init__(self, id, title, da_id):
        self.id = id
        self.title = title
        self.da_id = da_id

    def getId(self):
        return self.id

    def manage_edit(self, title="", da_id="", REQUEST=None):
        """
        Modify this object.
        """
        self.title = title
        self.da_id = da_id

        if REQUEST is not None:
            return self.manage_main(self, REQUEST)

    def da(self):
        """
        Return the data connection used by this pool
        """
        try:
            return self.restrictedTraverse(self.da_id)
        except Unauthorized:
            return None

    def _pool(self):
        """
        Return a _pool object that fits the DA's backend.
        """
        da = self.da()
        if da is not None and da.meta_type == "Z Psycopg 2 Database Connection":
            return _pgsql_pool(self)
        else:
            raise TypeError("Don't know how to work with a " + repr(da))
        
    def pool(self):
        r = self.REQUEST
        key = "__%s_dbpool__" % self.getId()
        if not r.has_key(key):
            r[key] = self._pool()
        return r[key]

    __call__ = pool

    
    def connection_counters(self):
        if not hasattr(self, "_v_connection_counters"):
            self._v_connection_counters = {}

        return self._v_connection_counters

Globals.InitializeClass(t4orm_pool)
        
