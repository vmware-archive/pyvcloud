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
import pkg_resources
from profiles import Profiles
from pyvcloud.vcd.client import _get_session_endpoints
from pyvcloud.vcd.client import _WellKnownEndpoint
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import QueryResultFormat
import requests
import traceback
import yaml
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from colorama import Fore, Back, Style
from vcd_cli.utils import as_metavar
from vcd_cli.utils import restore_session


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
API_CURRENT_VERSIONS = ['5.5',
                        '5.6',
                        '6.0',
                        '13.0',
                        '17.0',
                        '20.0',
                        '21.0',
                        '22.0',
                        '23.0',
                        '24.0',
                        '25.0',
                        '26.0',
                        '27.0',
                        '28.0',
                        '29.0']

def load_user_plugins():
    pass


@click.group(context_settings=CONTEXT_SETTINGS,
             invoke_without_command=True)
@click.option('-d',
              '--debug',
              is_flag=True,
              help='Enable debug')
@click.option('-j',
              '--json',
              'json_output',
              is_flag=True,
              help='Results as JSON object')
@click.pass_context
def cli(ctx=None, debug=None,
        json_output=None):
    """VMware vCloud Director Command Line Interface."""
    if ctx.invoked_subcommand is None:
        click.secho(ctx.get_help())
        return


@cli.command(short_help='show version')
@click.pass_context
def version(ctx):
    """Show vcd-cli version"""
    ver = pkg_resources.require("vca-cli")[0].version
    ver_obj = {'product': 'vcd-cli',
               'description': 'VMware vCloud Director Command Line Interface',
               'version': ver}
    if not ctx.find_root().params['json_output']:
        ver_obj = '%s, %s, %s' % (ver_obj['product'],
                                  ver_obj['description'],
                                  ver_obj['version'])
    stdout(ver_obj, ctx)



if __name__ == '__main__':
    cli()
else:
    import cluster  #NOQA
    import login  #NOQA
    import org  #NOQA
    import profile  # NOQA
    import system  #NOQA
    import vapp  #NOQA
    import vdc  #NOQA
    load_user_plugins()
