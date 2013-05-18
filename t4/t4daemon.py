#!/usr/bin/env python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2011-13 by Diedrich Vorberg <diedrich@tux4web.de>
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

import sys, os, os.path, optparse, traceback

from daemon import daemon
import debug
from t4.orm.datasource import datasource

"""
The t4daemon.t4daemon class adds t4-specific extensions adds
t4.debug.logstream based logging and optparse.OptionParser based
command line handling to t4.daemon.daemon.
"""

class t4daemon(daemon):
    """
    Add your own functionality be implementing the run() method.
    
    self.log and self.debug are t4.debug.logfiles that you can either call
       self.log('My message') or print to print >> self.log, 'My message'.
       
    self.options and self.args contain options and arguments supplied on
       the command line. Provide your own Option Parser by overwriting
       option_parser() and make sure they fit overwriting
       validate_options().

    A python daemon which is its own /etc/init.d/... script will look
    like this:

    class my_daemon(t4daemon):
       def option_parser(self):
          op = t4daemon.option_parser()
          ...
          return op

       def validate_options(self, option_parser, options, args):
          ...
       
       def run(self):
          ...

    my_daemon().init_script()
    
    """
    def __init__(self, pidfile=None,
                 logfile_name=None,
                 stdin="/dev/null",
                 stdout="/dev/null",
                 stderr="/dev/null"):
        daemon.__init__(self, pidfile, stdin, stdout, stderr)

        # The logfile's verbose flag is on by default.
        self.log = debug.logfile(logfile_name)
        self.log.verbose = True

        # Debug has to be turned on explicitly using -d.
        self.dlog = debug.tee(self.log, debug.logstream())
        self.dlog.verbose = True

        self.log.timestamp = True
        self.dlog.timestamp = True
        
    def init_script(self, cmd=None):
        op = self.option_parser()

        if op.get_option("-d") is None:
            short = "-d"
        else:
            short = None

        if op.get_option("--debug") is None:
            long = "--debug"
        else:
            long = None

        if short or long:
            op.add_option(short, long, action="callback",
                          callback=self.dlog,
                          help="Add debug messages to the logfile.")

        self.options, args = op.parse_args()

        if len(args) == 0:
            op.error("Please specify a command as first agument, one of "
                     "start, stop, restart, debug.")
        else:
            cmd = args[0]
            self.args = args[1:]
            
        self.validate_params(op, self.options, self.args)

        daemon.init_script(self, cmd)
        
    def option_parser(self):
        """
        This is called by __init__().
        
        Return a optparse.OptionParser(). You may use your own
        childclass and add your own options by overwriting this
        method. init_script() will automatically add -d/--debug if -d
        and(!) --debug are still available.

        Options and arguments will be available as self.options and
        self.args respectively.
        """
        return optparse.OptionParser()

    def validate_params(self, option_parser, options, args):
        """
        This is called by __init__().
        
        Validate the options/arguments supplied by the user on the
        command line. Use the option_parser's error() method to report
        problems to the user and terminate the process.
        """
        raise NotImplementedError("validate_params")

    def log_traceback(self):
        """
        Write a traceback of the latest exception to self.log.
        """
        traceback.print_exc(file=self.log)

    def debug(self):
        self.log = debug.tee(self.log, debug.logstream())
        self.log.verbose = True
        
        daemon.debug(self)

    
class t4orm_daemon(t4daemon):
    """
    Add functionality to t4daemon to maintain a single t4.orm based
    database connection.

    A t4.orm connection string is passed with the -c command line
    parameter. If you specify the dsn_env_var_name parameter to
    __init__(), -c will default to the content of that variable. 
    """
    def __init__(self, pidfile=None, logfile=None, stdin="/dev/null",
                 stdout="/dev/null", stderr="/dev/null",
                 dsn_env_var_name=None):
        t4daemon.__init__(self, pidfile, logfile, stdin, stdout, stderr)
        self.dsn_env_var_name = dsn_env_var_name
        self._ds = None
        
    def debug(self):
        debug.sqllog.verbose = True
        t4daemon.debug(self)
        
    def ds(self):
        """
        Return a t4.orm.datasource.datasource instance or None, if no
        database connection could be established.
        """
        if self._ds is None or not self._ds.ping():
            try:
                self._ds = datasource(self.options.dsn)
                self.created_new_datasource(self._ds)
            except Exception, e:
                self.log_traceback()
                return None

        return self._ds

    def created_new_datasource(self, ds):
        pass
            
        
    def option_parser(self):
        """
        If you write your own option_parser() method, make sure the
        database connection string ends up in self.options.dsn.
        """
        op = optparse.OptionParser()

        if self.dsn_env_var_name is not None:
            default = os.getenv(self.dsn_env_var_name, None)
        else:
            default = None

        op.add_option("-c", default=default, dest="dsn",
                      help="t4.orm database connection string")

        debug.sqllog.add_option(op)

        return op

    def validate_params(self, op, options, args):
        if not hasattr(options, "dsn") or options.dsn is None:
            op.error("Please provide a database connection string.")
              
