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
##  I have added a copy of the GPL in the file gpl.txt

"""
t4.orm comes with a whole bunch of exception classes, collected in
this module.
"""

from t4.validators import ValidatorException, NotNullError, NotEmptyError,\
    RangeValidatorError, LengthValidatorException, ReValidatorException,\
    DateValidatorException

class ORMException(Exception):
    """
    Base class for all of orm's exceptions
    """

class InternalError(Exception):
    """
    Something inside orm has gone wrong.
    """

class DatasourceClosed(ORMException):
    """
    The datasource was closed.
    """

class IllegalConnectionString(ORMException):
    """
    This exception indicates a syntax error in a connection string
    """

class IllegalPrimaryKey(ORMException):
    pass

class NoSuchAttributeOrColumn(ORMException):
    """
    Er... someone used an dbproperty that doesn't exist
    """

class NoPrimaryKey(ORMException):
    """
    This error is raised if a class does not have a primary key
    (__primary_key__ == None) but some function requires a primary key.
    """

class ObjectMustBeInserted(ORMException):
    """
    To perform the requested operation, the object must have been stored
    in the database.
    """

class ObjectWasNotInserted(ORMException):
    """
    This exception is raised when an object was supposed to be inserted,
    but could not be queried from the database after the INSERT command.
    """

class ObjectAlreadyInserted(ORMException): 
    """
    Relationships may require dbobjects not to have been inserted into
    the database prior to handling them. Also, you can't insert an object
    into a table with a AUTO_INCREMENT column (or simmilar), that has the
    corresponding attribute set already.
    """

class DBObjContainsNoData(ORMException):
    """
    This exception is raised if a dbobj wants to be inserted that has
    none of its attributes set. If you want an empty tuple to be
    inserted to the database (to be filled with default values by the
    backend, for instance) you have to set at least one of the
    db-attributes to None.
    """

class PrimaryKeyNotKnown(ORMException):
    """
    This exception is raised when the select after insert mechanism is
    invoked on an object of which the primary key is not known and cannot
    be determined through the backend.
    """
    
class BackendError(ORMException):
    """
    The backend had something to complain.
    """

class DuplicateKey(ORMException):
    """
    
    """
    
class DatatypeMustBeUsedInClassDefinition(ORMException):
    """
    Most datatypes need to be part of the class definition and cannot
    be added later.
    """
        
class NoDbPropertyByThatName(ORMException):
    """
    Raised by dbobject.__dbproperty__.
    """

class SimplePrimaryKeyNeeded(ORMException):
    """
    Raised if some function expects a single column primary key but a
    multi column primary key is provided.
    """
    
class KeyNotSet(ORMException):
    """
    Raised if a key is not set or not set completely (that is, all of
    its columns)
    """

class IllegalForeignKey(ORMException):
    """
    Raised if a foreign key attribute or set of attributes doesn't match
    the attributes in the other dbclass.
    """

class PasswordsDontMatch(ORMException):
    pass

