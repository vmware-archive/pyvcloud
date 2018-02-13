#!/usr/bin/env python3
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.

# Useful library functions for tenant onboarding and removal.

from lxml.objectify import ObjectifiedElement

from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.utils import extract_id


def handle_task(client, obj):
    """Track a task to completion.

    :param client: The client.
    :type client: Client
    :param obj: XML representation of an entity with a task in it
    :type obj: ObjectifiedElement
    """
    if 'task_href' in obj:
        obj = client.get_resource(obj.get('task_href'))
    if isinstance(obj, ObjectifiedElement):
        if obj.tag == '{' + NSMAP['vcloud'] + '}Task':
            # Track task output.
            obj = client.get_resource(obj.get('href'))
            task = client.get_task_monitor().wait_for_status(
                task=obj,
                timeout=60,
                poll_frequency=5,
                fail_on_statuses=None,
                expected_target_statuses=[
                    TaskStatus.SUCCESS, TaskStatus.ABORTED,
                    TaskStatus.ERROR, TaskStatus.CANCELED
                ],
                callback=_task_callback)
            if task.get('status') == TaskStatus.ERROR.value:
                text = 'task: %s, result: %s, message: %s' % \
                       (extract_id(task.get('id')),
                        task.get('status'),
                        task.Error.get('message'))
                print(text)
                raise Exception("Operation failed!")
            else:
                text = 'task: %s, %s, result: %s' % \
                       (extract_id(task.get('id')),
                        task.get('operation'),
                        task.get('status'))
                print(text)
    else:
        # No task to handle.
        pass


def _task_callback(task):
    """Print task status.

    :param task: XML representation of a task resource
    :type task: lxml.objectify.ObjectifiedElement
    """
    message = '{0}: {1}, status: {2}'.format(
        task.get('operationName'), task.get('operation'), task.get('status'))
    if hasattr(task, 'Progress'):
        message += ', progress: %s%%' % task.Progress
    print(message)
