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
import sys
from vca_cli import cli
from vca_cli import default_operation
from vca_cli import utils


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | use | info | create | delete]',
                type=click.Choice(['list', 'use', 'info', 'create',
                                   'delete']))
@click.option('-v', '--vdc', default=None, metavar='<vdc>',
              help='Virtual Data Center Name')
@click.option('-t', '--template', default=None, metavar='<template>',
              help='Virtual Data Center Template Name')
@click.option('-y', '--yes', is_flag=True,
              help='Confirm deletion of VDC')
def vdc(cmd_proc, operation, vdc, template, yes):
    """Operations with Virtual Data Centers"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ['Virtual Data Center', "Selected"]
        table = ['', '']
        if cmd_proc.vca.vcloud_session and \
           cmd_proc.vca.vcloud_session.organization:
            links = (cmd_proc.vca.vcloud_session.organization.Link if
                     cmd_proc.vca.vcloud_session.organization else [])
            table1 = [[details.get_name(),
                      '*' if details.get_name() == cmd_proc.vdc_name else '']
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
            utils.print_message("Using vdc '%s', profile '%s'" %
                                (vdc, cmd_proc.profile), cmd_proc)
            cmd_proc.vdc_name = vdc
            cmd_proc.select_default_gateway()
        else:
            utils.print_error("Unable to select vdc '%s' in profile '%s'" %
                              (vdc, cmd_proc.profile), cmd_proc)
            sys.exit(1)
    elif 'info' == operation:
        if vdc is None:
            vdc = cmd_proc.vdc_name
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        if the_vdc:
            gateways = cmd_proc.vca.get_gateways(vdc)
            headers1 = ['Type', 'Name']
            table1 = cmd_proc.vdc_to_table(the_vdc, gateways)
            headers2 = ['Resource', 'Allocated',
                        'Limit', 'Reserved', 'Used', 'Overhead']
            table2 = cmd_proc.vdc_resources_to_table(the_vdc)
            headers3 = ['Name', 'External IPs', 'DHCP', 'Firewall', 'NAT',
                        'VPN', 'Networks', 'Syslog', 'Uplinks', 'Selected']
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
            utils.print_error("Unable to select VDC %s, profile '%s': "
                              "VDC not found" %
                              (vdc, cmd_proc.profile), cmd_proc)
            sys.exit(1)
    elif 'create' == operation:
        if vdc is None:
            utils.print_error('please enter new VDC name')
            sys.exit(1)
        task = cmd_proc.vca.create_vdc(vdc, template)
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't create the VDC", cmd_proc)
            sys.exit(1)
    elif 'delete' == operation:
        if vdc is None:
            vdc = cmd_proc.vdc_name
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        if the_vdc:
            if not yes:
                confirmed = click.confirm("This will delete the VDC, its "
                                          "edge gateway and all its virtual "
                                          "machines.\n"
                                          "The action can't be undone.\n"
                                          "Do you want to delete VDC '%s'?"
                                          % vdc)
                if not confirmed:
                    utils.print_message('Action cancelled, '
                                        'VDC will not be deleted')
                    sys.exit(0)
            result = cmd_proc.vca.delete_vdc(vdc)
            if result[0]:
                utils.display_progress(result[1], cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                utils.print_error("can't delete the VDC", cmd_proc)
                sys.exit(1)
        else:
            utils.print_error("Unable to delete VDC '%s', profile '%s': "
                              "VDC not found" %
                              (vdc, cmd_proc.profile), cmd_proc)
            sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | create | delete |' +
                        ' delete-item | upload]',
                type=click.Choice(['list', 'info',
                                   'create', 'delete', 'delete-item',
                                   'upload']))
@click.option('-c', '--catalog', 'catalog_name', default='',
              metavar='<catalog>', help='Catalog Name')
@click.option('-i', '--item', 'item_name', default='',
              metavar='<catalog item>', help='Catalog Item Name')
@click.option('-d', '--description', default='',
              metavar='<description>', help='Catalog Description')
@click.option('-f', '--file', 'file_name',
              default=None, metavar='<file>',
              help='file to upload',
              type=click.Path(exists=True))
def catalog(cmd_proc, operation, catalog_name, item_name, description,
            file_name):
    """Operations with Catalogs"""
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        catalogs = cmd_proc.vca.get_catalogs()
        headers = ['Catalog', 'Item']
        table = cmd_proc.catalogs_to_table(catalogs)
        if cmd_proc.json_output:
            json_object = {'catalogs':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available catalogs and items in org '%s', "
                              "profile '%s':" %
                              (cmd_proc.vca.org, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif 'create' == operation:
        task = cmd_proc.vca.create_catalog(catalog_name, description)
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't create the catalog", cmd_proc)
            sys.exit(1)
    elif 'delete' == operation:
        result = cmd_proc.vca.delete_catalog(catalog_name)
        if result:
            utils.print_message('catalog deleted', cmd_proc)
        else:
            utils.print_error("can't delete the catalog", cmd_proc)
            sys.exit(1)
    elif 'delete-item' == operation:
        result = cmd_proc.vca.delete_catalog_item(catalog_name, item_name)
        if result:
            utils.print_message('catalog item deleted', cmd_proc)
        else:
            utils.print_error("can't delete the catalog item", cmd_proc)
            sys.exit(1)
    elif 'upload' == operation:
        if file_name.endswith('.iso'):
            result = cmd_proc.vca.upload_media(catalog_name, item_name,
                                               file_name, description, True,
                                               128*1024)
            if result:
                utils.print_message('file successfull uploaded', cmd_proc)
            else:
                utils.print_error("can't upload file", cmd_proc)
                sys.exit(1)
        else:
            utils.print_error('not implemented, ' +
                              'only .iso files are currently supported',
                              cmd_proc)
            sys.exit(1)
    else:
        utils.print_error('not implemented', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | create | delete | power-on'
                        ' | power-off | deploy | undeploy | customize'
                        ' | insert | eject | connect | disconnect'
                        ' | attach | detach]',
                type=click.Choice(
                    ['list', 'info', 'create', 'delete', 'power-on',
                     'power-off', 'deploy', 'undeploy', 'customize',
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
@click.option('-V', '--vm', 'vm_name', default=None,
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
        sys.exit(1)
    if vdc is None:
        vdc = cmd_proc.vdc_name
    the_vdc = cmd_proc.vca.get_vdc(vdc)
    if the_vdc is None:
        utils.print_error("VDC not found '%s'" % vdc, cmd_proc)
        sys.exit(1)
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
        for x in xrange(1, count + 1):
            vapp_name = vapp
            if count > 1:
                vapp_name += '-' + str(x)
            utils.print_message("creating vApp '%s' in VDC '%s'"
                                " from template '%s' in catalog '%s'" %
                                (vapp_name, vdc, template, catalog),
                                cmd_proc)
            task = None
            if ((vm_name is not None) and
                ((cmd_proc.vca.version == "1.0") or
                 (cmd_proc.vca.version == "1.5") or
                 (cmd_proc.vca.version == "5.1") or
                 (cmd_proc.vca.version == "5.5"))):
                task = cmd_proc.vca.create_vapp(vdc, vapp_name,
                                                template, catalog)
            else:
                task = cmd_proc.vca.create_vapp(vdc, vapp_name,
                                                template, catalog,
                                                vm_name=vm_name)
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
            else:
                utils.print_error("can't create the vApp", cmd_proc)
                sys.exit(1)
            the_vdc = cmd_proc.vca.get_vdc(vdc)
            the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp_name)
            if ((vm_name is not None) and
                ((cmd_proc.vca.version == "1.0") or
                 (cmd_proc.vca.version == "1.5") or
                 (cmd_proc.vca.version == "5.1") or
                 (cmd_proc.vca.version == "5.5"))):
                utils.print_message(
                    "setting VM name to '%s'"
                    % (vm_name), cmd_proc)
                task = the_vapp.modify_vm_name(1, vm_name)
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't set VM name", cmd_proc)
                    sys.exit(1)
                the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp_name)
            if vm_name is not None:
                utils.print_message(
                    "setting computer name for VM '%s'"
                    % (vm_name), cmd_proc)
                task = the_vapp.customize_guest_os(vm_name,
                                                   computer_name=vm_name)
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't set computer name", cmd_proc)
                    sys.exit(1)
                the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp_name)
            if cpu is not None:
                utils.print_message(
                    "configuring '%s' vCPUs for VM '%s', vApp '%s'"
                    % (cpu, vm_name, vapp_name), cmd_proc)
                task = the_vapp.modify_vm_cpu(vm_name, cpu)
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't configure virtual CPUs", cmd_proc)
                    sys.exit(1)
                the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp_name)
            if ram is not None:
                utils.print_message("configuring '%s' MB of memory"
                                    " for VM '%s', vApp '%s'"
                                    % (ram, vm_name, vapp_name), cmd_proc)
                task = the_vapp.modify_vm_memory(vm_name, ram)
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't configure RAM", cmd_proc)
                    sys.exit(1)
                the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp_name)
            if '' != network:
                utils.print_message("disconnecting VM from networks"
                                    " pre-defined in the template", cmd_proc)
                task = the_vapp.disconnect_vms()
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't disconnect VM from networks",
                                      cmd_proc)
                    sys.exit(1)
                utils.print_message("disconnecting vApp from networks"
                                    " pre-defined in the template", cmd_proc)
                task = the_vapp.disconnect_from_networks()
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't disconnect vApp from networks",
                                      cmd_proc)
                    sys.exit(1)
                nets = filter(lambda n: n.name == network,
                              cmd_proc.vca.get_networks(vdc))
                if len(nets) == 1:
                    utils.print_message("connecting vApp to network"
                                        " '%s' with mode '%s'" %
                                        (network, mode), cmd_proc)
                    task = the_vapp.connect_to_network(
                        nets[0].name, nets[0].href)
                    if task:
                        utils.display_progress(task, cmd_proc,
                                               cmd_proc.vca.vcloud_session.
                                               get_vcloud_headers())
                    else:
                        utils.print_error("can't connect the vApp "
                                          "to the network",
                                          cmd_proc)
                        sys.exit(1)
                    utils.print_message("connecting VM to network '%s'"
                                        " with mode '%s'" % (network, mode),
                                        cmd_proc)
                    task = the_vapp.connect_vms(
                        nets[0].name,
                        connection_index=0,
                        ip_allocation_mode=mode.upper(),
                        mac_address=None, ip_address=ip)
                    if task:
                        utils.display_progress(task,
                                               cmd_proc,
                                               cmd_proc.vca.vcloud_session.
                                               get_vcloud_headers())
                    else:
                        utils.print_error("can't connect the VM "
                                          "to the network", cmd_proc)
                        sys.exit(1)
    elif 'delete' == operation:
        utils.print_message("deleting vApp '%s' from VDC '%s'" % (vapp, vdc),
                            cmd_proc)
        task = cmd_proc.vca.delete_vapp(vdc, vapp)
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't delete the vApp", cmd_proc)
            sys.exit(1)
    elif 'deploy' == operation:
        utils.print_message("deploying vApp '%s' to VDC '%s'" % (vapp, vdc),
                            cmd_proc)
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp)
        task = the_vapp.deploy()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't deploy vApp", cmd_proc)
            sys.exit(1)
    elif 'undeploy' == operation:
        utils.print_message("undeploying vApp '%s' from VDC '%s'" %
                            (vapp, vdc), cmd_proc)
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp)
        task = the_vapp.undeploy()
        if task:
            utils.display_progress(task, cmd_proc,
                                   cmd_proc.vca.vcloud_session.
                                   get_vcloud_headers())
        else:
            utils.print_error("can't undeploy vApp", cmd_proc)
            sys.exit(1)
    elif ('info' == operation or 'power-off' == operation or
          'power-on' == operation):
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        if the_vdc:
            the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp)
            if the_vapp and the_vapp.me:
                if 'info' == operation:
                    headers = ['Entity', 'Attribute', 'Value']
                    table = cmd_proc.vapp_details_to_table(the_vapp)
                    if cmd_proc.json_output:
                        json_object = {'vapp':
                                       utils.table_to_json(headers, table)}
                        utils.print_json(json_object, cmd_proc=cmd_proc)
                    else:
                        utils.print_table("Details of vApp '%s', "
                                          "profile '%s':" %
                                          (vapp, cmd_proc.profile),
                                          headers, table, cmd_proc)
                else:
                    task = None
                    if 'power-on' == operation:
                        task = the_vapp.poweron()
                    elif 'power-off' == operation:
                        task = the_vapp.poweroff()
                    elif 'delete' == operation:
                        task = the_vapp.delete()
                    if task:
                        utils.display_progress(task,
                                               cmd_proc,
                                               cmd_proc.vca.vcloud_session.
                                               get_vcloud_headers())
                    else:
                        utils.print_error("can't operate with the vApp",
                                          cmd_proc)
                        sys.exit(1)
            else:
                utils.print_error("vApp '%s' not found" % vapp, cmd_proc)
                sys.exit(1)
        else:
            utils.print_error("VDC '%s' not found" % vdc, cmd_proc)
            sys.exit(1)
    elif 'customize' == operation:
        utils.print_message("customizing VM '%s'"
                            "in vApp '%s' in VDC '%s'" %
                            (vm_name, vapp, vdc))
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp)
        if the_vdc and the_vapp and cust_file:
            utils.print_message("uploading customization script", cmd_proc)
            task = the_vapp.customize_guest_os(vm_name, cust_file.read())
            if task:
                utils.display_progress(task, cmd_proc,
                                       cmd_proc.vca.vcloud_session.
                                       get_vcloud_headers())
                utils.print_message("deploying and starting the vApp",
                                    cmd_proc)
                task = the_vapp.force_customization(vm_name)
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't customize vApp", cmd_proc)
                    sys.exit(1)
            else:
                utils.print_error("can't customize vApp", cmd_proc)
                sys.exit(1)
        else:
            utils.print_error("can't find the resource",
                              cmd_proc)
            sys.exit(1)
    elif 'insert' == operation or 'eject' == operation:
        utils.print_message("%s media '%s', VM '%s'"
                            " in vApp '%s' in VDC '%s'" %
                            (operation, media, vm_name, vapp, vdc))
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        if the_vdc:
            the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp)
            if the_vapp:
                the_media = cmd_proc.vca.get_media(catalog, media)
                task = the_vapp.vm_media(vm_name, the_media, operation)
                if task:
                    utils.display_progress(task, cmd_proc,
                                           cmd_proc.vca.vcloud_session.
                                           get_vcloud_headers())
                else:
                    utils.print_error("can't insert or eject media",
                                      cmd_proc)
                    sys.exit(1)
            else:
                utils.print_error("vApp '%s' not found" % vapp, cmd_proc)
                sys.exit(1)
        else:
            utils.print_error("VDC '%s' not found" % vdc, cmd_proc)
            sys.exit(1)
    elif 'attach' == operation or 'detach' == operation:
        utils.print_message("%s disk '%s', VM '%s'"
                            " in vApp '%s' in VDC '%s'" %
                            (operation, disk_name, vm_name, vapp, vdc))
        the_vdc = cmd_proc.vca.get_vdc(vdc)
        if the_vdc:
            the_vapp = cmd_proc.vca.get_vapp(the_vdc, vapp)
            if the_vapp:
                link = filter(lambda link:
                              link.get_name() == disk_name,
                              cmd_proc.vca.get_diskRefs(the_vdc))
                if len(link) == 1:
                    if 'attach' == operation:
                        task = the_vapp.attach_disk_to_vm(vm_name,
                                                          link[0])
                    else:
                        task = the_vapp.detach_disk_from_vm(vm_name,
                                                            link[0])
                    if task:
                        utils.display_progress(task, cmd_proc,
                                               cmd_proc.vca.vcloud_session.
                                               get_vcloud_headers())
                    else:
                        utils.print_error("can't attach or detach disk",
                                          cmd_proc)
                        sys.exit(1)
                elif len(link) == 0:
                    utils.print_error("disk not found", cmd_proc)
                    sys.exit(1)
                elif len(link) > 1:
                    utils.print_error("more than one disk found with "
                                      "the same name",
                                      cmd_proc)
                    sys.exit(1)
            else:
                utils.print_error("vApp '%s' not found" % vapp, cmd_proc)
                sys.exit(1)
        else:
            utils.print_error("VDC '%s' not found" % vdc, cmd_proc)
            sys.exit(1)
    else:
        utils.print_error('not implemented', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | create | delete]',
                type=click.Choice(['list', 'create', 'delete']))
@click.option('-v', '--vdc', default=None, metavar='<vdc>',
              help='Virtual Data Center Name')
@click.option('-d', '--disk', 'disk_name', default=None,
              metavar='<disk_name>', help='Disk Name')
@click.option('-s', '--size', 'disk_size', default=5,
              metavar='<size>', help='Disk Size in GB', type=click.INT)
@click.option('-i', '--id', 'disk_id', default=None,
              metavar='<disk_id>', help='Disk Id')
def disk(cmd_proc, operation, vdc, disk_name, disk_size, disk_id):
    """Operations with Independent Disks"""
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
    if 'list' == operation:
        headers = ['Disk', 'Size GB', 'Id', 'Owner']
        disks = cmd_proc.vca.get_disks(vdc)
        table = cmd_proc.disks_to_table(disks)
        if cmd_proc.json_output:
            json_object = {'disks':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available independent disks in '%s'"
                              ", profile '%s':" %
                              (vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    elif 'create' == operation:
        assert disk_name, "Disk name can't be empty"
        size = disk_size * cmd_proc.DISK_SIZE
        result = cmd_proc.vca.add_disk(vdc, disk_name, size)
        if result and len(result) > 0:
            if result[0]:
                utils.print_message('disk %s successfully created'
                                    % disk_name, cmd_proc)
            else:
                utils.print_error('disk %s could not be created'
                                  % disk_name, cmd_proc)
    elif 'delete' == operation:
        result = cmd_proc.vca.delete_disk(vdc, disk_name, disk_id)
        if result and len(result) > 0:
            if result[0]:
                utils.print_message('disk %s successfully deleted'
                                    % (disk_id if disk_id else disk_name),
                                    cmd_proc)
            else:
                utils.print_error('disk %s could not be deleted: %s'
                                  % (disk_name, result[1]),
                                  cmd_proc)
                sys.exit(1)
    else:
        utils.print_error('not implemented', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list]',
                type=click.Choice(
                    ['list']))
@click.option('-v', '--vdc', default=None,
              metavar='<vdc>', help='Virtual Data Center Name')
@click.option('-a', '--vapp', 'vapp', default=None,
              metavar='<vapp>', help='vApp name')
def vm(cmd_proc, operation, vdc, vapp):
    """Operations with VMs"""
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
    if 'list' == operation:
        headers = ['VM', "vApp", "Status", "IPs", "MACs", "Networks",
                   "vCPUs", "Memory (GB)", "CD/DVD", "OS", "Owner"]
        table = cmd_proc.vms_to_table(the_vdc, vapp)
        if cmd_proc.json_output:
            json_object = {'vms':
                           utils.table_to_json(headers, table)}
            utils.print_json(json_object, cmd_proc=cmd_proc)
        else:
            utils.print_table("Available VMs in '%s', profile '%s':" %
                              (vdc, cmd_proc.profile),
                              headers, table, cmd_proc)
    else:
        utils.print_error('not implemented', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()
