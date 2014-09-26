#!/usr/bin/python
# -*- coding: utf-8; mode: python; ispell-local-dictionary: "english"; -*-

##  This file is part of psg, PostScript Generator.
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
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file gpl.txt.

"""
The model module contains classes used to represent the formating of a text.
"""

from t4.psg.util import colors
import backgrounds, lists

class font_style(object):
    """
    Specification of a font as used on the page.    
    """
    def __init__(self, font_wrapper,
                 font_size=10, kerning=True,
                 char_spacing=0.0, line_height=None):
        """
        @param font: psg.document.font_wrapper instance.
        @param font_size: Font size in PostScript units, (default 10).
        @param kerning: Boolean indicating whether to make use of kerning
           information from the font metrics if available.
        @param char_spacing: Space added between each pair of chars,
           in PostScript units.
        @param line_height: Space from one baseline to another, in PostScript
           units. Defaults to 1.5× the font-size. The line height must be
           greater than the font_size.
        """
        self.font_wrapper = font_wrapper
        self.font_size = font_size
        self.kerning = kerning
        self.char_spacing = char_spacing

        if line_height is None:
            line_height = 1.5 * font_size
            
        assert line_height >= font_size, ValueError(
            "The line height must always be larger than the font size.")

        self.line_height = line_height

class text_style(object):    
    def __init__(self, font_style_,
                 color = colors.black,
                 background = backgrounds.none,
                 padding = (0.0, 0.0,)):
        """
        @param font_spec_: An font_style object (see above), describing
            details of how the text shall look on the page.
        @param color: A color object to determin the text’s color.
        @param background: A backgrounds.background object. This color is used
            to draw a box around the text. The box goes from (left padding,
            descent) to (right padding, ascent).
        @param padding: A pair of floats (in PostScript units) as left and
            right padding.
        """
        self.font_style = font_style_
        self.color = color
        self.background = background
        self.padding = padding

class paragraph_style(object):
    def __init__(self,
                 margin = (0.0, 0.0, 0.0, 0.0,),
                 padding = (0.0, 0.0, 0.0, 0.0,),
                 
                 background = backgrounds.none,
                 
                 border_width = (0.0, 0.0, 0.0, 0.0,),
                 border_color = ( colors.transparent,
                                  colors.transparent,
                                  colors.transparent,
                                  colors.transparent, ),
                 
                 list_style = lists.none):
        """
        A paragraph is a box.

        Those four-tuples are in CSS order: top, right, bottom, left.
        
        @param margin: Four-tuple of floats, margin in PostScript units.
            No background will be drawn here
        @param padding: Four-tuple of floats, padding in PostScript units.
            Background will be drawn here, but no text.
        @param background: Background specification, backgrounds.background
            object.
        @param border_width: Four-tuple of floats, border with in PostScript
            units.
        @param border_color: Four-tuple of color objects.
        @param list_style: lists.list_style object for the list style.
        """         
        self.margin = margin
        self.padding = padding
        self.background = background
        self.border_width = border_width
        self.border_color = border_color
        self.list_style = list_style
                 
