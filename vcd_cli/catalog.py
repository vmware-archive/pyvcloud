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
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.utils import task_to_dict
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import cli


@cli.group(short_help='work with catalogs')
@click.pass_context
def catalog(ctx):
    """Work with catalogs in current organization.

\b
    Examples
        vcd catalog list
            Get list of catalogs in current organization.
\b
        vcd catalog create 'my catalog' -d 'My Catalog of Templates'
            Create catalog.
\b
        vcd catalog delete 'my catalog'
            Delete catalog.
\b
        vcd catalog info 'my catalog'
            Get details of a catalog.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@catalog.command(short_help='show catalog details')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def info(ctx, name):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        result = None
        catalogs = org.list_catalogs()
        for c in catalogs:
            if c['name'] == name and c['orgName'] == in_use_org_name:
                result = c
                break
        if result is None:
            raise Exception('Catalog not found.')
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='list catalogs')
@click.pass_context
def list(ctx):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        result = org.list_catalogs()
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='create a catalog')
@click.pass_context
@click.argument('name',
                metavar='<catalog-name>')
@click.option('-d',
              '--description',
              required=False,
              default='',
              metavar='[description]')
def create(ctx, name, description):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        result = org.create_catalog(name, description)
        stdout(task_to_dict(result), ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='delete a catalog')
@click.pass_context
@click.argument('name',
                metavar='<catalog-name>')
def delete(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        org.delete_catalog(name)
        stdout('Catalog deleted.', ctx)
    except Exception as e:
        stderr(e, ctx)
