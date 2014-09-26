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
These classes represent rich text. They contain methods to calculate
information on the objects they represent, like size on the page etc.
psg’s font-functions are used to retrieve data from the font files. 
"""

import types
import styles

class node(list):
    """
    A generic class as base for our node types.
    """
    def __init__(self, parent, children):
        self._parent = parent
        assert len(children) > 0, ValueError
        for child in children: self.append(child)

    @property
    def parent(self):
        return self._parent

class document(node):
    """
    This is the root node for a document.
    """
    def __init__(self, paragraphs,
                 default_paragraph_style, default_text_style):
        node.__init__(self, None, paragraphs)

        assert isinstance(styles.paragraph_style,
                          default_paragraph_style), TypeError        
        self._default_paragraph_style = default_paragraph_style

        assert isinstance(styles.text_style, default_text_style), TypeError 
        self._default_text_style = default_text_style

    @property
    def paragraph_style(self):
        return self._default_paragraph_style
    
    @property
    def text_style(self):
        return self._default_text_style
            
class paragraph(node):
    """
    This is a block of text. Think <div>.
    """
    def __init__(self, parent, children, paragraph_style=None, text_style=None):
        node.__init__(self, parent, children)
        
        assert paragraph_style is None or isinstance(
            paragraph_style, styles.paragraph_style), TypeError
        self._paragraph_style = paragraph_style

        assert text_style is None or isinstance(
            text_style, styles.text_style), TypeError
        self._text_style = text_style                

    @property
    def paragraph_style(self):
        return self._default_paragraph_style or self.parent.paragraph_style

class _node_with_text_style(node):
    def __init__(self, parent, children, text_style=None):
        node.__init__(self, parent, children)

        assert text_style is None or isinstance(
            style, styles.text_style), TypeError
        
        self._text_style = text_style

    @property
    def text_style(self):
        return self._default_text_style or self.parent.text_style
        
        
class text(_node_with_text_style):
    """
    ‘Inline’ text node. Think <span>.
    """
    pass
    
class word(_node_with_text_style):
    """
    A ‘word’ is a technical unit. Between words, line wrapping occurs.
    """
    pass

class syllable(_node_with_text_style):
    """
    A ‘syllable’ is a technical unit. It is the smallest, non-hyphenatble
    collection of letters we care about. It’s collection argument is a
    string, not a list!
    """
    def __init__(self, parent, letters, text_style=None):
        assert type(letters) == types.UnicodeType, TypeError        
        node.__init__(self, parent, list(letters))
        

