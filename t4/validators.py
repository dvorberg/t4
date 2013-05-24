#/usr/bin/env python
# -*- coding: utf-8 -*-

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
This module defines classes for validating values stored in dbproperties
before they screw up the database or cause a CONSTRAINT error.
"""

from types import *
from string import *

from res import *


class ValidatorException(Exception):
    """
    Parentclass for all those exceptions raised by validators. Those
    exceptions must always contain the dbobj, dbproperty and value
    that caused the exception along with a plausible error message(! ;-)
    This is ment to aid debugging and the creation of even more specific
    error message than a generic validator could contain. (The idea is that
    the message stored in the exception is an error for the programmer,
    the error message for the user will be created from those values).
    """
    def __init__(self, message, dbobj, dbproperty, value):
        """
        @param message: String(!) error message that goes into the regular
           exception object. This is intended for programmers (see above) and
           thus should be generic and in English.
        @param dbobj: The dbobject whoes property was supposed to be set
        @param dbproperty: The actual dbproperty that was supposed to be set
        @param value: A Python object (as opposed to a repr()) of the value
           the dbproperty was supposed to be set to
        """   
        Exception.__init__(self, message)
        self.dbobj = dbobj
        self.dbproperty = dbproperty
        self.value = value

    def __str__(self):
        return self.message # self.__class__.__name__


class NotNullError(ValidatorException):
    """
    Raised by the not_null_validator
    """
    
class NotEmptyError(ValidatorException):
    """
    Raised by the not_empty_validator
    """
    
class RangeValidatorError(ValidatorException):
    """
    Raised by range_check_validator
    """
    
class LengthValidatorException(ValidatorException):
    """
    Raised by length_validator
    """

class ReValidatorException(ValidatorException):
    def __init__(self, msg, dbobj, dbproperty, re, value):
        """
        @param re: The regular expression which has not been matched.
        """
        ValidatorException.__init__(self, msg, dbobj, dbproperty, value)
        self.re = re

class DateValidatorException(ValidatorException):
    def __init__(self, msg, dbobj, dbproperty, value, format):
        """
        @param format: Date format string as for strftime()/strptime()
        """
        ValidatorException.__init__(self, msg, dbobj, dbproperty, value)
        self.format = format
        
class IntValidatorException(ValidatorException):
    pass

class validator:
    """
    The default validator: It doesn't check anything.
    """
    def check(self, dbobj, dbproperty, value):
        pass

class not_null_validator(validator):
    """
    For NOT NULL columns.
    """
    def check(self, dbobj, dbproperty, value):
        if value is None:
            tpl = ( dbobj.__class__.__name__,
                    dbproperty.attribute_name, )
            raise NotNullError("%s.%s may not be NULL (None)" % tpl,
                               dbobj, dbproperty, value)

not_none_validator = not_null_validator # which identifyer makes more sense??


class not_empty_validator(validator):
    """
    For columns which may not contain empty strings.
    """
    def check(self, dbobj, dbproperty, value):
        if type(value) == StringType or type(value) == UnicodeType:
            if value == "":
                tpl = ( dbobj.__class__.__name__,
                        dbproperty.attribute_name, )
                raise NotEmptyError("%s.%s may not be empty" % tpl,
                                    dbobj, dbproperty, value)

class string_validator(validator):
    """
    Makes sure the value is a string.
    """
    def check(self, dbobj, dbproperty, value):
        if type(value) != StringType:
            raise TypeError("String required.")
            
class int_validator(validator):
    """
    Makes sure the value is an integer or can be converted to one.
    """
    def check(self, dbobj, dbproperty, value):
        if value is not None:
            try:
                int(value)
            except ValueError:
                raise IntValidatorException("%s not an integer." % repr(value),
                                            dbobj, dbproperty, value)
            
class length_validator(validator):
    """
    Check an argument value's length. None values will be ignored.
    """
    def __init__(self, max_length):
        self.max_length = max_length
        
    def check(self, dbobj, dbproperty, value):
        if value is not None and len(value) > self.max_length:
            msg = "Length check failed on %s.%s" % (dbobj.__class__.__name__,
                                                    dbproperty.attribute_name,)
            raise LengthValidatorException(msg, dbobj, dbproperty, value)

class range_validator(validator):
    """
    A generic validator for value ranges (fortunately Python doesn't care, it
    can be used for numerals, dates, strings...)
    """
    def __init__(self, lo, hi, include_bounds=False):
        """
        The formula goes::

           lo < value < hi

        if include_bounds is False (the default) or::

           lo <= value <= hi

        otherwise. If above formula is not valid, a RangeValidatorError will
        be raised by check()
        """
        self.lo = lo
        self.hi = hi
        self.include_bounds = include_bounds

    def check(self, dbobj, dbproperty, value):
        if not self.include_bounds:
            if self.lo < value and value < self.hi:
                return
            else:
                message = "Unmatched condition: %s < %s < %s (%s.%s)"
        else:
            if self.lo <= value and value <= self.hi:
                return
            else:
                message = "Unmatched condition: %s <= %s <= %s (%s.%s)"

        tpl = ( repr(self.lo), repr(self.hi), repr(value),
                dbobj.__class__.__name__, dbproperty.attribute_name, )
        raise RangeValidatorException(message % tpl, dbobj, dbproperty, value)

class re_validator(validator):
    """
    Regular expression validator. For strings and Unicode Objects
    """
    def __init__(self, RE):        
        if type(RE) in ( StringType, UnicodeType, ):
            self.re = re.compile(RE)
        else:
            self.re = RE

    def check(self, dbobj, dbproperty, value):
        if value is None:
            return
        
        match = self.re.match(value)

        if match is None:
            if dbproperty:
                tpl = ( repr(value), self.re.pattern,
                        dbobj.__class__.__name__, dbproperty.attribute_name, )
                msg = "%s does not match regular expression %s (%s.%s)" % tpl
            else:
                msg = "%s does not match regular expression %s" % (
                    repr(value), self.re.pattern,)
            raise ReValidatorException(msg, dbobj, dbproperty, self.re, value)


class email_validator(re_validator):
    """
    Check if the value is a valid e-Mail Address using a regular expression.
    Note that the re will not match un-encoded idna Domains, but it will work
    on Unicode strings.
    """
    
    def __init__(self):
        re_validator.__init__(self, email_re)

class url_validator(re_validator):
    """
    Check if the value is a valid (http://-) url.
    """
    
    def __init__(self):
        re_validator.__init__(self, http_url_re)

class fqdn_validator(re_validator):
    """
    Check if the value is a valid fully qualified domain name. Note
    that the rgex used will not match un-encoded idna Domains.
    """
    
    def __init__(self):
        re_validator.__init__(self, domain_name_re)

class idna_fqdn_validator(fqdn_validator):
    """
    Like fqdn_validator above, but for idna Domains (Unicode)
    """
    def __init__(self, may_be_empty):
        fqdn_validator.__init__(self)
        self.may_be_empty = may_be_empty
        
    def check(self, dbobj, dbproperty, value):
        if value is None:
            return
        
        if type(value) != UnicodeType:
            raise TypeError("An idna fqdn must be represented as a " + \
                            "unicode string!")

        if value == "" and self.may_be_empty:
            return True
        
        value = value.encode("idna")
        fqdn_validator.check(self, dbobj, dbproperty, value)


class idna_email_validator(email_validator):
    """
    Like email_validator above, but for idna Domains (Unicode)
    """

    def __init__(self, may_be_empty):
        email_validator.__init__(self)
        self.may_be_empty = may_be_empty
        
    def check(self, dbobj, dbproperty, value):
        if value is None:
            return

        if value == "" and self.may_be_empty:
            return 
        
        if type(value) != UnicodeType:
            raise TypeError("An idna fqdn must be represented as a " + \
                            "unicode string!")

        parts = split(value, "@")
        if len(parts) == 2:
            local_part, remote_part = parts

            try:
                local_part = local_part.encode("ascii")
            except UnicodeDecodeError:
                msg = "The local part of an e-mail address may not contain "+\
                      "non-ascii characters! (Even for an idna Domain!)"
                raise ReValidatorException(msg, dbobj, dbproperty,
                                           self.re, value)
            
            remote_part = remote_part.encode("idna")

            email_validator().check(dbobj, dbproperty,
                                    local_part + "@" + remote_part)
        else:
            tpl = ( repr(value), self.re.pattern,
                    dbobj.__class__.__name__, dbproperty.attribute_name, )
            msg = "%s does not match regular expression %s (%s.%s)" % tpl
            raise ReValidatorException(msg, dbobj, dbproperty, self.re, value)

class ip_address_validator(re_validator):
    """
    Check if the value is a valid e-Mail Address using a regular expression.
    Note that the re will not match un-encoded idna Domains, but it will work
    on Unicode strings.
    """
    
    def __init__(self):
        re_validator.__init__(self, ip_v4_address_with_mask_re)

        
