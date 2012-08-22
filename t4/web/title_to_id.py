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

# Python
import sys, re
from string import *
from unicodedata import decomposition
from types import StringType, UnicodeType

def asciify(string):
    '''
    "ASCIIfy" a Unicode string by stripping all umlauts, tildes, etc.

    This very cool function originates at
    http://www.physic.ut.ee/~kkannike/english/prog/python/index.html
    ''' 
    temp = u'' 
    for char in string:
        decomp = decomposition(char)
        if decomp: # Not an empty string
            d = decomp.split()[0]
            try:
                temp += unichr(int(d, 16))
            except ValueError:
                if d == "<super>":
                    temp += unichr(int(decomp.split()[1], 16))
                else:
                    pass
                    #raise Exception("Can't handle this: " + repr(decomp))
        else:
            temp += char

    return temp


_reserved_ids = splitfields("""
image_slots edit set get download id fields downloads image images
fields slotinfo store get_image has_image tag image_tag
search translator""")

def title_to_id(title):
    """
    Convert a document title or menu entry to a filename.
    """
    if type(title) == UnicodeType:
        title = asciify(title)
    elif type(title) == StringType:
        title = asciify(unicode(title, "utf-8"))
    elif type(title) != UnicodeType:
        title = str(title)
        
    title = lower(title)
    title = replace(title, u"ß", "ss")
    
    parts = [""]
    for char in title:
        if char in "abcdefghijklmnopqrstuvwxyz0123456789":
            parts[-1] += char
        else:
            if len(parts[-1]) > 0:
                parts.append("")

    if parts[-1] == "":
        parts = parts[:-1]
                
    id = join(parts, "_")
    id = id.encode("ascii", "ignore")
    id = lower(id)

    if id in _reserved_ids:
        id = capitalize(id)
        print "id (cap) =", repr(id)
    
    return id

