# vCloud Air CLI 0.1
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


import os
import click
import pkg_resources
import requests
from vca_cli_utils import VcaCliUtils


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
default_operation = 'list'


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('-p', '--profile', default='default',
              metavar='<profile>', help='Profile id')
@click.option('-f', '--profile-file', default='~/.vcarc',
              metavar='<file>', help='Profile file', type=click.Path())
@click.option('-v', '--version', is_flag=True, help='Show version')
@click.option('-d', '--debug', is_flag=True, help='Enable debug')
@click.option('-j', '--json', 'json_output',
              is_flag=True, help='Results as JSON object')
@click.option('-x', '--xml', 'xml_output',
              is_flag=True, help='Results as XML document')
@click.option('-i', '--insecure', is_flag=True,
              help='Perform insecure SSL connections')
@click.pass_context
def cli(ctx=None, profile=None, profile_file=None, version=None, debug=None,
        json_output=None, xml_output=None, insecure=None):
    """VMware vCloud Air Command Line Interface."""
    if version:
        version = pkg_resources.require("vca-cli")[0].version
        version_pyvcloud = pkg_resources.require("pyvcloud")[0].version
        msg = 'vca-cli version %s (pyvcloud: %s)' % (version, version_pyvcloud)
        click.secho(msg, fg='blue')
        return
    if ctx.invoked_subcommand is None:
        help_text = ctx.get_help()
        print(help_text)
        return
    utils = VcaCliUtils()
    if insecure:
        utils.print_warning('InsecureRequestWarning: ' +
                            'Unverified HTTPS request is being made. ' +
                            'Adding certificate verification is strongly ' +
                            'advised.', ctx)
        requests.packages.urllib3.disable_warnings()
    profile_file_fq = os.path.expanduser(profile_file)
    utils.load_context(ctx, profile, profile_file_fq)


@cli.command()
@click.pass_context
def status(ctx):
    """Show current status"""
    pass
