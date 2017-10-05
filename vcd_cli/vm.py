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
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vsphere import VSphere
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd


@vcd.group(short_help='manage VMs')
@click.pass_context
def vm(ctx):
    """Manage VMs in vCloud Director.

\b
    Examples
        vcd vm list
            Get list of VMs in current virtual datacenter.
\b
        vcd vm run myvapp myvm vcs.server.com 'administrator@vsphere.local' \\
            'pa$$w0rd' root 'pa$$w0rd' /usr/bin/date '>/tmp/now.txt'
            Run command on guest OS, requires access to vCenter.
\b
        vcd vm upload myvapp myvm vcs.server.com 'administrator@vsphere.local' \\
            'pa$$w0rd' root 'pa$$w0rd' ./my-commands.sh /tmp/my-commands.sh
            Upload file to guest OS, requires access to vCenter.
\b
        vcd vm download myvapp myvm vcs.server.com 'administrator@vsphere.local' \\
            'pa$$w0rd' root 'pa$$w0rd' /etc/hosts
            Download file from guest OS, requires access to vCenter.
\b
        vcd vm download myvapp myvm vcs.server.com 'administrator@vsphere.local' \\
            'pa$$w0rd' root 'pa$$w0rd' /etc/hosts ./hosts.txt
            Download file from guest OS and save locally, requires access to vCenter.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)


@vm.command(short_help='list VMs')
@click.pass_context
def list(ctx):
    try:
        raise Exception('not implemented')
    except Exception as e:
        stderr(e, ctx)


@vm.command(short_help='show VM details')
@click.pass_context
@click.argument('vapp-name',
                metavar='<vapp-name>',
                required=True)
@click.argument('vm-name',
                metavar='<vm-name>',
                required=True)
def info(ctx, vapp_name, vm_name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(vapp_name)
        vapp = VApp(client, resource=vapp_resource)
        result = {}
        result['primary_ip'] = vapp.get_primary_ip(vm_name)
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@vm.command(short_help='run command in guest')
@click.pass_context
@click.argument('vapp-name')
@click.argument('vm-name')
@click.argument('vc-host')
@click.argument('vc-user')
@click.argument('vc-password')
@click.argument('guest-user')
@click.argument('guest-password')
@click.argument('command')
@click.argument('args')
def run(ctx, vapp_name, vm_name, vc_host, vc_user, vc_password,
        guest_user, guest_password, command, args):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(vapp_name)
        va = VApp(client, resource=vapp_resource)
        vs = VSphere(vc_host,
                     vc_user,
                     vc_password)
        moid = va.get_vm_moid(vm_name)
        vs.connect()
        vm = vs.get_vm_by_moid(moid)
        result = vs.execute_program_in_guest(
                    vm,
                    guest_user,
                    guest_password,
                    command,
                    args,
                    True
                    )
        click.secho('exit_code=%s' % result)
    except Exception as e:
        stderr(e, ctx)


@vm.command(short_help='upload file to guest')
@click.pass_context
@click.argument('vapp-name')
@click.argument('vm-name')
@click.argument('vc-host')
@click.argument('vc-user')
@click.argument('vc-password')
@click.argument('guest-user')
@click.argument('guest-password')
@click.argument('input', type=click.File('rb'))
@click.argument('output')
def upload(ctx, vapp_name, vm_name, vc_host, vc_user, vc_password,
           guest_user, guest_password, input, output):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        vapp_resource = vdc.get_vapp(vapp_name)
        va = VApp(client, resource=vapp_resource)
        vs = VSphere(vc_host,
                     vc_user,
                     vc_password)
        moid = va.get_vm_moid(vm_name)
        vs.connect()
        vm = vs.get_vm_by_moid(moid)
        data = input.read()
        result = vs.upload_file_to_guest(
                    vm,
                    guest_user,
                    guest_password,
                    data,
                    output)
        click.secho('result=%s' % result)
    except Exception as e:
        stderr(e, ctx)


@vm.command(short_help='download file from guest')
@click.pass_context
@click.argument('vapp-name')
@click.argument('vm-name')
@click.argument('vc-host')
@click.argument('vc-user')
@click.argument('vc-password')
@click.argument('guest-user')
@click.argument('guest-password')
@click.argument('source')
@click.argument('output', type=click.File('wb'), required=False)
def download(ctx, vapp_name, vm_name, vc_host, vc_user, vc_password,
             guest_user, guest_password, source, output):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, vdc_href=vdc_href)
        vapp_resource = vdc.get_vapp(vapp_name)
        va = VApp(client, resource=vapp_resource)
        vs = VSphere(vc_host,
                     vc_user,
                     vc_password)
        moid = va.get_vm_moid(vm_name)
        vs.connect()
        vm = vs.get_vm_by_moid(moid)
        result = vs.download_file_from_guest(
                    vm,
                    guest_user,
                    guest_password,
                    source)
        if result.status_code == 200:
            if output is None:
                click.secho(result.content)
            else:
                output.write(result.content)
        else:
            raise Exception(result.content)
    except Exception as e:
        stderr(e, ctx)
