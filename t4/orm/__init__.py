#!/usr/bin/env python
# -*- coding: utf-8; mode: python; ispell-local-dictionary: "english" -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2002-2011 by Diedrich Vorberg <diedrich@tux4web.de>
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
Welcome to The Object Relational Membrane (v.2)
===============================================


 To get started with orm you might want to look at the
 L{t4.orm.datatypes} module first to find out what datatypes are there
 to populate your dbclasses with. Knowing a little SQL this should be
 pretty much self-explaining. Next, check out the
 L{t4.orm.relationships} module to see how you can interrelate your
 classes. The L{t4.orm.dbobject.dbobject} class has a couple of
 interesting properties, though you might not want to fiddle with most
 of it at the beginning. The L{t4.orm.adapters} module contains code for
 interfacing with the RDBMS, though the L{t4.orm.datasource.datasource}
 may likely be everything you need.

 To further study the intricacies of orm you might want to have a look
 at the L{t4.orm.sql} module, which handles SQL code generation and is
 going to be very helpful in writing advanced code. Consider using and/or
 interfacing with L{t4.orm.debug} to help you track down my and your
 errors. L{t4.orm.util} contains miscellaneous classes and functions
 that might come in handy.

 The L{t4.orm.ui} module is practically not there, yet, but you might be
 interested anyway.

 Any ideas, suggestion or criticism is always welcome!

 Diedrich Vorberg <U{diedrich@tux4web.de}>
 
"""

