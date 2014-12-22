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
import os, sys, re, cgi
from string import *
from types import *

def html_quote(content, lang="de"):
    content = cgi.escape(content)
    content = improve_typography(content, lang)
    
    return content

opening_quote_re = re.compile(r'(\s+|^)"([0-9a-zA-Z])')
closing_quote_re = re.compile(r'([^ ])"(\s+|$)')
opening_single_quote_re = re.compile(r"(\s+|^)'([0-9a-zA-Z])")
closing_single_quote_re = re.compile(r"([^ ])'(\s+|$)")
date_until_re = re.compile(r'(\d+)\.-(\d+)\.')

def improve_typography(content, lang="de"):
    if type(content) == StringType:
        return improve_typography_html(content, lang)
    elif type(content) == UnicodeType:
        return improve_typography_unicode(content, lang)
    else:
        raise TypeError()

def improve_typography_html(content, lang):
    if lang == "de":
        # "gerade" und ,,typografische'' Anführungszeichen    
        content = re.sub(opening_quote_re, r'\1&#132;\2', content)
        content = re.sub(closing_quote_re, r'\1&#147;\2', content)
    elif lang == "en":
        content = re.sub(opening_quote_re, r'\1&#147;\2', content)
        content = re.sub(closing_quote_re, r'\1&#148;\2', content)
    elif lang == "fr":
        content = re.sub(opening_quote_re, r'\1&#171;\2', content)
        content = re.sub(closing_quote_re, r'\1&#187;\2', content)        
    else:
        pass

    # Converts 1.-2. into 1.–2. (with a proper 'until' dash)
    content = re.sub(date_until_re, r'\1.&ndash;\2.', content)

    # Put long dashes where they (might) belog
    content = replace(content, " - ", "&#150;")

    # Ellipsis
    content = replace(content, " ...", "&nbsp;&hellip;")
    content = replace(content, "...", "&hellip;")
    
    return content

def improve_typography_unicode(content, lang):
    if lang == "de":
        # "gerade" und ,,typografische'' Anführungszeichen    
        content = re.sub(opening_quote_re, u"\\1„\\2", content)
        content = re.sub(closing_quote_re, u"\\1“\\2", content)
        content = re.sub(opening_single_quote_re, u"\\1‚\\2", content)
        content = re.sub(closing_single_quote_re, u"\\1‘\\2", content)
    elif lang == "en":
        content = re.sub(opening_quote_re, u"\\1“\\2", content)
        content = re.sub(closing_quote_re, u"\\1”\\2", content)
        content = re.sub(opening_single_quote_re, u"\\1‘\\2", content)
        content = re.sub(closing_single_quote_re, u"\\1’\\2", content)
    elif lang == "fr":
        content = re.sub(opening_quote_re, u"\\1«\\2", content)
        content = re.sub(closing_quote_re, u"\\1»\\2", content)
        content = re.sub(opening_single_quote_re, u"\\1‹\\2", content)
        content = re.sub(closing_single_quote_re, u"\\1›\\2", content)
    else:
        pass

    # Converts 1.-2. into 1.–2. (with a proper 'until' dash)
    content = re.sub(date_until_re, r"\1.–\2.", content)

    # Put long dashes where they (might) belog
    content = replace(content, " - ", " — ")

    # Ellipsis
    content = replace(content, " ...", " …")
    content = replace(content, "...", "…")
    
    return content

def pretty_money(m, form=False):
    if type(m) in (StringType, UnicodeType,): return m
    if m is None:
        return ""
    else:
        if m < 0:
            negative = True
            m *= -1
        else:
            negative = False
            
        s = "%.2f" % m
        euros, cents = map(int, split(s, "."))
        
        if cents == 0 and not form:
            s = str(euros) + ",—"
        else:
            s = "%i,%02i" % ( euros, cents, )

        if negative:
            return "-" + s
        else:
            return s
        
def parse_money(s):
    if strip(s) == "":
        return None
    else:
        s = replace(s, ",\xe2\x80\x94", ",00")
        s = replace(s, ",—", ",00")
        s = replace(s, ",–", ",00")
        s = replace(s, ",-", ",00")
        s = replace(s, ",", ".")
        return float(s)

tag_re = re.compile("<.*?>", re.DOTALL)
def remove_tags(s, substitute=""):
    """
    Remove HTML Tags from a string.
    """
    return tag_re.sub(substitute, s)
    
def pretty_bytes(bytes):
    if bytes < 1024:
        return str(bytes) + " Bytes"
    if bytes < 1024*1024:
        return "%i KB" % (bytes/1024)
    if bytes < 1024*1024*1024:
        return "%.1f MB" % ( float(bytes) / (1024*1024) )
    if bytes < 1024*1024*1024*1024:
        return "%.1f GB" % ( float(bytes) / (1024*1024*1024) )
    else:
        return "%.1f TB" % ( float(bytes) / (1024*1024*1024*1024) )

def normalize_whitespace(s):
    return " ".join(splitfields(s))
    
