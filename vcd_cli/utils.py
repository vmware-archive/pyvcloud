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
from pygments import formatters
from pygments import highlight
from pygments import lexers
from pyvcloud.vcd.client import Client
import requests
import sys
from tabulate import tabulate
from vcd_cli.profiles import Profiles


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
        raise Exception('can\'t restore session, please re-login')
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
    client.rehydrate(profiles)
    ctx.obj = {}
    ctx.obj['client'] = client
    ctx.obj['profiles'] = profiles


def stdout(obj, ctx=None, alt_text=None, show_id=False):
    o = obj
    if ctx is not None and ctx.find_root().params['json_output']:
        if isinstance(obj, basestring):
            o = {'message': obj}
        text = json.dumps(o,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))
        click.echo(highlight(unicode(text, 'UTF-8'), lexers.JsonLexer(),
                             formatters.TerminalFormatter()))
    else:
        if alt_text is not None:
            text = alt_text
        elif isinstance(obj, basestring):
            text = o
        elif not isinstance(obj, list):
            text = as_table([{'property': k, 'value': v} for k, v in
                            sorted(obj.iteritems())], show_id=show_id)
        else:
            text = as_table(obj, show_id=show_id)
        click.echo(text)


def stderr(exception, ctx=None):
    if exception.message:
        message = exception.message
    else:
        message = str(exception)
    if ctx is not None and ctx.find_root().params['json_output']:
        message = {'error': str(message)}
        text = json.dumps(message,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))
        message = highlight(unicode(text, 'UTF-8'), lexers.JsonLexer(),
                            formatters.TerminalFormatter())
        click.echo(message)
        sys.exit(1)
    else:
        message = Fore.RED + str(message)
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
