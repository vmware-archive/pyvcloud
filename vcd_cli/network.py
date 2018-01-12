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
        vcd network direct create direct-net1 \\
            --description 'Directly connected VDC network' \\
            --parent ext-net1 \\
            Create an org vdc network which is directly connected
            to an external network.
    """
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@network.group(short_help='work with isolated org vdc networks')
@click.pass_context
def isolated(ctx):
    """Work with isolated org vdc networks.

\b
    Examples
        vcd network isolated create isolated-net1 --gateway-ip 192.168.1.1 \\
            --netmask 255.255.255.0 --description 'Isolated VDC network' \\
            --primary-dns-ip 8.8.8.8 --dns-suffix example.com \\
            --ip-range-start 192.168.1.100 --ip-range-end 192.168.1.199 \\
            --dhcp-enabled --default-lease-time 3600 \\
            --max-lease-time 7200 --dhcp-ip-range-start 192.168.1.100 \\
            --dhcp-ip-range-end 192.168.1.199
            Create an isolated org vdc network with an inbuilt dhcp service.
    """
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@direct.command(
    'create',
    short_help='create a new directly connected org vdc '
    'network in vcd')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
@click.option(
    '-p',
    '--parent',
    'parent_network_name',
    required=True,
    metavar='<external network name>',
    help='Name of the external network to be connected to')
@click.option(
    '-d',
    '--description',
    'description',
    metavar='<description>',
    default='',
    help='Description of the network to be created')
@click.option(
    '-s/-n',
    '--shared/--not-shared',
    'is_shared',
    is_flag=True,
    default=False,
    help='Share/Don\'t share the network with other VDC(s) in the '
    'organization')
def create_direct_network(ctx, name, parent_network_name, description,
                          is_shared):
    try:
        client = ctx.obj['client']
        in_use_vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=in_use_vdc_href)

        result = vdc.create_directly_connected_vdc_network(
            network_name=name,
            parent_network_name=parent_network_name,
            description=description,
            is_shared=is_shared)

        stdout(result.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)


@isolated.command(
    'create', short_help='create a new isolated org vdc '
    'network in vcd')
@click.pass_context
@click.argument('name', metavar='<name>')
@click.option(
    '-g',
    '--gateway',
    'gateway_ip',
    required=True,
    metavar='<ip>',
    help='IP address of the gateway of the new network')
@click.option(
    '-n',
    '--netmask',
    'netmask',
    required=True,
    metavar='<netmask>',
    help='network mask for the gateway')
@click.option(
    '-d',
    '--description',
    'description',
    metavar='<description>',
    default='',
    help='Description of the network to be created')
@click.option(
    '--dns1',
    'primary_dns_ip',
    metavar='<ip>',
    help='IP of the primary DNS server')
@click.option(
    '--dns2',
    'secondary_dns_ip',
    metavar='<ip>',
    help='IP of the secondary DNS server')
@click.option(
    '--dns-suffix', 'dns_suffix', metavar='<name>', help='DNS suffix')
@click.option(
    '--ip-range-start',
    'ip_range_start',
    metavar='<ip>',
    help='Start address of the IP ranges used for static pool allocation in '
    'the network')
@click.option(
    '--ip-range-end',
    'ip_range_end',
    metavar='<ip>',
    help='End address of the IP ranges used for static pool allocation in '
    'the network')
@click.option(
    '--dhcp-enabled/--dhcp-disabled',
    'is_dhcp_enabled',
    is_flag=True,
    help='Enable/Disable DHCP service on the new network')
@click.option(
    '--default-lease-time',
    'default_lease_time',
    metavar='<integer>',
    help='Default lease in seconds for DHCP addresses')
@click.option(
    '--max-lease-time',
    'max_lease_time',
    metavar='<integer>',
    help='Max lease in seconds for DHCP addresses')
@click.option(
    '--dhcp-ip-range-start',
    'dhcp_ip_range_start',
    metavar='<ip>',
    help='Start address of the IP range used for DHCP addresses')
@click.option(
    '--dhcp-ip-range-end',
    'dhcp_ip_range_end',
    metavar='<ip>',
    help='End address of the IP range used for DHCP addresses')
@click.option(
    '--shared/--not-shared',
    'is_shared',
    is_flag=True,
    default=False,
    help='Share/Don\'t share the network with other VDC(s) in the '
    'organization')
def create_isolated_network(ctx, name, gateway_ip, netmask, description,
                            primary_dns_ip, secondary_dns_ip, dns_suffix,
                            ip_range_start, ip_range_end, is_dhcp_enabled,
                            default_lease_time, max_lease_time,
                            dhcp_ip_range_start, dhcp_ip_range_end, is_shared):
    try:
        client = ctx.obj['client']
        in_use_vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=in_use_vdc_href)

        result = vdc.create_isolated_vdc_network(
            network_name=name,
            gateway_ip=gateway_ip,
            netmask=netmask,
            description=description,
            primary_dns_ip=primary_dns_ip,
            secondary_dns_ip=secondary_dns_ip,
            dns_suffix=dns_suffix,
            ip_range_start=ip_range_start,
            ip_range_end=ip_range_end,
            is_dhcp_enabled=is_dhcp_enabled,
            default_lease_time=default_lease_time,
            max_lease_time=max_lease_time,
            dhcp_ip_range_start=dhcp_ip_range_start,
            dhcp_ip_range_end=dhcp_ip_range_end,
            is_shared=is_shared)

        stdout(result.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)
