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
from pyvcloud.vcd.utils import vapp_to_dict
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import cli


@cli.group(short_help='manage vApps')
@click.pass_context
def vapp(ctx):
    """Manage vApps in vCloud Director.

\b
    Examples
        vcd vapp list
            Get list of vApps in current virtual datacente3r.
\b
        vcd vapp info my-vapp
            Get details of the vApp 'my-vapp'.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)


@vapp.command(short_help='show vApp details')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def info(ctx, name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc_resource = client.get_resource(vdc_href)
        result = []
        if hasattr(vdc_resource, 'ResourceEntities') and \
           hasattr(vdc_resource.ResourceEntities, 'ResourceEntity'):
            for vapp in vdc_resource.ResourceEntities.ResourceEntity:
                if vapp.get('name') == name:
                    vapp_resource = client.get_resource(vapp.get('href'))
                    result.append(vapp_to_dict(vapp_resource))
        if len(result) == 0:
            raise Exception('not found')
        elif len(result) > 1:
            raise Exception('more than one found, use the vapp-id')
        stdout(result[0], ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command(short_help='list of vApps')
@click.pass_context
def list(ctx):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc_resource = client.get_resource(vdc_href)
        result = []
        if hasattr(vdc_resource, 'ResourceEntities') and \
           hasattr(vdc_resource.ResourceEntities, 'ResourceEntity'):
            for vapp in vdc_resource.ResourceEntities.ResourceEntity:
                result.append({'name': vapp.get('name'),
                               'type': vapp.get('type').split('+')[0].
                               split('.')[-1],
                               'id': vapp.get('href').split('/')[-1]})
        stdout(result, ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)
