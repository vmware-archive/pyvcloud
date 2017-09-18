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
from pyvcloud.vcd.utils import vapp_to_dict
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC
from vcd_cli.utils import is_admin
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false
from vcd_cli.vcd import vcd


@vcd.group(short_help='manage vApps')
@click.pass_context
def vapp(ctx):
    """Manage vApps in vCloud Director.

\b
    Examples
        vcd vapp list
            Get list of vApps in current virtual datacenter.
\b
        vcd vapp info my-vapp
            Get details of the vApp 'my-vapp'.
\b
        vcd vapp create my-catalog my-template my-vapp
            Create a new vApp.
\b
        vcd vapp create my-catalog my-template my-vapp \\
                 --cpu 4 --memory 4096 --network net1
            Create a new vApp with customized settings.
\b
        vcd vapp delete my-vapp --yes --force
            Delete a vApp.
\b
        vcd --no-wait vapp delete my-vapp --yes --force
            Delete a vApp without waiting for completion.
\b
        vcd vapp update-lease my-vapp 7776000
            Set vApp lease to 90 days.
\b
        vcd vapp update-lease my-vapp 0
            Set vApp lease to no expiration.
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
        vdc = VDC(client, vdc_href=vdc_href)
        vapp = vdc.get_vapp(name)
        stdout(vapp_to_dict(vapp), ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('list', short_help='list vApps')
@click.pass_context
def list_vapps(ctx):
    try:
        client = ctx.obj['client']
        result = []
        resource_type = 'adminVApp' if is_admin(ctx) else 'vApp'
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


@vapp.command(short_help='create a vApp')
@click.pass_context
@click.argument('catalog',
                metavar='<catalog>',
                required=True)
@click.argument('template',
                metavar='<template>',
                required=True)
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-n',
              '--network',
              'network',
              required=False,
              metavar='<network>',
              help='Network')
@click.option('-m',
              '--memory',
              'memory',
              required=False,
              metavar='<MB>',
              type=click.INT,
              help='Amount of memory in MB')
@click.option('-c',
              '--cpu',
              'cpu',
              required=False,
              metavar='<virtual-cpus>',
              type=click.INT,
              help='Number of CPUs')
def create(ctx, catalog, template, name, network, memory, cpu):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        vapp = vdc.instantiate_vapp(
            name,
            catalog,
            template,
            network=network,
            memory=memory,
            cpu=cpu)
        stdout(vapp.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command(short_help='delete a vApp')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to delete the vApp?')
@click.option('-f',
              '--force',
              is_flag=True,
              help='Force delete running vApps')
def delete(ctx, name, force):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        task = vdc.delete_vapp(name, force)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('update-lease', short_help='update vApp lease')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('runtime-seconds',
                metavar='<runtime-seconds>',
                required=True)
@click.argument('storage-seconds',
                metavar='[storage-seconds]',
                required=False)
def update_lease(ctx, name, runtime_seconds, storage_seconds):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, vapp_resource=vapp_resource)
        if storage_seconds is None:
            storage_seconds = runtime_seconds
        task = vapp.set_lease(runtime_seconds, storage_seconds)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)
