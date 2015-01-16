#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

##  This file is part of orm, The Object Relational Membrane Version 2.
##
##  Copyright 2002-2006 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file COPYING


"""
This datasouce module uses the Python-only, filesystem based SQL
backend called gadfly by Aaron Watters, currently maintained by
Richard Jones <richard@users.sf.net>. It is available at
U{http://gadfly.sourceforge.net}.
"""

__author__ = "Diedrich Vorberg <diedrich@tux4web.de>"
__version__ = "$Revision: 1.7 $"[11:-2]

# Python
from types import *
from sets import Set
import re

# orm
from t4.orm.datasource import datasource_base
from t4.orm.exceptions import *
from t4.orm.datatypes import common_serial

from t4 import sql
from t4.debug import sqllog, debug
from t4.utils import stupid_dict

import t4.orm.datasource

from gadfly import gadfly

class datasource(datasource_base):
    """
    An orm database adapter for gadfly.
    """
    no_fetchone = True
    
    def __init__(self, dbname="tmp", directory="/tmp",
                 encoding = "iso-8859-1"):
        """
        The default values will create a database called tmp in your
        /tmp directory. Gadfly will create a number of files called dbname.*
        there.
        """        
        t4.orm.datasource.datasource_base.__init__(self)

        self._conn = gadfly()
        self._conn.startup(dbname, directory)
        self.encoding = encoding

        self._update_cursor = self.cursor()

    def _from_params(params):
        database_name = params.get("dbname", "tmp")
        database_directory = params.get("directory", "/tmp")
        encoding = params.get("encoding", "iso-8859-1")

        return datasource(database_name, database_directory, encoding)

    from_params = staticmethod(_from_params)

    def backend_encoding(self):
        return self.encoding
                
    def insert(self, dbobj, dont_select=False):
        """
        The gadfly backend does not provide a mechanism to create unique
        keys for new rows. Values for the common_serial() datatype must be
        determined by the insert() function. It will query the maximum value
        of the id column and increment it.
        """
        # does the dbobj have a common_serial property?
        query_id = False
        for property in dbobj.__dbproperties__():
            if isinstance(property, common_serial):
                common_serial_property = property
                query_id = True
                break

        if query_id:
            query = "SELECT COUNT(*) FROM %s" % dbobj.__relation__
            cursor = self.execute(query)
            tpl = cursor.fetchone()
            count = tpl[0]

            if count == 0:
                new_id = 1
            else:            
                query = "SELECT MAX(id) FROM %s" % dbobj.__relation__
                cursor = self.execute(query)
                tpl = cursor.fetchone()
                max_id = tpl[0]

                new_id = max_id + 1
                
            common_serial_property.__set_from_result__(self, dbobj, new_id)

        datasource_base.insert(self, dbobj, dont_select)

    def select_one(self, dbclass, *clauses):
        """
        Gadfly doesn't support the LIMIT clause. 
        """
        result = self.select(dbclass, *clauses)
        result = list(result)
        
        if len(result) == 0:
            return None
        else:
            return result[0]

        
    def select_after_insert(self, dbobj):
        """
        The gadfly backend neither supports default values for columns
        not owns a mechanism to provide unique keys for new rows. So the
        select_after_insert() mechanism is useless.
        """
        pass
    
    def select_after_insert_where(self, dbobj):
        """
        See select_after_insert() above.
        """
        raise NotImplemented()

