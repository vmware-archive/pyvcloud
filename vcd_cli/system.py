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
from vcd_cli.vcd import as_metavar
from vcd_cli.vcd import cli
from vcd_cli.vcd import CONTEXT_SETTINGS
from pyvcloud.vcd.extension import Extension
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout


@cli.group(short_help='manage system settings')
@click.pass_context
def system(ctx):
    """Manage system settings in vCloud Director.

    """  # NOQA
    pass


if __name__ == '__main__':
    pass
else:
    import amqp  #NOQA
    import extension  # NOQA
