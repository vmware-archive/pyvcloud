# vCloud Air CLI 0.1
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


import sys
import click
from vca_cli import cli, utils, default_operation


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[info | list | use | set-syslog'
                        ' | add-ip | del-ip]',
                type=click.Choice(['info', 'list',
                                   'use', 'set-syslog',
                                   'add-ip', 'del-ip']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-g', '--gateway', default=None,
              metavar='<gateway>', help='Edge Gateway Name')
@click.option('-i', '--ip', default='', metavar='<ip>', help='IP address')
def gateway(cmd_proc, operation, vdc, gateway, ip):
    """Operations with Edge Gateway"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
    if gateway is None:
        gateway = cmd_proc.gateway
    the_gateway = cmd_proc.vca.get_gateway(vdc, gateway)
    if the_gateway is None:
        utils.print_error("gateway not found '%s'" % gateway, cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ['Name', 'External IPs', 'DHCP', 'Firewall', 'NAT',
                   'VPN', 'Routed Networks', 'Syslog', 'Uplinks', 'Selected']
        gateways = cmd_proc.vca.get_gateways(vdc)
        table = cmd_proc.gateways_to_table(gateways)
        if cmd_proc.json_output:
            json_object = {'gateways':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available gateways in '%s', profile '%s':" %
                              (vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif ('use' == operation or
          'info' == operation or
          'set-syslog' == operation or
          'add-ip' == operation or
          'del-ip' == operation):
        if 'set-syslog' == operation:
            task = the_gateway.set_syslog_conf(ip)
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                utils.print_error("can't set syslog server", cmd_proc)
                sys.exit(1)
        elif 'add-ip' == operation:
            utils.print_message("allocating public IP for gateway '%s' "
                                "in VDC '%s'" %
                                (gateway, vdc), cmd_proc)
            task = the_gateway.allocate_public_ip()
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                utils.print_error("can't allocate public IP", cmd_proc)
                sys.exit(1)
        elif 'del-ip' == operation:
            utils.print_message("deallocating public IP '%s' from gateway "
                                "'%s' in VDC '%s'" %
                                (ip, gateway, vdc), cmd_proc)
            task = the_gateway.deallocate_public_ip(ip)
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                utils.print_error("can't deallocate public IP", cmd_proc)
                sys.exit(1)
        elif 'use' == operation:
            cmd_proc.gateway = gateway
            utils.print_message("Selected gateway '%s'" % gateway, cmd_proc)
        elif 'info' == operation:
            headers = ['Property', 'Value']
            table = cmd_proc.gateway_to_table(the_gateway)
            if cmd_proc.json_output:
                json_object = {'gateway':
                               utils.table_to_json(headers, table)}
                utils.print_json(json_object, cmd_proc=cmd_proc)
            else:
                utils.print_table("Details of gateway '%s' in VDC '%s', "
                                  "profile '%s':" %
                                  (gateway, vdc, cmd_proc.profile),
                                  headers, table, cmd_proc)
    else:
        utils.print_error('not implemented', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()
