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
from pyvcloud.vcd.client import QueryResultFormat
import sys
import traceback
from vcd_cli import as_metavar
from vcd_cli import cli
from vcd_cli import OPERATIONS

def ddump(r):
    print(etree.tostring(r, pretty_print=True))
    print('---')

def _print(r):
    root = r
    # print('%s %s %s'% (root.tag, root.attrib['id'], root.attrib['name']))
    print(root.tag)
    print(root.attrib['name'])
    print(root.attrib['status'])
    print(root.attrib['orgName'])
    if 'objectName' in root.attrib: print(root.attrib['objectName'])
    print(root.attrib['ownerName'])
    print('---')


@cli.command()
@click.pass_context
@click.argument('operation',
                default=None,
                type=click.Choice(OPERATIONS),
                metavar=as_metavar(OPERATIONS)
                )
@click.argument('name',
                metavar='[name]',
                required=False)
def org(ctx, operation, name):
    """Operations with Organizations"""
    try:
        print('tasks list:\n')
        client = ctx.obj['client']
        q = client.get_typed_query('task', equality_filter=('name', 'CLUSTER_CREATE'), query_result_format=QueryResultFormat.ID_RECORDS)
        qr = q.execute()
        n = 0
        for r in qr:
            n += 1
            _print(r)
    except Exception as e:
        tb = traceback.format_exc()
        click.secho('can\'t retrieve organization: %s' % e,
                    fg='red', err=True)
