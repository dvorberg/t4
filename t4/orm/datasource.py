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

__docformat__ = "epytext en"

"""
Defines abstract class datasource, baseclass for adapter.*.datasource.

The datasource module defines the datasource class and a number of
conveniance classes for managing query results.
"""

# Python
from types import *
import string

# t4
from t4 import sql, stupid_dict
import keys
from exceptions import *

def datasource(connection_string="", **kwargs):
    """
    Return a ORM datasource object constructed from a connection
    string or a number of keyword arguments.

    The connection strings follow the conventions for PostgreSQL DSNs:
    they consist of keyword=value pairs seperated with whitespace.
    Keywords recognized are::

      adapter  - name of the ORM adapter used. Use the name from the
                 adapters/ directory.
      pool     - User datasource pool (requires psycopg2)           
      db       - name of the database to connect to
      user     - Database username
      password - Password used for authentication
      host     - hostname or IP address of the machine the database
                 runs on (note that there might be a difference if you
                 use 127.0.0.1 or localhost. The first creating a tcp/ip
                 connection, the latter a unix/fifo connection. This is
                 true for at leas pgsql and mysql
      debug    - if set SQL queries will be printed to stdout (actually
                 the debug.debug function is called so you can overload
                 it)

    Each of the database backends may define its own keywords. For
    instance PostgreSQL will understand each of the original keywords
    as aliases. Check the documentation!

    Values may not contain spaces.

    If you prefer to use the keyword argument syntax, the paramters must
    be the key and their arguments the values::

       datasource('db=test user=diedrich password=kfjdh')

    equals::

       datasource(db='test', user='diedrich', password='kfjdh')
    """
    
    try:
        parts = string.splitfields(connection_string)
        params = {}
        for part in parts:
            name, value = string.split(part, "=")
            if name != "" and value != "":
                params[name] = value
            else:
                raise ValueError()
            
    except ValueError, msg:
        raise IllegalConnectionString("%s (%s)" % (connection_string,
                                                   msg))
    
    params.update(kwargs)
    
    try:
        adapter = params["adapter"]
    except KeyError:
        raise IllegalConnectionString(
        "%s (The adapter= keyword must always be present!)" %connection_string)

    del params["adapter"]

    if params.has_key("pool"):
        if adapter == "pgsql":
            try:
                from t4.orm.adapters.pgsql.datasource import pool
            except ImportError:
                raise IllegalConnectionString(
                    "No pool module. Psycopg2 not installed?")
        else:
            raise IllegalConnectionString(
                "No pool module for this adapter: %s"\
                    % adapter)

        return pool(params)
    else:
        if adapter == "gadfly":
            from t4.orm.adapters.gadfly.datasource import datasource
        elif adapter == "pgsql":
            from t4.orm.adapters.pgsql.datasource import datasource
        elif adapter == "mysql":
            from t4.orm.adapters.mysql.datasource import datasource        
        elif adapter == "firebird":
            from t4.orm.adapters.firebird.datasource import datasource
        else:
            raise IllegalConnectionString("Unknown adapter: %s" % adapter)

        if params.has_key("debug"):
            debug = True
            del params["debug"]
        else:
            debug = False

        ds = datasource.from_params(params)
        ds._debug = debug
        
        return ds
    
