#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

"""
This module provides a simple wrapper for SQL within Python. The idea
is to obscure the SQL code that is being generated as little as
possible, but to hide all the gorry details, especially of quoting and
escaping things, away from the programmer. Also this code is supposed
to be backend independent. 

The way it works is best described by example::

  >>> ds = backend(...some params...)
  >>> s = select( ( quotes('first name'), 'lastname', 'age',
                   expression('age + 10'),
                   as(_quotes('negative age'), 'age - 10')),
                 'person',
                 where('age > 10'), order_by('age'))
  >>> print sql(ds)(s)
  SELECT "first name", lastname, age, age + 10,
     age - 10 AS "negative age" FROM person WHERE age > 10  ORDER BY "age"
  >>> u = update( 'person', where('id = 22'),
                 firstname = string_literal('Diedrich'),
                 lastname=string_literal('Vorberg'))
  >>> print sql(ds)(u)
  UPDATE person SET lastname = 'Vorberg', firstname = 'Diedrich' WHERE id = 22
  >>> d = delete ('person', where('id = 22'))
  >>> print sql(ds)(d)
  DELETE FROM person WHERE id = 22

"""
__author__ = "Diedrich Vorberg <diedrich@tux4web.de>"

from string import *
from types import *

from t4.debug import sqllog

NULL = "NULL" 

# Exceptions
class UnicodeNotAllowedInSQL(TypeError): pass
class SQLSyntaxError(Exception): pass
class UnicodeNotAllowedInSQL(Exception): pass
class ClauseAlreadyExists(Exception): pass 
class IllegalOrderDirection(Exception): pass


class backend:
    """
    This class provies all the methods needed for a datasource to work
    with an SQL backend.  This class' instances will work for most
    SQL92 complient backends that use utf-8 unicode encoding. 
    """

    escaped_chars = ( ('"', r'\"',),
                      ("'", r'\"',),
                      ("%", "%%",), )
    
    def identifyer_quotes(self, name):
        return '"%s"' % name

    def string_quotes(self, string):
        return "'%s'" % string

    def escape_string(self, string):
        for a in self.escaped_chars:
            string = string.replace(a[0], a[1])

        return string
    
    def backend_encoding(self):
        raise NotImplementedError()

class pgsql_backend(backend):
    """
    Backend definition for PostgreSQL.
    """
    escaped_chars = [ ("\\", "\\\\"),
                      ("'",  "\\'"),
                      ('"',  '\\"'),
                      ("\0", "\\000"),
                      ("`",  "\\`"),
                      ("\n", "\\n"),
                      ("\r", "\\r"),
                      ("\t", "\\t"),
                      ("%",  "\\045",),
                      ("?", "\\077",), ]
    
class mysql_backend(backend):
    escaped_chars = ( ('"', r'\"',),
                      ("'", r'\"',),
                      ("%", "%%",), )
    
    def identifyer_quotes(self, name):
        return '`%s`' % name
    
    #def escape_string(self, string):
    #    return self._conn.escape_string(string)
    # I'm using my own implementation, because MySQLdb uses
    # mysql_real_escape_string(), which does charset conversion. Yet, this
    # doesn't make sense on binary data for instance...

class firebird_backend(backend):
    pass

class gadfly_backend(backend):
    pass


class sql:
    """
    This class is used to do something that Haskell is called
    'cyrrying'. This is what leads to the somewhat unusual constructs
    in this source file, that look like::

      sql(backend)(some_element)

    The sql class is instantiated with the backend as the
    constructor's argument. The instance implements the __call__
    interface, which enables me to use it like a function. This
    'function' is then applied to the some_element parameter. This is
    especially usefull when programming in a functional style as I did
    here.

    It takes a while to get used to this type of thinking, but it's
    certainly worthwhile. Some consider this kind of programming
    beautifull in artistic meaning of the word ;-)

    @var params: After being called, this attribute contains those parameters
       of the SQL statement that have not been escaped by this module but
       shall be passed to cursor.execute() as second argument. Corresponding
       ?s will be contained in the SQL statement.
    """
    
    def __init__(self, ds):
        if not isinstance(ds, backend):
            raise TypeError("sql takes a datasource as argument")
        
        self.ds = ds
        self.params = []

    def __call__(self, *args):
        """
        The arguments must either provide an __sql__() function or be
        convertable to strings. The __sql__() function must return either a
        string containing SQL or a pair as ( SQL, params, ) in which params
        is a tuple which will be passed to cursor.execute() as second
        arguments. These are Python instances used by the cursor to replace
        ?s. This lets the lower level DBAPI module handle the quoting.
        """
        ret = []
        
        for arg in args:
            if type(arg) == UnicodeType:
                raise UnicodeNotAllowedInSQL()
            else:        
                if hasattr(arg, "__sql__"):
                    ret.append(arg.__sql__(self))
                else:
                    ret.append(str(arg))

        return join(ret, " ")

