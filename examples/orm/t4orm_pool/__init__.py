#!/usr/bin/python

#
# (c) 2011 Diedrich Vorberg <diedrich@tux4web.de>
#

import t4orm_pool
from Products.CMFCore import CMFCorePermissions

def initialize(context):
    context.registerClass (
        t4orm_pool.t4orm_pool,
        permission=CMFCorePermissions.AddPortalContent,
        constructors=(t4orm_pool.manage_addt4orm_pool_form,
                      t4orm_pool.manage_addt4orm_pool),
        icon="skin_files/t4orm_pool.png", )
    
