# VMware vCloud Director CLI
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
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.utils import vdc_to_dict
from pyvcloud.vcd.vdc import VDC

from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false
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
\b
        vcd vdc create dev-vdc -p prov-vdc -n net-pool -s '*' \\
            -a ReservationPool -d 'vDC for development'
            Create new virtual datacenter.
\b
        vcd vdc disable dev-vdc
            Disable virtual datacenter.
\b
        vcd vdc enable dev-vdc
            Enable virtual datacenter.
\b
        vcd vdc delete -y dev-vdc
            Delete virtual datacenter.
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@vdc.command(short_help='show virtual datacenter details')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
def info(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        in_use_vdc = ctx.obj['profiles'].get('vdc_in_use')
        org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, org_href)
        vdc_resource = org.get_vdc(name)
        vdc = VDC(client, resource=vdc_resource)
        access_control_settings = vdc.get_access_control_settings()
        result = vdc_to_dict(vdc_resource, access_control_settings)
        result['in_use'] = in_use_vdc == name
        result['org'] = in_use_org_name
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@vdc.command('list', short_help='list of virtual datacenters')
@click.pass_context
def list_vdc(ctx):
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
                    result.append({
                        'name': v.name,
                        'org': in_use_org_name,
                        'in_use': in_use_vdc == v.name
                    })
                break
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@vdc.command(short_help='set active virtual datacenter')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
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
                        vdc_in_use = name
                        vapp_in_use = ''
                        vapp_href = ''
                        client.get_resource(v.href)
                        ctx.obj['profiles'].set('vdc_in_use', vdc_in_use)
                        ctx.obj['profiles'].set('vdc_href', str(v.href))
                        ctx.obj['profiles'].set('vapp_in_use', vapp_in_use)
                        ctx.obj['profiles'].set('vapp_href', vapp_href)
                        message = 'now using org: \'%s\', vdc: \'%s\', vApp:' \
                            ' \'%s\'.' % (in_use_org_name, vdc_in_use,
                                          vapp_in_use)
                        stdout({
                            'org': in_use_org_name,
                            'vdc': vdc_in_use,
                            'vapp': vapp_in_use
                        }, ctx, message)
                        return
        raise Exception('not found')
    except Exception as e:
        stderr(e, ctx)


@vdc.command(short_help='create a virtual datacenter')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
@click.option(
    '-p',
    '--provider-vdc',
    'pvdc_name',
    required=True,
    metavar='[provider-vdc]',
    help='Provider VDC')
@click.option(
    '-n',
    '--network-pool',
    'network_pool_name',
    required=False,
    metavar='[network-pool]',
    help='Network pool')
@click.option(
    'allocation_model',
    '-a',
    '--allocation-model',
    type=click.Choice(['AllocationVApp', 'AllocationPool', 'ReservationPool']),
    required=False,
    default='AllocationVApp',
    metavar='<allocation-model>',
    help='Allocation model.')
@click.option(
    '-s',
    '--storage-profile',
    'sp_name',
    default='*',
    required=False,
    metavar='[storage-profile]',
    help='Provider VDC Storage Profile.')
@click.option(
    '--storage-profile-limit',
    'sp_limit',
    default=0,
    required=False,
    metavar='[storage-profile-limit]',
    help='Provider VDC Storage Profile limit (MB), 0 means unlimited.')
@click.option(
    '-D',
    '--description',
    required=False,
    default='',
    metavar='[description]',
    help='description.')
@click.option(
    '--cpu-allocated',
    required=False,
    default=0,
    metavar='<cpu-allocated>',
    type=click.INT,
    help='Capacity that is commited to be available.')
@click.option(
    '--cpu-limit',
    required=False,
    default=0,
    metavar='<cpu-limit>',
    type=click.INT,
    help='Capacity limit relative to the value specified for Allocation.')
def create(ctx, name, pvdc_name, network_pool_name, allocation_model,
           sp_name, sp_limit, description, cpu_allocated, cpu_limit):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        storage_profiles = [{
            'name': sp_name,
            'enabled': True,
            'units': 'MB',
            'limit': sp_limit,
            'default': True
        }]
        vdc_resource = org.create_org_vdc(
            name,
            pvdc_name,
            network_pool_name=network_pool_name,
            description=description,
            allocation_model=allocation_model,
            cpu_allocated=cpu_allocated,
            cpu_limit=cpu_limit,
            storage_profiles=storage_profiles,
            uses_fast_provisioning=True,
            is_thin_provision=True)
        stdout(vdc_resource.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)


@vdc.command(short_help='delete a virtual datacenter')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
@click.option(
    '-y',
    '--yes',
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt='Are you sure you want to delete the VDC?')
def delete(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        in_use_vdc = ctx.obj['profiles'].get('vdc_in_use')
        org = Org(client, in_use_org_href)
        vdc_resource = org.get_vdc(name)
        vdc = VDC(client, resource=vdc_resource)
        task = vdc.delete_vdc()
        if name == in_use_vdc:
            ctx.obj['profiles'].set('vdc_in_use', '')
            ctx.obj['profiles'].set('vdc_href', '')
            ctx.obj['profiles'].set('vapp_in_use', '')
            ctx.obj['profiles'].set('vapp_href', '')
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vdc.command(short_help='enable a virtual datacenter')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
def enable(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        vdc_resource = org.get_vdc(name)
        vdc = VDC(client, resource=vdc_resource)
        vdc.enable_vdc(True)
    except Exception as e:
        stderr(e, ctx)


@vdc.command(short_help='disable a virtual datacenter')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
def disable(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        vdc_resource = org.get_vdc(name)
        vdc = VDC(client, resource=vdc_resource)
        vdc.enable_vdc(False)
    except Exception as e:
        stderr(e, ctx)
