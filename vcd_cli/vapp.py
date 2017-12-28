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

from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.utils import to_dict
from pyvcloud.vcd.utils import vapp_to_dict
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC

from vcd_cli.utils import is_sysadmin
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
    Description
        The vapp command manages vApps.
\b
        'vapp create' creates a new vApp in the current vDC. When '--catalog'
        and '--template' are not provided, it creates an empty vApp and VMs can
        be added later. When specifying a template in a catalog, it creates an
        instance of the catalog template.
\b
        'vapp add-vm' adds a VM to the vApp. When '--catalog' is used, the
        <source-vapp> parameter refers to a template in the specified catalog
        and the command will instantiate the <source-vm> found in the template.
        If '--catalog' is not used, <source-vapp> refers to another vApp in the
        vDC and the command will copy the <source-vm> found in the vApp. The
        name of the VM and other options can be customized when the VM is added
        to the vApp.
\b
    Examples
        vcd vapp list
            Get list of vApps in current virtual datacenter.
\b
        vcd vapp list vapp1
            Get list of VMs in vApp 'vapp1'.
\b
        vcd vapp info vapp1
            Get details of the vApp 'vapp1'.
\b
        vcd vapp create vapp1
            Create an empty vApp with name 'vapp1'.
\b
        vcd vapp create vapp1 --network net1
            Create an empty vApp connected to a network.
\b
        vcd vapp create vapp1 -c catalog1 -t template1
            Instantiate a vApp from a catalog template.
\b
        vcd vapp create vapp1 -c catalog1 -t template1 \\
                 --cpu 4 --memory 4096 --disk-size 20000 \\
                 --network net1 --ip-allocation-mode pool \\
                 --hostname myhost --vm-name vm1 --accept-all-eulas \\
                 --storage-profile '*'
            Instantiate a vApp with customized settings.
\b
        vcd vapp delete vapp1 --yes --force
            Delete a vApp.
\b
        vcd --no-wait vapp delete vapp1 --yes --force
            Delete a vApp without waiting for completion.
\b
        vcd vapp update-lease vapp1 7776000
            Set vApp lease to 90 days.
\b
        vcd vapp update-lease vapp1 0
            Set vApp lease to no expiration.
\b
        vcd vapp shutdown vapp1 --yes
            Gracefully shutdown a vApp.
\b
        vcd vapp power-off vapp1
            Power off a vApp.
\b
        vcd vapp power-on vapp1
            Power on a vApp.
\b
        vcd vapp capture vapp1 catalog1
            Capture a vApp as a template in a catalog.
\b
        vcd vapp attach vapp1 vm1 disk1
            Attach a disk to a VM in the given vApp.
\b
        vcd vapp detach vapp1 vm1 disk1
            Detach a disk from a VM in the given vApp.
\b
        vcd vapp add-disk vapp1 vm1 10000
            Add a disk of 10000 MB to a VM.
