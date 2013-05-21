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
##  I have added a copy of the GPL in the file COPYING

__docformat__ = "epytext en"

"""
This module defines one class, L{dbobject}, which is the base class
for all objects orm retrieves from or stores in the database.
"""

from string import *
from types import *
import copy

from t4 import sql
import keys
from datasource import datasource_base
from exceptions import *
from datatypes import datatype

class result:
    """
    This is the base class for all results. A result is a collection of one
    kind of dbobjects that have been retrieved from the database. This class
    will emulate a sequence but also has a next() method like a generator (so
    I don't have to change all that code that assumes a result to be a
    generator). The result class also has two methods to determine the
    result's length by querying the database. If you need to traverse over a
    result more than once, you must cast it into a list (and by that copying
    all dbobjects to the client's memory).

    The result class needs to deal with datasources that have an attribute
    called no_fetchone set, that makes this class use the cursor.fetchall()
    method (most notable for the gadfly adapter).
    """

    def __init__(self, ds, dbclass, select):
        """
        @param ds: Datasource object
        @param dbclass: dbclass object of whoes instances this result will be
        @param select: orm2.sql.select instance of the query
        """
        self.ds = ds
        self.dbclass = dbclass

        if not isinstance(select, sql.select):
            raise TypeError("result can only work on sql.select instances!")

        self.select = select
        
        self.columns = dbclass.__select_columns__()
        self.cursor = ds.execute(select)

        if getattr(self.ds, "no_fetchone", False):
            self.rows = self.cursor.fetchall()
            self.rows.reverse()            

    def __iter__(self):
        return self

    def next(self):
        if hasattr(self, "rows"):
            if len(self.rows) == 0:
                tpl = None
            else:
                tpl = self.rows.pop()
        else:
            tpl = self.cursor.fetchone()

        if tpl is None:
            raise StopIteration
        else:
            return self.dbclass.__from_result__(
                self.ds, dict(zip(self.columns, tpl)))

    fetchone = next

    def __len__(self):
        ret = self.cursor.rowcount
        if ret == -1: raise Exception("No query has been run, yet.")        
        return ret

    def empty(self):
        return len(self) == 0
    
    def count(self):
        """
        This is a helper function that will perform a query as

           SELECT COUNT(*) ...

        appropriate to determine the number of rows in this result.
        This will remove all clauses of the original select except the
        WHERE clause.

        This can't be called __len__(), because then it is used by
        list() and yields a superflous SELECT query.
        """
        count_select = copy.deepcopy(self.select)
        count_select.clauses = \
                filter(lambda clause: isinstance(clause, sql.where),
                       count_select.clauses)
        count_select.columns = sql.expression("COUNT(*)")
        return int(self.ds.query_one(count_select))

    count_all = count


    
