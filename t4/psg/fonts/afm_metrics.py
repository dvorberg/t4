##!/usr/bin/python
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

"""
This module defines afm_metrics. This class implements the metrics
interface as a higher level interface to the AFM file parser from
afm_parser.py.
"""

import sys, re
from string import *
from types import *

from t4.psg.util import *
from afm_parser import parse_afm
from metrics import metrics, glyph_metric
from encoding_tables import *

class global_info(property):
    """
    Property class for properties that can be retrieved directly from
    the parser data.
    """
    def __init__(self, keyword):
        self.keyword = keyword

    def __get__(self, metrics, owner="dummy"):
        return metrics.FontMetrics.get(self.keyword, None)

class afm_metrics(metrics):
    gs_uni_re = re.compile("uni([A-Fa-f0-9]+).*")
    
    def __init__(self, fp):
        """
        @param fp: File pointer of the AFM file opened for reading.
        @raises KeyError: if the font's encoding is not known.
        """
        metrics.__init__(self)
        
        self.FontMetrics = parse_afm(fp)

        try:
            encoding_table = encoding_tables.get(self.encoding_scheme, {})
        except KeyError:
            raise KeyError("Unknown font encoding: %s" % \
                                                repr(self.encoding_scheme))

        # Create a glyph_metric object for every glyph and put it into self
        # indexed by its unicode code.
        char_metrics = self.FontMetrics["Direction"][0]["CharMetrics"]
        need_quote = map(ord, r"\()")
        for char_code, info in char_metrics.iteritems():
            glyph_name = info.get("N", None)

            uni_match = self.gs_uni_re.match(glyph_name)
    
            if glyph_name is None:
                unicode_char_code = encoding_table[char_code]
            elif glyph_name == ".notdef":
                continue
            elif uni_match is not None:
                # This may be a Ghostscript specific convention. No word
                # about this in the standard document.
                unicode_char_code = int(uni_match.groups()[0], 16)
            else:
                try:
                    unicode_char_code = glyph_name_to_unicode[glyph_name]
                except KeyError:
                    continue

            bb = bounding_box.from_tuple(info["B"])
            self[unicode_char_code] = glyph_metric(char_code, 
                                                   info["W0X"],
                                                   glyph_name,
                                                   bb)

        # Create kerning pair index
        try:
            kern_pairs = self.FontMetrics["KernData"]["KernPairs"]

            for pair, info in kern_pairs.iteritems():
                a, b = pair
                key, info0, info1 = info
            
                if key == "KPH":
                    a = encoding_table[a]
                    b = encoding_table[b]
                else:
                    a = glyph_name_to_unicode[a] 
                    b = glyph_name_to_unicode[b]

                kerning = info0

                self.kerning_pairs[ ( a, b, ) ] = kerning
        except KeyError:
            pass
        
    ps_name = global_info("FontName")
    full_name = global_info("FullName")
    family_name = global_info("FamilyName")
    weight = global_info("Weight")
    character_set = global_info("CharacterSet")
    encoding_scheme = global_info("EncodingScheme")
    fontbbox = global_info("FontBBox")
    ascender = global_info("Ascender")
    descender = global_info("Descender")

    def _italic(self):
        if self.FontMetrics.get("ItalicAngle", 0) == 0:
            return False
        else:
            return True

    def _fixed_width(self):
        Direction = self.FontMetrics["Direction"][0]
        if Direction is None:
            return None
        else:
            return Direction.get("IsFixedPitch", False)

    def character_codes(self):
        """
        Return a list of available character codes in font encoding.
        """
        cm = self.FontMetrics["Direction"][0]["CharMetrics"]
        return cm.keys()


    def font_bounding_box(self):
        """
        Return the font bounding box as a bounding_box object in regular
        PostScript units.
        """
        numbers = self.fontbbox
        numbers = map(lambda n: n / 1000.0, numbers)
        return bounding_box.from_tuple(numbers)
