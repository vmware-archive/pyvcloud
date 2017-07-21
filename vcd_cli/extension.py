# vCloud CLI 0.1
#
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.
#

import click
from lxml import etree
from pyvcloud.vcd.client import QueryResultFormat, _TypedQuery, RelationType, ExtensionServiceQuery
import sys
import traceback
from vcd_cli.vcd import as_metavar
from vcd import cli
from vcd_cli.vcd import OPERATIONS

def ddump(r):
    print etree.tostring(r, pretty_print=True)
    print '------------------------'
    pass

@cli.command(short_help='manage extensions')
@click.pass_context
@click.argument('operation',
                default=None,
                type=click.Choice(OPERATIONS),
                metavar=as_metavar(OPERATIONS)
                )
@click.argument('name',
                metavar='[name]',
                required=False)
def extension(ctx, operation, name):
    """Manages Extension Services on vCloud Director
    """
    try:
        client = ctx.obj['client']
        # admin = client.get_admin()
        # ddump(admin)
        # client.get_query_list()
        # q = get_typed_query('')
        # q = client.get_typed_query('')
        # ext = client.get_extension()
        # ddump(ext)
        # print(ext.Link)
        # es = client.get_linked_resource(ext, RelationType.DOWN, 'application/vnd.vmware.admin.extensionServices+xml')
        # tmp = client.get_resource('https://bos1-vcd-sp-static-199-4.eng.vmware.com/api/admin/extension/service')
        # es = client.get_linked_resource(tmp, 'down:services', 'application/vnd.vmware.vcloud.query.records+xml')
        # q = client.get_resource(ext.get('href')+'/query')
        # ddump(q)
        # q = _TypedQuery('application/vnd.vmware.vcloud.query.records+xml', client, QueryResultFormat.REFERENCES)
        # q.execute()
        # ql = client.get_query_list()
        # admin_href = ctx.obj['profiles'].get('wkep')['ADMIN']
        # q = client.get_resource(admin_href + 'extension/service/query')
        q = ExtensionServiceQuery('?', client, 'idrecords')
        records = q.execute()
        for r in records:
            print(r.get('name'), r.get('exchange'), r.get('enabled'))


        # raise Exception('not implemented')
    except Exception as e:
        print(traceback.format_exc())
        # click.secho('%s' % e,
                    # fg='red', err=True)
        ctx.fail('%s' % e)
