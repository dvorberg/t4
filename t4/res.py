#/usr/bin/env python
# -*- coding: utf-8 -*-

##  Copyright 2002-2011 by Diedrich Vorberg <diedrich@tux4web.de>
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

import re
domain_name_re = re.compile("(?:[0-9a-z](?:[0-9a-z-]*[0-9a-z])?\.)+[a-z]{2,6}")
local_part_re = re.compile(r"[-A-Za-z0-9!#$%&'\*+/=\?^_`\{|\}~\.]+")
email_re = re.compile(r"(?:[-A-Za-z0-9!#$%&'\*+/=\?^_`\{|\}~]\.?)*[-A-Za-z0-9!#$%&'\*+/=\?^_`\{|\}~]@(?:[0-9a-z](?:[0-9a-zA-Z-]*[0-9a-zA-Z])?\.)+[a-z]{2,4}")
email_re_groups = re.compile(email_re.pattern.replace("?:", ""))

dotted_quad_re = re.compile(r"(?:\d{1,3})\.(?:\d{1,3})\.(?:\d{1,3})\.(?:\d{1,3})")
dotted_quad_re_groups = re.compile(dotted_quad_re.pattern.replace("?:", ""))

ip_v4_address_re = dotted_quad_re
ip_v4_address_with_mask_re = re.compile(
    ip_v4_address_re.pattern + r"(?:/\d{1,2})?")
ip_v4_address_with_mask_re_groups = re.compile(
    ip_v4_address_with_mask_re.pattern.replace("?:", ""))

crawler_re = re.compile(r"^(?!Mozilla|Opera|Iceweasel)|"
                        r"^Mozilla/5\.0 \(compatible; Googlebot/|"
                        r"^Mozilla/5\.0 \(compatible; Yahoo! Slurp|"
                        r"^Mozilla/5\.0 \(compatible; bingbot")

http_url_re = re.compile("https?://(?:[0-9a-z](?:[0-9a-z-]*[0-9a-z])?\.)+[a-z]{2,6}(/.*)?")