class datasource_base:
    """
    The DataSource encapsulates the functionality we need to talk to the
    database. Most notably are the insert, select and delete methods.

    This class must be subclassed by the adapter.*.datasource.datasource
    classes.

    It inherits from sql.datasource to provide default implmentations of
    the methods the sql module depends upon.
    """
    _format_funcs = {}
    
    def __init__(self):
        self._conn = None
        self._debug = 0
        self._modify_cursor = None
        self._changed_dbobjs = set()

    def __register_change_of__(self, dbobj):
        self._changed_dbobjs.add(dbobj)
        
    def _dbconn(self):
        """
        Return the dbconn for this ds
        """
        return self._conn
    
    def query_one(self, query):
        """        
        This method is ment for results that return exactly one row or item

        It will:
        
          - return None if there is an empty result returned
          - if there are more than one result row, return the result as is 
            (a tuple of tuples)
          - if there is only one row, but several columns, return the row as 
            a tuple
          - if the only row has only one column, return the value of the 
            column
            
        @param query:  A string containing an SQL query.
        """
        cursor = self.execute(query)
        result = cursor.fetchall()

        try:
            if len(result) == 1:
                return result[0]
            else:
                return result
        except TypeError: # result has no size
            return result

    def execute(self, command, params=(), modify=False):
        """
        Execute COMMAND on the database. If modify is True, or the command
        is one of INSERT, UPDATE or DELETE, the command is assumed to
        modify the database. All modifying commands will be executed
        on the same cursor.
        
        @param command: A string containing an SQL command of any kind or an
               sql.statement instance.
        """
        if not modify:
            if type(command) == StringType:
                c = string.upper(string.lstrip(command[:6]))
                if c in ("DELETE", "INSERT", "UPDATE",):
                    modify = True
            elif isinstance(command, (sql.update, sql.insert, sql.delete)):
                modify = True

        if modify:
            cursor = self.__modify_cursor__()
            self.flush_updates()
        else:
            cursor = self.cursor()

        cursor.execute(command, params)
        return cursor

    def __modify_cursor__(self):
        if self._modify_cursor is None:
            self._modify_cursor = self.cursor()
            
        return self._modify_cursor

    def flush_updates(self, select_after_update=False):
        cursor = self.__modify_cursor__()
        for dbobj in self._changed_dbobjs:
            dbobj.__perform_updates__(cursor, select_after_update)
        self._changed_dbobjs = set()
    __flush_updates__ = flush_updates
        
    def commit(self, *dbobjs, **kw):
        """
        Run commit on this ds's connection. You need to do this for any
        change you really want to happen.

        If you specify dbobjects as arguments, only those dbobjs's
        updates will be performed and committed, the others will wait
        in the que. 
        """
        #cursor = kw.get("cursor", None)
        #self.perform_updates(cursor=cursor, *dbobjs)
        #self._dbconn().commit()
        #self._modify_cursor = None
        #return cursor
        self.flush_updates()
        self._dbconn().commit()
    
    def perform_updates(self, *dbobjs, **kw):
        pass
        
    def rollback(self):
        """
        Undo the changes you made to the database since the last commit()
        """
        self._dbconn().rollback()        
        
    def cursor(self):
        """
        Return a newly created dbi cursor.
        """
        return sql.cursor_wrapper(self, self._dbconn().cursor())

    def close(self):
        """
        Close the connection to the database.
        """
        self._dbconn().close()

    def ping(self):
        """
        Execute SELECT 1 on the database. If that raises any
        exception, return false, otherwise return true.
        """
        try:
            self.execute("SELECT 1")
            return True
        except:
            return False

    def select(self, dbclass, *clauses):
        """
        SELECT dbobjs from the database, according to clauses.

        @param dbclass: The dbclass of the objects to be selected.

        @param clauses: A list of t4.orm.sql clauses instances (or
                        equivalent Python object i.e. strings) that
                        are added to the sql.select query.  See
                        t4.orm.sql.select for details

        
        """
        from dbobject import dbobject

        clauses = filter(lambda clause: clause is not None, clauses)
        
        full_column_names = False
        for clause in clauses:
            if isinstance(clause, (sql.left_join, sql.right_join,)):
                full_column_names = True

            # GROUP BY clauses receive special treatment (in a good
            # way): If their first and only column (i.e. parameter
            # passed on creation) is a dbclass, it is replaced by the
            # dbclass' columns. This is a shorthand to formulate
            # joins. (And t4.sql can't know about dbclasses).
            if isinstance(clause, sql.group_by) and \
                    len(clause._columns) == 1 and \
                    hasattr(clause._columns[0], "__select_expressions__"):
                clause._columns = clause._columns[0].__select_expressions__(
                    True)
                
        query = sql.select(dbclass.__select_expressions__(full_column_names),
                           dbclass.__relation__, *clauses)
        
        return self.run_select(dbclass, query)

    
    def run_select(self, dbclass, select):
        """
        Run a select statement on this datasource that is ment to return
        rows suitable to construct objects of dbclass from them.

        @param dbclass: The dbclass of the objects to be selected
        @param select: sql.select instance representing the query
        """
        return dbclass.__result__(self, dbclass, select)

    def select_one(self, dbclass, *clauses):
        """
        This method is ment for queries of which you know that they
        will return exactly one dbobj. It will set a limit=1 clause.
        If the result is empty, it will return None, otherwise the
        selected dbobj.
        """
        clauses += (sql.limit(1),)

        result = self.select(dbclass, *clauses)

        try:
            return result.next()
        except StopIteration:
            return None
        
    def count(self, dbclass, *clauses):
        """
        All clauses except the WHERE clause will be ignored
        (including OFFSET and LIMIT!)
        
        @param dbclass: See select() above.
        @param clauses: See select() above.
        
        @return: An integer value indicating the number of objects
                 of dbclass select() would return if run with these clauses.
        """
        clauses = filter(lambda clause: (isinstance(clause, sql.where) or
                                         isinstance(clause, sql.left_join)),
                         clauses)
            
        query = sql.select("COUNT(*)", dbclass.__relation__, *clauses)
        return self.query_one(query)[0]

    def join_select(self, dbclass, *clauses):
        # this may take some figuring
        pass

    def primary_key_where(self, dbclass, key):
        """
        Return a t4.orm.sql where clause that will yield the object of dbclass
        whoes primary key equals key

        @param dbclass: The dbclass of the object the where clause is
                        supposed to be for.
        @param key: Python value representing the primary key or a tuple of
          such Python values, if the primary key has multiple columns
        """

        # this function is very simmilar to keys.key.where() - maybe unify?
        
        if type(key) != TupleType: key = ( key, )
        primary_key = keys.primary_key(dbclass)

        if len(key) != len(primary_key.key_attributes):
            msg = "The primary key for %s must have %i elements." % \
                     ( repr(dbclass), len(primary_key.key_attributes), )
            raise IllegalPrimaryKey(msg)

        where = []
        for property, value in zip(primary_key.attributes(), key):
            literal = property.sql_literal_class(property.__convert__(value))
            
            where.append(property.column)
            where.append("=")
            where.append(literal)
            where.append("AND")

        del where[-1] # remove last "AND"

        return sql.where(*where)
    
    def select_by_primary_key(self, dbclass, key):
        """
        Select a single object of dbclass from its relation, identified
        by its primary key.

        @param dbclass: Dbclass to be selected
        @param key: Python value representing the primary key or a tuple of
          such Python values, if the primary key has multiple columns
        @raise IllegalPrimaryKey: hallo
        @return: A single dbobj.
        """
        where = self.primary_key_where(dbclass, key)        
        result = self.select(dbclass, where)

        try:
            return result.next()
        except StopIteration:
            return None

    def select_for_update(self, dbclass, key):
        """
        This method works like L{select_by_primary_key} above, except that it
        doesn't select anything but returns a dummy object (an empty dbobj)
        that will allow setting attributes, yielding proper UPDATE statements.
        Note that supplying a primary key that does not exist will go
        unnoticed: The UPDATE statements won't create an error, they just
        won't affect any rows.

        This method is primarily ment for transaction based (i.e. www)
        applications.
        """
        if type(key) != TupleType: key = ( key, )
        primary_key = keys.primary_key(dbclass)

        if len(key) != len(primary_key.key_attributes):
            msg = "The primary key for %s must have %i elements." % \
                     ( repr(dbclass), len(primary_key.key_attributes), )
            raise IllegalPrimaryKey(msg)

        info = stupid_dict()
        for property, value in zip(primary_key.attributes(), key):        
            info[property.column] = value

        return dbclass.__from_result__(self, info)

    def insert(self, dbobj, dont_select=False, cursor=None):
        """
        @param dbobj: The dbobj to be inserted (must not be created by a
            select statement.
        @param dont_select: Do not perform a SELECT query for those columns
            whoes values are provided by the backend, either through
            AUTO_INCREMENT mechanisms or default column values.
        """
        if dbobj.__is_stored__():
            raise ObjectAlreadyInserted(repr(dbobj))
        
        sql_columns = []
        sql_values = []
        for property in dbobj.__dbproperties__():
            
            if property.isset(dbobj) and property.column not in sql_columns:
                update_expression = property.update_expression(dbobj)
                if update_expression is not None:
                    sql_columns.append(property.column)
                    sql_values.append(update_expression)

        if len(sql_columns) == 0:
            raise DBObjContainsNoData(
                "Please set at least one of the attributes of this dbobj")

        statement = sql.insert(dbobj.__relation__, sql_columns, sql_values)

        self.execute(statement)
        dbobj.__insert__(self)

        if dbobj.__primary_key__ is not None and not dont_select:
            self.select_after_insert(dbobj)

        return cursor

    def select_after_insert(self, dbobj):
        """
        This method will be run after each INSERT statement automaticaly
        generated by a ds to pick up default values and primary keys set
        by the backend. See insert().
        """
        properties = []
        columns = []
        for property in dbobj.__dbproperties__():
            if property.__select_after_insert__(dbobj):
                properties.append(property)
                columns.append(property.column)

        if len(properties) > 0:
            where = self.select_after_insert_where(dbobj)
            query = sql.select(columns, dbobj.__relation__, where)

            self._modify_cursor.execute(query)
            tpl = self._modify_cursor.fetchone()

            for property, value in zip(properties, tpl):
                property.__set_from_result__(self, dbobj, value)

    def select_after_insert_where(self, dbobj):
        raise NotImplemented()
    
    def close(self):
        self._dbconn().close()        

    def delete_by_primary_key(self, dbclass, primary_key_value, cursor=None):
        where = self.primary_key_where(dbclass, primary_key_value)
        self.delete(dbclass, where, cursor)
        
    def delete(self, dbclass, where, cursor=None):
        command = sql.delete(dbclass.__relation__, where)
        self.execute(command, cursor)
        
