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
from cmd_proc import CmdProc
from vca_cli_utils import VcaCliUtils


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
default_operation = 'list'
utils = VcaCliUtils()


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('-p', '--profile', default=None,
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
    if insecure:
        utils.print_warning('InsecureRequestWarning: ' +
                            'Unverified HTTPS request is being made. ' +
                            'Adding certificate verification is strongly ' +
                            'advised.')
        requests.packages.urllib3.disable_warnings()
    profile_file_fq = os.path.expanduser(profile_file)
    ctx.obj = CmdProc(profile=profile, profile_file=profile_file_fq,
                      debug=debug, insecure=insecure)
    ctx.obj.load_config(profile, profile_file)


@cli.command()
@click.pass_obj
def status(cmd_proc):
    """Show current status"""
    print 'host: ' + cmd_proc.host
    print 'user: ' + cmd_proc.user
    # print 'token: ' + cmd_proc.token
    print 'pass: ' + cmd_proc.password


@cli.command()
@click.pass_obj
@click.argument('user')
@click.option('-p', '--password', prompt=True,
              confirmation_prompt=False, hide_input=True, help='Password')
@click.option('-s', '--save-password', is_flag=True,
              default=False, help='Save Password')
@click.option('-v', '--version', 'service_version',
              default='5.7', metavar='[5.5 | 5.6 | 5.7]',
              type=click.Choice(['5.5', '5.6', '5.7']), help='')
@click.option('-h', '--host', default='https://vca.vmware.com', 
              help='')
@click.option('-i', '--instance', default=None, help='Instance Id')
@click.option('-o', '--org', default=None, help='Organization Name')
@click.option('-c', '--host-score', 'host_score',
              default='https://score.vca.io', help='URL of the Score server')
def login(cmd_proc, user, host, password, save_password,
          service_version, instance, org, host_score):
    """Login to a vCloud service"""
    if not (host.startswith('https://') or host.startswith('http://')):
        host = 'https://' + host
    if not (host_score.startswith('https://') or 
            host_score.startswith('http://')):
        host_score = 'https://' + host_score
    try:
        result = cmd_proc.login(host, user, password, version=service_version)
        if result:
            utils.print_message('user logged in (type=%s)' % cmd_proc.vca.service_type, cmd_proc)
        else:
            utils.print_error('can\'t login', cmd_proc)
    except Exception as e:
        utils.print_error(str(e), cmd_proc)


@cli.command()
@click.pass_obj
def logout(cmd_proc):
    """Logout from a vCloud service"""
    pass
    # vca = _getVCA(ctx)
    # if vca:
    #     vca.logout()
    # _save_property(ctx.obj['profile'], 'token', 'None')
    # _save_property(ctx.obj['profile'], 'session_token', 'None')
    # _save_property(ctx.obj['profile'], 'org_url', 'None')
    # _save_property(ctx.obj['profile'], 'session_uri', 'None')
    # _save_property(ctx.obj['profile'], 'password', 'None')
    # print_message('Logout successful '
    #               'for profile \'%s\'' % ctx.obj['profile'], ctx)
