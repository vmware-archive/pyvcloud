# VMware vCloud Director Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import RelationType


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
               error_message=None
               ):
        t = E.Task(status=status,
                   serviceNamespace=namespace,
                   type=EntityType.TASK.value,
                   operation=operation,
                   operationName=operation_name,
                   name='task'
                   )
        t.append(E.Owner(href=owner_href,
                         name=owner_name,
                         type=owner_type))
        if error_message is not None:
            t.append(E.Error(stackTrace='',
                             majorErrorCode='500',
                             message=error_message,
                             minorErrorCode='INTERNAL_SERVER_ERROR'))
        t.append(E.User(href=user_href,
                        name=user_name,
                        type=EntityType.USER.value))
        if progress is not None:
            t.append(E.Progress(progress))
        t.append(E.Details(details))
        if task_href is None:
            org_resource = self.client.get_resource(org_href)
            link = find_link(org_resource,
                             RelationType.DOWN,
                             EntityType.TASKS_LIST.value)
            return self.client.post_resource(
                link.href,
                t,
                EntityType.TASK.value)
        else:
            return self.client.put_resource(
                task_href,
                t,
                EntityType.TASK.value)
