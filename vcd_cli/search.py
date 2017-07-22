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
from pyvcloud.vcd.client import QueryResultFormat, RelationType
import sys
import traceback
from vcd_cli.vcd import as_metavar
from vcd_cli.vcd import cli
from vcd_cli.vcd import restore_session

def ddump(r):
    print etree.tostring(r, pretty_print=True)
    print '------------------------'
    pass

@cli.command(short_help='search resources')
@click.pass_context
@click.argument('name',
                metavar='[name]',
                required=False)
def search(ctx, name):
    """Search for resources in vCloud Director.

    \b
    Examples
        vcd search vapp
            Search for vApps.
        \b
        vcd search network
            Search for networks.

    """
    try:
        restore_session(ctx)
        client = ctx.obj['client']
        t='adminService'
        q = client.get_typed_query(name, query_result_format=QueryResultFormat.RECORDS)
        records= q.execute()
        print('records:')
        for r in records:
            ddump(r)
            href = r.get('href')
            print(href)
            # ext = client.get_resource(href)
            # ddump(ext)
            # print('  - %s' % (r.get('name')))
            # print(r.get('Enabled'))

        # raise Exception('not implemented')
    except Exception as e:
        print(traceback.format_exc())
        # click.secho('%s' % e,
                    # fg='red', err=True)
        ctx.fail('%s' % e)
