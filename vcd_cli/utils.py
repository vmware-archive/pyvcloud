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
from colorama import Fore
import json
import logging
from lxml.objectify import ObjectifiedElement
from pygments import formatters
from pygments import highlight
from pygments import lexers
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.client import VcdErrorResponseException
from pyvcloud.vcd.utils import extract_id
from pyvcloud.vcd.utils import to_dict
import requests
import sys
from tabulate import tabulate
import traceback
from vcd_cli.profiles import Profiles


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.FileHandler('vcd.log'))


def is_admin(ctx):
    org_name = ctx.obj['profiles'].get('org')
    return org_name == 'System'


def as_table(obj_list, header=None, show_id=False):
    if len(obj_list) == 0:
        return ''
    else:
        headers = sorted(obj_list[0].keys())
        if not show_id and 'id' in headers:
            headers.remove('id')
        table = []
        for obj in obj_list:
            table.append([obj[k] for k in headers])
        return tabulate(table, headers)


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
        raise Exception('Can\'t restore session, please re-login.')
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
                    log_requests=profiles.get('log_request'),
                    log_headers=profiles.get('log_header'),
                    log_bodies=profiles.get('log_body')
                    )
    client.rehydrate(profiles)
    ctx.obj = {}
    ctx.obj['client'] = client
    ctx.obj['profiles'] = profiles


def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor


spinner = spinning_cursor()


def task_callback(task):
    message = '\x1b[2K\r{0}: {1}, status: {2}'.format(
        task.get('operationName'), task.get('operation'), task.get('status')
    )
    if hasattr(task, 'Progress'):
        message += ', progress: %s%%' % task.Progress
    if task.get('status').lower() in [TaskStatus.QUEUED.value,
                                      TaskStatus.PENDING.value,
                                      TaskStatus.PRE_RUNNING.value,
                                      TaskStatus.RUNNING.value]:
        message += ' %s ' % next(spinner)
    click.secho(message, nl=False)


def stdout(obj, ctx=None, alt_text=None, show_id=False):
    o = obj
    if ctx is not None and \
       'json_output' in ctx.find_root().params and \
       ctx.find_root().params['json_output']:
        if isinstance(obj, str):
            o = {'message': obj}
        text = json.dumps(o,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))
        if sys.version_info[0] < 3:
            text = str(text, 'utf-8')
        click.echo(highlight(text, lexers.JsonLexer(),
                             formatters.TerminalFormatter()))
    else:
        if alt_text is not None:
            text = alt_text
        elif isinstance(obj, str):
            text = o
        else:
            if 'task_href' in obj:
                obj = ctx.obj['client'].get_resource(obj.get('task_href'))
            if isinstance(obj, ObjectifiedElement):
                if obj.tag == '{http://www.vmware.com/vcloud/v1.5}Task':
                    if ctx is not None and \
                       hasattr(ctx.find_root().params, 'no_wait') and \
                       ctx.find_root().params['no_wait']:
                        text = as_table([to_dict(obj)], show_id=True)
                    else:
                        client = ctx.obj['client']
                        task = client.get_task_monitor().wait_for_status(
                                            task=obj,
                                            timeout=60,
                                            poll_frequency=2,
                                            fail_on_status=None,
                                            expected_target_statuses=[
                                                TaskStatus.SUCCESS,
                                                TaskStatus.ABORTED,
                                                TaskStatus.ERROR,
                                                TaskStatus.CANCELED],
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
                else:
                    text = as_table(to_dict(obj), show_id=show_id)
            elif not isinstance(obj, list):
                text = as_table([{'property': k, 'value': v} for k, v in
                                sorted(obj.items())], show_id=show_id)
            else:
                text = as_table(obj, show_id=show_id)
        click.echo('\x1b[2K\r' + text)


def stderr(exception, ctx=None):
    try:
        LOGGER.error(traceback.format_exc())
    except Exception:
        LOGGER.error(exception)
    if type(exception) == VcdErrorResponseException:
        message = str(exception)
    elif hasattr(exception, 'message'):
        message = exception.message
    else:
        message = str(exception)
    if ctx is not None and ctx.find_root().params['json_output']:
        message = {'error': str(message)}
        text = json.dumps(message,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))
        if sys.version_info[0] < 3:
            text = str(text, 'utf-8')
        message = highlight(text, lexers.JsonLexer(),
                            formatters.TerminalFormatter())
        click.echo(message)
        sys.exit(1)
    else:
        message = Fore.RED + str(message) + Fore.BLACK
        click.echo('\x1b[2K\r', nl=False)
        if ctx is not None:
            ctx.fail(message)
        else:
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
