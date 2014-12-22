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
These classes are very simmilar to primitives in that they manage two
relations. The child relation however is not represented by a dbclass,
but only by a primitive type. 
"""

# Python
import sys
from types import *

# t4
from t4 import sql
from dbobject import dbobject
from datatypes import datatype
from exceptions import *
import keys

class _container(datatype):
    def __init__(self, child_relation, child_column,
                 child_key=None, title=None):
        """
        @param child_relation: sql.relation object or string, indicating
           the name of the dependent relation.
        @param child_column: It's datatype (datatype object). The datatype's
           column parameter may be used as well as teh validators. Title and
           has_default will be ignored. The column name defaults to the
           container's attribute_name in the parent dbclass.
        @param child_key: A string indicating the column in the child
           relation that is used in the foreign key to point to the parent.
           
        The the docstrings of the actual implementations for examples,
        that's going to make it clearer.

        As a sidenote: This only works for a single-column reference
        key from the parent class to the child class. It would be
        possible implementing this for multiple column keys using an
        anonymous dbclass, but it's just soooo darn complicated! So I
        thought to myself that t4.orm is complecated enough...
        """
        datatype.__init__(self, None, title)
        self.child_relation = child_relation
        self.child_column = child_column
        self.child_key = child_key


    def __init_dbclass__(self, dbclass, attribute_name):
        datatype.__init_dbclass__(self, dbclass, attribute_name)
        if self.child_column is not None:
           self.child_column.__init_dbclass__(dbobject, attribute_name)

        if self.child_key is None:
           pkey_column = dbclass.__primary_key__.column()
           self.child_key = "%s_%s" % ( dbclass.__relation__.name,
                                        pkey_column.name, )
        
    def __set_from_result__(self, ds, dbobj, value):
        """
        A container is not selected from a result.
        """
        raise NotImplementedError("Not implemented by this container datatype.")

    def __convert__(self, value):
        "Containers do not need a convert method or can't use it anyway."
        raise NotImplementedError(__doc__)

    def sql_literal(self, dbobj):
        "This container cannot be represented as an SQL literal."
        return None

    def select_expression(self, dbclass, full_column_names):
        return None
    
    def __select_after_insert__(self, dbobj):
        """
        @returns: False. Containers to not need to select anything,
          even after the insert.
        """
        return False

    def child_where(self, dbobj):
        """
        A where clause that leads to all the rows in the child table
        associated with this parent table.
        """
        return sql.where( self.child_key, " = ",
                          dbobj.__primary_key__.sql_literal() )
        

class sqltuple(_container):
    """
    This datatype represents a relationship between relations in which
    the child relation provides a number of values for a parent
    relation indexed by the parent's primary key. In the parent dbobject
    these values appear as a tuple.

    Like this::

       CREATE parent (
           id INTEGER,
           ... some more fields ...
       );

       CREATE child (
           parent_id INTEGER NOT NULL REFERENCES parent(id),
           info TEXT
       );

    An appropriate dbclass would look like this::

       class parent(dbobject):
           id = integer()
           info = sqltuple('child', text(), 'id', 'parent_id')

       result = ds.select(parent)
       p = result.next()
       p.info = ( "One", "Two", "Three", )

    An sqltuple is not mutable (i.e. a tuple and not a list), so you
    can't set any member of the tupe as in t[3] = 'Hallo'. To append a
    value you must say dbobj.tpl += ( "Hallo", ). The program will do
    the right thing and only create as many INSERT statements as
    strings added. For all other operations all rows referenced by the
    parent's key will be DELETEd and INSERTed again.

    The sqltuple dbattribute may be set to any iterable that yields
    values of the appropriate type. It will always return a Python
    tuple.

    The orderby parameter allows you to specify an SQL clause that
    will determine the order of the child table's rows that are
    returned. It may be None. Orderby must be an instance of
    t4.sql.orderby.

    A sqltuple cannot be None, just an empty tuple.
    """
    def __init__(self, child_relation, child_column, orderby=None,
                 child_key=None, title=None):
        _container.__init__(self, child_relation, child_column,
                            child_key, title)
        assert orderby is None or isinstance(orderby, sql.orderby), \
                                  "Orderby must be an instance of sql.orderby"
        self.orderby = orderby


    def __get__(self, dbobj, owner="What??"):
        if dbobj is None: return self
        self.check_dbobj(dbobj)

        if self.isset(dbobj):
            return getattr(dbobj, self.data_attribute_name())
        else:
            # Consturct the SQL query
            query = sql.select( self.child_column.column,
                                self.child_relation,
                                self.child_where(dbobj),
                                self.orderby )
            cursor = dbobj.__ds__().execute(query)
            ret = map(lambda tpl: self.child_column.__convert__(tpl[0]),
                      cursor.fetchall())
            ret = tuple(ret)
            setattr(dbobj, self.data_attribute_name(), ret)
            return ret

    def __set__(self, dbobj, new_values):
        self.check_dbobj(dbobj)
        
        if new_values is None:
            raise ValueError("You cannot set a sqltuple to None, sorry.")

        # Convert each of the values in the new tuple to the
        # child_column's type and run its validators on each of them.

        new = []
        for value in new_values:
            value = self.child_column.__convert__(value)
            for validator in self.child_column.validators:
                validator.check(dbobj, self, value)

            new.append(value)

        # Let's see if it's just an addition of values. In that case
        # we'll not delete anything, just create a couple of INSERT
        # statements.
        
        if self.isset(dbobj):
           dont_delete = True
           old = getattr(dbobj, self.data_attribute_name())
           
           if len(old) <= len(new):
              for o, n in zip(old, new):
                 if o != n:
                    dont_delete = False
                    break
        else:
           old = ()
           dont_delete = False
           
        if dont_delete:
            to_insert = new[len(old):]
        else:
            to_insert = new

            dbobj.__ds__().execute(sql.delete(self.child_relation,
                                              self.child_where(dbobj)))
        
        for value in to_insert:
            if value is None:
                literal = sql.NULL
            else:
                literal = self.child_column.sql_literal_class(value)
                
            dbobj.__ds__().execute(
                sql.insert(self.child_relation,
                           ( self.child_key,
                             self.child_column.column, ),
                           ( dbobj.__primary_key__.sql_literal(),
                             literal, ) ))
            
        setattr(dbobj, self.data_attribute_name(), tuple(new))
            

class sqldict(_container):
   """
   This datatype represents a relationship between relations in which
   the child relation proveies a number of values for a parent
   relation indexed by the parent's primary key and a unique key for
   each of the entries. In the parent dbobject these key/value pairs
   appear as a dict.

   Like this:

     CREATE user (
        id INTEGER,
        ... some more fields ...
     );

     CREATE user_info (
        user_id INTEGER REFERENCES user(id),
        key VARCHAR(100),
        value TEXT,

        PRIMARY KEY(user_id, key)
     );

   The PRIMARY KEY clause is not strictly necessary, but it will make
   sure every user_id/key pair only appears once. You may also want to
   create an index over the user_id column, because queries will
   usually call for all the child rows associated with the parent.

   An appropriate dbclass would look like this::

     class user(dbobject):
         id = integer()
         info = sqldict('user_info', varchar(column=key),
                        Unicode(column=value))

     result = ds.select(user)
     me = result.next()
     me.info['firstname'] = 'Diedrich'
     me.info['lastname'] = 'Vorberg'

     if me.info['age'] > '40': # FIXED! Old value: '30'
         print 'Consider suicide!'

   As for the sqltuple the whole thing only works on single-column
   primary keys.
   """
   def __init__(self, child_relation, child_key_column, child_value_column,
                child_key=None, title=None):
      _container.__init__(self, child_relation, child_column=None,
                          child_key=child_key, title=title)
      self.child_key_column = child_key_column
      self.child_value_column = child_value_column
    
   def __init_dbclass__(self, dbclass, attribute_name):
      _container.__init_dbclass__(self, dbclass, attribute_name)
      
      self.child_key_column.__init_dbclass__(dbobject, "key")
      self.child_value_column.__init_dbclass__(dbobject, "value")

   def __get__(self, dbobj, owner="Who??"):
        if dbobj is None: return self
        self.check_dbobj(dbobj)

        if self.isset(dbobj):
            return getattr(dbobj, self.data_attribute_name())
        else:
            # Consturct the SQL query
            query = sql.select( ( self.child_key_column.column,
                                  self.child_value_column.column, ), 
                                self.child_relation,
                                self.child_where(dbobj) )
            cursor = dbobj.__ds__().execute(query)
            ret = map(lambda tpl:
                         ( self.child_key_column.__convert__(tpl[0]),
                           self.child_value_column.__convert__(tpl[1]), ),
                      cursor.fetchall())
            ret = self.sqldict_dict(self, dbobj, dict(ret))
            setattr(dbobj, self.data_attribute_name(), ret)
            return ret


   def __set__(self, dbobj, new_dict):
      self.check_dbobj(dbobj)
        
      if new_values is None:
         raise ValueError("You cannot set a sqldict to None, sorry.")

        # Convert each of the keys and values in the new dict to the
        # appropriate types and run the validators on each of the values.

      new = {}
      for key, value in new_dict.items():
         key = self.child_key_column.__convert__(key)
         value = self.child_value_column.__convert__(value)
         
         for validator in self.child_key_column.validators:
            validator.check(dbobj, self, key)
            
         for validator in self.child_value_column.validators:
            validator.check(dbobj, self, value)
              
         new[key] = value

      # Delete the rows currently in the database
      dbobj.__ds__().execute(sql.delete(self.child_relation,
                                          self.child_where(dbobj)))

      # And insert new ones
      for key, value in new.items():
         key_literal = self.child_key_column.sql_literal_class(key)
           
         if value is None:
            value_literal = sql.NULL
         else:
            value_literal = self.child_value_column.sql_literal_class(value)
            
         query = sql.insert( self.child_relation,
                             ( self.child_key,
                               self.child_key_columnd.column,
                               self.child_value_column.column, ),
                             ( dbobj.__primary_key__.sql_literal(),
                               key_literal, value_literal, ) )
         dbobj.__ds__().execute(query)
            
         setattr(dbobj, self.data_attribute_name(),
                 self.sqldict_dict(self, dbobj, new))
            

   class sqldict_dict(dict):
      def __init__(self, sqldict, dbobj, data={}):
         self.update(data)
         self._sqldict = sqldict
         self._dbobj = dbobj
         
      def __setitem__(self, key, value):
         key_column = self._sqldict.child_key_column.column
         key_literal = self._sqldict.child_key_column.sql_literal_class(key)
         
         value_column = self._sqldict.child_value_column.column
         value_literal = self._sqldict.child_value_column.sql_literal_class(
            value)

         if self.has_key(key):
            where = self._sqldict.child_where(self._dbobj) + sql.where(
               key_column, " = ", key_literal)
            
            command = sql.update(self._sqldict.child_relation, where,
                                 { str(value_column): value_literal })
         else:
            command = sql.insert( self._sqldict.child_relation,
                                  ( self._sqldict.child_key,
                                    key_column,
                                    value_column, ),
                                  ( self._dbobj.__primary_key__.sql_literal(),
                                    key_literal, value_literal, ) )
            
         self._dbobj.__ds__().execute(command)
            
         dict.__setitem__(self, key, value)

      def __delitem__(self, key):
         key_column = self._sqldict.child_key_column.column
         key_literal = self._sqldict.child_key_column.sql_literal_class(key)

         where = self.child_where(dbobj) + sql.where(
             key_column, " = ", key_literal)
         
         dbobj.__ds__().execute(sql.delete(self.child_relation, where))
         
         dict.__delitem__(self, key)






