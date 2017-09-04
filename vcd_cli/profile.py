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
from vcd_cli.profiles import Profiles
from vcd_cli.vcd import vcd
import yaml


@vcd.command(short_help='manage profiles')
@click.pass_context
def profile(ctx):
    """Manage user profiles

    """
    profiles = Profiles.load()
    click.echo(yaml.dump(profiles.data, default_flow_style=False))
