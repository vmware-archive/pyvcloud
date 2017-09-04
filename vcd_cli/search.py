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
from pyvcloud.vcd.client import RESOURCE_TYPES
from pyvcloud.vcd.utils import to_camel_case
from pyvcloud.vcd.utils import to_dict
from tabulate import tabulate
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.utils import tabulate_names
from vcd_cli.vcd import vcd


@vcd.command(short_help='search resources')
@click.pass_context
@click.argument('resource_type',
                metavar='[resource-type]',
                required=False)
@click.option('-f',
              '--filter',
              'query_filter',
              required=False,
              metavar='[query-filter]',
              help='query filter')
def search(ctx, resource_type, query_filter):
    """Search for resources in vCloud Director.

\b
    Description
        Search for resources of the provided type. Resource type is not case
        sensitive. When invoked without a resource type, list the available
        types to search for. Admin types are only allowed when the user is
        the system administrator.
\b
        Filters can be applied to the search.
\b
    Examples
        vcd search
            lists available resource types.
\b
        vcd search task
            Search for all tasks in current organization.
\b
        vcd search task --filter 'status==running'
            Search for running tasks in current organization.
\b
        vcd search admintask --filter 'status==running'
            Search for running tasks in all organizations, system administrator only.
\b
        vcd search task --filter 'id==ffb96443-d7f3-4200-825d-0f297388ebc0'
            Search for a task by id
\b
        vcd search vapp
            Search for vApps.
\b
        vcd search vapp -f 'metadata:cse.node.type==STRING:master'
            Search for vApps by metadata.
\b
        vcd search vm
            Search for virtual machines.
    """  # NOQA
    try:
        if resource_type is None:
            click.secho(ctx.get_help())
            click.echo('\nAvailable resource types:')
            click.echo(tabulate(tabulate_names(RESOURCE_TYPES, 4)))
            return
        restore_session(ctx)
        client = ctx.obj['client']
        result = []
        resource_type_cc = to_camel_case(resource_type, RESOURCE_TYPES)
        q = client.get_typed_query(resource_type_cc,
                                   query_result_format=QueryResultFormat.
                                   ID_RECORDS,
                                   qfilter=query_filter)
        records = list(q.execute())
        if len(records) == 0:
            result = 'not found'
        else:
            for r in records:
                result.append(to_dict(r, resource_type=resource_type_cc))
        stdout(result, ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)
