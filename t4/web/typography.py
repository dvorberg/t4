#!/usr/bin/env python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2011–15 by Diedrich Vorberg <diedrich@tux4web.de>
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
import os, sys, re, cgi, decimal
from string import *
from types import *

def html_quote(content, lang="de"):
    content = cgi.escape(content)
    content = improve_typography(content, lang)
    
    return content

opening_quote_re = re.compile(r'(\s+|^)"([0-9a-zA-Z])')
closing_quote_re = re.compile(r'(\S+)"(\s+|$|[,\.;!])')
opening_single_quote_re = re.compile(r"(\s+|^)'([0-9a-zA-Z])")
closing_single_quote_re = re.compile(r"([^\s']+)'(\s+|$|[,\.;!])")
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
    content = replace(content, u" - ", u" — ")

    # Ellipsis
    content = replace(content, " ...", " …")
    content = replace(content, "...", "…")
    
    return content

def pretty_money(m, form=True):
    if type(m) in (StringType, UnicodeType,):
        try:
            m = german_float(m)
        except ValueError:
            if form:
                return m
            else:
                raise
    
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
    
def german_float(s):
    """
    Parse a string containing a German float-point number (.s separate
    1000s, and decimal comma) into a float.
    """
    if type(s) in ( StringType, UnicodeType,):
        # Replace , with .
        s = s.replace(",", ".")

        # Remove all .s except the last one.
        parts = s.split(".")
        if len(parts) > 2:
            s = ".".join(parts[:-1]) + "." + parts[-1]
        
    return float(s)

def german_integer(s):
    if type(s) == IntType:
        return s
    else:
        s = str(s)
        s = s.replace(".", "")
        return int(s)

german_int = german_integer        
    
def german_decimal(s):
    """
    Parse a string containing a German float-point number (.s separate
    1000s, and decimal comma) into a float.
    """
    # Replace , with .
    s = s.replace(",", ".")

    # Remove all .s except the last one.
    parts = s.split(".")
    if len(parts) > 2:
        s = ".".join(parts[:-1]) + "." + parts[-1]

    try:
        return decimal.Decimal(s)
    except decimal.InvalidOperation:
        raise ValueError()
        
def pretty_german_float(f, decimals=2, form=False):
    """
    Return a German representation of a float point number as a
    string. 
    """
    if type(f) != FloatType and not isinstance(f, decimal.Decimal):
        if form:
            if f is None:
                return ""
            else:
                try:
                    f = german_float(f)
                except ValueError:
                    return f
        else:
            raise TypeError("Don’t know how to convert " + str(type(f)))
        
    # f = float(f) Don’t do that. If this is a decimal.Decimal, we’d loose
    # precision!
    
    if f < 0:
        negative = True
        f *= -1
    else:
        negative = False
        
    s = "%f" % f
    euros, cents = split(s, ".")

    while cents.endswith("0"):
        cents = cents[:-1]

    if cents:
        s = euros + "," + cents
    else:
        s = euros
    
    if negative:
        return "-" + s
    else:
        return s

def pretty_german_integer(i, form=False):
    if not type(i) in (IntType, LongType,) and not isinstance(i, decimal.Decimal):
        if form:
            if i is None:
                return ""
            else:
                i = german_integer(i)
        else:
            raise TypeError(type(i))
    
    s = str(i)
    ret = ""
    while len(s) > 3:
        ret = "." + s[-3:] + ret
        s = s[:-3]

    return s + ret

def pretty_german_date(pit, with_time=False, with_timezone=False):
    """
    Return a pretty representation of this date.
    """
    if pit is None:
        return ""

    if with_time:
        r = "%s.%s.%s %02i:%02i Uhr" % ( pit.day, pit.month, pit.year,
                                         pit.hour, pit.minute, )
    else:
        r = "%s.%s.%s" % ( pit.day, pit.month, pit.year, )

    if with_timezone:
        r += " (%s)" % pit.timezone

    return r