class dbobject(object):
    """
    Base class for all database aware classes.

    It contains a number of helper methods which are called like this:
    __help__(). You may safely add db-aware properties, regular properties
    and methods.

    @cvar __primary_key__:  The primary key must be either
      - a keys.primary_key instance
      - a tuple of strings indicating attribute (not column!) names of this
        class that form a multi column primary key
      - a simple string indicating the attribute that manages the primary
        key column of this dbclass
      - None if the class does not have a primary key (which makes it
        impossible to update rows by updating an instance's attributes
        through orm)

    @cvar __result__: This attribute must be a class which inherits
       from result. It is used to represent results, sets of
       this dbclass retrieved from the database. It will returned for all
       calls to the datasource.run_select() method (which takes care of
       all methods'select' in their names, except where explicitly noted.

    @cvar __relation__: Name of the relation this dbclass' values are
       stored in. Defaults to the class' name. May be set to a string or an
       sql.relation instance.

    @cvar __schema__: String containing the name of the schema this dbclass'
      relatin resides in.    
    """

    __primary_key__ = "id"
    __result__ = result
    
    class __metaclass__(type):
        def __new__(cls, name, bases, dict):
            ret = type.__new__(cls, name, bases, dict)
            
            if name != "dbobject":
                if not hasattr(ret, "__relation__") or \
                       getattr(ret.__relation__, "__autocreated__", False):
                    # __relation__ which are set by this procedure
                    # are overwritten with one that uses the current class'
                    # name, considering the __schema__ class variable.
                    schema = getattr(ret, "__schema__", None)
                    ret.__relation__ = sql.relation(name, schema)
                    ret.__relation__.__autocreated__ = True
                elif type(ret.__relation__) == StringType:
                    schema = getattr(ret, "__schema__", None)
                    ret.__relation__ = sql.relation(ret.__relation__, schema)
                elif type(ret.__relation__) == UnicodeType:
                    raise TypeError("Unicode is not allowed as SQL identifyer")
                elif isinstance(ret.__relation__, sql.relation):
                    pass
                else:
                    msg = "Relation name must be a string or an" + \
                          "sql.relation() instance, not %s (%s)"
                    raise TypeError(msg % ( repr(type(ret.__relation__)),
                                            repr(ret.__relation__),) )

                # Initialize the dbproperties                
                for attr_name, property in dict.items():
                    if isinstance(property, datatype):
                        property.__init_dbclass__(ret, attr_name)

                # Add (=inherit) db-properties from our parent classes
                for base in bases:
                    for attr_name, property in base.__dict__.items():
                        if isinstance(property, (datatype,)):
                            property_cpy = copy.copy(property)
                            if hasattr(property_cpy, "__init_dbclass__"):
                                property_cpy.__init_dbclass__(ret, attr_name)
                            setattr(ret, attr_name, property_cpy)

            return ret

    
    def __init__(self, **kw):
        """
        Construct a dbobj from key word arguments. Example::

           me = person(firstname='Diedrich', lastname='Vorberg')

        firstname and lastname are dbproperties. The reserved parameter
        __ds allows you to pass a datasource to objects that are not
        inserted yet and might need a ds to construct stuff.
        """
        self.__changed_columns__ = {}
        
        if kw.has_key("__ds"):
            __ds = kw["__ds"]
            del kw["__ds"]

            if not isinstance(__ds, datasource_base):
                raise TypeError("__ds must be a subclass of "+\
                                "orm2.datasource.datasource_base")
            
        else:
            __ds = None
        
        self._ds = __ds
        self._is_stored = False

        for name, prop in self.__class__.__dict__.iteritems():
            if isinstance(prop, datatype) and not hasattr(prop, "dbclass"):
                prop.__init_dbclass__(self.__class__, name)

        self.__update_from_dict__(kw)
        
        if self.__primary_key__ is not None:
            self.__primary_key__ = keys.primary_key(self)


    def __register_change__(self, dbproperty):
        if self.__is_stored__():
            self._ds.__register_change_of__(self)
            self.__changed_columns__[dbproperty.column] = dbproperty
            
    def __perform_updates__(self, update_cursor):
        if len(self.__changed_columns__) == 0:
            return
        else:
            info = {}
            for column, datatype in self.__changed_columns__.items():
                if datatype.isexpression(self):
                    info[column] = datatype.expression(self)
                else:
                    info[column] = datatype.sql_literal(self)

            statement = sql.update(self.__relation__,
                                   self.__primary_key__.where(),
                                   info)
                
            update_cursor.execute(statement)

            # Clear the list of changed columns
            self.__changed_columns__.clear()


    def __from_result__(cls, ds, info):
        """
        This constructor is called by L{datasource.datasource_base}
        when an object is created using a row retreived from the RDBMS.
        
        @param ds: datasource we are created by (see select() method)
        @param info: dictionary as { 'column_name': <data> }        
        """
        self = cls(__ds=ds)
        for property in cls.__dbproperties__():
            if info.has_key(property.column):
                property.__set_from_result__(ds, self, info[property.column])

        self._ds = ds
        self._is_stored = True

        return self

    __from_result__ = classmethod(__from_result__)

    def __insert__(self, ds):
        """
        This method is called by datasource.insert() after the insert
        query has been performed. It sets the dbobj's _ds attribute.
        
        @param ds: datasource that just inserted us        
        """
        self._ds = ds
        self._is_stored = True
        self.__changed_columns__ = {}
    
    def __ds__(self):
        """
        Return this dbobject's datasource (the one it is stored in).
        """
        if not hasattr(self, "_ds"):
            raise ObjectMustBeInserted("...before you use __ds__()")
        
        return self._ds

    def __commit__(self):
        """
        Commit the ds this dbobject belongs to.
        """
        self.__ds__().commit()

    def __is_stored__(self):
        """
        @returns: Wheather this dbobj has been stored in the database already
           or retrieved from it
        """
        return self._is_stored

    def __dbproperties__(cls):
        """
        This is a generator over all the dbproperties in this dbobject.
        """
        ret = filter(lambda prop: isinstance(prop, datatype),
                     cls.__dict__.values())
        ret.sort()
        return ret
                
    __dbproperties__ = classmethod(__dbproperties__)


    def __dbproperty__(cls, name=None):
        """
        Return a dbproperty by its name. Raise exceptions if
        
          - there is no property by that name
          - it's not a dbproperty

        name defaults to the dbclass' primary key.  
        """
        if name is None:
            if cls.__primary_key__ is None:
                raise NoPrimaryKey()
            else:
                name = cls.__primary_key__

        try:
            property = cls.__dict__[name]
        except KeyError:
            tpl =  ( repr(name), cls.__name__, )
            raise AttributeError("No such attribute: %s (in class %s)" % tpl)

        if not isinstance(property, datatype):
            raise NoDbPropertyByThatName(name + " is not a orm2 datatype!")

        return property

    __dbproperty__ = classmethod(__dbproperty__)

    def __has_dbproperty__(cls, name):
        """
        Return whether this dbclass has a property named `name`.
        """
        try:
            cls.__dbproperty__(name)
            return True
        except NoDbPropertyByThatName:
            return False
        except AttributeError:
            return False


    __has_dbproperty__ = classmethod(__has_dbproperty__)


    def __select_columns__(cls, full_column_names=False):
        """
        A list of columns to select from the relation to construct one
        of these. 
        """
        columns = []
        for property in cls.__dbproperties__():
            if property.__select_this_column__():
                # I'm wondering if this is smart:
                # datatypes.expression sets its column attribute to an
                # sql.expression object. This makes joins work, but
                # creates a danger of ambiguities. 
                if full_column_names and \
                        not isinstance(property.column, sql.expression):
                    new = sql.column(property.column.name(),
                                     cls.__relation__,
                                     property.column.quote())
                else:
                    new = property.column

                if not new in columns:
                    columns.append(new)
                
        return columns
    
    __select_columns__ = classmethod(__select_columns__)

        
    def __repr__(self):
        """
        Return a human readable (more or less) representation of this
        dbobject.
        """
        ret = []

        ret.append("pyid=" + str(id(self)))
        
        #if self.oid():
        #    ret.append("oid=%i" % self.oid())
        #else:
        #    ret.append("oid=NULL")

        attribute_names = []
        for name, value in self.__dict__.items():
            if isinstance(value, datatype):
                attribute_names.append(name)
                
        for a in attribute_names:
            b = a + "="

            try:
                val = getattr(self, a)
                
                #if not isinstance(val, relationships.relationshipColumn):
                #    b += repr(val.get())
                #else:
                b += repr(val)
            except AttributeError:
                b += "<not set>"

            ret.append(b)
            
        return "<" + self.__class__.__name__ + " (" + \
               join(ret, " ") + ")>"


    def __eq__(self, other):
        """
        Two dbobjects are considered equal, if they have the same dbclass
        and the same primary key. B{This method does not check any
        attributes!} 
        """
        # Shortcut for the very same Python object:
        if id(self) == id(other):
            return True
        
        # Can't be equal.
        if other.__class__ != self.__class__:
            return False
        
        if self.__primary_key__ is None or other.__primary_key__ is None:
            raise ValueError("Can't check equality on dbclasses that "
                             "don't have a primary key")

        if not self.__primary_key__.isset() or \
           not other.__primary_key__.isset():
            raise ValueError("Can't check equality on a dbobj whoes "
                             "primary key is not yet set")
            
        return self.__primary_key__.__eq__(other.__primary_key__)

    def __ne__(self, other):
        """
        Same as L{__eq__}, just the other way 'round ;-)
        """
        return (not self == other)

    def __widget_specs__(self, module_name):
        """
        Return a list of all widget_specs for the module named module_name.
        """
        ret = []
        for property in self.__dbproperties__():
            for spec in property.widget_specs():
                if spec.belongs_to(module_name):
                    ret.append(spec)

        ret.sort()
        return ret

    def __delete__(self):
        cmd = sql.delete(self.__relation__,
                         self.__primary_key__.where())
        self.__ds__().execute(cmd)

    def __update_from_dict__(self, kw):
        for name, value in kw.items():
            if self.__class__.__dict__.has_key(name):
                self.__class__.__dict__[name].__set__(self, value)
            else:
                raise NoSuchAttributeOrColumn(name)
        
class zope_dbobject(dbobject):
    __allow_access_to_unprotected_subobjects__ = True

