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
import os
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.utils import task_to_dict
from pyvcloud.vcd.utils import to_dict
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import cli


@cli.group(short_help='work with catalogs')
@click.pass_context
def catalog(ctx):
    """Work with catalogs in current organization.

\b
    Examples
        vcd catalog list
            Get list of catalogs in current organization.
\b
        vcd catalog create 'my catalog' -d 'My Catalog of Templates'
            Create catalog.
\b
        vcd catalog delete 'my catalog'
            Delete catalog.
\b
        vcd catalog info 'my catalog'
            Get details of a catalog.
\b
        vcd catalog info 'my catalog' linux-template
            Get details of a catalog item.
\b
        vcd catalog list-items 'my catalog'
            Get list of items in a catalog.
\b
        vcd catalog upload 'my catalog' installer.iso
            Upload media file to a catalog.
\b
        vcd catalog download 'my catalog' installer.iso
            Download media file from catalog.
\b
        vcd catalog delete-item 'my catalog' installer.iso
            Delete media file from catalog.
    """  # NOQA
    if ctx.invoked_subcommand not in [None, 'item']:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@catalog.command(short_help='show catalog or item details')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>',
                required=True)
@click.argument('item-name',
                metavar='[item-name]',
                required=False,
                default=None)
def info(ctx, catalog_name, item_name):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        if item_name is None:
            result = org.get_catalog(catalog_name)
        else:
            result = org.get_catalog_item(catalog_name, item_name)
        stdout(to_dict(result), ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='list catalogs')
@click.pass_context
def list(ctx):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        result = org.list_catalogs()
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='create a catalog')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>')
@click.option('-d',
              '--description',
              required=False,
              default='',
              metavar='[description]')
def create(ctx, catalog_name, description):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        result = org.create_catalog(catalog_name, description)
        stdout(task_to_dict(result), ctx, show_id=True)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='delete a catalog')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>')
def delete(ctx, catalog_name):
    try:
        client = ctx.obj['client']
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href)
        org.delete_catalog(catalog_name)
        stdout('Catalog deleted.', ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='share a catalog')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>',
                required=True)
def share(ctx, catalog_name):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        org.share_catalog(catalog_name, True)
        stdout('Catalog shared.', ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command(short_help='unshare a catalog')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>',
                required=True)
def unshare(ctx, catalog_name):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        org.share_catalog(catalog_name, False)
        stdout('Catalog unshared.', ctx)
    except Exception as e:
        stderr(e, ctx)


def upload_callback(transferred, total):
    print('upload %s of %s bytes' % (transferred, total))


@catalog.command(short_help='upload file to catalog')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>')
@click.argument('file_name',
                type=click.Path(exists=True),
                metavar='<file-name>',
                required=True)
@click.option('-i',
              '--item-name',
              required=False,
              default=None,
              metavar='[item-name]')
@click.option('-p/-n',
              '--progress/--no-progress',
              is_flag=True,
              required=False,
              default=True,
              help='show progress')
def upload(ctx, catalog_name, file_name, item_name, progress):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        cb = upload_callback if progress else None
        result = org.upload_media(catalog_name,
                                  file_name,
                                  item_name,
                                  callback=cb)
        stdout(to_dict(result), ctx)
    except Exception as e:
        stderr(e, ctx)


def download_callback(transferred, total):
    print('download %s of %s bytes' % (transferred, total))


@catalog.command(short_help='download file from catalog')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>')
@click.argument('item-name',
                metavar='<item-name>',
                required=True,
                default=None)
@click.argument('file_name',
                type=click.Path(exists=False),
                metavar='[file-name]',
                default=None,
                required=False)
@click.option('-p/-n',
              '--progress/--no-progress',
              is_flag=True,
              required=False,
              default=True,
              help='show progress')
@click.option('-o',
              '--overwrite',
              is_flag=True,
              required=False,
              default=False,
              help='overwrite')
def download(ctx, catalog_name, item_name, file_name, progress, overwrite):
    try:
        save_as_name = item_name
        if file_name is not None:
            save_as_name = file_name
        if not overwrite and os.path.isfile(save_as_name):
            raise Exception('File exists.')
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        cb = download_callback if progress else None
        bytes_written = org.download_file(catalog_name,
                                          item_name,
                                          save_as_name,
                                          callback=cb)
        result = {'file': save_as_name, 'size': bytes_written}
        stdout(result, ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command('list-items', short_help='list catalog items')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>')
def list_items(ctx, catalog_name):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        items = org.list_catalog_items(catalog_name)
        stdout(items, ctx)
    except Exception as e:
        stderr(e, ctx)


@catalog.command('delete-item', short_help='delete a catalog item')
@click.pass_context
@click.argument('catalog-name',
                metavar='<catalog-name>')
@click.argument('item-name',
                metavar='<item-name>')
def delete_item(ctx, catalog_name, item_name):
    try:
        client = ctx.obj['client']
        org_name = ctx.obj['profiles'].get('org')
        in_use_org_href = ctx.obj['profiles'].get('org_href')
        org = Org(client, in_use_org_href, org_name == 'System')
        org.delete_catalog_item(catalog_name, item_name)
        stdout('Item deleted.', ctx)
    except Exception as e:
        stderr(e, ctx)
