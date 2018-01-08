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
from pyvcloud.vcd.vdc import VDC

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='manage edge gateways')
@click.pass_context
def gateway(ctx):
    """Manage edge gateways in vCloud Director.

\b
    Examples
        vcd gateway list
            Get list of edge gateways in current virtual datacenter.
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)


@gateway.command('list', short_help='list edge gateways')
@click.pass_context
def list_gateways(ctx):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        result = vdc.list_edge_gateways()
        for e in result:
            del e['href']
        stdout(result, ctx, show_id=False)
    except Exception as e:
        stderr(e, ctx)