def flatten_identifyer_list(runner, arg):
    """
    A helper function that takes a list of strings, column and relaton
    classes and converts if it to sensible sql. 
    """
    if type(arg) in (TupleType, ListType):
        arg = map(runner, arg)
        return join(arg, ", ")
    else:
        return runner(arg)

class _part:
    """
    The _part class is the base class for all SQL statement classes.
    It proviedes a __str__() method, which calls __sql__() with a minimal
    standard datasource that will yield SQL92 compliant results.
    """
    def __sql__(self, runner):
        raise NotImplementedError()

    def __str__(self):
        return sql(backend())(self)
    
    def __eq__(self, other):
        """
        Two SQL statements are considered equal if attributes containing
        strings or statements are equal. (That means, that this method will
        be called recursivly at times.
        """
        if not isinstance(other, self.__class__):
            # Two statements must be of the same class to be
            # equal.
            return False

        for property, my_value in self.__dict__.items():
            if not other.__dict__.has_key(property):
                # If the two statements have a different set of properties,
                # they must be different.
                return False
            
            other_value = other.__dict__[property]
            
            if my_value != other_value:
                # the != above may call this function recursivly.
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))
    
class statement(_part):
    """
    Base class for all statements (select, update, delete, etc)
    """

class clause(_part):
    """
    Base class for clauses. They will be ordered according to rank
    when used to form a statement.
    """
    rank = 0

class identifyer(_part):
    """
    Base class that encapsulates all sql identifyers.
    """
    def __init__(self, name, quotes=False):
        self._name = name
        self._quotes = quotes

    def __sql__(self, runner):
        if self._quotes:
            return runner.ds.identifyer_quotes(self._name)
        else:
            return self._name

    def __str__(self):
        """
        When converted to regular strings, identifyers are not quoted.
        """
        return self._name

    def name(self):
        return self._name

    def quotes(self):
        return self._quotes

class quotes(identifyer):
    """
    Shorthand for an identifyer that you'd like to be surrounded in
    quotes within the sql code.
    """
    def __init__(self, name):
        identifyer.__init__(self, name, True)

class literal(_part):
    """
    Base class for those classes that encapsulate a value that is ment
    to go into the SQL as-such.
    """
    def __init__(self, sql):
        if type(sql) == UnicodeType:
            raise UnicodeNotAllowedInSQL()
            
        self._sql = sql

    def __sql__(self, runner):
        return self._sql

class integer_literal(literal):    
    def __init__(self, i):
        if type(i) != IntType and type(i) != LongType:
            raise TypeError(
                "integer_literal takes an integer as argument, not a " +\
                    repr(type(i)))
        self._sql = str(i)

class float_literal(literal):
    def __init__(self, i):
        if type(i) != FloatType and type(i) != LongType:
            raise TypeError(
                "float_literal takes an float as argument, not a " + \
                    repr(type(i)))
        self._sql = str(i)

class string_literal(literal):
    def __init__(self, s):
        if type(s) == UnicodeType:
            raise TypeError("string_literal takes a string as argument. " + \
			    "Use unicode_literal for Unicode values.")
        
        self._content = str(s)

    def __sql__(self, runner):
        s = runner.ds.escape_string(self._content)
        sql = runner.ds.string_quotes(s)

        return sql

class unicode_literal(literal):
    def __init__(self, u, errors="strict"):
        """
        The errors parameter determines what to do if a character cannot
        be incoded in the target coding system. Other legal values 'ignore'
        and 'replace'. See the documentation for the built-in unicode()
        function.
        """
        if type(u) != UnicodeType:
            raise TypeError("unicode_literal takes a unicode argument.")

        self._content = u
        self._errors = errors

    def __sql__(self, runner):
        s = self._content.encode(runner.ds.backend_encoding(), self._errors)
        s = runner.ds.escape_string(s)
        sql = runner.ds.string_quotes(s)

        return sql

