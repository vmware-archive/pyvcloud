# VMware vCloud Director CLI
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

from pyvcloud.vcd.system import System

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with provider virtual datacenters')
@click.pass_context
def pvdc(ctx):
    """Work with provider virtual datacenters in vCloud Director.

\b
    Examples
        vcd pvdc list
            Get list of provider virtual datacenters.
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@pvdc.command('list', short_help='list of provider virtual datacenters')
@click.pass_context
def list_pvdc(ctx):
    try:
        client = ctx.obj['client']
        sys_admin_resource = client.get_admin()
        system = System(client, admin_resource=sys_admin_resource)
        result = []
        for pvdc in system.list_provider_vdcs():
            result.append({'name': pvdc.get('name')})
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)
