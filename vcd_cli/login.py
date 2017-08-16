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
from pyvcloud.vcd.client import API_CURRENT_VERSIONS
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import get_links
import requests
from vcd_cli.profiles import Profiles
from vcd_cli.utils import as_metavar
from vcd_cli.utils import restore_session
from vcd_cli.utils import stderr
from vcd_cli.utils import stdout
from vcd_cli.vcd import cli


@cli.command(short_help='login to vCD')
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
              help='Do not display warnings when not verifying SSL ' +
                   'certificates')
@click.option('-v',
              '--vdc',
              required=False,
              default=None,
              help='virtual datacenter')
def login(ctx, user, host, password, api_version, org,
          verify_ssl_certs, disable_warnings, vdc):
    """Login to vCloud Director

\b
    Login to a vCloud Director service.
\b
    Examples
        vcd login vcd.vmware.com org1 usr1
            Log in to host 'vcd.vmware.com'.
\b
        vcd login test.mysp.com org1 usr -i -w
            Log in to a host with self-signed SSL certificate.
\b
    Environment Variables
        VCD_PASSWORD
            If this environment variable is set, the command will use its value
            as the password for login and will not ask for one. The --password
            option has precedence over the environment variable.

    """
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
        for endpoint in _WellKnownEndpoint:
            if endpoint in client._session_endpoints:
                wkep[endpoint.name] = client._session_endpoints[endpoint]
        profiles = Profiles.load()
        logged_in_org = client.get_org()
        org_href = logged_in_org.get('href')
        vdc_href = ''
        in_use_vdc = ''
        if vdc is None:
            for v in get_links(logged_in_org, media_type=EntityType.VDC.value):
                in_use_vdc = v.name
                vdc_href = v.href
                break
        else:
            for v in get_links(logged_in_org, media_type=EntityType.VDC.value):
                if vdc == v.name:
                    in_use_vdc = v.name
                    vdc_href = v.href
                    break
            if len(in_use_vdc) == 0:
                raise Exception('VDC not found')
        profiles.update(host,
                        org,
                        user,
                        client._session.headers['x-vcloud-authorization'],
                        api_version,
                        wkep,
                        verify_ssl_certs,
                        disable_warnings,
                        vdc=in_use_vdc,
                        org_href=org_href,
                        vdc_href=vdc_href,
                        debug=True)
        alt_text = '%s logged in, org: \'%s\', vdc: \'%s\'' % \
                   (user, org, in_use_vdc)
        stdout({'user': user, 'org': org,
                'vdc': in_use_vdc, 'logged_in': True}, ctx, alt_text)
    except Exception as e:
        try:
            profiles = Profiles.load()
            profiles.set('token', '')
        except Exception:
            pass
        if not ctx.find_root().params['json_output']:
            click.secho('can\'t log in', fg='red', err=True)
        stderr(e, ctx)


@cli.command(short_help='logout from vCD')
@click.pass_context
def logout(ctx):
    """Logout from vCloud Director

    """
    try:
        restore_session(ctx)
        client = ctx.obj['client']
        profiles = ctx.obj['profiles']
        client.logout()
        profiles.set('token', '')
        stdout('%s logged out' % (profiles.get('user')), ctx)
    except Exception as e:
        stderr(e, ctx)
