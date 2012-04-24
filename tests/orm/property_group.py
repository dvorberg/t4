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
This module tests the L{orm2.datatypes.delayed} datatype wrapper.
"""

import os, unittest
from string import *

from orm2.debug import sqllog
sqllog.verbose = True
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource
from orm2.util.datatypes import pickle

class city(dbobject):
    """
    This is our minimal data model consiting of one class
    """
    id = common_serial()
    name = property_group(Unicode, ("de", "en",), "en")
    
class test(unittest.TestCase):
    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE city (
                             id INTEGER,
                             name_en VARCHAR,
                             name_de VARCHAR ) """)

        self.ds.execute("""INSERT INTO city
                                VALUES (1, 'Cologne', 'K�ln')""")
                        
        
    def test(self):
        result = self.ds.select(city)
        
        cologne = result.next()
        self.assertEqual(cologne.name["de"], u"K�ln")
        self.assertEqual(cologne.name["en"], u"Cologne")
        
        # Let's add a city
        munich = city(name={"de": u"M�nchen", "en": "Munich"})
        
        self.assertEqual(munich.name["de"], u"M�nchen")
        self.assertEqual(munich.name["en"], u"Munich")
        
        self.ds.insert(munich)

        # Check, if it's been inserted correctly
        result = self.ds.select(city, sql.order_by("id"))
        result = list(result)
        munich = result[-1]

        self.assertEqual(munich.name["de"], u"M�nchen")
        self.assertEqual(munich.name["en"], u"Munich")

        # Updates
        munich.name["de"] = u"Landeshauptstadt M�nchen"

        self.ds.commit(munich)
        self.assert_("UPDATE city SET name_de = 'Landeshauptstadt M�nchen' WHERE id = 2" in sqllog.queries)

        munich.name["en"] = u"State Capital Munich"

        # Set to dict
        cologne.name = {"de": u"Domstadt K�ln", "en":
                        u"City with a big Cathedral Cologne"}
                        # They are incredibly found of that thing ;-)
                       
        self.ds.commit(cologne)
        self.assert_("UPDATE city SET name_de = 'Domstadt K�ln', name_en = 'City with a big Cathedral Cologne' WHERE id = 1" in sqllog.queries)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(test))

        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

