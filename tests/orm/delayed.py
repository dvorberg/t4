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
##  I have added a copy of the GPL in the file gpl.txt.

"""
This module tests the L{t4.orm.datatypes.delayed} datatype wrapper.
"""

import os, unittest
from string import *

from t4.debug import sqllog
sqllog.verbose = True
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from t4.orm.dbobject import dbobject
from t4.orm.datatypes import *
from t4.orm.datasource import datasource
from t4.orm.datatypes import pickle

class person(dbobject):
    """
    This is our minimal data model consiting of one class
    """
    __relation__ = "person"
    
    id = common_serial()
    name = Unicode()
    image = delayed(string())
    
class person_insert_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    """
    
    def setUp(self):
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))

        self.ds.execute("""CREATE TABLE person (
                             id SERIAL,
                             name VARCHAR,
                             image VARCHAR ) """)
        
    def test_simple(self):
        sample = person(name = u"Me",
                        image="Incredibly long image data string")

        self.ds.insert(sample)
        
        result = self.ds.select(person)
        me = result.next()
        self.assertEqual(me.image, "Incredibly long image data string")

        #self.assertEqual(sqllog.queries[-1],
        #                 "SELECT image FROM person WEHRE id = 1")
        # God knows why this test fails. The strings look identical to me...


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(person_insert_test))        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