class idna_literal(unicode_literal):
    """
    SQL literal class for Unicode (idna) domain names and email
    addresses. This represents a Python unicode object as an idna
    string in the database.
    """
    def __sql__(self, runner):
        if "@" in self._content: # e-Mail address
            local, remote = split(self._content, "@")
            local = local.encode("ascii")
            remote = remote.encode("idna")

            s = "%s@%s" % ( local, remote, )
            s = runner.ds.escape_string(s)
            sql = runner.ds.string_quotes(s)
        else:
            s = self._content.encode("idna")
            s = runner.ds.escape_string(s)
            sql = runner.ds.string_quotes(s)

        return sql

class bool_literal(literal):
    def __init__(self, b):
        self._content = bool(b)

    def __sql__(self, runner):
        if self._content:
            return "TRUE"
        else:
            return "FALSE"

class direct_literal(literal):
    """
    This returns a %s as SQL code and the content you pass to the
    constructor to be quoted by the cursor's implementation rather
    than by the backend class' mechanism.

    Refer to he sql class' __call__() method.
    """
    def __init__(self, content):
        self._content = content

    def __sql__(self, runner):
        runner.params.append(self._content)
        return "%s"
    
            
class relation(_part): 
    def __init__(self, name, schema=None, quote=False):
        if not isinstance(name, identifyer):
            self._name = identifyer(name, quote)
        else:
            self._name = name

        if type(schema) == StringType:
            self._schema = identifyer(schema)
        else:
            self._schema = schema

    def __sql__(self, runner):
        if self._schema is not None:
            return runner(self._schema) + "." + runner(self._name)
        else:
            return runner(self._name)

    def name(self, underscore=False):
        """
        @param underscore: If underscore is True, dots in the output will be
            replaced by underscores.
        """
        ret = str(self)
        
        if underscore:
            return replace(ret, ".", "_")
        else:
            return ret

    def schema(self):
        return self._schema

        
class column(_part):
    """
    A column name. If the relation argument is passed to the
    constructor, the sql result will look like::

       relation.column_name

    including appropriate quotes if desired. The relation parameter
    may be an sql.identifyer instance if the relation name needs to be
    quoted.
    """
    def __init__(self, name, relation=None, quote=False):
        if not isinstance(name, identifyer):
            self._name = identifyer(name, quote)
        else:
            self._name = name

        if type(relation) == StringType:
            self._relation = identifyer(relation)
        else:
            self._relation = relation

        self._quote = quote

    def __sql__(self, runner):
        if self._relation is not None:
            return runner(self._relation) + "." + runner(self._name)
        else:
            return runner(self._name)

    def name(self, underscore=False):
        """
        @param underscore: If underscore is True, dots in the output will be
            replaced by underscores.
        """
        ret = str(self)
        
        if underscore:
            return replace(ret, ".", "_")
        else:
            return ret

    def quote(self):
        return self._quote

    def __eq__(self, other):
        try:
            if other is None:
                return False
            elif self._relation is not None and other._relation is not None:
                return ( self._relation == other._relation and \
                             self._name == other._name )
            else:
                return self._name == other._name
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return "<%s %s>" % ( self.__class__.__name__, str(self), )
        
class expression:
    """
    Encapsolate an SQL expression like an arithmetic expression or a
    function call.

    >>> sql()( expression('COUNT(amount) + ', 10) )
    ==> COUNT(amount) + 10
    """
    def __init__(self, *parts):
        self._parts = []
        self._append(parts)
        self._name = "<<EXPRESSION>>"

    def _append(self, parts):
        for part in parts:
            if type(part) in ( TupleType, ListType, GeneratorType, ):
                self._append(part)
            else:
                self._parts.append(part)

    def __sql__(self, runner):
        parts = map(runner, self._parts)
        parts = map(strip, parts)
        return join(parts, " ")

    def __add__(self, other):
        ret = expression()
        ret.parts = self._parts + other._parts

        return ret

class as_(expression):
    """
    Encapsulates an expression that goes into an AS statement in a
    SELECT's column list.

    >>> sql()( AS('column', 'columns / 10') )
    ==> columns / 10 AS column_div_by_ten

    """
    def __init__(self, column, *parts):
        self._column = column
        expression.__init__(self, *parts)

    def __sql__(self, runner):
        return expression.__sql__(self, runner)+" AS "+runner(self._column)

