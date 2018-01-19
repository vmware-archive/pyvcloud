#
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with rights')
@click.pass_context
def right(ctx):
    """Work with rights

\b
    Note
       All sub-commands execute in the context of organization specified
       via --org option; it defaults to current organization-in-use
       if --org option is not specified.

\b
    Examples
        vcd right list -o myOrg
            Gets list of rights associated with the organization

\b
        vcd right list --all
            Gets list of all rights available in the System

\b
        vcd right add 'vApp: Copy' 'General: View Error Details' -o myOrg
            Adds list of rights to the organization

\b
        vcd rights remove 'vApp: Copy' 'Disk: Create' -o myOrg
            Removes list of rights from the organization
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@right.command('list', short_help='lists rights in the current organization or System')
@click.pass_context
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
@click.option('--all',
              is_flag=True,
              required=False,
              default=False,
              metavar='[all]',
              help='list all rights available in the System')
def list_rights(ctx, org_name, all):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        if all:
            right_records = org.list_rights_available_in_system()
        else:
            right_records = org.list_rights_of_org()
        for right in right_records:
            del right['href']
        stdout(right_records, ctx)
    except Exception as e:
        stderr(e, ctx)

@right.command('add', short_help='Add rights to the organization')
@click.pass_context
@click.argument('rights',
                nargs=-1,
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
def add(ctx, rights, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        org.add_rights(rights)
        stdout("Rights added to the Org \'%s\'" % org_name, ctx)
    except Exception as e:
        stderr(e, ctx)


@right.command('remove', short_help='remove rights from the organization')
@click.pass_context
@click.argument('rights',
                nargs=-1,
                required=True)
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='[org-name]',
              help='name of the org')
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to remove rights from the organization?')
def remove(ctx, rights, org_name):
    try:
        client = ctx.obj['client']
        if org_name is not None:
            org_href = client.get_org_by_name(org_name).get('href')
        else:
            org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, href=org_href)
        org.remove_rights(rights)
        stdout("Rights removed from the Org \'%s\'" % org_name, ctx)
    except Exception as e:
        stderr(e, ctx)

