# VMware vCloud Director CLI
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
import collections
import json
import logging
import re
import sys
import traceback
from os import environ

import click
from colorama import Fore
from lxml.objectify import ObjectifiedElement
from pygments import formatters
from pygments import highlight
from pygments import lexers
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import MissingLinkException
from pyvcloud.vcd.client import MissingRecordException
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.client import VcdErrorResponseException
from pyvcloud.vcd.utils import extract_id
from pyvcloud.vcd.utils import task_to_dict
from pyvcloud.vcd.utils import to_dict
import requests
from tabulate import tabulate

from vcd_cli.profiles import Profiles

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.FileHandler('vcd.log'))


def is_sysadmin(ctx):
    org_name = ctx.obj['profiles'].get('org')
    return org_name == 'System'


def as_table(obj_list, show_id=False, sort_headers=True,
             hide_fields=['href', 'type']):
    if len(obj_list) == 0:
        return ''
    else:
        if sort_headers:
            headers = sorted(obj_list[0].keys())
        else:
            headers = obj_list[0].keys()
        if not show_id and 'id' in headers:
            headers.remove('id')
        for field in hide_fields:
            if field in headers:
                headers.remove(field)
        table = []
        for obj in obj_list:
            table.append(
                [obj.get(k) if k in obj.keys() else '' for k in headers])
        return tabulate(table, headers)


def as_prop_value_list(obj, show_id=True):
    return as_table([{'property': k, 'value': v} for k, v in
                    sorted(obj.items())], show_id=show_id)

def as_metavar(values):
    result = ''
    for v in values:
        if len(result) > 0:
            result += '|'
        result += v
    result = '[%s]' % result
    return result


def restore_session(ctx):
    profiles = Profiles.load()
    token = profiles.get('token')
    if token is None or len(token) == 0:
        raise Exception('Can\'t restore session, please login again.')
    if not profiles.get('verify'):
        if profiles.get('disable_warnings'):
            pass
        else:
            click.secho(
                'InsecureRequestWarning: '
                'Unverified HTTPS request is being made. '
                'Adding certificate verification is strongly '
                'advised.',
                fg='yellow',
                err=True)
        requests.packages.urllib3.disable_warnings()
    client = Client(
        profiles.get('host'),
        api_version=profiles.get('api_version'),
        verify_ssl_certs=profiles.get('verify'),
        log_file='vcd.log',
        log_requests=profiles.get('log_request'),
        log_headers=profiles.get('log_header'),
        log_bodies=profiles.get('log_body'))
    client.rehydrate(profiles)
    ctx.obj = {}
    ctx.obj['client'] = client
    ctx.obj['profiles'] = profiles


def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor


spinner = spinning_cursor()

last_message = ''


def task_callback(task):
    global last_message
    message = '\x1b[2K\r{0}: {1}, status: {2}'.format(
        task.get('operationName'), task.get('operation'), task.get('status'))
    if message != last_message:
        if last_message != '':
            click.secho(re.sub(', status: .*$', '', last_message))
        last_message = message
    if hasattr(task, 'Progress'):
        message += ', progress: %s%%' % task.Progress
    if task.get('status').lower() in [TaskStatus.QUEUED.value,
                                      TaskStatus.PRE_RUNNING.value,
                                      TaskStatus.RUNNING.value]:
        message += ' %s ' % next(spinner)
    click.secho(message, nl=False)


def stdout(obj, ctx=None, alt_text=None, show_id=False, sort_headers=True):
    global last_message
    last_message = ''
    o = obj
    if ctx is not None and \
       'json_output' in ctx.find_root().params and \
       ctx.find_root().params['json_output']:
        if isinstance(obj, str):
            o = {'message': obj}
        text = json.dumps(o, sort_keys=True, indent=4, separators=(',', ': '))
        if sys.version_info[0] < 3:
            text = str(text, 'utf-8')
        if ctx.find_root().params['is_colorized']:
            click.echo(
                highlight(text, lexers.JsonLexer(),
                          formatters.TerminalFormatter()))
        else:
            click.echo(text)
    else:
        if alt_text is not None:
            text = alt_text
        elif isinstance(obj, str):
            text = o
        else:
            if 'task_href' in obj:
                obj = ctx.obj['client'].get_resource(obj.get('task_href'))
            if isinstance(obj, ObjectifiedElement):
                if obj.tag == '{' + NSMAP['vcloud'] + '}Task':
                    if ctx is not None and \
                       'no_wait' in ctx.find_root().params and \
                       ctx.find_root().params['no_wait']:
                        text = as_prop_value_list(obj, show_id=show_id)
                    else:
                        client = ctx.obj['client']
                        task = client.get_task_monitor().wait_for_status(
                            task=obj,
                            timeout=60,
                            poll_frequency=5,
                            fail_on_statuses=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS, TaskStatus.ABORTED,
                                TaskStatus.ERROR, TaskStatus.CANCELED
                            ],
                            callback=task_callback)
                        if task.get('status') == TaskStatus.ERROR.value:
                            text = 'task: %s, result: %s, message: %s' % \
                                   (extract_id(task.get('id')),
                                    task.get('status'),
                                    task.Error.get('message'))
                            # TODO(should return != 0)
                        else:
                            text = 'task: %s, %s, result: %s' % \
                                   (extract_id(task.get('id')),
                                    task.get('operation'),
                                    task.get('status'))
                elif ctx.command.name == 'list' and \
                        isinstance(obj, collections.Iterable):
                    text = as_table(obj)
                elif ctx.command.name == 'info':
                    text = as_table([{'property': k, 'value': v} for k, v in
                                    sorted(to_dict(obj).items())],
                                    show_id=show_id)
                else:
                    text = as_table(to_dict(obj), show_id=show_id)
            elif not isinstance(obj, list):
                obj1 = {}
                for k, v in obj.items():
                    if type(v) in [list, tuple]:
                        value = ''.join('%s\n' % x for x in v)
                    elif type(v) is dict:
                        value = ''.join(
                            '%s: %s\n' % (x, y) for x, y in v.items())
                    else:
                        value = v
                    obj1[k] = value
                text = as_prop_value_list(obj1, show_id=show_id)
            else:
                text = as_table(
                    obj, show_id=show_id, sort_headers=sort_headers)
        click.echo('\x1b[2K\r' + text)


