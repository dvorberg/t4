#!/usr/bin/env python
# -*- coding: utf-8; mode: python; ispell-local-dictionary: "english" -*-

##  This file is part of the t4 Python module collection. 
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

__docformat__ = "epytext en"

"""
This module implements datatype classes that are specific to PostgreSQL.
"""

# Python
import sys, string, types
from uuid import UUID


# orm
from t4 import sql
from t4.orm.datatypes import *
from t4.validators import ip_address_validator

# Some regular expressions that may come in handy
point_re = re.compile(r"\(?\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)?")

class serial(integer):
    """
    Datatype class for PostgreSQL serial columns
    """
    def __init__(self, column=None, sequence_name=None):
        """
        @param sequence_name: The SQL identifyer of the sequence used for
           this serial. It defaults to the one created by the backend.
        """
        integer.__init__(self, column=column, title=None,
                         validators=(), has_default=True)
        self.sequence_name = sequence_name
                
    def __select_after_insert__(self, dbobj):
        # When we've already got a value, we can't be inserted again.
        
        if self.isset(dbobj):
            tpl = ( self.attribute_name,
                    self.dbclass.__name__,
                    repr(dbobj.__primary_key__), )
            
            raise ObjectAlreadyInserted(
                "Attribute %s of '%s' (%s) has already been set." % tpl)
        
        return True

    def __set__(self, dbobj, value):
        if self.isset(dbobj):
            raise ORMException( "A serial property is not mutable, " + \
                                "once it is set on object creation" )
        else:
            integer.__set__(self, dbobj, value)
    

class bytea_literal(sql.literal):
    def __init__(self, bindata):
        if type(bindata) != types.BufferType:
            self.bindata = buffer(bindata)
        else:
            self.bindata = bindata

    def __sql__(self, runner):
        if runner.ds.psycopg_version[0] == "1":
            from psycopg import Binary
            runner.params.append(Binary(str(self.bindata)))
        elif runner.ds.psycopg_version[0] == "2":
            runner.params.append(self.bindata)
        else:
            raise Exception("I don't know your psycopg")
            
        return "%s"

class bytea(datatype):
    python_class = str
    sql_literal_class = bytea_literal

blob = bytea

class inet(string):
    """
    The inet datatype is the same as string (IP address literals are
    essentially string literals), but it adds an extra validator.
    (That validator understands IPv4 addresses with optional (numeric)
    netmask. PostgreSQL understands IPv6 addresses. Support wouldn't 
    need more than an extensions of the re in validators.py
    """
    def __init__(self, column=None, title=None,
                 validators=(), has_default=False, null_on_empty=False):
        validators = list(validators)
        validators.insert(0, ip_address_validator())        
        string.__init__(self, column, title,
                        validators, has_default, null_on_empty)
        

def _pair_of_floats(p):
    if type(p) in ( types.ListType, types.TupleType, ):
        if len(p) != 2:
            raise ValueError("A point is represented by a pair of floats.")
        p = map(float, p)
    elif type(p) in ( types.StringType, types.UnicodeType, ):
        match = point_re.match(p)
        if match is None:
            raise ValueError(p)
        else:
            p = map(float, match.groups())
    else:
        raise TypeError("Expected pair of numbers or string representation")

    return tuple(p)
    
class point_literal(sql.literal):    
    def __init__(self, p):
        self._sql = "POINT( %f, %f )" % _pair_of_floats(p)

class point(datatype):
    """
    A PostgreSQL POINT is always represented as a pair (=tuple) of
    numbers in Python. The column will always return either None
    (=NULL) or a pair of floats. It will accept any pair of numbers
    and valid PostgreSQL POINT literals (i.e. the obvious string
    representation '(1.123,2.345)' ) as input.
    """
    sql_literal_class = point_literal

    def __convert__(self, value):
        if not value:
            return None
        else:
            return _pair_of_floats(value)

class uuid_literal(sql.literal):
    def __init__(self, u):
        if not isinstance(u, UUID):
            u = UUID(u)
        self._content = u

    def __sql__(self, runner):
        return "'" + str(self._content) + "'"
        

class uuid(datatype):
    """
    An interface to PostgreSQL's UUID type based on Python's
    uuid.UUID.
    """
    sql_literal_class = uuid_literal

    def __convert__(self, value):
        if value is None:
            return None
        else:
            if not isinstance(value, UUID):
                return UUID(value)
            else:
                return valuet4pg_catalog_model

class tsvector_data:
    def __hash__(self):
        return hash(repr(self.texts))
    
    def __init__(self, configuration_name, texts):
        self.configuration_name = configuration_name
        self.texts = texts
            
class to_tsvector_expression(sql.expression):
    def __init__(self, configuration_name, texts):
        """
        The dictionary texts goes { "<weight>": "<Text>", ... },
        <weight> being one of 'A', 'B', 'C', 'D' and <Text> the text
        to be indexed with that weight.
        """
        sql.expression.__init__(self)
        self._name = "ts_vector"

        for key in texts.keys():
            if strip(texts[key]) == "":
                del texts[key]
        
        for weight, text in texts.items():
            if type(text) != types.UnicodeType: text = unicode(text)
            self._append( ("setweight(",
                           "  to_tsvector(",
                           sql.string_literal(configuration_name), ", ",
                           sql.unicode_literal(text),
                           "), ", sql.string_literal(upper(weight)), ")",
                           "||",) )
        if len(self._parts) > 0:
            self._parts.pop() # Remove last ||
            

class tsvector(datatype):
    """
    ...both direction and magnitude!
    """
    def __set__(self, dbobj, value):
        if value is not None:            
            if not isinstance(value, tsvector_data):
                raise TypeError( "A tsvector dbattribute must be set to a "
                                 "tsvector_data instance.")
        
            self.check_dbobj(dbobj)
            setattr(dbobj, self.data_attribute_name(), value)
                         
    def sql_literal(self, dbobj):
        data = getattr(dbobj, self.data_attribute_name(), None)
        if data and data.texts:
            return to_tsvector_expression(data.configuration_name,
                                          data.texts)
        else:
            return "NULL"

    def __select_this_column__(self):
        return False

    def __select_after_insert__(self, dbobj):
        return False
