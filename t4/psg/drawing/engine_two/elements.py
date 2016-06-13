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
These classes represent rich text. They contain methods to
calculate information on the objects they represent (size on the page
etc.)  and functions draw them into a box.

The model is a tree of objects.

The root is a richtext objects, which contains 1..n
boxes, which each contain a mix of 1..n boxes and/or paragraphs.
paragraphs, which each contain 1..n
words, which each contain 1..n
syllables.

Note that “word” and “syllable” are technical not linguistic units here.
Refer to the class descriptions below for details.
"""

import types, itertools, collections, unicodedata
from string import *
from t4.utils import here_and_next
import t4.psg.drawing.box

import styles

soft_hyphen_character = unicodedata.lookup("soft hyphen")
hyphen_character = unicodedata.lookup("hyphen")


class _node(list):
    """
    An abstract base class for our node types.
    """
    def __init__(self, *children, **kw):
        """
        The style= argument is currently the only one extracted from kw.
        The argument list must be written in arbitrary form, because
        otherwise the syntax I wanted for the element objects does not
        work. Consequently, style= always needs to be passed as a keyword
        argument.
        """
        self._parent = None
        self._style = kw.get("style", None)
        self._calculated_style = None
        
        for child in children:
            self.append(child)


    def _set_parent(self, parent):
        assert self.parent is None, ValueError(
            "The node %s has already been inserted." % repr(self))
        self._parent = parent
        self._calculated_style = None
        
    @property
    def parent(self):
        return self._parent

    @property
    def style(self):
        if not self._calculated_style:
            assert self._parent is not None, AttributeError(
                "The style attribute is only available after the "
                "parent has been set. (%s)" % repr(self))
            self._calculated_style = self.parent.style + self._style
        return self._calculated_style

        
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

    def __repr__(self):
        return self.__class__.__name__ + ":" + list.__repr__(self)
        

    # Methods from the list class we need to overload.
    def _check_child(self, child):
        raise NotImplemented("The _node class is an abstract base, don’t "
                             "instantiate it at all.")
        
    def append(self, child):
        if not isinstance(child, _node) and \
           isinstance(child, collections.Iterable):
            for a in child:
                self.append(a)
        else:
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

    def _style_info(self):
        if self._parent is None:
            return "_" + repr(self._style)
        else:
            return repr(self.style)

    def __repr__(self):
        return self.__class__.__name__ + " " + self._style_info()
            
    def __print__(self, indentation=0):
        for child in self:
            child.__print__(indentation+1)
            
        
class _container_node(_node):
    """
    A common base class for the richtext (=root node) and the box
    type.
    """
    def render(self, canvas, cursor=None, y=None):
        if y is None:
            y = canvas.h()            

        # If the cursor is set and has an entry for this object,
        # the entry is the index of the last element that has not been
        # completely rendered.
        elements = enumerate(self)
        if cursor and cursor.has_key(id(self)):
            elements = itertools.islice(elements, cursor[id(self)], None)
        else:
            cursor = {}
            
        for index, element in elements:
            space = t4.psg.drawing.box.canvas(canvas, 0, 0, canvas.w(), y)
            canvas.append(space)
            
            y, cursor = element.render(space, cursor)
            if not cursor is None:
                # This element has not been rendered completely.
                cursor[id(self)] = index
                return y, cursor,

        return y, None,
    
            
class richtext(_container_node):
    """
    This is the root node for a richtext tree.
    """
    def __init__(self, *children, **kw):
        style = kw.get("style", None)
        assert style is not None, ValueError(
            "A richtext’s style may not be None.")
        _node.__init__(self, *children, **kw)
    
    def _check_child(self, child):
        assert isinstance(child, box), TypeError(
            "You can only add boxes to a richtext object.")

    @property
    def style(self):
        return self._style

            

class box(_container_node):
    """
    This is a box with margin, padding and background.
    """
    def _check_child(self, child):
        assert isinstance(child, (paragraph, box,)), TypeError(
            "Can’t add %s to a box, only paragraphs and boxes." % repr(child))

    def render(self, canvas, cursor=None):
        def canvas_with_margin(parent, margin):
            if margin == (0, 0, 0, 0,):
                return parent
            else:
                t, r, b, l = margin
                ret =  t4.psg.drawing.box.canvas(
                    parent, l, b, parent.w() - r - l, parent.h() - t - b)
                parent.append(ret)
                return ret

        margin_canvas = canvas_with_margin(canvas, self.style.margin)
        padding_canvas = canvas_with_margin(margin_canvas, self.style.padding)

        if self.style.background:
            raise NotImplementedError("Backgrounds aren’t implemented, yet. "
                                      "Patches welcome!")
            # Draw the background in the padding_canvas

        return _container_node.render(self, padding_canvas, cursor)

class paragraph(_node):
    """
    This is a block of text. Think <div>.
    """
    def _check_child(self, child):
        assert isinstance(child, word), TypeError(
            "Can’t add %s to a paragraph, only texts." % repr(child))

    def render(self, canvas, cursor=None):
        """
        Render this paragraph on `canvas`. The origin is expected to be
        located at the upper(!) left corner of the paragraph.

        The function returns a pair:

          (1) The current vertical postion, that is, the y-coordinate
               of bottom of the last rendered paragraph and        
          (2) When running out of space, this function returns the
              (integer) index of the first word that could not be
              rendered. If all words were rendered, it returns None.
        """
        y = canvas.h()
        last_line_rendered = None
        for line in self.lines(canvas.w(), cursor):
            height = line.height()

            if y - height < 0:
                return y, { "last_line_rendered": last_line_rendered, }
            else:
                print >> canvas, "gsave % paragraph.render()"
                print >> canvas, 0, y, "translate"
                print >> canvas, 0, 0, "moveto"
                line.render(canvas)
                print >> canvas, "grestore % paragraph.render()"
                y -= height
                last_line_rendered = line
                
        return y, None,
        
    def lines(self, width, cursor):
        """
        Yield _line objects for the current paragraph, starting with the
        word at `first_word_idx`, fittet to a box `width`.
        """
        if cursor:
            line = cursor["last_line_rendered"]
        else:
            line = None
            
        while True:
            line = self._line(self, width, line)
            yield line
            if line.last:
                break

    def words_starting_with(self, index):
        """
        Yield pairs as (index, word), starting with the word in self
        at `index`.
        """
        for i, word in enumerate(self[index:]):
            yield index + i, word,
                
    class _line(list):
        """
        This class represents one line of a paragraph and allows to
        render it to a PostScript box (a t4.psg.drawing.box.canvas object).

        @ivar paragraph: The paragraph we’re part of.
        @ivar width: The box’s width we’ve been calculated for.
        @ivar first_word_idx: The index in the paragraph of the first word
           we contain.
        @ivar last_word_idx: Ditto, last word.
        @ivar space_used: Horizontal space used by all our words, including
           intermediate white space.
        @ivar word_space_used: Ditto, w/o the white space.
        @ivar white_space_used: The difference of above two.
        """
        def __init__(self, paragraph, width, previous_line):

            if previous_line is None:
                self.first_word_idx = 0
                words = paragraph.words_starting_with(self.first_word_idx)
            else:
                self.first_word_idx = previous_line.last_word_idx + 1
                words = paragraph.words_starting_with(self.first_word_idx)

                remainder = previous_line.hyphenation_remainder
                if remainder is not None:
                    words = itertools.chain(iter([(previous_line.last_word_idx,
                                                   remainder,),]),
                                            words)

            self.paragraph = paragraph
            self.width = width
            self.hyphenation_remainder = None

            # Ok, let’s see which words fit the width.
            self.space_used = 0.0
            self.word_space_used = 0.0
            self.white_space_used = 0.0

            old_space_width = 0
            for idx, word in words:
                word_width = word.width()

                if word_width > width:
                    # The word is wider than the box we render into.
                    # To avoid an infinet loop, we render it outside the box.
                    word_width = width
                
                space_width = word.space_width()
                
                if self.space_used + old_space_width + word_width <= width:
                    self.space_used += old_space_width
                    old_space_width = space_width
                    
                    space_width = word.space_width()
                    self.append(word)
                    
                    self.space_used += word_width
                    self.word_space_used += word_width
                    self.white_space_used += space_width
                else:
                    # This is where we’d have to ask word, if it can by
                    # hyphenated.
                    fits, remainder = word.hyphenated_at(
                        width - self.space_used - old_space_width)

                    if fits is not None:
                        self.append(fits)
                        self.hyphenation_remainder = remainder

                        word_width = fits.width()
                        self.space_used += word_width
                        self.word_space_used += word_width
                        self.white_space_used += space_width
                        
                    else:
                        # This will put the word we couldn’t fit here on the
                        # next line.
                        idx -= 1

                    break
            
            self.last_word_idx = idx
            self.last = ( idx == len(self.paragraph)-1 and \
                          self.hyphenation_remainder is None)

        def height(self):
            """
            The height of a line is the maximum height of the contained words.
            """
            return max(map(lambda word: word.height(), self))

        def cenders(self):
            """
            Return a tripple of floats, the maximum ascender, median and
            descender of all our syllables.
            """
            # This works exactly as word.cenders() and is a copy.
            cenders = map(lambda word: word.cenders(), self)
            ascenders, medians, descenders = zip(*cenders)
            return max(ascenders), max(medians), max(descenders),

        def render(self, canvas):
            """
            Render this line on `canvas`. This expects the cursor to be
            located at the upper(!) left corner of the line.
            """
            ascender, median, descender = self.cenders()

            print >> canvas, "gsave % line.render()"
            print >> canvas, 0, -self.height(), "translate"
            print >> canvas, 0, 0, "moveto"
            
            # For word.render() to work properly, we need to position the
            # cursor on the baseline, at the beginning of the word.
            def calc_xs(starting):
                """
                Yield the x coordinate for each word on this line starting
                at `string`.
                """
                x = starting
                for word in self:
                    yield x
                    x += word.width() + word.space_width()
                
            
            def left_xs(): return calc_xs(0.0)
            def right_xs(): return calc_xs(self.width - self.space_used)
            def center_xs(): return calc_xs((self.width - self.space_used) / 2)
            
            def justify_xs():
                if self.last:
                    for x in left_xs():
                        yield x
                else:
                    x = 0.0
                    distance = (self.width-self.word_space_used)/(len(self)-1)
                    
                    for word in self:
                        yield x
                        x += word.width() + distance
                
            xs = { "left": left_xs,
                   "right": right_xs,
                   "center": center_xs,
                   "justified": justify_xs, }[self.paragraph.style.text_align] 

            for x, word in zip(xs(), self):
                if x > 0 : print >> canvas, x, 0, "moveto"
                word.render(canvas)
            
            print >> canvas, "grestore % line.render()"

class _wordlike:
    """
    This is a common base class for word (a word of the text) and _wordpart
    (a wraper class used to temporarily store hyphenated words).
    """
    def width(self):
        """
        The width of a word is the sum of the widths of its syllables, duh.
        """
        return sum(map(lambda syllable: syllable.width(), self))

    def cenders(self):
        """
        Return a triplle of floats, the maximum ascender, median and
        descender of all our syllables.
        """
        cenders = map(lambda syllable: syllable.cenders(), self)
        ascenders, medians, descenders = zip(*cenders)
        return max(ascenders), max(medians), max(descenders)

    def height(self):
        """
        The height of a word is the sum of its cenders.
        """
        #return sum(self.cenders())
        return max(map(lambda kid: kid.height(), self))

    def space_width(self):
        """
        Return the width of the space charater in our last syllable’s font
        """
        return self[-1].space_width()
        
    def render(self, canvas):
        """
        Render the word on the canvas (t4.psg.drawing.box.canvas object).
        This function assumes that the baseline is y=0 and that the cursor
        is located at the position of the first letter.
        """
        for syllable in self:
            syllable.render(canvas)

    def hyphenated_at(self, x):
        """
        If this word can by hyphenated (that is, has syllables with
        soft_hyphen set) at a horizontal position <= `x`, this
        function will return a pair of wordpart instances, the first
        of which will render the part of the word before `x`, a hyphen
        and the second the remainder of the word. If the word cannot be
        hyphenated appropriately, this function will return (None, None,).
        """
        minwidth = 0.0
        ret = None, None, 
        for idx, syllable in enumerate(self):
            minwidth += syllable.width()
            if minwidth > x:
                return ret

            if syllable.soft_hyphen:
                if minwidth + syllable.hyphen_width() <= x:
                    ret = ( _wordpart(self[:idx+1], True),
                            _wordpart(self[idx+1:]), )

        return ret


        
class word(_wordlike, _node):
    """
    A ‘word’ is a technical unit. Between words, line wrapping occurs.
    This class inherits most of its actual functionality from _wordlike,
    because it’s identical to the functionality of _wordpart, which is not
    a descendent of _node.
    """
    def __init__(self, *children, **kw):
        _node.__init__(self, *children, **kw)
        self._hyphenated = False
    
    def _check_child(self, child):
        assert isinstance(child, syllable), TypeError(
            "Can’t add %s to a word, only syllables." % repr(child))
        if child.soft_hyphen:
            self._hyphenated = True
            
    def __repr__(self):
        if self._parent is None:
            return _node.__repr__(self) + " NO PARENT"
        else:
            return "%s %.1f×%.1f" % ( _node.__repr__(self),
                                      self.width(), self.height(), )

    def hyphenated_at(self, x):
        if self.style.hyphenator is not None and not self._hyphenated:
            new_syllables = self.style.hyphenator(self)
            if new_syllables is not None:                
                del self[:]
                for a in new_syllables:
                    a._parent = None
                    self.append(a)
                    
            self._hyphenated = True

        return _wordlike.hyphenated_at(self, x)

class _wordpart(_wordlike, list):
    """
    A wordpart is a wrapper around syllables after hyphenation. The
    syllables stay connected to their word, but may be rendered by
    this class.
    """
    def __init__(self, syllables, draw_hyphen=False):
        list.__init__(self, syllables)
        self._draw_hyphen = draw_hyphen

    def width(self):
        width = _wordlike.width(self)

        if self._draw_hyphen:
            return width + self[-1].hyphen_width()
        else:
            return width

    def render(self, canvas):
        for syllable in self[:-1]:
            syllable.render(canvas)
        self[-1].render(canvas, with_hyphen=self._draw_hyphen)
        
        
class syllable(_node):
    """
    A ‘syllable’ is a technical unit. It is the smallest, non-splittable
    collection of letters rendered in one text style. Its sequence argument
    is a unicode string, not a list!
    """    
    def __init__(self, letters, style=None, whitespace_style=None,
                 soft_hyphen=None):
        if type(letters) == types.StringType:
            letters = unicode(letters)

        assert type(letters) == types.UnicodeType, TypeError
        assert letters != u"", ValueError

        if letters[-1] == soft_hyphen_character:
            self._soft_hyphen = True
            letters = letters[:-1]
        else:
            self._soft_hyphen = soft_hyphen

        assert soft_hyphen_character not in letters, ValueError(
            "Soft hyphens are only allowed as the last character of "
            "a syllable.")

        _node.__init__(self, *list(letters), style=style)
        self._whitespace_style = whitespace_style

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
        
    def width(self):
        """
        Return the width of this syllable on the page in PostScript units.
        """
        letters = self.text_transformed()

        return self.font_metrics.stringwidth(
            list(letters),
            self.style.font_size,
            self.style.kerning,
            self.style.char_spacing)

    def text_transformed(self):
        letters = join(self, "")
        
        if self.style.text_transform == "uppercase":
            return letters.upper()
        elif self.style.text_transform == "lowercase":
            return letters.lower()
        else:
            return letters

    def height(self):
        return self.style.line_height

    def cenders(self, pad_for_line_height=True):
        """
        Return a tripple of floats, ascender, median and descender of the
        current font scaled to our text style’s size.
        """
        factor = self.style.font_size / 1000.0
        ascender, descender = ( self.font_metrics.ascender * factor,
                                self.font_metrics.descender * factor, )
        median = self.style.font_size - (ascender + descender)

        if pad_for_line_height:
            padding = ( self.style.line_height - ( self.style.font_size ) ) / 2
            return ascender + padding, median, descender + padding
        else:
            return ascender, median, descender


    def space_width(self):
        """
        Return the with of a space character in our font.
        """
        if self._whitespace_style:
            whitespace_style = self.parent.style + self._whitespace_style
        else:
            whitespace_style = self.parent.style

        # This assumes the font has a space character. If this makes your
        # program crash, the bug is in the font file :-P
        metric = self.font_metrics[32].width # 32 = " "
        return metric * whitespace_style.font_size / 1000.0

    def hyphen_width(self):
        metric = self.font_metrics.get(ord(hyphen_character), None)
        if metric is None:
            metric = self.font_metrics.get("-", None)
            if metric is None:
                return self.space_width()
        
        return metric.width * self.style.font_size / 1000.0
    
    def __repr__(self, indentation=0):
        if self._parent is None:
            return "%s %s NO PARENT" % ( self.__class__.__name__,
                                         repr("".join(self)), )
        else:
            return "%s %s %s %.1f×%.1f" % ( self.__class__.__name__,
                                            repr("".join(self)),
                                            self._style_info(),
                                            self.width(), self.height(), )
        
    def __print__(self, indentation=0):
        print indentation * "  ", repr(self)

        
    def render(self, canvas, with_hyphen=False):
        """
        Render this syllable to `canvas`. This assumes the cursor is located
        right at our first letter.
        """
        font = self.style.font_family.getfont(self.style.text_style,
                                              self.style.font_weight)
        font_wrapper = canvas.page.register_font(font)
        font_size = self.style.font_size        
        
        # We have to set and select the font
        print >> canvas, "/%s findfont" % font_wrapper.ps_name()
        print >> canvas, "%f scalefont" % font_size
        print >> canvas, "setfont"
        print >> canvas, self.style.color

        letters = list(self.text_transformed())

        if with_hyphen:
            letters.append(hyphen_character)
                
        def kerning_for_pairs():
            """
            For each characters in this syllable, return the kerning between
            it and the next character.
            """
            for char, next_ in here_and_next(letters):
                if next_ is None:
                    yield 0.0
                else:
                    yield font_wrapper.font.metrics.kerning_pairs.get(
                        ( char, next_, ), 0.0)

        if self.style.kerning:
            kerning = kerning_for_pairs()
        else:
            kerning = itertools.repeat(0.0)

        spacing = self.style.char_spacing
        char_widths = map(lambda char: font_wrapper.font.metrics.charwidth(
            ord(char), font_size), letters)
        char_offsets = map(lambda (width, kerning,): width + kerning + spacing,
                           zip(char_widths, kerning))
        char_offsets = map(lambda f: "%.2f" % f, char_widths)        
        glyph_representation = font_wrapper.postscript_representation(
            map(ord, letters))
        
        print >> canvas, "(%s) [ %s ] xshow" % ( glyph_representation,
                                                 " ".join(char_offsets), )
        
            
            