def stderr(exception, ctx=None):
    try:
        LOGGER.error(traceback.format_exc())
    except Exception:
        LOGGER.error(exception)
    if type(exception) == VcdErrorResponseException:
        if exception.status_code == 401:
            message = 'Session has expired or is invalid, please login again.'
        elif exception.status_code == 403:
            message = 'Access to the resource is forbidden, please login ' \
                      'with the required credentials and access level.'
        elif exception.status_code == 408:
            message = 'The server timed out waiting for the request, ' \
                      'please check your connection.'
        else:
            message = str(exception)
    elif type(exception) == MissingLinkException:
        message = str(exception)
    elif type(exception) == MissingRecordException:
        message = 'Record not found.'
    elif hasattr(exception, 'message'):
        message = exception.message
    else:
        message = str(exception)
    if ctx is not None and ctx.find_root().params['json_output']:
        message = {'error': str(message)}
        text = json.dumps(
            message, sort_keys=True, indent=4, separators=(',', ': '))
        if sys.version_info[0] < 3:
            text = str(text, 'utf-8')
        if ctx.find_root().params['is_colorized']:
            message = highlight(text, lexers.JsonLexer(),
                                formatters.TerminalFormatter())
        else:
            message = text
        click.echo(message)
        sys.exit(1)
    else:
        click.echo('\x1b[2K\r', nl=False)
        if ctx is not None:
            if ctx.find_root().params['is_colorized']:
                message = Fore.RED + str(message)
            ctx.fail(message)
        else:
            if 'VCD_USE_COLORED_OUTPUT' in environ.keys() and \
               environ['VCD_USE_COLORED_OUTPUT'] != '0':
                message = Fore.RED + str(message)
            click.echo(message)
            sys.exit(1)


def tabulate_names(names, columns=4):
    result = []
    row = None
    for n in range(len(names)):
        if n % columns == 0:
            row = [''] * columns
            result.append(row)
        row[n % columns] = names[n]
    return result


def acl_str_to_list_of_dict(access_settings_tuple):
    access_settings_list = []
    for access_str in access_settings_tuple:
        validate_access_str(access_str)
        access_setting = access_str.strip("'").split(":")

        access_dict = {'type': access_setting[0], 'name': access_setting[1]}
        if len(access_setting) > 2:
            access_dict['access_level'] = access_setting[2]
        access_settings_list.append(access_dict)
    return access_settings_list


def validate_access_str(access_str):
    access_setting = access_str.strip("'").split(":")

    valid_access_setting_format = \
        ['<subject-type>:<subject-name>:<access-level>',
         '<subject-type>:<subject-name>']
    valid_subject_type = ['org', 'user']
    valid_access_level = ['ReadOnly', 'Change', 'FullControl']

    if any(val == '' for val in access_setting):
        raise Exception("format of access setting %s should be one of "
                        "%s" % (access_str, valid_access_setting_format))

    if access_setting[0] not in valid_subject_type:
        raise Exception('subject-type in %s is not valid. Should be one of '
                        '%s,' % (access_str, valid_subject_type))
    if len(access_setting) > 2:
        if access_setting[2] not in valid_access_level:
            raise Exception(
                'access-level in %s is not valid. Should be one of '
                '%s' % (access_str, valid_access_level))


def access_settings_to_list(control_access_params, org_in_use=''):
    result = []
    entity_to_subject_type_dict = {
        EntityType.USER.value: 'user',
        EntityType.ADMIN_ORG.value: 'org'
    }
    current_org_access = {}
    if hasattr(control_access_params, 'IsSharedToEveryone'):
        current_org_access['subject_name'] = '%s (org_in_use)' % org_in_use
        current_org_access['subject_type'] = 'org'
    if hasattr(control_access_params, 'EveryoneAccessLevel'):
        current_org_access['access_level'] = control_access_params[
            'EveryoneAccessLevel']
    else:
        current_org_access['access_level'] = 'None'
    result.append(current_org_access)

    if hasattr(control_access_params, 'AccessSettings') and \
            hasattr(control_access_params.AccessSettings,
                    'AccessSetting') and \
            len(control_access_params.AccessSettings.AccessSetting) > 0:
        for access_setting in list(
                control_access_params.AccessSettings.AccessSetting):

            result.append({
                'subject_name':
                access_setting.Subject.get('name'),
                'subject_type':
                entity_to_subject_type_dict[access_setting.Subject.get(
                    'type')],
                'access_level':
                access_setting.AccessLevel
            })
    return result


def extract_name_and_id(user_input):
    """Determines if the string user_input is a name or an id.

    :param user_input: (str): input string from user
    :return: (name, id) pair
    """
    name = id = None
    if user_input.lower().startswith('id:'):
        id = user_input[3:]
    else:
        name = user_input
    return name, id
