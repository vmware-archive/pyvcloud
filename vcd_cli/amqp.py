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
import json
from pyvcloud.vcd.amqp import AmqpService
from pyvcloud.vcd.utils import to_dict
import sys
from vcd_cli.system import system
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout


@system.group(short_help='manage AMQP settings')
@click.pass_context
def amqp(ctx):
    """Manages AMQP settings in vCloud Director.

\b
    Examples
        vcd system amqp info
            Get details of AMQP configuration.
\b
        vcd -j system amqp info > amqp-config.json
            Save current AMQP configuration to file.
\b
        vcd system amqp test amqp-config.json --password guest
            Test AMQP configuration.
\b
        vcd system amqp set amqp-config.json --password guest
            Set AMQP configuration.
    """  # NOQA
    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@amqp.command(short_help='show AMQP settings')
@click.pass_context
def info(ctx):
    try:
        client = ctx.obj['client']
        amqp = AmqpService(client)
        settings = amqp.get_settings()
        stdout(to_dict(settings), ctx)
    except Exception as e:
        stderr(e, ctx)


@amqp.command(short_help='test AMQP settings')
@click.pass_context
@click.option('-p', '--password', prompt=True, hide_input=True,
              confirmation_prompt=False)
@click.argument('config-file', type=click.File('rb'), metavar='<config-file>',
                required=True)
def test(ctx, password, config_file):
    try:
        client = ctx.obj['client']
        config = json.loads(config_file.read(1024).decode(
            sys.getfilesystemencoding()))
        amqp = AmqpService(client)
        result = amqp.test_config(config, password)
        if result['Valid'].text == 'true':
            stdout('The configuration is valid.', ctx)
        else:
            raise Exception('The configuration is invalid: %s' %
                            result['error'].get('message'))
    except Exception as e:
        stderr(e, ctx)


@amqp.command('set', short_help='configure AMQP settings')
@click.pass_context
@click.option('-p', '--password', prompt=True, hide_input=True,
              confirmation_prompt=False)
@click.argument('config-file', type=click.File('rb'), metavar='<config-file>',
                required=True)
def set_config(ctx, password, config_file):
    try:
        client = ctx.obj['client']
        config = json.loads(config_file.read(1024).decode(
            sys.getfilesystemencoding()))
        amqp = AmqpService(client)
        amqp.set_config(config, password)
        stdout('Updated AMQP configuration.', ctx)
    except Exception as e:
        stderr(e, ctx)
