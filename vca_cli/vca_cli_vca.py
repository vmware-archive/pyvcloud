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
from pyvcloud.vcloudair import VCA
import sys
from vca_cli import cli
from vca_cli import default_operation
from vca_cli import utils


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list | info | create | delete | '
                        'validate | change-password | '
                        'reset-password]',
                type=click.Choice(['list', 'info',
                                   'create', 'delete', 'validate',
                                   'change-password', 'reset-password']))
@click.option('-u', '--user', 'username', default='',
              metavar='<user>', help='User')
@click.option('-i', '--id', 'user_id', default=None,
              metavar='<user-id>', help='User Id')
@click.option('-p', '--password', 'password', default='',
              metavar='<password>', help='Password')
@click.option('-n', '--new-password', 'new_password', default='',
              metavar='<password>', help='New Password')
@click.option('-f', '--first', 'first_name', default='',
              metavar='<first-name>', help='First Name')
@click.option('-l', '--last', 'last_name', default='',
              metavar='<last-name>', help='Last Name')
@click.option('-r', '--roles', 'roles', default='',
              metavar='<roles>', help='Comma-separated list of Roles')
@click.option('-t', '--token', 'token', default='',
              metavar='<token>', help='Token')
def user(cmd_proc, operation, username, user_id, password, new_password,
         first_name, last_name, roles, token):
    """Operations with Users"""
    if cmd_proc.vca.service_type != VCA.VCA_SERVICE_TYPE_VCA:
        utils.print_error('Operation not supported '
                          'in this service type')
        sys.exit(1)
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    try:
        if 'list' == operation:
            headers = ['User Name', 'First', 'Last', 'Email', 'State', 'Id',
                       'Roles']
            table = []
            for u in cmd_proc.vca.get_users():
                roles = []
                for r in u.get('roles').get('roles'):
                    roles.append(str(r.get('name')))
                table.append([u.get('userName'), u.get('givenName'),
                              u.get('familyName'), u.get('email'),
                              u.get('state'),
                              u.get('id'),
                              utils.beautified(roles)])
            sorted_table = sorted(table, key=operator.itemgetter(0),
                                  reverse=False)
            utils.print_table("Available users in instance '%s'"
                              ", profile '%s':" %
                              (cmd_proc.instance, cmd_proc.profile),
                              headers, sorted_table,
                              cmd_proc)
        elif 'info' == operation:
            cmd_proc.error_message = 'not implemented'
            sys.exit(1)
        elif 'create' == operation:
            roles_array = roles.split(',')
            result = cmd_proc.vca.add_user(username, first_name,
                                           last_name, roles_array)
            utils.print_message("User '%s' successfully created" % username)
        elif 'delete' == operation:
            result = cmd_proc.vca.del_user(user_id)
            utils.print_message("Successfully deleted user '%s'" %
                                cmd_proc.vca.username)
        elif 'change-password' == operation:
            result = cmd_proc.vca.change_password(password, new_password)
            utils.print_message("Successfully changed password for user '%s'"
                                % cmd_proc.vca.username)
        elif 'validate' == operation:
            result = cmd_proc.vca.validate_user(username, password, token)
            print(result)
        elif 'reset-password' == operation:
            result = cmd_proc.vca.reset_password(user_id)
            utils.print_message("Successfully reset password for user id"
                                "'%s', check email to enter new password"
                                % user_id)
    except Exception:
        utils.print_error('An error has ocurred', cmd_proc)
        sys.exit(1)
    cmd_proc.save_current_config()


@cli.command()
@click.pass_obj
@click.argument('operation', default=default_operation,
                metavar='[list ]',
                type=click.Choice(['list']))
def role(cmd_proc, operation):
    """Operations with Roles"""
    if cmd_proc.vca.service_type != VCA.VCA_SERVICE_TYPE_VCA:
        utils.print_message('Operation not supported '
                            'in this service type')
        sys.exit(1)
    result = cmd_proc.re_login()
    if not result:
        utils.print_error('Not logged in', cmd_proc)
        sys.exit(1)
    if 'list' == operation:
        headers = ['Role Name', 'Description', 'Permissions']
        table = []
        for r in cmd_proc.vca.get_roles():
            permissions = []
            if len(r.get('rights')) > 0:
                for p in r.get('rigths'):
                    permissions.append(str(p.get('name')))
            table.append([r.get('name'),
                          r.get('description'),
                          utils.beautified(permissions)])
        sorted_table = sorted(table, key=operator.itemgetter(0), reverse=False)
        utils.print_table("Available roles in instance '%s'"
                          ", profile '%s':" %
                          (cmd_proc.instance, cmd_proc.profile),
                          headers, sorted_table,
                          cmd_proc)
    cmd_proc.save_current_config()
