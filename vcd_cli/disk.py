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
import humanfriendly
from pyvcloud.vcd.client import VCLOUD_STATUS_MAP
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.utils import disk_to_dict
from pyvcloud.vcd.utils import extract_id
from pyvcloud.vcd.vdc import VDC

from vcd_cli.utils import extract_name_and_id
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false
from vcd_cli.vcd import vcd


@vcd.group(short_help='manage independent disks')
@click.pass_context
def disk(ctx):
    """Manage independent disks in vCloud Director.

\b
    Examples
        vcd disk list
            Get list of independent disks in the current virtual datacenter.
\b
        vcd disk create disk1 10g --description '10 GB Disk'
            Create a 10 GB independent disk using the default storage profile.
\b
        vcd disk info disk1
            Get details of the disk named 'disk1'.
\b
        vcd disk info id:91b3a2e2-fd02-412b-9914-9974d60b2351
            Get details of the disk for a given id.
\b
        vcd disk update disk1 --size 20g --description "new description"
            Update an existing independent disk with new size and description.
\b
        vcd disk delete disk1
            Delete an existing independent disk named 'disk1'.
    """

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)


@disk.command('info', short_help='show details of an independent disk')
@click.pass_context
@click.argument('name', metavar='<name>')
def info(ctx, name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)

        name, id = extract_name_and_id(name)
        disk = vdc.get_disk(name=name, disk_id=id)

        stdout(disk_to_dict(disk), ctx)
    except Exception as e:
        stderr(e, ctx)


@disk.command('list', short_help='list independent disks')
@click.pass_context
def list_disks(ctx):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        disks = vdc.get_disks()
        result = []
        for disk in disks:
            attached_vms = ''
            if hasattr(disk, 'attached_vms') and \
               hasattr(disk.attached_vms, 'VmReference'):
                attached_vms = disk.attached_vms.VmReference.get('name')
            result.append({'name': disk.get('name'),
                           'id': extract_id(disk.get('id')),
                           'owner': disk.Owner.User.get('name'),
                           'size': humanfriendly.format_size(
                               int(disk.get('size'))),
                           'size_bytes': disk.get('size'),
                           'status': VCLOUD_STATUS_MAP.get(int(
                               disk.get('status'))),
                           'vms_attached': attached_vms})
        stdout(result, ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)


@disk.command(short_help='create an independent disk')
@click.pass_context
@click.argument('name', metavar='<name>')
@click.argument('size', metavar='<size in bytes>')
@click.option('-d',
              '--description',
              'description',
              required=False,
              metavar='<description>',
              help='Description of the new disk')
@click.option('-s',
              '--storage-profile',
              'storage_profile',
              required=False,
              metavar='<name>',
              help='Name of the Storage Profile to be used for the new disk.')
@click.option('-i',
              '--iops',
              'iops',
              required=False,
              metavar='<iops>',
              help='Iops requirements of the new disk')
def create(ctx, name, size, description, storage_profile, iops):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        disk_resource = vdc.create_disk(
            name=name,
            size=humanfriendly.parse_size(size),
            description=description,
            storage_profile_name=storage_profile,
            iops=iops)
        stdout(disk_resource.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)


@disk.command(short_help='delete a disk')
@click.pass_context
@click.argument('name', metavar='<name>')
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to delete the disk?')
def delete(ctx, name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)

        name, id = extract_name_and_id(name)
        task = vdc.delete_disk(name=name, disk_id=id)

        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@disk.command('update', short_help='update disk')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-n',
              '--new-name',
              'new_name',
              required=False,
              metavar='<name>',
              help='New name of the disk')
@click.option('-s',
              '--size',
              'size',
              metavar='<size>',
              required=False,
              help='New size of the disk in bytes')
@click.option('-d',
              '--description',
              'description',
              required=False,
              metavar='<description>',
              help='New Description of the disk')
@click.option('-S',
              '--storage-profile',
              'storage_profile',
              required=False,
              metavar='<name>',
              help='Name of the new Storage Profile to be used for the disk.')
@click.option('-i',
              '--iops',
              'iops',
              required=False,
              metavar='<iops>',
              default=None,
              help='New iops requirement of the disk')
def update(ctx, name, new_name, size, description, storage_profile, iops):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)

        new_size = None
        if size is not None:
            new_size = humanfriendly.parse_size(size)

        name, id = extract_name_and_id(name)
        task = vdc.update_disk(name=name,
                               disk_id=id,
                               new_name=new_name,
                               new_size=new_size,
                               new_description=description,
                               new_storage_profile_name=storage_profile,
                               new_iops=iops)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@disk.command('change-owner', short_help='change owner of disk')
@click.pass_context
@click.argument('disk-name', metavar='<disk-name>')
@click.argument('user_name', metavar='<user_name>')
def change_disk_owner(ctx, disk_name, user_name):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)

        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        user_resource = org.get_user(user_name)

        disk_name, disk_id = extract_name_and_id(disk_name)
        vdc.change_disk_owner(user_href=user_resource.get('href'),
                              name=disk_name,
                              disk_id=disk_id)

        stdout('Owner of disk \'%s\' changed to \'%s\'' %
               (disk_name, user_name), ctx)
    except Exception as e:
        stderr(e, ctx)
