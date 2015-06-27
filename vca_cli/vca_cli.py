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


import click
import pkg_resources


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('-v', '--version', is_flag=True, help='Show version')
@click.pass_context
def cli(ctx=None, version=False):
    """VMware vCloud Air Command Line Interface."""
    
    if version:
        version = pkg_resources.require("vca-cli")[0].version
        version_pyvcloud = '?'#pkg_resources.require("pyvcloud")[0].version
        msg = 'vca-cli version %s (pyvcloud: %s)' % (version, version_pyvcloud)
        click.secho(msg, fg='blue')


