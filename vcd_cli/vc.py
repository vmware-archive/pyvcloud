# VMware vCloud Director CLI
#
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.platform import Platform

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='manage vCenter Servers')
@click.pass_context
def vc(ctx):
    """Manage vCenter Servers in vCloud Director.

\b
    Examples
        vcd vc list
            Get list of vCenter Servers attached to the vCD system.
\b
        vcd vc info vc1
            Get details of the vCenter Server 'vc1' attached to the vCD system.
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@vc.command('list', short_help='list vCenter Servers')
@click.pass_context
def list_vcenters(ctx):
    try:
        platform = Platform(ctx.obj['client'])
        stdout(platform.list_vcenters(), ctx)
    except Exception as e:
        stderr(e, ctx)


@vc.command(short_help='show vCenter details')
@click.pass_context
@click.argument('name')
def info(ctx, name):
    try:
        platform = Platform(ctx.obj['client'])
        stdout(platform.get_vcenter(name), ctx)
    except Exception as e:
        stderr(e, ctx)
