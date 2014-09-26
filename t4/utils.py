#!/usr/bin/env python
# -*- coding: utf-8; -*-

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

import sys, os, os.path as op
from random import random
from string import *
from types import *

def random_password(length=8, use_specials=True):
    letters = "ABCDEFGHJKLMNPQRSTUVWYXZabcdefghijkmnpqrstuvwyxz"
    digits = "123456789"
    letters_and_digits = letters + digits
    specials = "+-/*!&#;"

    if use_specials:
        # Use at least one letter and one special char.
        length -= 2
    
    ret = []
    ret.append(letters[int(random() * len(letters))])
    for a in range(length-1):
        ret.append(letters_and_digits[int(random() * len(letters_and_digits))])

    if use_specials:
        for a in ( digits, specials, ):
            idx = int(random() * (len(ret)-1)) + 1
            ret.insert(idx, a[int(random() * len(a))])

    if len(ret) > length: ret = ret[:length]
    ret = join(ret, "")
    return ret

def slug(length=10):
    return random_password(length, False)

class stupid_dict:
    """
    This class implements the mapping (dict) interface. It uses a
    simple list to store its data and sequential search to access
    it. It does not depend on __hash__() to manage contained
    objects. (See Python Reference Manual Chapter 3.3)

    The actual data is stored in self.data as a list of tuples like
    (key, value).
    """
    def __init__(self, initdata=[]):
        if type(initdata) in (ListType, TupleType,):
            self.data = []
            for tpl in initdata:
                if type(tpl) not in (ListType, TupleType) or len(tpl) != 2:
                    raise ValueError("Cannot inittiate stupid_dict from "+\
                                     "that data")
                else:
                    self.data.append(tpl)
        elif type(initdata) == DictType:
            self.data = initdata.items()
        else:
            raise ValueError("A stupid_dict must be initialized either by "+\
                             "a list of pairs or a regular dictionary.")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, which):
        for key, value in self.data:
            if key == which:
                return value

        if hasattr(self, "default"):
            return self.default
        else:
            raise KeyError(what)

    def __setitem__(self, which, what):
        if self.has_key(which):
            self.__delitem__(which)
            
        self.data.append( (which, what,) )

    def __delitem__(self, which):
        if self.has_key(which):
            idx = self.keys().index(which)
            del self.data[idx]
        else:
            raise KeyError(which)


    def __iter__(self):
        for key, value in self.data: yield key


    def __contains__(self, which):
        return which in self.keys()

    def __cmp__(self, other):
        raise NotImplementedError("I have no idea on how to do this...")
        
    def __eq__(self, other):
        self.data.sort()
        other.data.sort()
        
        if self.data == other.data:
            return True
        else:
            return False

    def __repr__(self):
        return "stupid_dict(%s)" % repr(self.data)

    def clear(self):
        self.data = []

    def copy(self):
        return stupid_dict(self.data[:])

    def get(self, which, default=None):
        if self.has_key(which):
            return self[which]
        else:
            return default

    def has_key(self, which):
        if which in self.keys():
            return True
        else:
            return False

    def items(self):
        return self.data[:]

    def iteritems(self):
        for tpl in self.data: yield tpl

    iterkeys = __iter__
    
    def itervalues(self):
        for key, value in self.data: yield value

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def pop(self):
        raise NotImplementedError("This doesn't make sense in a stupid_dict,"+\
                                  " or does it? No, seriously...")

    popitem = pop

    def setdefault(self, default):
        self.default = default

    def update(self, other):
        """
        Other must implement the mapping (i.e. dict) interface.
        """
        for key, value in other.items():
            self[key] = value

