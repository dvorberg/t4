#!/usr/bin/env python
# -*- coding: utf-8; mode: python; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2011 by Diedrich Vorberg <diedrich@tux4web.de>
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
##  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
##  I have added a copy of the GPL in the file COPYING

"""
There are three (significant) ways of storing date/time values in a
Python instance: The datetime module (new in Python 2.5 I belive),
egenix mx.DateTime and Zope's DateTime.DateTime.DateTime
class. (Besides that there is a module called 'time' that provides a
lower level interface to the libc and works with various integer,
string and tuple (i.e. C struct) representations.)

This module's functions will convert any object that has year, month,
day, hour, minute and second attributes or methods to a python object.

* normalize_datetime() will yield a datetime.datetime object.
* normalize_date() will yield a datetime.datee
* normalize_datetime_zope() will yield a DateTime.DateTime.DateTime object.
* normlize_date_zope() is an alias for the above.
"""

# Python
import re, datetime

def normalize_datetime(value):
    """
    Put in pretty much any representation of a date and receive a
    datetime.datetime object.
    """

    if value is None:
        return None
    elif isinstance(value, datetime.datetime):
        return value
    elif hasattr(value, "year") and hasattr(value, "month") \
            and hasattr(value, "day") and hasattr(value, "hour") \
            and hasattr(value, "minute") and hasattr(value, "second"):

        if callable(value.year):
            return datetime.datetime(value.year(),
                                     value.month(),
                                     value.day(),
                                     value.hour(),
                                     value.minute(),
                                     int(value.second()))
        else:
            return datetime.datetime(value.year,
                                     value.month,
                                     value.day,
                                     value.hour,
                                     value.minute,
                                     value.second)
    else:
        raise TypeError(value)

def normalize_date(value):
    """
    Put in pretty much any representation of a date and receive a
    datetime.date object.
    """
    if value is None:
        return None
    elif isinstance(value, datetime.date):
        return value
    elif hasattr(value, "year") and hasattr(value, "month")\
            and hasattr(value, "day"):

        if callable(value.year):
            return datetime.date(value.year(),
                                 value.month(),
                                 value.day())
        else:
            return datetime.date(value.year,
                                 value.month,
                                 value.day)
    else:
        raise TypeError(value)
    
    
# Zope
try:
    try:
        from DateTime.DateTime import DateTime
    except AttributeError:
        raise ImportError
    
    def normalize_datetime_zope(value):
        """
        Put in pretty much any representation of a date and receive a
        DateTime.DateTime.DateTime object.
        """
        if value is None:
            return None
        elif isinstance(value, DateTime):
            return value
        elif hasattr(value, "year") and hasattr(value, "month") \
                and hasattr(value, "day") and hasattr(value, "hour") \
                and hasattr(value, "minute") and hasattr(value, "second"):

            if callable(value.year):
                return DateTime(value.year(),
                                value.month(),
                                value.day(),
                                value.hour(),
                                value.minute(),
                                value.second())
            else:
                return DateTime(value.year,
                                value.month,
                                value.day,
                                value.hour,
                                value.minute,
                                value.second)

        elif hasattr(value, "year") and hasattr(value, "month")\
                and hasattr(value, "day"):

            if callable(value.year):
                return DateTime(value.year(),
                                value.month(),
                                value.day())
            else:
                return DateTime(value.year,
                                value.month,
                                value.day)
        else:
            raise TypeError(value)

    normalize_date_zope = normalize_datetime_zope

except ImportError:
    pass


german_date_re = re.compile(r"(\d+)\.(\d+)\.(\d+)")
def parse_german_date(s):
    match = german_date_re.match(s)
    if match is None:
        raise ValueError("This doesn't seem to be a german date: " + repr(s))
    tpl = map(int, match.groups())
    d, m, y = tpl
    return datetime.date(y, m, d)
    