class where(clause, expression):
    """
    Encapsulates the WHERE clause of a SELECT, UPDATE and DELETE
    statement. Just an expression with WHERE prepended.
    """
    rank = 1

    def __sql__(self, runner):
        return "WHERE " + expression.__sql__(self, runner)

    def __add__(self, other):
        """
        Multiplying two where clauses connects them using OR (including
        parantheses). 
        """
        return self.or_(self, other)

    def __mul__(self, other):
        """
        Adding two where clauses connects them using AND (including
        parantheses)
        """
        return self.and_(self, other)

    def or_(cls, *others):
        """
        OTHERS is a list of sql.where instances that are connected
        using OR.
        """
        others = filter(lambda o: o is not None, others)
        
        if len(others) < 1:
            raise ValueError("Empty input for or_()")
        
        ret = where()
        
        for other in others:
            ret._parts.append("(")
            ret._parts += list(other._parts)
            ret._parts.append(")")
            ret._parts.append(" OR ")
            
        del ret._parts[-1] # remove the last OR

        return ret
    or_ = classmethod(or_)
    
    def and_(cls, *others):
        """
        OTHERS is a list of sql.where instances that are connected
        using OR.
        """
        others = filter(lambda o: o is not None, others)
        
        if len(others) < 1:
            raise ValueError("Empty input for and_()")
        
        ret = where()
        
        for other in others:
            ret._parts.append("(")
            ret._parts += list(other._parts)
            ret._parts.append(")")
            ret._parts.append(" AND ")
            
        del ret._parts[-1] # remove the last OR

        return ret
    and_ = classmethod(and_)

class order_by(clause):
    """
    Encapsulate the ORDER BY clause of a SELECT statement. Takes a
    list of columns as argument.

    FIXME: order by expression, ASC, DESC!!!
    """
    
    rank = 4
    
    def __init__(self, *columns, **kw):
        self._columns = columns

        dir = kw.get("dir", "ASC")
        if upper(dir) not in ("ASC", "DESC",):
            raise SQLSyntaxError("dir must bei either ASC or DESC")
        else:
            if dir == "ASC":
                self._dir = None
            else:
                self._dir = dir

    def __sql__(self, runner):
        ret = "ORDER BY %s" % flatten_identifyer_list(runner, self._columns)
        
        if self._dir is not None:
            ret = "%s %s" % ( ret, self._dir, )

        return ret

orderby = order_by    

class group_by(clause):
    """
    Encapsulate the GROUP BY clause of a SELECT statement. Takes a
    list of columns as argument.
    """
    
    rank = 3
    
    def __init__(self, *columns, **kw):
        self._columns = columns

    def __sql__(self, runner):
        return "GROUP BY %s" % flatten_identifyer_list(runner, self._columns)
        
groupby = group_by

class limit(clause):
    """
    Encapsulate a SELECT statement's limit clause.
    """
    
    rank = 5
    
    def __init__(self, limit):
        if type(limit) != IntType:
            raise TypeError("Limit must be an integer")
        
        self._limit = limit

    def __sql__(self, runner):
        limit = integer_literal(self._limit)
        return "LIMIT %s" % runner(limit)

class offset(clause):
    """
    Encapsulate a SELECT statement's offset clause.
    """
    
    rank = 6
    
    def __init__(self, offset):
        if not type(offset) in (IntType, LongType,):
            raise TypeError("Offset must be an integer")
        
        self._offset = offset

    def __sql__(self, runner):
        offset = integer_literal(self._offset)
        return "OFFSET %s" % runner(offset)

class select(statement):
    """
    Encapsulate a SELECT statement.
    """
    
    def __init__(self, columns, relations, *clauses):
        self._columns = columns
        self._relations = relations
        self._clauses = filter(lambda clause: clause is not None,
                               list(clauses))
        for c in self._clauses:
            if not isinstance(c, clause):
                raise TypeError("%s is not an SQL clause" % repr(c))
            
    def __sql__(self, runner):
        clauses = filter(lambda a: a is not None, self._clauses)
        clauses.sort(lambda a, b: cmp(a.rank, b.rank))
        clauses = map(runner, clauses)
        clauses = join(clauses, " ")

        columns = flatten_identifyer_list(runner, self._columns)
        relations = flatten_identifyer_list(runner, self._relations)

        return "SELECT %(columns)s FROM %(relations)s %(clauses)s" % locals()

