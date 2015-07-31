#!/usr/bin/python
# -*- coding: utf-8; -*-

import sys, os, os.path as op, re, unicodedata
from string import *


def ignore_this_name(name):
    return (name.startswith("HEBREW ACCENT") or
            name == "HEBREW POINT METEG")

_is_hebrew_accent = {}
def is_hebrew_accent(char):
    if not _is_hebrew_accent.has_key(char):
        try:
            name = unicodedata.name(char)
        except ValueError:
            return False
        _is_hebrew_accent[char] = ignore_this_name(name)
    return _is_hebrew_accent[char]

def remove_hebrew_accents(line):
    return filter(lambda c: not is_hebrew_accent(c), line)
    
def analyze(text):
    lines = split(text, "\n")
    map(analyze_line, lines)

def print_unicode_names(line):
    for char in line:
        print >> sys.stderr,  unicodedata.name(char)
    
def analyze_line(line):
    line = unicodedata.normalize("NFD", line) # Decompose!
    print_unicode_names(line)
    print >> sys.stderr
    
def main():
    text = sys.stdin.read()
    text = unicode(text, "utf-8")

    analyze(text)
    print
    
    print remove_hebrew_accents(text)

main()    
