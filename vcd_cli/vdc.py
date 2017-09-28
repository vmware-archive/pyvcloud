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
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.utils import vdc_to_dict
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with virtual datacenters')
@click.pass_context
def vdc(ctx):
    """Work with virtual datacenters in vCloud Director.

\b
    Examples
        vcd vdc list
            Get list of virtual datacenters in current organization.
\b
        vcd vdc info my-vdc
            Get details of the virtual datacenter 'my-vdc'.
\b
        vcd vdc use my-vdc
            Set virtual datacenter 'my-vdc' as default.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@vdc.command(short_help='show virtual datacenter details')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def info(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        in_use_vdc = ctx.obj['profiles'].get('vdc_in_use')
        orgs = client.get_org_list()
        result = {}
        vdc_resource = None
        for org in [o for o in orgs.Org if hasattr(orgs, 'Org')]:
            if org.get('name') == in_use_org_name:
                resource = client.get_resource(org.get('href'))
                for v in get_links(resource, media_type=EntityType.VDC.value):
                    if v.name == name:
                        vdc_resource = client.get_resource(v.href)
                        result = vdc_to_dict(vdc_resource)
                        result['in_use'] = in_use_vdc == name
                        result['org'] = in_use_org_name
                        break
        if vdc_resource is None:
            raise Exception('not found')
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@vdc.command(short_help='list of virtual datacenters')
@click.pass_context
def list(ctx):
    try:
        client = ctx.obj['client']
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        in_use_vdc = ctx.obj['profiles'].get('vdc_in_use')
        orgs = client.get_org_list()
        result = []
        for org in [o for o in orgs.Org if hasattr(orgs, 'Org')]:
            if org.get('name') == in_use_org_name:
                resource = client.get_resource(org.get('href'))
                for v in get_links(resource, media_type=EntityType.VDC.value):
                    result.append({'name': v.name,
                                   'org': in_use_org_name,
                                   'in_use': in_use_vdc == v.name})
                break
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@vdc.command(short_help='set active virtual datacenter')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def use(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        orgs = client.get_org_list()
        for org in [o for o in orgs.Org if hasattr(orgs, 'Org')]:
            if org.get('name') == in_use_org_name:
                resource = client.get_resource(org.get('href'))
                for v in get_links(resource, media_type=EntityType.VDC.value):
                    if v.name == name:
                        client.get_resource(v.href)
                        ctx.obj['profiles'].set('vdc_in_use', str(name))
                        ctx.obj['profiles'].set('vdc_href', str(v.href))
                        message = 'now using org: \'%s\', vdc: \'%s\'.' % \
                                  (in_use_org_name, name)
                        stdout({'org': in_use_org_name, 'vdc': vdc},
                               ctx,
                               message)
                        return
        raise Exception('not found')
    except Exception as e:
        stderr(e, ctx)
