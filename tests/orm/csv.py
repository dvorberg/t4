#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

##  This file is part of orm, The Object Relational Membrane Version 2.
##
##  Copyright 2002-2009 by Diedrich Vorberg <diedrich@tux4web.de>
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

"""

import os, unittest, struct, socket
from types import *

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource
from orm2 import sql
from orm2.debug import sqllog
#sqllog.verbose = False

from insert_and_select import same_data

class user(dbobject):
    """
    From the insert.py test...
    """
    __relation__ = sql.relation("users")
    id = common_serial()
    login = Unicode()
    roles = csv(Unicode())
    
class user_insert_and_select_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    The gadfly adapter doesn't know NULL values and Unicode screws it up.
    So the jucyer tests are reserved for the 'real' databases.
    """
    data = ( ( "diedrich", ("member", "reviewer", "manager",),), )
    
    def connect_and_create_table(self):
        self.ds = datasource("adapter=pgsql")

        self.ds.execute("""CREATE TABLE users (
                             id SERIAL,
                             login TEXT,
                             roles TEXT)""")
    
    def setUp(self):
        self.connect_and_create_table()

        for login, roles in self.data:
            dbobj = user( login = login, roles = roles )
            self.ds.insert(dbobj)

    def tearDown(self):
        self.ds.execute("DROP TABLE users")

    def test(self):
        self.select_all()
        
    def select_all(self):
        all = self.ds.select(user)

        tpls = []
        for dbobj in all:
            tpls.append( (dbobj.login, dbobj.roles,) )

        self.assert_(same_data(self.data, tpls))

if __name__ == '__main__':

    # IP Number conversion does not seem to work with Python 2.4
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(user_insert_and_select_test))
        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

