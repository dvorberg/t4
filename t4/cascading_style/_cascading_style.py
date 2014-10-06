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
This module implements a generic mechanism to style things. Obviously,
it’s somewhat modeled after the w3c’s CSS standard.
"""
import copy

from t4.utils import name_mangling_dict, curried_name_mangling_dict, \
    read_only_dict
from t4.web.title_to_id import title_to_id

import constraints
        
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
    # For documentation of the constraints’ semantics, see the constraints
    # module.

    @classmethod
    def _mangle_key(cls, key):
        """
        Overwrite name_mangling_dict’s abstract method.
        We use title_or_id on all our keys.
        """
        if key == "__default__":
            return "__default__"
        else:
            return title_to_id(key, all_lowercase=False)

    class __metaclass__(type):
        def __new__(cls, name, bases, dict):
            ret = type.__new__(cls, name, bases, dict)

            # Make sure constraints are callable.
            for name, value in ret.__constraints__.items():
                assert callable(value), ValueError(
                    "Constraints must be callable, the one for %s isn’t." % (
                        repr(name)))

            ret.__constraints__ = curried_name_mangling_dict(
                ret._mangle_key, ret.__constraints__)
            
            return ret

    def __init__(self, styles={}, parent=None, name=None):
        """
        The `parent` style is the one we refer to if we can’t find a
        requested attribute in `self`.
        """
        if name is None:
            self._name = "<%s style>" % self.__class__.__name__
        else:
            self._name = name

        if parent: self.update(parent)
        self.update(styles)

    @property
    def name(self):
        return self._name

    def set_name(self, name):
        self._name = name
        
    def __add__(self, other):
        if other is None:
            return self
        elif isinstance(other, mutable_cascading_style):
            constraints = {}
            constraints.update(self.__constraints__)
            constraints.update(other.__constraints__)

            retcls = type("+style", (mutable_cascading_style,),
                          { "__constraints__": constraints })
            return retcls(other, self, self.name + "+" + other.name)
        else:
            # We use our own class as a template.
            other = dict(other)
            return self.__class__(other, self,
                                  "%s+%s" % ( self.name, repr(other), ))

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name, *args):
        key = self._mangle_key(name)
        return dict.__getitem__(self, key)

    def __setitem__(self, name, value):
        constraint = self.__constraints__.get(name, None)
        if constraint is None:
            constraint = self.__constraints__["__default__"]
            
        try:
            result = constraint(name, value)
        except TypeError:
            result = constraint(value)
            
        if isinstance(constraint, constraints.conversion):
            # The constraint will return a value for us to store.
            value = result

        name_mangling_dict.__setitem__(self, name, value)

    def update(self, other):
        for key, value in other.iteritems():
            self[key] = value

    def __getattr__(self, name):
        try:
            return self.__getitem__(title_to_id(name, all_lowercase=False))
        except KeyError, key:
            raise AttributeError(key)
        
    def __setattr__(self, name, value):
        if name.startswith("_"):
            name_mangling_dict.__setattr__(self, name, value)
        else:
            self.__setitem__(title_to_id(name, all_lowercase=False), value)

    def __repr__(self):
        return "<%s %s>" % ( self.__class__.__name__, self.name, )
            
                
class cascading_style(mutable_cascading_style):
    """
    I’d think that mutable styles (especially when close to the root of a
    style tree) may cause some confusion. Usually a cascading style dict
    is defined on instantiation and not changed around afterwards.
    """
    def __init__(self, styles={}, parent=None, name=None):
        mutable_cascading_style.__init__(self, styles, parent, name)
        
        def __setitem__(self, name, value):
            raise TypeError("This style is not mutable.")

        self.__setitem__ = __setitem__
    
if __name__ == "__main__":
    from t4.psg.util import colors

    black = colors.rgb_color(0, 0, 0)
    white = colors.rgb_color(1, 1, 1)
    red   = colors.rgb_color(1, 0, 0)
    green = colors.rgb_color(0, 1, 0)
    blue  = colors.rgb_color(0, 0, 1)

    class test_style(cascading_style):            
        __constraints__ = {
            "__default__": constraints.unknown_property(),
            "font-family": constraints.conversion(str),
            "font-size": constraints.conversion(float),
            "color": constraints.isinstance(colors.color)
        }

    parent_style = test_style({
        "font-family": "Computer Modern Sans Serif",
        "font-size": 12,
        "color": black})
    
    child_style = test_style({"font-family": "Computer Modern Roman"},
                             parent_style)

    try:
        parent_style.font_size = 14
    except TypeError:
        pass
    else:
        raise Exception("These styles should not be mutable.")
    
    # A bunch of basic tests.
    assert parent_style.font_family == "Computer Modern Sans Serif"
    assert child_style.font_family == "Computer Modern Roman"
    assert parent_style.font_size == child_style.font_size and \
      parent_style.font_size == 12

    # Using the + operator.
    result = parent_style + child_style
    assert result.font_family == "Computer Modern Roman"
    

      
