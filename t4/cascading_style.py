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
This module implements a generic mechanism to style things. It is obviously
modeled after the w3c’s CSS standard.
"""

from t4.utils import name_mangling_dict, curried_name_mangling_dict, \
    read_only_dict
from t4.web.title_to_id import title_to_id

class converting_constraint(object):
    """
    A converting constraint will attemt to convert a given value into
    a type acceptable to the type and raise an exception if it cannot do
    so. A style will test a passed value to the converter and store the
    result, rather than just checking the given value.
    """
    def __init__(self, conversion_function):
        self._conversion_function = conversion_function

    def __call__(self, value):
        return self._conversion_function(value)

class isinstance_constraint(object):
    """
    Makes sure a give value is an instance of a specified class.
    """
    def __init__(self, class_):
        self._class = class_

    def __call__(self, value):
        assert isinstance(value, self._class), \
            ValueError("This property must be set to instances of "
                       "%s" % self._class.__name__)

class mutable_cascading_style(name_mangling_dict):
    """
    This is a dict-object, that maps attribute names to corresponding
    values. It provides a mechanism to validate the style object and
    construct a style hierarchy in which attributes from supperior
    (“parent”) styles are present in inferior (“child”) styles unless
    they are overwritten.

    Attributes are available through the dict interface (style['attribute']),
    but also as properties (style.attribute). t4.web.title_to_id() is used
    to map attribute keys to property names with all_lowercase=False. This
    means, there is some ambiguity, but styles are case sensitive.

    If you “think” CSS and maybe JavaScript, this means that a cascading_style
    object behaves differently from the Element.style attribute in JavaScript
    DOM objects. There, text-style becomes textStyle (“camelCase”). Here it
    becomes style.text_style. This is more pythonesque (c.f. PEP 8 “Method
    Names and Instance Variables”).
    """

    __constraints__ = {"__default__": lambda obj: True}
    # The __constraints__ dict defines the style. Every attribute’s value
    # will be checked against its corresponsding constraint. If no
    # constraint for that attribute can be found, the reserved __default__
    # constraint is used. In the default form, this will return True and thus
    # pass the value as acceptable. You may not remove the default constraint,
    # but define your own returning False and thus disallowing all attributes
    # not explicitly defined at class definition time.
    #
    # A constraint is a function object that will either accept two arguments
    # (attribute name in normalized form and the value ) or one (just the
    # value). The former will be tried first, the latter second. This way you
    # may write constraint functions that deal with groups of style attributes
    # depending on their name.
    #
    # The __constraints__ dict will be turned into a read-only
    # name_mangling_dict after class definition.

    def _mangle_key(self, key):
        """
        Overwrite name_mangling_dict’s abstract method.
        We use title_or_id on all our keys.
        """
        if key == "__default__":
            return "__default__"
        else:
            return title_to_id(key, all_lowercase=False)

    def __metaclass__(name, bases, dict):
        def normalize_key(key):
            return dict["_mangle_key"](None, key)

        dict["__constraints__"] = curried_name_mangling_dict(
            normalize_key, dict["__constraints__"])

        return type(name, bases, dict)
        
    def __init__(self, parent=None, styles={}):
        """
        The `parent` style is the one we refer to if we can’t find a
        requested attribute in `self`.
        """
        self._parent = parent
        self.update(styles)

    def __getitem__(self, name):
        key = self._mangle_key(name)
        
        if dict.has_key(self, key):
            return dict.__getitem__(self, key)
        else:
            if self._parent is None:
                raise KeyError("Not present in style tree: %s" % repr(name))
            else:
                return self._parent[name]

    def __setitem__(self, name, value):
        print "name =", repr(name), "value =", repr(value)
        
        constraint = self.__constraints__.get(name, "__default__")
        if isinstance(constraint, converting_constraint):
            # The constraint will return a value for us to store.
            value = constraint(value)
        else:
            # The constraint checks the given value.
            constraint(value)

        name_mangling_dict.__setitem__(self, name, value)

    def update(self, other):
        for key, value in other.iteritems():
            self[key] = value
        
                
class cascading_style(mutable_cascading_style):
    """
    I’d think that mutable styles (especially when close to the root of
    a style tree) may cause some confusion. Usually a cascading style
    dict is defined on instantiation and not changed around afterwards.
    """
    def __init__(self, parent=None, styles={}):
        mutable_cascading_style.__init__(self, parent, styles)
        
        def __setitem__(self, name, value):
            raise TypeError("This style is not mutable.")

        # Overwrite this object’s modifying method.
        self.__setitem__ = __setitem__

    
if __name__ == "__main__":
    from t4.psg.util import colors

    red   = colors.rgb_color(1, 0, 0)
    green = colors.rgb_color(0, 1, 0)
    blue  = colors.rgb_color(0, 0, 1)

    def default_constraint(name, value):
        raise ValueError("Unknown style property: %s" % repr(name))
    
    class test_style(cascading_style):            
        __constraints__ = {
            "__default__": default_constraint,
            "font-family": converting_constraint(str),
            "font-size": converting_constraint(float),
            "color": isinstance_constraint(colors.color)
        }
        
    parent_style = test_style(None, {
        "font-family": "Computer Modern Sans Serif",
        "font-size": 12,
        "color": "test"})
    
