# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import urllib

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import TaskStatus


class Task(object):
    def __init__(self, client):
        self.client = client

    def update(self,
               status,
               namespace,
               operation,
               operation_name,
               details,
               progress,
               owner_href,
               owner_name,
               owner_type,
               user_href,
               user_name,
               org_href=None,
               task_href=None,
               error_message=None,
               stack_trace=''):
        """Update a task in vCD.

        :param str status: new status of the task.
        :param str namespace: identifier of the service that created the task.
            It must not start with com.vmware.vcloud and the length must be
            between 1 and 128 symbols.
        :param str operation: new message describing the operation that is
            being tracked by this task.
        :param str operation_name: new short name of the operation that is
            being tracked by the task.
        :param details: new detailed message about the task.
        :param str progress: read-only indicator of task progress as an
            approximate percentage between 0 and 100. Not available for all
            tasks.
        :param str owner_href: href of the owner of the task. This is typically
            the object that the task is creating or updating.
        :param str owner_name: name of the owner of the task.
        :param str owner_type: XML type of the owner object
        :param str user_href: href of the user who started the task.
        :param str user_name: name of the user who started the task.
        :param str org_href: href of the organization, which the user mentioned
            above belongs to.
        :param str task_href: href of the task.
        :param str error_message: represents error information from a failed
            task.
        :param str stack_trace: stack trace of the error message from a
            failed task.

        :return: an object containing EntityType.TASK XML data representing the
            updated task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        t = E.Task(
            status=status,
            serviceNamespace=namespace,
            type=EntityType.TASK.value,
            operation=operation,
            operationName=operation_name,
            name='task')
        t.append(E.Owner(href=owner_href, name=owner_name, type=owner_type))
        if error_message is not None:
            t.append(
                E.Error(
                    stackTrace=stack_trace,
                    majorErrorCode='500',
                    message=error_message,
                    minorErrorCode='INTERNAL_SERVER_ERROR'))
        t.append(
            E.User(href=user_href, name=user_name, type=EntityType.USER.value))
        if progress is not None:
            t.append(E.Progress(progress))
        t.append(E.Details(details))
        if task_href is None:
            org_resource = self.client.get_resource(org_href)
            link = find_link(org_resource, RelationType.DOWN,
                             EntityType.TASKS_LIST.value)
            return self.client.post_resource(link.href, t,
                                             EntityType.TASK.value)
        else:
            return self.client.put_resource(task_href, t,
                                            EntityType.TASK.value)

    def list_tasks(self,
                   filter_status_list=[
                       TaskStatus.QUEUED.value, TaskStatus.PRE_RUNNING.value,
                       TaskStatus.RUNNING.value
                   ],
                   newer_first=True):
        """Return a list of tasks accessible by the user, filtered by status.

        :param list filter_status_list: a list of strings representing task
            statuses that should be used to filter the query result.

        :return: tasks in form of lxml.objectify.ObjectifiedElement containing
            EntityType.TASK XML data representing the tasks that matched the
            status filter.

        :rtype: generator object
        """
        query_filter = ''
        for f in filter_status_list:
            query_filter += 'status==%s,' % urllib.parse.quote_plus(f)
        if len(query_filter) > 0:
            query_filter = query_filter[:-1]
        sort_asc = None
        sort_desc = None
        if newer_first:
            sort_desc = 'startDate'
        else:
            sort_asc = 'startDate'
        resource_type_cc = 'task'
        if self.client.is_sysadmin():
            resource_type_cc = 'adminTask'
        q = self.client.get_typed_query(
            resource_type_cc,
            query_result_format=QueryResultFormat.ID_RECORDS,
            qfilter=query_filter,
            sort_asc=sort_asc,
            sort_desc=sort_desc)
        return q.execute()
