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
from pyvcloud.vcd.client import _WellKnownEndpoint
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.utils import to_dict
from vcd_cli.vcd import vcd


@vcd.group(short_help='manage system settings')
@click.pass_context
def system(ctx):
    """Manage system settings in vCloud Director."""  # NOQA

    if ctx.invoked_subcommand is not None:
        try:
            restore_session(ctx)
        except Exception as e:
            stderr(e, ctx)


@system.command(short_help='show system details')
@click.pass_context
def info(ctx):
    try:
        client = ctx.obj['client']
        result = client.get_resource(
            client._session_endpoints[_WellKnownEndpoint.ADMIN])
        stdout(to_dict(result), ctx)
    except Exception as e:
        stderr(e, ctx)


if __name__ == '__main__':
    pass
else:
    from vcd_cli import amqp  # NOQA
    from vcd_cli import extension  # NOQA
