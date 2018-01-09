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
from pyvcloud.vcd.vdc import VDC
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='work with vcd networks')
@click.pass_context
def network(ctx):
    """Work with networks in vCloud Director.
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@network.group(short_help='work with directly connected org vdc networks')
@click.pass_context
def direct(ctx):
    """Work with directly connected org vdc networks.

\b
    Examples
        vcd network direct create 'direct-net1' \\
            --description 'directly connected orgvdc network' \\
            --parent 'ext-net1'
            Create an org vdc network which is directly connected \\
                to an external network
    """
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@direct.command('create', short_help='create a new directly connected org vdc '
                'network in vcd')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
@click.option(
    '-d',
    '--description',
    'description',
    required=False,
    metavar='<description>',
    default='',
    help='Description of the network to be created.')
@click.option(
    '-p',
    '--parent',
    'parent_network_name',
    required=True,
    metavar='<external network name>',
    help='Name of the external network to be connected to.')
@click.option(
    '-s/-n',
    '--shared/--not-shared',
    'is_shared',
    is_flag=True,
    required=False,
    default=False,
    help='Share/don\'t share the netowrk with other VDC(s) in the '
         'organization.')
def create(ctx, name, description, parent_network_name, is_shared):
    try:
        client = ctx.obj['client']
        in_use_vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=in_use_vdc_href)
        result = vdc.create_directly_connected_vdc_network(
            network_name=name,
            description=description,
            parent_network_name=parent_network_name,
            is_shared=is_shared)
        stdout(result.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)
