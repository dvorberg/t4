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

import sys, os, os.path as op, types, subprocess, threading
from random import random
from string import *
from types import *

password_specials = "+-/*!&;$,@"
def random_password(length=8, use_specials=True):
    letters = "ABCDEFGHJKLMNPQRSTUVWYXZabcdefghijkmnpqrstuvwyxz"
    digits = "0123456789"
    letters_and_digits = letters + digits

    ret = []
    ret.append(letters[int(random() * len(letters))])
    for a in range(length-1):
        ret.append(letters_and_digits[int(random() * len(letters_and_digits))])

    if use_specials:
        for a in ( digits, password_specials, ):
            idx = int(random() * (len(ret)-1)) + 1
            ret.insert(idx, a[int(random() * len(a))])

    if len(ret) > length: ret = ret[:length]
    return join(ret, "")

def password_good_enough(password):
    password = str(password)
    
    if len(password) < 8:
        return False
        
    def contains_one_of(s):
        for a in s:
            if a in password:
                return True
        else:
            return False

    return contains_one_of("ABCDEFGHJKLMNPQRSTUVWYXZ") and \
        contains_one_of("abcdefghijkmnpqrstuvwyxz") and \
        contains_one_of("0123456789") and \
        contains_one_of(password_specials) 

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


class name_mangling_dict(dict):
    """
    This dict type changes its keys using its _mangle_key(). Keys
    will also be normalized on access. This creates transparent
    identifyer ambiguity.
    """

    def __init__(self, contents=None):
        """
        The constructor accepts the same types of input as dict’s
        constructur. The input datastructure must have non-ambigious
        keys even after our key normalization applied. Otherwise a
        ValueError is raise.
        """
        dict.__init__(self)
        
        if contents is not None:
            # First, we turn contents into a regular dict to use dict’s
            # constructor to figure out what to do with the datastrcture
            # provided.
            contents = dict(contents)

            # Now we use our __setitem__ function below to set our values,
            # but we make sure the source dict was non-ambigious considering
            # our key normalization. This error checking saved the user
            # from missing supplied values by surprise.
            for key, value in contents.iteritems():
                if self.has_key(key):
                    raise ValueError(("Key %s already present in new "
                                      "name_mangling_dict.") % repr(key))
                else:
                    self[key] = value
            
    def _mangle_key(self, key):
        """
        We do not implement a default mangling.
        """
        raise NotImplementedError()
        
    def __setitem__(self, key, value):
        dict.__setitem__(self, self._mangle_key(key), value)

    def __getitem__(self, key):
        return dict.__getitem__(self, self._mangle_key(key))

    def __delitem__(self, which):
        dict.__delitem__(self, self._mangle_key(key))

    def get(self, key, *args):
        return dict.get(self, self._mangle_key(key), *args)

    def has_key(self, key):
        return dict.has_key(self, self._mangle_key(key))
        
    __contains__ = has_key
        

class curried_name_mangling_dict(name_mangling_dict):
    def __init__(self, mangle_function, contents=None):
        self._mangle_key = mangle_function
        name_mangling_dict.__init__(self, contents)
    
class read_only_dict:
    """
    This is a wrapper arround a regular dict that disallows use of the
    __setitem__() function.
    """
    def __init__(self, dict_):
        self._dict = dict_

    def __setitem__(self, name, value):
        raise TypeError("This is a read-only dict.")

    def __getattr__(self, name):
        return getattr(self._dict, name)
    

def here_and_next(seq, end_marker=None):
    """
    Yield pairs like (seq0, seq1,), (seq1, seq2,), … (seqN, `end_marker`,). 
    """
    iterator = iter(seq)
    here = iterator.next()
    while True:
        try:
            next = iterator.next()
        except StopIteration:
            yield here, end_marker
            break
        else:
            yield here, next        
            here = next

def run_with_timeout(cmd, timeout=25, input=None, creates_output=False):
    """
    Executes cmd using a subprocess (including shell). If `input` is
    provided, it will be piped into the subprocess, if creates_output
    is set, its standard output will be captured and returned.

    @returns: A pair as: The return value from subprocess.communicate() ( 
       a tuple) of various contents and and the (integer) exit code of the
       subprocess. Usage: ((stdout, stderr), retval) = run_with_timeout(…)

    @raises: IOError if the timeout is exceed.
    """
    if type(cmd) == types.ListType:
        cmd = join(cmd, " ")

    d = {}
    if input is not None:
        stdin = subprocess.PIPE
    else:
        stdin = None

    if creates_output:
        stdout = subprocess.PIPE
    else:
        stdout = None
        
    pipe = subprocess.Popen( cmd, shell=True,
                             stdin = stdin,
                             stdout = stdout,
                             stderr = subprocess.PIPE )

    def target():                        
        d["output"] = ( pipe.communicate(input), pipe.returncode, )

    thread = threading.Thread(target=target)
    thread.pipe = pipe

    thread.start()

    thread.join(timeout)

    if thread.is_alive():
        thread.pipe.terminate()
        thread.join()
        raise IOError("Subprocess timeout.")

    return d["output"]

def thumb_size(original_size, maxsize):
    """
    Return a tuple as (width, height) for this image when it is scaled
    down to MAXSIZE from PIL's image.py
    """
    ow, oh = original_size
    mw, mh = maxsize

    if ow < mw and oh < mh:
        # The original image is smaller than maxsize, we have so scale up!
        w = mw
        h = oh * ( mw / ow )
        if h > mh:
            h = mh
            w = ow * ( mh / oh)
    else:    
        w = mw
        h = oh * (mw / ow)
        
        if h > mh:            
            w = ow * (mh / oh)
            h = mh
            
    return (w, h)
