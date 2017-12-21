#!/usr/bin/python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2011–17 by Diedrich Vorberg <diedrich@tux4web.de>
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

from string import *
import dns.resolver
from cStringIO import StringIO

def dig(record_type, fqdn, server=None):
    """
    Convenience function wrapper for dns.resolver.Resolver()
    
    @record_type: One of A, TXT, MX, NS
    @fqdn: Host/Domainname to query
    @server: DNS Server to query, defaults to system server

    Returns:
    A -> List of IP addresses
    TXT -> List of strings. (Multiple entries are concatenated with ' '.
           Use lower level dns.resolver functionality for more flexibility!)
    MX -> List of tuples, (preference, 'name', [ip address, ip address],)
    NS -> List of tuples, (name, [ip address, ip address],)

    Raises
    • ValueError if you specify an unknown record type
    • None if there was no result    
    • or anything dns.resolver raises.
    """
    assert record_type in {"A", "TXT", "MX", "NS"}, ValueError
    
    if server is None:
        resolver = dns.resolver.get_default_resolver()
    else:
        resolver = dns.resolver.Resolver(StringIO("nameserver %s" % server))

    try:
        answer = resolver.query(fqdn, record_type)
    except ( dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, ):
        return None

    def name_to_string(name):
        ret = str(name)
        if ret[-1] == ".": ret = ret[:-1]
        return ret

    def mx_tuple(entry):
        return ( entry.preference, name_to_string(entry.exchange),
                 dig("A", entry.exchange, server), )

    def ns_tuple(entry):
        return ( name_to_string(entry), dig("A", entry.target, server), )
        
    if record_type == "A":
        return map(name_to_string, answer)
    if record_type == "TXT":
        return map(lambda entry: join(entry.strings, " "), answer)
    if record_type == "MX":
        return map(mx_tuple, answer)
    if record_type == "NS":
        return map(ns_tuple, answer)
        

if __name__ == "__main__":        
    print dig("A", "www.tux4web.de", "127.0.0.1")
    print dig("TXT", "_acme-challenge.fry.tux4web.de", "127.0.0.1")
    print dig("MX", "tux4web.de", "127.0.0.1")
    print dig("NS", "tux4web.de", "127.0.0.1")



#r = Resolver(StringIO('nameserver 8.8.8.8'))

# Resolver.query()
# qname (dns.name.Name object or string) - the query name
# rdtype (int or string) - the query type
# rdclass (int or string) - the query class
# tcp (bool) - use TCP to make the query (default is False).
# source (IP address in dotted quad notation) - bind to this IP address (defaults to machine default IP).
# raise_on_no_answer (bool) - raise NoAnswer if there's no answer (defaults is True).
# source_port (int) - The port from which to send the message. The default is 0.
#result = r.query("tux4web.de", "MX")

# for mx in result:
#     print mx.preference, type(mx.preference)
#     print mx.exchange, type(mx.exchange)
#     print dir(mx)
#     print mx.to_text()
#     print

    
