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
import operator
from vca_cli import cli, utils, default_operation
from pyvcloud.vcloudair import VCA


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | change-pass]',
                type=click.Choice(['list', 'info', 'change-pass']))
@click.option('-u', '--user', 'username', default='',
              metavar='<user>', help='User')
@click.option('-p', '--password', 'password', default='',
              metavar='<password>', help='Password')
def user(cmd_proc, operation, username, password):
    """Operations with Users"""
    if cmd_proc.vca.service_type is not VCA.VCA_SERVICE_TYPE_VCA:
        utils.print_message('Operation not supported '
                            'in this service type')
        return
#  see https://wiki.eng.vmware.com/Praxis_IAM_API_Details
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        return
    if 'list' == operation:
        headers = ['User Name', 'First', 'Last', 'Email', 'State', 'Roles']
        table = []
        for u in cmd_proc.vca.get_users():
            roles = []
            for r in u.get('roles').get('roles'):
                roles.append(str(r.get('name')))
            table.append([u.get('userName'), u.get('givenName'),
                         u.get('familyName'), u.get('email'), u.get('state'),
                          utils.beautified(roles)])
        sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
        utils.print_table("Available users in instance '%s'"
                          ", profile '%s':" %
                          (cmd_proc.instance, cmd_proc.profile),
                          headers, sorted_table,
                          cmd_proc)
    elif 'info' == operation:
        pass
    cmd_proc.save_current_config()
