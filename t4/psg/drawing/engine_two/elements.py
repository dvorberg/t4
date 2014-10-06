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
information on the objects they represent (size on the page etc.)
and functions draw them into a box. 

The model is a tree of objects.

The root is a document objects, which contains 1..n
boxes, which each contain a mix of 1..n boxes and/or paragraphs.
paragraphs, which each contain 1..n
texts, which each contain 1..n
words, which each contain 1..n
syllables.

Note that “word” and “syllable” are technical not linguistic units here.
Refer to the class descriptions below for details.
"""

import types, unicodedata
import styles

class _node(list):
    """
    An abstract base class for our node types.
    """
    def __init__(self, children=[], style=None):
        self._parent = None
        self._style = style
        
        for child in children:
            self.append(child)


    def _set_parent(self, parent):
        assert self.parent is None, ValueError(
            "This node has already been inserted.")
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    @property
    def style(self):
        assert self._parent is not None, AttributeError(
            "The style attribute is only available after the "
            "parent has been set.")
        return self.parent.style + self._style

        
    def remove_empty_children(self):
        for child in children:
            child.remove_empty_children()

        i = 0
        while i < len(self):
            if child[i].empty():
                del self[i]
            else:
                i += 1

    def empty(self):
        return len(self) == 0
        

    # Methods from the list class we need to overload.
    def _check_child(self, child):
        raise NotImplemented("The _node class is an abstract base, don’t "
                             "instantiate it at all.")
        
    def append(self, child):
        self._check_child(child)
        child._set_parent(self)
        list.append(self, child)

    def __setitem__(self, key, child):
        self._check_child(child)
        child._set_parent(self)
        list.__setitem__(self, key, child)

    def __setslice__(self, i, j, sequence):
        map(self._check_child, sequence)
        map(lambda child: child._set_parent(self), sequence)
        list.__setslice__(self, i, j, squence)

    def __print__(self, indentation=0):
        print indentation * "  ", self.__class__.__name__, repr(self.style)
        for child in self:
            child.__print__(indentation+1)
            
        

class document(_node):
    """
    This is the root node for a document.
    """
    def __init__(self, base_style, paragraphs):
        _node.__init__(self, paragraphs)
        self._base_style = base_style

    @property
    def style(self):
        """
        The document is the root of the style inheritence mechanism.
        """
        return self._base_style

    def _check_child(self, child):
        assert isinstance(child, box), TypeError
        

class box(_node):
    """
    This is a box with margin, padding and background.
    """
    def _check_child(self, child):
        assert isinstance(child, (paragraph, box,)), TypeError(
            "Can’t add %s to a box, only paragraphs and boxes." % repr(child))

class paragraph(_node):
    """
    This is a block of text. Think <div>.
    """
    def _check_child(self, child):
        assert isinstance(child, text), TypeError(
            "Can’t add %s to a paragraph, only texts." % repr(child))
        
class text(_node):
    """
    ‘Inline’ text node. Think <span>.
    """
    def _check_child(self, child):
        assert isinstance(child, word), TypeError(
            "Can’t add %s to a text, only words." % repr(child))
        
    
class word(_node):
    """
    A ‘word’ is a technical unit. Between words, line wrapping occurs.
    """
    def _check_child(self, child):
        assert isinstance(child, syllable), TypeError(
            "Can’t add %s to a word, only syllables." % repr(child))


class syllable(_node):
    """
    A ‘syllable’ is a technical unit. It is the smallest, non-splittable
    collection of letters rendered in one text style. Its sequence argument
    is a unicode string, not a list!
    """
    soft_hyphen_character = unicodedata.lookup("soft hyphen")
    hyphen_character = unicodedata.lookup("hyphen")
    
    def __init__(self, letters, style=None, soft_hyphen=None):
        if type(letters) == types.StringType:
            letters = unicode(letters)
            
        assert type(letters) == types.UnicodeType, TypeError
        assert letters != u"", ValueError

        if letters[-1] == self.soft_hyphen_character:
            self._soft_hyphen = True
            letters = letters[:-1]
        else:
            self._soft_hyphen = soft_hyphen

        assert self.soft_hyphen_character not in letters, ValueError(
            "Soft hyphens are only allowed as the last character of "
            "a syllable.")

        self.letters = letters
        _node.__init__(self, list(letters), style)

    def append(self, letter):
        self._check_child(letter)
        list.append(self, letter)
        
    def _check_child(self, child):
        assert type(child) == types.UnicodeType, TypeError(
            "Need Unicode letter, not %s" % repr(child))
        
    @property
    def soft_hyphen(self):
        return self._soft_hyphen

    @property
    def font(self):
        ff = self.style.font_family
        return ff.getfont(self.style.text_style,
                          self.style.font_weight)
        
    @property
    def font_metrics(self):
        return self.font.metrics
        
    @property
    def width(self):
        """
        Return the width of this syllable on the page in PostScript units.
        """
        self.font_metrics.stringwidth(
            self.letters,
            self.style.font_size,
            self.style.kerning,
            self.style.char_spacing)

    @property 
    def height(self):
        return self.text_style.line_height

    @property
    def cenders(self):
        """
        Return a pair of floats, ascender and descender of the current font
        scaled to our text style’s size.
        """
        factor = self.text_style.font_size / 1000.0
        return ( self.font_metrics.ascender * factor,
                 self.font_metrics.descender * factor, )

    def __print__(self, indentation=0):
        print indentation * "  ", self.__class__.__name__, "".join(self)
        
