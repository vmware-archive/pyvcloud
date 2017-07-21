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
from vcd_cli.vcd import as_metavar
from vcd_cli.vcd import cli
from vcd_cli.vcd import OPERATIONS
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.client import RelationType



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
        client = ctx.obj['client']
        if operation == 'info':
            my_org = client.get_org()
            click.secho('name: %s' % my_org.attrib['name'])
            click.secho('id: %s ' % my_org.attrib['id'].split(':')[-1])
            click.secho('full name: %s ' % my_org.FullName)
            click.secho('description: %s ' % my_org.Description)
            click.secho('virtual datacenters:')
            for link in get_links(my_org, RelationType.DOWN, EntityType.VDC.value):
                print('  - %s' % link.name)
            click.secho('organization networks:')
            for link in get_links(my_org, RelationType.DOWN, EntityType.ORG_NETWORK.value):
                print('  - %s' % link.name)
            click.secho('catalogs:')
            for link in get_links(my_org, RelationType.DOWN, EntityType.CATALOG.value):
                print('  - %s' % link.name)
        else:
            raise Exception('not implemented')
    except Exception as e:
        tb = traceback.format_exc()
        click.secho('can\'t retrieve organization: %s' % e,
                    fg='red', err=True)
        print(tb)
