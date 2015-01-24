#!/usr/bin/env python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2008-12 by Diedrich Vorberg <diedrich@tux4web.de>
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

__docformat__ = "epytext en"

"""
orm's debug module was re-written in one of my brigher moments:

First of all it contains a class called logstream which implements a
subset of Python's file interface. This class is instantiated three
times and the objects are provided as global variables: log, debug and
sql. Each of these have a verbose attribute which determines, it log,
debug or sql information are written to stderr.

Furthermore, the logstream class contains a mechanism to
automatically add options to a Python optparse.option_parser
automatically. Example:

    >>> parser = optparse.OptionParser(doc, version=__version__)
    >>> log.add_option(parser)
    >>> debug.add_option(parser)

resulting in these options:

  -v, --verbose         Be verbose (to stderr)
  -d, --debug           Print debug messages (to stderr)

sql only adds a long --show-sql option if used in this manner. If
you'd like to use other switches you'll have to copy the lines below
over to your program.

"""

import sys, re, time, os.path
from string import *

class logstream(object):
    """    
    Implement a subset of the file interface to be used for status
    messages.  Depending on its verbose flag, the write() method will
    pass its argument to sys.stderr.write() or discard it.
    """
    def __init__(self):
        self.verbose = False
        self.fp = sys.stderr

        self.end = True
        self.timestamp = False
        
    def write(self, s):
        if self.verbose:
            if self.end and self.timestamp:
                self.fp.write(time.strftime("%a, %d %b %Y %H:%M:%S ",
                                            time.gmtime()))

            self.fp.write(s)
            
            if self.end:
                self.fp.flush()

        if s.endswith("\n"):
            self.end = True
        else:
            self.end = False
            
    def flush(self):
        if self.verbose:
            self.fp.flush()

    def __call__(self, *args):
        print >> self, join(map(str, args), " ")
        self.flush()


    def __nonzero__(self):
        """
        Return true if logging is ON, otherwise return False. This is ment
        to be used in if clauses::

           if debug:
              print 'Debug!'
        """
        if self.verbose:
            return True
        else:
            return False
        
    def _make_verbose(self, *args, **kw):
        self.verbose = True        
            
class logfile(logstream):
    def __init__(self, fn=None):
        logstream.__init__(self)
        
        if fn is None:
            me = os.path.basename(sys.argv[0])
            fn = os.path.join("/var/log/%s.log" % me)

        self.fp = open(fn, "a")

class tee(logstream):
    """
    Chain a number of logstreams together (parameters to __init__).
    """
    def __init__(self, *kids):
        logstream.__init__(self)
        self.kids = kids

    def __setattr__(self, name, value):
        logstream.__setattr__(self, name, value)
        if name == "verbose" and hasattr(self, "kids"):
            for kid in self.kids:
                kid.verbose = self.verbose
        
    def write(self, s):
        for kid in self.kids:
            kid.write(s)

    def flush(self):
        for kid in self.kids:
            kid.flush()

    def __setattr__(self, name, value):
        if name == "verbose":
            for kid in getattr(self, "kids", []):
                kid.verbose = value
                
        object.__setattr__(self, name, value)
        
        
        
class _log(logstream):
    def add_option(self, option_parser, short="-v", long="--verbose", ):
        option_parser.add_option(short, long, action="callback",
                                 callback=self._make_verbose,
                                 help="Be verbose (to stderr)")
    def add_argument(self, argument_parser, short="-v", long="--verbose", ):
        argument_parser.add_option([short, long,], type=self._make_verbose,
                                   metavar="", help="Be verbose (to stderr)")
                                     
        
class _debug(logstream):
    def add_option(self, option_parser, short="-d", long="--debug"):
        option_parser.add_option(short, long, action="callback",
                                 callback=self._make_verbose,
                                 help="Print debug messages (to stderr)")
        
    def add_argument(self, argument_parser, short="-d", long="--debug", ):
        argument_parser.add_option([short, long,], type=self._make_verbose,
                                   metavar="", 
                                   help="Print debug messages (to stderr)")
        
class _sql(logstream):
    """
    The _sql class has a logging mechanism that is controlled through
    the buffer_size attribute. If buffer_size is greater than 0, buffer_size
    sql statements will be retained in a list attribute called queries. This
    is used by unit tests to see if queries are generated as expected.
    """
    
    def __init__(self):
        logstream.__init__(self)
        self.buffer_size = 0
        self.queries = []
        
    sql_element_re = re.compile(r"('.*?'|[^ \n]+)", re.DOTALL)
    def normalize_sql_whitespace(self, sql):
        result = self.sql_element_re.findall(sql)
        result = map(lambda s: replace(s, "\n", r"\n"), result)
        return join(result, " ")
    
    def write(self, s):
        t = self.normalize_sql_whitespace(s)
        if s[-1] == "\n":
            s = t + "\n"
        else:
            s = t
            
        logstream.write(self, s)

        s = strip(s)
        if s == "": return

        if self.buffer_size > 0:
            self.queries.append(s)
            if len(self.queries) > self.buffer_size:
                del self.queries[0]

    def reset(self):
        self.queries = []
        
    def add_option(self, option_parser):
        option_parser.add_option(
            "--show-sql", action="callback",
            callback=self._make_verbose,
            help="Log SQL queries and commands (to stderr)")

    def _argparse_callback(self, filename):
        self.verbose = True
        if filename != "-":
            self.fp = open(filename, "a")
        
    def add_argument(self, argument_parser):
        argument_parser.add_argument(
            "--show-sql", action="store_true",
            dest="sqllog", help="Log SQL queries and commands (to stderr)")
        
log = _log()
debug = _debug()
sqllog = _sql()

class dont_log_sql:
    def __enter__(self):
        self.state = sqllog.verbose
        sqllog.verbose = False

    def __exit__(self, type, value, traceback):
        sqllog.verbose = self.state

class do_log_sql:
    def __enter__(self):
        pass
    def __exit__(self, type, value, traceback):
        pass