class insert(statement):
    """
    Encapsulate an INSERT statement.

    The VALUES param to the constructor may be a sql.select() instance.
    We'll do the right thing.
    """
    def __init__(self, relation, columns, *values):
        self._relation = relation
        self._columns = columns
        self._values = values

        if len(values) == 0:
            raise SQLSyntaxError(
                "You  must supply values to an insert statement")
        
        if not isinstance(values[0], select):
            for tpl in values:
                if len(self._columns) != len(tpl):
                    raise SQLSyntaxError(
                        "You must provide exactly one value for each column")

    def __sql__(self, runner):
        relation = self._relation
        columns = flatten_identifyer_list(runner, self._columns)

        INSERT = "INSERT INTO %(relation)s(%(columns)s)" % locals()

        if isinstance(self._values[0], select):
            return "%s %s" % ( INSERT, self._values[0].__sql__(runner), ) 
        else:
            # ok, values are no identifyers, but it's really the same thing
            # that's supposed to happen with them: call sql() on each of them,
            # put a , in between and return them as a string
            tuples = []
            for tpl in self._values:
                # Look for expressions among the values. Convert them into
                # simple strings with ( argound them ).
                tpl = list(tpl)
                for idx, part in enumerate(tpl):
                    if isinstance(part, expression):
                        tpl[idx] = "(" + runner(part) + ")"
                        
                tpl = flatten_identifyer_list(runner, tpl)
                tuples.append("(" + tpl + ")")
            tuples = join(tuples, ", ")
                                
            return INSERT + " VALUES " + tuples
    
class update(statement):
    """
    Encapsulate a UPDATE statement.
    """
    
    def __init__(self, relation, where_clause, info={}, **param_info):
        """
        @param relation: The relation to be updates.
        @param where_clause: where clause that determines the row to be updated
        @param info: Dictionary as {'column': sql_literal}
        """
        self._relation = relation
        self._info = info
        self._info.update(param_info)

        if not isinstance(where_clause, where):
            where_clause = where(where_clause)
            
        self._where = where_clause
        
    def __sql__(self, runner):
        relation = runner(self._relation)
        where = runner(self._where)

        info = []
        for column, value in self._info.items():
            column = runner(column)
            value = runner(value)

            info.append( "%s = %s" % (column, value,) )

        info = join(info, ", ")
        
        return "UPDATE %(relation)s SET %(info)s %(where)s" % locals()


class delete(statement):
    """
    Encapsulate a DELETE statement.
    """
    
    def __init__(self, relation, where_clause=None):
        self._relation = relation
        self._where = where_clause
        
    def __sql__(self, runner):
        relation = runner(self._relation)

        if self._where is not None:
            where = runner(self._where)        
            return "DELETE FROM %(relation)s %(where)s" % locals()
        else:
            return "DELETE FROM %(relation)s" % locals()

class left_join(clause, expression):
    def __init__(self, relation, *parts):
        if hasattr(relation, "__relation__"): relation = relation.__relation__
        expression.__init__(self, *parts)
        self._relation = relation

    def __sql__(self, runner):
        relation = flatten_identifyer_list(runner, self._relation)
        return "LEFT JOIN %s ON %s" % ( relation,
                                        expression.__sql__(self, runner), )
    
class right_join(clause, expression):
    def __init__(self, relation, *parts):
        if hasattr(relation, "__relation__"): relation = relation.__relation__
        expression.__init__(self, *parts)
        self._relation = relation

    def __sql__(self, runner):
        relation = flatten_identifyer_list(runner, self._relation)
        return "RIGHT JOIN %s ON %s" % ( relation,
                                        expression.__sql__(self, runner), )

class nil(expression, clause, statement):
    def __sql__(self, runner):
        return ""
    
class cursor_wrapper:
    """
    The cursor wrapper takes a regular database cursor and 'wraps' it
    up so that its execute() method understands sql.* objects as
    parameters. 
    """
    def __init__(self, ds, cursor):
        self._ds = ds
        self._cursor = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def execute(self, command, params=None):
        if type(command) == UnicodeType:
            raise TypeError("Database queries must be strings, not unicode")

        if isinstance(command, statement):
            runner = sql(self._ds)
            command = runner(command)
            params = runner.params

        if params is None:
            print >> sqllog, self._cursor, command
            self._cursor.execute(command)
        else:
            print >> sqllog, self._cursor, command, " || ", repr(params)
            self._cursor.execute(command, tuple(params))


def join_tokens(lst, sep):
    ret = []
    for a in lst:
        ret.append(a)
        ret.append(sep)

    ret.pop()
    
    return ret

