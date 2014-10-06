#!/usr/bin/env python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2014 by Diedrich Vorberg <diedrich@tux4web.de>
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
This module defines classes for constraints used by cascading styles.

The cascading_style’s __constraints__ dict defines the style. Every
attribute’s value will be checked against its corresponsding
constraint. If no constraint for that attribute can be found, the
reserved __default__ constraint is used. In the default form, this
will return True and thus pass the value as acceptable. You may not
remove the default constraint, but define your own returning False and
thus disallowing all attributes not explicitly defined at class
definition time.

A constraint is a function object that will either accept two
arguments (attribute name in normalized form and the value ) or one
(just the value). The former will be tried first, the latter
second. This way you may write constraint functions that deal with
groups of style attributes depending on their name.

A costraint may be a callable instance of a class. The constraint
class below is provided as a common base. The conversion child-class
of constraint is treated specially. Its call-function must return a
value with which the original value is replaced. This way you can
normalize input in type definitions.
The __constraints__ dict will be turned into a read-only

name_mangling_dict after class definition.
"""

import __builtin__

class constraint(object):
    def __call__(self, name, value):
        raise NotImplemented()

class isinstance(constraint):
    """
    Makes sure a give value is an instance of a specified class.
    """
    def __init__(self, class_):
        self._class = class_

    def __call__(self, name, value):
        assert __builtin__.isinstance(value, self._class), \
            ValueError("The %s property must be set to instances of %s" % (
                repr(name), repr(self._class), ))

    
class unknown_property(constraint):
    """
    This could be replaced by

        "__default__": lambda somthing: False

    but readability is a good thing. 
    """
    def __call__(self, name, value):
        raise ValueError("Unknown style property: %s" % repr(name))

class accept_none(constraint):
    """
    This is a constraint wrapper, that passes values that are None.
    """
    def __init__(self, subconstraint):
        self.subconstraint = subconstraint

    def __call__(self, name, value):
        if value is None:
            return None
        else:
            return self.subconstraint(name, value)
    
class one_of(constraint):
    def __init__(self, set_):
        self.set_ = set(set_)

    def __call__(self, name, value):
        assert value in self.set_, ValueError(
            "Value %s not among %s." % ( repr(value),
                                         repr(self.set_), ))

class conversion(constraint):
    """
    A converting constraint will attemt to convert a given value into
    a type acceptable to the type and raise an exception if it cannot
    do so. A style will test a passed value to the converter and store
    the result, rather than just checking the given value.
    """
    def __init__(self, conversion_function):
        self._conversion_function = conversion_function

    def __call__(self, name, value):
        return self._conversion_function(value)

    
class tuple_of(conversion):
    """
    This conversion checks and/or convers collections of things into
    tuples of a specific length and a specific type.
    """
    def __init__(self, count, subconversion):
        self.count = count
        self.subconversion = subconversion

    def __call__(self, name, value):
        assert len(value) == self.count, ValueError(
            "%s must be set to a collection." % repr(name))
        return tuple(map(self.subconversion, value))

