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

import sys, re
from string import *
from types import *

class html_length:
    """
    Represent a length in an HTML-compatible way (actually, it's more
    a CSS compatible way).
    """
    length_re = re.compile(r"([0-9\.]+)([a-z]+)?")
    
    def __init__(self, length, unit="px"):
        if type(length) in ( StringType, UnicodeType, ):
            match = self.length_re.match(length)
            l, u = match.groups()
            
            self.length = float(l) # Internally, all math is done with floats
            if u is not None:
                self.unit = u
            else:
                self.unit = unit
        else:
            self.length = float(length)
            self.unit = unit

    def __str__(self):
        if self.unit == "px":
            return "%i%s" % ( int(self.length), self.unit, )
        else:
            return "%.2f%s" % ( self.length, self.unit, )

    def __repr__(self):
        return "<html_length %s>" % ( str(self), ) 

    def _math(self, method_name, other):
        if type(other) in ( FloatType, IntType, ):
            other = html_length(other)
            
        if other.unit != self.unit:
            raise ValueError("Unit mismatch, %s %s" % ( repr(self.unit),
                                                        repr(other.unit), ))
        method = getattr(self.length.__class__, "__" + method_name + "__")
        return html_length(method(self.length, other.length), self.unit)

    def __add__(self, other): return self._math("add", other)
    def __sub__(self, other): return self._math("sub", other)
    def __mul__(self, other): return self._math("mul", other)
    def __div__(self, other): return self._math("div", other)

    def __float__(self): return self.length
    def __int__(self): return int(self.length)
                             
    
class html_area:
    def __init__(self, width, height, unit=None):
        if not isinstance(width, html_length): width = html_length(width)
        if not isinstance(height, html_length): height = html_length(height)

        if unit is None: unit = width.unit        
        if unit != width.unit or unit != height.unit:
            raise ValueError("Unit mismatch")

        self.width = width
        self.height = height
        self.unit = unit

    @classmethod
    def from_size(self, tpl, unit="px"):
        w, h = tpl
        return html_area(w, h, unit)
    
    @classmethod
    def parse_size(self, size_string):
        """
        Takes a string with a valid embed size specification: one of
        the keys in the _sizes dict or a string as '100x100' or so...
        """
        size_string = strip(size_string)
        
        try:
            width, height = split(size_string, "x")
            
            ow, oh = self.original_size()
            if width == "" and height == "":
                return ow, oh
            elif width == "":
                height = int(height)
                width = int(float(height) / float(oh) * float(ow))
            elif height == "":
                width = int(width)
                height = int(float(width) / float(ow) * float(oh))
                
            if width == 0 or height == 0:                    
                raise ValueError("Width and height must be > 0.")
                    
            return html_size(int(width), int(height))
        except TypeError, ValueError:
            raise ValueError(
                "A size string must be a size keyword or have the format 100x100")

    def thumb_size(self, maxsize):
        """
        MAXSIZE is either a pair of numbers, html_length instances or
        another html_area instance. Returns an html_area instance.
        """
        if isinstance(maxsize, html_area):
            maxsize = ( maxsize.width, maxsize.height, )

        # other
        w, h = maxsize
        w = float(w)
        h = float(h)

        # self
        x, y = self.width.length, self.height.length,
        
        if x > w: y = y * w / x; x = w
        if y > h: x = x * h / y; y = h
        
        return html_area(x, y, self.unit)

    scale_to_max = thumb_size
    
    def scale(self, factor):
        return html_area(float(self.width) * factor,
                         float(self.height) * factor, self.unit)
    
    __mul__ = scale

    def css(self):
        if self.unit == "px":
            return "width: %ipx; height: %ipx;" % ( int(self.width),
                                                    int(self.height), )
        else:
            return "width: %.2f%s; height: %.2f%s;" % (
                float(self.width), self.unit,
                float(self.height), self.unit, )

    __str__ = css

    def __repr__(self):
        return "<html_area %.2fx%.2f%s" % ( float(self.width),
                                            float(self.height),
                                            self.unit, )

    def size(self):
        return ( int(self.width), int(self.height), )
            
        
    
