#!/usr/bin/python
# -*- coding: utf-8; mode: python; ispell-local-dictionary: "english"; -*-

##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006-12 by Diedrich Vorberg <diedrich@tux4web.de>
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

def rgb(r, g, b):
    return "%f %f %f setrgbcolor" % ( float(r), float(g), float(b), )

def grey(g):
    return "%f setgray" % float(g)

gray = grey
    
def web_color_to_ps_command(color):
    """
    Take a web-compatible hexadecimal tuple as a string and return a
    PostScript command appropriate to set that color.
    """
    # Make sure we have a legal color string
    color = strip(lower(color))

    std_colors = { "white": "ffffff",
                   "black": "000000",
                   "red": "ff0000",
                   "green": "00ff00",
                   "blue": "0000ff" }

    if std_colors.has_key(color):
        color = std_colors[color]

    if color[0] == "#": color = color[1:]
    if len(color) > 6: color = color[:5]
    if len(color) != 6: color += "0" * (6 - len(color))
    
    red = int(color[:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[-2:], 16)

    return rgb( red / 255.0, green / 255.0, blue / 255.0, )

