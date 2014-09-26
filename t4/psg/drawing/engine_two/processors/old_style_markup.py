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

u"""\
_My old style markup_

This is a slightly updated version of my ‘old style’ markup, a primitive markdown-enspired markup I used a couple of years back. I put his here mainly as a testbed. The following rules apply:

__Syntax__
• Unix(!)-Linefeeds \n —
  (1) A single linefeed is a ‘soft’ paragraph break, think <br>.
  (2) An empty line (two or more consecutive linefeeds) separate paragraphs.
  (3) A single linefeed followed by one or more space/tab characters is
      ignored. This is important for ‘pretty’ source formatting of lists.
• All white space is normalized to one space like in HTML or LaTeX.
• There are limited (wikklytext inspired) inline maarkup options:
  ''bold'', //italic//, ''//bold italic//''
• Headings are lines that have equal numbers of leading and trailing
  underscores. _h1_, __h2__, ___h3___.
• Lists are paragraphs (blocks of text separated by empty lines) whose
  lines start with •, * or -.
  Lists may not be nested. Note that linefeeds followed by space will be
  considered simple space characters.

Emacs has (with some settings) a tendency to leave stray white space in your text file. This may cause some confusion we won’t address here. rstrip()ing each line should do the job, though. 

__Limitations__
This parser is quite primitive. I’m just not much of a computer scientist, so I can’t write a real one. But it does the job for my purposes. The strategy is splitting the input into recognizable parts and do meaningfull stuff with them. Devide and conquer, I guess.

__Poem__
For testing purposes this docstring contains a poem:

___Fog___
//by Carl Sandburg//

The fog comes
on little cat feet.

It sits looking
over harbor and city
on silent haunches
and then moves on.


"""

import re, types
from string import *

from t4.web.typography import normalize_whitespace

# Line feeds followed by regular white-space are considered simple spaces.
ignorable_linefeeds = re.compile(ur"\n[ \t]+")

# A _-marked heading
heading_re = re.compile(ur"((?:^|\n)(_+)(.*?)(_+)(?:\n|$))")

# Blocks are separated by more than one consecutive \n.
block_separator_re = re.compile(ur"\n\n+")

def convert(source):
    """
    Convert `source`, a unicode string formatted as describe in the module
    docstring, to a engine_two.model-tree that can be rendered to PostScript
    using the engine.
    """

    # If the source is not a unicode string, we try to convert it.
    if type(source) != types.UnicodeType:
        source = unicode(str(source))

    # As a means of preparation, we replace linefeeds that we want to
    # ignore with simple spaces.
    source = ignorable_linefeeds.sub(" ", source)

    # Make sure headings are recognized as blocks (i.e. paragraphs)
    source = heading_re.sub(r"\n\1\n", source)

    # Split the whole thing into blocks. There are three types: headings,
    # lists and regular paragraphs.
    block_source = block_separator_re.split(source)

    blocks = map(_block.from_source, block_source)

    for b in blocks:
        print repr(b)

class _block(object):
    """
    A ‘block’ in terms of the old style markup processor is a heading, a
    list or a regular paragraph. Each are rendered into specific
    engine_two.model objects.
    """
    def __init__(self, parts):
        """
        ‘Parts’ of a paragraph are separated by soft new-lines.
        """
        raise NotImplemented()
        
    @classmethod
    def from_source(cls, source):
        """
        Return a heading, list or paragraph object, depending on the input.
        """
        match = heading_re.match(source)
        if match is not None:
            # A heading.
            all, leading, text, trailing, = match.groups()
            level = len(leading)
            return heading(text, level)
        else:
            parts = split(source, "\n")

            is_list = True
            for part in parts:
                if not (len(part) > 0 and part[0] in u"*•-"):
                    is_list = False
                    break

            if is_list:
                return bullet_list(parts)
            else:
                return paragraph(parts)

    def __repr__(self):
        return "<%s with %i parts, '%s…'>" % ( self.__class__.__name__,
                                               len(self.parts),
                                               self.parts[0][:10], )
        
            
class heading(_block):
    def __init__(self, text, level):
        self.text = normalize_whitespace(text)
        self.level = level

    def __repr__(self):
        return "<%s '%s', level=%i>" % ( self.__class__.__name__,
                                         self.text, self.level, )
        
class paragraph(_block):    
    def __init__(self, parts):
        self.parts = map(normalize_whitespace, parts)
    
class bullet_list(paragraph):
    def __init__(self, parts):
        # Remove the bullet character from the parts.
        parts = map(lambda s:s[1:], parts)
        paragraph.__init__(self, parts)

if __name__ == "__main__":
    convert(__doc__)
    
