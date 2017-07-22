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
from vcd_cli.utils import as_metavar
from vcd_cli.utils import restore_session
from vcd_cli.vcd import cli
from vcd_cli.system import system
from vcd_cli.vcd import CONTEXT_SETTINGS
from pyvcloud.vcd.extension import Extension
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.profiles import Profiles


@system.group(short_help='manage AMQP settings')
@click.pass_context
def amqp(ctx):
    """Manages AMQP settings in vCloud Director.

\b
    Examples
        vcd amqp info
            Get details of AMQP configuration.
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
        raise Exception('not implemented')
    except Exception as e:
        stderr(e, ctx)
