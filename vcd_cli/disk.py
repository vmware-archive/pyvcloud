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
from pyvcloud.vcd.client import VCLOUD_STATUS_MAP
from pyvcloud.vcd.utils import disk_to_dict
from pyvcloud.vcd.utils import extract_id
from pyvcloud.vcd.vdc import VDC
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
            Get list of independent disks in current virtual datacenter.
\b
        vcd disk info disk1
            Get details of the disk named 'disk1'.
\b
        vcd disk info disk1 --id 91b3a2e2-fd02-412b-9914-9974d60b2351
            Get details of the disk named 'disk1' that has the supplied id.
\b
        vcd disk create disk1 100 --description '100 MB Disk'
            Create a new 100 MB independent disk named 'disk1' using the default storage profile.
\b
        vcd disk delete disk1
            Delete an existing independent disk named 'disk1'.
\b
        vcd disk update disk1 15
            Update an existing independent disk updating its size and storage profile.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            if not ctx.obj['profiles'].get('vdc_in_use') or \
               not ctx.obj['profiles'].get('vdc_href'):
                raise Exception('select a virtual datacenter')
        except Exception as e:
            stderr(e, ctx)


@disk.command('info', short_help='show disk details')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-i',
              '--id',
              'disk_id',
              required=False,
              metavar='<id>',
              help='Disk id')
def info(ctx, name, disk_id):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        disk = vdc.get_disk(name, disk_id=disk_id)
        stdout(disk_to_dict(disk), ctx)
    except Exception as e:
        stderr(e, ctx)


@disk.command('list', short_help='list disks')
@click.pass_context
def list_disks(ctx):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        disks = vdc.get_disks()
        result = []
        for disk in disks:
            result.append({'name': disk.get('name'),
                           'id': extract_id(disk.get('id')),
                           'size_MB': disk.get('size'),
                           'status': VCLOUD_STATUS_MAP.get(int(
                                disk.get('status')))})
        stdout(result, ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)


@disk.command(short_help='create a disk')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('size',
                metavar='<size>',
                required=True)
@click.option('-d',
              '--description',
              'description',
              required=False,
              metavar='<description>',
              help='Description')
@click.option('storage_profile',
              '-s',
              '--storage-profile',
              required=False,
              metavar='<storage-profile>',
              help='Name of Storage Profile to be used for new disk.')
def create(ctx, name, size, description, storage_profile):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        disk_resource = vdc.add_disk(name=name,
                                     size=size,
                                     description=description,
                                     storage_profile_name=storage_profile)
        stdout(disk_resource.Tasks.Task[0], ctx)
    except Exception as e:
        stderr(e, ctx)


@disk.command(short_help='delete a disk')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-i',
              '--id',
              'disk_id',
              required=False,
              metavar='<id>',
              help='Disk id')
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to delete the disk?')
def delete(ctx, name, disk_id):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        task = vdc.delete_disk(name, disk_id=disk_id)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)


@disk.command('update', short_help='update disk')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('size',
                metavar='<new-size>',
                required=False)
@click.option('-d',
              '--description',
              'description',
              required=False,
              metavar='<description>',
              help='New Description')
@click.option('new_name',
              '-new-name',
              '--new-name',
              required=False,
              metavar='<new-name>',
              help='New name')
@click.option('storage_profile',
              '-s',
              '--storage-profile',
              required=False,
              metavar='<storage-profile>',
              help='Name of new Storage Profile to be used for new disk.')
@click.option('-id',
              '--id',
              'disk_id',
              required=False,
              metavar='<id>',
              help='Disk id')
def update(ctx, name, size, description, new_name, storage_profile, disk_id):
    try:
        client = ctx.obj['client']
        vdc_href = ctx.obj['profiles'].get('vdc_href')
        vdc = VDC(client, href=vdc_href)
        task = vdc.update_disk(name,
                               size,
                               new_name,
                               description=description,
                               storage_profile_name=storage_profile,
                               disk_id=disk_id)
        stdout(task, ctx)
    except Exception as e:
        stderr(e, ctx)
