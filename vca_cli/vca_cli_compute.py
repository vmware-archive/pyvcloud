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


import click
import operator
from vca_cli import cli, utils, default_operation


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | use | info]',
                type=click.Choice(['list', 'use', 'info']))
@click.option('-v', '--vdc', default=None, metavar='<vdc>',
              help='Virtual Data Center Name')
def vdc(cmd_proc, operation, vdc):
    """Operations with Virtual Data Centers"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        return
    if 'list' == operation:
        headers = ['Virtual Data Center', "Selected"]
        table = ['', '']
        if cmd_proc.vca.vcloud_session and \
           cmd_proc.vca.vcloud_session.organization:
            links = (cmd_proc.vca.vcloud_session.organization.Link if
                     cmd_proc.vca.vcloud_session.organization else [])
            table1 = [[details.get_name(),
                      '*' if details.get_name() == cmd_proc.vca.vdc else '']
                      for details in filter(lambda info: info.name and
                      (info.type_ == 'application/vnd.vmware.vcloud.vdc+xml'),
                      links)]
            table = sorted(table1, key=operator.itemgetter(0), reverse=False)
        utils.print_table(
            "Available Virtual Data Centers in org '%s', profile '%s':" %
            (cmd_proc.vca.org, cmd_proc.profile),
            headers, table, cmd_proc)
    elif 'use' == operation:
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        if the_vdc is not None:
            utils.print_message("Using vdc '%s' in profile '%s'" %
                                (vdc, cmd_proc.profile), cmd_proc)
            cmd_proc.vca.vdc = vdc
        else:
            utils.print_error("Unable to select vdc '%s' in profile '%s'" %
                              (vdc, cmd_proc.profile), cmd_proc)
    elif 'info' == operation:
        if vdc is None:
            vdc = cmd_proc.vca.vdc
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        if the_vdc:
            gateways = cmd_proc.vca.get_gateways(vdc)
            headers1 = ['Type', 'Name']
            table1 = cmd_proc.vdc_to_table(the_vdc, gateways)
            headers2 = ['Resource', 'Allocated',
                        'Limit', 'Reserved', 'Used', 'Overhead']
            table2 = cmd_proc.vdc_resources_to_table(the_vdc)
            headers3 = ['Name', 'External IPs', 'DHCP', 'Firewall', 'NAT',
                        'VPN', 'Routed Networks', 'Syslog', 'Uplinks']
            table3 = cmd_proc.gateways_to_table(gateways)
            if cmd_proc.json_output:
                json_object = {'vdc_entities':
                               utils.table_to_json(headers1, table1),
                               'vdc_resources':
                               utils.table_to_json(headers2, table2),
                               'gateways':
                               utils.table_to_json(headers3, table3)}
                utils.print_json(json_object, cmd_proc=cmd_proc)
            else:
                utils.print_table(
                    "Details of Virtual Data Center '%s', profile '%s':" %
                    (vdc, cmd_proc.profile),
                    headers1, table1, cmd_proc)
                utils.print_table("Compute capacity:",
                                  headers2, table2, cmd_proc)
                utils.print_table('Gateways:',
                                  headers3, table3, cmd_proc)
        else:
            utils.print_error("Unable to select vdc '%s' in profile '%s'" %
                              (vdc, cmd_proc.profile), cmd_proc)
    cmd_proc.save_current_config()


# TODO: user power-on instead of power.on, etc
@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | create | delete | power-on'
                        ' | power-off | deploy | undeploy | customize'
                        ' | insert | eject | connect | disconnect'
                        ' | attach | detach]',
                type=click.Choice(
                    ['list', 'info', 'create', 'delete', 'power.on',
                     'power.off', 'deploy', 'undeploy', 'customize',
                     'insert', 'eject', 'connect', 'disconnect',
                     'attach', 'detach']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-a', '--vapp', 'vapp', default='',
              metavar='<vapp>', help='vApp name')
@click.option('-c', '--catalog', default='',
              metavar='<catalog>', help='Catalog name')
@click.option('-t', '--template', default='',
              metavar='<template>', help='Template name')
@click.option('-n', '--network', default='',
              metavar='<network>', help='Network name')
@click.option('-m', '--mode', default='POOL',
              metavar='[pool, dhcp, manual]', help='Network connection mode',
              type=click.Choice(['POOL', 'pool', 'DHCP', 'dhcp', 'MANUAL',
                                 'manual']))
@click.option('-V', '--vm', 'vm_name', default='',
              metavar='<vm>', help='VM name')
@click.option('-f', '--file', 'cust_file',
              default=None, metavar='<customization_file>',
              help='Guest OS Customization script file', type=click.File('r'))
@click.option('-e', '--media', default='',
              metavar='<media>', help='Virtual media name (ISO)')
@click.option('-d', '--disk', 'disk_name', default=None,
              metavar='<disk_name>', help='Disk Name')
@click.option('-o', '--count', 'count', default=1,
              metavar='<count>', help='Number of vApps to create')
@click.option('-p', '--cpu', 'cpu', default=None,
              metavar='<virtual CPUs>', help='Virtual CPUs')
@click.option('-r', '--ram', 'ram', default=None,
              metavar='<MB RAM>', help='Memory in MB')
@click.option('-i', '--ip', default='', metavar='<ip>', help='IP address')
def vapp(cmd_proc, operation, vdc, vapp, catalog, template,
         network, mode, vm_name, cust_file,
         media, disk_name, count, cpu, ram, ip):
    """Operations with vApps"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        return
    if vdc is None:
        vdc = cmd_proc.vca.vdc
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if 'list' == operation:
        headers = ['vApp', "VMs", "Status", "Deployed", "Description"]
        table = cmd_proc.vapps_to_table(the_vdc)
        if cmd_proc.json_output:
            json_object = {'vapps':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available vApps in '%s', profile '%s':" %
                              (vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif 'create' == operation:
        utils.print_message('not implemented', cmd_proc)
    else:
        utils.print_message('not implemented', cmd_proc)
    cmd_proc.save_current_config()
