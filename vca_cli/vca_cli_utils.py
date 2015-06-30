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
import json
import operator
from tabulate import tabulate


class VcaCliUtils:

    def _print(self, message, cmd_proc=None, fg='black'):
        click.secho(message, fg=fg)

    def print_warning(self, message, cmd_proc=None):
        self._print(message, cmd_proc, fg='yellow')

    def print_message(self, message, cmd_proc=None):
        self._print(message, cmd_proc, fg='blue')

    def print_error(self, message, cmd_proc=None):
        msg = message
        if cmd_proc is not None and \
                cmd_proc.vca is not None and \
                cmd_proc.vca.response is not None and \
                cmd_proc.vca.response.content is not None:
            if 'message' in cmd_proc.vca.response.content:
                json_message = json.loads(cmd_proc.vca.response.content)
                msg += ': ' + json_message.get('message')
            else:
                msg += ': ' + cmd_proc.vca.response.content
        self._print(msg, cmd_proc, fg='red')

    def print_table(self, message, headers, table, cmd_proc=None):
        if cmd_proc is not None and cmd_proc.json_output:
            json_obj = self.table_to_json(headers, table)
            self._print_json(message, json_obj, cmd_proc)
        elif cmd_proc is not None and cmd_proc.xml_output:
            click.secho('Not implemented', fg='black')
        else:
            self._print_table(message, headers, table, cmd_proc)

    def print_json(self, message, json_obj, cmd_proc=None):
        if cmd_proc is not None and cmd_proc.json_output:
            self._print_json(message, json_obj, cmd_proc)
        elif cmd_proc is not None and cmd_proc.xml_output:
            click.secho('Not implemented', fg='black')
        else:
            headers = ['Key', 'Value']
            table = []
            for key in json_obj.keys():
                table.append([key, json_obj.get(key)])
            sorted_table = sorted(table, key=operator.itemgetter(0),
                                  reverse=False)
            self._print_table(message, headers, sorted_table, cmd_proc)

    def _print_table(self, message, headers, table, cmd_proc=None):
        click.secho(message, fg='blue')
        print(tabulate(table, headers=headers, tablefmt="orgtbl"))

    def _print_json(self, message, json_obj, cmd_proc=None):
        click.secho(json.dumps(json_obj, sort_keys=True,
                    indent=4, separators=(',', ': ')), fg='black')

    def table_to_json(self, headers, table):
        return [dict(zip(headers, row)) for row in table]

    def beautified(self, input_array):
        return str(input_array).strip('[]').replace("'", "")
