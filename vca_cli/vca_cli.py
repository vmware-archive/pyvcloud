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
import operator
import click
import pkg_resources
import requests
from cmd_proc import CmdProc
from vca_cli_utils import VcaCliUtils
from pyvcloud.vcloudair import VCA


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
        version_vca_cli = pkg_resources.require("vca-cli")[0].version
        version_pyvcloud = pkg_resources.require("pyvcloud")[0].version
        msg = 'vca-cli version %s (pyvcloud: %s)' % \
              (version_vca_cli, version_pyvcloud)
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
    cmd_proc.save_config(cmd_proc.profile, cmd_proc.profile_file)
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
    print 'profile_file:   ' + cmd_proc.profile_file
    print 'profile:        ' + cmd_proc.profile
    print 'host:           ' + cmd_proc.vca.host
    print 'user:           ' + str(cmd_proc.vca.username)
    if cmd_proc.password is None or len(cmd_proc.password) == 0:
        print 'pass:           ' + str(cmd_proc.password)
    else:
        print 'pass:           ' + '<encrypted>'
    print 'type:           ' + str(cmd_proc.vca.service_type)
    print 'active session: ' + str(result)


@cli.command()
@click.pass_obj
@click.argument('user')
@click.option('-p', '--password', prompt=True,
              confirmation_prompt=False, hide_input=True, help='Password')
@click.option('-d', '--do-not-save-password', is_flag=True,
              default=False, help='Do not save password')
@click.option('-v', '--version', 'service_version',
              default='5.7', metavar='[5.5 | 5.6 | 5.7]',
              type=click.Choice(['5.5', '5.6', '5.7']), help='')
@click.option('-H', '--host', default='https://vca.vmware.com',
              help='')
@click.option('-i', '--instance', default=None, help='Instance Id')
@click.option('-o', '--org', default=None, help='Organization Name')
@click.option('-c', '--host-score', 'host_score',
              default='https://score.vca.io', help='URL of the Score server')
def login(cmd_proc, user, host, password, do_not_save_password,
          service_version, instance, org, host_score):
    """Login to a vCloud service"""
    if not (host.startswith('https://') or host.startswith('http://')):
        host = 'https://' + host
    if not (host_score.startswith('https://') or
            host_score.startswith('http://')):
        host_score = 'https://' + host_score
    try:
        cmd_proc.logout()
        result = cmd_proc.login(host, user, password, version=service_version,
                                save_password=(not do_not_save_password))
        if result:
            utils.print_message("User '%s' logged in, profile '%s'" %
                                (cmd_proc.vca.username, cmd_proc.profile),
                                cmd_proc)
            if not do_not_save_password:
                utils.print_warning('Password encrypted and saved ' +
                                    'in local profile. Use ' +
                                    '--do-not-save-password to disable it.',
                                    cmd_proc)
        else:
            utils.print_error('Can\'t login', cmd_proc)
    except Exception as e:
        utils.print_error('Can\'t login: ' + str(e), cmd_proc)


@cli.command()
@click.pass_obj
def logout(cmd_proc):
    """Logout from a vCloud service"""
    user = cmd_proc.vca.username
    profile = cmd_proc.profile
    cmd_proc.logout()
    utils.print_message("User '%s' logged out, profile '%s'" %
                        (user, profile),
                        cmd_proc)


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | use]',
                type=click.Choice(['list', 'info', 'use']))
@click.option('-i', '--instance', default='', metavar='<instance>',
              help='Instance Id')
def instance(cmd_proc, operation, instance):
    """Operations with Instances"""
    if cmd_proc.vca.service_type != VCA.VCA_SERVICE_TYPE_VCA:
        utils.print_message('This service type doesn\'t support this command')
        return
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        return
    if 'list' == operation:
        headers = ["Service Group", "Region", "Plan", "Instance Id"]
        instances = cmd_proc.vca.instances
        plans = cmd_proc.vca.get_plans()
        service_groups = cmd_proc.vca.get_service_groups()
        items = instances if instances else []
        table = []
        for item in items:
            plan_name = filter(lambda plan: plan['id'] == item['planId'],
                               plans)[0]['name']
            service_group = filter(lambda sg:
                                   sg['id'] == item['serviceGroupId'],
                                   service_groups['serviceGroup'])
            service_group_name = '' if len(service_group) == 0 else \
                                 service_group[0]['displayName']
            table.append([
                service_group_name,
                item['region'].split('.')[0],
                plan_name,
                item['id']
            ])
        sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
        utils.print_table("Available instances for user '%s'"
                          ", profile '%s':" %
                          (cmd_proc.vca.username, cmd_proc.profile),
                          'instances', headers, sorted_table, cmd_proc)
    else:
        utils.print_message('Not implemented')
