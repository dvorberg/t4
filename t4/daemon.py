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

import sys, os, os.path, atexit, signal, time

"""
This module's daemon class is a classic, minimalistic implementation
of a Unix daemon. The t4daemon.t4daemon class adds t4-specific
extensions adds t4.debug.logstream based logging and
optparse.OptionParser based command line handling.
"""

class daemon:
    """
    A generic daemon class.
       
    Usage: subclass the Daemon class and override the run() method.
    """
    def __init__(self, pidfile=None, stdin="/dev/null",
                 stdout="/dev/null", stderr="/dev/null"):
        if pidfile is None:
            me = os.path.basename(sys.argv[0])
            pidfile = "/var/run/%s.pid" % me
            
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self._debug = False
       
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno,
                                                            e.strerror))
            sys.exit(1)
       
        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
       
        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno,
                                                            e.strerror))
            sys.exit(1)
              
        # write pidfile
        try:
            pid = str(os.getpid())
            file(self.pidfile,'w+').write("%s\n" % pid)
        except IOError, e:
            print >> sys.stderr, "Failed to write pid file:", e
            sys.exit(1)
            
        atexit.register(self.delpid)
        
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
       
    def delpid(self):
        os.remove(self.pidfile)
 
    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            try:
                pid = int(pf.read().strip())
            except ValueError:
                pid = None
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
           
        # Start the daemon
        self.startup()
        self.daemonize()
        self.run()
 
    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
       
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart
 
        # Try killing the daemon process       
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
 
    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def debug(self):
        """
        Set self._debug and call self.run().
        """
        self._debug = True
        self.startup()
        self.run()

    def init_script(self, cmd=None):
        """
        Perform the operation specified by CMD. If CMD is None, take
        it from sys.argv[1]. If no parameter was specified on the
        command line, an error message will be issued and the program
        terminates (sys.exit(255)). Supported commands are:

        start
        stop
        restart
        debug

        'debug' will not background the daemon, but set
        self._debug=True and call run() in the foreground.
        """
        def usage():
            print >> sys.stderr, self.usage()
            sys.exit(255)

        if cmd is None:
            if len(sys.argv) == 1: usage()
            cmd = sys.argv[1]

        if cmd == "start": self.start()
        elif cmd == "stop": self.stop()
        elif cmd == "restart": self.stop(); self.start()
        elif cmd == "debug": self.debug()
        else: usage()

    def usage(self):
        return "Usage: %s [optinos] start|stop|restart|debug" % (
            os.path.basename(sys.argv[0]),)

    def startup(self):
        """
        This method is called after __init__() is complete and before
        we're putting ourselves in the background. To implement this
        method is optional.
        """
        
    def run(self):
        """
        You should override this method when you subclass Daemon. It
        will be called after the process has been daemonized by
        start() or restart().
        """
        raise NotImplementedError("run")
