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
from datetime import datetime
import dateutil.parser
import json
import operator
import os
from pyvcloud.helper import CommonUtils
from pyvcloud import Http
from pyvcloud import Log
from pyvcloud.schema.vcd.v1_5.schemas.vcloud.vcloudType import parseString
import requests
import sys
from tabulate import tabulate
import time
import xmltodict


class VcaCliUtils(object):

    def _print(self, message, cmd_proc=None, fg='black'):
        click.secho(message, fg=fg, err=(fg in ['yellow', 'red']))

    def print_warning(self, message, cmd_proc=None):
        self._print(message, cmd_proc, fg='yellow')

    def print_message(self, message, cmd_proc=None):
        self._print(message, cmd_proc, fg='blue')

    def print_error(self, message, cmd_proc=None, module=None):
        msg = message
        if cmd_proc is not None and \
                cmd_proc.vca is not None and \
                cmd_proc.vca.response is not None and \
                cmd_proc.vca.response.content is not None:
            if '<Error xmlns=' in cmd_proc.vca.response.content:
                error = parseString(cmd_proc.vca.response.content, True)
                msg = message + ': ' + error.get_message()
            elif 'message' in cmd_proc.vca.response.content and \
                    '<Error' not in cmd_proc.vca.response.content:
                json_message = json.loads(cmd_proc.vca.response.content)
                msg = message + ': ' + json_message.get('message')
        if cmd_proc is not None and \
                cmd_proc.vca is not None and \
                cmd_proc.vca.vcloud_session is not None and \
                cmd_proc.vca.vcloud_session.response is not None and \
                cmd_proc.vca.vcloud_session.response.content is not None:
            if '<Error xmlns=' in cmd_proc.vca.vcloud_session.response.content:
                error = parseString(cmd_proc.vca.vcloud_session.response.
                                    content,
                                    True)
                msg = message + ': ' + error.get_message()
            elif 'message' in cmd_proc.vca.vcloud_session.response.content \
                    and '<Error' not in \
                    cmd_proc.vca.vcloud_session.response.content:
                json_message = json.loads(cmd_proc.vca.vcloud_session.response.
                                          content)
                msg = message + ': ' + json_message.get('message')
        if cmd_proc is not None and \
                cmd_proc.error_message is not None:
                msg = message + ': ' + cmd_proc.error_message
        if module is not None and \
                module.response is not None and \
                'message' in module.response.json():
                msg = message + ': ' + module.response.json().get('message')
        if (msg == 'Not logged in'):
            msg += ', try the --insecure flag when using self-signed ' \
                   'certificates.'
        self._print(msg, cmd_proc, fg='red')

    def print_table(self, message, headers, table, cmd_proc=None):
        if cmd_proc is not None and cmd_proc.json_output:
            json_obj = self.table_to_json(headers, table)
            self._print_json(json_obj)
        elif cmd_proc is not None and cmd_proc.xml_output:
            click.secho('Not implemented', fg='black')
        else:
            self._print_table(message, headers, table, cmd_proc)

    def print_json(self, json_obj, message=None, cmd_proc=None):
        if cmd_proc is not None and cmd_proc.json_output:
            self._print_json(json_obj)
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
        if message is not None:
            click.secho(message, fg='blue')
        print(tabulate(table, headers=headers, tablefmt="orgtbl"))

    def _print_json(self, json_obj):
        click.secho(json.dumps(json_obj, sort_keys=True,
                    indent=4, separators=(',', ': ')), fg='black')

    def table_to_json(self, headers, table):
        return [dict(zip(headers, row)) for row in table]

    def beautified(self, input_array):
        return str(input_array).strip('[]').replace("'", "")

    def display_progress(self, task, cmd_proc=None, headers=None):
        progress = task.get_Progress()
        status = task.get_status()
        rnd = 0
        response = None
        rows, columns = os.popen('stty size', 'r').read().split()
        while status != "success":
            if status == "error":
                error = task.get_Error()
                sys.stdout.write('\r' + ' ' * int(columns) + '\r')
                sys.stdout.flush()
                self.print_error(task.get_operation(),
                                 cmd_proc=cmd_proc)
                self.print_error(CommonUtils.convertPythonObjToStr(
                                 error, name="Error"),
                                 cmd_proc=cmd_proc)
                return None
            else:
                # some task doesn't not report progress
                if progress:
                    sys.stdout.write("\rprogress: [" + "*" *
                                     int(progress) + " " *
                                     (40 - int(progress - 1)) + "] " +
                                     str(progress) + " %")
                else:
                    sys.stdout.write("\rprogress: ")
                    if rnd % 4 == 0:
                        sys.stdout.write(
                            "[" + "*" * 10 + " " * 30 + "]")
                    elif rnd % 4 == 1:
                        sys.stdout.write(
                            "[" + " " * 10 + "*" * 10 + " " * 20 + "]")
                    elif rnd % 4 == 2:
                        sys.stdout.write(
                            "[" + " " * 20 + "*" * 10 + " " * 10 + "]")
                    elif rnd % 4 == 3:
                        sys.stdout.write(
                            "[" + " " * 30 + "*" * 10 + "]")
                    rnd += 1
                msg = ' %s' % task.get_operation()
                sys.stdout.write(msg + ' ' * (int(columns)-52-len(msg)) + '\r')
                sys.stdout.flush()
                time.sleep(1)
                response = Http.get(task.get_href(), headers=headers,
                                    verify=cmd_proc.verify,
                                    logger=cmd_proc.logger)
                if response.status_code == requests.codes.ok:
                    task = parseString(response.content, True)
                    progress = task.get_Progress()
                    status = task.get_status()
                else:
                    Log.error(cmd_proc.logger, "can't get task")
                    return
            rows, columns = os.popen('stty size', 'r').read().split()
        sys.stdout.write("\r" + " " * int(columns) + '\r')
        sys.stdout.flush()
        if response is not None:
            if cmd_proc is not None and cmd_proc.json_output:
                sys.stdout.write("\r" +
                                 self.task_to_json(response.content) + '\n')
            else:
                sys.stdout.write("\r" +
                                 self.task_to_table(response.content) + '\n')
            sys.stdout.flush()

    def utc2local(self, utc):
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp(epoch) -\
            datetime.utcfromtimestamp(epoch)
        return utc + offset

    def remove_unwanted_keys_from_task(self, task_dict):
        removed_keys = ["expiryTime", "cancelRequested",
                        "id", "name", "operation",
                        "operationName", "serviceNamespace",
                        "type", "xmlns",
                        "xmlns:xsi", "xsi:schemaLocation", "Details",
                        "Organization", "Owner", "User"]
        for removed_key in removed_keys:
            for key in task_dict["Task"]:
                if removed_key in key:
                    del task_dict["Task"][key]
                    break

    def task_to_json(self, task):
        task_dict = xmltodict.parse(task)
        self.remove_unwanted_keys_from_task(task_dict)
        task_dict["Errorcode"] = "0"
        return json.dumps(task_dict, sort_keys=True,
                          indent=4, separators=(',', ': '))

    def task_to_table(self, task):
        task_dict = xmltodict.parse(task)
        self.remove_unwanted_keys_from_task(task_dict)
        for key in task_dict["Task"]:
            if "Link" in key:
                rel = [task_dict["Task"][key][link_key]
                       for link_key in task_dict["Task"][key]
                       if "rel" in link_key][0]
                href = [task_dict["Task"][key][link_key]
                        for link_key in task_dict["Task"][key]
                        if "href" in link_key][0]
                task_dict["Task"][rel] = href
                del task_dict["Task"][key]
        headers = ['Start Time', 'Duration', 'Status']
        startTime = dateutil.parser.parse(
            task_dict["Task"].get('@startTime'))
        endTime = dateutil.parser.parse(
            task_dict["Task"].get('@endTime'))
        duration = endTime - startTime
        localStartTime = self.utc2local(startTime)
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 60 * 60)
        minutes, seconds = divmod(remainder, 60)
        table = []
        if hours <= 0:
            table.append([localStartTime.strftime("%Y-%m-%d %H:%M:%S"),
                          '{} mins {} secs'.format(minutes, seconds),
                          task_dict["Task"].get('@status')])
        else:
            table.append([localStartTime.strftime("%Y-%m-%d %H:%M:%S"),
                          '{} hours {} mins {} secs'.
                          format(hours, minutes, seconds),
                          task_dict["Task"].get('@status')])
        return tabulate(table, headers=headers, tablefmt="orgtbl")
