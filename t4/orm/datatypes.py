#!/usr/bin/env python
# -*- coding: utf-8; mode: python; ispell-local-dictionary: "english" -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2002-2014 by Diedrich Vorberg <diedrich@tux4web.de>
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
Datatype classes for the default SQL datatypes.
===============================================

  Each of the classes in this module models an SQL datatype. Their
  instances will be responsible for managing an attribute in a
  dbclass. The classes accept a number of arguments for you to
  influence what exactly they do. Refer to L{datatype.__init__} for these.
  
"""
# Python
import sys, copy, cPickle
from types import *
from string import *
from datetime import time as py_time

# t4
from t4.validators import *
from t4 import normalize_date, normalize_datetime
from t4 import sql

_property_counter = 0

class datatype(property):
    """
    This class encapsulates a dbclass' property (=attribute). It takes
    care of the SQL column name and the information actually stored in the
    database/the dbobject.

    You may set most dbproperties to sql.expression-instances which are
    included in the generated INSERT or UPDATE statements as-is. On INSERT
    the corresponding columns will be SELECTed from the database (like
    AUTO INCREMENT or default= columns), but on UPDATE they will be put
    in an unset state and raise an exception on access, because we don't
    know if the value stored in the dbobj still matches the one in the db.
    """
    python_class = None    
    sql_literal_class = None

    def __init__(self, column=None, title=None,
                 validators=(), has_default=False):
        """
        @param column: A t4.orm.sql column instance or a string containing a SQL
            column name pointing to the column this property is
            responsible for. Defaults to the column with the same name
            as the attribute.
        @param title: The title of this column used in dialogs, tables and
            validator error messages (among other things). This must be a
            unicode object or None. 
        @param validators: A sequence of objects of validators.validator
            children. (A single validator is ok, too)
        @param has_default: Boolean property that determines whether this
            dbproperty is retrieved from the database after the dbobject has
            been INSERTed. (So has_default referrs to the SQL column really).
        """
        global _property_counter
        
        if type(column) == StringType or isinstance(column, sql.quotes):
            self.column = sql.column(column)
        elif isinstance(column, sql.column):
            self.column = column
        elif column is None:
            self.column = None
        else:
            raise TypeError("Column must either be a string or an sql.column"+\
                            " instance, not %s (%s)" % ( repr(type(column)),
                                                         repr(column),) )
        self.title = title

        if isinstance(validators, validator):
            self.validators = ( validators, )
        else:
            self.validators = tuple(validators)
                
        self.has_default = has_default

        self.index = _property_counter
        _property_counter += 1

    def __cmp__(self, other):
        return cmp(self.index, other.index)

    def __init_dbclass__(self, dbclass, attribute_name):
        """
        This methods gets called by dbobject's metaclass. It supplies the
        db property with info about the class it belongs to and its attribute
        name. 
        """
        self.dbclass = dbclass
        self.attribute_name = attribute_name
        # The actual data attribute's names start with a space character
        # to avoid name clashes.
        
        if self.column is None:
            self.column = sql.column(attribute_name)
            
        self._data_attribute_name = " %s" % str(self.column)

        if self.title is None:
            self.title = unicode(self.attribute_name, "ascii")
            # It's save to use ascii, because Python does not allow non-ascii
            # identifyers and the attribute_name is an identifyer, of course.

    def data_attribute_name(self):
        try:
            return self._data_attribute_name
        except AttributeError:
            from exceptions import DatatypeMustBeUsedInClassDefinition
            raise DatatypeMustBeUsedInClassDefinition(self.__class__.__name__)
        
    def __get__(self, dbobj, owner="owner? Like owner of what??"):
        """
        See the Python Language Reference, chapter 3.3.2.2 for details on
        how this works. Be sure to be in a relaxed, ready-for-hard-figuring
        mood.
        """
        # The error checking in this method may seem overblown. But there is
        # no such thing as too much information on errors.
        
        if dbobj is None: return self
        self.check_dbobj(dbobj)
            
        if self.isset(dbobj):
            return getattr(dbobj, self.data_attribute_name())
        else:
            if dbobj.__primary_key__ is not None:
                primary_key_property = repr(tuple(
                    dbobj.__primary_key__.attribute_names()))
            else:
                primary_key_property = "<no pkey>"
                
            if dbobj.__primary_key__ is None or \
               not dbobj.__primary_key__.isset():
                pk_literal = "<unset>"
            else:
                pk_literal = repr(tuple(dbobj.__primary_key__.values()))
                    
            tpl = ( self.attribute_name,
                    dbobj.__class__.__name__,
                    primary_key_property,
                    pk_literal, )
            
            msg = "Attribute '%s' of '%s' [ %s=%s ] has not yet been set" % tpl
                
            raise AttributeError( msg )
        
    def __set__(self, dbobj, value):
        """
        Set the attribute managed by this datatype class on instance
        to value.  This will be called by Python on attribute
        assignment. The __set_from_result__ method does the same thing
        for data retrieved from the RDBMS. See below.
        """
        self.check_dbobj(dbobj)

        if isinstance(value, sql.expression):
            setattr(dbobj, " expression" + self.data_attribute_name(), value)
            if self.isset(dbobj):
                # Remove the current value from the dbobj so we don't
                # return a value that's not in sync with the database.
                delattr(dbobj, self.data_attribute_name())                
            dbobj.__register_change__(self)
        else:
            if value is not None: value = self.__convert__(value)

            for validator in self.validators:
                validator.check(dbobj, self, value)

            old = getattr(dbobj, self.data_attribute_name(), StringType)
            setattr(dbobj, self.data_attribute_name(), value)

            if old != value:
                dbobj.__register_change__(self)

    def __set_from_result__(self, ds, dbobj, value):
        setattr(dbobj, self.data_attribute_name(),
                self.__convert__(value))

    def check_dbobj(self, dbobj):
        if self.attribute_name is not None and \
               not self in dbobj.__dbproperties__():
            msg = "dbclass '%s' does not have attribute '%s' (wrong " + \
                  "dbclass for this dbproperty!)"
            msg = msg % ( dbobj.__class__.__name__, self.attribute_name, )
            raise AttributeError(msg)

    def isset(self, dbobj):
        """
        @returns: True, if this property is set, otherwise... well.. False.
        """
        return hasattr(dbobj, self.data_attribute_name())

    def update_expression(self, dbobj):
        """
        The expression this function returns is used in INSERT and UPDATE
        statements to represet this column’s value. May return None. 
        """
        if hasattr(dbobj, " expression" + self.data_attribute_name()):
            return getattr(dbobj, " expression" + self.data_attribute_name())
        else:
            return self.sql_literal(dbobj)

    def select_expression(self, dbclass, full_column_names):
        """
        The expression this function returns is used to SELECT this column
        from the database.
        """
        if full_column_names:
            return sql.column(self.column.name(), dbclass.__relation__,
                              self.column.quote())
        else:
            return self.column
        
    
    def __convert__(self, value):
        """
        Return value converted as a Python object of the class assigned to
        this datatype.
        """
        if value is None:
            return None
        elif not isinstance(value, self.python_class):
            return self.python_class(value)
        else:
            return value

    def sql_literal(self, dbobj):
        """
        Return an SQL literal representing the data managed by this property
        in dbobj.

        @returns: SQL literal as a string.
        """
        if not self.isset(dbobj):
            msg = "This attribute has not been retrieved from the database."
            raise AttributeError(msg)
        else:        
            value = getattr(dbobj, self.data_attribute_name())

            if value is None:
                return sql.NULL
            else:
                return self.sql_literal_class(value)
    
    def __select_after_insert__(self, dbobj):
        """
        Indicate whether this column needs to be SELECTed after the dbobj has
        been inserted to pick up information supplied by backend as by SQL
        default values and auto increment columns.
        """
        return (self.has_default and not self.isset(dbobj))

    def __delete__(self, dbobj):
        raise NotImplementedError(
            "Can't delete a database property from a dbobj.")

    def __repr__(self):
        return "<datatype %s attr:%s column:%s>" % (
            self.__class__.__name__, self.attribute_name, str(self.column), )

class integer(datatype):
    """
    dbclass property for INTEGER SQL columns.
    """    
    python_class = int
    sql_literal_class = sql.integer_literal

class Long(datatype):
    """
    dbclass property for INTEGER SQL columns.
    """    
    python_class = long
    sql_literal_class = sql.integer_literal

class Float(datatype):
    """
    dbclass property for FLOAT and DOUBLE (etc) SQL columns.
    """    
    python_class = float
    sql_literal_class = sql.float_literal

real = Float

class string(datatype):
    """
    dbclass property for TEXT etc. SQL columns.
    """    
    python_class = str
    sql_literal_class = sql.string_literal

    def __init__(self, column=None, title=None,
                 validators=(), has_default=False, null_on_empty=False):
        """
        @null_on_empty: If True, empty strings will be converted to
                        None (i.e. SQL NULL) values on setting. Make sure
                        you don't combine this with a NOT NULL column.
        """
        datatype.__init__(self, column, title, validators, has_default)
        self.null_on_empty = null_on_empty

    def __set__(self, dbobj, value):
        if not isinstance(value, sql.expression) and \
           value is not None and self.null_on_empty and strip(value) == "" :
            value = None
        datatype.__set__(self, dbobj, value)

text = string

class varchar(string):
    """
    dbclass property for string values with a fixed (maximum-)length.
    This is the string class above with a length_validator added.
    """    
    def __init__(self, max_length, column=None, title=None,
                 validators=(), has_default=False, null_on_empty=False):
        validators = list(validators)
        validators.append(length_validator(max_length))
        string.__init__(self, column, title,
                        validators, has_default, null_on_empty)

char = varchar        

class Unicode(string):
    """
    dbclass property for TEXT, VARCHAR, CHAR() etc. SQL columns that
    are to be converted from SQL literals (i.e. encoded strings) to
    Python Unicode objectes and vice versa.

    When setting a Unicode property of a dbobj, you might want to convert
    the value to Unicode yourself. This class uses Python's default encoding
    (see documentation for sys.getdefaultencoding()) to convert things *to*
    Unicode, which may or may not be what you want. 
    """
    python_class = unicode
    sql_literal_class = sql.unicode_literal

    def __set_from_result__(self, ds, dbobj, value):
        if value is not None and type(value) != UnicodeType:
            try:
                value = unicode(value, ds.backend_encoding())
            except TypeError:
                raise TypeError(repr(self) + " " + repr(value))
            
        setattr(dbobj, self.data_attribute_name(), value)

    def __convert__(self, value):
        if type(value) != UnicodeType:
            try:
                return unicode(value)
            except UnicodeDecodeError:
                raise ValueError("This string can't be converted "+\
                  "to unicode using sys.defaultencoding. You must use the "+\
                  "unicode() function with a specific encoding to convert it"+\
                  " or set the default encoding. (%s)" % repr(value))
        else:
            return value


class datetime_base(datatype):
    """
    This is the baseclass for datetime, date, and time. Writing a
    datetime datatype is more intricate matter than one would expect
    on first sight.  The challenges that come with it are, among other
    things:

       - that there are different calendars, Gregorian, Julian, Arabic and
         others, which were/are used historically and locally
       - that time is pretty much linear, but not entirely: There have been
         corrections in history, large and small, as well as leap years and
         seconds
       - There are numerous different conventions on how to write date and
         time, which are even ambiguous.

    SQL backends approach these problems in diverse ways, which must
    be handled by specific classes in the backend's datatype
    module. Fortunately they all share a common denominator which I'm
    trying to work with here.  There are three classes: date, time and
    datetime. On the Python side they use the datetime module (the
    timedelta, date and datetime classes for the time, data and
    datetime datatype respectively). Values provided as mx.DateTime
    instances by the database will be converted. Towards the database
    it will convert these into ISO compliant date representations,
    quoted like SQL string literals. This is going to just work in
    most situations.

    If anyone feels like writing custom datetime datatypes for
    specific backends, mapping Python's new datatypes to PostgreSQL's
    timezone or DateTimeDelta capabilities or MySQL's ability to store
    illegal dates (with 0s in it), they are very welcome!
    """
    def sql_literal(self, dbobj):
        if not self.isset(dbobj):
            msg = "This attribute has not been retrieved from the database."
            raise AttributeError(msg)
        else:        
            value = getattr(dbobj, self.data_attribute_name())

            if value is None:
                return sql.NULL
            else:
                return sql.string_literal(self.datetime_as_string(value))

    def __set_from_result__(self, ds, dbobj, value):
        if value is not None: value = self.__convert__(value)
        datatype.__set_from_result__(self, ds, dbobj, value)

    def __convert__(self, value):
        raise NotImplementedError()

    def datetime_as_string(self, value):
        raise NotImplementedError()
        
        
class datetime(datetime_base):
    """
    Date and time without a timezone.

    See L{datetime_base} for details.
    """
    def datetime_as_string(self, value):
        return str(value)
    
    def __convert__(self, value):
        try:
            return normalize_datetime(value) 
        except TypeError, e:
            raise ValueError("This dbattribute may only be set to "+\
                             "datetime instances of various types, not %s!"%\
                             repr(type(value)))


class date(datetime):
    """
    date (resolution of one day)

    See L{datetime_base} for details.
    """
    def datetime_as_string(self, value):
        return value.strftime("%Y-%m-%d")

    def __convert__(self, value):
        try:
            return normalize_date(value)
        except TypeError:
            raise ValueError("This dbattribute may only be set to "+\
                             "date instances of various types, not %s!" % \
                             repr(value))
        
class time(datetime_base):
    """
    Time of day, 00:00:00 to 23:59:59
    The resolution of the time class is limited to one second.

    See L{datetime_base} for details.
    """
    def datetime_as_string(self, value):
        return value

    def __convert__(self, value):
        if isinstance(value, py_time):
            return value
        elif value is None:
            return None
        else:
            raise ValueError("This dbattribute may only be set to "+\
                             "datetime.time instances, not %s!" % \
                             repr(type(value)))

class boolean(datatype):
    python_class = bool
    sql_literal_class = sql.bool_literal

Boolean = boolean
    
class common_serial(integer):
    """
    The common_serial datatype is an primary key integer column whoes
    value is supplied by the backend using its default mechanism. The
    default mechanism for each backend is defined by the adapter's
    datatype module (see there). The name of the common_serial column is
    alway 'id'.

    This class used by some of the test cases to define data models that
    work on every backend.

       - For gadfly this works on a regular INTEGER column and is not suitable
         for multi user operations (see L{t4.orm.adapters.gadfly.datasource}
         for details)
       - For postgresql this works on a SERIAL column named id.
       - For mysql this works on an INTEGER column with AUTO_INCREMENT set. 
       - For firebird this works with an INTEGER column which is
         combined with a sequence as described U{here
         <http://firebird.sourceforge.net/index.php?op=faq#q0011.dat>}. The
         sequence must be named GEN_PK_<tablename>. This is basically
         the same what L{t4.orm.adapter.firebird.datatypes.serial} does,
         except for the naming scheme for the generator.
    """
    
    def __init__(self):
        datatype.__init__(self, column="id",
                          has_default=True)

    def __init_dbclass__(self, dbclass, attribute_name):
        if attribute_name != "id":
            raise ORMException("All common_serial columns must be called 'id'")
        integer.__init_dbclass__(self, dbclass, "id")

    def __set__(self, dbobj, value):
        raise NotImplementedError("common_serial values are always " + \
                                  "retrieved from the database backend")

    def __set_from_result__(self, ds, dbobj, value):
        integer.__set_from_result__(self, ds, dbobj, value)
        


class _inside_method:
    def __init__(self, instance, method):
        self.instance = instance
        self.method = method
        
    def __call__(self, *args, **kw):
        return self.method(self.instance, *args, **kw)
    
class wrapper(datatype):
    """
    This is the base class for those datatype that are 'wrappers' for regular
    datatypes. This class will forward all attribute access to the inner
    datatype, including method calls. Except for those methods and attributes
    it contains itself.

    All classes derived from wrapper must overload the __copy__ method for
    dbclass inheritance to work properly.
    """
    def __init__(self, inside_datatype):
        self.inside_datatype = inside_datatype

    def __getattribute__(self, name):        
        my_dict = object.__getattribute__(self, "__dict__")
        my_cls = object.__getattribute__(self, "__class__")
        my_cls_dict = my_cls.__dict__
        inside_datatype = object.__getattribute__(self, "inside_datatype")
        
        if my_dict.has_key(name):
            return my_dict[name]
        
        elif my_cls_dict.has_key(name):
            ret = my_cls_dict[name]
            if type(ret) == FunctionType:
                return _inside_method(self, ret)
            else:
                return ret

        elif wrapper.__dict__.has_key(name):
            return _inside_method(self, wrapper.__dict__[name])
        
        elif hasattr(inside_datatype, name):
            return getattr(self.inside_datatype, name)
        
        else:
            raise AttributeError(name)

    def __eq__(self, other):
        """
        This will let the in in L{datatype.check_dbobj} yield True.
        """
        return other == self.inside_datatype

    def __copy__(self):
        raise NotImplementedError( "All classes derived from wrapper must "
                                   "overload the __copy__ method for "
                                   "dbclass inheritance to work properly." )

class delayed(wrapper):
    """
    This is a pseudy-datatype that takes an actual datatype as argument.
    Values from that datatypes's column will not be SELECTed from the database
    regularly, but only on attribute access. This way you can treat a dbclass
    that contains large amount of data just like all the others and only
    load the data at the point in time when it's needed.
    """
    def __init__(self, inside_datatype, cache=False):
        """
        @param inside_datatype: The datatype <b>instance</b> this wrapper is
             responsible for
        @param cache: Parameter that determines whether the data is kept in
             memory once it is loaded from the database
        """
        wrapper.__init__(self, inside_datatype)
        self.cache = cache        

    def __get__(self, dbobj, owner="I don't know what this is for"):
        if dbobj is None: return self
        
        self.check_dbobj(dbobj)
            
        if self.isset(dbobj):
            return getattr(dbobj, self.data_attribute_name())
        else:
            query = sql.select(( self.column, ),
                               dbobj.__relation__,
                               dbobj.__primary_key__.where())
            cursor = dbobj.__ds__().execute(query)
            row = cursor.fetchone()

            if row is None: raise IllegelPrimaryKey() # This shouldn't happen

            value = row[0]

            # The way this is handled is a little strange. Let me explain!
            # The point is, __set_from_result__() may convert the 
            # data retreived from the RDBMS into some other Python
            # representation (t4.orm.util.pickle works that way for instance).
            # So we use the function to do its job and, if we're not supposed
            # to cache the value, *undo* the changes it made on the dbobj.
            # This presumes that the data_attribute_name() mechanism is used
            # by __set_from_result__(), which is relatively save, I guess.
            
            self.inside_datatype.__set_from_result__(dbobj.__ds__(),
                                                     dbobj, value)

            ret = getattr(dbobj, self.data_attribute_name())

            if not self.cache and hasattr(dbobj, self.data_attribute_name()):
                delattr(dbobj, self.data_attribute_name())

            return ret
            
    def select_expression(self, dbclass, full_column_names):
        return None

    def __select_after_insert__(self, *args):
        return False

    def __copy__(self):
        return delayed(copy.copy(self.inside_datatype), self.cache)

class csv(wrapper):
    """
    csv stands for 'comma separated values'. This wrapper takes a
    datatype that represents a string or unicode column (or any other
    datatype that supports split() and join() operations). On getting,
    the database value will be split and the result returned as a
    tuple, on setting the supplied (collection) will be joined. No
    further type checking is performed! Setting a csv attribute to a
    simple string is going to result in m,a,n,y, ,c,o,m,m,a,s in the
    database. Watchout!
    """
    def __init__(self, inside_datatype, separator=","):
        wrapper.__init__(self, inside_datatype)
        self.separator = separator

    def __get__(self, dbobj, owner="I still don't know what this does"):
        value = self.inside_datatype.__get__(dbobj, owner)
        if value is None:
            return None
        else:
            return tuple(split(value, self.separator))

    def __set__(self, dbobj, value):
        if isinstance(value, sql.expression):
            raise TypeError("Can't set csv columns to expressions.")
        value = join(value, self.separator)
        self.inside_datatype.__set__(dbobj, value)

    def __copy__(self):
        return csv(copy.copy(self.inside_datatype), self.separator)
        
class expression(wrapper):
    """
    Insert an arbitrary SQL expression into the SQL query.

    The expression string may contain placeholders $relation, $table
    (which are the same thing) and $attribute_name which will be replaced
    prior to execution by appropriate strings. This is especially usefull
    when using inheritance.

    The has_default and default parameters may be used to supply a
    default value which the expression dbproperty will contain it the
    dbobject has not been SELECTed from the database. Has_default must
    be set to True to use this feature. Default defaults to None ;-)
    """
    def __init__(self, inside_datatype, expression,
                 has_default=False, default=None):
        wrapper.__init__(self, inside_datatype)

        if type(expression) == StringType:
            expression = sql.expression(expression)
            
        if not isinstance(expression, sql.expression):
            msg = ( "You must initialize an expression datatype width an "
                    "sql.expression instance, or a string, "
                    "not %s") % repr(expression)
            raise TypeError(msg)

        self.expression = expression

        self.has_default = has_default
        self.default = default

    def __get__(self, dbobj, owner="I don't know about this"):
        if self.has_default and not self.isset(dbobj):
            return self.default
        else:
            return wrapper.__get__(self, dbobj, owner)

    def __init_dbclass__(self, dbclass, attribute_name):
        wrapper.__init_dbclass__(self, dbclass, attribute_name)
        self.inside_datatype.__init_dbclass__(dbclass, attribute_name)

        exp = self.expression._parts[:]
        exp.insert(0, "(")
        exp.append(") AS ")
        exp.append(self.column)

        # Perform template substitution
        info = { "$relation": str(dbclass.__relation__),
                 "$table": str(dbclass.__relation__),
                 "$attribute": attribute_name }
        
        for key, value in info.items():
            n = []
            for a in exp:
                if type(a) == StringType:
                    parts = a.split(key)
                    parts.reverse()

                    s = []
                    while parts:
                        s.append(parts.pop())
                        if parts: s.append(value)
                    n.append(join(s, ""))
                            
                else:
                    n.append(a)

            exp = n

        identifyer = "%s-identifyer" % self.column.name()
        self._expression = sql.expression(*exp, _identifyer=identifyer)

    def select_expression(self, dbclass, full_column_names):
        return self._expression

    def __copy__(self):
        return expression(self.inside_datatype, self.expression)
    
    def __repr__(self):
        return "<expression of type %s: %s>" % ( repr(self.inside_datatype),
                                                 repr(self._expression), )
        
class property_group(datatype):
    """
    This datatype will manage several columns of the same datatype
    that follow a naming convention. It is mainy indended for database
    tables that store several versions of a string in several columns,
    as for example for applications where you have more than one language.

    Example::

       CREATE TABLE item_category
       (
          id SERIAL,
          name_en TEXT,
          name_de TEXT,

          PRIMARY KEY(id)
       )

    And in Python::

       class item_category:
           id = serial()
           name = datatype_group(Unicode, ('en', 'de',), 'en')

    The datatype_group instance will add one dbproperty to the dbclass for
    each postfix you supply. These are not accessible directly, but the
    datatype_group dbproperty will behave like a Python dictionary::

       lang = 'de'
       category_name = item_category.name[lang]

    The naming convention for the database column goes
    <attribute name>_<postfix>. If you want to use your own column names,
    you may pass a dictionary as the postfixes parameter like::

       { 'p1': sql.column(name1), 'p2': sql.column(name2) }

    In this case the implementation will accept any datatype for the
    postfixes.
    """

    def __init__(self, inside_datatype, postfixes, default_postfix=None,
                 title=None, validators=(), 
                 has_default=False):
        """
        The rest of the params just like L{datatype}.
        
        @param inside_datatype: This is the datatype <b>class</b> for the
            managed attributes.
        @param postfixes: This may either be a tuple of strings, which will be
            used in the column names as described above or a dictionary
            mapping arbitrary keys to column names.
        """
        datatype.__init__(self, None, title, validators, 
                          has_default)
        
        self.inside_datatype = inside_datatype
        self.inside_dbproperty_names = {}
        
        self.postfixes = postfixes
        self.default_postfix = default_postfix

    def __init_dbclass__(self, dbclass, attribute_name):
        datatype.__init_dbclass__(self, dbclass, attribute_name)
        
        if type(self.postfixes) != DictType:
            p = {}
            for postfix in self.postfixes:
                if type(postfix) != StringType:
                    raise TypeError("All postfixes must be strings!")

                if p.has_key(postfix):
                    raise ValueError("The members of the postfixes "
                                     "parameter must be unique.")
                
                p[postfix] = sql.column("%s_%s" % ( attribute_name,
                                                    postfix, ))

            self.postfixes = p
            
        else:
            for postfix, column in self.postfixes:
                if not isinstance(column, sql.column):
                    self.postfixes[postfix] = sql.column(column)


        for postfix, column in self.postfixes.items():
            attr_name = " %s_%s" % ( attribute_name, repr(postfix), )
            dt = self.inside_datatype(column=column,
                                      title=self.title,
                                      validators=self.validators,
                                      has_default=self.has_default)        
            setattr(dbclass, attr_name, dt)
            dt.__init_dbclass__(dbclass, attr_name)
            self.inside_dbproperty_names[postfix] = attr_name


    def inside_dbproperties(self):
        """
        Return a dict as { postfix: <datatype instance> }
        """
        ret = {}
        for postfix, attr_name in self.inside_dbproperty_names.items():
            ret[postfix] = self.dbclass.__dict__[attr_name]

        return ret

    def __get__(self, dbobj, owner=""):
        return self.result(self, dbobj)

    def __set__(self, dbobj, value):
        if type(value) != DictType:
            raise TypeError("%s.%s dbattribute can only be set to a dict!" % \
                            ( self.dbclass.__name__, self.attribute_name, ))

        for postfix, v in value.items():
            if postfix not in self.postfixes:
                raise KeyError("%s not a valid postfix" % repr(postfix))

            property = self.inside_dbproperties()[postfix]
            property.__set__(dbobj, v)

    def __set_from_result__(self, ds, dbobj, value):
        raise NotImplementedError()

    def isset(self, dbobj):
        for property in self.inside_dbproperties().values():
            if property.isset(dbobj):
                return True

        return False

    def sql_literal(self, dbobj):
        return None

    def select_expression(self, dbclass, full_column_names):
        return None

    def __select_after_insert__(self, dbobj):
        return False
    
    class result:
        def __init__(self, parent_dbproperty, dbobj):
            self.parent = parent_dbproperty
            self.dbobj = dbobj

        def __getitem__(self, key):
            if not self.parent.postfixes.has_key(key):
                raise KeyError("Illegal postfix: %s" % repr(key))

            property = self.parent.inside_dbproperties()[key]
            if property.isset(self.dbobj):
                return property.__get__(self.dbobj)
            else:
                if self.parent.default_postfix is not None:
                    pf = self.parent.default_postfix
                    property = self.parent.inside_dbproperties()[pf]
                    if property.isset(self.dbobj):
                        return property.__get__(self.dbobj)
                raise KeyError("No value for %s, default not set" % repr(pf))

            raise KeyError(key)

        def __setitem__(self, key, value):
            if not self.parent.postfixes.has_key(key):
                raise KeyError("Illegal postfix: %s" % repr(key))

            property = self.parent.inside_dbproperties()[key]
            property.__set__(self.dbobj, value)
            

class PDomain(Unicode):
    """
    Just like t4.orm.datatypes.Unicode, except that it doesn't use the
    backend's charset to convert the Unicode string, but Python's idna
    (Internationalized Domain Names in Applications) codec which takes
    care of lowercasing and punicode representation and so on.
    """
    sql_literal_class = sql.idna_literal
    
    def __init__(self, column=None, title=None, validators=(),
                 has_default=False, may_be_emptry=False):
        
        if isinstance(validators, validator): validators = [ validators, ]
        validators = list(validators)
        #validators.append(idna_fqdn_validator(may_be_emptry))
        
        Unicode.__init__(self, column, title, validators,
                         has_default)

    def __set_from_result__(self, ds, dbobj, value): 
        if value is not None and type(value) != UnicodeType:
            value = unicode(value, "idna")
            
        setattr(dbobj, self.data_attribute_name(), value)
        
    def __convert__(self, value):
        if type(value) is not UnicodeType:
            raise TypeError(
                "You must set a PDomain property to a unicode value!")
        else:
            return value


class PEMail(Unicode):
    """
    Like PDomain above, but for e-Mail addresses. The local part will be 
    checked against a regular expression, the remote part will be treated
    like a domain name by the PDomain class above.
    """
    sql_literal_class = sql.idna_literal
    
    def __init__(self, column=None, title=None, validators=(),
                 has_default=False, may_be_empty=False):

        if isinstance(validators, validator): validators = [ validators, ]
        validators = list(validators)
        #validators.append(idna_email_validator(may_be_empty))
        
        Unicode.__init__(self, column, title, validators,
                         has_default)


    def __convert__(self, value):
        if type(value) is not UnicodeType:
            return unicode(value)
            #raise TypeError(
            #    "You must set a PEMail property to a unicode value!")
        else:
            return value
        

class pickle(datatype):
    """
    This datatype uses Python's pickle module to serialize (nearly)
    arbitrary Python objects into a string representation that is then
    stored in a regular database column. See U{http://localhost/Documentation/Python/Main/lib/module-pickle.html} for details on pickling.
    """
    
    def __init__(self, pickle_protocol=cPickle.HIGHEST_PROTOCOL,
                 column=None, title=None,
                 validators=(), has_default=False):
        """
        @param pickle_protocol: Version number of the protocol being used by
           the pickle functions. See U{http://localhost/Documentation/Python/Main/lib/module-pickle.html} for details. 
        """
        self.pickle_protocol = pickle_protocol
        datatype.__init__(self, column, title, validators, 
                         has_default)
        

    def __set_from_result__(self, ds, dbobj, value):
        """
        This method takes care of un-pickling the value stored in the datbase.
        """
        value = cPickle.loads(value)
        setattr(dbobj, self.data_attribute_name(), value)

    def __convert__(self, value):
        """
        Since we store the Python object 'as is', convert does nothing.
        """
        return value

    def sql_literal(self, dbobj):
        """
        This function takes care of converting the Python object into a
        serialized string representation.
        """
        if not self.isset(dbobj):
            msg = "This attribute has not been retrieved from the database."
            raise AttributeError(msg)
        else:        
            value = getattr(dbobj, self.data_attribute_name())

            if value is None:
                return sql.NULL
            else:
                pickled = cPickle.dumps(value, self.pickle_protocol)
                return sql.string_literal(pickled)
    
class python_literal(datatype):
    """
    This datatype is for built-in python datastructures. They will be
    represented as a string when stored using repr() and parsed using
    eval() on retrievel from the database.

    NOTE THAT THIS ENABLES FOREIGN USERS FROM INJECTING EXECUTABLE
    PYTHON CODE INTO YOUR PROGRAM IF THEY HAVE WRITE ACCESS TO THE
    RESPECTIVE DATABASE COLUMNS! 
    """    
    def __init__(self, column=None, title=None,
                 validators=(), has_default=False):
        datatype.__init__(self, column, title, validators, has_default)

    def __set_from_result__(self, ds, dbobj, value):
        """
        This method evaulates the value into a Python datastructure.
        """
        value = eval(value)
        setattr(dbobj, self.data_attribute_name(), value)

    def __convert__(self, value):
        """
        Since we store the Python object 'as is', convert does nothing.
        """
        return value

    def sql_literal(self, dbobj):
        """
        This function takes care of converting the Python object into a
        serialized string representation.
        """
        if not self.isset(dbobj):
            msg = "This attribute has not been retrieved from the database."
            raise AttributeError(msg)
        else:        
            value = getattr(dbobj, self.data_attribute_name())

            if value is None:
                return sql.NULL
            else:
                r = repr(value)
                return sql.string_literal(r)
    
class path(datatype):
    """
    This datatypes allows to store (ZODB or Unix filesystem) paths in
    the database.  On the database side, a TEXT column is assumed, on
    the Python side, a tuple is returned.
    """
    
    def __init__(self, column=None, title=None,
                 validators=(), has_default=False):
        """
        """
        datatype.__init__(self, column, title, validators, 
                         has_default)
        

    def __set_from_result__(self, ds, dbobj, value):
        """
        This method takes care of un-pickling the value stored in the datbase.
        """
        value = tuple(split(value, "/"))
        setattr(dbobj, self.data_attribute_name(), value)

    def __convert__(self, value):
        """
        """
        if type(value) == UnicodeType:
            value = str(value)
            
        if type(value) == StringType:
            return split(value, "/")
        else:
            return tuple(value)

    def sql_literal(self, dbobj):
        """
        This function takes care of converting the Python object into a
        serialized string representation.
        """
        if not self.isset(dbobj):
            msg = "This attribute has not been retrieved from the database."
            raise AttributeError(msg)
        else:        
            value = getattr(dbobj, self.data_attribute_name())

            if value is None:
                return sql.NULL
            else:                
                return sql.string_literal(join(value, "/"))
    
class enum(string):
    """
    Represent an SQL ENUM column.
    """
    def __init__(self, values, column=None, title=None, validators=(),
                 has_default=False):
        string.__init__(self, column, title, validators, False, False)
        self._values = values

    def __set__(self, dbobj, value):
        value = str(value)
        
        if not value in self._values:
            raise ValueError(value)
        else:
            datatype.__set__(self, dbobj, value)
    
