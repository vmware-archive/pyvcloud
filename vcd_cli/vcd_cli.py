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
OPERATIONS = ['list',
              'create',
              'delete',
              'info']


def as_metavar(values):
    result = ''
    for v in values:
        if len(result) > 0:
            result += '|'
        result += v
    result = '[%s]' % result
    return result


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
    """VMware vCloud Command Line Interface."""
    if ctx.invoked_subcommand is None:
        click.secho(ctx.get_help())
        return
    if ctx.invoked_subcommand not in ['login', 'profile']:
        profiles = Profiles.load()
        token = profiles.get('token')
        if token is None or len(token) == 0:
            click.secho('not logged in', fg='red', err=True)
            ctx.exit(1)
        if not profiles.get('verify'):
            if profiles.get('disable_warnings'):
                pass
            else:
                click.secho('InsecureRequestWarning: '
                            'Unverified HTTPS request is being made. '
                            'Adding certificate verification is strongly '
                            'advised.', fg='yellow', err=True)
            requests.packages.urllib3.disable_warnings()
        client = Client(profiles.get('host'),
                        api_version=profiles.get('api_version'),
                        verify_ssl_certs=profiles.get('verify'),
                        log_file='vcd.log',
                        log_headers=True,
                        log_bodies=True
                       )
        try:
            client.rehydrate(profiles)
            # logger.debug('restored session as %s' % \
            #             profiles.get('user'),
            #             fg='blue')
            ctx.obj = {}
            ctx.obj['client'] = client
        except Exception as e:
            tb = traceback.format_exc()
            click.secho('can\'t restore session, please re-login:\n%s' % tb,
                        fg='red', err=True)



@cli.command()
@click.pass_context
def version(ctx):
    """Show version"""
    click.secho('vcd-cli, VMware vCloud Command Line Interface, version %s' %
                pkg_resources.require("vca-cli")[0].version)

@cli.command()
@click.pass_context
@click.option('-s',
              '--show-password',
              'show_password',
              is_flag=True,
              default=False,
              help='Show encrypted password')
def status(ctx, show_password):
    """Show current status"""
    pass

@cli.command()
@click.pass_context
@click.argument('host',
                metavar='host')
@click.argument('org',
                metavar='organization')
@click.argument('user',
                metavar='user')
@click.option('-p',
              '--password',
              prompt=True,
              metavar='<password>',
              confirmation_prompt=False,
              envvar='VCD_PASSWORD',
              hide_input=True,
              help='Password')
@click.option('-d',
              '--do-not-save-password',
              is_flag=True,
              default=False,
              help='Do not save password for expired sessions')
@click.option('-V',
              '--version',
              'api_version',
              default=API_CURRENT_VERSIONS[-1],
              metavar=as_metavar(API_CURRENT_VERSIONS),
              type=click.Choice(API_CURRENT_VERSIONS),
              help='API version')
@click.option('-s/-i',
              '--verify-ssl-certs/--no-verify-ssl-certs',
              required=False,
              default=True,
              help='Verify SSL certificates')
@click.option('-w',
              '--disable-warnings',
              is_flag=True,
              required=False,
              default=False,
              help='Do not display warnings when not verifying SSL ' + \
                   'certificates')
def login(ctx, user, host, password, do_not_save_password,
          api_version, org, verify_ssl_certs, disable_warnings):
    """Login to vCloud"""
    if not verify_ssl_certs:
        if disable_warnings:
            pass
        else:
            click.secho('InsecureRequestWarning: '
                        'Unverified HTTPS request is being made. '
                        'Adding certificate verification is strongly '
                        'advised.', fg='yellow', err=True)
        requests.packages.urllib3.disable_warnings()
    client = Client(host,
                    api_version=api_version,
                    verify_ssl_certs=verify_ssl_certs,
                    log_file='vcd.log',
                    log_headers=True,
                    log_bodies=True
                   )
    try:
        client.set_credentials(BasicLoginCredentials(user, org, password))
        wkep = {}
        for ep in _WellKnownEndpoint:
            wkep[ep.name] = client._session_endpoints[ep]
        profiles = Profiles.load()
        profiles.update(host, org, user,
            client._session.headers['x-vcloud-authorization'],
            api_version,
            wkep,
            verify_ssl_certs,
            disable_warnings,
            debug=True)
        click.secho('%s logged in' % (user), fg='blue')
    except Exception as e:
        tb = traceback.format_exc()
        click.secho('can\'t log in:\n%s' % tb, fg='red', err=True)


@cli.command()
@click.pass_context
def logout(ctx):
    """Logout from vCloud"""
    profiles = Profiles.load()
    profiles.set('token', '')
    click.secho('%s logged out' % (profiles.get('user')), fg='blue')


if __name__ == '__main__':
    cli()
else:
    import vcd_cluster  # NOQA
    import vcd_org  #NOQA
    import vcd_profile  # NOQA
