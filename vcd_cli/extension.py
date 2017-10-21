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
from pyvcloud.vcd.extension import Extension
from vcd_cli.system import system
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import abort_if_false


@system.group(short_help='manage extensions')
@click.pass_context
def extension(ctx):
    """Manage Extension Services in vCloud Director.

\b
    Examples
        vcd system extension list
            List available extension services.
\b
        vcd system extension create cse cse cse vcdext '/api/cluster, /api/cluster/.*, /api/cluster/.*/.*'
            Register a new extension service named 'cse'.
\b
        vcd system extension delete cse
            Unregister an extension service named 'cse'.
\b
        vcd system extension info cse
            Get details of an extension service named 'cse'.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
            ctx.obj['ext'] = Extension(ctx.obj['client'])
        except Exception as e:
            stderr(e, ctx)


@extension.command(short_help='list extensions')
@click.pass_context
def list(ctx):
    try:
        ext = ctx.obj['ext']
        stdout(ext.list_extensions(), ctx)
    except Exception as e:
        stderr(e, ctx)


@extension.command(short_help='show extension details')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
def info(ctx, name):
    try:
        ext = ctx.obj['ext']
        stdout(ext.get_extension(name), ctx)
    except Exception as e:
        stderr(e, ctx)


@extension.command(short_help='register new extension')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.argument('namespace',
                metavar='<namespace>',
                required=True)
@click.argument('routing-key',
                metavar='<routing-key>',
                required=True)
@click.argument('exchange',
                metavar='<exchange>',
                required=True)
@click.argument('patterns',
                metavar='<patterns>',
                required=True)
def create(ctx, name, namespace, routing_key, exchange, patterns):
    try:
        ext = ctx.obj['ext']
        ext.add_extension(name, namespace, routing_key, exchange,
                          patterns.split(','))
        stdout('Extension registered.', ctx)
    except Exception as e:
        import traceback
        traceback.print_exc()
        stderr(e, ctx)


@extension.command(short_help='unregister extension')
@click.pass_context
@click.argument('name',
                metavar='<name>',
                required=True)
@click.option('-y',
              '--yes',
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to unregister it?')
def delete(ctx, name):
    try:
        ext = Extension(ctx.obj['client'])
        ext.delete_extension(name)
    except Exception as e:
        stderr(e, ctx)