\b
        vcd vapp add-vm vapp1 template1.ova vm1 -c catalog1
            Add a VM to a vApp. Instantiate the source VM \'vm1\' that is in
            the \'template1.ova\' template in the \'catalog1\' catalog and
            place the new VM inside \'vapp1\' vApp.
    """

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
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        md = vapp.get_metadata()
        access_control_settings = vapp.get_access_control_settings()
        result = vapp_to_dict(vapp_resource, md, access_control_settings)
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command(short_help='attach disk to VM in vApp')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
@click.argument('vm-name',
                metavar='<vm-name>',
                required=True)
@click.argument('disk-name',
                metavar='<disk-name>',
                required=True)
@click.option('-i',
              '--id',
              'disk_id',
              required=False,
              metavar='<id>',
              help='Disk id')
def attach(ctx, vapp_name, vm_name, disk_name, disk_id):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        disk = vdc.get_disk(disk_name, disk_id)
        vapp_resource = vdc.get_vapp(vapp_name)
        vapp = VApp(client, resource=vapp_resource)
        task = vapp.attach_disk_to_vm(
            disk_href=disk.get('href'),
            vm_name=vm_name)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command(short_help='detach disk from VM in vApp')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
@click.argument('vm-name',
                metavar='<vm-name>',
                required=True)
@click.argument('disk-name',
                metavar='<disk-name>',
                required=True)
@click.option('-i',
              '--id',
              'disk_id',
              required=False,
              metavar='<id>',
              help='Disk id')
def detach(ctx, vapp_name, vm_name, disk_name, disk_id):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        disk = vdc.get_disk(disk_name, disk_id)
        vapp_resource = vdc.get_vapp(vapp_name)
        vapp = VApp(client, resource=vapp_resource)
        task = vapp.detach_disk_from_vm(
            disk_href=disk.get('href'),
            disk_type=disk.get('type'),
            disk_name=disk_name,
            vm_name=vm_name)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('list', short_help='list vApps')
@click.pass_context
@click.argument('name',
                metavar='[name]',
                required=False)
def list_vapps(ctx, name):
    try:
        client = ctx.obj['client']
        result = []
        if name is None:
            resource_type = 'adminVApp' if is_sysadmin(ctx) else 'vApp'
            qfilter = None
            attributes = None
        else:
            resource_type = 'adminVm' if is_sysadmin(ctx) else 'vm'
            qfilter = 'containerName==%s' % name
            attributes = ['name', 'containerName', 'ipAddress', 'status',
                          'memoryMB', 'numberOfCpus']
        q = client.get_typed_query(resource_type,
                                   query_result_format=QueryResultFormat.
                                   ID_RECORDS, qfilter=qfilter)
        records = list(q.execute())
        if len(records) == 0:
            result = 'not found'
        else:
            for r in records:
                result.append(to_dict(r, resource_type=resource_type,
                                      attributes=attributes))
        stdout(result, ctx, show_id=False)
    except Exception as e:
        stderr(e, ctx)


@vapp.command(short_help='create a vApp')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-d',
              '--description',
              metavar='text',
              help='vApp description')
@click.option('-c',
              '--catalog',
              metavar='name',
              help='Catalog where the template is')
@click.option('-t',
              '--template',
              metavar='name',
              help='Name of the template')
@click.option('-n',
              '--network',
              'network',
              required=False,
              default=None,
              metavar='name',
              help='Network')
@click.option('ip_allocation_mode',
              '-i',
              '--ip-allocation-mode',
              type=click.Choice(['dhcp', 'pool']),
              required=False,
              default='dhcp',
              metavar='mode',
              help='IP allocation mode')
@click.option('-m',
              '--memory',
              'memory',
              required=False,
              default=None,
              metavar='<MB>',
              type=click.INT,
              help='Amount of memory in MB')
@click.option('-u',
              '--cpu',
              'cpu',
              required=False,
              default=None,
              metavar='<virtual-cpus>',
              type=click.INT,
              help='Number of CPUs')
@click.option('-k',
              '--disk-size',
              'disk_size',
              required=False,
              default=None,
              metavar='<MB>',
              type=click.INT,
              help='Size of the vm home disk in MB')
@click.option('-v',
              '--vm-name',
              required=False,
              default=None,
              metavar='name',
              help='VM name')
@click.option('-o',
              '--hostname',
              metavar='hostname',
              help='Hostname')
@click.option('storage_profile',
              '-s',
              '--storage-profile',
              required=False,
              default=None,
              metavar='name',
              help='Name of the storage profile for the vApp')
@click.option('-a',
              '--accept-all-eulas',
              is_flag=True,
              default=False,
              help='Accept all EULAs')
def create(ctx, name, description, catalog, template, network, memory, cpu,
           disk_size, ip_allocation_mode, vm_name, hostname, storage_profile,
           accept_all_eulas):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        if catalog is None and template is None:
            vapp_resource = vdc.create_vapp(name, description=description,
                                            network=network,
                                            accept_all_eulas=accept_all_eulas)
        else:
            vapp_resource = vdc.instantiate_vapp(
                name,
                catalog,
                template,
                network=network,
                memory=memory,
                cpu=cpu,
                disk_size=disk_size,
                deploy=True,
                power_on=True,
                accept_all_eulas=accept_all_eulas,
                cust_script=None,
                ip_allocation_mode=ip_allocation_mode,
                vm_name=vm_name,
                hostname=hostname,
                storage_profile=storage_profile)
        stdout(vapp_resource.Tasks.Task[0], ctx)
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
        vdc = VDC(client, href=vdc_href)
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
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        if storage_seconds is None:
            storage_seconds = runtime_seconds
        task = vapp.set_lease(runtime_seconds, storage_seconds)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('change-owner', short_help='change vApp owner')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
@click.argument('user-name',
                metavar='<user-name>',
                required=True)
def change_owner(ctx, vapp_name, user_name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        user_resource = org.get_user(user_name)
        vapp_resource = vdc.get_vapp(vapp_name)
        vapp = VApp(client, resource=vapp_resource)
        vapp.change_owner(user_resource.get('href'))
        stdout('vapp owner changed', ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('power-off', short_help='power off a vApp')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to power off the vApp?')
@click.option('-f',
              '--force',
              is_flag=True,
              help='Force power off running vApps')
def power_off(ctx, name, force):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        task = vapp.power_off()
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('power-on', short_help='power on a vApp')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def power_on(ctx, name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        task = vapp.power_on()
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('shutdown', short_help='shutdown a vApp')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to shutdown the vApp?')
def shutdown(ctx, name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        task = vapp.shutdown()
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command(short_help='save a vApp as a template')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('catalog',
                metavar='<catalog>',
                required=True)
@click.argument('template',
                metavar='[template]',
                required=False)
@click.option('-i',
              '--identical',
              'customizable',
              flag_value='identical',
              help='Make identical copy')
@click.option('-c',
              '--customizable',
              'customizable',
              flag_value='customizable',
              default=True,
              help='Make copy customizable during instantiation')
def capture(ctx, name, catalog, template, customizable):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        catalog_resource = org.get_catalog(catalog)
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        if template is None:
            template = vapp_resource.get('name')
        task = org.capture_vapp(
                     catalog_resource,
                     vapp_href=vapp_resource.get('href'),
                     catalog_item_name=template,
                     description='',
                     customize_on_instantiate=customizable == 'customizable')
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('add-disk', short_help='add disk to vm')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('vm-name',
                required=True,
                metavar='<vm-name>')
@click.argument('size',
                metavar='<size>',
                required=True,
                type=click.INT)
@click.option('storage_profile',
              '-s',
              '--storage-profile',
              required=False,
              default=None,
              metavar='<storage-profile>',
              help='Name of the storage profile for the new disk')
def add_disk(ctx, name, vm_name, size, storage_profile):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        task = vapp.add_disk_to_vm(vm_name, size)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@vapp.command(short_help='set active vApp')
@click.pass_context
@click.argument('name', metavar='<name>', required=True)
def use(ctx, name):
    try:
        client = ctx.obj['client']
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        in_use_vdc_name = ctx.obj['profiles'].get('vdc_in_use')
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        ctx.obj['profiles'].set('vapp_in_use', str(name))
        ctx.obj['profiles'].set('vapp_href', str(vapp.href))
        message = 'now using org: \'%s\', vdc: \'%s\', vApp: \'%s\'.' % \
                  (in_use_org_name, in_use_vdc_name, name)
        stdout({
            'org': in_use_org_name,
            'vdc': in_use_vdc_name,
            'vapp': name
        }, ctx, message)
    except Exception as e:
        stderr(e, ctx)


@vapp.command('add-vm', short_help='add VM to vApp')
@click.pass_context
@click.argument('name',
                metavar='<target-vapp>',
                required=True)
@click.argument('source-vapp',
                metavar='<source-vapp>',
                required=True)
@click.argument('source-vm',
                metavar='<source-vm>',
                required=True)
@click.option('-c',
              '--catalog',
              metavar='name',
              help='Name of the catalog if the source vApp is a template')
@click.option('-t',
              '--target-vm',
              metavar='name',
              help='Rename the target VM with this name')
@click.option('-o',
              '--hostname',
              metavar='hostname',
              help='Customize VM and set hostname in the guest OS')
@click.option('-n',
              '--network',
              metavar='name',
              help='vApp network to connect to')
@click.option('ip_allocation_mode',
              '-i',
              '--ip-allocation-mode',
              type=click.Choice(['dhcp', 'pool']),
              required=False,
              default='dhcp',
              metavar='mode',
              help='IP allocation mode')
@click.option('storage_profile',
              '-s',
              '--storage-profile',
              metavar='name',
              help='Name of the storage profile for the VM')
@click.option('--password-auto',
              is_flag=True,
              help='Autogenerate administrator password')
@click.option('--accept-all-eulas',
              is_flag=True,
              help='Accept all EULAs')
def add_vm(ctx, name, source_vapp, source_vm, catalog, target_vm, hostname,
           network, ip_allocation_mode, storage_profile, password_auto,
           accept_all_eulas):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        source_vapp_resource = None
        if catalog is None:
            source_vapp_resource = vdc.get_vapp(source_vapp)
        else:
            catalog_item = org.get_catalog_item(catalog, source_vapp)
            source_vapp_resource = client.get_resource(
                catalog_item.Entity.get('href'))
        assert source_vapp_resource is not None
        vapp_resource = vdc.get_vapp(name)
        vapp = VApp(client, resource=vapp_resource)
        spec = {'source_vm_name': source_vm, 'vapp': source_vapp_resource}
        if target_vm is not None:
            spec['target_vm_name'] = target_vm
        if hostname is not None:
            spec['hostname'] = hostname
        if network is not None:
            spec['network'] = network
            spec['ip_allocation_mode'] = ip_allocation_mode
        if storage_profile is not None:
            spec['storage_profile'] = vdc.get_storage_profile(storage_profile)
        if password_auto is not None:
            spec['password_auto'] = password_auto
        task = vapp.add_vms([spec], all_eulas_accepted=accept_all_eulas)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)
