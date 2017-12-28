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
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.utils import to_dict

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='manage EdgeGateways')
@click.pass_context
def edgegateway(ctx):
    """Manage EdgeGateways in vCloud Director.

\b
    Examples
        vcd edgegateway list
            Get list of EdgeGates in current virtual datacenter.
\b
        vcd edgegateway info edgegateway1
            Get details of the ÊdgeGateway 'edgegateway1'
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)

@edgegateway.command('list', short_help='list EdgeGateways')
@click.pass_context
def list_edgegateways(ctx):
     try:
        client = ctx.obj['client']
        result = []
        resource_type = 'edgeGateway'
        q = client.get_typed_query(resource_type,
                                   query_result_format=QueryResultFormat.
                                   ID_RECORDS)
        records = list(q.execute())
        if len(records) == 0:
            result = 'not found'
        else:
            for r in records:
                result.append(to_dict(r, resource_type=resource_type))
        stdout(result, ctx, show_id=False)
     except Exception as e:
        stderr(e, ctx)
