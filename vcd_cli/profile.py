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
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import vcd

import yaml


@vcd.command(short_help='manage profiles')
@click.pass_context
def profile(ctx):
    """Manage user profiles

    """

    profiles = Profiles.load()
    click.echo(yaml.dump(profiles.data, default_flow_style=False))


@vcd.command(short_help='current resources in use')
@click.pass_context
def pwd(ctx):
    """Current resources in use

    """

    try:
        restore_session(ctx)
        host = ctx.obj['profiles'].get('host')
        user = ctx.obj['profiles'].get('user')
        in_use_org_name = ctx.obj['profiles'].get('org_in_use')
        in_use_vdc_name = ctx.obj['profiles'].get('vdc_in_use')
        in_use_vapp_name = ctx.obj['profiles'].get('vapp_in_use')
        message = ('connected to %s as \'%s\'\n' +
                   'using org: \'%s\', vdc: \'%s\', vApp: \'%s\'.') % \
                  (host, user, in_use_org_name, in_use_vdc_name,
                   in_use_vapp_name)
        stdout({
            'host': host,
            'user': user,
            'org': in_use_org_name,
            'vdc': in_use_vdc_name,
            'vapp': in_use_vapp_name
        }, ctx, message)
    except Exception as e:
        stderr(e, ctx)
