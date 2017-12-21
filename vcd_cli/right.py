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
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with rights')
@click.pass_context
def right(ctx):
    """Work with rights

\b
    Examples
        vcd right list -o myOrg
            Get list of rights in the specified organization
            (defaults to current organization in use).
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@right.command('list',
               short_help='list rights in the specified or current org')
@click.pass_context
@click.option('-o',
              '--org',
              'org_name',
              required=False,
              metavar='<org-name>',
              help='name of the org')
def list_rights(ctx, org_name):
    try:
        client = ctx.obj['client']
        if org_name is None:
            org_name = ctx.obj['profiles'].get('org_in_use')
        org = Org(client, resource=client.get_org_by_name(org_name))
        right_records = org.list_rights()
        for right in right_records:
            del right['href']
        stdout(right_records, ctx)
    except Exception as e:
        stderr(e, ctx)
